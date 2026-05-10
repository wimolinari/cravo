"""Constrói knowledge base do chatbot a partir do PDF + recursos do site.

Saída em chatbot/knowledge/:
  - tratado_full.txt — texto integral dos 4 tratados (pp. 7-119, sem capa/sumário)
  - glossary.json     — 70 termos do dicionário (extraído do glossario.js)
  - sitemap.json      — mapping URL canônica → tema → palavras-chave
  - images.json       — inventário das 167 imagens com captions
"""
import os, re, json, fitz, glob

ROOT = r'C:\Outros\Cravo'
PDF = os.path.join(ROOT, '2020tratadocravo.pdf')
SITE = os.path.join(ROOT, 'site')
OUT = os.path.join(ROOT, 'chatbot', 'knowledge')

# 1) Extract integral text
doc = fitz.open(PDF)
sections = []
current_section = None
all_text = []

# Map page ranges to sections
section_map = [
    ('apresentacao',     range(9, 11),   'Apresentação'),
    ('prefacio',         range(11, 21),  'Prefácio (sobre os 4 tratados)'),
    ('sancta_maria',     range(21, 54),  'Sancta Maria — Arte de tocar Fantasia (1565)'),
    ('frescobaldi',      range(55, 59),  'Frescobaldi — Ao Leitor (1637)'),
    ('couperin',         range(59, 109), 'Couperin — A Arte de tocar o Cravo (1717)'),
    ('rameau',           range(109, 120), 'Rameau — Da Mecânica dos Dedos no Cravo (1724)'),
]

for sec_id, page_range, sec_label in section_map:
    section_text = [f'\n\n=== SECTION: {sec_label} ===\n']
    for pno in page_range:
        if pno - 1 >= len(doc):
            continue
        page = doc[pno - 1]
        text = page.get_text() or ''
        # Clean: remove copyright footers
        text = re.sub(r'©\s*2013\s*by\s*Fagerlande[^\n]*', '', text)
        text = re.sub(r'Tomas de Sancta Maria[^\n]*Arte de tocar Fantasia\s*', '', text)
        text = re.sub(r'François Couperin[^\n]*Arte de tocar o Cravo\s*', '', text)
        text = re.sub(r'Jean-Philippe Rameau[^\n]*Cravo\s*', '', text)
        text = re.sub(r'Tratados e Métodos de Teclado\s*', '', text)
        text = re.sub(r'Girolamo Frescobaldi\s*[–-]\s*Ao Leitor\s*', '', text)
        text = re.sub(r'Prefácio\s*\n', '\n', text)
        # Mark page boundary
        section_text.append(f'\n[Page {pno}]\n{text.strip()}\n')
    sections.append((sec_id, '\n'.join(section_text)))

# Combine
full_text = '\n'.join(s[1] for s in sections)
total = len(doc)
doc.close()

with open(os.path.join(OUT, 'tratado_full.txt'), 'w', encoding='utf-8') as f:
    f.write(full_text)
print(f'tratado_full.txt: {len(full_text)} chars, {total} pages source')

# Save individual sections too
for sec_id, content in sections:
    with open(os.path.join(OUT, f'section_{sec_id}.txt'), 'w', encoding='utf-8') as f:
        f.write(content)

# 2) Extract glossary from glossario.js
glossary_js = os.path.join(SITE, 'assets', 'glossario.js')
with open(glossary_js, 'r', encoding='utf-8') as f:
    js_content = f.read()

# Parse window.GLOSSARIO = { ... }
match = re.search(r'window\.GLOSSARIO\s*=\s*(\{.*?\n\};)', js_content, re.DOTALL)
glossary = {}
if match:
    raw = match.group(1)
    # Match each entry: 'key': { titulo: '...', original: '...', descricao: '...' }
    # JS uses single quotes — convert to JSON-like
    entries = re.finditer(
        r"'([\w-]+)':\s*\{\s*titulo:\s*'([^']*(?:''[^']*)*)',\s*original:\s*'([^']*(?:''[^']*)*)',\s*descricao:\s*'([^']*(?:''[^']*)*)'",
        raw, re.DOTALL
    )
    for e in entries:
        key, titulo, original, descricao = e.groups()
        glossary[key] = {
            'titulo': titulo,
            'original': original,
            'descricao': descricao
        }

