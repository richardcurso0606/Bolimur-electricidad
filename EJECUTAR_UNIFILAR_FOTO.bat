@echo off
title BOLIMUR - Extractor de Esquema Unifilar por Foto REBT
echo ========================================================
echo   BOLIMUR REBT - EXTRACTOR DE ESQUEMA UNIFILAR POR FOTO
echo   Modulo Independiente de Vision Artificial
echo ========================================================
echo.
echo Abriendo aplicacion en tu navegador...
cd /d "C:\Users\Usuario\Desktop\Bolimur"
start "" http://localhost:8502
call .venv\Scripts\python.exe -m streamlit run modulos\unifilar_foto.py --server.port 8502
pause
