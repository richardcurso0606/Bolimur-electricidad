@echo off
title BOLIMUR REBT PRO - Launcher
echo ========================================================
echo   INICIANDO BOLIMUR REBT PRO - INGENIERIA ELECTRICA
echo ========================================================
echo.
echo Abriendo aplicacion en tu navegador...
cd /d "C:\Users\Usuario\Desktop\Bolimur"
start "" http://localhost:8501
call .venv\Scripts\python.exe -m streamlit run inicio.py --server.port 8501
pause
