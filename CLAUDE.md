# ProspectEngine — État d'avancement

## Projet
Conversion de `prospect_engine.html` (démo HTML) en application Python/Streamlit fonctionnelle avec vraies APIs, scoring Claude, agent conversationnel Email+WhatsApp, et launcher double-clic Windows.

## Documents de référence
- **Spec complète** : `docs/superpowers/specs/2026-04-16-prospect-engine-python-design.md`
- **Plan d'implémentation** : `docs/superpowers/plans/2026-04-16-prospect-engine-python.md`

## Méthode d'exécution
Subagent-Driven Development — un sous-agent par tâche, review spec + qualité après chaque tâche.

## Avancement (2026-04-16)

### ✅ Tasks terminées

| Task | Fichiers | Commit |
|---|---|---|
| Task 1 : Setup projet | requirements.txt, .gitignore, START.bat, .env.example, __init__.py, data/.gitkeep | `1c0cf77` + `e1c2763` |
| Task 2 : db.py | modules/db.py, tests/test_db.py — 7 tests PASSED | `4a96147` |

### 🔲 Tasks restantes (Task 3 → 16)

| Task | Description |
|---|---|
| **Task 3** | `modules/sirene.py` — API recherche-entreprises.api.gouv.fr (sans clé, pagination) |
| **Task 4** | `modules/bodacc.py` — flux Bodacc data.gouv.fr, enrichissement signaux |
| **Task 5** | `modules/scoring.py` — Claude Haiku scoring, score+signaux+messages |
| **Task 6** | `modules/export.py` — CSV Excel-compatible UTF-8 BOM |
| **Task 7** | `modules/agent/prompts.py` + `modules/agent/conversation.py` — scripts 3 phases + ConversationManager |
| **Task 8** | `modules/agent/qualifier.py` — analyse réponse prospect, décision IA |
| **Task 9** | `modules/agent/channels/email.py` — SMTP/IMAP |
| **Task 10** | `modules/agent/channels/whatsapp.py` — Twilio polling |
| **Task 11** | `app.py` squelette + onglet Paramètres (sauvegarde .env via python-dotenv) |
| **Task 12** | `app.py` onglet Recherche & Génération (vraies APIs SIRENE + Bodacc + scoring) |
| **Task 13** | `app.py` onglet Session mode Manuel (file d'attente + statuts) |
| **Task 14** | `app.py` onglet Session mode Agent IA (toggle + qualification + takeover) |
| **Task 15** | `app.py` onglet Historique (sessions passées + conversations) |
| **Task 16** | Tests finaux + vérification bout en bout + START.bat |

## Architecture cible

```
prospect_engine/
├── START.bat              ← double-clic client Windows
├── requirements.txt
├── .env                   ← secrets locaux (jamais commités)
├── app.py                 ← Streamlit 4 onglets
├── modules/
│   ├── db.py              ✅ FAIT
│   ├── sirene.py          ← Task 3
│   ├── bodacc.py          ← Task 4
│   ├── scoring.py         ← Task 5
│   ├── export.py          ← Task 6
│   └── agent/
│       ├── prompts.py     ← Task 7
│       ├── conversation.py← Task 7
│       ├── qualifier.py   ← Task 8
│       └── channels/
│           ├── email.py   ← Task 9
│           └── whatsapp.py← Task 10
└── data/
    └── leads.db           ← SQLite local
```

## Choix techniques clés
- **SIRENE** : `https://recherche-entreprises.api.gouv.fr/search` — sans clé API
- **Bodacc** : `https://bodacc-datadica.fr/api/records/1.0/search/` — sans clé API
- **Scoring** : Claude `claude-haiku-4-5-20251001` — ~0.001€/lead
- **WhatsApp** : Twilio polling (pas de webhook — outil local)
- **Déploiement** : START.bat crée venv + installe deps automatiquement au premier lancement
- **Secrets** : uniquement dans `.env` local, jamais dans le code

## Pour reprendre
1. Lire ce fichier pour l'état d'avancement
2. Lire le plan complet : `docs/superpowers/plans/2026-04-16-prospect-engine-python.md`
3. Reprendre à la première task non cochée
4. Utiliser le skill `superpowers:subagent-driven-development`
