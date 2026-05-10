"""
Backend FastAPI para o chatbot pedagógico do site Tratados do Cravo.

- Anthropic SDK (claude-sonnet-4-6 ou claude-opus-4-7) com prompt caching ephemeral.
- Streaming SSE em /api/chat.
- /api/topics retorna sugestões iniciais (cards estilo comparador.html).
- /api/health para smoke test.
- Knowledge base = tratado integral (179KB) + glossário (69 termos) + sitemap (17 URLs)
  + inventário de imagens (114). Tudo no system prompt -> cache hit a partir da 2ª chamada.
"""

import json
import os
import sqlite3
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# ─── ENV ──────────────────────────────────────────────────────────────────────
# .env pode estar em estruturas diferentes dependendo do ambiente:
#   dev:  C:\Outros\Cravo\.env (3 níveis acima de backend/app.py)
#   prod: D:\apps\cravo-chatbot\.env (2 níveis acima de backend/app.py)
# Tenta ambos. override=True garante que .env vence variáveis de ambiente
# vazias herdadas do shell.
_script_dir = Path(__file__).resolve().parent
for _candidate in (_script_dir.parent / ".env", _script_dir.parent.parent / ".env"):
    if _candidate.is_file():
        load_dotenv(_candidate, override=True)
        break

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    print("ERRO: ANTHROPIC_API_KEY não encontrada em .env", file=sys.stderr)
    sys.exit(1)

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# ─── KNOWLEDGE BASE ───────────────────────────────────────────────────────────
KB_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def _read_text(name: str) -> str:
    return (KB_DIR / name).read_text(encoding="utf-8")


def _read_json(name: str):
    return json.loads(_read_text(name))


TRATADO_FULL = _read_text("tratado_full.txt")
GLOSSARY = _read_json("glossary.json")
SITEMAP = _read_json("sitemap.json")
IMAGES = _read_json("images.json")
TOPICS = _read_json("topics.json")

# Topics traduzidos por idioma — carregados se existirem (gerados pelo
# translate-knowledge.py).
TOPICS_BY_LANG = {"pt": TOPICS}
for _lang in ("en", "fr", "es"):
    _f = KB_DIR / f"topics.{_lang}.json"
    if _f.is_file():
        try:
            TOPICS_BY_LANG[_lang] = json.loads(_f.read_text(encoding="utf-8"))
        except Exception:
            pass

# ─── COMUNIDADE (SQLite) ──────────────────────────────────────────────────────
# Auto-save de toda conversa concluída para uma biblioteca anônima e pública.
# Site demo: sem autenticação, sem moderação, sem rate-limit. Pode ser
# expandido depois quando houver controle de acesso.
DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "community.db"


def _db_init() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS community_chats (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                lang         TEXT    NOT NULL,
                title        TEXT    NOT NULL,
                messages     TEXT    NOT NULL,
                turn_count   INTEGER NOT NULL,
                created_at   INTEGER NOT NULL,
                hidden       INTEGER DEFAULT 0
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_lang_created "
            "ON community_chats(lang, created_at DESC)"
        )
        conn.commit()


_db_init()


def db_save_chat(lang: str, messages: list[dict]) -> int | None:
    """Salva conversa completa. Retorna o ID criado, ou None se inválida."""
    if not messages or len(messages) < 2:
        return None
    # Título = 1ª pergunta truncada
    first_user = next((m for m in messages if m["role"] == "user"), None)
    if not first_user:
        return None
    title = first_user["content"].strip()[:140]
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                "INSERT INTO community_chats (lang, title, messages, turn_count, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    (lang or "pt").lower(),
                    title,
                    json.dumps(messages, ensure_ascii=False),
                    len(messages),
                    int(time.time()),
                ),
            )
            conn.commit()
            return cur.lastrowid
    except Exception as e:
        print(f"[community] erro ao salvar: {e}", file=sys.stderr)
        return None


def db_list_chats(lang: str, limit: int = 50, offset: int = 0) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, title, turn_count, created_at FROM community_chats "
            "WHERE lang = ? AND hidden = 0 ORDER BY created_at DESC LIMIT ? OFFSET ?",
            ((lang or "pt").lower(), limit, offset),
        ).fetchall()
    return [
        {"id": r[0], "title": r[1], "turn_count": r[2], "created_at": r[3]}
        for r in rows
    ]


