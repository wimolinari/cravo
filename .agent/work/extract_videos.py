"""Extract unique YouTube video metadata from PT pages."""
import re, json, sys
from pathlib import Path

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

pt_files = [
  'tratados/sancta-maria.html', 'tratados/rameau.html',
  'tratados/frescobaldi.html', 'tratados/couperin.html',
  'temas/ritmo-tempo.html', 'temas/postura.html',
  'temas/ornamentos.html', 'temas/exercicios-baterias.html',
  'temas/dedilhados.html', 'temas/articulacao.html',
  'roteiro-estudo.html'
]
all_videos = {}
for rel in pt_files:
  p = Path('C:/Outros/Cravo/site') / rel
  text = p.read_text(encoding='utf-8', errors='replace')
  for m in re.finditer(r"data-videos='(\[.*?\])'", text, re.DOTALL):
    raw = m.group(1)
    try:
      arr = json.loads(raw)
    except Exception:
      continue
    for v in arr:
      vid = v.get('id')
      info = {'page': rel, 'performer': v.get('performer',''),
              'title': v.get('title',''), 'year': v.get('year',''),
              'duration': v.get('duration',''), 'note': v.get('note','')}
      all_videos.setdefault(vid, []).append(info)

out = Path('C:/Outros/Cravo/.agent/work/videos.json')
out.write_text(json.dumps(all_videos, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"# unique IDs: {len(all_videos)}")
