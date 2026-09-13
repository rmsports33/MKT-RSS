@echo off
title Iniciar MKT Flow
color 0A
echo Iniciando servidor...
call venv\Scripts\activate.bat
python api.py
pause