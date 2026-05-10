@echo off
REM Inicia o backend FastAPI do chatbot do Cravo na porta 8000.
REM Pre-requisito: Python 3.10+ no PATH e ".env" preenchido em C:\Outros\Cravo\.env

setlocal
cd /d "%~dp0"

REM Cria venv local se ainda nao existir
if not exist ".venv" (
    echo [setup] Criando venv...
    py -3 -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo [setup] Instalando/atualizando dependencias...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo.
echo [run] Subindo backend em http://127.0.0.1:8000
echo       Health: http://127.0.0.1:8000/api/health
echo       Topics: http://127.0.0.1:8000/api/topics
echo.

python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

endlocal
