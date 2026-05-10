@echo off
REM ============================================================================
REM Cravo Chatbot - Instalar API como Servico Windows (NSSM + uvicorn)
REM
REM Padrao copiado do HSR_VoiceCode/deploy/install_api_service.bat
REM Adaptado para porta 8001 (8000 ja esta ocupada pelo HSR VoiceCode).
REM
REM EXECUTAR REMOTAMENTE NO SERVIDOR (\\10.10.100.10) via RDP, como Admin.
REM
REM Pre-requisitos no servidor:
REM   1. Backend ja copiado para D:\apps\cravo-chatbot\ (rodar _deploy_backend.bat)
REM   2. .env criado em D:\apps\cravo-chatbot\ com ANTHROPIC_API_KEY
REM   3. Python 3.10+ instalado (ja existe no servidor)
REM   4. nssm.exe em deploy\ (bundled com este script)
REM ============================================================================
echo ========================================================
echo   Cravo Chatbot - Instalar API como Servico Windows
echo ========================================================
echo.

set INSTALL_DIR=D:\apps\cravo-chatbot
set SERVICE_NAME=CravoChatbot_API
set NSSM=%INSTALL_DIR%\deploy\nssm.exe
set PORT=8001

REM Verificar se esta rodando como admin
net session >nul 2>&1
if errorlevel 1 (
    echo ERRO: Execute este script como Administrador!
    pause
    exit /b 1
)

REM Verificar NSSM
if not exist "%NSSM%" (
    echo ERRO: nssm.exe nao encontrado em %NSSM%
    echo NSSM deveria estar bundled em deploy\nssm.exe
    pause
    exit /b 1
)

REM Verificar backend
if not exist "%INSTALL_DIR%\backend\app.py" (
    echo ERRO: %INSTALL_DIR%\backend\app.py nao existe.
    echo Rode _deploy_backend.bat na maquina dev primeiro.
    pause
    exit /b 1
)

REM Verificar .env
if not exist "%INSTALL_DIR%\.env" (
    echo ERRO: Arquivo .env nao encontrado em %INSTALL_DIR%\.env
    echo Crie com:
    echo   ANTHROPIC_API_KEY=sk-ant-api03-...
    echo   ANTHROPIC_MODEL=claude-sonnet-4-6
    pause
    exit /b 1
)

REM Criar venv se nao existir
if not exist "%INSTALL_DIR%\venv\Scripts\python.exe" (
    echo.
    echo [setup] Criando venv...
    echo -------------------------------------------------------
    py -3 -m venv "%INSTALL_DIR%\venv"
    if errorlevel 1 (
        echo ERRO: Python 3 nao encontrado. Instale Python 3.10+ no servidor.
        pause
        exit /b 1
    )
    echo Venv criado.
)

REM Instalar dependencias
echo.
echo [setup] Instalando dependencias do requirements.txt...
echo -------------------------------------------------------
"%INSTALL_DIR%\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%INSTALL_DIR%\venv\Scripts\pip.exe" install -r "%INSTALL_DIR%\backend\requirements.txt"
if errorlevel 1 (
    echo AVISO: Algumas dependencias podem ter falhado. Verifique acima.
)

REM Criar pasta de logs
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"

echo.
echo [1/4] Removendo servico anterior (se existir)...
echo -------------------------------------------------------
"%NSSM%" stop %SERVICE_NAME% >nul 2>&1
"%NSSM%" remove %SERVICE_NAME% confirm >nul 2>&1
echo OK.

echo.
echo [2/4] Criando servico %SERVICE_NAME%...
echo -------------------------------------------------------
"%NSSM%" install %SERVICE_NAME% "%INSTALL_DIR%\venv\Scripts\python.exe"
"%NSSM%" set %SERVICE_NAME% AppParameters "-m uvicorn backend.app:app --host 127.0.0.1 --port %PORT%"
"%NSSM%" set %SERVICE_NAME% AppDirectory "%INSTALL_DIR%"
"%NSSM%" set %SERVICE_NAME% Description "Cravo Chatbot - FastAPI Backend (uvicorn porta %PORT%) - Mestre do Cravo"
"%NSSM%" set %SERVICE_NAME% Start SERVICE_AUTO_START
"%NSSM%" set %SERVICE_NAME% AppStdout "%INSTALL_DIR%\logs\api_stdout.log"
"%NSSM%" set %SERVICE_NAME% AppStderr "%INSTALL_DIR%\logs\api_stderr.log"
"%NSSM%" set %SERVICE_NAME% AppStdoutCreationDisposition 4
"%NSSM%" set %SERVICE_NAME% AppStderrCreationDisposition 4
"%NSSM%" set %SERVICE_NAME% AppRotateFiles 1
"%NSSM%" set %SERVICE_NAME% AppRotateOnline 1
"%NSSM%" set %SERVICE_NAME% AppRotateBytes 5242880
echo Servico criado.

echo.
echo [3/4] Iniciando servico...
echo -------------------------------------------------------
"%NSSM%" start %SERVICE_NAME%
timeout /t 3 >nul

echo.
echo [4/4] Verificando...
echo -------------------------------------------------------
"%NSSM%" status %SERVICE_NAME%
echo.

REM Testar health endpoint
echo Testando API...
timeout /t 2 >nul
curl -s http://localhost:%PORT%/api/health
if errorlevel 1 (
    echo.
    echo AVISO: API nao respondeu ainda. Aguarde alguns segundos e teste:
    echo   curl http://localhost:%PORT%/api/health
    echo.
    echo Verifique os logs em:
    echo   %INSTALL_DIR%\logs\api_stdout.log
    echo   %INSTALL_DIR%\logs\api_stderr.log
) else (
    echo.
    echo API respondendo OK!
)

echo.
echo ========================================================
echo   Servico %SERVICE_NAME% instalado!
echo.
echo   Comandos uteis:
echo     nssm start %SERVICE_NAME%     (iniciar)
echo     nssm stop %SERVICE_NAME%      (parar)
echo     nssm restart %SERVICE_NAME%   (reiniciar)
echo     nssm status %SERVICE_NAME%    (ver status)
echo     nssm edit %SERVICE_NAME%      (editar config)
echo.
echo   O servico inicia automaticamente com o Windows.
echo   Logs em: %INSTALL_DIR%\logs\
echo.
echo   Smoke test publico (apos o web.config no IIS):
echo     curl https://routepesquisa.com.br/cravo/api/health
echo ========================================================
pause
