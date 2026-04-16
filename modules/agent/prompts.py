QUALIFICATION_SYSTEM = """Tu es un assistant de prospection pour un Conseiller en Gestion de Patrimoine (CGP) indépendant. Tu gères des conversations de qualification avec des prospects B2B.

Ton rôle : analyser la réponse du prospect et décider de la prochaine action.

Règles :
- Maximum 4 échanges au total (agent + prospect)
- Ton humain, direct, sans jargon financier excessif
- Ne pas insister si le prospect décline clairement
- Proposer le RDV dès que score_maturite >= seuil_qualification
- Le message doit être prêt à envoyer tel quel (pas de [NOM], pas de placeholder)

Retourne UNIQUEMENT ce JSON (pas de markdown) :
{
  "action": "reply",
  "score_maturite": <0-100>,
  "message": "<message prêt à envoyer>",
  "raison": "<explication courte>"
}

Actions possibles :
- "reply" : continuer la qualification
- "propose_rdv" : proposer un créneau de 20 min (inclure le lien_calendly dans le message)
- "archive" : prospect pas intéressé ou échanges épuisés"""


def get_outreach_message(canal, profil, nom, secteur, ville):
    """Returns the initial outreach message for a lead.

    Args:
        canal: "email" or "linkedin"
        profil: "cgp" or other profile
        nom: prospect's first name
        secteur: prospect's sector
        ville: prospect's city

    Returns:
        Formatted outreach message ready to send
    """
    templates = {
        "linkedin": {
            "cgp": lambda n, s, v: (
                f"Bonjour {n},\n\n"
                f"Votre activité de {s} à {v} a retenu mon attention.\n\n"
                f"En tant que CGP, j'accompagne des dirigeants dans votre secteur "
                f"sur la transmission, l'optimisation fiscale et la structuration patrimoniale.\n\n"
                f"Disponible 20 minutes cette semaine ?"
            ),
        },
        "email": {
            "cgp": lambda n, s, v: (
                f"Bonjour {n},\n\n"
                f"Je vous contacte en tant que Conseiller en Gestion de Patrimoine "
                f"spécialisé dans le secteur {s}.\n\n"
                f"À votre stade, les questions de transmission, d'optimisation fiscale "
                f"et de diversification patrimoniale méritent souvent une attention particulière.\n\n"
                f"Je propose un premier échange de 20 minutes, sans engagement.\n\n"
                f"Disponible cette semaine ?\n\nCordialement"
            ),
        },
    }

    canal_templates = templates.get(canal, templates["email"])
    template_fn = canal_templates.get(profil, canal_templates.get("cgp"))
    if template_fn:
        return template_fn(nom, secteur, ville)
    return f"Bonjour {nom},\n\nJe souhaite échanger avec vous sur vos enjeux patrimoniaux.\n\nCordialement"
