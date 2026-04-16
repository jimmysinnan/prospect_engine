import requests

BODACC_API = "https://bodacc-datadica.fr/api/records/1.0/search/"


def get_signals_for_siret(siret):
    """Returns list of Bodacc signal strings for a given SIRET."""
    if not siret:
        return []

    params = {
        "dataset": "annonces-commerciales",
        "q": f"registre:{siret}",
        "rows": 5,
        "sort": "dateparution",
        "order": "desc",
    }
    try:
        resp = requests.get(BODACC_API, params=params, timeout=8)
        resp.raise_for_status()
        records = resp.json().get("records", [])
    except requests.RequestException:
        return []

    signals = []
    for record in records:
        type_ann = record.get("fields", {}).get("typeavis_lib", "").lower()
        if "cession" in type_ann:
            signals.append("Cession annoncée (Bodacc)")
        elif "immatriculation" in type_ann or "création" in type_ann:
            signals.append("Création récente (Bodacc)")
        elif "procédure" in type_ann or "redressement" in type_ann or "liquidation" in type_ann:
            signals.append("Procédure judiciaire (Bodacc)")
        elif "modification" in type_ann:
            signals.append("Modification récente (Bodacc)")

    return signals


def enrich_leads(leads):
    """Add Bodacc signals to a list of lead dicts. Modifies in-place."""
    for lead in leads:
        siret = lead.get("siret", "")
        if siret:
            bodacc_signals = get_signals_for_siret(siret)
            existing = lead.get("signaux", [])
            lead["signaux"] = existing + bodacc_signals
    return leads
