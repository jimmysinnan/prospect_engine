# ProspectEngine — État d'avancement

## Projet
Conversion de `prospect_engine.html` (démo HTML) en application Python/Streamlit fonctionnelle avec vraies APIs, scoring Claude, agent conversationnel Email+WhatsApp, et launcher double-clic Windows.

## Documents de référence
- **Spec complète** : `docs/superpowers/specs/2026-04-16-prospect-engine-python-design.md`
- **Plan d'implémentation** : `docs/superpowers/plans/2026-04-16-prospect-engine-python.md`

## Méthode d'exécution
Subagent-Driven Development — un sous-agent par tâche, review spec + qualité après chaque tâche.

## Avancement (2026-04-17)

### ✅ Ce qui est fait

- ✅ Setup projet (requirements.txt, .gitignore, START.bat, .env.example)
- ✅ DB SQLite (modules/db.py) — 7 tests PASSED
- ✅ SIRENE API (modules/sirene.py) — recherche entreprises sans clé API
- ✅ Bodacc flux (modules/bodacc.py) — enrichissement signaux
- ✅ Scoring Claude (modules/scoring.py) — score + signaux + messages
- ✅ Export CSV (modules/export.py) — format UTF-8 BOM Excel-compatible
- ✅ Google Maps (modules/google_maps.py) — extraction département + localisation
- ✅ Fix localisation DOM-TOM 972 (SIRENE + Google Maps)
- ✅ Sélecteur NAF prédéfini (17 codes) dans le formulaire de recherche
- ✅ Module enrichissement web multi-pages (email, tél, réseaux sociaux, maturité digitale)
- ✅ 3 variantes email outbound par prospect (Direct / Storytelling / ROI)

### 🔲 Tasks restantes

| Task | Description |
|---|---|
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

### Derniers commits

- `34e99c7` — feat: UI enrichissement web + 3 onglets email (Direct/Storytelling/ROI) + maturité digitale
- `c8e323f` — feat: 3 variantes email par prospect (direct / storytelling / ROI)
- `153babc` — feat: enrichissement web multi-pages (contact + mentions légales + footer)
- `3e22e44` — feat: sélecteur NAF prédéfini dans le formulaire de recherche
- `010181d` — fix: normalisation localisation DOM-TOM Google Maps (972 → Martinique, region=mq)
- `3773f0c` — fix: extraction département DOM-TOM depuis code_postal (fallback SIRENE)

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
