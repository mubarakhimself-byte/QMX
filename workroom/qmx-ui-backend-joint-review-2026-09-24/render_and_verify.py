"""Render the joint document review and verify its two immutable input sets."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import re

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
BASE = REPO / '_bmad-output/planning-artifacts/architecture'
CANDIDATES = {
    'backend': BASE / 'architecture-QMX-UI-BACKEND-2026-09-24',
    'ui': BASE / 'architecture-QMX-UI-2026-09-23',
}
helper = ROOT.parent / 'qmx-ui-closure-review-2026-09-24/render_and_verify.py'
spec = importlib.util.spec_from_file_location('review_helpers', helper)
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

report = (ROOT / 'REVIEW.md').read_text(encoding='utf-8')
prompt = (ROOT / 'GROK-FOLLOWUP.md').read_text(encoding='utf-8')
document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QMX joint UI and backend architecture review</title><style>{helpers.CSS}</style>
</head><body><main><nav><a href="#review">Review</a><a href="#followup">Grok follow-up</a>
<a href="REVIEW.md">Markdown</a><a href="evidence/verification.json">Input verification</a></nav>
<section id="review">{helpers.render(report)}</section>
<section id="followup" class="scope">{helpers.render(prompt)}</section>
</main></body></html>'''
(ROOT / 'review.html').write_text(document, encoding='utf-8')

manifest = json.loads((ROOT / 'evidence/input-manifest.json').read_text(encoding='utf-8-sig'))
mismatches = []
changes = {}
for source, candidate in CANDIDATES.items():
    entries = [e for e in manifest if e['source'] == source]
    for e in entries:
        for surface, base in [('snapshot', ROOT / 'evidence' / f'{source}-as-reviewed'), ('candidate', candidate)]:
            p = base / e['path']
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest().upper() != e['sha256'].upper():
                mismatches.append({'source': source, 'surface': surface, 'path': e['path']})
    expected = {e['path'].replace('\\', '/') for e in entries}
    current = {p.relative_to(candidate).as_posix() for p in candidate.rglob('*') if p.is_file()}
    changes[source] = {'added': sorted(current - expected), 'removed': sorted(expected - current)}

missing_links = []
for name in ['START-HERE.md', 'REVIEW.md', 'GROK-FOLLOWUP.md']:
    for target in re.findall(r'\]\(([^)]+)\)', (ROOT / name).read_text(encoding='utf-8')):
        if target.startswith(('http://', 'https://', '#')) or target == 'evidence/verification.json':
            continue
        path = target.split('#')[0]
        if not (ROOT / path).exists():
            missing_links.append({'document': name, 'target': target})
reviewers = ['admission.md', 'state-data.md', 'authoring-currency.md']
lint = {s: json.loads((ROOT / 'evidence' / f'{s}-lint.json').read_text(encoding='utf-8-sig')) for s in CANDIDATES}
result = {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'input_file_count': len(manifest),
    'sha256_mismatches': mismatches,
    'candidate_file_changes_since_snapshot': changes,
    'missing_report_links': missing_links,
    'independent_reports_present': all((ROOT / 'reviews' / p).is_file() for p in reviewers),
    'structural_lints': lint,
    'application_runtime_verified': False,
    'scope': 'Architecture document review only; candidate inputs not edited by Codex',
}
result['ok'] = not mismatches and not missing_links and not any(v['added'] or v['removed'] for v in changes.values()) and result['independent_reports_present'] and all(v.get('ok') is True for v in lint.values())
(ROOT / 'evidence/verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
if not result['ok']:
    raise SystemExit(1)
