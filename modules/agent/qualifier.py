import os
import json
import anthropic
from dotenv import load_dotenv
from modules.agent.prompts import QUALIFICATION_SYSTEM

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"
MAX_TURNS = 4
QUALIFICATION_SCORE_THRESHOLD = 60


def qualify_response(lead, prospect_reply, conversation_manager, calendly_url=""):
    """
    Analyzes prospect reply and decides next action.
    Returns dict: {action, score_maturite, message, raison}
    """
    turn_count = conversation_manager.get_turn_count(lead["id"])

    if turn_count >= MAX_TURNS:
        return {
            "action": "archive",
            "score_maturite": 0,
            "message": "",
            "raison": "Nombre maximum d'échanges atteint"
        }

    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    threshold = int(os.getenv("QUALIFICATION_THRESHOLD", str(QUALIFICATION_SCORE_THRESHOLD)))
    history = conversation_manager.format_history_for_prompt(lead["id"])

    user_content = json.dumps({
        "prospect": {
            "nom": lead.get("nom", ""),
            "secteur": lead.get("secteur", ""),
            "ville": lead.get("ville", ""),
            "score_initial": lead.get("score", 0),
        },
        "historique": history,
        "derniere_reponse": prospect_reply,
        "tour_actuel": turn_count,
        "tours_restants": MAX_TURNS - turn_count,
        "seuil_qualification": threshold,
        "lien_calendly": calendly_url or os.getenv("CALENDLY_URL", "https://calendly.com/votre-lien"),
    }, ensure_ascii=False)

    message = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=QUALIFICATION_SYSTEM,
        messages=[{"role": "user", "content": user_content}]
    )

    try:
        result = json.loads(message.content[0].text)
    except (json.JSONDecodeError, IndexError, KeyError):
        result = {
            "action": "reply",
            "score_maturite": 30,
            "message": "Merci pour votre retour. Seriez-vous disponible 20 minutes cette semaine ?\n\nCordialement",
            "raison": "Erreur de parsing, réponse par défaut"
        }

    return result
