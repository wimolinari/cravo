"""
Corrige apóstrofos não escapados dentro de atributos data-videos='...' nos
HTMLs do site. Esses apóstrofos terminam o atributo HTML prematuramente,
quebrando JSON.parse no video-picker.js (sintoma: console com WARNING
'Invalid video list SyntaxError: Unterminated string in JSON').

Estratégia: detectar o padrão  data-videos='[...]'  e dentro do bloco
substituir cada `'` por `&#39;`. NÃO toca em outros atributos nem em
textos visíveis.

Idempotente: roda múltiplas vezes sem efeito colateral (o segundo run não
encontra apóstrofos crus dentro do data-videos pois já estão escapados).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

SITE_DIR = Path(__file__).resolve().parent.parent / "site"

# Padrão multilinha: data-videos='([^']|escape)*'
# Como temos apóstrofos NÃO ESCAPADOS dentro, regex precisa ser não-greedy
# até `']` ou `'>` (fim plausível do atributo).
# Heurística: o atributo data-videos sempre tem `'[` como abertura e `]'`
# como fechamento. Vou usar isso como âncora.
ATTR_RE = re.compile(
    r"(data-videos\s*=\s*')(\[.*?\])(')",
    re.DOTALL,
)


def fix_block(match: re.Match) -> str:
    prefix, json_block, suffix = match.group(1), match.group(2), match.group(3)
    # Substitui apóstrofos crus dentro do JSON pelo entity HTML
    fixed = json_block.replace("'", "&#39;")
    return prefix + fixed + suffix


def process_file(path: Path) -> tuple[int, int]:
    """Retorna (blocos_modificados, apostrofos_escapados)."""
    text = path.read_text(encoding="utf-8")
    blocks_modified = 0
    apostrophes_escaped = 0

    def counter(m: re.Match) -> str:
        nonlocal blocks_modified, apostrophes_escaped
        json_block = m.group(2)
        n_apos = json_block.count("'")
        if n_apos > 0:
            blocks_modified += 1
            apostrophes_escaped += n_apos
        return fix_block(m)

    new_text = ATTR_RE.sub(counter, text)
    if blocks_modified > 0:
        path.write_text(new_text, encoding="utf-8")
    return blocks_modified, apostrophes_escaped


def main() -> None:
    pages = sorted(SITE_DIR.rglob("*.html"))
    if not pages:
        print(f"Nenhum HTML em {SITE_DIR}")
        return

    total_files = 0
    total_blocks = 0
    total_apos = 0

    for p in pages:
        blocks, apos = process_file(p)
        if blocks > 0:
            rel = p.relative_to(SITE_DIR)
            print(f"  {rel}: {blocks} block(s), {apos} apostrof(es)")
            total_files += 1
            total_blocks += blocks
            total_apos += apos

    print()
    if total_files == 0:
        print("Nenhum picker tinha apóstrofo cru. Tudo OK (já escapados ou inexistentes).")
    else:
        print(
            f"Resumo: {total_files} arquivos modificados | "
            f"{total_blocks} blocks data-videos corrigidos | "
            f"{total_apos} apóstrofos escapados (' → &#39;)"
        )


if __name__ == "__main__":
    main()
