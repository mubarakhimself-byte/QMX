"""Render the read-only architecture review in Markdown and standalone HTML."""
from pathlib import Path
import json
import html

ROOT = Path(__file__).resolve().parent
d = json.loads((ROOT / "review-data.json").read_text(encoding="utf-8"))

def mdlink(s):
    return f'[{s["label"]}:{s["line"]}](<{s["path"]}:{s["line"]}>)'

def hlink(s):
    uri = Path(s["path"]).as_uri() + f'#L{s["line"]}'
    return f'<a href="{html.escape(uri, quote=True)}">{html.escape(s["label"])}:{s["line"]}</a>'

lines = [f'# {d["title"]}', '', f'**{d["verdict"]}**', '', d['summary'], '', d['scope'], '',
         'Review date: ' + d['date'] + '. Seven high-priority corrections and two medium corrections. Severity describes architecture readiness, not demonstrated production incidents.', '',
         '## Keep these foundations', '']
lines += ['- ' + s for s in d['strengths']]
lines += ['', '## Required corrections', '']
for f in d['findings']:
    lines += [f'### {f["id"]} · {f["severity"]} — {f["title"]}', '', f['finding'], '',
              '**Consequence:** ' + f['consequence'], '',
              '**Correction:** ' + f['correction'], '',
              '**Closure evidence:** ' + f['closure'], '',
              '**Disposition:** ' + f['disposition'], '',
              '**Evidence:** ' + '; '.join(mdlink(s) for s in f['evidence']) + '.', '']
lines += ['## Whole-session coverage rubric', '',
          'Pass means the architecture preserves the requirement; it is not evidence that software executes correctly. Partial areas require concrete contracts or explicit supported/deferred boundaries, not a requirement to ship every feature in the first slice.', '',
          '| Area | Assessment | Meaning |', '| --- | --- | --- |']
lines += ['| ' + ' | '.join(row) + ' |' for row in d['rubric']]
for key, title in [('deferred','Safe deferrals and limits'),('adjudication','Reviewer adjudication'),('method','Method and evidence limits')]:
    lines += ['', '## ' + title, ''] + ['- ' + s for s in d[key]]
lines += ['', '## Next step', '', d['next'], '',
          '[Ready-to-send correction prompt](<C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-review-2026-09-23/GROK-CORRECTION-PROMPT.md>)', '',
          '## Supporting reviews', ''] + ['- ' + mdlink(s) for s in d['reviews']]
lines += ['', '## Primary technical references', '',
          'Checked by the independent currency reviewer on 2026-09-23; that report records version-specific evidence and limits.', '']
lines += [f'- [{label}]({url})' for label,url in d['primarySources']]
lines += ['', '[Integrity and lint record](<C:/Users/Mubarak/Desktop/QMX/workroom/qmx-ui-review-2026-09-23/evidence/verification.json>)', '']
(ROOT / 'REVIEW.md').write_text('\n'.join(lines), encoding='utf-8')

esc = html.escape
def bullets(items):
    return '<ul>' + ''.join('<li>' + esc(s) + '</li>' for s in items) + '</ul>'

parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>QMX architecture return review</title>',
         '''<style>
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f5f5f3;color:#202328;font:16px/1.65 system-ui,-apple-system,Segoe UI,sans-serif}main{max-width:1120px;margin:auto;padding:48px 32px 96px}h1{font-size:38px;line-height:1.15;letter-spacing:-.8px;margin:12px 0 24px}h2{font-size:25px;margin-top:52px}h3{font-size:21px;line-height:1.35;margin:0 0 18px}p{margin:12px 0}a{color:#245ca6;text-underline-offset:3px}a:focus-visible{outline:3px solid #245ca6;outline-offset:4px}.eyebrow,.label{font-size:13px;font-weight:650;letter-spacing:.04em;text-transform:uppercase;color:#626873}.verdict{border-left:5px solid #a74b27;background:#fff3e8;padding:20px 24px;font-size:20px;font-weight:650}.meta{color:#616976;font-size:14px}.card{background:white;padding:28px;margin:24px 0;border:1px solid #d7dce0;border-radius:8px;scroll-margin-top:24px}.high{color:#a64028}.medium{color:#795a15}.evidence{font-size:14px;border-top:1px solid #e4e7e9;padding-top:14px;overflow-wrap:anywhere}nav{display:flex;flex-wrap:wrap;gap:8px 18px;padding:18px 0}li{margin:9px 0}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;border-bottom:1px solid #d5dadd;padding:12px;vertical-align:top}th{background:#e9ecee}td:first-child{min-width:160px;font-weight:600}td:nth-child(2){min-width:210px}footer{margin-top:48px;padding-top:20px;border-top:1px solid #d5dadd;color:#616976} @media(max-width:650px){main{padding:24px 18px 56px}h1{font-size:30px}.card{padding:20px}} @media print{body{background:white}main{padding:0;max-width:none}nav{display:none}.card{break-inside:avoid}a{color:inherit}.table-wrap{overflow:visible}}
</style>''', '<main>', '<div class="eyebrow">Independent architecture review · 23 September 2026</div>',
         '<h1>Keep the foundation.<br>Close the implementation contracts.</h1>',
         '<div class="verdict">' + esc(d['verdict']) + '</div>',
         '<p>' + esc(d['summary']) + '</p><p class="meta">' + esc(d['scope']) + '</p>',
         '<nav aria-label="Report sections"><a href="#findings">Required corrections</a><a href="#rubric">Whole-session rubric</a><a href="#limits">Evidence limits</a><a href="#next">Correction prompt</a></nav>',
         '<h2>What is worth keeping</h2>', bullets(d['strengths']),
         '<h2 id="findings">Required corrections</h2><p class="meta">Seven high-priority corrections and two medium corrections. No production incident or successful runtime test is asserted.</p>']
for f in d['findings']:
    parts += [f'<article class="card" id="{f["id"]}">', f'<div class="label {f["severity"].lower()}">{f["id"]} · {f["severity"]}</div>', '<h3>'+esc(f['title'])+'</h3>', '<p>'+esc(f['finding'])+'</p>']
    for key,label in [('consequence','Why it matters'),('correction','Required correction'),('closure','Closure evidence'),('disposition','Disposition')]:
        parts.append('<p><strong>'+label+':</strong> '+esc(f[key])+'</p>')
    parts += ['<p class="evidence"><strong>Evidence:</strong> ' + ' · '.join(hlink(s) for s in f['evidence']) + '</p></article>']
parts += ['<h2 id="rubric">Whole-session coverage rubric</h2><p>Pass means the architecture preserves the requirement. It does not mean the application has been built or tested.</p>', '<div class="table-wrap"><table><thead><tr><th>Area</th><th>Assessment</th><th>Meaning</th></tr></thead><tbody>']
parts += ['<tr>'+''.join('<td>'+esc(cell)+'</td>' for cell in row)+'</tr>' for row in d['rubric']]
parts += ['</tbody></table></div>']
for key,title,anchor in [('deferred','Safe deferrals','deferred'),('adjudication','Reviewer adjudication','adjudication'),('method','Method and evidence limits','limits')]:
    parts += [f'<h2 id="{anchor}">'+title+'</h2>',bullets(d[key])]
parts += ['<h2 id="next">Next step</h2><p>'+esc(d['next'])+'</p>', '<p><a href="GROK-CORRECTION-PROMPT.md">Open the ready-to-send correction prompt</a> · <a href="REVIEW.md">Markdown report</a> · <a href="evidence/verification.json">Integrity record</a></p>', '<h2>Independent reviews</h2><ul>']
parts += ['<li>'+hlink(s)+'</li>' for s in d['reviews']]
parts += ['</ul><h2>Primary technical references</h2><ul>']
parts += [f'<li><a href="{esc(url,quote=True)}">{esc(label)}</a></li>' for label,url in d['primarySources']]
parts += ['</ul><footer>Document review only. Original candidate preserved; review artifacts added separately. Generated from review-data.json.</footer></main></html>']
(ROOT / 'review.html').write_text('\n'.join(parts), encoding='utf-8')
print('Rendered REVIEW.md and review.html')
