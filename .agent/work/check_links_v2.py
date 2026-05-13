"""Verify all external links from the CURRENT site files."""
import sys, urllib.request, ssl, json, re, time
from urllib.error import URLError, HTTPError

sys.stdout.reconfigure(encoding='utf-8')

urls_data = json.loads(open('C:/Outros/Cravo/.agent/work/urls.json', encoding='utf-8').read())
SKIP_HOSTS = ('fonts.googleapis.com', 'fonts.gstatic.com', 'www.w3.org')
urls = sorted(u for u in urls_data if not any(h in u for h in SKIP_HOSTS))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

results = []
for u in urls:
  try:
    req = urllib.request.Request(u, headers={'User-Agent': UA, 'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'})
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
      body = r.read(8192).decode('utf-8', errors='replace')
      mt = re.search(r'<title[^>]*>(.*?)</title>', body, re.I|re.S)
      title = mt.group(1).strip()[:100] if mt else ''
      print(f'OK {r.status} {u}')
      if title: print(f'   title: {title}')
      results.append({'url': u, 'status': r.status, 'ok': True, 'title': title})
  except HTTPError as e:
    print(f'HTTP {e.code} {u}')
    results.append({'url': u, 'status': e.code, 'ok': False})
  except URLError as e:
    print(f'URLERR {e.reason} {u}')
    results.append({'url': u, 'status': None, 'ok': False, 'reason': str(e.reason)})
  except Exception as e:
    print(f'ERR {e} {u}')
    results.append({'url': u, 'status': None, 'ok': False, 'reason': str(e)})
  time.sleep(0.5)

with open('C:/Outros/Cravo/.agent/work/link_results_v2.json', 'w', encoding='utf-8') as f:
  json.dump(results, f, ensure_ascii=False, indent=2)
ok = sum(1 for r in results if r.get('ok'))
print(f'\nResult: {ok}/{len(results)} OK')
