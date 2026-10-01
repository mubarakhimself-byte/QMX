# Generation source and identity admission diagnosis

Status: CHANGES REQUIRED on active source inspected 2026-10-01. Public API controls, no product edits or Git mutations.

`qml/src/qml/generation/__init__.py:507` stringifies both source paths and contents. Public `author_new_structure(logic_source={'factory.py': b'def factory(): return 1\n'})` succeeds but its manifest differs from `mint_logic_identity('research-bot', '1.0.0', same_source)`: source bytes become their Python repr instead of their actual UTF-8 content. An integer path 7 becomes filename '7' and is admitted although the canonical source-manifest mint refuses the original path. Genuine string path/text content yields exactly equal authored and canonical LogicIdentity, confirming a precise coercion defect.

Other actual public false admissions:

- `classify_parameter_search(bot_fp1=Fingerprint('bad'), trial_bot_fp1s=[Fingerprint('bad')])` returns SEARCH. Generation `_coerce_fingerprint` trusts the nominal wrapper without validating its value.
- `author_new_structure(logic_reference=LogicIdentity('', '', Fingerprint('bad')))` returns an authored structure with invalid distribution/version/manifest.
- `author_new_structure(confluence=Confluence(()))` accepts empty CT34 confluence. Canonical Confluence.try_create also bypasses validation when passed a nominal Confluence directly.

Bounded repair: pass original source mapping through the existing canonical source-manifest admission, preserving supported bytes semantics and refusing non-string paths rather than converting them. Validate wrapped fingerprint values via Fingerprint.try_create in generation and logic reference admission. Reconstruct typed LogicIdentity and typed Confluence/legs through their existing semantic validators, avoiding current nominal-instance early-return shortcuts. Preserve genuine authored text/byte source identity, valid parameter-search equality, nonempty validated confluence, and declared ordering behavior. Do not invent new source projections or generator grammar.

Existing generation ownership/gaps suites remain green: `.venv/bin/python -m pytest -q -p no:cacheprovider qml/tests/test_generation_ownership.py qml/tests/test_generation_gaps_unfilled.py` — **27 passed**, despite these independent public defects. No source fixes, staging, commits, or full generation acceptance claim.
