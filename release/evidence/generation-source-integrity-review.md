# Generation source and identity admission diagnosis

Status: CHANGES REQUIRED on active source inspected 2026-10-01. Public API controls, no product edits or Git mutations.

`qml/src/qml/generation/__init__.py:507` stringifies both source paths and contents. Public `author_new_structure(logic_source={'factory.py': b'def factory(): return 1\n'})` succeeds but its manifest differs from `mint_logic_identity('research-bot', '1.0.0', same_source)`: source bytes become their Python repr instead of their actual UTF-8 content. An integer path 7 becomes filename '7' and is admitted although the canonical source-manifest mint refuses the original path. Genuine string path/text content yields exactly equal authored and canonical LogicIdentity, confirming a precise coercion defect.

Other actual public false admissions:

- `classify_parameter_search(bot_fp1=Fingerprint('bad'), trial_bot_fp1s=[Fingerprint('bad')])` returns SEARCH. Generation `_coerce_fingerprint` trusts the nominal wrapper without validating its value.
- `author_new_structure(logic_reference=LogicIdentity('', '', Fingerprint('bad')))` returns an authored structure with invalid distribution/version/manifest.
- `author_new_structure(confluence=Confluence(()))` accepts empty CT34 confluence. Canonical Confluence.try_create also bypasses validation when passed a nominal Confluence directly.

Bounded repair: pass original source mapping through the existing canonical source-manifest admission, preserving supported bytes semantics and refusing non-string paths rather than converting them. Validate wrapped fingerprint values via Fingerprint.try_create in generation and logic reference admission. Reconstruct typed LogicIdentity and typed Confluence/legs through their existing semantic validators, avoiding current nominal-instance early-return shortcuts. Preserve genuine authored text/byte source identity, valid parameter-search equality, nonempty validated confluence, and declared ordering behavior. Do not invent new source projections or generator grammar.

Existing generation ownership/gaps suites remain green: `.venv/bin/python -m pytest -q -p no:cacheprovider qml/tests/test_generation_ownership.py qml/tests/test_generation_gaps_unfilled.py` — **27 passed**, despite these independent public defects. No source fixes, staging, commits, or full generation acceptance claim.

## e8f2a03e corrective review

Candidate `e8f2a03e6a6eaa6d0f8a39f1aef482d3c27dc74b`: original byte source now exactly matches canonical mint identity; integer path, malformed nominal Fingerprint search, malformed LogicIdentity and direct empty nominal Confluence each typed-refuse. Existing generation/confluence suites: **53 passed**.

CHANGES REQUIRED remains for an actual nested typed bypass: `author_new_structure(confluence_legs=[{'role': 'level', 'confluence_ref': Confluence(())}])` succeeds and cites a fingerprint of the invalid empty child. `_coerce_child_ref` still fingerprints a typed Confluence before its semantic validation. Revalidate that child through canonical Confluence admission before deriving its reference. Exact public reproduction sent numeric/root. No product edits or commits.

## 6ae34954 nested-child corrective retest

Candidate `6ae3495434a81de5200b0c6c0b9dbeec4b47fab4` atop e8f2a03e: **bounded PASS**. `_coerce_child_ref` now validates nominal child Confluence through Confluence.try_create before deriving its fingerprint. Original nested empty-child admission and malformed bool format-version child both typed-refuse.

Independent `/tmp/review_generation_final.py` confirms original invalid path/fingerprint/logic/direct-empty-child controls remain refused; genuine text and UTF-8 byte sources produce exactly the canonical mint LogicIdentity; a genuine nested authored child preserves its exact canonical child fingerprint. Typed ProducerBinding reconstructed from a valid ProducerTemplate preserves the f2fdd1e9 nested arithmetic dict/list snapshot: mutation of original reference configuration does not change its admitted binding fingerprint. Existing confluence ordering/identity controls remain green.

Reviewer combined generation ownership/gaps, confluence, footprint suites: **82 passed**. This approves the bounded generation source/nominal identity correction, not external source execution, install, or full QMA worker behavior. Evidence-only edits, no staging or commits.
