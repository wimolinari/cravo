"""Find Toccate Libro 2 on Frescobaldi page; Santa María via Google; Gallica direct."""
import sys, urllib.request, ssl, re, time
from urllib.error import HTTPError

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def fetch(url, n=300000):
  req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language':'en;q=0.9'})
  with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
    return r.status, r.geturl(), r.read(n).decode('utf-8', errors='replace')

# Get Frescobaldi page and find all Toccate work links
print('--- Frescobaldi Toccate/Libro links ---')
try:
  s, fin, body = fetch('https://imslp.org/wiki/Category:Frescobaldi%2C_Girolamo', 500000)
  # Extract all work links + nearby anchor text
  work_links = re.findall(r'href="(/wiki/[^"#?]+_\(Frescobaldi[^"]*\))"[^>]*>([^<]+)<', body)
  toccate = [(href, txt) for href, txt in work_links if 'occate' in href or 'occate' in txt or 'Libro' in href or 'Libro' in txt]
  seen = set()
  for href, txt in toccate:
    if href in seen: continue
    seen.add(href)
    print(f'  {txt!r}')
    print(f'    https://imslp.org{href}')
except Exception as e:
  print(f'  ERR {e}')

print('\n--- IMSLP general search: Santa Maria ---')
try:
  s, fin, body = fetch('https://imslp.org/index.php?title=Special%3ASearch&search=Tom%C3%A1s+de+Santa+Mar%C3%ADa', 100000)
  print(f'  {s} {fin}')
  # Capture mw-search-result-heading anchors
  res = re.findall(r'class="mw-search-result-heading"[^>]*>.*?href="([^"]+)"[^>]*>([^<]+)<', body, re.S)
  for href, txt in res[:15]:
    print(f'  {txt!r}')
    print(f'    https://imslp.org{href}')
except Exception as e:
  print(f'  ERR {e}')

# Gallica search direct
print('\n--- Gallica search L\'Art de toucher ---')
time.sleep(2)
try:
  url = 'https://gallica.bnf.fr/services/Search?lang=FR&query=%28dc.title%20all%20%22Art%20de%20toucher%20le%20clavecin%22%29&filter=dc.creator%20all%20%22Couperin%22'
  s, fin, body = fetch(url, 50000)
  print(f'  {s} {fin}')
  arks = sorted(set(re.findall(r'(ark:/12148/[A-Za-z0-9]+)', body)))
  for a in arks[:20]:
    print(f'  {a}')
except Exception as e:
  print(f'  ERR {e}')
