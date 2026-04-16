# ProspectEngine Python — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir la démo HTML en application Python/Streamlit fonctionnelle avec vraies APIs, scoring Claude, agent conversationnel Email+WhatsApp, et launcher double-clic Windows.

**Architecture:** Streamlit app (app.py) orchestrant des modules indépendants : collecte (sirene.py, bodacc.py), IA (scoring.py), agent multi-canal (agent/), persistance (db.py). Tout tourne localement, secrets dans .env, données en SQLite.

**Tech Stack:** Python 3.10+, Streamlit 1.35+, Anthropic SDK (claude-haiku-4-5-20251001), requests, python-dotenv, twilio, pandas, pytest, unittest.mock

---

## Structure des fichiers

```
prospect_engine/
├── START.bat
├── requirements.txt
├── .env.example
├── .gitignore
├── app.py
├── modules/
│   ├── __init__.py
│   ├── sirene.py
│   ├── bodacc.py
│   ├── scoring.py
│   ├── db.py
│   ├── export.py
│   └── agent/
│       ├── __init__.py
│       ├── conversation.py
│       ├── qualifier.py
│       ├── prompts.py
│       └── channels/
│           ├── __init__.py
│           ├── email.py
│           └── whatsapp.py
├── tests/
│   ├── __init__.py
│   ├── test_db.py
│   ├── test_sirene.py
│   ├── test_bodacc.py
│   ├── test_scoring.py
│   ├── test_export.py
│   └── agent/
│       ├── __init__.py
│       ├── test_conversation.py
│       ├── test_qualifier.py
│       ├── test_email.py
│       └── test_whatsapp.py
└── data/
    └── .gitkeep
```

---

## Task 1 : Setup projet

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `START.bat`
- Create: `modules/__init__.py`
- Create: `modules/agent/__init__.py`
- Create: `modules/agent/channels/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/agent/__init__.py`
- Create: `data/.gitkeep`

- [ ] **Étape 1 : Créer requirements.txt**

```
streamlit>=1.35
anthropic>=0.30
python-dotenv>=1.0
requests>=2.31
twilio>=9.0
pandas>=2.0
pytest>=8.0
```

- [ ] **Étape 2 : Créer .env.example**

```
ANTHROPIC_API_KEY=sk-ant-api03-...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ton@email.com
SMTP_PASS=mot_de_passe_application
IMAP_HOST=imap.gmail.com
IMAP_FOLDER=INBOX
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
CALENDLY_URL=https://calendly.com/ton-lien
QUALIFICATION_THRESHOLD=60
```

- [ ] **Étape 3 : Créer .gitignore**

```
.env
venv/
__pycache__/
*.pyc
data/leads.db
.streamlit/
```

- [ ] **Étape 4 : Créer START.bat**

```batch
@echo off
title ProspectEngine
cd /d %~dp0
echo Demarrage de ProspectEngine...

if not exist venv\ (
    echo Installation initiale (environ 2 minutes, une seule fois)...
    python -m venv venv
    if errorlevel 1 (
        echo ERREUR : Python n'est pas installe.
        echo Telecharger Python sur https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q --disable-pip-version-check

streamlit run app.py --server.port 8501 --browser.gatherUsageStats false --server.headless false
pause
```

- [ ] **Étape 5 : Créer les fichiers __init__.py vides**

Créer `modules/__init__.py`, `modules/agent/__init__.py`, `modules/agent/channels/__init__.py`, `tests/__init__.py`, `tests/agent/__init__.py` — tous vides.

- [ ] **Étape 6 : Créer data/.gitkeep**

Fichier vide pour que git suive le dossier `data/`.

- [ ] **Étape 7 : Commit**

```bash
git add .
git commit -m "chore: setup projet ProspectEngine Python"
```

---

## Task 2 : Base de données (db.py)

**Files:**
- Create: `modules/db.py`
- Create: `tests/test_db.py`

- [ ] **Étape 1 : Écrire les tests**

```python
# tests/test_db.py
import pytest
from modules.db import Database

@pytest.fixture
def db():
    return Database(":memory:")

def test_create_session(db):
    session_id = db.create_session()
    assert isinstance(session_id, int)
    assert session_id > 0

def test_insert_lead(db):
    session_id = db.create_session()
    lead = {
        "siret": "12345678901234", "nom": "Jean Martin",
        "societe": "Martin & Associés", "secteur": "Expertise comptable",
        "ville": "Lyon", "email": "jean@martin.fr", "tel": "+33612345678",
        "score": 75, "priorite": 1, "signaux": ["Création récente"], "source": "SIRENE"
    }
    lead_id = db.insert_lead(session_id, lead)
    assert lead_id > 0

def test_get_leads_by_session(db):
    session_id = db.create_session()
    lead = {"siret": "111", "nom": "A", "societe": "B", "secteur": "C",
            "ville": "D", "email": "", "tel": "", "score": 50,
            "priorite": 2, "signaux": [], "source": "SIRENE"}
    db.insert_lead(session_id, lead)
    leads = db.get_leads_by_session(session_id)
    assert len(leads) == 1
    assert leads[0]["nom"] == "A"

def test_update_lead_status(db):
    session_id = db.create_session()
    lead_id = db.insert_lead(session_id, {"siret": "1", "nom": "X", "societe": "Y",
        "secteur": "Z", "ville": "W", "email": "", "tel": "",
        "score": 0, "priorite": 3, "signaux": [], "source": "SIRENE"})
    db.update_lead_status(lead_id, "sent")
    leads = db.get_leads_by_session(session_id)
    assert leads[0]["status"] == "sent"

def test_insert_and_get_conversations(db):
    session_id = db.create_session()
    lead_id = db.insert_lead(session_id, {"siret": "1", "nom": "X", "societe": "Y",
        "secteur": "Z", "ville": "W", "email": "", "tel": "",
        "score": 0, "priorite": 3, "signaux": [], "source": "SIRENE"})
    db.insert_conversation(lead_id, "email", "agent", "Bonjour !", 0)
    db.insert_conversation(lead_id, "email", "prospect", "Merci, intéressé.", 45)
    convs = db.get_conversations(lead_id)
    assert len(convs) == 2
    assert convs[0]["role"] == "agent"
    assert convs[1]["score_maturite"] == 45

def test_get_all_sessions(db):
    db.create_session()
    db.create_session()
    sessions = db.get_all_sessions()
    assert len(sessions) == 2

def test_update_session(db):
    session_id = db.create_session()
    db.update_session(session_id, nb_leads=150, nb_sent=42)
    sessions = db.get_all_sessions()
    assert sessions[0]["nb_leads"] == 150
    assert sessions[0]["nb_sent"] == 42
```

- [ ] **Étape 2 : Vérifier que les tests échouent**

```bash
pytest tests/test_db.py -v
```

Attendu : `ModuleNotFoundError: No module named 'modules.db'`

