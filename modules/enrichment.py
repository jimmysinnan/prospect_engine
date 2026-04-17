import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

TIMEOUT = 8
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ProspectEngine/2.0)"}

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
# Accepte un espace optionnel entre le préfixe international (+596 596...) et le numéro local
_PHONE_RE = re.compile(r"(?:\+(?:33|596|262|594|269)|0033|0)\s?[1-9](?:[\s.\-]?\d{2}){4}")
_SOCIAL_DOMAINS = {
    "linkedin": "linkedin.com",
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "twitter": "twitter.com",
}

_CONTACT_KEYWORDS = ["contact", "nous-contacter", "contactez", "joindre"]
_LEGAL_KEYWORDS = ["mentions-legales", "mentions_legales", "mentionslegales",
                   "legal", "legales", "informations-legales"]


def enrich_lead(lead):
    """
    Enrichit un lead depuis son site web.
    Stratégie : homepage → contact + mentions légales → footer.
    Modifie le lead in-place. Retourne le lead.
    """
    website = lead.get("website", "")
    if not website:
        lead.setdefault("socials", {})
        lead["digital_score"] = 0
        lead["digital_maturity_label"] = "Absent"
        return lead

    base_url = _normalize_url(website)
    homepage_html = _fetch_html(base_url)
    if not homepage_html:
        lead.setdefault("socials", {})
        lead["digital_score"] = 20
        lead["digital_maturity_label"] = "Site inaccessible"
        return lead

    all_html_parts = [homepage_html]

    footer_html = extract_footer_html(homepage_html)
    if footer_html:
        all_html_parts.append(footer_html)

    subpage_urls = find_subpage_urls(homepage_html, base_url=base_url)
    for url in subpage_urls[:4]:
        page_html = _fetch_html(url)
        if page_html:
            all_html_parts.append(page_html)

    combined_html = "\n".join(all_html_parts)

    emails = extract_email_from_html(combined_html)
    phones = extract_phone_from_html(combined_html)
    socials = extract_socials_from_html(combined_html)

    if not lead.get("email") and emails:
        lead["email"] = emails[0]
    if not lead.get("tel") and phones:
        lead["tel"] = phones[0]

    lead["socials"] = socials
    lead["digital_score"] = compute_digital_score(
        has_website=True,
        has_email=bool(emails),
        has_phone=bool(phones),
        socials=socials,
    )
    lead["digital_maturity_label"] = _maturity_label(lead["digital_score"])
    return lead


def enrich_leads_batch(leads, progress_callback=None):
    """Enrichit une liste de leads. Ignore silencieusement les erreurs."""
    for i, lead in enumerate(leads):
        try:
            enrich_lead(lead)
        except Exception:
            lead.setdefault("socials", {})
            lead.setdefault("digital_score", 0)
            lead.setdefault("digital_maturity_label", "Erreur")
        if progress_callback:
            progress_callback(i + 1, len(leads))
    return leads


def find_subpage_urls(html, base_url):
    """Trouve les URLs contact et mentions légales dans la homepage."""
    soup = BeautifulSoup(html, "html.parser")
    contact_urls = []
    legal_urls = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip().lower()
        text = tag.get_text(strip=True).lower()
        full_url = urljoin(base_url, tag["href"].strip())

        parsed = urlparse(full_url)
        base_parsed = urlparse(base_url)
        if parsed.netloc and parsed.netloc != base_parsed.netloc:
            continue
        if not parsed.path or parsed.path == "/":
            continue

        if any(kw in href or kw in text for kw in _CONTACT_KEYWORDS):
            contact_urls.append(full_url)
        elif any(kw in href or kw in text for kw in _LEGAL_KEYWORDS):
            legal_urls.append(full_url)

    seen = set()
    result = []
    for url in contact_urls + legal_urls:
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result


def extract_footer_html(html):
    """Extrait le contenu du tag <footer> ou d'une div.footer."""
    soup = BeautifulSoup(html, "html.parser")
    footer = soup.find("footer")
    if footer:
        return str(footer)
    for div in soup.find_all("div", class_=True):
        classes = " ".join(div.get("class", []))
        if "footer" in classes.lower():
            return str(div)
    return ""


def extract_email_from_html(html):
    """Extrait les emails uniques. Décode les obfuscations courantes."""
    text = html.replace("[at]", "@").replace("(at)", "@").replace(" at ", "@")
    return list(dict.fromkeys(_EMAIL_RE.findall(text)))


def extract_phone_from_html(html):
    """Extrait les téléphones uniques (France métro + DOM-TOM)."""
    raw = _PHONE_RE.findall(html)
    cleaned = [re.sub(r"[\s.\-]", "", p) for p in raw]
    return list(dict.fromkeys(cleaned))


def extract_socials_from_html(html):
    """Extrait les liens réseaux sociaux."""
    soup = BeautifulSoup(html, "html.parser")
    found = {}
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        for name, domain in _SOCIAL_DOMAINS.items():
            if domain in href and name not in found:
                found[name] = href
    return found


def compute_digital_score(has_website, has_email, has_phone, socials):
    """Score de maturité digitale 0-100."""
    if not has_website:
        return 0
    score = 30
    if has_email:
        score += 25
    if has_phone:
        score += 20
    score += min(len(socials) * 10, 25)
    return min(score, 100)


def _normalize_url(url):
    if not url.startswith("http"):
        return "https://" + url
    return url


def _fetch_html(url):
    try:
        resp = requests.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def _maturity_label(score):
    if score == 0:
        return "Absent"
    if score < 30:
        return "Minimal"
    if score < 60:
        return "Basique"
    if score < 85:
        return "Actif"
    return "Avancé"