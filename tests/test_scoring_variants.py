# tests/test_scoring_variants.py
from modules.scoring import _parse_score_response, _default_score

def test_parse_score_response_avec_variantes():
    raw = """{
      "score": 75,
      "signaux": ["création récente"],
      "message_linkedin": "Bonjour Jean,\\n\\nVotre cabinet retient mon attention.",
      "email_variante_1": "Objet: Optimisation patrimoine\\n\\nBonjour Jean...",
      "email_variante_2": "Objet: Une question rapide\\n\\nJ'ai vu que votre cabinet...",
      "email_variante_3": "Objet: Gain concret pour votre activité\\n\\nEn tant que CGP...",
      "priorite": 1,
      "raison": "Score élevé — création récente"
    }"""
    result = _parse_score_response(raw, {})
    assert result["score"] == 75
    assert result["email_variante_1"].startswith("Objet:")
    assert result["email_variante_2"].startswith("Objet:")
    assert result["email_variante_3"].startswith("Objet:")

def test_parse_score_response_fallback_variantes():
    """Si l'IA ne retourne qu'un message_email, on le copie dans variante_1."""
    raw = """{
      "score": 50,
      "signaux": [],
      "message_linkedin": "Bonjour,",
      "message_email": "Bonjour, je vous contacte...",
      "priorite": 2,
      "raison": "Score moyen"
    }"""
    result = _parse_score_response(raw, {"ville": "Lyon"})
    assert "email_variante_1" in result
    assert result["email_variante_1"] != ""

def test_default_score_has_variantes():
    result = _default_score({"ville": "Fort-de-France", "societe": "Cabinet Test"})
    assert "email_variante_1" in result
    assert "email_variante_2" in result
    assert "email_variante_3" in result