- [ ] **Étape 3 : Implémenter modules/db.py**

```python
import sqlite3
from pathlib import Path
import json


class Database:
    def __init__(self, db_path="data/leads.db"):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                nb_leads INTEGER DEFAULT 0,
                nb_sent INTEGER DEFAULT 0,
                nb_qualified INTEGER DEFAULT 0,
                duree_sec INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER REFERENCES sessions(id),
                siret TEXT,
                nom TEXT,
                societe TEXT,
                secteur TEXT,
                ville TEXT,
                email TEXT DEFAULT '',
                tel TEXT DEFAULT '',
                score INTEGER DEFAULT 0,
                priorite INTEGER DEFAULT 3,
                signaux TEXT DEFAULT '[]',
                source TEXT DEFAULT 'SIRENE',
                status TEXT DEFAULT 'new',
                mode TEXT DEFAULT 'manual',
                message_linkedin TEXT DEFAULT '',
                message_email TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER REFERENCES leads(id),
                canal TEXT,
                role TEXT,
                message TEXT,
                score_maturite INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def create_session(self):
        cur = self.conn.execute("INSERT INTO sessions DEFAULT VALUES")
        self.conn.commit()
        return cur.lastrowid

    def update_session(self, session_id, **kwargs):
        cols = ", ".join(f"{k}=?" for k in kwargs)
        self.conn.execute(
            f"UPDATE sessions SET {cols} WHERE id=?",
            (*kwargs.values(), session_id)
        )
        self.conn.commit()

    def insert_lead(self, session_id, lead):
        signaux = lead.get("signaux", [])
        if isinstance(signaux, list):
            signaux = json.dumps(signaux, ensure_ascii=False)
        cur = self.conn.execute("""
            INSERT INTO leads (session_id, siret, nom, societe, secteur, ville,
                               email, tel, score, priorite, signaux, source,
                               message_linkedin, message_email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, lead.get("siret", ""), lead.get("nom", ""),
            lead.get("societe", ""), lead.get("secteur", ""), lead.get("ville", ""),
            lead.get("email", ""), lead.get("tel", ""),
            lead.get("score", 0), lead.get("priorite", 3), signaux,
            lead.get("source", "SIRENE"),
            lead.get("message_linkedin", ""), lead.get("message_email", "")
        ))
        self.conn.commit()
        return cur.lastrowid

    def get_leads_by_session(self, session_id):
        rows = self.conn.execute(
            "SELECT * FROM leads WHERE session_id=? ORDER BY score DESC",
            (session_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def update_lead_status(self, lead_id, status, mode=None):
        if mode:
            self.conn.execute(
                "UPDATE leads SET status=?, mode=? WHERE id=?",
                (status, mode, lead_id)
            )
        else:
            self.conn.execute(
                "UPDATE leads SET status=? WHERE id=?",
                (status, lead_id)
            )
        self.conn.commit()

    def insert_conversation(self, lead_id, canal, role, message, score_maturite=0):
        cur = self.conn.execute("""
            INSERT INTO conversations (lead_id, canal, role, message, score_maturite)
            VALUES (?, ?, ?, ?, ?)
        """, (lead_id, canal, role, message, score_maturite))
        self.conn.commit()
        return cur.lastrowid

    def get_conversations(self, lead_id):
        rows = self.conn.execute(
            "SELECT * FROM conversations WHERE lead_id=? ORDER BY timestamp",
            (lead_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_sessions(self):
        rows = self.conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_leads_pending_agent(self):
        """Returns leads in agent mode awaiting response."""
        rows = self.conn.execute("""
            SELECT * FROM leads
            WHERE mode='agent' AND status='sent'
            ORDER BY created_at ASC
        """).fetchall()
        return [dict(r) for r in rows]
```

- [ ] **Étape 4 : Vérifier que les tests passent**

```bash
pytest tests/test_db.py -v
```

Attendu : 7 tests PASSED

- [ ] **Étape 5 : Commit**

```bash
git add modules/db.py tests/test_db.py
git commit -m "feat: module db SQLite avec tables leads, sessions, conversations"
```

---

## Task 3 : Module SIRENE (sirene.py)

**Files:**
- Create: `modules/sirene.py`
- Create: `tests/test_sirene.py`

- [ ] **Étape 1 : Écrire les tests**

```python
# tests/test_sirene.py
import pytest
from unittest.mock import patch, Mock
from modules.sirene import search_companies, _parse_company, _match_taille

MOCK_API_RESPONSE = {
    "results": [
        {
            "nom_complet": "MARTIN & ASSOCIES CONSEIL",
            "activite_principale": "6630Z",
            "activite_principale_libelle": "Gestion de fonds",
            "date_creation": "2024-03-15",
            "tranche_effectif_salarie": "11",
            "dirigeants": [{"prenoms": "Jean", "nom": "Martin"}],
            "siege": {
                "siret": "12345678901234",
                "libelle_commune": "Lyon",
                "departement": "69",
                "adresse": "10 rue de la Paix, 69006 Lyon"
            }
        }
    ],
    "total_results": 1
}

def test_parse_company_returns_expected_fields():
    item = MOCK_API_RESPONSE["results"][0]
    company = _parse_company(item)
    assert company["siret"] == "12345678901234"
    assert company["societe"] == "MARTIN & ASSOCIES CONSEIL"
    assert company["ville"] == "Lyon"
    assert company["nom"] == "Jean Martin"
    assert company["source"] == "SIRENE"
    assert isinstance(company["anciennete_mois"], int)

def test_parse_company_missing_siege_returns_none():
    result = _parse_company({"nom_complet": "Test", "siege": {}})
    assert result is None

def test_match_taille_tpe():
    assert _match_taille("NN", "0") is True
    assert _match_taille("01", "0") is True
    assert _match_taille("11", "0") is False

def test_match_taille_pme():
    assert _match_taille("11", "1") is True
    assert _match_taille("21", "1") is True
    assert _match_taille("31", "1") is False

def test_match_taille_unknown_code():
    assert _match_taille("99", "0") is False

@patch("modules.sirene.requests.get")
def test_search_companies_returns_list(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = MOCK_API_RESPONSE
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    results = search_companies(secteur="gestion de fonds", departement="69", nb=1)
    assert len(results) == 1
    assert results[0]["siret"] == "12345678901234"

@patch("modules.sirene.requests.get")
def test_search_companies_handles_api_error(mock_get):
    import requests
    mock_get.side_effect = requests.RequestException("timeout")
    results = search_companies(secteur="test", nb=10)
    assert results == []

@patch("modules.sirene.requests.get")
def test_search_companies_filters_by_age(mock_get):
    mock_resp = Mock()
    # Company created 24 months ago — should be filtered out with age_max_mois=12
    old_item = {**MOCK_API_RESPONSE["results"][0], "date_creation": "2022-01-01"}
    mock_resp.json.return_value = {"results": [old_item], "total_results": 1}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    results = search_companies(secteur="test", nb=10, age_max_mois=12)
    assert results == []
```

