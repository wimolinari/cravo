"""Fill the empty Premier Livre pickers in all 4 languages with verified
real-performance videos."""
import sys, json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Build entries — note: apostrophes inside JSON must be HTML-encoded as &#39; because
# the data-videos attribute is wrapped in single quotes.
def to_attr(arr):
  raw = json.dumps(arr, ensure_ascii=False, separators=(',', ':'))
  # Escape apostrophes for HTML attribute safety
  return raw.replace("'", '&#39;')

videos_by_lang = {
  'pt': {
    'intro': "As peças mencionadas — Primeiro Livro (1713). Gravações em vídeo com intérpretes ao instrumento:",
    'list': [
      {"id":"fO16kQYaVHU","performer":"Magdalena Baczewska","title":"1er Ordre em Sol menor (integral)","year":"","duration":"19:52"},
      {"id":"QzAS9BuJPkA","performer":"Charlotte Mattax Moersch","title":"Sarabande la Majestueuse, 1er Ordre","year":"","duration":"2:26"},
      {"id":"dSx_MOtch08","performer":"Charlotte Mattax Moersch","title":"Allemande l'Auguste, 1er Ordre","year":"","duration":"2:41"},
    ],
  },
  'en': {
    'intro': "The pieces mentioned — First Book (1713). Video performances at the instrument:",
    'list': [
      {"id":"fO16kQYaVHU","performer":"Magdalena Baczewska","title":"1er Ordre in G minor (complete)","year":"","duration":"19:52"},
      {"id":"QzAS9BuJPkA","performer":"Charlotte Mattax Moersch","title":"Sarabande la Majestueuse, 1er Ordre","year":"","duration":"2:26"},
      {"id":"dSx_MOtch08","performer":"Charlotte Mattax Moersch","title":"Allemande l'Auguste, 1er Ordre","year":"","duration":"2:41"},
    ],
  },
  'fr': {
    'intro': "Les pièces mentionnées — Premier Livre (1713). Enregistrements vidéo d'interprètes à l'instrument :",
    'list': [
      {"id":"fO16kQYaVHU","performer":"Magdalena Baczewska","title":"1er Ordre en sol mineur (intégrale)","year":"","duration":"19:52"},
      {"id":"QzAS9BuJPkA","performer":"Charlotte Mattax Moersch","title":"Sarabande la Majestueuse, 1er Ordre","year":"","duration":"2:26"},
      {"id":"dSx_MOtch08","performer":"Charlotte Mattax Moersch","title":"Allemande l'Auguste, 1er Ordre","year":"","duration":"2:41"},
    ],
  },
  'es': {
    'intro': "Las piezas mencionadas — Primer Libro (1713). Grabaciones en vídeo con intérpretes al instrumento:",
    'list': [
      {"id":"fO16kQYaVHU","performer":"Magdalena Baczewska","title":"1er Ordre en sol menor (integral)","year":"","duration":"19:52"},
      {"id":"QzAS9BuJPkA","performer":"Charlotte Mattax Moersch","title":"Sarabande la Majestueuse, 1er Ordre","year":"","duration":"2:26"},
      {"id":"dSx_MOtch08","performer":"Charlotte Mattax Moersch","title":"Allemande l'Auguste, 1er Ordre","year":"","duration":"2:41"},
    ],
  },
}

# Per language: file path, current intro, new intro
files = {
  'pt': ('C:/Outros/Cravo/site/tratados/couperin.html',
         'As peças mencionadas — Primeiro Livro (1713). A integral está no recital de Rousset:'),
  'en': ('C:/Outros/Cravo/site/en/tratados/couperin.html',
         "The pieces mentioned — First Book (1713). The complete recording is in Rousset's recital:"),
  'fr': ('C:/Outros/Cravo/site/fr/tratados/couperin.html',
         "Les pièces mentionnées — Premier Livre (1713). L'intégrale figure dans le récital de Rousset :"),
  'es': ('C:/Outros/Cravo/site/es/tratados/couperin.html',
         "Las piezas mencionadas — Primer Libro (1713). La integral está en el recital de Rousset:"),
}

for lang, (path, old_intro) in files.items():
  p = Path(path)
  text = p.read_text(encoding='utf-8')
  data = videos_by_lang[lang]
  new_attr = to_attr(data['list'])
  # Replace intro
  text2 = text.replace(f'data-intro="{old_intro}"', f'data-intro="{data["intro"]}"')
  if text2 == text:
    print(f'WARN: intro not found in {path}')
  # Replace empty array (only the one for this picker — but all empty arrays in this
  # file are this picker by now, so safe)
  text3 = text2.replace("data-videos='[]'", f"data-videos='{new_attr}'", 1)
  if text3 == text2:
    print(f'WARN: empty data-videos not found in {path}')
    continue
  p.write_text(text3, encoding='utf-8')
  print(f'OK  {path}')
print('\nDone.')
