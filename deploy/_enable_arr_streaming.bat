@echo off
REM ============================================================================
REM Cravo Chatbot - Habilitar streaming SSE via ARR
REM
REM Por padrao, o IIS/ARR ignora serverVariables que nao estao na "allowed list"
REM do servidor. Sem RESPONSE_BUFFER_LIMIT permitido, o ARR bufferiza a resposta
REM inteira antes de enviar ao client - SSE streaming nao funciona.
REM
REM Sintoma sem este fix: chat fica "pensando" 30s+ e ai aparece tudo de uma vez.
REM Sintoma com este fix: cada palavra chega instantaneamente conforme Claude
REM gera (TTFB ~2s, palavra por palavra).
REM
REM EXECUTAR REMOTAMENTE NO SERVIDOR via RDP, como Admin.
REM ============================================================================
echo ========================================================
echo   Cravo Chatbot - Habilitar SSE Streaming via ARR
echo ========================================================
echo.

REM Verificar admin
net session >nul 2>&1
if errorlevel 1 (
    echo ERRO: Execute este script como Administrador!
    pause
    exit /b 1
)

set APPCMD=%windir%\system32\inetsrv\appcmd.exe

if not exist "%APPCMD%" (
    echo ERRO: appcmd.exe nao encontrado em %APPCMD%
    echo IIS Management Tools nao esta instalado?
    pause
    exit /b 1
)

echo [1/2] Verificando estado atual...
echo -------------------------------------------------------
"%APPCMD%" list config -section:system.webServer/rewrite/allowedServerVariables 2>&1 | findstr /i "RESPONSE_BUFFER_LIMIT"
if errorlevel 1 (
    echo RESPONSE_BUFFER_LIMIT NAO esta na allowed list. Adicionando...
) else (
    echo RESPONSE_BUFFER_LIMIT JA esta na allowed list. Nada a fazer.
    goto :verify
)

echo.
echo [2/2] Adicionando RESPONSE_BUFFER_LIMIT a allowed server variables...
echo -------------------------------------------------------
"%APPCMD%" set config -section:system.webServer/rewrite/allowedServerVariables /+"[name='RESPONSE_BUFFER_LIMIT']" /commit:apphost
if errorlevel 1 (
    echo ERRO: Falha ao adicionar. Tentar novamente ou aplicar manualmente:
    echo.
    echo   IIS Manager -^> servidor -^> URL Rewrite -^> View Server Variables
    echo   -^> Add -^> RESPONSE_BUFFER_LIMIT
    pause
    exit /b 1
)
echo OK adicionado.

:verify
echo.
echo Reciclando IIS para aplicar mudanca...
echo -------------------------------------------------------
iisreset /restart
echo.

echo ========================================================
echo  Smoke test apos fix:
echo    curl -N https://routepesquisa.com.br/cravo/api/chat ^
echo         -H "Content-Type: application/json" ^
echo         --data "{\"question\":\"oi\",\"history\":[],\"lang\":\"pt\"}"
echo.
echo  Esperado: chunks chegando palavra por palavra (TTFB ~2s)
echo ========================================================
pause