- [ ] **Étape 2 : Vérifier que les tests échouent**

```bash
pytest tests/test_sirene.py -v
```

Attendu : `ModuleNotFoundError: No module named 'modules.sirene'`

- [ ] **Étape 3 : Implémenter modules/sirene.py**

```python
import requests
from datetime import datetime

SIRENE_API = "https://recherche-entreprises.api.gouv.fr/search"


def search_companies(secteur="", departement="", nb=150, age_max_mois=None, taille=None):
    """
    Returns list of company dicts from SIRENE public API.
    Handles pagination automatically.
    """
    per_page = min(nb, 25)
    params = {"per_page": per_page, "page": 1}
    if secteur:
        params["q"] = secteur
    if departement:
        params["departement"] = departement.strip().split(",")[0].strip()

    results = []
    page = 1
    while len(results) < nb:
        params["page"] = page
        try:
            resp = requests.get(SIRENE_API, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException:
            break

        items = data.get("results", [])
        if not items:
            break

        for item in items:
            company = _parse_company(item)
            if company is None:
                continue
            if age_max_mois and company.get("anciennete_mois", 999) > age_max_mois:
                continue
            if taille and not _match_taille(company.get("effectifs_code", ""), taille):
                continue
            results.append(company)
            if len(results) >= nb:
                break

        if len(items) < per_page:
            break
        page += 1

    return results[:nb]


def _parse_company(item):
    """Parse a SIRENE API result into a lead dict. Returns None if invalid."""
    siege = item.get("siege", {})
    if not siege or not siege.get("siret"):
        return None

    date_creation = item.get("date_creation", "")
    anciennete_mois = 0
    if date_creation:
        try:
            d = datetime.strptime(date_creation, "%Y-%m-%d")
            anciennete_mois = max(0, (datetime.now() - d).days // 30)
        except ValueError:
            pass

    dirigeants = item.get("dirigeants", [])
    nom_dirigeant = ""
    if dirigeants:
        d = dirigeants[0]
        nom_dirigeant = f"{d.get('prenoms', '')} {d.get('nom', '')}".strip()

    return {
        "siret": siege.get("siret", ""),
        "nom": nom_dirigeant or item.get("nom_complet", ""),
        "societe": item.get("nom_complet", ""),
        "secteur": item.get("activite_principale_libelle", ""),
        "naf": item.get("activite_principale", ""),
        "ville": siege.get("libelle_commune", ""),
        "departement": siege.get("departement", ""),
        "adresse": siege.get("adresse", ""),
        "effectifs_code": item.get("tranche_effectif_salarie", ""),
        "anciennete_mois": anciennete_mois,
        "date_creation": date_creation,
        "source": "SIRENE",
        "email": "",
        "tel": "",
        "score": 0,
        "priorite": 3,
        "signaux": [],
        "message_linkedin": "",
        "message_email": "",
    }


def _match_taille(code, taille_filter):
    """
    taille_filter: '0'=TPE, '1'=PME, '2'=ETI, '3'=Grande
    SIRENE effectif codes: NN/00/01/02/03=TPE, 11/12/21/22=PME, 31/32/41/42/51=ETI, 52/53=Grande
    """
    mapping = {
        "0": {"NN", "00", "01", "02", "03"},
        "1": {"11", "12", "21", "22"},
        "2": {"31", "32", "41", "42", "51"},
        "3": {"52", "53"},
    }
    return code in mapping.get(taille_filter, set())
```

- [ ] **Étape 4 : Vérifier que les tests passent**

```bash
pytest tests/test_sirene.py -v
```

Attendu : 7 tests PASSED

- [ ] **Étape 5 : Commit**

```bash
git add modules/sirene.py tests/test_sirene.py
git commit -m "feat: module SIRENE — recherche entreprises API publique"
```

---

## Task 4 : Module Bodacc (bodacc.py)

**Files:**
- Create: `modules/bodacc.py`
- Create: `tests/test_bodacc.py`

- [ ] **Étape 1 : Écrire les tests**

```python
# tests/test_bodacc.py
import pytest
from unittest.mock import patch, Mock
from modules.bodacc import get_signals_for_siret, enrich_leads

MOCK_BODACC_RESPONSE = {
    "records": [
        {"fields": {"typeavis_lib": "Vente et cession", "dateparution": "2024-01-15"}},
        {"fields": {"typeavis_lib": "Immatriculation", "dateparution": "2024-01-10"}},
    ]
}

@patch("modules.bodacc.requests.get")
def test_get_signals_cession(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = MOCK_BODACC_RESPONSE
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    signals = get_signals_for_siret("12345678901234")
    assert any("Cession" in s for s in signals)

@patch("modules.bodacc.requests.get")
def test_get_signals_creation(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = {
        "records": [{"fields": {"typeavis_lib": "Immatriculation"}}]
    }
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    signals = get_signals_for_siret("12345678901234")
    assert any("Création" in s for s in signals)

@patch("modules.bodacc.requests.get")
def test_get_signals_handles_error(mock_get):
    import requests
    mock_get.side_effect = requests.RequestException("timeout")
    signals = get_signals_for_siret("99999999999999")
    assert signals == []

@patch("modules.bodacc.requests.get")
def test_enrich_leads_adds_signals(mock_get):
    mock_resp = Mock()
    mock_resp.json.return_value = {"records": [
        {"fields": {"typeavis_lib": "Vente et cession"}}
    ]}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    leads = [{"siret": "12345678901234", "signaux": ["Création récente"]}]
    enriched = enrich_leads(leads)
    assert len(enriched[0]["signaux"]) > 1

@patch("modules.bodacc.requests.get")
def test_enrich_leads_skips_empty_siret(mock_get):
    leads = [{"siret": "", "signaux": []}]
    enriched = enrich_leads(leads)
    mock_get.assert_not_called()
    assert enriched[0]["signaux"] == []
```

- [ ] **Étape 2 : Vérifier que les tests échouent**

```bash
pytest tests/test_bodacc.py -v
```

Attendu : `ModuleNotFoundError`

- [ ] **Étape 3 : Implémenter modules/bodacc.py**