with open(os.path.join(OUT, 'glossary.json'), 'w', encoding='utf-8') as f:
    json.dump(glossary, f, ensure_ascii=False, indent=2)
print(f'glossary.json: {len(glossary)} entries')

# 3) Sitemap with topic → URL mapping
sitemap = {
    'tratados': {
        'sancta_maria': {
            'url': '/cravo/tratados/sancta-maria.html',
            'titulo': 'Thomas de Sancta Maria — Livro chamado Arte de tocar Fantasia (1565)',
            'topicos': ['posição das mãos', 'mão de gato', 'ataque das teclas', 'dedilhado',
                        'oitavas encolhidas', 'oitavas estendidas', 'redobros', 'quebros',
                        'ornamentos antigos', 'desigualdades rítmicas', 'elegância', 'buen ayre',
                        'consonâncias', 'hexacorde'],
            'capitulos': {
                'cap13': 'XIII — As 8 condições para tocar com perfeição',
                'cap14': 'XIV — Posição das mãos (mão de gato)',
                'cap15': 'XV — Como atacar as teclas',
                'cap16': 'XVI — Limpeza e distinção de vozes',
                'cap17': 'XVII — Correr as mãos',
                'cap18': 'XVIII — Dedilhado (tabela completa)',
                'cap19a': 'XIX — Tocar com elegância (notes inégales)',
                'cap19b': 'XIXb — Redobros e Quebros (ornamentos)',
            },
        },
        'frescobaldi': {
            'url': '/cravo/tratados/frescobaldi.html',
            'titulo': 'Girolamo Frescobaldi — Ao Leitor (1637)',
            'topicos': ['stylus fantasticus', 'tocata', 'tempo livre', 'afetos cantáveis',
                        'arpejar', 'cadências sustentadas', 'trinado', 'partita',
                        'passacalha', 'chacona'],
            'pontos': {
                'p1': 'Tempo livre, como nos madrigais',
                'p2': 'Tocatas em passagens autônomas',
                'p3': 'Começos arpejando',
                'p4': 'Pausa após trinados',
                'p5': 'Cadências sustentadas',
                'p6': 'Trinado em uma mão, passagem na outra',
                'p7': 'Colcheias e semicolcheias',
                'p8': 'Pausa antes das passagens duplas',
                'p9': 'Partitas, Passacalhas, Chaconas',
            },
        },
        'couperin': {
            'url': '/cravo/tratados/couperin.html',
            'titulo': 'François Couperin — A Arte de tocar o Cravo (1717)',
            'topicos': ['posição do corpo', 'idade para começar', 'espineta',
                        'cravo acoplado', 'plectros', 'aspiração', 'suspensão',
                        'mordente', 'apogiatura', 'trinado', 'port-de-voix', 'pincé',
                        'tremblement', 'progressões', 'terças ligadas', 'alemanda',
                        'prelúdios', 'mesuré', 'compasso', 'cadência', 'movimento',
                        'sonatas', 'bom gosto', 'notas críticas'],
            'capitulos': {
                'prefacio': 'Prefácio e plano do método',
                'postura': '1 — Posição do corpo e das mãos',
                'reflexoes': '2 — Reflexões pedagógicas',
                'dedilhado-modo': '3 — Maneira de escolher o dedilhado',
                'expressao': '4 — Aspiração e suspensão',
                'ornamentos': '5 — Ornamentos',
                'exercicios': '6 — Pequenos exercícios para formar as mãos',
                'dedilhados-pecas': '7 — Dedilhados nas peças do Primeiro Livro',
                'preludios': '8 — Os 8 Prelúdios',
                'sonatas': '9 — O cravo, as Sonatas e o bom gosto francês',
                'notas-criticas': '10 — Notas Críticas (apêndice editorial · 23 correções)',
                'tabela': '11 — Tabela de ornamentos do Primeiro Livro',
            },
        },
        'rameau': {
            'url': '/cravo/tratados/rameau.html',
            'titulo': 'Jean-Philippe Rameau — Da Mecânica dos Dedos no Cravo (1724)',
            'topicos': ['mecânica dos dedos', 'analogia andar/tocar', 'cotovelos progressivos',
                        'mão morta', 'pulso flexível', 'movimento natural',
                        'independência dos dedos', 'cair (não bater)',
                        'primeira lição', 'rolamento', 'bateria', 'passagem do polegar',
                        'cadência', 'trinado', 'menuet en rondeau', 'les cyclopes',
                        'les tourbillons', 'mãos cruzadas'],
            'capitulos': {
                'analogia': '1 — A analogia: andar e tocar',
                'postura': '2 — Posição ao instrumento',
                'movimento': '3 — O movimento dos dedos',
                'licao': '4 — A Primeira Lição',
                'rolamentos': '5 — Rolamentos e baterias',
                'trinados': '6 — Trinados e cadências',
                'observacoes': '7 — Observações finais',
            },
        },
    },
    'temas': {
        'postura': {
            'url': '/cravo/temas/postura.html',
            'titulo': 'Postura ao instrumento',
            'topicos': ['mão de gato', 'arco esticado', 'espelho', 'cotovelos',
                        'altura do assento', 'distância do teclado'],
        },
        'dedilhados': {
            'url': '/cravo/temas/dedilhados.html',
            'titulo': 'Dedilhados — do antigo ao moderno',
            'topicos': ['3 sobre 2', 'passagem do polegar', 'cruzamento',
                        'substituição de dedos', 'numeração'],
        },
        'ornamentos': {
            'url': '/cravo/temas/ornamentos.html',
            'titulo': 'Ornamentos comparados',
            'topicos': ['trinado', 'mordente', 'redobro', 'quebro',
                        'apogiatura', 'aspiração', 'suspensão'],
        },
        'articulacao': {
            'url': '/cravo/temas/articulacao.html',
            'titulo': 'Articulação e toque',
            'topicos': ['legato', 'doçura', 'cair vs bater', 'aspiração'],
        },
        'ritmo-tempo': {
            'url': '/cravo/temas/ritmo-tempo.html',
            'titulo': 'Ritmo, tempo e expressão',
            'topicos': ['notes inégales', 'tempo livre', 'cadência expressiva',
                        'mesuré', 'rubato'],
        },
        'exercicios-baterias': {
            'url': '/cravo/temas/exercicios-baterias.html',
            'titulo': 'Exercícios e baterias',
            'topicos': ['primeira lição', 'progressões', 'baterias cruzadas',
                        'rolamentos'],
        },
    },
    'recursos': {
        'comparador':         {'url': '/cravo/comparador.html',         'titulo': 'Comparador lado a lado dos 4 autores'},
        'roteiro':            {'url': '/cravo/roteiro-estudo.html',     'titulo': 'Roteiro de estudo em 6 etapas'},
        'partituras_viewer':  {'url': '/cravo/partituras-viewer.html',  'titulo': 'Visualizador de partituras (27 obras)'},
        'glossario':          {'url': '/cravo/glossario.html',          'titulo': 'Dicionário (70 termos)'},
        'pdf_original':       {'url': '/cravo/ler-pdf.html',            'titulo': 'PDF original UFRJ 2013'},
        'creditos':           {'url': '/cravo/creditos.html',           'titulo': 'Créditos e bibliografia'},
        'apresentacao':       {'url': '/cravo/apresentacao-prefacio.html', 'titulo': 'Apresentação e Prefácio'},
    }
}