def db_get_chat(chat_id: int) -> dict | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id, lang, title, messages, turn_count, created_at "
            "FROM community_chats WHERE id = ? AND hidden = 0",
            (chat_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "lang": row[1],
        "title": row[2],
        "messages": json.loads(row[3]),
        "turn_count": row[4],
        "created_at": row[5],
    }


def db_count_chats(lang: str) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM community_chats WHERE lang = ? AND hidden = 0",
            ((lang or "pt").lower(),),
        ).fetchone()
    return row[0] if row else 0

# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""Você é o **Mestre do Cravo**, um assistente pedagógico especializado nos 4 tratados \
históricos sobre o cravo cobertos pelo site Tratados do Cravo (UFRJ 2013):

1. **Thomas de Sancta Maria** — *Livro chamado Arte de tocar Fantasia* (1565)
2. **Girolamo Frescobaldi** — *Ao Leitor* (1637)
3. **François Couperin** — *L'Art de toucher le Clavecin* (1717)
4. **Jean-Philippe Rameau** — *De la Mécanique des doigts sur le Clavessin* (1724)

# Como você deve responder

- Responda **sempre em português do Brasil**.
- Cite os tratados com o nome do autor e o capítulo/parágrafo quando possível \
  (ex.: "Couperin, capítulo 3" ou "Sancta Maria, cap. XV").
- Quando um termo técnico for relevante, **explique-o em linguagem simples** \
  e indique se está no glossário do site.
- Se o usuário pedir um vídeo, lembre que há combos curados nas páginas de cada tema \
  e em cada página de tratado.
- **Compare** os 4 autores quando faz sentido (são épocas e estéticas diferentes — \
  Espanha 1565, Itália 1637, França 1717, França 1724).
- Quando não tiver certeza ou o tratado não cobrir o assunto, diga isso explicitamente \
  em vez de inventar. Você pode dar sua opinião pedagógica desde que sinalize \
  ("Os tratados não tratam disso diretamente, mas...").
- Seja **caloroso e didático**. O leitor pode ser estudante de cravo, pianista \
  curioso, professor ou ouvinte de música antiga.
- **Não** reproduza grandes blocos do texto integral; resuma e cite. Quando precisar \
  citar um trecho, use 1–2 frases entre aspas com o autor.
- Use **Markdown leve**: negrito para destacar conceitos, listas curtas, e títulos \
  de seção quando a resposta for longa.
- **Seja conciso por default** — vá direto ao ponto, máximo 3-4 parágrafos curtos. \
  Se o usuário pedir explicação detalhada, aprofunde. Mas para perguntas genéricas, \
  prefira respostas de 100-300 palavras (não 800+). O usuário pode sempre pedir mais.

# REGRAS CRÍTICAS DE LINKS — siga à risca, sem exceção

**NUNCA invente URLs.** Os domínios `tratadosdocravo.vercel.app`, `cravo.com.br`, \
`github.io` ou qualquer outro **NÃO EXISTEM** — não use. O site fica em \
`routepesquisa.com.br/cravo/` mas você **não deve** incluir o domínio nas suas \
respostas.

**Formato OBRIGATÓRIO de todo link:**
- Sempre **caminho relativo à raiz começando em `/cravo/`**, sem domínio, sem \
  protocolo (`http`/`https`), sem `www`.
- Exemplo certo: `[Posição das mãos](/cravo/temas/postura.html)`
- Exemplos errados (NUNCA faça):
  - `[…](https://tratadosdocravo.vercel.app/cravo/...)` ❌ domínio inventado
  - `[…](https://routepesquisa.com.br/cravo/...)` ❌ não inclua domínio
  - `[…](cravo/temas/postura.html)` ❌ falta a barra inicial
  - `[…](temas/postura.html)` ❌ não é relativo à raiz

**Só linke URLs que aparecem literalmente nas seções `SITEMAP` ou `INVENTÁRIO DE \
IMAGENS` deste prompt.** Se a URL exata não está numa dessas duas seções, **não \
invente uma** — em vez disso, mencione o conteúdo em prosa ("veja a página de \
Postura do site") sem criar link.

