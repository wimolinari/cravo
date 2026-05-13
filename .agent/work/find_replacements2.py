"""Probe IMSLP composer pages and Gallica search."""
import sys, urllib.request, ssl, re
from urllib.parse import quote
from urllib.error import HTTPError

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def fetch(url, n=20000):
  req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language':'en;q=0.9'})
  with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
    return r.status, r.geturl(), r.read(n).decode('utf-8', errors='replace')

# 1) IMSLP composer page for Santa María
print('--- IMSLP Category:Santa_Maria,_Tomas_de ---')
for slug in [
  'Category:Santa_Mar%C3%ADa%2C_Tom%C3%A1s_de',
  'Category:Santamar%C3%ADa%2C_Tom%C3%A1s_de',
  'Category:Santa_Maria%2C_Tom%C3%A1s_de',
]:
  url = 'https://imslp.org/wiki/' + slug
  try:
    s, fin, body = fetch(url, 60000)
    print(f'  {s} {url}')
    if s == 200:
      # Find work links: /wiki/<work>_(<composer>)
      works = re.findall(r'href="(/wiki/[^"#?]+_\(Santa[^"]*\))"', body)
      print(f'    found {len(works)} work links')
      for w in sorted(set(works))[:10]:
        print('     ', 'https://imslp.org' + w)
  except HTTPError as e:
    print(f'  {e.code} {url}')

# 2) IMSLP Frescobaldi composer page
print('\n--- IMSLP Frescobaldi works ---')
try:
  s, fin, body = fetch('https://imslp.org/wiki/Category:Frescobaldi%2C_Girolamo', 200000)
  print(f'  {s} {fin}')
  works = re.findall(r'href="(/wiki/[^"#?]+_\(Frescobaldi[^"]*\))"', body)
  candidates = [w for w in sorted(set(works)) if 'oc' in w.lower() or 'Libro' in w or '2' in w]
  print(f'  matches with "oc" or Libro or 2: {len(candidates)}')
  for w in candidates[:30]:
    print('   ', 'https://imslp.org' + w)
except Exception as e:
  print(f'  ERR {e}')

# 3) Gallica catalog search via SRU API (simpler text endpoint)
print('\n--- Gallica search: L\'Art de toucher Couperin ---')
search_urls = [
  'https://gallica.bnf.fr/services/Search?q=L%27Art+de+toucher+le+clavecin+Couperin',
  "https://gallica.bnf.fr/SRU?operation=searchRetrieve&query=(dc.title%20all%20%22Art%20de%20toucher%20le%20clavecin%22)%20and%20(dc.creator%20all%20%22Couperin%22)&maximumRecords=5",
]
for url in search_urls:
  try:
    s, fin, body = fetch(url, 30000)
    print(f'  {s} {url[:80]}...')
    # Extract any ark links
    arks = re.findall(r'(ark:/12148/[A-Za-z0-9]+)', body)
    for a in sorted(set(arks))[:10]:
      print('   ', a)
  except Exception as e:
    print(f'  ERR {e}')
