"""Render this document review and verify the exact candidate input snapshot."""
from pathlib import Path
import importlib.util
import json
import hashlib
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
CANDIDATE = REPO / '_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23'
helper_path = ROOT.parent / 'qmx-ui-closure-review-2026-09-24/render_and_verify.py'
spec = importlib.util.spec_from_file_location('review_render_helpers', helper_path)
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

report = (ROOT / 'REVIEW.md').read_text(encoding='utf-8')
intake = (ROOT / 'BACKEND-INTAKE-SUPPLEMENT.md').read_text(encoding='utf-8')
document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>QMX second-amendment closure review</title>
<style>{helpers.CSS}</style></head><body><main>
<nav><a href="#review">Closure review</a><a href="#intake">Backend intake</a><a href="REVIEW.md">Markdown</a><a href="FRESH-BACKEND-PROMPT.md">Fresh-session prompt</a></nav>
<div class="badge">8 findings closed · 1 authentication correction · Next: fresh backend architecture</div>
<section id="review">{helpers.render(report)}</section>
<section id="intake" class="scope">{helpers.render(intake)}</section>
</main></body></html>'''
(ROOT / 'review.html').write_text(document, encoding='utf-8')

manifest = json.loads((ROOT / 'evidence/input-manifest.json').read_text(encoding='utf-8-sig'))
mismatches = []
for entry in manifest:
    for label, base in [('snapshot', ROOT / 'evidence/candidate-as-reviewed'), ('candidate', CANDIDATE)]:
        path = base / entry['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest().upper() != entry['sha256'].upper():
            mismatches.append({'surface': label, 'path': entry['path']})
expected = {entry['path'].replace('\\', '/') for entry in manifest}
current = {p.relative_to(CANDIDATE).as_posix() for p in CANDIDATE.rglob('*') if p.is_file()}
missing_links = []
for name in ['START-HERE.md', 'REVIEW.md', 'BACKEND-INTAKE-SUPPLEMENT.md']:
    for target in re.findall(r'\]\(([^)]+)\)', (ROOT / name).read_text(encoding='utf-8')):
        if target.startswith(('http://', 'https://', '#')) or target == 'evidence/verification.json':
            continue
        if not (ROOT / target.split('#')[0]).exists():
            missing_links.append({'document': name, 'target': target})
reviewers_present = all((ROOT / 'reviews' / name).is_file() for name in ['auth-chat.md', 'experience.md', 'cancel-currency.md'])
lint = json.loads((ROOT / 'evidence/spine-lint.json').read_text(encoding='utf-8-sig'))
result = {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'input_file_count': len(manifest),
    'sha256_mismatches': mismatches,
    'candidate_files_added_since_snapshot': sorted(current - expected),
    'candidate_files_removed_since_snapshot': sorted(expected - current),
    'missing_report_links': missing_links,
    'independent_reports_present': reviewers_present,
    'structural_lint': lint,
    'application_runtime_verified': False,
    'scope': 'Document-only closure review; no application or candidate changes',
}
result['ok'] = not (mismatches or current != expected or missing_links) and reviewers_present and lint.get('ok') is True
(ROOT / 'evidence/verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
if not result['ok']:
    raise SystemExit(1)
