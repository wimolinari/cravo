"""Test alternative slugs for broken external links."""
import sys, urllib.request, ssl, re
from urllib.error import URLError, HTTPError

sys.stdout.reconfigure(encoding='utf-8')

candidates = {
  'IMSLP Santa Maria': [
    'https://imslp.org/wiki/Libro_llamado_Arte_de_ta%C3%B1er_fantas%C3%ADa_(Santa_Mar%C3%ADa%2C_Tom%C3%A1s_de)',
    'https://imslp.org/wiki/Arte_de_ta%C3%B1er_fantas%C3%ADa_(Santamar%C3%ADa%2C_Tom%C3%A1s_de)',
    'https://imslp.org/wiki/Libro_Llamado_Arte_de_Ta%C3%B1er_Fantas%C3%ADa_(Santa_Mar%C3%ADa%2C_Tom%C3%A1s_de)',
    'https://imslp.org/wiki/Special:Search/Santa+Maria+Arte+tañer',
  ],
  'IMSLP Rameau Pieces de clavecin': [
    'https://imslp.org/wiki/Pi%C3%A8ces_de_clavecin_(Rameau%2C_Jean-Philippe)',
    'https://imslp.org/wiki/Pi%C3%A8ces_de_Clavecin_(Rameau%2C_Jean-Philippe)',
    'https://imslp.org/wiki/Pieces_de_clavecin_(Rameau%2C_Jean-Philippe)',
    'https://imslp.org/wiki/Pi%C3%A8ces_de_clavessin_avec_une_m%C3%A9thode_(Rameau%2C_Jean-Philippe)',
    'https://imslp.org/wiki/Pi%C3%A8ces_de_clavecin_avec_une_m%C3%A9thode_(Rameau%2C_Jean-Philippe)',
    'https://imslp.org/wiki/Nouvelles_suites_de_pi%C3%A8ces_de_clavecin_(Rameau%2C_Jean-Philippe)',
  ],
  'IMSLP Frescobaldi Libro 2': [
    'https://imslp.org/wiki/Il_secondo_libro_di_toccate%2C_canzone%2C_versi_d%27hinni%2C_magnificat%2C_gagliarde%2C_correnti_et_altre_partite_d%27intavolatura_di_cimbalo_et_organo_(Frescobaldi%2C_Girolamo)',
    'https://imslp.org/wiki/Toccate_d%27intavolatura_di_cimbalo_et_organo%2C_Libro_2_(Frescobaldi%2C_Girolamo)',
    'https://imslp.org/wiki/Toccate%2C_Libro_2_(Frescobaldi%2C_Girolamo)',
    'https://imslp.org/wiki/Toccate_e_Partite_d%27Intavolatura_di_Cimbalo%2C_Libro_II_(Frescobaldi%2C_Girolamo)',
    'https://imslp.org/wiki/Il_Secondo_Libro_di_Toccate_(Frescobaldi%2C_Girolamo)',
  ],
  'Wikimedia Hands harpsichord': [
    'https://commons.wikimedia.org/wiki/Category:Hands_at_the_harpsichord',
    'https://commons.wikimedia.org/wiki/Category:Hands_playing_keyboard_instruments',
    'https://commons.wikimedia.org/wiki/Category:Harpsichordists',
    'https://commons.wikimedia.org/wiki/Category:People_playing_harpsichord',
    'https://commons.wikimedia.org/wiki/Category:People_playing_the_harpsichord',
    'https://commons.wikimedia.org/wiki/Category:Harpsichord_players',
    'https://commons.wikimedia.org/wiki/Category:Playing_harpsichord',
    'https://commons.wikimedia.org/wiki/Category:Harpsichord',
  ],
  'Gallica L Art de toucher': [
    'https://gallica.bnf.fr/ark:/12148/bpt6k856840.image',
    'https://gallica.bnf.fr/ark:/12148/bpt6k856840.r=couperin',
    'https://gallica.bnf.fr/ark:/12148/btv1b8451606d',
    'https://gallica.bnf.fr/ark:/12148/bpt6k856840/f1.item',
    'https://gallica.bnf.fr/ark:/12148/bd6t5378133r',
  ],
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

for label, urls in candidates.items():
  print(f'\n=== {label} ===')
  for u in urls:
    try:
      req = urllib.request.Request(u, headers={'User-Agent': UA, 'Accept-Language':'en;q=0.9'})
      with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        body = r.read(16384).decode('utf-8', errors='replace')
        mt = re.search(r'<title[^>]*>(.*?)</title>', body, re.I|re.S)
        title = mt.group(1).strip()[:120] if mt else ''
        print(f'  OK {r.status} {u}')
        if r.geturl() != u: print(f'     final: {r.geturl()}')
        if title: print(f'     title: {title}')
    except HTTPError as e:
      print(f'  {e.code} {u}')
    except Exception as e:
      print(f'  ERR {e} {u}')
