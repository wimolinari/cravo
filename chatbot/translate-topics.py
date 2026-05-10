"""
Traduz knowledge/topics.json para EN, FR e ES, gerando:
    knowledge/topics.en.json
    knowledge/topics.fr.json
    knowledge/topics.es.json

O backend (app.py) carrega automaticamente esses arquivos e responde via
/api/topics?lang=...
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)
API_KEY = os.environ["ANTHROPIC_API_KEY"]
MODEL = "claude-sonnet-4-6"

KB_DIR = ROOT / "chatbot" / "knowledge"
SRC = KB_DIR / "topics.json"

LANGS = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
}

PROMPT = """Translate the following JSON of starter topic cards from Brazilian Portuguese to {target}.

The JSON has 10 entries, each with:
- "icon": emoji (KEEP AS IS)
- "label": short topic name (TRANSLATE)
- "sample_question": example question that triggers a chatbot conversation (TRANSLATE — use natural, idiomatic phrasing in the target language)
- "related_url": site URL like /cravo/temas/postura.html (KEEP AS IS — do NOT translate the path)

Musical terminology rules:
- "notes inégales" → keep verbatim (universal term)
- "mordente" → "mordent" (EN), "mordant" (FR), "mordente" (ES)
- "trinado" → "trill" (EN), "trille" (FR), "trino" (ES)
- "mão de gato" → "cat's hand" (EN), "main de chat" (FR), "mano de gato" (ES)
- "baterias" (in Rameau context) → "batteries" (EN/FR), "baterías" (ES)
- "Les Cyclopes" — keep as is (French piece title)
- "Sancta Maria", "Couperin", "Frescobaldi", "Rameau" → keep names

Output ONLY the translated JSON array (valid JSON, no markdown fences, no explanation).

INPUT JSON:
{src}
"""


def translate(client, src_text: str, lang_code: str) -> list:
    out = []
    with client.messages.stream(
        model=MODEL,
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": PROMPT.format(target=LANGS[lang_code], src=src_text),
        }],
    ) as stream:
        for chunk in stream.text_stream:
            out.append(chunk)
    text = "".join(out).strip()
    # Remove eventuais cercas markdown
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def main():
    if not SRC.exists():
        print(f"ERRO: {SRC} não existe")
        sys.exit(1)

    src_text = SRC.read_text(encoding="utf-8")
    client = anthropic.Anthropic(api_key=API_KEY)

    for lang_code in LANGS:
        out_path = KB_DIR / f"topics.{lang_code}.json"
        if out_path.exists():
            print(f"  {lang_code}  →  skip (já existe)")
            continue
        print(f"  {lang_code}  →  ", end="", flush=True)
        try:
            translated = translate(client, src_text, lang_code)
            out_path.write_text(
                json.dumps(translated, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"ok ({len(translated)} entries)")
        except Exception as e:
            print(f"erro: {e}")


if __name__ == "__main__":
    main()
