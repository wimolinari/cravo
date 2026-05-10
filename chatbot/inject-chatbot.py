"""
Injeta o chatbot (CSS + JS) em todas as páginas HTML do site Cravo.

- CSS é incluído antes do </head>
- JS é incluído antes do </body>
- Caminhos são relativos à pasta da página (assets/ ou ../assets/)
- Idempotente: detecta se já foi injetado.
- Adiciona meta <meta name="cravo-chat-api" content="..."> com URL configurável.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Encoding seguro no console Windows
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

SITE_DIR = Path("C:/Outros/Cravo/site")

# A URL da API pode ser sobrescrita por <meta>. Em produção, atualizar para a URL real.
# Como o backend ainda não está em produção, deixamos localhost para dev e o usuário
# pode alterar a meta tag em cada deploy.
DEFAULT_API = "http://127.0.0.1:8000"

CSS_LINK = '<link rel="stylesheet" href="{prefix}assets/chatbot.css">'
JS_TAG = '<script src="{prefix}assets/chatbot.js" defer></script>'
META_TAG = f'<meta name="cravo-chat-api" content="{DEFAULT_API}">'

MARKER = "<!-- cravo-chatbot:injected -->"


def assets_prefix(page: Path) -> str:
    """Retorna '' para pages na raiz, '../' para pages em subpastas."""
    rel = page.relative_to(SITE_DIR)
    depth = len(rel.parts) - 1
    return "../" * depth


def inject(page: Path) -> str:
    text = page.read_text(encoding="utf-8")

    if MARKER in text:
        return "skip (já injetado)"

    prefix = assets_prefix(page)
    css = CSS_LINK.format(prefix=prefix)
    js = JS_TAG.format(prefix=prefix)

    # Insere CSS + meta antes de </head>
    head_close = re.search(r"</head>", text, re.IGNORECASE)
    if not head_close:
        return "erro: sem </head>"

    inject_head = f"  {META_TAG}\n  {css}\n  {MARKER}\n"
    text = text[: head_close.start()] + inject_head + text[head_close.start() :]

    # Insere JS antes de </body>
    body_close = re.search(r"</body>", text, re.IGNORECASE)
    if not body_close:
        return "erro: sem </body>"

    inject_body = f"  {js}\n"
    text = text[: body_close.start()] + inject_body + text[body_close.start() :]

    page.write_text(text, encoding="utf-8")
    return "ok"


def main():
    pages = sorted(SITE_DIR.rglob("*.html"))
    if not pages:
        print("Nenhum HTML encontrado.")
        return

    print(f"[inject-chatbot] {len(pages)} páginas em {SITE_DIR}\n")
    counts = {"ok": 0, "skip (já injetado)": 0, "erro": 0}
    for p in pages:
        result = inject(p)
        rel = p.relative_to(SITE_DIR)
        print(f"  {rel}  →  {result}")
        if result.startswith("erro"):
            counts["erro"] += 1
        elif result.startswith("skip"):
            counts["skip (já injetado)"] += 1
        else:
            counts["ok"] += 1

    print()
    print(f"OK: {counts['ok']} | Skip: {counts['skip (já injetado)']} | Erros: {counts['erro']}")


if __name__ == "__main__":
    main()
