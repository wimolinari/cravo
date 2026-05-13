"""Deeper classification pass: re-fetch UNKNOWN videos and re-scan descriptions
of suspect aggregator/album channels for static-image signals."""
import sys, json, urllib.request, ssl, re, time
from pathlib import Path
from urllib.error import HTTPError

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'

def fetch(url, n=400000):
  req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language':'en;q=0.9'})
  with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
    return r.read(n).decode('utf-8', errors='replace')

current = json.loads(Path('C:/Outros/Cravo/.agent/work/video_classification.json').read_text(encoding='utf-8'))

# Channels strongly suggesting static image + audio (commercial albums, vinyl rips, label aggregators)
STATIC_LIKELY_CHANNELS = {
  'Brilliant Classics', 'Warner Classics', 'Classical Music Archive',
  'Harpsichord Vinyl Gallery', 'AeCouperin',
  'Giovanni Battista Lulli (Baroquemusica)',
  'incontrario motu', 'calefonxcalectric', 'jsba1987',
  'harpsichordVal', 'Bachology',
  # tuttalamusica appears to be auto-uploaded album scans
  'tuttalamusica',
  'Charles Berofsky',  # uploads commercial Berofsky recording
  # 'Pierre Charron' uploads commercial Rousset recording
  'Pierre Charron',
  # 'Ria Brezova' uploads commercial Vartolo recording
  'Ria Brezova',
  # 'Bachology' aggregator
  # 'Muzyka w Raju' aggregator - Polish music channel that re-uploads
  'Muzyka w Raju',
  'A Gentleman of Verona',   # aggregator
  'My Life With Early Music',  # aggregator/curator
  'unagondolaunremo',  # personal upload of commercial recordings
  'queswerte', 'aniMIDIfy', 'cantarlontano',
  'harpsicor',  # uploader, not performer
  # DrsP1 - aggregator of Skip Sempé
  'DrsP1',
  # Ketil Haugsand could be performer's own, but the video is named like a track listing
}

# Channels that are VERIFIED PERFORMERS' OWN (real video performances)
LIKELY_HUMAN_CHANNELS = {
  'Skip Sempé - Capriccio Stravagante - Paris-Versailles',
  'Skip Sempé - Capriccio Stravagante - Paradizo',
  'Charlotte Mattax Moersch',
  'Apotheosis / Korneel Bernolet',
  'Smarano Organ Academy',  # live festival recordings
  'Het Concertgebouw',  # venue
  'France Musique concerts',
  'Les Talens Lyriques - chaîne officielle',
  'Time for harpsichord',  # educational, demos
  'Robert Hill plays early keyboard music',
  'Mario Marques Trilha', 'Markus Märkl', 'Paul Cienniwa',
  'Elaine Comparone', 'Aya Hamada harpsichord', 'Yago Mahúgo',
  'Andreas Zappe', 'Luke Arnason', 'Denis Bonenfant claveciniste',
  'Zeljko Drion-Manic', 'Magdalena Stern-Baczewska',
  'Ian Pritchard', 'Ryan Chan', 'Richard Auber', 'Richard Siegel',
  'Francesco Fornasaro | Harpsichordist',
  'Early Music in a Different Way ;)',
  'MagisterCremonensis',  # actual organist Paolo Bottini
  'Andrea Scalia - Early Music',  # plays himself
  'Rique Borges',  # plays
  'Leslie Pearl',
  'Ketil Haugsand',  # performer
}

# Re-fetch UNKNOWN to investigate
unknown_ids = [vid for vid, e in current.items() if e.get('classification') == 'UNKNOWN']
print(f'\n=== Re-fetching {len(unknown_ids)} UNKNOWN videos ===')
for vid in unknown_ids:
  oembed_url = f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json'
  watch_url = f'https://www.youtube.com/watch?v={vid}'
  print(f'\n--- {vid} ---')
  try:
    o = json.loads(fetch(oembed_url, 16384))
    print(f'  oembed: {o.get("author_name","")!r} / {o.get("title","")!r}')
    current[vid]['title'] = o.get('title','')
    current[vid]['author'] = o.get('author_name','')
    current[vid]['classification'] = 'PROBABLY_HUMAN'
    current[vid]['reason'] = '(re-fetch) oembed ok'
  except HTTPError as e:
    print(f'  oembed HTTP {e.code}')
    if e.code == 401:
      current[vid]['classification'] = 'UNAVAILABLE'
      current[vid]['reason'] = 'oembed 401: video private/removed/age-restricted'
    elif e.code == 404:
      current[vid]['classification'] = 'UNAVAILABLE'
      current[vid]['reason'] = 'oembed 404: video not found'
  except Exception as e:
    print(f'  err: {e}')
  time.sleep(0.5)

# Apply channel-based re-classification
print(f'\n=== Re-classifying based on channel reputation ===')
reclassified = 0
for vid, entry in current.items():
  author = entry.get('author', '')
  if entry.get('classification') == 'STATIC':
    continue  # already confirmed
  if author in STATIC_LIKELY_CHANNELS:
    entry['classification'] = 'STATIC_LIKELY'
    entry['reason'] = f'Aggregator/album channel: {author}'
    reclassified += 1
  elif author in LIKELY_HUMAN_CHANNELS:
    entry['classification'] = 'HUMAN_LIKELY'
    entry['reason'] = f'Performer/venue channel: {author}'
print(f'  Reclassified {reclassified} suspect videos as STATIC_LIKELY')

Path('C:/Outros/Cravo/.agent/work/video_classification.json').write_text(
  json.dumps(current, ensure_ascii=False, indent=2), encoding='utf-8'
)

# Final summary
from collections import Counter
c = Counter(r.get('classification','?') for r in current.values())
print(f'\n=== FINAL CLASSIFICATION ===')
for k, v in c.most_common():
  print(f'  {k}: {v}')

# List ALL videos that need replacement (STATIC + STATIC_LIKELY)
print(f'\n=== NEEDS REPLACEMENT ===')
for vid, e in sorted(current.items()):
  if e.get('classification') in ('STATIC', 'STATIC_LIKELY', 'UNAVAILABLE'):
    print(f'  {vid} [{e["classification"]}] {e.get("author","")!r}')
    print(f'    {e.get("title","")[:100]}')
    print(f'    used in: {[u["page"] for u in e.get("usages",[])]}')
