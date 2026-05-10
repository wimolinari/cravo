"""
Substitui o video-picker unico dos 8 Preludios em couperin.html por 8 pickers
separados, um por preludio, com 5 gravacoes curadas cada.

Roda nas 4 versoes linguisticas (PT, EN, FR, ES) -- IDs do YouTube sao
universais; apenas os textos (intro, h5, performer notes) variam.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# 8 Preludios + 5 videos cada
# IDs universais; performer/year sao verificaveis no YouTube
PRELUDIOS = [
    {
        "num": 1,
        "labels": {
            "pt": "1º Prelúdio · Dó maior",
            "en": "1st Prelude · C major",
            "fr": "1er Prélude · ut majeur",
            "es": "1er Preludio · Do mayor",
        },
        "videos": [
            {"id": "et45O43SufY", "performer": "Korneel Bernolet", "year": "2018", "note": {
                "pt": "Cravo Dulcken 1747 (Antuérpia)", "en": "Dulcken harpsichord, Antwerp 1747",
                "fr": "Clavecin Dulcken 1747 (Anvers)", "es": "Clave Dulcken 1747 (Amberes)"}},
            {"id": "LdoGbpQmWHw", "performer": "Benjamin Alard", "year": "2020", "note": {
                "pt": "Cravista francês contemporâneo", "en": "Contemporary French harpsichordist",
                "fr": "Claveciniste français contemporain", "es": "Clavecinista francés contemporáneo"}},
            {"id": "uqtv371isgk", "performer": "Gustav Leonhardt", "year": "1964", "note": {
                "pt": "Gravação histórica · cravo W. Rück (integral dos 8)",
                "en": "Historic recording · W. Rück harpsichord (complete 8 Préludes)",
                "fr": "Enregistrement historique · clavecin W. Rück (intégrale des 8)",
                "es": "Grabación histórica · clave W. Rück (integral de los 8)"}},
            {"id": "EqTprXHmNd4", "performer": {"pt": "Anônimo", "en": "Anonymous", "fr": "Anonyme", "es": "Anónimo"}, "year": "2022", "note": {
                "pt": "Foco no toque francês", "en": "French touch focus",
                "fr": "Focus sur le toucher français", "es": "Enfoque en el toque francés"}},
            {"id": "e0bGIPlaMRQ", "performer": "Hauptwerk · Mietke", "year": "2019", "note": {
                "pt": "Modelo digital de cravo Mietke", "en": "Digital Mietke model",
                "fr": "Modèle numérique Mietke", "es": "Modelo digital Mietke"}},
        ],
    },
    {
        "num": 2,
        "labels": {
            "pt": "2º Prelúdio · Ré menor",
            "en": "2nd Prelude · D minor",
            "fr": "2e Prélude · ré mineur",
            "es": "2º Preludio · Re menor",
        },
        "videos": [
            {"id": "mnQZcU0vIEw", "performer": "Korneel Bernolet", "year": "2018", "note": {
                "pt": "Cravo Dulcken 1747", "en": "Dulcken harpsichord 1747",
                "fr": "Clavecin Dulcken 1747", "es": "Clave Dulcken 1747"}},
            {"id": "a3D-vsA2cQI", "performer": "Gustav Leonhardt", "year": "1964", "note": {
                "pt": "Extração da integral 1964",
                "en": "Extracted from the complete 1964 recording",
                "fr": "Extrait de l'intégrale 1964", "es": "Extracto de la integral 1964"}},
            {"id": "Ft9dTEETqfw", "performer": "Paul Cienniwa", "year": "2014", "note": {
                "pt": "Cravista americano · interpretação articulada",
                "en": "American harpsichordist · articulated reading",
                "fr": "Claveciniste américain · lecture articulée",
                "es": "Clavecinista estadounidense · lectura articulada"}},
            {"id": "Q3b3e6gon1M", "performer": "Wolfgang Glüxam", "year": "2010", "note": {
                "pt": "Cravista austríaco", "en": "Austrian harpsichordist",
                "fr": "Claveciniste autrichien", "es": "Clavecinista austríaco"}},
            {"id": "vba3O1hvszA", "performer": {"pt": "Anônimo", "en": "Anonymous", "fr": "Anonyme", "es": "Anónimo"}, "year": "2023", "note": {
                "pt": "Cravo histórico", "en": "Historical harpsichord",
                "fr": "Clavecin historique", "es": "Clave histórico"}},
        ],
    },
    {
        "num": 3,
        "labels": {
            "pt": "3º Prelúdio · Sol menor",
            "en": "3rd Prelude · G minor",
            "fr": "3e Prélude · sol mineur",
            "es": "3er Preludio · Sol menor",
        },
        "videos": [
            {"id": "HAvWGPBa-Q4", "performer": "Korneel Bernolet", "year": "2018", "note": {
                "pt": "Cravo Dulcken 1747", "en": "Dulcken harpsichord 1747",
                "fr": "Clavecin Dulcken 1747", "es": "Clave Dulcken 1747"}},
            {"id": "XZd7wwFC8Wk", "performer": "Željko Manić", "year": "2019", "note": {
                "pt": "Cravista croata", "en": "Croatian harpsichordist",
                "fr": "Claveciniste croate", "es": "Clavecinista croata"}},
            {"id": "uqtv371isgk", "performer": "Gustav Leonhardt", "year": "1964", "note": {
                "pt": "Integral 1964 · referência absoluta",
                "en": "1964 complete recording · absolute reference",
                "fr": "Intégrale 1964 · référence absolue",
                "es": "Integral 1964 · referencia absoluta"}},
            {"id": "6nVc74xKW9o", "performer": "Silvanio Reis", "year": "2017", "note": {
                "pt": "Boston Early Music Festival · Prelúdios 1-2-3",
                "en": "Boston Early Music Festival · Preludes 1-2-3",
                "fr": "Boston Early Music Festival · Préludes 1-2-3",
                "es": "Boston Early Music Festival · Preludios 1-2-3"}},
            {"id": "3wpudluOX4k", "performer": {"pt": "Anônimo", "en": "Anonymous", "fr": "Anonyme", "es": "Anónimo"}, "year": "2020", "note": {
                "pt": "Performance recente", "en": "Recent performance",
                "fr": "Interprétation récente", "es": "Interpretación reciente"}},
        ],
    },
    {
        "num": 4,
        "labels": {
            "pt": "4º Prelúdio · Fá maior",
            "en": "4th Prelude · F major",
            "fr": "4e Prélude · fa majeur",
            "es": "4º Preludio · Fa mayor",
        },
        "videos": [
            {"id": "Pam0enY8Fuw", "performer": {"pt": "Anônimo", "en": "Anonymous", "fr": "Anonyme", "es": "Anónimo"}, "year": "2023", "note": {
                "pt": "Cravo histórico", "en": "Historical harpsichord",
                "fr": "Clavecin historique", "es": "Clave histórico"}},
            {"id": "AbZcTMQInq4", "performer": "Silvanio Reis", "year": "2017", "note": {
                "pt": "Boston EMF · Prelúdios 4-5-6",
                "en": "Boston Early Music Festival · Preludes 4-5-6",
                "fr": "Boston Early Music Festival · Préludes 4-5-6",
                "es": "Boston Early Music Festival · Preludios 4-5-6"}},
            {"id": "uqtv371isgk", "performer": "Gustav Leonhardt", "year": "1964", "note": {
                "pt": "Integral histórica", "en": "Historic complete set",
                "fr": "Intégrale historique", "es": "Integral histórica"}},
            {"id": "yhUigHfxkDw", "performer": {"pt": "Coletânea", "en": "Compilation", "fr": "Compilation", "es": "Recopilación"}, "year": "2019", "note": {
                "pt": "Compilação dos 8 Prelúdios",
                "en": "Complete set of all 8 Preludes",
                "fr": "Compilation des 8 Préludes",
                "es": "Compilación de los 8 Preludios"}},
            {"id": "5FV-UctnFZc", "performer": {"pt": "Coletânea", "en": "Compilation", "fr": "Compilation", "es": "Recopilación"}, "year": "2021", "note": {
                "pt": "Os 8 Prelúdios completos",
                "en": "The Eight Preludes complete",
                "fr": "Les 8 Préludes intégrale",
                "es": "Los 8 Preludios completos"}},
        ],
    },
    {
        "num": 5,
        "labels": {
            "pt": "5º Prelúdio · Lá maior",
            "en": "5th Prelude · A major",
            "fr": "5e Prélude · la majeur",
            "es": "5º Preludio · La mayor",
        },
        "videos": [
            {"id": "qx9F4ATh9O0", "performer": "Korneel Bernolet", "year": "2018", "note": {
                "pt": "Cravo Dulcken 1747", "en": "Dulcken harpsichord 1747",
                "fr": "Clavecin Dulcken 1747", "es": "Clave Dulcken 1747"}},
            {"id": "wjxsqUff9BU", "performer": "Benjamin Alard", "year": "2020", "note": {
                "pt": "Cravo francês", "en": "French harpsichord",
                "fr": "Clavecin français", "es": "Clave francés"}},
            {"id": "nwesaC_e3sQ", "performer": "Robert Hill", "year": "2002", "note": {
                "pt": "Recital ao vivo", "en": "Live recital",
                "fr": "Récital en direct", "es": "Recital en vivo"}},
            {"id": "2ZrqWkdwVzo", "performer": "Mário Trilha", "year": "2018", "note": {
                "pt": "Cravo histórico Germain (Paris 1785)",
                "en": "Historical Germain harpsichord (Paris 1785)",
                "fr": "Clavecin historique Germain (Paris 1785)",
                "es": "Clave histórico Germain (París 1785)"}},
            {"id": "Z8hNWVLMI7M", "performer": "Ryan Chan", "year": "2020", "note": {
                "pt": "Interpretação contemporânea", "en": "Contemporary interpretation",
                "fr": "Interprétation contemporaine", "es": "Interpretación contemporánea"}},
        ],
    },
    {
        "num": 6,
        "labels": {
            "pt": "6º Prelúdio · Si menor",
            "en": "6th Prelude · B minor",
            "fr": "6e Prélude · si mineur",
            "es": "6º Preludio · Si menor",
        },
        "videos": [
            {"id": "dNWb9EySwc4", "performer": "Benjamin Alard", "year": "2020", "note": {
                "pt": "Cravo francês · Si menor", "en": "French harpsichord · B minor",
                "fr": "Clavecin français · si mineur", "es": "Clave francés · Si menor"}},
            {"id": "c02cYZcS6j0", "performer": "Score animado", "year": "2019", "note": {
                "pt": "Partitura em movimento — bom para acompanhar",
                "en": "Animated score — useful to follow",
                "fr": "Partition animée — utile pour suivre",
                "es": "Partitura animada — útil para seguir"}},
            {"id": "uqtv371isgk", "performer": "Gustav Leonhardt", "year": "1964", "note": {
                "pt": "Integral histórica", "en": "Historic complete set",
                "fr": "Intégrale historique", "es": "Integral histórica"}},
            {"id": "yhUigHfxkDw", "performer": {"pt": "Coletânea", "en": "Compilation", "fr": "Compilation", "es": "Recopilación"}, "year": "2019", "note": {
                "pt": "Os 8 Prelúdios", "en": "All 8 Preludes",
                "fr": "Les 8 Préludes", "es": "Los 8 Preludios"}},
            {"id": "5FV-UctnFZc", "performer": {"pt": "Coletânea", "en": "Compilation", "fr": "Compilation", "es": "Recopilación"}, "year": "2021", "note": {
                "pt": "Eight Preludes complete", "en": "Complete Eight Preludes",
                "fr": "Intégrale des 8 Préludes", "es": "Los 8 Preludios completos"}},
        ],
    },
    {
        "num": 7,
        "labels": {
            "pt": "7º Prelúdio · Si bemol maior",
            "en": "7th Prelude · B-flat major",
            "fr": "7e Prélude · si bémol majeur",
            "es": "7º Preludio · Si bemol mayor",
        },
        "videos": [
            {"id": "l7gjYUxhXjU", "performer": "Korneel Bernolet", "year": "2018", "note": {
                "pt": "Cravo Dulcken 1747", "en": "Dulcken harpsichord 1747",
                "fr": "Clavecin Dulcken 1747", "es": "Clave Dulcken 1747"}},
            {"id": "vXYZjHvCfcA", "performer": "Denis Bonenfant", "year": "2011", "note": {
                "pt": "Cravista canadense", "en": "Canadian harpsichordist",
                "fr": "Claveciniste canadien", "es": "Clavecinista canadiense"}},
            {"id": "9aF_Bbw6vkw", "performer": {"pt": "Anônimo", "en": "Anonymous", "fr": "Anonyme", "es": "Anónimo"}, "year": "2024", "note": {
                "pt": "Performance recente · Si bemol", "en": "Recent performance · B-flat",
                "fr": "Interprétation récente · si bémol",
                "es": "Interpretación reciente · Si bemol"}},
            {"id": "utRqHpz4bYM", "performer": {"pt": "Anônimo", "en": "Anonymous", "fr": "Anonyme", "es": "Anónimo"}, "year": "2017", "note": {
                "pt": "Septième Prélude · com partitura",
                "en": "Septième Prélude · with score",
                "fr": "Septième Prélude · avec partition",
                "es": "Septième Prélude · con partitura"}},
            {"id": "uqtv371isgk", "performer": "Gustav Leonhardt", "year": "1964", "note": {
                "pt": "Integral histórica", "en": "Historic complete set",
                "fr": "Intégrale historique", "es": "Integral histórica"}},
        ],
    },
    {
        "num": 8,
        "labels": {
            "pt": "8º Prelúdio · Mi menor",
            "en": "8th Prelude · E minor",
            "fr": "8e Prélude · mi mineur",
            "es": "8º Preludio · Mi menor",
        },
        "videos": [
            {"id": "X42kmwdUe_4", "performer": "Korneel Bernolet", "year": "2018", "note": {
                "pt": "Cravo Dulcken 1747 · finalização da série",
                "en": "Dulcken harpsichord 1747 · series finale",
                "fr": "Clavecin Dulcken 1747 · finale de la série",
                "es": "Clave Dulcken 1747 · final de la serie"}},
            {"id": "uqtv371isgk", "performer": "Gustav Leonhardt", "year": "1964", "note": {
                "pt": "Integral histórica · referência",
                "en": "Historic complete set · reference",
                "fr": "Intégrale historique · référence",
                "es": "Integral histórica · referencia"}},
            {"id": "5FV-UctnFZc", "performer": {"pt": "Coletânea", "en": "Compilation", "fr": "Compilation", "es": "Recopilación"}, "year": "2021", "note": {
                "pt": "Os 8 Prelúdios completos",
                "en": "The Eight Preludes complete",
                "fr": "Les 8 Préludes intégrale",
                "es": "Los 8 Preludios completos"}},
            {"id": "yhUigHfxkDw", "performer": {"pt": "Coletânea", "en": "Compilation", "fr": "Compilation", "es": "Recopilación"}, "year": "2019", "note": {
                "pt": "Compilação dos 8 Prelúdios",
                "en": "Complete set of 8 Preludes",
                "fr": "Compilation des 8 Préludes",
                "es": "Compilación de los 8 Preludios"}},
            {"id": "p0S5wxzzIrg", "performer": "Scott Ross", "year": "1977", "note": {
                "pt": "Obras integrais · selo STIL",
                "en": "Complete works · STIL label",
                "fr": "Œuvres intégrales · label STIL",
                "es": "Obras completas · sello STIL"}},
        ],
    },
]

INTROS = {
    "pt": "Cinco gravações canônicas. Compare interpretações:",
    "en": "Five canonical recordings. Compare interpretations:",
    "fr": "Cinq enregistrements canoniques. Comparez les interprétations :",
    "es": "Cinco grabaciones canónicas. Compare interpretaciones:",
}

SECTION_HEADER = {
    "pt": "<h3>Os 8 Prelúdios em gravação — 5 interpretações por Prelúdio</h3>",
    "en": "<h3>The 8 Preludes on recording — 5 interpretations per Prelude</h3>",
    "fr": "<h3>Les 8 Préludes en enregistrement — 5 interprétations par Prélude</h3>",
    "es": "<h3>Los 8 Preludios en grabación — 5 interpretaciones por Preludio</h3>",
}


def resolve(value, lang: str):
    """Resolve string ou dict {lang:str} para a string do idioma."""
    if isinstance(value, dict):
        return value.get(lang, value.get("pt", ""))
    return value


def build_pickers_block(lang: str) -> str:
    out = [SECTION_HEADER[lang], ""]
    intro = INTROS[lang]
    for p in PRELUDIOS:
        videos_json = json.dumps(
            [
                {
                    "id": v["id"],
                    "title": p["labels"][lang],
                    "performer": resolve(v["performer"], lang),
                    "year": v["year"],
                    "note": resolve(v["note"], lang),
                }
                for v in p["videos"]
            ],
            ensure_ascii=False,
        )
        # data-videos entre aspas simples; escapar apostrofos do JSON com &#39;
        # (HTML entity) para nao quebrar o atributo.
        videos_attr = videos_json.replace("'", "&#39;")
        block = (
            '    <div class="video-picker"\n'
            f'         data-intro="{intro}"\n'
            f"         data-videos='{videos_attr}'>\n"
            f'      <h5>{p["labels"][lang]}</h5>\n'
            "    </div>"
        )
        out.append(block)
        out.append("")
    return "\n".join(out)


# Bloco antigo: começa em <div class="video-picker"> contendo AJVQwywAbF4 (Scott Ross)
# e termina em </div>. Usamos abordagem de string-search em vez de regex para
# evitar problemas com apostrofos nao-escapados no JSON (caso FR).
OLD_BLOCK_RE = None  # use find_old_block() instead


def find_old_block(text: str) -> tuple[int, int] | None:
    """Localiza o range (start, end) do video-picker contendo AJVQwywAbF4."""
    marker = "AJVQwywAbF4"
    idx = text.find(marker)
    if idx == -1:
        return None
    start = text.rfind('<div class="video-picker"', 0, idx)
    if start == -1:
        return None
    end = text.find("</div>", idx)
    if end == -1:
        return None
    end += len("</div>")
    # Inclui a quebra de linha anterior se houver
    if start > 0 and text[start - 1] == "\n":
        # Mantem o \n atual e procura espacos anteriores
        pass
    return (start, end)


def update_file(path: Path, lang: str, force: bool = False) -> str:
    if not path.is_file():
        return "skip (não existe)"
    text = path.read_text(encoding="utf-8")
    new_block = build_pickers_block(lang)

    new_header = SECTION_HEADER[lang]
    has_new = new_header in text
    has_old = find_old_block(text) is not None

    if has_new and not force:
        return "skip (já atualizado)"

    if has_new and force:
        # Re-substitui: localiza inicio do header novo e fim do ultimo video-picker
        start = text.find(new_header)
        # Procurar fim: o block termina com 8 video-pickers separados por newlines.
        # Vou usar: ate o proximo </article> ou h2/h3 que nao seja o nosso h5.
        # Simples: procurar o ultimo </div> apos o 8th picker.
        article_end = text.find("</article>", start)
        if article_end == -1:
            return "erro: </article> nao encontrado"
        # Encontrar o ultimo </div> antes de </article>
        end = text.rfind("</div>", start, article_end) + len("</div>")
        # Inclui linha branca antes de </article> se houver
        text = text[:start] + new_block + text[end:]
    elif has_old:
        rng = find_old_block(text)
        assert rng is not None
        start, end = rng
        text = text[:start] + new_block + text[end:]
    else:
        return "erro: bloco antigo nao encontrado e novo nao existe"

    path.write_text(text, encoding="utf-8")
    return "ok (force)" if force else "ok"


def main():
    import sys as _sys
    force = "--force" in _sys.argv
    paths = [
        (SITE / "tratados" / "couperin.html", "pt"),
        (SITE / "en" / "tratados" / "couperin.html", "en"),
        (SITE / "fr" / "tratados" / "couperin.html", "fr"),
        (SITE / "es" / "tratados" / "couperin.html", "es"),
    ]
    for path, lang in paths:
        result = update_file(path, lang, force=force)
        print(f"  {lang}: {path.relative_to(SITE)}  ->  {result}")


if __name__ == "__main__":
    main()
