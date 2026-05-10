@echo off
REM ============================================================================
REM Cravo Chatbot — Instalacao do servico Windows no servidor 10.10.100.10
REM
REM EXECUTAR REMOTAMENTE NO SERVIDOR (\\10.10.100.10) via RDP, como Admin.
REM
REM Pre-requisitos no servidor (todos ja existem):
REM   1. Python 3.10+ no PATH
REM   2. nssm.exe em C:\Tools\nssm.exe (ja instalado pelo OfertasMontadoras)
REM   3. URL Rewrite + ARR no IIS (ja instalados, comprovado em /credentials/)
REM   4. Backend ja copiado para D:\apps\cravo-chatbot\
REM      (rodar _deploy_backend.bat antes deste script)
REM
REM O que este script faz:
REM   - Cria/atualiza venv em D:\apps\cravo-chatbot\.venv
REM   - Instala dependencias do requirements.txt
REM   - Cria servico Windows "CravoChatbot_App" via NSSM, porta 8001
REM     (8000 ja ocupada pelo Hsr_VoiceCode FastAPI)
REM   - Inicia servico
REM ============================================================================
setlocal
set SERVICE=CravoChatbot_App
set NSSM=C:\Tools\nssm.exe
set APP_ROOT=D:\apps\cravo-chatbot
set PORT=8001

REM Validacoes
if not exist "%NSSM%" (
  echo [ERRO] nssm.exe nao encontrado em %NSSM%
  echo Instale-o em C:\Tools\ ou ajuste o caminho neste script.
  exit /b 1
)
if not exist "%APP_ROOT%\backend\app.py" (
  echo [ERRO] %APP_ROOT%\backend\app.py nao existe.
  echo Faca o deploy primeiro: rode _deploy_backend.bat na maquina local.
  exit /b 1
)
if not exist "%APP_ROOT%\.env" (
  echo [AVISO] %APP_ROOT%\.env NAO existe.
  echo Crie com a chave Anthropic:
  echo   ANTHROPIC_API_KEY=sk-ant-api03-...
  echo   ANTHROPIC_MODEL=claude-sonnet-4-6
  echo Continuar mesmo assim? Ctrl+C para cancelar.
  pause >nul
)

cd /d "%APP_ROOT%"

REM 1. Cria venv (idempotente)
if not exist "%APP_ROOT%\.venv" (
  echo [1/4] Criando venv...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo [ERRO] py -3 falhou. Verifique se Python 3.10+ esta no PATH.
    exit /b 1
  )
)

REM 2. Instala/atualiza dependencias
echo [2/4] Instalando dependencias do requirements.txt...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip --quiet
pip install -r backend\requirements.txt --quiet

REM 3. Remove servico anterior se existir
"%NSSM%" status %SERVICE% >nul 2>&1
if not errorlevel 1 (
  echo [3/4] Servico %SERVICE% ja existe. Atualizando...
  "%NSSM%" stop %SERVICE%
  timeout /t 3 /nobreak >nul
  "%NSSM%" remove %SERVICE% confirm
)

REM 4. Cria servico
echo [4/4] Instalando servico %SERVICE%...
"%NSSM%" install %SERVICE% "%APP_ROOT%\.venv\Scripts\python.exe"
"%NSSM%" set %SERVICE% AppParameters "-m uvicorn backend.app:app --host 127.0.0.1 --port %PORT%"
"%NSSM%" set %SERVICE% AppDirectory "%APP_ROOT%"
"%NSSM%" set %SERVICE% DisplayName "Cravo Chatbot - Mestre do Cravo"
"%NSSM%" set %SERVICE% Description "FastAPI + Anthropic Claude chatbot pedagogico para o site Tratados do Cravo (porta %PORT%)"
"%NSSM%" set %SERVICE% Start SERVICE_AUTO_START

REM Logs em arquivos rotacionados (1 MB cada)
if not exist "%APP_ROOT%\logs" mkdir "%APP_ROOT%\logs"
"%NSSM%" set %SERVICE% AppStdout "%APP_ROOT%\logs\stdout.log"
"%NSSM%" set %SERVICE% AppStderr "%APP_ROOT%\logs\stderr.log"
"%NSSM%" set %SERVICE% AppStdoutCreationDisposition 4
"%NSSM%" set %SERVICE% AppStderrCreationDisposition 4
"%NSSM%" set %SERVICE% AppRotateFiles 1
"%NSSM%" set %SERVICE% AppRotateOnline 1
"%NSSM%" set %SERVICE% AppRotateBytes 1048576

REM Inicia
"%NSSM%" start %SERVICE%
timeout /t 5 /nobreak >nul

echo.
echo ============================================================================
echo  Servico %SERVICE% instalado e rodando em http://127.0.0.1:%PORT%
echo  Logs: %APP_ROOT%\logs\
echo ============================================================================
echo.
echo Smoke test:
echo   curl http://127.0.0.1:%PORT%/api/health
echo.
echo Status:
sc query %SERVICE% | findstr /i "STATE"
echo.
echo Proximo passo: copiar deploy\web.config-cravo para o IIS:
echo   copy /Y deploy\web.config-cravo "D:\Websites\routepesquisa.com.br\cravo\web.config"
echo.
endlocal
