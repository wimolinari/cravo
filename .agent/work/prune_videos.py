"""Remove static-image / unavailable videos from data-videos= JSON across all
HTML files (PT + en/es/fr). Reports any picker that ends up with 0 videos."""
import sys, json, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

classification = json.loads(
  Path('C:/Outros/Cravo/.agent/work/video_classification.json').read_text(encoding='utf-8')
)

# IDs to remove
REMOVE = {
  vid for vid, e in classification.items()
  if e.get('classification') in ('STATIC', 'STATIC_LIKELY', 'UNAVAILABLE')
}
KEEP_HUMAN = {
  vid for vid, e in classification.items()
  if e.get('classification') in ('HUMAN_LIKELY', 'PROBABLY_HUMAN')
}
print(f'IDs to remove: {len(REMOVE)}')
print(f'IDs to keep:   {len(KEEP_HUMAN)}')

# Iterate all HTML files
root = Path('C:/Outros/Cravo/site')
attr_re = re.compile(r"data-videos='(\[.*?\])'", re.DOTALL)

empty_pickers = []  # (file, picker_intro_or_position)
changes_per_file = {}

for p in root.rglob('*.html'):
  text = p.read_text(encoding='utf-8')
  orig = text
  def repl(m):
    raw = m.group(1)
    try:
      arr = json.loads(raw)
    except Exception:
      return m.group(0)
    new_arr = [v for v in arr if v.get('id') not in REMOVE]
    removed = [v for v in arr if v.get('id') in REMOVE]
    if not removed:
      return m.group(0)
    # Track empty picker
    if not new_arr:
      empty_pickers.append((str(p.relative_to(root)).replace('\\','/'), [v.get('id') for v in removed]))
    # Re-serialize without spaces, preserve HTML attribute compatibility
    new_json = json.dumps(new_arr, ensure_ascii=False)
    return f"data-videos='{new_json}'"

  new_text = attr_re.sub(repl, text)
  if new_text != orig:
    p.write_text(new_text, encoding='utf-8')
    rel = str(p.relative_to(root)).replace('\\','/')
    changes_per_file[rel] = True

print(f'\nChanged {len(changes_per_file)} files.')
print(f'Empty pickers (0 videos after pruning): {len(empty_pickers)}')
for f, removed_ids in empty_pickers:
  print(f'  {f}: had only {removed_ids}')

# Dump cleanup report
Path('C:/Outros/Cravo/.agent/work/prune_report.json').write_text(
  json.dumps({
    'removed_ids': sorted(REMOVE),
    'kept_ids': sorted(KEEP_HUMAN),
    'changed_files': sorted(changes_per_file),
    'empty_pickers': empty_pickers,
  }, ensure_ascii=False, indent=2),
  encoding='utf-8',
)
