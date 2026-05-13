"""Extract external links from href=, src=, content= attributes — handles parens in URLs."""
import re, sys, json
from pathlib import Path
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding='utf-8')

root = Path('C:/Outros/Cravo/site')
attr_re = re.compile(r'(?:href|src|content)\s*=\s*"([^"]+)"', re.IGNORECASE)
urls = {}

for p in root.rglob('*.html'):
  rel = str(p.relative_to(root)).replace('\\', '/')
  text = p.read_text(encoding='utf-8', errors='replace')
  for m in attr_re.finditer(text):
    u = m.group(1).strip()
    if u.startswith('http://') or u.startswith('https://'):
      urls.setdefault(u, set()).add(rel)

result = {u: sorted(list(p)) for u, p in urls.items()}
Path('C:/Outros/Cravo/.agent/work/urls.json').write_text(
  json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8'
)

by_host = {}
for u, pages in urls.items():
  host = urlparse(u).netloc
  by_host.setdefault(host, []).append(u)

print(f"Total unique URLs: {len(urls)}\n")
SKIP = {'fonts.googleapis.com', 'fonts.gstatic.com', 'www.w3.org'}
for host in sorted(by_host):
  if host in SKIP:
    print(f"[skip infra] {host}: {len(by_host[host])} URLs")
    continue
  print(f"=== {host} ===")
  for u in sorted(set(by_host[host])):
    print(f"  {u}")
  print()
