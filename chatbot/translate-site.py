"""
Traduz o site completo (18 páginas HTML) do PT-BR para EN, FR e ES.

- Usa Anthropic SDK (Claude Sonnet 4.6).
- Mantém estrutura HTML intacta — apenas conteúdo de texto visível é traduzido.
- Preserva títulos de tratados em idioma original, nomes de autores, anos.
- Ajusta paths relativos (assets/, partituras/, *.pdf) com `../` extra.
- Idempotente: pula traduções já existentes (a menos que --force).

Estrutura resultante:
    site/                  PT (original, intocado)
    site/en/index.html     EN
    site/fr/index.html     FR
    site/es/index.html     ES
    site/{lang}/tratados/couperin.html
    site/{lang}/temas/postura.html
    ... (espelha estrutura PT)

Uso:
    python translate-site.py                  # traduz tudo (idempotente)
    python translate-site.py --lang en        # só inglês
    python translate-site.py --pages index    # só pages que casam com pattern
    python translate-site.py --force          # re-traduz mesmo se já existe
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Encoding seguro no console Windows
sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    print("ERRO: ANTHROPIC_API_KEY não encontrada em .env")
    sys.exit(1)

# Modelo: Sonnet 4.6 é barato e ótimo para tradução
MODEL = "claude-sonnet-4-6"

SITE_DIR = ROOT / "site"

LANGS = {
    "en": ("English", "en"),
    "fr": ("French", "fr"),
    "es": ("Spanish", "es"),
}

# -------------------------------------------------------------------------
# Prompt de tradução
# -------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert translator specialized in Western classical music history, harpsichord pedagogy, and 16th-18th century treatises. You translate HTML pages from Brazilian Portuguese to {target_name} ({target_code}).

CRITICAL RULES — follow ALL of them:

1. TRANSLATE ALL VISIBLE TEXT CONTENT:
   - Paragraphs, headings, list items, button labels
   - alt, title, placeholder, aria-label, value attributes (when they contain user-facing text)
   - <title> tag content
   - <meta name="description"> content attribute

2. PRESERVE EXACTLY:
   - All HTML tags, attributes, classes, IDs, data-* attributes
   - All href, src, action attribute values (URLs stay literal — DO NOT translate paths)
   - All inline styles and <style>/<script> contents
   - Author names: Thomas de Sancta Maria, Girolamo Frescobaldi, François Couperin, Jean-Philippe Rameau
   - Years: 1565, 1637, 1717, 1724 (and any other year)
   - Original-language treatise titles when they appear in italics or quotes:
     * "L'Art de toucher le Clavecin" (French — keep)
     * "De la Mécanique des doigts sur le Clavessin" (French — keep)
     * "Libro Llamado Arte de tañer Fantasía" (Spanish — keep)
     * "Toccate e Partite" (Italian — keep)
   - Quoted excerpts from the original treatises (PT/FR/ES/IT/LA): keep verbatim within the quotes; you may add a translated paraphrase in parentheses if it improves understanding, but do NOT replace the original.
   - Code blocks, HTML entities (&nbsp; &mdash; etc.), Unicode special characters

3. CHANGE:
   - <html lang="pt-BR"> → <html lang="{html_lang}">
   - <meta http-equiv="Content-Language"> if present

4. MUSICAL TERM CONVENTIONS:
   - PT "notes inégales" / "desigualdades rítmicas" — keep "notes inégales" (universally used in musicology); add translated explanation if needed.
   - PT "mordente" → EN "mordent", FR "mordant", ES "mordente"
   - PT "trinado" → EN "trill", FR "trille", ES "trino"
   - PT "redobro" → EN "redouble (redobro)", FR "redoublement (redobro)", ES "redoble (redobro)"
   - PT "quebro" → EN "quebro (Spanish ornament)", FR "quebro", ES "quiebro"
   - PT "mão de gato" / "garra de gato" → EN "cat's hand / cat's claw", FR "main de chat / griffe de chat", ES "mano de gato / garra de gato"
   - PT "stylus fantasticus" — keep (Latin, universal term)
   - PT "tocata" → EN "toccata", FR "toccata", ES "tocata"
   - PT "passacalha" → EN "passacaglia", FR "passacaille", ES "pasacalle"
   - PT "chacona" → EN "chaconne", FR "chaconne", ES "chacona"
   - PT "mesuré" — keep (French term, universal)
   - PT "port-de-voix" / "pincé" / "tremblement" — keep (French ornaments)

5. CULTURAL ADAPTATION:
   - Use the target language's standard musicology terminology (Grove Dictionary / equivalent).
   - When the PT uses an idiomatic Brazilian Portuguese expression, translate to the target language's equivalent that fits a scholarly/pedagogical register.
   - Keep the same warm, didactic tone of the original.

6. OUTPUT FORMAT:
   - Return ONLY the translated HTML.
   - NO markdown fences (no ```html or ```).
   - NO preamble, no explanation, no commentary.
   - Start with <!DOCTYPE html> or <!doctype html> matching the source.
   - End with </html>.
"""


