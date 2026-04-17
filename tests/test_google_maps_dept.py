# tests/test_google_maps_dept.py
from modules.google_maps import _normalize_localisation, _extract_departement

def test_normalize_972():
    assert _normalize_localisation("972") == "Martinique"

def test_normalize_971():
    assert _normalize_localisation("971") == "Guadeloupe"

def test_normalize_973():
    assert _normalize_localisation("973") == "Guyane"

def test_normalize_974():
    assert _normalize_localisation("974") == "La Réunion"

def test_normalize_976():
    assert _normalize_localisation("976") == "Mayotte"

def test_normalize_texte_inchange():
    assert _normalize_localisation("Martinique") == "Martinique"
    assert _normalize_localisation("Fort-de-France") == "Fort-de-France"
    assert _normalize_localisation("Lyon") == "Lyon"

def test_extract_departement_martinique():
    assert _extract_departement("1 rue de la Liberté, 97200 Fort-de-France, Martinique") == "972"

def test_extract_departement_guadeloupe():
    assert _extract_departement("12 bd de la République, 97100 Basse-Terre, Guadeloupe") == "971"