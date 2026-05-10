@echo off
REM ============================================================================
REM Cravo Chatbot - Deploy do backend para o servidor 10.10.100.10
REM
REM EXECUTAR LOCALMENTE (sua maquina dev). Faz robocopy backend + knowledge
REM para D:\apps\cravo-chatbot\ no servidor.
REM Apos rodar este, conectar via RDP no servidor e rodar _install_service.bat
REM (que esta dentro de D:\apps\cravo-chatbot\deploy\).
REM ============================================================================
setlocal
set SRC=C:\Outros\Cravo
set DST=\\10.10.100.10\d$\apps\cravo-chatbot

echo ============================================================================
echo  DEPLOY BACKEND CRAVO
echo  SRC: %SRC%
echo  DST: %DST%
echo ============================================================================
echo.

REM Garante que pasta destino existe
if not exist "%DST%" mkdir "%DST%"

REM 1. Codigo do backend (sem .venv, __pycache__, .pytest_cache)
echo [1/3] Copiando backend...
robocopy "%SRC%\chatbot\backend" "%DST%\backend" /E /R:2 /W:2 /MT:4 /NFL /NDL /XD __pycache__ .venv .pytest_cache

REM 2. Knowledge base
echo [2/3] Copiando knowledge base...
robocopy "%SRC%\chatbot\knowledge" "%DST%\knowledge" /E /R:2 /W:2 /MT:4 /NFL /NDL

REM 3. Scripts e config de deploy (incluindo _install_service.bat)
echo [3/3] Copiando scripts de deploy...
robocopy "%SRC%\deploy" "%DST%\deploy" *.bat web.config-cravo /R:2 /W:2 /NFL /NDL

echo.
echo ============================================================================
echo  Deploy concluido. Proximos passos no servidor:
echo ============================================================================
echo.
echo  1. Conecte via RDP em 10.10.100.10
echo.
echo  2. Crie o arquivo .env em %DST%\:
echo       ANTHROPIC_API_KEY=sk-ant-api03-...
echo       ANTHROPIC_MODEL=claude-sonnet-4-6
echo     (pode copiar de C:\Outros\Cravo\.env localmente; NAO incluido no robocopy
echo      por seguranca - chaves nao devem trafegar por compartilhamento publico)
echo.
echo  3. Rode no servidor (em prompt admin):
echo       cd D:\apps\cravo-chatbot
echo       deploy\_install_service.bat
echo.
echo  4. Aplicar web.config no IIS site:
echo       copy /Y D:\apps\cravo-chatbot\deploy\web.config-cravo ^
^         D:\Websites\routepesquisa.com.br\cravo\web.config
echo.
echo  5. Smoke test no servidor:
echo       curl http://127.0.0.1:8001/api/health
echo.
echo  6. Smoke test publico (depois do passo 4):
echo       curl https://routepesquisa.com.br/cravo/api/health
echo.
endlocal