**Imagens (partituras/diagramas):** o INVENTÁRIO DE IMAGENS abaixo é uma \
**lista curada** com `url_path`, `titulo`, `descricao`, `nivel` e `grupo`. \
Cada entrada corresponde a UMA obra/seção real (ex.: "Primeiro Prelúdio · Dó" → \
`/cravo/partituras/couperin/embedded/p081-img1.jpeg`). **Regras inegociáveis**:

1. Antes de sugerir QUALQUER imagem, faça um match exato pelo `titulo` ou \
   `descricao` da entrada. Se não há entrada que case com o que o usuário pediu, \
   **NÃO INVENTE** uma URL — direcione para `/cravo/partituras-viewer.html`.
2. Use SEMPRE o `url_path` literal da entrada — nunca componha um caminho \
   adivinhando o número da página.
3. O texto do link no Markdown deve ser o `titulo` da entrada (ex.: \
   `[Primeiro Prelúdio · Dó](/cravo/partituras/couperin/embedded/p081-img1.jpeg)`).
4. Se o usuário pedir uma obra que existe nos tratados mas NÃO está no \
   inventário curado (ex.: "Les Cyclopes inteiro"), explique que o site só tem \
   trechos curados e mande para `/cravo/partituras-viewer.html`.

Exemplos de uso correto:
- "Prelúdio 1 de Couperin" → match titulo "Primeiro Prelúdio · Dó" → \
  `[Primeiro Prelúdio · Dó](/cravo/partituras/couperin/embedded/p081-img1.jpeg)`
- "exemplo de dedilhado em Sancta Maria" → procure no grupo "Sancta Maria" → \
  ofereça o título e link da entrada que mais combina (ex.: "Mão direita · ascendente").
- "Les Tourbillons" (não está no inventário) → "Esta peça não está nas \
  partituras curadas do site, mas você pode ver as obras disponíveis em \
  [Visualizador de partituras](/cravo/partituras-viewer.html)."

**Sugerir páginas:** sempre que possível, sugira **uma** página do SITEMAP que \
aprofunde o tema, no formato `[texto](/cravo/...)`.

# Conhecimento de base

A seguir está o **TEXTO INTEGRAL** dos 4 tratados (português, edição UFRJ 2013), \
o **glossário** completo do site (69 termos), o **sitemap** (todas as páginas) e o \
**inventário de imagens** (partituras e diagramas). Use isto como sua única fonte de \
verdade — se algo não estiver aqui, diga que não sabe.

═══════════════════════════════════════════════════════════════════════════════
TEXTO INTEGRAL DOS 4 TRATADOS
═══════════════════════════════════════════════════════════════════════════════

{TRATADO_FULL}

═══════════════════════════════════════════════════════════════════════════════
GLOSSÁRIO DO SITE (69 termos)
═══════════════════════════════════════════════════════════════════════════════

{json.dumps(GLOSSARY, ensure_ascii=False, indent=2)}

═══════════════════════════════════════════════════════════════════════════════
SITEMAP (URLs do site para sugerir como referência)
═══════════════════════════════════════════════════════════════════════════════

{json.dumps(SITEMAP, ensure_ascii=False, indent=2)}

═══════════════════════════════════════════════════════════════════════════════
INVENTÁRIO DE IMAGENS (114 partituras/diagramas extraídos do PDF)
═══════════════════════════════════════════════════════════════════════════════

