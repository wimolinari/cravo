"""Validate final replacement candidates."""
import sys, urllib.request, ssl, re, time
from urllib.error import HTTPError

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def check(url, label=''):
  req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language':'en;q=0.9'})
  try:
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
      body = r.read(16384).decode('utf-8', errors='replace')
      mt = re.search(r'<title[^>]*>(.*?)</title>', body, re.I|re.S)
      title = mt.group(1).strip()[:150] if mt else ''
      print(f'  {r.status} {label}')
      print(f'      URL: {url}')
      if r.geturl() != url: print(f'      final: {r.geturl()}')
      if title: print(f'      title: {title}')
      return True
  except HTTPError as e:
    print(f'  {e.code} {label} :: {url}')
  except Exception as e:
    print(f'  ERR {e} {label} :: {url}')
  return False

# Final candidates
print('=== Frescobaldi Libro 2 (CORRECTED) ===')
check('https://imslp.org/wiki/Toccate_e_partite_d%27intavolatura%2C_Libro_2_(Frescobaldi%2C_Girolamo)', 'fixed slug')

print('\n=== Rameau Pieces de clavecin (CORRECTED) ===')
check('https://imslp.org/wiki/Pi%C3%A8ces_de_clavecin_(Rameau%2C_Jean-Philippe)', 'fixed slug')

print('\n=== Santa Maria — Internet Archive fallback ===')
for u in [
  'https://archive.org/details/librollamadoarte01sant',
  'https://archive.org/details/librollamadoarte00sant',
  'https://archive.org/details/librollamadoart00sant',
  'https://en.wikipedia.org/wiki/Tom%C3%A1s_de_Santa_Mar%C3%ADa',
]:
  check(u)

print('\n=== Santa Maria — IMSLP composer alternatives ===')
for slug in [
  'Sancta_Maria%2C_Tom%C3%A1s_de',
  'Santa-Mar%C3%ADa%2C_Tom%C3%A1s_de',
  'Tom%C3%A1s_de_Santa_Mar%C3%ADa',
  'Santa_Maria_Tom%C3%A1s_de',
]:
  check('https://imslp.org/wiki/Category:' + slug)

print('\n=== Wikimedia harpsichord categories (CORRECTED) ===')
check('https://commons.wikimedia.org/wiki/Category:Harpsichordists', 'replacement')

print('\n=== Gallica L\'Art de toucher (alternative arks) ===')
time.sleep(3)
for ark in [
  'bpt6k856840w',
  'bpt6k856840p',
  'btv1b86260229',
  'bpt6k1153117t',  # known L'Art de toucher BnF copy
  'bpt6k857245',
]:
  url = f'https://gallica.bnf.fr/ark:/12148/{ark}'
  check(url, ark)
  time.sleep(1)
