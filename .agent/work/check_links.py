"""HTTP-check each external URL: status + final URL after redirects."""
import sys, urllib.request, ssl, json
from urllib.error import URLError, HTTPError

sys.stdout.reconfigure(encoding='utf-8')

urls = [
  'https://commons.wikimedia.org/w/index.php?search=cat+paw+arched&title=Special:MediaSearch&go=Go&type=image',
  'https://commons.wikimedia.org/wiki/Category:Fran%C3%A7ois_Couperin',
  'https://commons.wikimedia.org/wiki/Category:Frescobaldi',
  'https://commons.wikimedia.org/wiki/Category:Hands_playing_harpsichord',
  'https://commons.wikimedia.org/wiki/Category:Jean-Philippe_Rameau',
  'https://gallica.bnf.fr/ark:/12148/bpt6k856840',
  'https://imslp.org/wiki/Arte_de_ta%C3%B1er_fantas%C3%ADa_(Santa_Mar%C3%ADa%2C_Tom%C3%A1s_de)',
  'https://imslp.org/wiki/L%27Art_de_toucher_le_clavecin_(Couperin%2C_Fran%C3%A7ois)',
  'https://imslp.org/wiki/Pi%C3%A8ces_de_clavessin_(Rameau%2C_Jean-Philippe)',
  'https://imslp.org/wiki/Toccate_e_partite_d%27intavolatura_di_cimbalo%2C_Libro_2_(Frescobaldi%2C_Girolamo)',
  'https://routepesquisa.com.br/cravo',
  'https://www.musica.ufrj.br',
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE  # be lenient — we only care if endpoint exists

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

results = []
for u in urls:
  try:
    req = urllib.request.Request(u, headers={'User-Agent': UA, 'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
      status = r.status
      final = r.geturl()
      title = ''
      try:
        body = r.read(8192).decode('utf-8', errors='replace')
        import re as _re
        mt = _re.search(r'<title[^>]*>(.*?)</title>', body, _re.I|_re.S)
        if mt: title = mt.group(1).strip()[:120]
      except Exception:
        pass
      print(f'OK {status} {u}')
      if final != u:
        print(f'   → final: {final}')
      if title:
        print(f'   title: {title}')
      results.append({'url': u, 'status': status, 'final': final, 'title': title, 'ok': True})
  except HTTPError as e:
    print(f'HTTP {e.code} {u}')
    results.append({'url': u, 'status': e.code, 'ok': False, 'reason': str(e)})
  except URLError as e:
    print(f'URLERR {e.reason} {u}')
    results.append({'url': u, 'status': None, 'ok': False, 'reason': str(e.reason)})
  except Exception as e:
    print(f'ERROR {e} {u}')
    results.append({'url': u, 'status': None, 'ok': False, 'reason': str(e)})

with open('C:/Outros/Cravo/.agent/work/link_results.json', 'w', encoding='utf-8') as f:
  json.dump(results, f, ensure_ascii=False, indent=2)
print(f'\nDone. {sum(1 for r in results if r.get("ok"))} of {len(results)} OK.')