with open(os.path.join(OUT, 'sitemap.json'), 'w', encoding='utf-8') as f:
    json.dump(sitemap, f, ensure_ascii=False, indent=2)
print(f'sitemap.json: {sum(len(v) for v in sitemap.values())} entries')

# 4) Curated images — extraído de partituras-viewer.html (única fonte de verdade
# para mapeamento "imagem ↔ obra/seção"). O modelo só deve referenciar imagens
# desta lista, com os títulos exatos.
viewer_html = os.path.join(SITE, 'partituras-viewer.html')
with open(viewer_html, 'r', encoding='utf-8') as f:
    viewer_content = f.read()

curated = []
current_group = None
# Parse <optgroup label="..."> e <option value="..." data-meta="..." data-tip="...">Title</option>
group_re = re.compile(r'<optgroup\s+label="([^"]+)"')
option_re = re.compile(
    r'<option\s+value="([^"]+)"'
    r'\s+data-meta="([^"]*)"'
    r'\s+data-tip="([^"]*)"\s*>'
    r'([^<]+)'
    r'</option>'
)

for line in viewer_content.split('\n'):
    g = group_re.search(line)
    if g:
        current_group = g.group(1).strip()
        continue
    o = option_re.search(line)
    if o:
        rel_path, meta, tip, title = o.groups()
        # rel_path tipo "couperin/embedded/p081-img1.jpeg"
        tratado = rel_path.split('/')[0]
        m = re.search(r'p(\d{3})-img', rel_path)
        pdf_page = int(m.group(1)) if m else 0
        curated.append({
            'tratado': tratado,
            'titulo': title.strip(),
            'descricao': meta.strip(),
            'nivel': tip.strip(),
            'grupo': current_group or '',
            'pdf_page': pdf_page,
            'url_path': f'/cravo/partituras/{rel_path}',
        })

