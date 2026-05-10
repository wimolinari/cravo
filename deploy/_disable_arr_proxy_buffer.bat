@echo off
REM ============================================================================
REM Cravo Chatbot - Desabilitar buffer do ARR proxy (passo 2 de SSE streaming)
REM
REM O appcmd previo (set RESPONSE_BUFFER_LIMIT) habilitou o uso da var no
REM nivel do site. Mas o ARR tem PROPRIO buffer no nivel de proxy server
REM (responseBufferThreshold padrao = 4096 bytes), que ainda agrupa chunks
REM antes de enviar ao client. Sintoma: TTFB ~30s para respostas longas,
REM e mesmo respostas curtas chegam em chunks de ~700ms (nao palavra-por-palavra).
REM
REM Este script:
REM   - Zera responseBufferThreshold do ARR proxy (nivel server)
REM   - Restart IIS
REM
REM Apos rodar, primeira resposta (cache miss) ainda demora 5-10s.
REM Mas perguntas seguintes (cache hit) devem ter TTFB ~1-2s e chunks
REM chegando palavra-por-palavra.
REM
REM EXECUTAR REMOTAMENTE NO SERVIDOR via RDP, como Admin.
REM ============================================================================
echo ========================================================
echo   Cravo Chatbot - Desabilitar ARR Proxy Buffer
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

echo [1/3] Estado atual do ARR proxy...
echo -------------------------------------------------------
"%APPCMD%" list config -section:system.webServer/proxy 2>&1
echo.

echo [2/3] Desabilitando response buffer do ARR...
echo -------------------------------------------------------
REM responseBufferThreshold=0 desabilita buffer (envia chunks imediatamente)
"%APPCMD%" set config -section:system.webServer/proxy /responseBufferThreshold:"0" /commit:apphost
if errorlevel 1 (
    echo ERRO: Falha ao desabilitar. Pode ser que /proxy section nao esteja registrada.
    echo Vamos tentar via webFarms config.
    "%APPCMD%" set config -section:system.webServer/proxy /enabled:"true" /preserveHostHeader:"true" /reverseRewriteHostInResponseHeaders:"true" /responseBufferThreshold:"0" /commit:apphost
)

REM Tambem desabilitar output cache para SSE
echo.
echo [3/3] Desabilitando output cache para text/event-stream...
echo -------------------------------------------------------
"%APPCMD%" set config -section:system.webServer/caching /enabled:"false" /enableKernelCache:"false" /commit:apphost 2>&1
echo.

echo Reciclando IIS...
echo -------------------------------------------------------
iisreset /restart

echo.
echo ========================================================
echo  Smoke test apos fix:
echo    curl -N --no-buffer -X POST ^
echo      https://routepesquisa.com.br/cravo/api/chat ^
echo      -H "Content-Type: application/json" ^
echo      --data "{\"question\":\"oi\",\"history\":[],\"lang\":\"pt\"}"
echo.
echo  Esperado: cada chunk chega instantaneamente (gap ~30-50ms entre chunks)
echo  Anterior: gaps de 700ms entre chunks
echo ========================================================
pause
