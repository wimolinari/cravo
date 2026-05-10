"""
Injeta o chatbot (CSS + JS) em todas as páginas HTML do site Cravo.

- Idempotente: detecta blocos já injetados e ATUALIZA (em vez de duplicar).
- Cache-busting: anexa ?v=<hash dos arquivos> em chatbot.css/js — toda mudança
  no JS/CSS força clientes a baixarem a versão nova.
- CSS antes de </head>, JS antes de </body>
- Caminhos relativos à pasta da página (assets/ ou ../assets/)
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

# Encoding seguro no console Windows
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

SITE_DIR = Path("C:/Outros/Cravo/site")
ASSETS_DIR = SITE_DIR / "assets"

# URL BASE do backend (SEM o /api final — o JS appenda /api/health, /api/chat etc.)
# Em produção: https://routepesquisa.com.br/cravo
#   (reverse proxy IIS encaminha /cravo/api/* para localhost:8001/api/*)
# Em dev local: http://127.0.0.1:8000 (run-backend.bat sobe uvicorn na 8000)
DEFAULT_API = "https://routepesquisa.com.br/cravo"

# Markers do bloco injetado — usados para detectar e SUBSTITUIR (não duplicar)
MARK_BEGIN = "<!-- cravo-chatbot:begin -->"
MARK_END = "<!-- cravo-chatbot:end -->"
LEGACY_MARK = "<!-- cravo-chatbot:injected -->"

# Padrão de bloco completo (head ou body) com markers — usado para remoção
BLOCK_RE = re.compile(
    re.escape(MARK_BEGIN) + r".*?" + re.escape(MARK_END),
    re.DOTALL,
)
# Linhas legadas (do esquema antigo single-line)
LEGACY_HEAD_RE = re.compile(
    r"\s*<meta[^>]*cravo-chat-api[^>]*>\s*\n"
    r"\s*<link[^>]*chatbot\.css[^>]*>\s*\n"
    r"\s*" + re.escape(LEGACY_MARK) + r"\s*\n",
    re.IGNORECASE,
)
LEGACY_BODY_RE = re.compile(
    r"\s*<script[^>]*chatbot\.js[^>]*>\s*</script>\s*\n",
    re.IGNORECASE,
)


def short_hash(paths: list[Path]) -> str:
    """SHA-256 dos arquivos concatenados — primeiros 8 hex chars."""
    h = hashlib.sha256()
    for p in paths:
        h.update(p.read_bytes())
    return h.hexdigest()[:8]


def assets_prefix(page: Path) -> str:
    rel = page.relative_to(SITE_DIR)
    depth = len(rel.parts) - 1
    return "../" * depth


def make_blocks(prefix: str, version: str) -> tuple[str, str]:
    """Gera (head_block, body_block) com markers + version."""
    head = (
        f"  {MARK_BEGIN}\n"
        f'  <meta name="cravo-chat-api" content="{DEFAULT_API}">\n'
        f'  <link rel="stylesheet" href="{prefix}assets/chatbot.css?v={version}">\n'
        f"  {MARK_END}\n"
    )
    body = (
        f"  {MARK_BEGIN}\n"
        f'  <script src="{prefix}assets/chatbot.js?v={version}" defer></script>\n'
        f"  {MARK_END}\n"
    )
    return head, body


def update(page: Path, version: str) -> str:
    text = page.read_text(encoding="utf-8")
    original = text

    # 1. Remove blocos antigos (com markers begin/end) — idempotência
    text = BLOCK_RE.sub("", text)
    # 2. Remove o esquema LEGADO (do primeiro inject) se ainda existir
    text = LEGACY_HEAD_RE.sub("", text)
    text = LEGACY_BODY_RE.sub("", text)
    # 3. Limpa marker solto que tenha ficado
    text = text.replace(LEGACY_MARK + "\n", "")

    prefix = assets_prefix(page)
    head_block, body_block = make_blocks(prefix, version)

    # 4. Insere head antes de </head>
    head_close = re.search(r"</head>", text, re.IGNORECASE)
    if not head_close:
        return "erro: sem </head>"
    text = text[: head_close.start()] + head_block + text[head_close.start() :]

    # 5. Insere body antes de </body>
    body_close = re.search(r"</body>", text, re.IGNORECASE)
    if not body_close:
        return "erro: sem </body>"
    text = text[: body_close.start()] + body_block + text[body_close.start() :]

    if text == original:
        return "skip (sem mudança)"
    page.write_text(text, encoding="utf-8")
    return "ok"


def main():
    css = ASSETS_DIR / "chatbot.css"
    js = ASSETS_DIR / "chatbot.js"
    if not css.exists() or not js.exists():
        print("ERRO: chatbot.css/js não encontrados em assets/")
        sys.exit(1)

    version = short_hash([css, js])
    print(f"[inject-chatbot] versão (hash): {version}\n")

    pages = sorted(SITE_DIR.rglob("*.html"))
    if not pages:
        print("Nenhum HTML encontrado.")
        return

    counts = {"ok": 0, "skip (sem mudança)": 0, "erro": 0}
    for p in pages:
        result = update(p, version)
        rel = p.relative_to(SITE_DIR)
        print(f"  {rel}  →  {result}")
        if result.startswith("erro"):
            counts["erro"] += 1
        elif result.startswith("skip"):
            counts["skip (sem mudança)"] += 1
        else:
            counts["ok"] += 1

    print()
    print(
        f"OK: {counts['ok']} | "
        f"Skip: {counts['skip (sem mudança)']} | "
        f"Erros: {counts['erro']} | "
        f"Versão: {version}"
    )


if __name__ == "__main__":
    main()
