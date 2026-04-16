import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

PLACES_TEXT_SEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"

DETAIL_FIELDS = "name,formatted_phone_number,international_phone_number,website,formatted_address,types,business_status"


def search_places(secteur, localisation, nb=50):
    """
    Search Google Places for businesses matching secteur + localisation.
    Returns list of lead dicts with tel and website when available.
    Requires GOOGLE_MAPS_API_KEY in .env.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY non définie dans .env")

    query = f"{secteur} {localisation}"
    params = {
        "query": query,
        "key": api_key,
        "language": "fr",
        "region": "fr",
    }

    results = []
    seen_ids = set()

    while len(results) < nb:
        try:
            resp = requests.get(PLACES_TEXT_SEARCH, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException:
            break

        status = data.get("status", "")
        if status not in ("OK", "ZERO_RESULTS"):
            break

        for place in data.get("results", []):
            if place.get("business_status") == "CLOSED_PERMANENTLY":
                continue
            place_id = place.get("place_id", "")
            if place_id in seen_ids:
                continue
            seen_ids.add(place_id)

            detail = _get_place_details(place_id, api_key)
            company = _parse_place(place, detail)
            results.append(company)
            if len(results) >= nb:
                break

        next_token = data.get("next_page_token")
        if not next_token or len(results) >= nb:
            break

        # Google requires a short delay before using next_page_token
        time.sleep(2)
        params = {"pagetoken": next_token, "key": api_key}

    return results[:nb]


def _get_place_details(place_id, api_key):
    """Fetch phone, website and address details for a place."""
    try:
        resp = requests.get(
            PLACES_DETAILS,
            params={"place_id": place_id, "fields": DETAIL_FIELDS, "key": api_key, "language": "fr"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("result", {})
    except requests.RequestException:
        return {}


def _parse_place(place, detail):
    """Build a lead dict from Google Places data."""
    name = detail.get("name") or place.get("name", "")
    address = detail.get("formatted_address") or place.get("formatted_address", "")
    ville = _extract_city(address)
    departement = _extract_departement(address)

    # Prefer international format for WhatsApp compatibility
    tel_raw = detail.get("international_phone_number") or detail.get("formatted_phone_number", "")
    tel = _normalize_phone(tel_raw)

    types = detail.get("types") or place.get("types", [])
    secteur_label = _types_to_label(types)

    return {
        "siret": "",
        "nom": name,
        "societe": name,
        "secteur": secteur_label,
        "naf": "",
        "ville": ville,
        "departement": departement,
        "adresse": address,
        "tel": tel,
        "email": "",
        "website": detail.get("website", ""),
        "effectifs_code": "",
        "anciennete_mois": 0,
        "date_creation": "",
        "source": "Google Maps",
        "score": 0,
        "priorite": 3,
        "signaux": [],
        "message_linkedin": "",
        "message_email": "",
        "rating": place.get("rating", 0),
        "nb_avis": place.get("user_ratings_total", 0),
    }


def _normalize_phone(tel):
    """Return phone in E.164-compatible format (e.g. +33612345678)."""
    if not tel:
        return ""
    # international_phone_number already in +XX format — just strip spaces
    tel = re.sub(r"\s+", "", tel)
    return tel


def _extract_city(address):
    """Extract city name from Google formatted address."""
    if not address:
        return ""
    parts = [p.strip() for p in address.split(",")]
    # Format: "Street, PostalCode City, Country"
    # Try to find the part with a postal code prefix
    for part in parts:
        match = re.match(r"^\d{5}\s+(.+)$", part.strip())
        if match:
            return match.group(1).strip()
    # Fallback: second-to-last part before country
    if len(parts) >= 2:
        return parts[-2].strip()
    return ""


def _extract_departement(address):
    """Extract department code from postal code in address."""
    if not address:
        return ""
    match = re.search(r"\b(\d{5})\b", address)
    if match:
        cp = match.group(1)
        # DOM-TOM: 971-976
        if cp.startswith("97"):
            return cp[:3]
        return cp[:2]
    return ""


def _types_to_label(types):
    """Convert Google place types list to a human-readable label."""
    label_map = {
        "accounting": "Expertise comptable",
        "lawyer": "Avocat",
        "real_estate_agency": "Agence immobilière",
        "insurance_agency": "Assurance",
        "finance": "Finance",
        "bank": "Banque",
        "doctor": "Médecin",
        "dentist": "Dentiste",
        "veterinary_care": "Vétérinaire",
        "restaurant": "Restaurant",
        "store": "Commerce",
        "car_dealer": "Concessionnaire",
        "beauty_salon": "Salon de beauté",
        "gym": "Salle de sport",
        "lodging": "Hôtellerie",
    }
    exclude = {"point_of_interest", "establishment", "premise", "street_address"}
    for t in types:
        if t in label_map:
            return label_map[t]
    # Return first non-generic type, formatted
    for t in types:
        if t not in exclude:
            return t.replace("_", " ").capitalize()
    return "Entreprise"
