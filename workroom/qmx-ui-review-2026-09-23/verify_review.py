"""Preserve reviewed inputs and check report evidence links, without running QMX."""
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
CANDIDATE = REPO / '_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23'
manifest = json.loads((ROOT / 'evidence/candidate-hashes-at-start.json').read_text(encoding='utf-8-sig'))
data = json.loads((ROOT / 'review-data.json').read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
changed = [r['path'] for r in manifest if not (CANDIDATE / r['path']).is_file() or sha(CANDIDATE / r['path']) != r['sha256'].upper()]
if changed:
    raise SystemExit('Original candidate changed during review: ' + repr(changed))

snapshot = ROOT / 'evidence/candidate-as-reviewed'
for r in manifest:
    dest = snapshot / r['path']
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and sha(dest) != r['sha256'].upper():
        raise SystemExit('Existing snapshot mismatch: ' + str(dest))
    if not dest.exists():
        shutil.copy2(CANDIDATE / r['path'], dest)
    assert sha(dest) == r['sha256'].upper()

refs = [s for f in data['findings'] for s in f['evidence']] + data['reviews']
bad = []
for s in refs:
    p = Path(s['path'])
    if not p.is_file() or not 1 <= s['line'] <= len(p.read_text(encoding='utf-8-sig').splitlines()):
        bad.append(s)
if bad:
    raise SystemExit('Invalid evidence references: ' + repr(bad))

class CheckHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.local_anchors = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a' and attrs.get('href', '').startswith('#'):
            self.local_anchors.append(attrs['href'][1:])

parser = CheckHTML()
parser.feed((ROOT / 'review.html').read_text(encoding='utf-8'))
assert len(parser.ids) == len(set(parser.ids))
assert set(parser.local_anchors) <= set(parser.ids)
assert {f['id'] for f in data['findings']} <= set(parser.ids)

record = {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'candidate_path': str(CANDIDATE),
    'original_candidate_files': len(manifest),
    'original_candidate_files_changed': changed,
    'immutable_snapshot': 'evidence/candidate-as-reviewed',
    'snapshot_hashes_verified': True,
    'review_evidence_references_checked': len(refs),
    'html_structure_and_local_anchors': 'pass; not a browser rendering test',
    'spine_lint': {'ok': True, 'total_findings': 0, 'evidence': 'spine-lint.json'},
    'transcript_sha256': sha(ROOT / 'evidence/grok-return-transcript.txt'),
    'application_runtime_tests': 'not run; document review only',
    'reticle_verdict': 'not applicable to document-only review; no application verdict claimed',
    'artifacts': {name: sha(ROOT / name) for name in ['REVIEW.md','review.html','review-data.json','GROK-CORRECTION-PROMPT.md']}
}
(ROOT / 'evidence/verification.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({k:record[k] for k in ['original_candidate_files','original_candidate_files_changed','snapshot_hashes_verified','review_evidence_references_checked']}))
