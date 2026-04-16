# ProspectEngine — Design Spec
**Date :** 2026-04-16  
**Auteur :** Jimmy Sinnan  
**Statut :** Approuvé

---

## 1. Objectif

Convertir la démo HTML `prospect_engine.html` en application Python/Streamlit fonctionnelle avec :
- Vraies données publiques françaises (SIRENE, Bodacc)
- Scoring IA réel via Claude API
- Agent conversationnel multi-canal (Email + WhatsApp) pour la qualification de leads
- Déploiement client en double-clic (Windows `.bat`)
- Historique local SQLite — zéro cloud, zéro abonnement SaaS

---

## 2. Périmètre

### Inclus
- Recherche de leads via API publiques (SIRENE sans clé, Bodacc flux data.gouv.fr)
- Scoring et génération de messages via Claude Haiku
- Session de prospection manuelle (reprise du flux HTML)
- Agent IA conversationnel : Email (SMTP/IMAP) + WhatsApp (Twilio)
- Toggle Manuel / Agent IA par lead
- Historique des conversations en SQLite
- Export CSV
- Launcher `START.bat` avec auto-installation des dépendances

### Exclu
- Intégration CRM (HubSpot, O2S) — prévu v2
- Déploiement cloud — hors scope (outil local propriétaire client)
- Interface mobile native
- WhatsApp Business API directe (on passe par Twilio)

---

## 3. Architecture

```
prospect_engine/
├── START.bat                  ← launcher Windows (double-clic client)
├── START.command              ← launcher Mac (optionnel)
├── requirements.txt
├── .env                       ← secrets locaux (jamais commités)
├── .gitignore
├── app.py                     ← point d'entrée Streamlit
├── modules/
│   ├── sirene.py              ← API recherche-entreprises.api.gouv.fr
│   ├── bodacc.py              ← flux Bodacc via data.gouv.fr
│   ├── scoring.py             ← Claude Haiku — score + signaux + message
│   ├── db.py                  ← SQLite CRUD
│   ├── export.py              ← génération CSV
│   └── agent/
│       ├── conversation.py    ← gestion multi-tours (historique)
│       ├── qualifier.py       ← Claude API — analyse réponse + prochaine action
│       ├── prompts.py         ← scripts de conversation (3 phases)
│       └── channels/
│           ├── email.py       ← SMTP (envoi) + IMAP (lecture)
│           └── whatsapp.py    ← Twilio API (envoi + webhook)
└── data/
    └── leads.db               ← base SQLite locale
```

---

## 4. Sources de données

### 4.1 SIRENE — API recherche-entreprises.api.gouv.fr
- **URL :** `https://recherche-entreprises.api.gouv.fr/search`
- **Clé requise :** non (API publique)
- **Limite :** pas de rate limit documenté (usage raisonnable)
- **Paramètres utilisés :** `q` (secteur/APE), `departement`, `tranche_effectif_salarie`, `date_creation_min/max`, `nombre`
- **Données retournées :** SIRET, raison sociale, adresse, NAF, date création, effectifs, dirigeants

### 4.2 Bodacc — data.gouv.fr
- **URL :** `https://bodacc-datadica.fr/api/records/1.0/search/`
- **Dataset :** `annonces-commerciales`
- **Clé requise :** non
- **Filtre :** par SIRET ou par ville/département + date récente
- **Données retournées :** type d'annonce (création, cession, procédure), date, montant si disponible

---

## 5. Scoring IA

**Modèle :** `claude-haiku-4-5-20251001` (coût ~0.001€/lead)

**Input JSON par lead :**
```json
{
  "siret": "...",
  "societe": "...",
  "secteur": "...",
  "ville": "...",
  "anciennete_mois": 14,
  "ca_estime": 850,
  "signaux_bodacc": ["création récente", "cession annoncée"],
  "has_website": false,
  "profil_cible": "cgp"
}
```

**Output JSON attendu :**
```json
{
  "score": 82,
  "signaux": ["Création récente", "Sans site web", "Cession Bodacc"],
  "message_linkedin": "...",
  "message_email": "...",
  "priorite": 1,
  "raison": "Dirigeant en phase de structuration patrimoniale..."
}
```

**Prompt système (configurable dans `prompts.py`) :**  
Adapté au profil cible du cabinet (CGP par défaut). Injecte les critères de qualification dans le system prompt.

---

## 6. Agent conversationnel

### 6.1 Phases de conversation

**Phase 1 — Accroche (message 1)**
- Généré par `scoring.py` lors de la création du lead
- Personnalisé : prénom, secteur, ville, signal principal
- Ton : direct, humain, 3 lignes max, pas de jargon financier
- Canal choisi automatiquement : WhatsApp si téléphone connu, Email sinon

**Phase 2 — Qualification (messages 2–4 maximum)**
- `qualifier.py` lit la réponse du prospect via IMAP ou webhook Twilio
- Claude analyse : sentiment, intention, objections, signaux positifs
- Décide de l'action : relancer / approfondir / proposer RDV / archiver
- Score de maturité mis à jour à chaque échange (0→100)

**Phase 3 — Conversion (score ≥ 60)**
- Propose un créneau de 20 minutes
- Envoie lien Calendly (configuré dans Paramètres)
- Lead marqué "Qualifié — RDV proposé"
- Notification dans l'interface client

**Sortie de conversation :**
- "pas intéressé" / "ne pas contacter" détecté → archivage automatique, statut "Exclu"
- 4 échanges sans réponse → statut "Inactif"
- Reprise manuelle possible à tout moment (bouton "Je prends la main")

### 6.2 Canal Email

