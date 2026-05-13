"""Extract and categorize unique external URLs."""
import re, sys, json
from pathlib import Path
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding='utf-8')

root = Path('C:/Outros/Cravo/site')
urls = {}

for p in root.rglob('*.html'):
  rel = p.relative_to(root)
  try:
    text = p.read_text(encoding='utf-8', errors='replace')
  except Exception:
    continue
  for m in re.finditer(r'https?://[^\s"\'<>)]+', text):
    u = m.group(0).rstrip('.,;')
    urls.setdefault(u, set()).add(str(rel).replace('\\', '/'))

for p in (root/'assets').rglob('*.js'):
  rel = p.relative_to(root)
  try:
    text = p.read_text(encoding='utf-8', errors='replace')
  except Exception:
    continue
  for m in re.finditer(r'https?://[^\s"\'<>)]+', text):
    u = m.group(0).rstrip('.,;')
    urls.setdefault(u, set()).add(str(rel).replace('\\', '/'))

# Persist
result = {u: sorted(list(p)) for u, p in urls.items()}
Path('C:/Outros/Cravo/.agent/work/urls.json').write_text(
  json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8'
)

by_host = {}
for u, pages in urls.items():
  host = urlparse(u).netloc
  by_host.setdefault(host, []).append((u, sorted(pages)))

print(f"Total unique full URLs: {len(urls)}")
print(f"Total unique hosts: {len(by_host)}\n")
for host in sorted(by_host):
  uniq = by_host[host]
  print(f"=== {host} ({len(uniq)} URL{'s' if len(uniq)>1 else ''}) ===")
  for u, pages in sorted(uniq)[:8]:
    print(f"  {u}")
  if len(uniq) > 8:
    print(f"  ... +{len(uniq)-8} more")
  print()
