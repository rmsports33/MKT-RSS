@echo off
title Instalador MKT Flow
color 0A
echo ================================================
echo    MKT FLOW 3.0 - INSTALADOR
echo ================================================
echo.
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Baixe em https://www.python.org/downloads/
    pause
    exit /b
)
echo Python encontrado!
echo.
echo Criando ambiente virtual...
python -m venv venv
call venv\Scripts\activate.bat
echo Instalando dependencias...
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo INSTALACAO CONCLUIDA!
echo Execute iniciar.bat para rodar o servidor.
pause