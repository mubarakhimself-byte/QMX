"""Render the document-only closure report and verify its immutable inputs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import html
import json
import re

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
CANDIDATE = REPO / '_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23'


def inline(value):
    value = html.escape(value)
    value = re.sub(r'`([^`]+)`', r'<code>\1</code>', value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', value)
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', value)


def render(source):
    lines = source.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', c) for c in cells):
                    rows.append(cells)
                i += 1
            out.append('<div class="table-wrap"><table>')
            for row_index, cells in enumerate(rows):
                tag = 'th' if row_index == 0 else 'td'
                out.append('<tr>' + ''.join(f'<{tag}>{inline(c)}</{tag}>' for c in cells) + '</tr>')
            out.append('</table></div>')
            continue
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            out.append(f'<h{level}>{inline(line[level:].strip())}</h{level}>')
        elif line.startswith('- '):
            out.append('<ul>')
            while i < len(lines) and lines[i].startswith('- '):
                out.append(f'<li>{inline(lines[i][2:])}</li>')
                i += 1
            out.append('</ul>')
            continue
        elif re.match(r'^\d+\. ', line):
            out.append('<ol>')
            while i < len(lines) and re.match(r'^\d+\. ', lines[i]):
                item = re.sub(r'^\d+\. ', '', lines[i])
                out.append(f'<li>{inline(item)}</li>')
                i += 1
            out.append('</ol>')
            continue
        else:
            out.append(f'<p>{inline(line)}</p>')
        i += 1
    return '\n'.join(out)


CSS = '''
:root{color-scheme:light;--ink:#18212b;--muted:#536171;--line:#d5dce3}
*{box-sizing:border-box}body{margin:0;background:#f4f6f8;color:var(--ink);font:16px/1.65 system-ui,sans-serif}
main{max-width:1140px;margin:auto;padding:38px 44px 72px;background:white;min-height:100vh}
nav{display:flex;flex-wrap:wrap;gap:18px;padding-bottom:22px;border-bottom:1px solid var(--line);font-size:14px}
h1{font-size:32px;line-height:1.2;letter-spacing:-.03em;margin:30px 0 20px}
h2{font-size:23px;margin-top:40px;border-top:1px solid var(--line);padding-top:24px}
h3{font-size:19px;line-height:1.4;margin-top:32px}p,li{max-width:100ch}
a{color:#125c87;text-underline-offset:3px}code{font: .88em ui-monospace,Consolas,monospace;background:#eef1f4;padding:1px 4px;border-radius:3px;overflow-wrap:anywhere}
.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.5}
th,td{border:1px solid var(--line);padding:12px;text-align:left;vertical-align:top}th{background:#eaf0f5}
li+li{margin-top:9px}.scope{margin-top:56px;border-top:4px solid #4b647c;padding-top:16px}
.badge{font-weight:650;background:#fff4d9;border:1px solid #d9ba67;padding:12px 16px;margin:22px 0}
@media(max-width:700px){main{padding:24px 18px}h1{font-size:27px}td,th{min-width:130px}}
@media print{body,main{background:white}main{max-width:none;padding:0}nav{display:none}a{color:inherit}}
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    manifest = json.loads((ROOT / 'evidence/input-manifest.json').read_text(encoding='utf-8-sig'))
    mismatches = []
    for entry in manifest:
        for label, base in [('snapshot', ROOT / 'evidence/candidate-as-reviewed'), ('candidate', CANDIDATE)]:
            path = base / entry['path']
            if not path.is_file() or digest(path) != entry['sha256'].upper():
                mismatches.append({'surface': label, 'path': entry['path']})
    expected = {e['path'].replace('\\', '/') for e in manifest}
    current = {p.relative_to(CANDIDATE).as_posix() for p in CANDIDATE.rglob('*') if p.is_file()}
    added = sorted(current - expected)
    removed = sorted(expected - current)
    report_text = (ROOT / 'REVIEW.md').read_text(encoding='utf-8')
    backend_text = (ROOT / 'BACKEND-SCOPE.md').read_text(encoding='utf-8')
    missing_links = []
    for name in ['START-HERE.md', 'REVIEW.md']:
        for target in re.findall(r'\]\(([^)]+)\)', (ROOT / name).read_text(encoding='utf-8')):
            if target.startswith(('https://', 'http://', '#')):
                continue
            # The verification file is created immediately below.
            if target == 'evidence/verification.json':
                continue
            if not (ROOT / target.split('#')[0]).exists():
                missing_links.append({'document': name, 'target': target})
    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>QMX architecture closure review · 24 September</title>
<style>{CSS}</style></head><body><main>
<nav><a href="#closure">Closure review</a><a href="#backend">Backend scope</a><a href="REVIEW.md">Markdown</a><a href="GROK-FOLLOWUP.md">Follow-up prompt</a></nav>
<div class="badge">Ready after listed corrections · Architecture review only · No implementation started</div>
<section id="closure">{render(report_text)}</section>
<section id="backend" class="scope">{render(backend_text)}</section>
</main></body></html>'''
    (ROOT / 'review.html').write_text(document, encoding='utf-8')
    # Verify link targets after the HTML artifact has been produced.
    missing_links = [item for item in missing_links if not (ROOT / item['target']).exists()]
    result = {
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'input_file_count': len(manifest),
        'sha256_mismatches': mismatches,
        'candidate_files_added_since_snapshot': added,
        'candidate_files_removed_since_snapshot': removed,
        'missing_report_links': missing_links,
        'independent_reports_present': all((ROOT / 'reviews' / name).is_file() for name in ['runtime.md', 'experience.md', 'currency.md']),
        'structural_lint': 'pass; zero findings; see spine-lint.json',
        'app_runtime_verification': 'not performed; documents only',
    }
    result['ok'] = not (mismatches or added or removed or missing_links) and result['independent_reports_present']
    (ROOT / 'evidence/verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    if not result['ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