```python
import requests

BODACC_API = "https://bodacc-datadica.fr/api/records/1.0/search/"


def get_signals_for_siret(siret):
    """Returns list of Bodacc signal strings for a given SIRET."""
    if not siret:
        return []

    params = {
        "dataset": "annonces-commerciales",
        "q": f"registre:{siret}",
        "rows": 5,
        "sort": "dateparution",
        "order": "desc",
    }
    try:
        resp = requests.get(BODACC_API, params=params, timeout=8)
        resp.raise_for_status()
        records = resp.json().get("records", [])
    except requests.RequestException:
        return []

    signals = []
    for record in records:
        type_ann = record.get("fields", {}).get("typeavis_lib", "").lower()
        if "cession" in type_ann:
            signals.append("Cession annoncée (Bodacc)")
        elif "immatriculation" in type_ann or "création" in type_ann:
            signals.append("Création récente (Bodacc)")
        elif "procédure" in type_ann or "redressement" in type_ann or "liquidation" in type_ann:
            signals.append("Procédure judiciaire (Bodacc)")
        elif "modification" in type_ann:
            signals.append("Modification récente (Bodacc)")

    return signals


def enrich_leads(leads):
    """Add Bodacc signals to a list of lead dicts. Modifies in-place."""
    for lead in leads:
        siret = lead.get("siret", "")
        if siret:
            bodacc_signals = get_signals_for_siret(siret)
            existing = lead.get("signaux", [])
            lead["signaux"] = existing + bodacc_signals
    return leads
```

- [ ] **Étape 4 : Vérifier que les tests passent**

```bash
pytest tests/test_bodacc.py -v
```

Attendu : 5 tests PASSED

- [ ] **Étape 5 : Commit**

```bash
git add modules/bodacc.py tests/test_bodacc.py
git commit -m "feat: module Bodacc — enrichissement signaux via data.gouv.fr"
```

---

## Task 5 : Module Scoring (scoring.py)

**Files:**
- Create: `modules/scoring.py`
- Create: `tests/test_scoring.py`

- [ ] **Étape 1 : Écrire les tests**

```python
# tests/test_scoring.py
import pytest
import json
from unittest.mock import patch, Mock, MagicMock
from modules.scoring import score_lead, score_leads_batch, SYSTEM_PROMPT

MOCK_LEAD = {
    "siret": "12345678901234",
    "societe": "Martin & Associés Conseil",
    "secteur": "Gestion de fonds",
    "ville": "Lyon",
    "anciennete_mois": 8,
    "signaux": ["Création récente (Bodacc)"],
    "effectifs_code": "11",
}

MOCK_AI_RESPONSE = {
    "score": 82,
    "signaux": ["Création récente", "Potentiel patrimonial fort"],
    "message_linkedin": "Bonjour,\n\nVotre cabinet à Lyon a retenu mon attention.\n\nDisponible 20 min ?",
    "message_email": "Bonjour,\n\nJe vous contacte concernant votre situation patrimoniale.\n\nCordialement",
    "priorite": 1,
    "raison": "Entreprise récente avec CA potentiel significatif dans un secteur favorable."
}

@patch("modules.scoring.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-key"})
def test_score_lead_returns_expected_fields(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps(MOCK_AI_RESPONSE))]
    mock_client.messages.create.return_value = mock_message

    result = score_lead(MOCK_LEAD)

    assert result["score"] == 82
    assert result["priorite"] == 1
    assert "message_linkedin" in result
    assert "message_email" in result
    assert isinstance(result["signaux"], list)

@patch("modules.scoring.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-key"})
def test_score_lead_merges_existing_signals(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps({
        **MOCK_AI_RESPONSE, "signaux": ["Signal IA"]
    }))]
    mock_client.messages.create.return_value = mock_message

    lead = {**MOCK_LEAD, "signaux": ["Bodacc signal"]}
    result = score_lead(lead)
    assert "Bodacc signal" in result["signaux"]
    assert "Signal IA" in result["signaux"]

@patch("modules.scoring.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-key"})
def test_score_lead_fallback_on_invalid_json(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="not json")]
    mock_client.messages.create.return_value = mock_message

    result = score_lead(MOCK_LEAD)
    assert result["score"] == 30
    assert "message_linkedin" in result

def test_score_lead_raises_without_api_key():
    import os
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    with patch.dict("os.environ", env, clear=True):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            score_lead(MOCK_LEAD)

@patch("modules.scoring.score_lead")
def test_score_leads_batch_calls_progress(mock_score):
    mock_score.side_effect = lambda l, p: {**l, "score": 50, "priorite": 2,
        "signaux": [], "message_linkedin": "", "message_email": "", "raison": ""}
    leads = [MOCK_LEAD, MOCK_LEAD]
    progress_calls = []
    score_leads_batch(leads, progress_callback=lambda i, t: progress_calls.append((i, t)))
    assert progress_calls == [(1, 2), (2, 2)]
```

- [ ] **Étape 2 : Vérifier que les tests échouent**

```bash
pytest tests/test_scoring.py -v
```

Attendu : `ModuleNotFoundError`

- [ ] **Étape 3 : Implémenter modules/scoring.py**

```python
import os
import json
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
        result = json.loads(message.content[0].text)
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

    # Merge Bodacc signals already on the lead with AI-detected signals
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
```

- [ ] **Étape 4 : Vérifier que les tests passent**

```bash
pytest tests/test_scoring.py -v
```

Attendu : 5 tests PASSED

- [ ] **Étape 5 : Commit**

```bash
git add modules/scoring.py tests/test_scoring.py
git commit -m "feat: module scoring Claude Haiku — score + signaux + messages"
```

---

## Task 6 : Module Export (export.py)

**Files:**
- Create: `modules/export.py`
- Create: `tests/test_export.py`

- [ ] **Étape 1 : Écrire les tests**

```python
# tests/test_export.py
import pytest
from modules.export import leads_to_csv

SAMPLE_LEADS = [
    {
        "score": 82, "nom": "Jean Martin", "societe": "Martin Conseil",
        "secteur": "Gestion de fonds", "ville": "Lyon", "siret": "12345678901234",
        "email": "jean@martin.fr", "tel": "+33612345678", "source": "SIRENE",
        "anciennete_mois": 8, "signaux": ["Création récente"], "status": "new",
        "message_linkedin": "Bonjour Jean,", "message_email": "Objet: ..."
    },
    {
        "score": 45, "nom": "Sophie Dubois", "societe": "Dubois SAS",
        "secteur": "Comptabilité", "ville": "Paris", "siret": "98765432109876",
        "email": "", "tel": "", "source": "Bodacc",
        "anciennete_mois": 24, "signaux": [], "status": "sent",
        "message_linkedin": "", "message_email": ""
    }
]

def test_leads_to_csv_returns_bytes():
    result = leads_to_csv(SAMPLE_LEADS)
    assert isinstance(result, bytes)

def test_leads_to_csv_contains_headers():
    result = leads_to_csv(SAMPLE_LEADS).decode("utf-8-sig")
    assert "Score" in result
    assert "Nom" in result
    assert "SIRET" in result

def test_leads_to_csv_contains_data():
    result = leads_to_csv(SAMPLE_LEADS).decode("utf-8-sig")
    assert "Jean Martin" in result
    assert "82" in result
    assert "Lyon" in result

def test_leads_to_csv_handles_list_signals():
    lead = {**SAMPLE_LEADS[0], "signaux": ["Signal A", "Signal B"]}
    result = leads_to_csv([lead]).decode("utf-8-sig")
    assert "Signal A" in result

def test_leads_to_csv_handles_json_string_signals():
    lead = {**SAMPLE_LEADS[0], "signaux": '["Signal A", "Signal B"]'}
    result = leads_to_csv([lead]).decode("utf-8-sig")
    assert "Signal A" in result

def test_leads_to_csv_empty_list():
    result = leads_to_csv([])
    assert isinstance(result, bytes)
```

