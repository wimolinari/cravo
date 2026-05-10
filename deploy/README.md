# Deploy do backend Cravo (M1)

## Arquitetura

```
Internet → routepesquisa.com.br/cravo/api/*
              ↓ (IIS URL Rewrite, mesmo origin)
            http://localhost:8001/api/*
              ↓
        FastAPI uvicorn (servico Windows CravoChatbot_App)
              ↓
        Anthropic Claude API
```

- Site estático: `D:\Websites\routepesquisa.com.br\cravo\`
- Backend: `D:\apps\cravo-chatbot\` (mesma máquina, porta 8001)
- Reverse proxy via IIS URL Rewrite + ARR (mesmo padrão de `/credentials/api/`)

## Por que porta 8001 (e não 8000)

A porta 8000 já está ocupada pelo backend FastAPI do Hsr_VoiceCode (que serve `/credentials/api/`). O Cravo usa 8001 para evitar conflito.

## Passo a passo (deploy inicial)

### 1. Na máquina dev (sua máquina)

Rode:

```cmd
C:\Outros\Cravo\deploy\_deploy_backend.bat
```

Isso copia via robocopy:
- `chatbot/backend/` → `\\10.10.100.10\d$\apps\cravo-chatbot\backend\`
- `chatbot/knowledge/` → `\\10.10.100.10\d$\apps\cravo-chatbot\knowledge\`
- `deploy/` → `\\10.10.100.10\d$\apps\cravo-chatbot\deploy\`

### 2. Conecte ao servidor via RDP (10.10.100.10)

### 3. No servidor, crie o `.env` em `D:\apps\cravo-chatbot\`

```
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-sonnet-4-6
```

> **Nunca** commitar essa chave. Pode copiar de `C:\Outros\Cravo\.env` da sua máquina dev (manualmente, pelo RDP).

### 4. Rode (prompt admin):

```cmd
cd D:\apps\cravo-chatbot
deploy\_install_service.bat
```

Isso:
- Cria venv Python
- Instala `requirements.txt`
- Registra serviço Windows `CravoChatbot_App` via NSSM (auto-start)
- Inicia o serviço (porta 8001)

Smoke test no servidor:
```cmd
curl http://127.0.0.1:8001/api/health
```
Esperado:
```json
{"status":"ok","model":"claude-sonnet-4-6","kb":{...}}
```

### 5. Aplique o web.config no IIS

```cmd
copy /Y D:\apps\cravo-chatbot\deploy\web.config-cravo D:\Websites\routepesquisa.com.br\cravo\web.config
```

(O IIS recarrega automaticamente quando o web.config muda.)

### 6. Smoke test público

```cmd
curl https://routepesquisa.com.br/cravo/api/health
```
Esperado: o mesmo JSON do passo 4.

### 7. Volte à máquina dev e rode:

```bat
C:\Outros\Cravo\deploy\_finalize_deploy.bat
```

Isso:
- Atualiza `inject-chatbot.py` para apontar `cravo-chat-api` para `https://routepesquisa.com.br/cravo/api`
- Re-injeta em todas as 72 páginas
- Faz `_deploy.bat` (publica site)

A partir desse momento, o chat funciona publicamente para qualquer visitante.

## Atualizações futuras do backend

Quando você mudar `app.py`, `requirements.txt` ou knowledge:

1. Na máquina dev:
   ```cmd
   C:\Outros\Cravo\deploy\_deploy_backend.bat
   ```
2. Via RDP no servidor:
   ```cmd
   sc stop CravoChatbot_App
   D:\apps\cravo-chatbot\.venv\Scripts\pip install -r D:\apps\cravo-chatbot\backend\requirements.txt
   sc start CravoChatbot_App
   ```

(Ou rodar `_install_service.bat` de novo — é idempotente, só recria o serviço.)

## Comandos úteis no servidor

```cmd
:: Status do serviço
sc query CravoChatbot_App

:: Logs
type D:\apps\cravo-chatbot\logs\stdout.log
type D:\apps\cravo-chatbot\logs\stderr.log

:: Reiniciar
sc stop CravoChatbot_App && timeout /t 3 && sc start CravoChatbot_App

:: Verificar porta
netstat -ano | findstr :8001
```

## Custo estimado

Com tráfego baixo-médio:
- Cache write (1× por sessão): 80 K tokens × $3.75/M = **$0.30**
- Cache read (cada turno): 80 K tokens × $0.30/M = **$0.024**
- Output: ~500 tokens × $15/M = **$0.0075**

**Por turno em conversa quente: ~$0.03**
**Primeira mensagem da sessão: ~$0.31**

Para 1000 perguntas/dia: ~**$30/mês** (estimativa otimista, depende muito de cache hit rate).

## Troubleshooting

| Sintoma | Causa | Fix |
|---|---|---|
| `502 Bad Gateway` em `/cravo/api/health` | serviço CravoChatbot_App não está rodando | `sc start CravoChatbot_App` |
| Health retorna mas chat trava streaming | RESPONSE_BUFFER_LIMIT não setado no web.config | já está no `web.config-cravo`; verificar se foi aplicado |
| Serviço não sobe | `.env` ausente ou ANTHROPIC_API_KEY inválida | criar `.env` em `D:\apps\cravo-chatbot\` |
| Cache miss em toda mensagem | TTL do prompt cache (5min) expirou | normal — só primeira msg da sessão paga $0.30 |
| Erro de SSL/CORS | meta tag aponta pra URL errada | rodar `_finalize_deploy.bat` |
