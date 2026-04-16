@echo off
title ProspectEngine
cd /d "%~dp0"

echo === ProspectEngine - Demarrage ===
echo Repertoire : %CD%
echo.

if not exist venv\ (
    echo [1/3] Creation de l'environnement Python...
    python -m venv venv
    if errorlevel 1 (
        echo ERREUR : python introuvable ou venv impossible.
        echo Verifiez que Python 3.10+ est installe et dans le PATH.
        pause
        exit /b 1
    )
    echo OK - venv cree.
)

echo [2/3] Activation et installation des dependances...
call venv\Scripts\activate.bat

python -m pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 (
    echo ERREUR : pip install a echoue.
    pause
    exit /b 1
)
echo OK - dependances installees.

if not exist app.py (
    echo ERREUR : app.py introuvable dans %CD%
    pause
    exit /b 1
)

echo [3/3] Lancement de Streamlit...
echo Ouvrez http://localhost:8501 dans votre navigateur.
echo Pour arreter : fermez cette fenetre ou appuyez Ctrl+C
echo.

python -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false

echo.
echo Streamlit arrete.
pause
