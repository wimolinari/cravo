@echo off
REM ============================================================================
REM Cravo Chatbot - Finalizacao do deploy backend publico
REM
REM Roda LOCALMENTE depois que o servico CravoChatbot_App estiver UP no
REM servidor e o web.config aplicado.
REM
REM Este script:
REM   1. Atualiza inject-chatbot.py com URL publica
REM   2. Re-injeta meta cravo-chat-api em todas as 72 paginas
REM   3. Re-deploya o site
REM   4. Smoke test publico /cravo/api/health
REM ============================================================================
setlocal
set ROOT=C:\Outros\Cravo
set PROD_API=https://routepesquisa.com.br/cravo/api

echo ============================================================================
echo  FINALIZE DEPLOY - apontando chatbot para %PROD_API%
echo ============================================================================
echo.

REM 1. Smoke test antes (sanity check: backend publico esta UP?)
echo [1/4] Verificando backend publico...
curl -sf %PROD_API%/health -m 8
if errorlevel 1 (
  echo.
  echo [ERRO] Backend publico em %PROD_API%/health nao respondeu.
  echo Ainda nao rodou _install_service.bat no servidor? Ou web.config nao aplicado?
  echo Cancelando finalize.
  exit /b 1
)
echo.
echo Backend OK. Continuando.
echo.

REM 2. Atualiza DEFAULT_API no inject-chatbot.py (idempotente)
echo [2/4] Atualizando DEFAULT_API em inject-chatbot.py...
powershell -NoProfile -Command "(Get-Content -Raw '%ROOT%\chatbot\inject-chatbot.py') -replace 'DEFAULT_API\s*=\s*\"http://127\.0\.0\.1:8000\"', 'DEFAULT_API = \"%PROD_API%\"' | Set-Content -NoNewline '%ROOT%\chatbot\inject-chatbot.py'"

REM 3. Re-injeta em todas as 72 paginas
echo [3/4] Re-injetando chatbot em todas as paginas...
cd /d "%ROOT%\chatbot\backend"
.venv\Scripts\python.exe ..\inject-chatbot.py

REM 4. Deploy site
echo [4/4] Deploy do site para producao...
cd /d "%ROOT%"
call _deploy.bat

echo.
echo ============================================================================
echo  Smoke test final:
echo ============================================================================
curl -s https://routepesquisa.com.br/cravo/index.html | findstr "cravo-chat-api"
echo.
curl -s %PROD_API%/health
echo.
echo ============================================================================
echo  Finalize concluido. Chatbot agora esta publico em routepesquisa.com.br/cravo/
echo ============================================================================
endlocal