- [ ] **Étape 2 : Vérifier que les tests échouent**

```bash
pytest tests/test_export.py -v
```

Attendu : `ModuleNotFoundError`

- [ ] **Étape 3 : Implémenter modules/export.py**

```python
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
```

- [ ] **Étape 4 : Vérifier que les tests passent**

```bash
pytest tests/test_export.py -v
```

Attendu : 6 tests PASSED

- [ ] **Étape 5 : Commit**

```bash
git add modules/export.py tests/test_export.py
git commit -m "feat: module export CSV Excel-compatible"
```

---

## Task 7 : Agent — Prompts et ConversationManager

**Files:**
- Create: `modules/agent/prompts.py`
- Create: `modules/agent/conversation.py`
- Create: `tests/agent/test_conversation.py`

- [ ] **Étape 1 : Écrire les tests**

```python
# tests/agent/test_conversation.py
import pytest
from modules.db import Database
from modules.agent.conversation import ConversationManager

@pytest.fixture
def db():
    return Database(":memory:")

@pytest.fixture
def manager(db):
    return ConversationManager(db)

@pytest.fixture
def lead_id(db):
    sid = db.create_session()
    return db.insert_lead(sid, {
        "siret": "1", "nom": "Jean Martin", "societe": "Martin SAS",
        "secteur": "CGP", "ville": "Lyon", "email": "j@m.fr", "tel": "+336",
        "score": 75, "priorite": 1, "signaux": [], "source": "SIRENE"
    })

def test_start_conversation_creates_agent_message(manager, db, lead_id):
    manager.start_conversation(lead_id, "email", "Bonjour Jean,")
    convs = db.get_conversations(lead_id)
    assert len(convs) == 1
    assert convs[0]["role"] == "agent"
    assert convs[0]["canal"] == "email"

def test_start_conversation_sets_lead_status_sent(manager, db, lead_id):
    manager.start_conversation(lead_id, "email", "Bonjour Jean,")
    leads = db.get_leads_by_session(db.conn.execute(
        "SELECT session_id FROM leads WHERE id=?", (lead_id,)
    ).fetchone()[0])
    assert leads[0]["status"] == "sent"
    assert leads[0]["mode"] == "agent"

def test_add_prospect_reply(manager, db, lead_id):
    manager.start_conversation(lead_id, "email", "Bonjour Jean,")
    manager.add_prospect_reply(lead_id, "email", "Intéressé, dites m'en plus.")
    convs = db.get_conversations(lead_id)
    assert len(convs) == 2
    assert convs[1]["role"] == "prospect"

def test_get_turn_count(manager, db, lead_id):
    manager.start_conversation(lead_id, "email", "Message 1")
    manager.add_prospect_reply(lead_id, "email", "Réponse 1")
    manager.add_agent_reply(lead_id, "email", "Message 2", score_maturite=40)
    assert manager.get_turn_count(lead_id) == 2

def test_format_history_for_prompt(manager, db, lead_id):
    manager.start_conversation(lead_id, "email", "Bonjour Jean,")
    manager.add_prospect_reply(lead_id, "email", "Bonjour, je suis intéressé.")
    history = manager.format_history_for_prompt(lead_id)
    assert "CGP:" in history
    assert "Prospect:" in history
    assert "Bonjour Jean," in history

from modules.agent.prompts import get_outreach_message

def test_get_outreach_message_linkedin():
    msg = get_outreach_message("linkedin", "cgp", "Jean Martin", "CGP", "Lyon")
    assert "Jean Martin" in msg
    assert "Lyon" in msg

def test_get_outreach_message_email():
    msg = get_outreach_message("email", "cgp", "Sophie Dubois", "Comptabilité", "Paris")
    assert "Sophie Dubois" in msg
```

- [ ] **Étape 2 : Vérifier que les tests échouent**

```bash
pytest tests/agent/test_conversation.py -v
```

Attendu : `ModuleNotFoundError`

- [ ] **Étape 3 : Implémenter modules/agent/prompts.py**

```python
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
    """Returns the initial outreach message for a lead."""
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
```

- [ ] **Étape 4 : Implémenter modules/agent/conversation.py**

```python
from modules.db import Database


class ConversationManager:
    def __init__(self, db: Database):
        self.db = db

    def start_conversation(self, lead_id, canal, initial_message):
        """Record the agent's first outreach message and update lead status."""
        self.db.insert_conversation(
            lead_id=lead_id,
            canal=canal,
            role="agent",
            message=initial_message,
            score_maturite=0
        )
        self.db.update_lead_status(lead_id, "sent", mode="agent")

    def add_prospect_reply(self, lead_id, canal, message):
        """Record a prospect's reply."""
        self.db.insert_conversation(
            lead_id=lead_id,
            canal=canal,
            role="prospect",
            message=message,
            score_maturite=0
        )

    def add_agent_reply(self, lead_id, canal, message, score_maturite=0):
        """Record agent's follow-up message."""
        self.db.insert_conversation(
            lead_id=lead_id,
            canal=canal,
            role="agent",
            message=message,
            score_maturite=score_maturite
        )

    def get_history(self, lead_id):
        """Returns full conversation history for a lead."""
        return self.db.get_conversations(lead_id)

    def get_turn_count(self, lead_id):
        """Returns number of agent messages sent (outreach + follow-ups)."""
        return sum(1 for h in self.get_history(lead_id) if h["role"] == "agent")

    def format_history_for_prompt(self, lead_id):
        """Format conversation history as text for AI context."""
        history = self.get_history(lead_id)
        lines = []
        for msg in history:
            role_label = "CGP" if msg["role"] == "agent" else "Prospect"
            lines.append(f"{role_label}: {msg['message']}")
        return "\n\n".join(lines)
```

- [ ] **Étape 5 : Vérifier que les tests passent**

```bash
pytest tests/agent/test_conversation.py -v
```

Attendu : 8 tests PASSED

- [ ] **Étape 6 : Commit**

```bash
git add modules/agent/prompts.py modules/agent/conversation.py tests/agent/test_conversation.py
git commit -m "feat: agent prompts et ConversationManager"
```

---

## Task 8 : Agent — Qualifier (qualifier.py)

**Files:**
- Create: `modules/agent/qualifier.py`
- Create: `tests/agent/test_qualifier.py`

- [ ] **Étape 1 : Écrire les tests**

