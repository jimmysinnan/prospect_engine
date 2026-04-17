import os
import json
import re
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """Tu es un expert en qualification de leads pour conseillers en gestion de patrimoine (CGP) indépendants.

Pour chaque prospect, évalue sa pertinence comme client potentiel pour un CGP. Retourne UNIQUEMENT ce JSON :
{
  "score": <0-100>,
  "signaux": [<liste de strings>],
  "message_linkedin": "<message court 3 lignes max, humain, sans jargon>",
  "email_variante_1": "<Email direct — Objet: <sujet>\\n\\n<corps 5 lignes, ton factuel>",
  "email_variante_2": "<Email storytelling — Objet: <sujet>\\n\\n<corps 5 lignes, ton narratif>",
  "email_variante_3": "<Email ROI — Objet: <sujet>\\n\\n<corps 5 lignes, axé gain concret>",
  "priorite": <1|2|3>,
  "raison": "<explication 1-2 phrases>"
}

Format email : commencer par "Objet: <sujet>\\n\\n<corps>"

Critères de scoring :
- Dirigeant TPE/PME secteur libéral/conseil/immobilier = base favorable
- Ancienneté < 12 mois = +20 points (structuration patrimoniale urgente)
- anciennete_mois == 0 = traiter comme très récent
- Cession Bodacc = +25 points (liquidité imminente)
- Absence site web (has_website=false) = +10 points
- CA estimé > 500K (code effectif >= 11) = +15 points
- Secteur gestion de patrimoine/CGP = -15 points (déjà servi)

Messages : directs, humains, 1ère personne, jamais "j'espère que vous allez bien"."""


def score_lead(lead, profil_prompt=None):
    """Score a single lead using Claude Haiku. Returns dict with scoring fields."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY non définie dans .env")

    client = anthropic.Anthropic(api_key=api_key)
    system = profil_prompt or SYSTEM_PROMPT

    user_content = json.dumps({
        "siret": lead.get("siret", ""),
        "societe": lead.get("societe", ""),
        "secteur": lead.get("secteur", ""),
        "ville": lead.get("ville", ""),
        "anciennete_mois": lead.get("anciennete_mois", 0),
        "signaux_bodacc": lead.get("signaux", []),
        "has_website": bool(lead.get("website", "")),
        "effectifs_code": lead.get("effectifs_code", ""),
    }, ensure_ascii=False)

    message = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": user_content}]
    )

    raw = message.content[0].text.strip()
    result = _parse_score_response(raw, lead)
    all_signals = list(set(lead.get("signaux", []) + result.get("signaux", [])))
    result["signaux"] = all_signals
    return result


def _parse_score_response(raw, lead):
    """Parse Claude response. Returns scored dict with 3 email variants."""
    try:
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        result = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError, KeyError):
        return _default_score(lead)

    # Backward-compat : si message_email présent mais pas les variantes
    if "message_email" in result and "email_variante_1" not in result:
        result["email_variante_1"] = result.pop("message_email")
    if "email_variante_1" not in result:
        result["email_variante_1"] = ""
    if "email_variante_2" not in result:
        result["email_variante_2"] = ""
    if "email_variante_3" not in result:
        result["email_variante_3"] = ""

    return result


def _default_score(lead):
    ville = lead.get("ville", "")
    societe = lead.get("societe", "")
    return {
        "score": 30,
        "signaux": [],
        "message_linkedin": (
            f"Bonjour,\n\nVotre activité à {ville} a retenu "
            f"mon attention.\n\nDisponible 20 min cette semaine ?"
        ),
        "email_variante_1": (
            f"Objet: Optimisation patrimoniale — {societe}\n\n"
            f"Bonjour,\n\nJe suis CGP spécialisé dans votre secteur à {ville}.\n"
            f"J'aimerais échanger 20 minutes sur votre situation.\n\nCordialement"
        ),
        "email_variante_2": (
            f"Objet: Une question rapide sur {societe}\n\n"
            f"Bonjour,\n\nEn parcourant les entreprises de {ville}, votre activité a retenu mon attention.\n"
            f"Beaucoup de dirigeants dans votre secteur ignorent des optimisations simples.\n\nDisponible cette semaine ?"
        ),
        "email_variante_3": (
            f"Objet: Économiser sur votre fiscalité — {societe}\n\n"
            f"Bonjour,\n\nEn tant que CGP, j'aide des dirigeants comme vous à réduire leur charge fiscale.\n"
            f"Résultat moyen : 8 000€/an récupérés. Échange de 20 min ?\n\nCordialement"
        ),
        "priorite": 3,
        "raison": "Scoring par défaut (erreur de parsing)"
    }


def score_leads_batch(leads, profil_prompt=None, progress_callback=None):
    """Score a list of leads sequentially. Calls progress_callback(i, total) if provided."""
    for i, lead in enumerate(leads):
        scored = score_lead(lead, profil_prompt)
        lead.update(scored)
        if progress_callback:
            progress_callback(i + 1, len(leads))
    return leads