def adjust_relative_paths(html: str, original_depth: int) -> str:
    """Os arquivos traduzidos ficam um nível mais profundo (em /en/, /fr/, /es/),
    então paths relativos a recursos compartilhados (assets, partituras, PDF)
    precisam de um `../` extra. Páginas internas (tratados/, temas/) NÃO precisam
    ajuste — pois também são duplicadas no /lang/."""

    # Mapeia: caminhos relativos a recursos COMPARTILHADOS recebem mais um ../
    # Patterns dependem do depth original:
    #   depth 1 (raiz): href="assets/..." → href="../assets/..."
    #   depth 2 (subdir): href="../assets/..." → href="../../assets/..."

    if original_depth == 1:
        # Páginas em /cravo/*.html — refs relativas começam direto
        replacements = [
            (r'(href|src)="(assets/[^"]*)"', r'\1="../\2"'),
            (r'(href|src)="(partituras/[^"]*)"', r'\1="../\2"'),
            (r'(href|src)="(2020tratadocravo\.pdf[^"]*)"', r'\1="../\2"'),
        ]
    else:
        # Páginas em /cravo/{tratados|temas}/*.html — refs já têm ../
        replacements = [
            (r'(href|src)="\.\./(assets/[^"]*)"', r'\1="../../\2"'),
            (r'(href|src)="\.\./(partituras/[^"]*)"', r'\1="../../\2"'),
            (r'(href|src)="\.\./(2020tratadocravo\.pdf[^"]*)"', r'\1="../../\2"'),
        ]

    for pat, repl in replacements:
        html = re.sub(pat, repl, html)
    return html


def translate_html(client: anthropic.Anthropic, html: str, lang_code: str) -> str:
    target_name, html_lang = LANGS[lang_code]
    system = SYSTEM_PROMPT.format(
        target_name=target_name,
        target_code=lang_code,
        html_lang=html_lang,
    )

    # Use streaming para evitar timeout em páginas grandes
    out_parts: list[str] = []
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        system=system,
        messages=[{"role": "user", "content": html}],
    ) as stream:
        for text in stream.text_stream:
            out_parts.append(text)

    translated = "".join(out_parts)
    # Remove eventuais cercas markdown que o modelo possa ter colocado
    translated = re.sub(r"^```(?:html)?\s*\n", "", translated)
    translated = re.sub(r"\n```\s*$", "", translated)
    return translated.strip() + "\n"


def validate_translation(html: str, lang_code: str) -> tuple[bool, str]:
    """Valida sanity checks na tradução."""
    if not re.search(r"<!DOCTYPE\s+html>|<!doctype\s+html>", html, re.IGNORECASE):
        return False, "missing DOCTYPE"
    if "</html>" not in html.lower():
        return False, "missing </html>"
    if "</body>" not in html.lower():
        return False, "missing </body>"
    if "</head>" not in html.lower():
        return False, "missing </head>"
    if not re.search(rf'<html\s+lang="{lang_code}"', html, re.IGNORECASE):
        return False, f'<html lang="{lang_code}"> not found'
    return True, "ok"


def process(
    client: anthropic.Anthropic,
    pt_path: Path,
    lang_code: str,
    force: bool = False,
) -> tuple[str, int, int]:
    rel = pt_path.relative_to(SITE_DIR)
    out_path = SITE_DIR / lang_code / rel

    if out_path.exists() and not force:
        return ("skip", 0, 0)

    html = pt_path.read_text(encoding="utf-8")
    chars_in = len(html)
    t0 = time.time()
    try:
        translated = translate_html(client, html, lang_code)
    except anthropic.APIError as e:
        return (f"erro API: {e}", chars_in, 0)

    ok, reason = validate_translation(translated, lang_code)
    if not ok:
        return (f"erro validação: {reason}", chars_in, len(translated))

    # Ajusta paths relativos
    depth = len(rel.parts) - 1
    original_depth = 1 if depth == 0 else 2
    translated = adjust_relative_paths(translated, original_depth)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(translated, encoding="utf-8")
    elapsed = time.time() - t0
    return (f"ok ({elapsed:.1f}s)", chars_in, len(translated))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lang", choices=list(LANGS.keys()), help="Só esse idioma")
    p.add_argument("--pages", help="Só páginas cujo path contém este pattern")
    p.add_argument("--force", action="store_true", help="Re-traduz se já existe")
    p.add_argument("--limit", type=int, help="Máximo de páginas (para teste)")
    args = p.parse_args()

    pages = sorted(SITE_DIR.glob("*.html"))
    pages += sorted((SITE_DIR / "tratados").glob("*.html"))
    pages += sorted((SITE_DIR / "temas").glob("*.html"))

    if args.pages:
        pages = [p for p in pages if args.pages in str(p)]

    langs = [args.lang] if args.lang else list(LANGS.keys())

    if args.limit:
        pages = pages[: args.limit]

    print(f"[translate-site] {len(pages)} páginas × {len(langs)} idiomas = {len(pages) * len(langs)} tasks")
    print(f"  Modelo: {MODEL}")
    print(f"  Output: {SITE_DIR}/{{en,fr,es}}/")
    print(f"  Force:  {args.force}")
    print()

    client = anthropic.Anthropic(api_key=API_KEY)

    total_in = total_out = ok_count = skip_count = err_count = 0
    for lang_code in langs:
        print(f"=== {LANGS[lang_code][0]} ({lang_code}) ===")
        for pt_path in pages:
            rel = pt_path.relative_to(SITE_DIR)
            print(f"  {rel}  →  {lang_code}/  ", end="", flush=True)
            status, ci, co = process(client, pt_path, lang_code, force=args.force)
            print(status)
            total_in += ci
            total_out += co
            if status.startswith("ok"):
                ok_count += 1
            elif status == "skip":
                skip_count += 1
            else:
                err_count += 1
        print()

    print(f"=== Resumo ===")
    print(f"  OK:    {ok_count}")
    print(f"  Skip:  {skip_count}")
    print(f"  Err:   {err_count}")
    print(f"  Chars in:  {total_in:>10,}")
    print(f"  Chars out: {total_out:>10,}")


if __name__ == "__main__":
    main()