```python
# tests/agent/test_qualifier.py
import pytest
import json
from unittest.mock import patch, MagicMock
from modules.db import Database
from modules.agent.conversation import ConversationManager
from modules.agent.qualifier import qualify_response

@pytest.fixture
def db():
    return Database(":memory:")

@pytest.fixture
def setup(db):
    sid = db.create_session()
    lead_id = db.insert_lead(sid, {
        "siret": "1", "nom": "Jean Martin", "societe": "Martin SAS",
        "secteur": "Comptabilité", "ville": "Lyon", "email": "j@m.fr",
        "tel": "+336", "score": 70, "priorite": 1, "signaux": [], "source": "SIRENE"
    })
    manager = ConversationManager(db)
    manager.start_conversation(lead_id, "email", "Bonjour Jean,")
    lead = db.get_leads_by_session(sid)[0]
    return lead, manager

@patch("modules.agent.qualifier.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
def test_qualify_returns_reply(mock_cls, setup):
    lead, manager = setup
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps({
        "action": "reply",
        "score_maturite": 45,
        "message": "Merci pour votre retour. Quelle est votre principale priorité ?",
        "raison": "Prospect intéressé mais besoin d'en savoir plus"
    }))]
    mock_client.messages.create.return_value = mock_message

    result = qualify_response(lead, "Intéressé, dites m'en plus.", manager)
    assert result["action"] == "reply"
    assert result["score_maturite"] == 45
    assert isinstance(result["message"], str)

@patch("modules.agent.qualifier.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
def test_qualify_returns_propose_rdv(mock_cls, setup):
    lead, manager = setup
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=json.dumps({
        "action": "propose_rdv",
        "score_maturite": 75,
        "message": "Parfait ! Voici mon lien : https://calendly.com/test",
        "raison": "Prospect qualifié"
    }))]
    mock_client.messages.create.return_value = mock_message

    result = qualify_response(lead, "Oui je suis très intéressé.", manager)
    assert result["action"] == "propose_rdv"
    assert result["score_maturite"] >= 60

def test_qualify_archives_after_max_turns(db):
    sid = db.create_session()
    lead_id = db.insert_lead(sid, {
        "siret": "1", "nom": "X", "societe": "Y", "secteur": "Z", "ville": "W",
        "email": "", "tel": "", "score": 50, "priorite": 2, "signaux": [], "source": "SIRENE"
    })
    manager = ConversationManager(db)
    # Simulate 4 agent turns already done
    for i in range(4):
        manager.add_agent_reply(lead_id, "email", f"Message {i}", 30)

    lead = db.get_leads_by_session(sid)[0]
    result = qualify_response(lead, "Réponse", manager)
    assert result["action"] == "archive"

@patch("modules.agent.qualifier.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
def test_qualify_fallback_on_bad_json(mock_cls, setup):
    lead, manager = setup
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="invalid json")]
    mock_client.messages.create.return_value = mock_message

    result = qualify_response(lead, "Intéressé.", manager)
    assert result["action"] in ("reply", "propose_rdv", "archive")
    assert "message" in result
```

- [ ] **Étape 2 : Vérifier que les tests échouent**

```bash
pytest tests/agent/test_qualifier.py -v
```

Attendu : `ModuleNotFoundError`

- [ ] **Étape 3 : Implémenter modules/agent/qualifier.py**

```python
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
```

- [ ] **Étape 4 : Vérifier que les tests passent**

```bash
pytest tests/agent/test_qualifier.py -v
```

Attendu : 4 tests PASSED

- [ ] **Étape 5 : Commit**

```bash
git add modules/agent/qualifier.py tests/agent/test_qualifier.py
git commit -m "feat: agent qualifier — analyse réponse prospect et décision IA"
```

---

## Task 9 : Agent — Canal Email

**Files:**
- Create: `modules/agent/channels/email.py`
- Create: `tests/agent/test_email.py`

- [ ] **Étape 1 : Écrire les tests**

```python
# tests/agent/test_email.py
import pytest
from unittest.mock import patch, MagicMock, call
from modules.agent.channels.email import send_email, _decode_header_str, _get_body

@patch("modules.agent.channels.email.smtplib.SMTP")
@patch.dict("os.environ", {
    "SMTP_HOST": "smtp.gmail.com", "SMTP_PORT": "587",
    "SMTP_USER": "test@gmail.com", "SMTP_PASS": "password"
})
def test_send_email_calls_smtp(mock_smtp_cls):
    mock_smtp = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = mock_smtp

    result = send_email("prospect@example.com", "Test subject", "Bonjour !")
    assert result is True
    mock_smtp.send_message.assert_called_once()

@patch.dict("os.environ", {"SMTP_USER": "", "SMTP_PASS": ""})
def test_send_email_raises_without_credentials():
    with pytest.raises(ValueError, match="SMTP_USER"):
        send_email("to@example.com", "Subject", "Body")

def test_decode_header_str_plain():
    assert _decode_header_str("Hello World") == "Hello World"

def test_decode_header_str_encoded():
    # Encoded header (base64 UTF-8)
    encoded = "=?utf-8?b?Qm9uam91cg==?="
    assert _decode_header_str(encoded) == "Bonjour"

@patch("modules.agent.channels.email.imaplib.IMAP4_SSL")
@patch.dict("os.environ", {
    "IMAP_HOST": "imap.gmail.com",
    "SMTP_USER": "test@gmail.com",
    "SMTP_PASS": "password",
    "IMAP_FOLDER": "INBOX"
})
def test_fetch_replies_returns_list(mock_imap_cls):
    mock_imap = MagicMock()
    mock_imap_cls.return_value = mock_imap
    # No messages found
    mock_imap.search.return_value = ("OK", [b""])

    replies = fetch_replies_fn()
    assert isinstance(replies, list)

def fetch_replies_fn():
    from modules.agent.channels.email import fetch_replies
    return fetch_replies(since_hours=1)

@patch.dict("os.environ", {"SMTP_USER": "", "SMTP_PASS": ""})
def test_fetch_replies_returns_empty_without_credentials():
    from modules.agent.channels.email import fetch_replies
    result = fetch_replies()
    assert result == []
```

- [ ] **Étape 2 : Vérifier que les tests échouent**

```bash
pytest tests/agent/test_email.py -v
```

Attendu : `ModuleNotFoundError`

- [ ] **Étape 3 : Implémenter modules/agent/channels/email.py**

