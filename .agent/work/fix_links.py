"""Apply URL fixes to all postura.html files (PT, EN, ES, FR)."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Exact OLD URL -> NEW URL replacements
fixes = [
  # Wikimedia: Hands_playing_harpsichord (404) -> Harpsichordists
  (
    'https://commons.wikimedia.org/wiki/Category:Hands_playing_harpsichord',
    'https://commons.wikimedia.org/wiki/Category:Harpsichordists',
  ),
  # IMSLP Santa Maria: Arte de tañer fantasía (Santa María, Tomás de) (404)
  # -> Arte de Tañer Fantasia (Santamaría, Tomás)
  (
    'https://imslp.org/wiki/Arte_de_ta%C3%B1er_fantas%C3%ADa_(Santa_Mar%C3%ADa%2C_Tom%C3%A1s_de)',
    'https://imslp.org/wiki/Arte_de_Ta%C3%B1er_Fantasia_(Santamar%C3%ADa%2C_Tom%C3%A1s)',
  ),
  # IMSLP Rameau: Pièces_de_clavessin -> Pièces_de_clavecin
  (
    'https://imslp.org/wiki/Pi%C3%A8ces_de_clavessin_(Rameau%2C_Jean-Philippe)',
    'https://imslp.org/wiki/Pi%C3%A8ces_de_clavecin_(Rameau%2C_Jean-Philippe)',
  ),
  # IMSLP Frescobaldi Libro 2: remove "di_cimbalo"
  (
    "https://imslp.org/wiki/Toccate_e_partite_d%27intavolatura_di_cimbalo%2C_Libro_2_(Frescobaldi%2C_Girolamo)",
    "https://imslp.org/wiki/Toccate_e_partite_d%27intavolatura%2C_Libro_2_(Frescobaldi%2C_Girolamo)",
  ),
  # Gallica ark bpt6k856840 (400) -> bpt6k1508406q (Wikipedia-confirmed correct ark for L'Art de toucher 1716)
  (
    'https://gallica.bnf.fr/ark:/12148/bpt6k856840',
    'https://gallica.bnf.fr/ark:/12148/bpt6k1508406q',
  ),
]

targets = [
  'C:/Outros/Cravo/site/temas/postura.html',
  'C:/Outros/Cravo/site/en/temas/postura.html',
  'C:/Outros/Cravo/site/es/temas/postura.html',
  'C:/Outros/Cravo/site/fr/temas/postura.html',
]

for tgt in targets:
  p = Path(tgt)
  text = p.read_text(encoding='utf-8')
  orig = text
  applied = []
  for old, new in fixes:
    if old in text:
      n = text.count(old)
      text = text.replace(old, new)
      applied.append(f'{n}x {old[:80]}')
  if text != orig:
    p.write_text(text, encoding='utf-8')
    print(f'\n[CHANGED] {tgt}')
    for a in applied:
      print(f'  - {a}')
  else:
    print(f'[unchanged] {tgt}')

print('\nDone.')
