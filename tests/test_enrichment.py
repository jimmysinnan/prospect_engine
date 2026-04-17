# tests/test_enrichment.py
from modules.enrichment import (
    extract_email_from_html,
    extract_phone_from_html,
    extract_socials_from_html,
    extract_footer_html,
    find_subpage_urls,
    compute_digital_score,
)

HOMEPAGE_HTML = """
<html>
<body>
  <header><nav>
    <a href="/contact">Contact</a>
    <a href="/mentions-legales">Mentions légales</a>
    <a href="/about">À propos</a>
  </nav></header>
  <main><p>Bienvenue sur notre site.</p></main>
  <footer>
    <p>Tél : 0596 72 10 20</p>
    <a href="https://www.linkedin.com/company/cabinet-dupont">LinkedIn</a>
    <a href="https://www.facebook.com/cabinetdupont">Facebook</a>
  </footer>
</body>
</html>
"""

CONTACT_HTML = """
<html><body>
  <h1>Contactez-nous</h1>
  <p>Email : contact@cabinet-dupont.fr</p>
  <p>Téléphone : +596 596 72 10 20</p>
</body></html>
"""

MENTIONS_HTML = """
<html><body>
  <h1>Mentions légales</h1>
  <p>Responsable : Jean DUPONT</p>
  <p>Contact : direction@cabinet-dupont.fr</p>
</body></html>
"""

def test_extract_email_from_contact_page():
    emails = extract_email_from_html(CONTACT_HTML)
    assert "contact@cabinet-dupont.fr" in emails

def test_extract_email_from_mentions():
    emails = extract_email_from_html(MENTIONS_HTML)
    assert "direction@cabinet-dupont.fr" in emails

def test_extract_phone_local():
    phones = extract_phone_from_html(CONTACT_HTML)
    assert any("0596" in p or "596" in p for p in phones)

def test_extract_socials_from_footer():
    footer = extract_footer_html(HOMEPAGE_HTML)
    socials = extract_socials_from_html(footer)
    assert socials.get("linkedin") == "https://www.linkedin.com/company/cabinet-dupont"
    assert socials.get("facebook") == "https://www.facebook.com/cabinetdupont"

def test_find_subpage_urls_contact():
    urls = find_subpage_urls(HOMEPAGE_HTML, base_url="https://cabinet-dupont.fr")
    assert "https://cabinet-dupont.fr/contact" in urls

def test_find_subpage_urls_mentions():
    urls = find_subpage_urls(HOMEPAGE_HTML, base_url="https://cabinet-dupont.fr")
    assert "https://cabinet-dupont.fr/mentions-legales" in urls

def test_extract_no_email():
    assert extract_email_from_html("<html><body>Pas d'email ici</body></html>") == []

def test_compute_digital_score_full():
    score = compute_digital_score(
        has_website=True,
        has_email=True,
        has_phone=True,
        socials={"linkedin": "x", "facebook": "x"},
    )
    assert score >= 80

def test_compute_digital_score_minimal():
    score = compute_digital_score(
        has_website=True,
        has_email=False,
        has_phone=False,
        socials={},
    )
    assert score <= 40

def test_compute_digital_score_no_website():
    score = compute_digital_score(
        has_website=False,
        has_email=False,
        has_phone=False,
        socials={},
    )
    assert score == 0