```python
import smtplib
import imaplib
import email as email_lib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def send_email(to_address, subject, body):
    """Send a plain-text email via SMTP. Raises ValueError if credentials missing."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        raise ValueError("SMTP_USER et SMTP_PASS requis dans .env")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_address
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    return True


def fetch_replies(since_hours=1):
    """Fetch unread replies via IMAP polling. Returns list of reply dicts."""
    imap_host = os.getenv("IMAP_HOST", "imap.gmail.com")
    imap_user = os.getenv("SMTP_USER", "")
    imap_pass = os.getenv("SMTP_PASS", "")
    imap_folder = os.getenv("IMAP_FOLDER", "INBOX")

    if not imap_user or not imap_pass:
        return []

    replies = []
    try:
        mail = imaplib.IMAP4_SSL(imap_host)
        mail.login(imap_user, imap_pass)
        mail.select(imap_folder)

        since_date = (datetime.now() - timedelta(hours=since_hours)).strftime("%d-%b-%Y")
        _, msg_nums = mail.search(None, f"SINCE {since_date} UNSEEN")

        for num in (msg_nums[0].split() if msg_nums[0] else []):
            _, msg_data = mail.fetch(num, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            msg = email_lib.message_from_bytes(raw)
            replies.append({
                "from": msg.get("From", ""),
                "subject": _decode_header_str(msg.get("Subject", "")),
                "body": _get_body(msg),
                "message_id": msg.get("Message-ID", ""),
                "in_reply_to": msg.get("In-Reply-To", ""),
            })

        mail.logout()
    except Exception:
        pass

    return replies


def _decode_header_str(header_str):
    if not header_str:
        return ""
    decoded, encoding = decode_header(header_str)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(encoding or "utf-8", errors="replace")
    return str(decoded)


def _get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode("utf-8", errors="replace")
    return ""
```

- [ ] **Étape 4 : Vérifier que les tests passent**

```bash
pytest tests/agent/test_email.py -v
```

Attendu : 6 tests PASSED

- [ ] **Étape 5 : Commit**

```bash
git add modules/agent/channels/email.py tests/agent/test_email.py
git commit -m "feat: canal email SMTP/IMAP pour agent conversationnel"
```

---

## Task 10 : Agent — Canal WhatsApp

**Files:**
- Create: `modules/agent/channels/whatsapp.py`
- Create: `tests/agent/test_whatsapp.py`

- [ ] **Étape 1 : Écrire les tests**

```python
# tests/agent/test_whatsapp.py
import pytest
from unittest.mock import patch, MagicMock
from modules.agent.channels.whatsapp import send_whatsapp, fetch_replies, _normalize_number

def test_normalize_number_adds_prefix():
    assert _normalize_number("+33612345678") == "whatsapp:+33612345678"

def test_normalize_number_keeps_existing_prefix():
    assert _normalize_number("whatsapp:+33612345678") == "whatsapp:+33612345678"

@patch("modules.agent.channels.whatsapp.Client")
@patch.dict("os.environ", {
    "TWILIO_ACCOUNT_SID": "ACtest", "TWILIO_AUTH_TOKEN": "token",
    "TWILIO_WHATSAPP_FROM": "whatsapp:+14155238886"
})
def test_send_whatsapp_calls_twilio(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(sid="SM123")

    result = send_whatsapp("+33612345678", "Bonjour !")
    assert result == "SM123"
    mock_client.messages.create.assert_called_once()

@patch.dict("os.environ", {"TWILIO_ACCOUNT_SID": "", "TWILIO_AUTH_TOKEN": ""})
def test_send_whatsapp_raises_without_credentials():
    with pytest.raises(ValueError, match="TWILIO"):
        send_whatsapp("+33612345678", "Bonjour !")

@patch("modules.agent.channels.whatsapp.Client")
@patch.dict("os.environ", {
    "TWILIO_ACCOUNT_SID": "ACtest", "TWILIO_AUTH_TOKEN": "token"
})
def test_fetch_replies_returns_list(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.messages.list.return_value = []

    result = fetch_replies()
    assert isinstance(result, list)

@patch.dict("os.environ", {"TWILIO_ACCOUNT_SID": "", "TWILIO_AUTH_TOKEN": ""})
def test_fetch_replies_returns_empty_without_credentials():
    result = fetch_replies()
    assert result == []
```

- [ ] **Étape 2 : Vérifier que les tests échouent**

```bash
pytest tests/agent/test_whatsapp.py -v
```

Attendu : `ModuleNotFoundError`

- [ ] **Étape 3 : Implémenter modules/agent/channels/whatsapp.py**

```python
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def send_whatsapp(to_number, message):
    """Send a WhatsApp message via Twilio. Returns message SID."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    if not account_sid or not auth_token:
        raise ValueError("TWILIO_ACCOUNT_SID et TWILIO_AUTH_TOKEN requis dans .env")

    from twilio.rest import Client
    client = Client(account_sid, auth_token)
    msg = client.messages.create(
        body=message,
        from_=from_number,
        to=_normalize_number(to_number)
    )
    return msg.sid


def fetch_replies(since_minutes=60):
    """Poll Twilio for inbound WhatsApp messages. Returns list of reply dicts."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")

    if not account_sid or not auth_token:
        return []

    from twilio.rest import Client
    client = Client(account_sid, auth_token)
    since = datetime.utcnow() - timedelta(minutes=since_minutes)

    replies = []
    try:
        messages = client.messages.list(date_sent_after=since, direction="inbound")
        for msg in messages:
            replies.append({
                "from": msg.from_,
                "body": msg.body,
                "sid": msg.sid,
                "date_sent": msg.date_sent,
            })
    except Exception:
        pass

    return replies


def _normalize_number(number):
    """Ensure number has whatsapp: prefix."""
    if number.startswith("whatsapp:"):
        return number
    return f"whatsapp:{number}"
```

- [ ] **Étape 4 : Vérifier que les tests passent**

```bash
pytest tests/agent/test_whatsapp.py -v
```

Attendu : 5 tests PASSED

- [ ] **Étape 5 : Suite de tests complète**

```bash
pytest tests/ -v
```

Attendu : tous les tests précédents PASSED

- [ ] **Étape 6 : Commit**

```bash
git add modules/agent/channels/whatsapp.py tests/agent/test_whatsapp.py
git commit -m "feat: canal WhatsApp Twilio pour agent conversationnel"
```

---

## Task 11 : App Streamlit — Squelette + Paramètres

**Files:**
- Create: `app.py`

- [ ] **Étape 1 : Implémenter app.py (squelette avec onglet Paramètres fonctionnel)**

```python
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

# ===== PLACEHOLDER TABS =====
with tab_search:
    st.info("Onglet Recherche — implémenté en Task 12")

with tab_session:
    st.info("Onglet Session — implémenté en Task 13 et 14")

with tab_history:
    st.info("Onglet Historique — implémenté en Task 15")
```

- [ ] **Étape 2 : Lancer l'application et vérifier**

```bash
streamlit run app.py
```

Ouvrir `http://localhost:8501`. Vérifier :
- Les 4 onglets s'affichent
- L'onglet Paramètres fonctionne (saisie, sauvegarde dans .env)
- Aucune erreur dans la console

- [ ] **Étape 3 : Commit**

```bash
git add app.py
git commit -m "feat: squelette Streamlit + onglet Paramètres complet"
```

---

## Task 12 : Onglet Recherche & Génération

**Files:**
- Modify: `app.py` — remplacer le placeholder `tab_search`

- [ ] **Étape 1 : Remplacer le bloc `with tab_search:` dans app.py**

