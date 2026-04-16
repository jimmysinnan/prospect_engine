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
