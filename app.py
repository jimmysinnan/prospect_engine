import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

load_dotenv()

from modules.db import Database

ENV_FILE = Path(".env")

st.set_page_config(
    page_title="ProspectEngine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS minimal
st.markdown("""
<style>
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { padding: 8px 20px; border-radius: 8px; }
[data-testid="metric-container"] { background: #0d0f13; border: 1px solid #1a1e24; border-radius: 8px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# Init database
@st.cache_resource
def get_db():
    return Database("data/leads.db")

db = get_db()

# Session state
if "leads" not in st.session_state:
    st.session_state.leads = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "session_idx" not in st.session_state:
    st.session_state.session_idx = 0

# Header
st.markdown("## ⚡ ProspectEngine")
st.markdown("---")

# Tabs
tab_search, tab_session, tab_history, tab_settings = st.tabs([
    "🔍 Recherche & Génération",
    "⚡ Session Prospection",
    "📊 Historique",
    "⚙ Paramètres"
])

# ===== TAB SETTINGS =====
with tab_settings:
    st.subheader("Configuration")

    with st.expander("🤖 API Claude", expanded=True):
        api_key = st.text_input(
            "Clé API Claude (Anthropic)",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            type="password",
            help="Obtenir sur console.anthropic.com"
        )
        if st.button("Sauvegarder la clé Claude"):
            ENV_FILE.touch(exist_ok=True)
            set_key(str(ENV_FILE), "ANTHROPIC_API_KEY", api_key)
            st.success("Clé sauvegardée dans .env")

    with st.expander("🗺 Google Maps (téléphone & site web des leads)"):
        st.caption("Permet d'utiliser Google Maps comme source de leads avec téléphone et site web. Gratuit jusqu'à ~6 000 recherches/mois.")
        gmaps_key = st.text_input(
            "Clé API Google Maps",
            value=os.getenv("GOOGLE_MAPS_API_KEY", ""),
            type="password",
            help="console.cloud.google.com → Places API → Activer → Créer une clé"
        )
        if st.button("Sauvegarder la clé Google Maps"):
            ENV_FILE.touch(exist_ok=True)
            set_key(str(ENV_FILE), "GOOGLE_MAPS_API_KEY", gmaps_key)
            st.success("Clé sauvegardée dans .env")

    with st.expander("📧 Email (SMTP/IMAP)"):
        col1, col2 = st.columns(2)
        with col1:
            smtp_host = st.text_input("SMTP Host", value=os.getenv("SMTP_HOST", "smtp.gmail.com"))
            smtp_user = st.text_input("Email (SMTP user)", value=os.getenv("SMTP_USER", ""))
            imap_host = st.text_input("IMAP Host", value=os.getenv("IMAP_HOST", "imap.gmail.com"))
        with col2:
            smtp_port = st.text_input("SMTP Port", value=os.getenv("SMTP_PORT", "587"))
            smtp_pass = st.text_input("Mot de passe app", value=os.getenv("SMTP_PASS", ""), type="password")
            imap_folder = st.text_input("Dossier IMAP", value=os.getenv("IMAP_FOLDER", "INBOX"))
        if st.button("Sauvegarder Email"):
            ENV_FILE.touch(exist_ok=True)
            for k, v in [
                ("SMTP_HOST", smtp_host), ("SMTP_PORT", smtp_port),
                ("SMTP_USER", smtp_user), ("SMTP_PASS", smtp_pass),
                ("IMAP_HOST", imap_host), ("IMAP_FOLDER", imap_folder),
            ]:
                set_key(str(ENV_FILE), k, v)
            st.success("Config email sauvegardée")

    with st.expander("📱 WhatsApp (Twilio)"):
        col1, col2 = st.columns(2)
        with col1:
            twilio_sid = st.text_input("Account SID", value=os.getenv("TWILIO_ACCOUNT_SID", ""), type="password")
            twilio_from = st.text_input("Numéro expéditeur", value=os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"))
        with col2:
            twilio_token = st.text_input("Auth Token", value=os.getenv("TWILIO_AUTH_TOKEN", ""), type="password")
        if st.button("Sauvegarder WhatsApp"):
            ENV_FILE.touch(exist_ok=True)
            for k, v in [
                ("TWILIO_ACCOUNT_SID", twilio_sid), ("TWILIO_AUTH_TOKEN", twilio_token),
                ("TWILIO_WHATSAPP_FROM", twilio_from),
            ]:
                set_key(str(ENV_FILE), k, v)
            st.success("Config WhatsApp sauvegardée")

    with st.expander("🎯 Profil cible & Seuil de qualification"):
        calendly = st.text_input("Lien Calendly", value=os.getenv("CALENDLY_URL", ""))
        threshold = st.slider("Seuil de qualification (score)", 0, 100, int(os.getenv("QUALIFICATION_THRESHOLD", "60")))
        profil_prompt = st.text_area(
            "Description du profil cible (injecté dans le prompt de scoring)",
            value="Cabinet CGP indépendant — Dirigeant 45-65 ans, patrimoine >500K€, secteurs libéraux et PME",
            height=80
        )
        if st.button("Sauvegarder profil"):
            ENV_FILE.touch(exist_ok=True)
            set_key(str(ENV_FILE), "CALENDLY_URL", calendly)
            set_key(str(ENV_FILE), "QUALIFICATION_THRESHOLD", str(threshold))
            set_key(str(ENV_FILE), "PROFIL_PROMPT", profil_prompt)
            st.success("Profil sauvegardé")

# ===== TAB SEARCH =====
with tab_search:
    from modules.sirene import search_companies
    from modules.bodacc import enrich_leads
    from modules.scoring import score_leads_batch
    from modules.export import leads_to_csv
    from modules.google_maps import search_places
    import json
    from datetime import date

    col_form, col_stats = st.columns([2, 1])

    with col_form:
        st.subheader("🎯 Configurer la recherche")
        NAF_PRESETS = {
            "— Saisir manuellement —": "",
            "68.31Z — Agences immobilières": "agence immobilière",
            "56.10A — Restaurants traditionnels": "restaurant",
            "86.21Z — Médecins généralistes": "médecin généraliste",
            "86.23Z — Dentistes": "dentiste",
            "71.11Z — Architectes": "architecte",
            "70.22Z — Conseil en gestion / coaching": "conseil gestion",
            "85.59B — Organismes de formation": "organisme formation",
            "62.01Z — Développeurs / SSII": "développeur informatique",
            "96.02A — Coiffure": "salon coiffure",
            "93.13Z — Salles de sport / fitness": "salle de sport",
            "55.10Z — Hôtels": "hôtel",
            "43.21A — Électriciens": "électricien",
            "43.22A — Plombiers": "plombier",
            "69.20Z — Experts comptables": "expert comptable",
            "66.22Z — Agents généraux d'assurance": "assurance",
            "68.20A — Location immobilière": "agence immobilière location",
        }
        with st.form("search_form"):
            # Source selector
            has_gmaps = bool(os.getenv("GOOGLE_MAPS_API_KEY", ""))
            source_options = ["SIRENE (registre officiel — sans contacts)"]
            if has_gmaps:
                source_options.append("Google Maps (téléphone + site web disponibles)")
            source = st.radio(
                "Source de données",
                source_options,
                help="Google Maps donne le téléphone et le site web des entreprises qui ont une fiche Google."
            )
            use_gmaps = "Google Maps" in source

            naf_choice = st.selectbox(
                "Code NAF (optionnel)",
                options=list(NAF_PRESETS.keys()),
                index=0,
                help="Sélectionne un secteur prédéfini ou laisse 'Saisir manuellement'"
            )
            secteur_default = NAF_PRESETS[naf_choice]
            secteur = st.text_input(
                "Secteur d'activité",
                value=secteur_default,
                placeholder="Ex: expert comptable, notaire, agence immobilière…"
            )
            col1, col2 = st.columns(2)
            with col1:
                if use_gmaps:
                    localisation = st.text_input("Localisation", placeholder="Ex: Martinique, Fort-de-France, 972…")
                else:
                    departement = st.text_input("Département(s)", placeholder="Ex: 972, 69, 75")
            with col2:
                nb_leads = st.selectbox("Nombre de leads", [25, 50, 100, 150, 200], index=2)

            if not use_gmaps:
                col3, col4 = st.columns(2)
                with col3:
                    taille = st.selectbox("Taille entreprise", ["Toutes", "TPE (0-9)", "PME (10-49)", "ETI (50-249)", "Grande (250+)"], index=0)
                with col4:
                    age_max = st.selectbox("Ancienneté max", ["Toutes", "3 mois", "6 mois", "1 an", "3 ans", "5 ans"], index=0)
                use_bodacc = st.checkbox("Enrichir avec Bodacc (signaux de cession/création)", value=True)
            else:
                taille = "Toutes"
                age_max = "Toutes"
                use_bodacc = False
                st.caption("ℹ️ Google Maps fournit téléphone (~70%) et site web (~60%) pour les entreprises avec une fiche Google active.")

            submitted = st.form_submit_button("⚡ Générer les leads", use_container_width=True)

    with col_stats:
        st.subheader("📊 Stats session")
        leads_count = len(st.session_state.leads)
        hot = sum(1 for l in st.session_state.leads if l.get("score", 0) >= 70)
        signals = sum(len(l.get("signaux", [])) for l in st.session_state.leads)
        st.metric("Leads générés", leads_count)
        st.metric("Leads chauds (>70)", hot)
        st.metric("Signaux détectés", signals)
        if st.session_state.leads:
            csv_bytes = leads_to_csv(st.session_state.leads)
            st.download_button(
                "📥 Exporter CSV",
                data=csv_bytes,
                file_name=f"leads_{date.today()}.csv",
                mime="text/csv",
                use_container_width=True
            )

    if submitted:
        taille_map = {"Toutes": None, "TPE (0-9)": "0", "PME (10-49)": "1", "ETI (50-249)": "2", "Grande (250+)": "3"}
        age_map = {"Toutes": None, "3 mois": 3, "6 mois": 6, "1 an": 12, "3 ans": 36, "5 ans": 60}

        if use_gmaps:
            progress = st.progress(0, text="Recherche Google Maps…")
            try:
                with st.spinner("Interrogation Google Maps…"):
                    leads_raw = search_places(secteur, localisation, nb=nb_leads)
            except ValueError as e:
                st.error(str(e))
                st.stop()
            if not leads_raw:
                st.error("Aucun résultat Google Maps. Essayez une localisation plus large (ex: Martinique au lieu de Fort-de-France).")
                st.stop()
            has_tel = sum(1 for l in leads_raw if l.get("tel"))
            progress.progress(40, text=f"{len(leads_raw)} entreprises trouvées — {has_tel} avec téléphone. Scoring IA…")
        else:
            progress = st.progress(0, text="Interrogation SIRENE…")
            with st.spinner("Recherche en cours…"):
                leads_raw = search_companies(
                    secteur=secteur,
                    departement=departement,
                    nb=nb_leads,
                    taille=taille_map[taille],
                    age_max_mois=age_map[age_max]
                )
            if not leads_raw:
                st.error("Aucun résultat SIRENE. Essayez un secteur plus large ou un autre département.")
                st.stop()
            progress.progress(30, text=f"{len(leads_raw)} entreprises trouvées. Enrichissement Bodacc…")
            if use_bodacc:
                with st.spinner("Enrichissement Bodacc…"):
                    leads_raw = enrich_leads(leads_raw)

        progress.progress(55, text="Scoring IA (Claude Haiku)…")

        api_key_check = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key_check:
            st.error("Clé API Claude manquante. Configurez-la dans l'onglet Paramètres.")
            st.stop()

        scored_leads = []
        score_progress = st.progress(0, text="Scoring en cours…")

        def on_progress(i, total):
            score_progress.progress(i / total, text=f"Scoring {i}/{total}…")

        try:
            scored_leads = score_leads_batch(leads_raw, progress_callback=on_progress)
        except Exception as e:
            st.error(f"Erreur scoring : {e}")
            st.stop()

        # Save to DB
        session_id = db.create_session()
        st.session_state.session_id = session_id
        for lead in scored_leads:
            lead["id"] = db.insert_lead(session_id, lead)

        db.update_session(session_id, nb_leads=len(scored_leads))
        st.session_state.leads = scored_leads
        progress.progress(100, text="✅ Terminé !")
        st.rerun()

    if st.session_state.leads:
        from modules.enrichment import enrich_leads_batch

        leads_with_website = [l for l in st.session_state.leads if l.get("website")]
        if leads_with_website:
            col_enrich1, col_enrich2 = st.columns([3, 1])
            with col_enrich1:
                st.caption(f"💡 {len(leads_with_website)} leads ont un site web — enrichissement disponible (email, tél, réseaux, maturité digitale)")
            with col_enrich2:
                if st.button("🔍 Enrichir les leads", use_container_width=True):
                    enrich_progress = st.progress(0, text="Enrichissement web…")
                    def on_enrich(i, total):
                        enrich_progress.progress(i / total, text=f"Enrichissement {i}/{total}…")
                    enrich_leads_batch(st.session_state.leads, progress_callback=on_enrich)
                    enrich_progress.progress(1.0, text="✅ Enrichissement terminé")
                    st.rerun()

        leads = st.session_state.leads
        st.subheader(f"Résultats — {len(leads)} leads")

        filter_col = st.columns(6)
        with filter_col[0]:
            show_filter = st.selectbox("Filtrer", ["Tous", "Chauds (>70)", "Tièdes (45-70)", "Froids (<45)", "Récents (<12m)"])

        filtered = leads
        if show_filter == "Chauds (>70)":
            filtered = [l for l in leads if l.get("score", 0) >= 70]
        elif show_filter == "Tièdes (45-70)":
            filtered = [l for l in leads if 45 <= l.get("score", 0) < 70]
        elif show_filter == "Froids (<45)":
            filtered = [l for l in leads if l.get("score", 0) < 45]
        elif show_filter == "Récents (<12m)":
            filtered = [l for l in leads if l.get("anciennete_mois", 999) < 12]

        for i, lead in enumerate(filtered):
            score = lead.get("score", 0)
            score_color = "🔴" if score >= 70 else "🟡" if score >= 45 else "🔵"
            signaux = lead.get("signaux", [])
            if isinstance(signaux, str):
                try:
                    signaux = json.loads(signaux)
                except Exception:
                    signaux = []

            with st.expander(f"{score_color} **{score}** — {lead.get('nom', '')} · {lead.get('societe', '')} · {lead.get('ville', '')}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Secteur :** {lead.get('secteur', '')}")
                    st.markdown(f"**Ancienneté :** {lead.get('anciennete_mois', 0)} mois")
                    st.markdown(f"**Source :** {lead.get('source', '')}")
                    if lead.get("digital_score") is not None:
                        st.markdown(f"**Maturité digitale :** {lead.get('digital_maturity_label', '')} ({lead.get('digital_score', 0)}/100)")
                    if lead.get("socials"):
                        socials = lead.get("socials", {})
                        social_links = " · ".join(f"[{k.capitalize()}]({v})" for k, v in socials.items())
                        st.markdown(f"**Réseaux :** {social_links}")
                    st.markdown(f"**Signaux :** {' · '.join(signaux) if signaux else '—'}")
                    if lead.get("tel"):
                        st.markdown(f"**Téléphone :** {lead.get('tel')}")
                    if lead.get("website"):
                        st.markdown(f"**Site web :** {lead.get('website')}")
                with col_b:
                    st.markdown(f"**SIRET :** `{lead.get('siret', '') or '—'}`")
                    st.markdown(f"**Raison :** {lead.get('raison', '')}")
                    if lead.get("rating"):
                        st.markdown(f"**Google :** ⭐ {lead.get('rating')} ({lead.get('nb_avis', 0)} avis)")

                st.markdown("**Message LinkedIn :**")
                st.text_area("", value=lead.get("message_linkedin", ""), height=100,
                             key=f"msg_li_{lead.get('siret', '')}_{i}", label_visibility="collapsed")

                email_tabs = st.tabs(["✉️ Email Direct", "📖 Storytelling", "💰 ROI"])
                with email_tabs[0]:
                    st.text_area("", value=lead.get("email_variante_1", ""), height=120,
                                 key=f"em1_{lead.get('siret', '')}_{i}", label_visibility="collapsed")
                with email_tabs[1]:
                    st.text_area("", value=lead.get("email_variante_2", ""), height=120,
                                 key=f"em2_{lead.get('siret', '')}_{i}", label_visibility="collapsed")
                with email_tabs[2]:
                    st.text_area("", value=lead.get("email_variante_3", ""), height=120,
                                 key=f"em3_{lead.get('siret', '')}_{i}", label_visibility="collapsed")

# ===== TAB SESSION =====
with tab_session:
    import json
    import time

    if not st.session_state.leads:
        st.info("Générez des leads depuis l'onglet Recherche pour lancer une session.")
        st.stop()

    leads = st.session_state.leads
    idx = st.session_state.session_idx

    col_queue, col_work = st.columns([1, 3])

    with col_queue:
        st.subheader(f"File d'attente ({idx}/{min(len(leads), 50)})")
        for i, lead in enumerate(leads[:50]):
            score = lead.get("score", 0)
            icon = "🔴" if score >= 70 else "🟡" if score >= 45 else "🔵"
            status = lead.get("status", "new")
            status_icon = "✓" if status == "sent" else "⏰" if status == "later" else "→" if status == "skip" else "○"
            label = f"{status_icon} {icon} {score} — {lead.get('nom', '')}"
            if st.button(label, key=f"q_{i}", use_container_width=True):
                st.session_state.session_idx = i
                st.rerun()

    with col_work:
        if idx >= len(leads):
            st.success("🎉 Session terminée ! Tous les prospects ont été traités.")
        else:
            lead = leads[idx]
            score = lead.get("score", 0)
            signaux = lead.get("signaux", [])
            if isinstance(signaux, str):
                try:
                    signaux = json.loads(signaux)
                except Exception:
                    signaux = []

            st.markdown(f"### {lead.get('nom', '')} — {lead.get('societe', '')}")
            st.markdown(f"📍 {lead.get('ville', '')} · {lead.get('secteur', '')} · Score **{score}**")

            c1, c2, c3 = st.columns(3)
            c1.metric("Ancienneté", f"{lead.get('anciennete_mois', 0)} mois")
            c2.metric("Source", lead.get("source", ""))
            c3.metric("Priorité", f"P{lead.get('priorite', 3)}")

            if signaux:
                st.markdown("**Signaux :** " + " · ".join(signaux))

            st.markdown(f"**Analyse IA :** {lead.get('raison', '')}")

            # Mode toggle
            mode = st.radio("Mode", ["Manuel", "Agent IA"], key=f"mode_{idx}", horizontal=True)

            if mode == "Manuel":
                canal = st.radio("Canal", ["LinkedIn", "Email"], horizontal=True, key=f"canal_{idx}")
                msg_key = "message_linkedin" if canal == "LinkedIn" else "message_email"
                msg = st.text_area(
                    f"Message {canal}",
                    value=lead.get(msg_key, ""),
                    height=140,
                    key=f"msg_{idx}"
                )

                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                with col_s1:
                    if st.button("✓ Envoyé", key=f"sent_{idx}", use_container_width=True):
                        leads[idx]["status"] = "sent"
                        db.update_lead_status(lead.get("id", 0), "sent")
                        db.update_session(st.session_state.session_id,
                            nb_sent=sum(1 for l in leads if l.get("status") == "sent"))
                        st.session_state.session_idx = min(idx + 1, len(leads) - 1)
                        st.rerun()
                with col_s2:
                    if st.button("⏰ Plus tard", key=f"later_{idx}", use_container_width=True):
                        leads[idx]["status"] = "later"
                        db.update_lead_status(lead.get("id", 0), "later")
                        st.session_state.session_idx = min(idx + 1, len(leads) - 1)
                        st.rerun()
                with col_s3:
                    if st.button("→ Passer", key=f"skip_{idx}", use_container_width=True):
                        leads[idx]["status"] = "skip"
                        db.update_lead_status(lead.get("id", 0), "skip")
                        st.session_state.session_idx = min(idx + 1, len(leads) - 1)
                        st.rerun()
                with col_s4:
                    if st.button("Suivant ▶", key=f"next_{idx}", use_container_width=True):
                        st.session_state.session_idx = min(idx + 1, len(leads) - 1)
                        st.rerun()

            else:
                from modules.agent.conversation import ConversationManager
                from modules.agent.qualifier import qualify_response
                from modules.agent.prompts import get_outreach_message
                from modules.agent.channels import email as email_channel
                from modules.agent.channels import whatsapp as wa_channel

                conv_manager = ConversationManager(db)
                lead_id = lead.get("id", 0)
                history = conv_manager.get_history(lead_id)
                lead_status = lead.get("status", "new")

                # Canal
                has_tel = bool(lead.get("tel", ""))
                canal_options = ["Email", "WhatsApp"] if has_tel else ["Email"]
                canal_agent = st.radio("Canal agent", canal_options, horizontal=True, key=f"ca_{idx}")

                # Display conversation history
                if history:
                    st.markdown("**Historique de conversation :**")
                    for msg in history:
                        role_label = "**CGP (agent) :**" if msg["role"] == "agent" else "**Prospect :**"
                        score_label = f" _(maturité: {msg['score_maturite']})_" if msg["role"] == "agent" and msg["score_maturite"] > 0 else ""
                        st.markdown(f"{role_label}{score_label}")
                        st.info(msg["message"])

                # If conversation not started
                if lead_status == "new":
                    msg_preview = get_outreach_message(
                        canal_agent.lower(), "cgp",
                        lead.get("nom", ""), lead.get("secteur", ""), lead.get("ville", "")
                    )
                    st.markdown("**Message d'accroche généré :**")
                    st.text_area("", value=msg_preview, height=120, key=f"agent_preview_{idx}", label_visibility="collapsed")

                    if st.button("🚀 Envoyer via agent", key=f"agent_start_{idx}", use_container_width=True):
                        try:
                            if canal_agent == "Email" and lead.get("email"):
                                email_channel.send_email(lead["email"], f"Présentation — {lead.get('societe', '')}", msg_preview)
                            elif canal_agent == "WhatsApp" and lead.get("tel"):
                                wa_channel.send_whatsapp(lead["tel"], msg_preview)
                            else:
                                st.warning("Aucun contact disponible pour ce lead.")
                                st.stop()
                            conv_manager.start_conversation(lead_id, canal_agent.lower(), msg_preview)
                            leads[idx]["status"] = "sent"
                            leads[idx]["mode"] = "agent"
                            db.update_session(st.session_state.session_id,
                                nb_sent=sum(1 for l in leads if l.get("status") == "sent"))
                            st.success("Message envoyé ! L'agent surveille les réponses.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur d'envoi : {e}")

                # If waiting for reply
                elif lead_status == "sent" and lead.get("mode") == "agent":
                    st.info("⏳ En attente de réponse du prospect…")

                    # Manual reply input (for testing / if no auto-polling)
                    with st.expander("📥 Saisir une réponse manuellement (test ou réponse reçue)"):
                        manual_reply = st.text_area("Réponse du prospect", key=f"manual_reply_{idx}")
                        if st.button("Traiter cette réponse", key=f"process_reply_{idx}"):
                            if manual_reply.strip():
                                conv_manager.add_prospect_reply(lead_id, canal_agent.lower(), manual_reply)
                                calendly_url = os.getenv("CALENDLY_URL", "")
                                result = qualify_response(lead, manual_reply, conv_manager, calendly_url)

                                conv_manager.add_agent_reply(lead_id, canal_agent.lower(), result["message"], result["score_maturite"])

                                if result["action"] == "propose_rdv":
                                    new_status = "qualified"
                                elif result["action"] == "archive":
                                    new_status = "skip"
                                else:
                                    new_status = "sent"

                                # Send the agent's response
                                if result["message"] and new_status != "skip":
                                    try:
                                        if canal_agent == "Email" and lead.get("email"):
                                            email_channel.send_email(lead["email"], "Re: Présentation", result["message"])
                                        elif canal_agent == "WhatsApp" and lead.get("tel"):
                                            wa_channel.send_whatsapp(lead["tel"], result["message"])
                                    except Exception as e:
                                        st.warning(f"Réponse enregistrée mais envoi échoué : {e}")

                                leads[idx]["status"] = new_status
                                db.update_lead_status(lead_id, new_status)
                                if new_status == "qualified":
                                    db.update_session(st.session_state.session_id,
                                        nb_qualified=sum(1 for l in leads if l.get("status") == "qualified"))
                                st.success(f"Action : {result['action']} — Score maturité : {result['score_maturite']}")
                                st.rerun()

                    if st.button("✋ Je prends la main (mode manuel)", key=f"takeover_{idx}"):
                        leads[idx]["mode"] = "manual"
                        db.update_lead_status(lead_id, lead_status, mode="manual")
                        st.rerun()

                elif lead_status == "qualified":
                    st.success("🎯 Lead qualifié — RDV proposé !")
                    if st.button("Suivant ▶", key=f"agent_next_{idx}", use_container_width=True):
                        st.session_state.session_idx = min(idx + 1, len(leads) - 1)
                        st.rerun()

# ===== TAB HISTORY =====
with tab_history:
    import json

    sessions = db.get_all_sessions()

    if not sessions:
        st.info("Aucune session enregistrée. Générez des leads pour commencer.")
    else:
        st.subheader(f"📊 {len(sessions)} sessions")

        for session in sessions:
            created = session.get("created_at", "")[:16]
            nb = session.get("nb_leads", 0)
            sent = session.get("nb_sent", 0)
            qualified = session.get("nb_qualified", 0)
            duree = session.get("duree_sec", 0)
            duree_fmt = f"{duree // 60}m{duree % 60:02d}s" if duree else "—"

            with st.expander(f"📅 {created} — {nb} leads · {sent} envois · {qualified} qualifiés · {duree_fmt}"):
                leads_session = db.get_leads_by_session(session["id"])

                if not leads_session:
                    st.write("Aucun lead dans cette session.")
                    continue

                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Leads", nb)
                col_m2.metric("Envois", sent)
                col_m3.metric("Qualifiés", qualified)

                # Filter by status
                status_filter = st.selectbox(
                    "Filtrer par statut",
                    ["Tous", "Envoyés", "Qualifiés", "Plus tard", "Passés"],
                    key=f"hist_filter_{session['id']}"
                )
                status_map = {"Tous": None, "Envoyés": "sent", "Qualifiés": "qualified",
                              "Plus tard": "later", "Passés": "skip"}
                filtered_leads = leads_session
                if status_map[status_filter]:
                    filtered_leads = [l for l in leads_session if l.get("status") == status_map[status_filter]]

                for lead in filtered_leads:
                    score = lead.get("score", 0)
                    icon = "🔴" if score >= 70 else "🟡" if score >= 45 else "🔵"
                    status = lead.get("status", "new")
                    mode_badge = "🤖" if lead.get("mode") == "agent" else "👤"
                    signaux = lead.get("signaux", [])
                    if isinstance(signaux, str):
                        try:
                            signaux = json.loads(signaux)
                        except Exception:
                            signaux = []

                    with st.expander(f"{icon} {score} {mode_badge} — {lead.get('nom', '')} · {lead.get('ville', '')} [{status}]"):
                        conversations = db.get_conversations(lead["id"])

                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**Secteur :** {lead.get('secteur', '')}")
                            st.markdown(f"**Email :** {lead.get('email', '—')}")
                            st.markdown(f"**Signaux :** {' · '.join(signaux) if signaux else '—'}")
                        with c2:
                            st.markdown(f"**SIRET :** `{lead.get('siret', '')}`")
                            st.markdown(f"**Mode :** {'Agent IA 🤖' if lead.get('mode') == 'agent' else 'Manuel 👤'}")

                        if conversations:
                            st.markdown("**Conversation :**")
                            for msg in conversations:
                                role = "**Agent :**" if msg["role"] == "agent" else "**Prospect :**"
                                score_m = f" _(maturité: {msg['score_maturite']})_" if msg.get("score_maturite", 0) > 0 else ""
                                ts = msg.get("timestamp", "")[:16]
                                st.markdown(f"{role} {ts}{score_m}")
                                st.info(msg["message"])
