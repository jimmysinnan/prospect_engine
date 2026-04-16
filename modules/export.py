import pandas as pd
import io
import json


def leads_to_csv(leads):
    """Convert list of lead dicts to UTF-8 BOM CSV bytes (Excel-compatible)."""
    rows = []
    for lead in leads:
        signaux = lead.get("signaux", [])
        if isinstance(signaux, str):
            try:
                signaux = json.loads(signaux)
            except json.JSONDecodeError:
                signaux = []

        rows.append({
            "Score": lead.get("score", 0),
            "Nom": lead.get("nom", ""),
            "Société": lead.get("societe", ""),
            "Secteur": lead.get("secteur", ""),
            "Ville": lead.get("ville", ""),
            "SIRET": lead.get("siret", ""),
            "Email": lead.get("email", ""),
            "Téléphone": lead.get("tel", ""),
            "Source": lead.get("source", ""),
            "Ancienneté (mois)": lead.get("anciennete_mois", 0),
            "Signaux": " | ".join(signaux),
            "Statut": lead.get("status", "new"),
            "Message LinkedIn": lead.get("message_linkedin", ""),
            "Message Email": lead.get("message_email", ""),
        })

    df = pd.DataFrame(rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    return buf.getvalue().encode("utf-8-sig")
