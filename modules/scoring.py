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
  "message_email": "<message email 5 lignes max, personnalisé>",
  "priorite": <1|2|3>,
  "raison": "<explication 1-2 phrases>"
}

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
        "has_website": lead.get("has_website", True),
        "effectifs_code": lead.get("effectifs_code", ""),
    }, ensure_ascii=False)

    message = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": user_content}]
    )

    try:
        raw = message.content[0].text.strip()
        # Strip markdown code blocks if present (```json ... ``` or ``` ... ```)
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        result = json.loads(raw)
    except (json.JSONDecodeError, IndexError, KeyError):
        result = {
            "score": 30,
            "signaux": [],
            "message_linkedin": (
                f"Bonjour,\n\nVotre activité à {lead.get('ville', '')} a retenu "
                f"mon attention.\n\nDisponible 20 min cette semaine ?"
            ),
            "message_email": (
                f"Bonjour,\n\nJe vous contacte en tant que CGP spécialisé dans votre "
                f"secteur.\n\nDisponible pour un échange rapide ?\n\nCordialement"
            ),
            "priorite": 3,
            "raison": "Scoring par défaut (erreur de parsing)"
        }

    all_signals = list(set(lead.get("signaux", []) + result.get("signaux", [])))
    result["signaux"] = all_signals
    return result


def score_leads_batch(leads, profil_prompt=None, progress_callback=None):
    """Score a list of leads sequentially. Calls progress_callback(i, total) if provided."""
    for i, lead in enumerate(leads):
        scored = score_lead(lead, profil_prompt)
        lead.update(scored)
        if progress_callback:
            progress_callback(i + 1, len(leads))
    return leads
