"""The coordinator's check: every line of the brief rests on at least one kept claim, in that
claim's own section, and every HIGH claim appears in some line, so the coordinator can neither add
an unsourced line nor drop a strong one. Its inputs, the cut rules' result and the coordinator's
lines, are told apart by shape. Prints the verdict and each problem."""

import json
import sys

given = json.load(sys.stdin)["in"]
desk = next(v for v in given if "kept" in v)
brief = next(v for v in given if "lines" in v)
sections = {claim["id"]: claim["section"] for claim in desk["kept"]}
problems = []
for n, line in enumerate(brief["lines"], start=1):
    unknown = [c for c in line["claim_ids"] if c not in sections]
    if not line["claim_ids"] or unknown:
        problems.append(f"line {n} rests on no kept claim: {unknown or 'none named'}")
    elif line["section"] not in {sections[c] for c in line["claim_ids"]}:
        problems.append(f"line {n} is in {line['section']}, which none of its claims is")
used = {c for line in brief["lines"] for c in line["claim_ids"]}
dropped = sorted(c for c, s in sections.items() if s == "HIGH" and c not in used)
if dropped:
    problems.append(f"HIGH claims in no line: {', '.join(dropped)}")
verdict = "fail" if problems else "pass"
print(
    json.dumps(
        {"verdict": verdict, "feedback": {"problems": problems, "lines": len(brief["lines"])}}
    )
)
