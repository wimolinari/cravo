"""Scrape YouTube search HTML for video IDs + metadata."""
import sys, urllib.request, ssl, re, json
from urllib.parse import quote

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def search(query):
  url = f'https://www.youtube.com/results?search_query={quote(query)}'
  req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language':'en;q=0.9'})
  with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
    body = r.read(2_000_000).decode('utf-8', errors='replace')
  # Extract videoRenderer entries from ytInitialData
  m = re.search(r'var ytInitialData = (\{.*?\});', body)
  if not m:
    return []
  try:
    data = json.loads(m.group(1))
  except Exception:
    return []
  out = []
  def walk(o):
    if isinstance(o, dict):
      vr = o.get('videoRenderer')
      if vr and isinstance(vr, dict):
        vid = vr.get('videoId')
        title = ''
        t = vr.get('title', {})
        if 'runs' in t and t['runs']:
          title = t['runs'][0].get('text','')
        elif 'simpleText' in t:
          title = t['simpleText']
        owner = ''
        o2 = vr.get('ownerText', {})
        if 'runs' in o2 and o2['runs']:
          owner = o2['runs'][0].get('text','')
        length = ''
        lt = vr.get('lengthText', {})
        if 'simpleText' in lt:
          length = lt['simpleText']
        if vid:
          out.append({'id': vid, 'title': title, 'channel': owner, 'length': length})
      for v in o.values():
        walk(v)
    elif isinstance(o, list):
      for v in o:
        walk(v)
  walk(data)
  return out

queries = [
  'couperin premier livre harpsichord recital',
  'couperin les silvains harpsichord performance live',
  'couperin premier ordre clavecin live',
  'couperin first book harpsichord live concert',
]

for q in queries:
  print(f'\n=== Query: {q} ===')
  try:
    res = search(q)
    print(f'  Found {len(res)} videos. Showing first 12:')
    seen = set()
    count = 0
    for r in res:
      if r['id'] in seen or count >= 12: continue
      seen.add(r['id'])
      ch = r['channel']
      # Skip Topic channels and obvious aggregators
      if ch.endswith('- Topic') or ch in ('Brilliant Classics','Warner Classics','Classical Music Archive'):
        continue
      count += 1
      print(f'    [{r["id"]}] {ch:<30} | {r["length"]:<7} | {r["title"][:100]}')
  except Exception as e:
    print(f'  ERR {e}')
