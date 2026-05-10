# Chatbot do Cravo — Mestre do Cravo

Chatbot pedagógico para o site **Tratados do Cravo** (UFRJ 2013).
Usa Claude (Anthropic) com prompt caching, tendo como base de conhecimento
o texto integral dos 4 tratados, o glossário do site, o sitemap e o
inventário de imagens.

## Estrutura

```
chatbot/
├─ build-knowledge.py     # extrai PDF + glossário + sitemap + imagens
├─ inject-chatbot.py      # injeta CSS+JS no HTML de todas as páginas
├─ knowledge/             # gerado pelo build-knowledge.py
│   ├─ tratado_full.txt   # 170 KB ≈ 50 K tokens
│   ├─ section_*.txt      # por tratado
│   ├─ glossary.json      # 69 termos
│   ├─ sitemap.json       # 17 URLs
│   ├─ images.json        # 114 partituras
│   └─ topics.json        # 10 cards iniciais
└─ backend/
    ├─ app.py             # FastAPI + Anthropic SDK + prompt caching
    ├─ requirements.txt
    └─ run-backend.bat    # cria venv e sobe o servidor
```

## Como rodar localmente

### 1. Pré-requisitos

- Python 3.10+ no PATH (`py -3` no Windows).
- Arquivo `C:\Outros\Cravo\.env` contendo:

```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-6   # ou claude-opus-4-7
```

### 2. Build do knowledge base (uma vez, ou após mudar conteúdo)

```bash
cd C:/Outros/Cravo/chatbot
python build-knowledge.py
```

### 3. Subir backend

```bat
:: na pasta C:\Outros\Cravo\chatbot\backend
run-backend.bat
```

O script cria `.venv\` local, instala `requirements.txt` e sobe o servidor em
`http://127.0.0.1:8000`.

Endpoints:
- `GET /api/health` — status + tamanhos do KB
- `GET /api/topics` — 10 cards iniciais
- `POST /api/chat` — streaming SSE (campo `question`, `history` opcional)

### 4. Servir o site (em outra janela)

```bash
cd C:/Outros/Cravo/site
python -m http.server 8181
```

Abrir `http://localhost:8181/` — o botão `✦` (canto inferior direito) abre o chat.

## Como funciona o cache

A 1ª chamada cria o cache do system prompt (~80 K tokens, ~$0.30).
A partir daí, cada conversa lê do cache (`cache_read_input_tokens` = 79 457).
TTL = 5 min — para conversas espaçadas, o cache pode expirar.

Verificar via console:

```bash
curl -s -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  --data '{"question":"Olá!","history":[]}'
# usage: cache_read_input_tokens: 79457  (cache hit)
```

## Como injetar o chatbot em novas páginas

```bash
python C:/Outros/Cravo/chatbot/inject-chatbot.py
```

O script é idempotente — usa o marcador `<!-- cravo-chatbot:injected -->`
para detectar páginas já injetadas e pular.

Cada página recebe:
- `<meta name="cravo-chat-api" content="http://127.0.0.1:8000">` — URL do backend
- `<link rel="stylesheet" href="assets/chatbot.css">`
- `<script src="assets/chatbot.js" defer></script>`

Para apontar para um backend remoto em produção, mude o `DEFAULT_API`
em `inject-chatbot.py` e rode de novo (será necessário primeiro remover
o marcador, ou rodar um sed para atualizar a meta).

## Deploy em produção (futuro)

O backend ainda **não foi publicado**. Opções:

1. **Mesma máquina do site** (`10.10.100.10`): subir uvicorn como
   serviço Windows, expor porta interna, IIS reverse-proxy `/cravo/api/*`
   → `127.0.0.1:8000`. Nesse caso, `cravo-chat-api` aponta para
   `https://routepesquisa.com.br/cravo/api`.
2. **Container externo** (ex.: Render, Fly): expor publicamente,
   `cravo-chat-api` aponta para a URL pública. Precisa CORS já liberado
   para `https://routepesquisa.com.br`.

Sempre que mudar a URL, rodar o `inject-chatbot.py` (ou um sed)
para atualizar o meta tag em todas as páginas.

## Modelo

- Default: `claude-sonnet-4-6` (do `.env`).
- Alternativa: `claude-opus-4-7` (mais inteligente, ~5× mais caro).
- O cache do system prompt é compartilhado por modelo — trocar de modelo
  invalida o cache.

## Custos estimados

Com `claude-sonnet-4-6`:
- Cache write (1 vez por sessão): 80 K tokens × $3.75/M = **$0.30**
- Cache read (cada turno): 80 K tokens × $0.30/M = **$0.024**
- Tokens novos (input): ~50 tokens = desprezível
- Output: ~500 tokens × $15/M = **$0.0075**

**Por turno em conversa quente: ~$0.03** (3 centavos).
**Primeira mensagem da sessão: ~$0.31**.

## Conteúdo da base

- 4 tratados em PT-BR (edição UFRJ 2013), 122 páginas extraídas:
  - Sancta Maria — Arte de tocar Fantasia (1565)
  - Frescobaldi — Ao Leitor (1637)
  - Couperin — A Arte de tocar o Cravo (1717)
  - Rameau — Da Mecânica dos Dedos no Cravo (1724)
- 69 termos de glossário do site
- 17 URLs do site (4 tratados + 6 temas + 7 recursos)
- 114 partituras/diagramas catalogados (path + página + tamanho)

## Tópicos iniciais (cards do welcome)

Definidos em `knowledge/topics.json`:
1. 🪑 Postura ao instrumento
2. ✋ Posição das mãos
3. 🎹 Como atacar a tecla
4. 🤚 Dedilhado
5. 〰 Ornamentos
6. 🎵 Notes inégales
7. 📖 Os 4 tratados
8. 🎼 Repertório
9. 👶 Idade para começar
10. 🌪 Baterias e Les Cyclopes

Para alterar, edite `build-knowledge.py` (função `build_topics`) e rode
`python build-knowledge.py` de novo.
