import requests
from datetime import datetime

SIRENE_API = "https://recherche-entreprises.api.gouv.fr/search"


def search_companies(secteur="", departement="", nb=150, age_max_mois=None, taille=None):
    per_page = min(nb, 25)
    params = {"per_page": per_page, "page": 1}
    if secteur:
        params["q"] = secteur
    dept_filter = departement.strip().split(",")[0].strip() if departement else ""
    if dept_filter:
        params["departement"] = dept_filter

    results = []
    page = 1
    while len(results) < nb:
        params["page"] = page
        try:
            resp = requests.get(SIRENE_API, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException:
            break

        items = data.get("results", [])
        if not items:
            break

        for item in items:
            company = _parse_company(item)
            if company is None:
                continue
            # Client-side department filter (API filter is not always strict)
            if dept_filter and company.get("departement", "") != dept_filter:
                continue
            if age_max_mois and company.get("anciennete_mois", 999) > age_max_mois:
                continue
            if taille and not _match_taille(company.get("effectifs_code", ""), taille):
                continue
            results.append(company)
            if len(results) >= nb:
                break

        if len(items) < per_page:
            break
        page += 1

    return results[:nb]


def _parse_company(item):
    siege = item.get("siege", {})
    if not siege or not siege.get("siret"):
        return None

    date_creation = item.get("date_creation", "")
    anciennete_mois = 0
    if date_creation:
        try:
            d = datetime.strptime(date_creation, "%Y-%m-%d")
            anciennete_mois = max(0, (datetime.now() - d).days // 30)
        except ValueError:
            pass

    dirigeants = item.get("dirigeants", [])
    nom_dirigeant = ""
    if dirigeants:
        d = dirigeants[0]
        nom_dirigeant = f"{d.get('prenoms', '')} {d.get('nom', '')}".strip()

    dept = siege.get("departement", "").strip()
    if not dept:
        dept = _dept_from_postal(siege.get("code_postal", ""))

    return {
        "siret": siege.get("siret", ""),
        "nom": nom_dirigeant or item.get("nom_complet", ""),
        "societe": item.get("nom_complet", ""),
        "secteur": item.get("activite_principale_libelle", ""),
        "naf": item.get("activite_principale", ""),
        "ville": siege.get("libelle_commune", ""),
        "departement": dept,
        "adresse": siege.get("adresse", ""),
        "effectifs_code": item.get("tranche_effectif_salarie", ""),
        "anciennete_mois": anciennete_mois,
        "date_creation": date_creation,
        "source": "SIRENE",
        "email": "",
        "tel": "",
        "score": 0,
        "priorite": 3,
        "signaux": [],
        "message_linkedin": "",
        "message_email": "",
    }


def _dept_from_postal(code_postal):
    """Extrait le code département depuis un code postal."""
    cp = code_postal.strip()
    if not cp or len(cp) < 2:
        return ""
    if cp.startswith("97") and len(cp) >= 3:
        return cp[:3]
    if cp.startswith("98") and len(cp) >= 3:
        return cp[:3]
    return cp[:2]


def _match_taille(code, taille_filter):
    mapping = {
        "0": {"NN", "00", "01", "02", "03"},
        "1": {"11", "12", "21", "22"},
        "2": {"31", "32", "41", "42", "51"},
        "3": {"52", "53"},
    }
    return code in mapping.get(taille_filter, set())
