"""Verify candidate replacement videos via oEmbed."""
import sys, json, urllib.request, ssl
from urllib.error import HTTPError

sys.stdout.reconfigure(encoding='utf-8')
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

candidates = [
  ('fO16kQYaVHU', 'Magdalena Baczewska — 1er Ordre in G minor'),
  ('QzAS9BuJPkA', 'Charlotte Mattax Moersch — Sarabande la Majestueuse, 1er Ordre'),
  ('dSx_MOtch08', 'Charlotte Mattax Moersch — Allemande L\'Auguste, 1er Ordre'),
  ('NHcaIpFnuKs', 'nagiseuk — Allemande l\'Auguste, 1er Ordre'),
  ('Ky_NVsDztPI', 'Magdalena Baczewska — Ordre 1er in g minor (GRAND PIANO SERIES)'),
]

for vid, label in candidates:
  try:
    url = f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
      o = json.loads(r.read().decode('utf-8'))
    print(f'OK  {vid}  channel={o.get("author_name","")!r}')
    print(f'    title={o.get("title","")!r}')
  except HTTPError as e:
    print(f'HTTP {e.code} {vid} {label}')
  except Exception as e:
    print(f'ERR {e} {vid}')
