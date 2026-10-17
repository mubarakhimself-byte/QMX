# RS1 Paper scout to research note

Built from card R1 in `research/methodology/15-templates-researcher.md`. Every six hours it looks at the newest arXiv papers in trading, portfolio management, statistical finance and risk management. When there are new ones it keeps at most three that could be tested on price data, reads each one with a fixed question battery, checks every quoted claim against the paper, and writes a research note. When nothing is new, or nothing passes triage, the run ends silently and spends no tokens after triage.

## Steps

1. `New paper ids?` is a monitor on `scripts/feed_ids.py`, the zero-token pre-check. It wakes the rest only when the ids change.
2. `Only the new ids` (the shared `preflight` block's script) hands on the ids it had not seen.
3. `Fetch titles and abstracts` fetches up to 20 new papers in one arXiv request. arXiv's one request per 3 seconds rule lives in the two fetch scripts.
4. `Triage against watch topics` (role `triage`) keeps at most three papers. The watch topics are in `prompts/triage.md`; edit them there.
5. `Read each paper` (role `reader`) runs one reader per paper with the question battery of the shared `paper-read` block.
6. `Citations check` (the shared `research-harness` grader) marks every claim whose quote is not in the paper.
7. `Write the note` (role `writer`) writes one entry per paper: testable yes or no, replicable yes, proxy or no, costs known or unknown, the flags, and only the cited claims.
8. `Check the note's quotes` runs the same citation grader over the note: every quote must appear in the paper it names, or the run stops as failed.
9. `Render and grade` (the shared `render-and-grade` block) checks the note against `schemas/output.json` and checks that every number in it appears in the cards or abstracts. A failed check stops the run as failed. `Deliver` hands on the note as the run's result.

## Test runs

A run started with `{"fixture": true}` replays `fixtures/feed.json` and `fixtures/papers.json`, six synthetic papers, instead of arXiv. Install tests the template this way on real models. The answers in `fixtures/recorded/` serve the `--fake` switch for the `llm` nodes and the unit tests.

## Left out, and why

- The alphaXiv hot feed beside arXiv's RSS: it needs an alphaXiv tool.
- Reading the full PDF with `answer_pdf_queries`: readers answer from the title and abstract, and say `not stated` for the rest. A PDF tool is a later packet.
- Listing a code repository's tree when a paper links one: it needs a GitHub tool.
- R7 calibrate on the headline claims: the calibrate block is not built.
- Opening a proposal for R2 or R3 when a paper is testable and replicable: those templates and the proposal card are not built.
- Mermaid, chart and headless render checks: no renderer is wired to the engine yet; the grader checks the schema and the numbers.
- `seen_ids` as a workflow memory row, and starred authors and topics: the monitor's own state holds the last ids.
- "Could not read" for a reader that fails twice: a failed reader parks the run instead.
- The 5, 15 and 30 minute retry ladder is the monitor's and the fetch step's retry; alphaXiv quota waits need the alphaXiv tool.