- **Envoi :** SMTP standard (Gmail, Outlook, domaine pro — configurable)
- **Réception :** IMAP polling toutes les 15 minutes (thread background Streamlit)
- **Thread :** réponses liées au lead par `Message-ID` / `In-Reply-To`
- **Config `.env` :** `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `IMAP_HOST`, `IMAP_FOLDER`

### 6.3 Canal WhatsApp (Twilio)

- **Envoi :** `twilio.rest.Client` → `messages.create()`
- **Réception :** polling Twilio API toutes les 60 secondes (thread background Streamlit) — pas de webhook, pas de port forwarding requis en local
- **Config `.env` :** `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`
- **Note :** Twilio Sandbox gratuit pour les tests. Production : numéro WhatsApp Business approuvé Meta.

---

## 7. Base de données SQLite

### Table `leads`
| Colonne | Type | Description |
|---|---|---|
| id | INTEGER PK | |
| siret | TEXT | |
| nom | TEXT | Dirigeant |
| societe | TEXT | |
| secteur | TEXT | |
| ville | TEXT | |
| email | TEXT | |
| tel | TEXT | |
| score | INTEGER | 0–100 |
| priorite | INTEGER | 1/2/3 |
| signaux | TEXT | JSON array |
| source | TEXT | SIRENE/Bodacc/Places |
| status | TEXT | new/sent/later/skip/qualified/excluded |
| mode | TEXT | manual/agent |
| created_at | TIMESTAMP | |
| session_id | INTEGER | FK → sessions |

### Table `sessions`
| Colonne | Type | Description |
|---|---|---|
| id | INTEGER PK | |
| created_at | TIMESTAMP | |
| nb_leads | INTEGER | |
| nb_sent | INTEGER | |
| nb_qualified | INTEGER | |
| duree_sec | INTEGER | |

### Table `conversations`
| Colonne | Type | Description |
|---|---|---|
| id | INTEGER PK | |
| lead_id | INTEGER | FK → leads |
| canal | TEXT | email/whatsapp |
| role | TEXT | agent/prospect |
| message | TEXT | |
| score_maturite | INTEGER | Score à ce tour |
| timestamp | TIMESTAMP | |

---

## 8. Interface Streamlit (4 onglets)

### Onglet 1 — Recherche & Génération
- Formulaire identique au HTML : secteur, département, ville, taille, ancienneté, nb leads, profil cible
- Sources toggleables : SIRENE, Bodacc (Google Places retiré — pas d'API gratuite)
- Barre de progression avec étapes réelles
- Tableau de résultats avec filtres (chaud/tiède/froid/sans site/nouveaux)
- Panneau détail par lead avec message modifiable
- Boutons : Export CSV / Lancer la session

### Onglet 2 — Session Prospection
- File d'attente des leads (triés par score)
- Zone de travail : infos lead + contexte IA + message
- **Toggle Manuel / Agent IA** par lead
- Mode Manuel : copier-coller + statut (envoyé/plus tard/passer)
- Mode Agent : bouton "Envoyer via agent" → conversation gérée automatiquement
- Historique de conversation en temps réel pour les leads en mode Agent
- Bouton "Je prends la main" pour reprendre en manuel
- Chronomètre de session

### Onglet 3 — Historique
- Liste des sessions passées avec métriques (nb leads, envois, qualifiés, durée)
- Filtres : par date, par statut, par canal
- Vue détaillée d'une session : tableau des leads + conversations agent
- Re-ouvrir une session pour reprendre les leads "Plus tard"

### Onglet 4 — Paramètres
- **API Claude :** champ masqué pour saisir/modifier la clé (sauvegardé dans `.env`)
- **Email :** SMTP host/port/user/pass, IMAP host/folder
- **WhatsApp :** Twilio SID, Token, numéro expéditeur
- **Profil cible :** description du client idéal (injecté dans le prompt de scoring)
- **Calendly :** URL du lien de prise de RDV
- **Seuil de qualification :** score minimum pour proposer un RDV (défaut : 60)

---

## 9. Launcher START.bat

```batch
@echo off
title ProspectEngine — Démarrage
cd /d %~dp0
echo Démarrage de ProspectEngine...

if not exist venv\ (
    echo Installation initiale (une seule fois)...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q --disable-pip-version-check

streamlit run app.py ^
  --server.port 8501 ^
  --browser.gatherUsageStats false ^
  --server.headless false
```

**Premier lancement (~2 min) :** crée le venv, installe les packages.  
**Lancements suivants (~5 sec) :** démarre directement.

---

## 10. Sécurité

- `.env` listé dans `.gitignore` — jamais dans le dépôt
- Les credentials sont lus uniquement via `os.getenv()` après `load_dotenv()`
- La clé API est saisie dans l'onglet Paramètres et écrite dans `.env` local — jamais affichée en clair dans l'UI
- SQLite local uniquement — aucune donnée transmise à des serveurs tiers (sauf les appels API intentionnels)

---

## 11. Dépendances Python

```
streamlit>=1.35
anthropic>=0.30
python-dotenv>=1.0
requests>=2.31
twilio>=9.0
pandas>=2.0
```

---

## 12. Critères de succès

- [ ] `START.bat` installe et lance l'appli sans intervention technique
- [ ] La recherche SIRENE retourne de vraies entreprises filtrées par secteur/département
- [ ] Le scoring Claude génère un score cohérent et un message personnalisé
- [ ] L'agent envoie un email de prospection et répond automatiquement aux réponses
- [ ] L'agent WhatsApp fonctionne via Twilio Sandbox
- [ ] L'historique SQLite persiste entre les sessions
- [ ] Export CSV fonctionnel avec toutes les colonnes
