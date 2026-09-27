"""Rebuild this documentation/evidence packet; no app changes or Git mutation."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
SESSION = REPO / 'workroom/ui-reset-2026-09-23'
assert ROOT.name == 'qmx-ui-architecture-handoff-2026-09-23'
assert SESSION.is_dir()
assert ROOT.is_relative_to(REPO / 'workroom')
stamp = datetime.now(timezone.utc).isoformat()
provenance = {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    path = ROOT / path
    assert path.resolve().is_relative_to(ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8')


def write_json(path, value):
    write(path, json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def copy(source, relative, expected=None):
    source = Path(source)
    data = source.read_bytes()
    source_hash = digest(data)
    if expected:
        assert source_hash.lower() == expected.lower(), f'Source changed: {source}'
    destination = ROOT / relative
    assert destination.resolve().is_relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    provenance[Path(relative).as_posix()] = {
        'source': str(source), 'sourceSha256': source_hash,
        'copyMode': 'byte-identical',
    }


# The original board must still match the fully read afternoon snapshot.
board_provenance = json.loads((SESSION / 'live-research/board-current/provenance.json').read_text(encoding='utf-8-sig'))
assert digest(Path(board_provenance['source']).read_bytes()).lower() == board_provenance['sha256'].lower(), 'Storyboard changed; refresh evidence before packaging'
for row in json.loads((SESSION / 'evidence/provenance.json').read_text(encoding='utf-8-sig'))['records']:
    if row['role'] == 'image':
        assert digest(Path(row['source']).read_bytes()) == row['sha256'], f"Original image changed: {row['source']}"

# Preserve history in place so its relative image references remain meaningful.
allowed = {'.md', '.json', '.jsonl', '.png', '.jpg', '.jpeg', '.cjs', '.html', '.txt', '.py'}
for source in sorted(SESSION.rglob('*')):
    if source.is_file() and source.name != 'checkpoint-manifest.json':
        assert not source.is_symlink(), source
        assert source.suffix.lower() in allowed, f'Review unexpected evidence type: {source}'
        relative = Path('evidence/session') / source.relative_to(SESSION)
        copy(source, relative)
        if source.suffix.lower() == '.md' and source.name != 'session-visible-messages.md':
            text = (ROOT / relative).read_text(encoding='utf-8-sig')
            old = '../qmx-ui-architecture-handoff-2026-09-23/'
            if old in text:
                write(relative, text.replace(old, '../../'))
                provenance[relative.as_posix()]['copyMode'] = 'relative handoff links rebased; content otherwise retained'

video = next(row for row in json.loads((SESSION / 'evidence/provenance.json').read_text(encoding='utf-8-sig'))['records'] if row['role'] == 'video')
copy(video['source'], 'evidence/terminal-preview.mp4', video['sha256'])

# Canonical BDD set and supporting context, one copy per source.
bdd = json.loads((SESSION / 'handoff-working/bdd-source-list.json').read_text(encoding='utf-8-sig'))
bdd_rows = []
for row in bdd['canonicalSet']['featureFiles']:
    destination = 'evidence/bdd/behavior/' + row['name']
    copy(row['absolutePath'], destination, row['sha256'])
    bdd_rows.append({**row, 'packetPath': destination})
for row in bdd['supplementarySources']:
    destination = 'evidence/bdd/context/' + Path(row['absolutePath']).name
    assert not any(entry['packetPath'] == destination for entry in bdd_rows)
    copy(row['absolutePath'], destination, row['sha256'])
    bdd_rows.append({**row, 'packetPath': destination})
write_json('evidence/bdd/source-map.json', {'capturedAt': stamp, 'sources': bdd_rows})
bdd_links = '\n'.join(f"- [{Path(row['packetPath']).name}]({Path(row['packetPath']).relative_to('evidence/bdd').as_posix()}) — source `{row['repositoryRelativePath']}`" for row in bdd_rows)
write('evidence/bdd/README.md', '# Existing BDD sources\n\n85 scenario IDs in five canonical Stage-B feature files; one outline has four examples. These are draft behavioral specifications, not reported passing UI tests. See the [inventory](../session/handoff-working/bdd-inventory.md) for coverage, duplicate-copy provenance and runner limits. Original handoff commands in these files are historical evidence only.\n\n' + bdd_links + '\n\n[source-map.json](source-map.json) preserves original paths and hashes. Refresh the current repository scenario catalog during architecture reconciliation.\n')

# One narrow, newly observed document is context, not an audit of active work.
scenario = REPO / 'docs/scenarios/SCN-0024-optional-copilot-headless.md'
copy(scenario, 'evidence/current-context/SCN-0024-optional-copilot-headless.md')
write('evidence/current-context/README.md', '# Current repository context — narrow observation\n\nThe [SCN-0024 snapshot](SCN-0024-optional-copilot-headless.md) was read while locating existing journeys. It already describes headless packs, optional copilot panels, app-use change requests and closing a tab without cancelling work. Its own text distinguishes intended behavior from code at integration@34c148b. It was uncommitted when observed. Frontmatter marked ratified is a documentation status, not a new code/runtime verification by Codex.\n\nGrok should refresh this document and its cited 2026-09-23 architecture/ADR-0025 sources from the repository, then establish a consistent current baseline. The rest of that evolving architecture was not audited or frozen by this packet. No agents were interrupted.\n')


def git(*args):
    result = subprocess.run(['git', '-C', str(REPO), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


status = git('status', '--porcelain=v1', '--untracked-files=normal')
worktrees = git('worktree', 'list', '--porcelain')
relevant = []
for block in worktrees.split('\n\n'):
    record = dict(line.split(' ', 1) for line in block.splitlines() if ' ' in line)
    if record.get('worktree') in {str(REPO).replace('\\', '/'), str(REPO / '.worktrees/integration-inspect').replace('\\', '/'), str(REPO / '.worktrees/ui').replace('\\', '/')}:
        relevant.append(record)
write_json('repository-snapshot.json', {
    'capturedAt': stamp, 'repository': str(REPO), 'rootBranch': git('branch', '--show-current'),
    'rootCommit': git('rev-parse', 'HEAD'), 'rootHasUncommittedChanges': bool(status),
    'statusEntryCount': len(status.splitlines()), 'relevantWorktrees': relevant,
    'observedLatestArchitectureDirectory': '_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23',
    'observationLimit': 'Read-only metadata and a narrow scenario/BDD inventory, not full backend review or fresh runtime verification. Existing ui checkout is not selected as the new UI integration base. Refresh changing documents before using them.',
})

# Packet checks: primary navigation, source counts, canonical hashes and transcript boundaries.
primary = sorted(ROOT.glob('0[0-5]-*.md'))
assert len(primary) == 6
broken = []
files_to_check = primary + [ROOT / 'evidence/bdd/README.md', ROOT / 'evidence/current-context/README.md']
write_json('packet-manifest.json', {'status': 'being finalized'})
for source in files_to_check:
    for target in re.findall(r'\]\(([^)]+)\)', source.read_text(encoding='utf-8')):
        target = unquote(target.strip('<>')).split('#')[0]
        if not target or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', target):
            continue
        path = (source.parent / target).resolve()
        if not path.exists() or not path.is_relative_to(ROOT):
            broken.append({'document': source.relative_to(ROOT).as_posix(), 'target': target})
assert not broken, broken
assert len(list((ROOT / 'evidence/session/evidence/source-images').glob('*.png'))) == 10
assert len(list((ROOT / 'evidence/session/live-research/screenshots').glob('*.png'))) == 18
assert len(list((ROOT / 'evidence/session/experience-v03/references').glob('*.png'))) == 5
session_text = (ROOT / 'evidence/session/session-visible-messages.md').read_text(encoding='utf-8-sig')
assert len(re.findall(r'^## User — turn ', session_text, re.M)) == 15
feature_count = sum(len(re.findall(r'^\s*Scenario(?: Outline)?:', file.read_text(encoding='utf-8-sig'), re.M)) for file in (ROOT / 'evidence/bdd/behavior').glob('*.feature'))
assert feature_count == 85, feature_count

write_json('verification.json', {
    'checkedAt': stamp, 'primaryDocuments': 6, 'navigationDocumentsChecked': len(files_to_check),
    'brokenPrimaryRelativeLinks': broken, 'originalImages': 10, 'savedWebCaptures': 18,
    'userCodexScreenshots': 5, 'visibleSessionUserTurns': 15, 'bddScenarioDeclarations': feature_count,
    'sourceHashChecks': 'Original storyboard, ten original images, original short video and selected BDD sources matched the read snapshots',
    'scope': 'Documentation/package integrity only. No application tests, implementation, installed-product proof or Reticle verdict.',
})

records = []
for file in sorted(ROOT.rglob('*')):
    if file.is_file() and file.name != 'packet-manifest.json':
        relative = file.relative_to(ROOT).as_posix()
        data = file.read_bytes()
        records.append({'path': relative, 'bytes': len(data), 'sha256': digest(data), **provenance.get(relative, {})})
write_json('packet-manifest.json', {
    'packet': ROOT.name, 'builtAt': stamp, 'status': 'Architecture input; not approved implementation or runtime evidence',
    'authority': 'Read 02-CURRENT-DIRECTION.md before historical evidence',
    'transcriptBoundary': 'All 15 returned turns at capture; active turn partial; user-visible messages only; images separate',
    'externalRequirements': ['Current source repository for implementation claims', 'Installed complete skills if invoked'],
    'files': records,
})

archive = ROOT.parent / (ROOT.name + '.zip')
assert archive.resolve().parent == ROOT.parent
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as output:
    for file in sorted(ROOT.rglob('*')):
        if file.is_file():
            output.write(file, ROOT.name + '/' + file.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as check:
    assert check.testzip() is None
    assert len(check.namelist()) == len(records) + 1
    for record in records:
        assert digest(check.read(ROOT.name + '/' + record['path'])) == record['sha256'], record['path']
    assert check.read(ROOT.name + '/packet-manifest.json') == (ROOT / 'packet-manifest.json').read_bytes()
archive_hash = digest(archive.read_bytes())
archive.with_suffix('.zip.sha256').write_text(archive_hash + '  ' + archive.name + '\n', encoding='utf-8')
print(json.dumps({'archive': str(archive), 'files': len(records) + 1, 'bytes': archive.stat().st_size, 'sha256': archive_hash, 'allZipHashesMatch': True, 'brokenPrimaryLinks': len(broken)}))
