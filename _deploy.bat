@echo off
REM Deploy do site Tratados do Cravo
REM SRC: C:\Outros\Cravo\site
REM DST: \\10.10.100.10\d$\Websites\routepesquisa.com.br\cravo
REM
REM Usa /E (cópia recursiva sem deletar destino) na primeira publicação.
REM Em deploys subsequentes pode-se trocar para /MIR (espelha = apaga extras).

SET SRC=C:\Outros\Cravo\site
SET DST=\\10.10.100.10\d$\Websites\routepesquisa.com.br\cravo

echo.
echo ============================================================
echo   Deploy: Tratados do Cravo
echo   SRC: %SRC%
echo   DST: %DST%
echo ============================================================
echo.

robocopy "%SRC%" "%DST%" /E /R:2 /W:2 /MT:8 /NFL /NDL
SET RC=%ERRORLEVEL%

echo.
echo ============================================================
echo   Robocopy exit code: %RC%
echo   (0=nada a fazer, 1=copiados, 2-7=avisos, 8+=ERRO)
echo ============================================================

REM Robocopy retorna codigos < 8 como sucesso
if %RC% LSS 8 (
  exit /b 0
) else (
  exit /b %RC%
)