Remplacer:
```python
with tab_search:
    st.info("Onglet Recherche — implémenté en Task 12")
```

Par:
```python
with tab_search:
    from modules.sirene import search_companies
    from modules.bodacc import enrich_leads
    from modules.scoring import score_leads_batch
    from modules.export import leads_to_csv
    import json
    from datetime import date

    col_form, col_stats = st.columns([2, 1])

    with col_form:
        st.subheader("🎯 Configurer la recherche")
        with st.form("search_form"):
            secteur = st.text_input("Secteur d'activité ou code APE", placeholder="Ex: expertise comptable, 6630Z, notaire…")
            col1, col2 = st.columns(2)
            with col1:
                departement = st.text_input("Département(s)", placeholder="Ex: 69, 75, 13")
            with col2:
                nb_leads = st.selectbox("Nombre de leads", [50, 100, 150, 200, 300], index=2)

            col3, col4 = st.columns(2)
            with col3:
                taille = st.selectbox("Taille entreprise", ["Toutes", "TPE (0-9)", "PME (10-49)", "ETI (50-249)", "Grande (250+)"], index=0)
            with col4:
                age_max = st.selectbox("Ancienneté max", ["Toutes", "3 mois", "6 mois", "1 an", "3 ans", "5 ans"], index=0)

            use_bodacc = st.checkbox("Enrichir avec Bodacc (signaux de cession/création)", value=True)
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

        progress.progress(55, text="Scoring IA (Claude)…")

        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
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

        for lead in filtered:
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
                    st.markdown(f"**Signaux :** {' · '.join(signaux) if signaux else '—'}")
                with col_b:
                    st.markdown(f"**SIRET :** `{lead.get('siret', '')}`")
                    st.markdown(f"**Raison :** {lead.get('raison', '')}")

                st.markdown("**Message LinkedIn :**")
                st.text_area("", value=lead.get("message_linkedin", ""), height=100, key=f"msg_li_{lead.get('siret', '')}", label_visibility="collapsed")
                st.markdown("**Message Email :**")
                st.text_area("", value=lead.get("message_email", ""), height=120, key=f"msg_em_{lead.get('siret', '')}", label_visibility="collapsed")
```

- [ ] **Étape 2 : Vérifier dans le navigateur**

```bash
streamlit run app.py
```

- Remplir le formulaire avec "expertise comptable", département "69", 50 leads
- Cliquer "Générer" — la barre de progression s'affiche
- Des vrais résultats SIRENE apparaissent dans les expanders
- L'export CSV télécharge un fichier valide

- [ ] **Étape 3 : Commit**

```bash
git add app.py
git commit -m "feat: onglet Recherche avec vraies APIs SIRENE + Bodacc + scoring Claude"
```

---

## Task 13 : Onglet Session — Mode Manuel

**Files:**
- Modify: `app.py` — remplacer le placeholder `tab_session`

- [ ] **Étape 1 : Remplacer le bloc `with tab_session:` dans app.py**

Remplacer:
```python
with tab_session:
    st.info("Onglet Session — implémenté en Task 13 et 14")
```

Par:
```python
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
                # Agent IA — implémenté en Task 14
                st.info("Mode Agent IA — implémenté en Task 14")
```

- [ ] **Étape 2 : Vérifier dans le navigateur**

- Générer des leads (onglet Recherche)
- Aller dans Session
- Cliquer sur les leads dans la queue
- Tester les boutons Envoyé / Plus tard / Passer / Suivant
- Vérifier que les statuts changent (icônes dans la queue)

- [ ] **Étape 3 : Commit**

```bash
git add app.py
git commit -m "feat: onglet Session mode manuel — file d'attente et statuts"
```

---

## Task 14 : Onglet Session — Mode Agent IA

**Files:**
- Modify: `app.py` — remplacer le placeholder `# Agent IA — implémenté en Task 14`

- [ ] **Étape 1 : Remplacer le placeholder agent dans `with tab_session:`**

Remplacer:
```python
            else:
                # Agent IA — implémenté en Task 14
                st.info("Mode Agent IA — implémenté en Task 14")
```

Par:
```python
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
                                calendly = os.getenv("CALENDLY_URL", "")
                                result = qualify_response(lead, manual_reply, conv_manager, calendly)

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
```

- [ ] **Étape 2 : Vérifier dans le navigateur**

- Générer des leads, aller en Session
- Basculer un lead en mode "Agent IA"
- Cliquer "Envoyer via agent" (sans email configuré → message d'erreur attendu)
- Avec un email configuré : vérifier que le message part
- Saisir manuellement une réponse → vérifier que l'agent répond et met à jour le statut
- Tester "Je prends la main"

- [ ] **Étape 3 : Commit**

```bash
git add app.py
git commit -m "feat: onglet Session mode Agent IA — envoi + qualification + takeover"
```

---

## Task 15 : Onglet Historique

**Files:**
- Modify: `app.py` — remplacer le placeholder `tab_history`

- [ ] **Étape 1 : Remplacer le bloc `with tab_history:` dans app.py**

Remplacer:
```python
with tab_history:
    st.info("Onglet Historique — implémenté en Task 15")
```

Par:
```python
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
```

- [ ] **Étape 2 : Vérifier dans le navigateur**

- Aller dans l'onglet Historique après avoir fait une session
- Vérifier que les sessions apparaissent avec leurs métriques
- Ouvrir une session, filtrer par statut
- Vérifier les conversations agent (si des leads en mode agent existent)

- [ ] **Étape 3 : Commit**

```bash
git add app.py
git commit -m "feat: onglet Historique sessions et conversations"
```

---

## Task 16 : Tests finaux et vérification globale

**Files:**
- Aucun nouveau fichier

- [ ] **Étape 1 : Lancer la suite de tests complète**

```bash
pytest tests/ -v --tb=short
```

Attendu : tous les tests PASSED (aucun FAILED)

- [ ] **Étape 2 : Vérifier le lancement via START.bat**

Double-cliquer sur `START.bat`. Vérifier :
- Première exécution : crée le venv et installe les packages sans erreur
- Le navigateur s'ouvre sur `http://localhost:8501`
- Les 4 onglets sont accessibles
- L'onglet Paramètres permet de saisir une clé Claude

- [ ] **Étape 3 : Test de bout en bout**

1. Saisir la clé API Claude dans Paramètres → Sauvegarder
2. Onglet Recherche : chercher "expertise comptable" en département "69", 50 leads
3. Vérifier que les résultats sont de vraies entreprises lyonnaises
4. Lancer la session → traiter 3 leads en manuel
5. Tester l'export CSV → vérifier qu'il s'ouvre dans Excel
6. Onglet Historique → vérifier que la session est enregistrée

- [ ] **Étape 4 : Commit final**

```bash
git add .
git commit -m "feat: ProspectEngine Python — version complète avec agent conversationnel"
```
