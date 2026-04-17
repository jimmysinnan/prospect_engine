# tests/test_sirene_dept.py
from modules.sirene import _parse_company

def test_departement_extrait_depuis_code_postal_martinique():
    item = {
        "siege": {
            "siret": "12345678900011",
            "departement": "",          # champ vide = bug actuel
            "code_postal": "97200",
            "libelle_commune": "Fort-de-France",
            "adresse": "1 rue Victor Hugo 97200 Fort-de-France",
        },
        "nom_complet": "CABINET DUPONT",
        "activite_principale_libelle": "Conseil",
        "activite_principale": "70.22Z",
        "date_creation": "2024-01-15",
        "tranche_effectif_salarie": "11",
        "dirigeants": [{"prenoms": "Jean", "nom": "DUPONT"}],
    }
    company = _parse_company(item)
    assert company["departement"] == "972"

def test_departement_extrait_depuis_code_postal_metropole():
    item = {
        "siege": {
            "siret": "12345678900012",
            "departement": "",
            "code_postal": "69003",
            "libelle_commune": "Lyon",
            "adresse": "10 rue de la Paix 69003 Lyon",
        },
        "nom_complet": "SARL MARTIN",
        "activite_principale_libelle": "Immobilier",
        "activite_principale": "68.31Z",
        "date_creation": "2023-06-01",
        "tranche_effectif_salarie": "01",
        "dirigeants": [],
    }
    company = _parse_company(item)
    assert company["departement"] == "69"

def test_departement_siege_prioritaire():
    item = {
        "siege": {
            "siret": "12345678900013",
            "departement": "972",
            "code_postal": "97200",
            "libelle_commune": "Fort-de-France",
            "adresse": "2 bd du Général de Gaulle 97200 Fort-de-France",
        },
        "nom_complet": "SARL TEST",
        "activite_principale_libelle": "Test",
        "activite_principale": "70.22Z",
        "date_creation": "2022-01-01",
        "tranche_effectif_salarie": "00",
        "dirigeants": [],
    }
    company = _parse_company(item)
    assert company["departement"] == "972"