# Verificação: cada arquivo curado realmente existe em disco
missing = []
for img in curated:
    rel = img['url_path'].replace('/cravo/', '')
    full = os.path.join(SITE, rel)
    if not os.path.isfile(full):
        missing.append(img['url_path'])
if missing:
    print(f'AVISO: {len(missing)} imagens curadas não encontradas em disco:')
    for m in missing:
        print(f'  - {m}')

with open(os.path.join(OUT, 'images.json'), 'w', encoding='utf-8') as f:
    json.dump(curated, f, ensure_ascii=False, indent=2)
print(f'images.json: {len(curated)} imagens curadas (com títulos e contexto)')

# 5) Topics for chatbot starter (inspired by comparador.html)
topics = [
    {
        'icon': '🪑',
        'label': 'Postura ao instrumento',
        'sample_question': 'Como devo me posicionar ao cravo segundo Couperin e Rameau?',
        'related_url': '/cravo/temas/postura.html',
    },
    {
        'icon': '✋',
        'label': 'Posição das mãos',
        'sample_question': 'O que Sancta Maria quer dizer com "mão de gato"?',
        'related_url': '/cravo/temas/postura.html#maos',
    },
    {
        'icon': '🎹',
        'label': 'Como atacar a tecla',
        'sample_question': 'Devo atacar com força ou com leveza? O que dizem os tratados?',
        'related_url': '/cravo/temas/articulacao.html#ataque',
    },
    {
        'icon': '🤚',
        'label': 'Dedilhado',
        'sample_question': 'Quando uso passagem do polegar e quando cruzo o 3 sobre o 2?',
        'related_url': '/cravo/temas/dedilhados.html',
    },
    {
        'icon': '〰',
        'label': 'Ornamentos',
        'sample_question': 'Como começar um trinado: pela nota principal ou pela superior?',
        'related_url': '/cravo/temas/ornamentos.html',
    },
    {
        'icon': '🎵',
        'label': 'Notes inégales',
        'sample_question': 'O que são as desigualdades rítmicas francesas e como aplicá-las?',
        'related_url': '/cravo/temas/ritmo-tempo.html',
    },
    {
        'icon': '📖',
        'label': 'Os 4 tratados',
        'sample_question': 'Qual a diferença entre os tratados de Couperin e Rameau?',
        'related_url': '/cravo/comparador.html',
    },
    {
        'icon': '🎼',
        'label': 'Repertório',
        'sample_question': 'Quais peças posso estudar primeiro como iniciante de cravo?',
        'related_url': '/cravo/roteiro-estudo.html',
    },
    {
        'icon': '👶',
        'label': 'Idade para começar',
        'sample_question': 'Com que idade Couperin recomenda iniciar o estudo do cravo?',
        'related_url': '/cravo/temas/postura.html',
    },
    {
        'icon': '🌪',
        'label': 'Baterias e Les Cyclopes',
        'sample_question': 'O que são as "baterias com mãos cruzadas" inventadas por Rameau?',
        'related_url': '/cravo/temas/exercicios-baterias.html',
    },
]

with open(os.path.join(OUT, 'topics.json'), 'w', encoding='utf-8') as f:
    json.dump(topics, f, ensure_ascii=False, indent=2)
print(f'topics.json: {len(topics)} starter topics')

print('\nKnowledge base built successfully.')