{json.dumps(IMAGES, ensure_ascii=False)}
"""

# ─── ANTHROPIC CLIENT ─────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=API_KEY)

# ─── FASTAPI ──────────────────────────────────────────────────────────────────
app = FastAPI(title="Cravo Chatbot Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://routepesquisa.com.br",
        "http://routepesquisa.com.br",
        "http://localhost:8181",
        "http://localhost:8000",
        "http://127.0.0.1:8181",
        "http://127.0.0.1:8000",
        "*",  # site é público; respostas não trazem dado sensível
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[Message] = []
    lang: str = "pt"  # pt | en | fr | es


# Instruções de idioma anexadas ao system prompt por requisição
LANG_INSTRUCTIONS = {
    "pt": "Responda em **português do Brasil**.",
    "en": (
        "Respond in **English** (the user's interface is in English). "
        "Translate the source quotations from the treatises when helpful, but keep "
        "the original Portuguese (UFRJ 2013) wording in italics or quotes when you cite "
        "verbatim. Use established English musicology terminology (Grove Dictionary)."
    ),
    "fr": (
        "Répondez en **français**. Pour les citations directes des traités, gardez le "
        "texte portugais original (édition UFRJ 2013) entre guillemets et donnez une "
        "paraphrase française. Utilisez la terminologie musicologique française "
        "établie (notes inégales, port-de-voix, pincé, tremblement, etc.)."
    ),
    "es": (
        "Responda en **español**. Para citas directas de los tratados, conserve el texto "
        "portugués original (edición UFRJ 2013) entre comillas y proporcione una paráfrasis "
        "en español. Use la terminología musicológica española establecida."
    ),
}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": MODEL,
        "kb": {
            "tratado_chars": len(TRATADO_FULL),
            "glossary_terms": len(GLOSSARY),
            "sitemap_entries": sum(len(v) for v in SITEMAP.values()),
            "images": len(IMAGES),
            "topics": len(TOPICS),
        },
    }


@app.get("/api/topics")
def get_topics(lang: str = "pt"):
    return TOPICS_BY_LANG.get(lang.lower(), TOPICS)


@app.get("/api/community")
def list_community(lang: str = "pt", limit: int = 50, offset: int = 0):
    """Lista as conversas mais recentes da comunidade no idioma escolhido.
    Não retorna o conteúdo das mensagens — só metadata (title, turn_count)."""
    limit = max(1, min(limit, 100))
    return {
        "total": db_count_chats(lang),
        "items": db_list_chats(lang, limit=limit, offset=max(0, offset)),
    }


@app.get("/api/community/{chat_id}")
def get_community_chat(chat_id: int):
    """Retorna a conversa completa (mensagens) de uma conversa pública."""
    chat = db_get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="conversa não encontrada")
    return chat


@app.post("/api/community/{chat_id}/hide")
def hide_community_chat(chat_id: int, key: str = ""):
    """Esconde uma conversa da listagem pública. key precisa bater com
    ANTHROPIC_API_KEY (admin only)."""
    if not key or key != API_KEY:
        raise HTTPException(status_code=403, detail="forbidden")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "UPDATE community_chats SET hidden = 1 WHERE id = ?", (chat_id,)
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="conversa não encontrada")
    return {"ok": True, "hidden_id": chat_id}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="question vazio")

    # Limita histórico para não estourar contexto (mantém últimos 16 turnos)
    history = [m.model_dump() for m in req.history[-16:]]
    messages = history + [{"role": "user", "content": req.question.strip()}]

    # Instrução de idioma (NÃO entra no cache — varia por request)
    lang = (req.lang or "pt").lower()
    if lang not in LANG_INSTRUCTIONS:
        lang = "pt"
    lang_block = (
        "\n\n═══ INSTRUÇÃO DE IDIOMA (esta requisição) ═══\n"
        + LANG_INSTRUCTIONS[lang]
    )

    def event_stream():
        accumulated = []  # chunks de texto pra salvar no fim
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=1024,  # respostas mais concisas e rapidas (IIS+ARR bufferiza ate done)
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": lang_block,
                    },
                ],
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    accumulated.append(text)
                    yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"

                # final message com usage
                final = stream.get_final_message()
                usage = {
                    "input_tokens": final.usage.input_tokens,
                    "output_tokens": final.usage.output_tokens,
                    "cache_creation_input_tokens": getattr(
                        final.usage, "cache_creation_input_tokens", 0
                    ),
                    "cache_read_input_tokens": getattr(
                        final.usage, "cache_read_input_tokens", 0
                    ),
                }
                # ─── auto-save da conversa completa pra biblioteca pública ──
                full_assistant = "".join(accumulated)
                if full_assistant.strip():
                    full_messages = messages + [
                        {"role": "assistant", "content": full_assistant}
                    ]
                    chat_id = db_save_chat(lang, full_messages)
                    if chat_id:
                        usage["community_id"] = chat_id
                yield f"data: {json.dumps({'done': True, 'usage': usage}, ensure_ascii=False)}\n\n"
        except anthropic.APIError as e:
            err = {"error": True, "message": f"Erro Anthropic: {e}"}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"
        except Exception as e:  # noqa: BLE001
            err = {"error": True, "message": f"Erro interno: {e}"}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # nginx/iis reverse proxy: desliga buffer
        },
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
