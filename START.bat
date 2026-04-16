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
if errorlevel 1 (
    echo ERREUR : L'installation des dependances a echoue. Verifiez votre connexion internet.
    pause
    exit /b 1
)

if not exist app.py (
    echo ERREUR : app.py introuvable. Verifiez que tous les fichiers sont presents.
    pause
    exit /b 1
)

streamlit run app.py --server.port 8501 --browser.gatherUsageStats false
pause
