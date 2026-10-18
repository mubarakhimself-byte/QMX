# RS4 Literature review on a topic

Built from card R4 with R7 (calibrate) in `research/methodology/15-templates-researcher.md`. It answers "what methods exist for X, which hold up, which could we test" across a set of sources: a headline, a methods matrix with an evidence tier and a confidence per row, what QMX could test next, and the gaps.

## Steps

1. `Topic and sources` takes the topic and its sources, or fetches up to 40 arXiv papers on the topic in one request (arXiv's 3-second rule lives in the script).
2. `Plan the review` (role `planner`) classes the question and writes the one question and the brief every searcher works to. The scope questions a clarifier would ask become recorded assumptions.
3. `Search each chunk of sources` (role `searcher`) runs one searcher per chunk. The chunk size is the `chunk.size` setting, so 200 sources at the default 10 make 20 searchers and none is dropped. Each source gets an evidence tier from its venue.
4. `Synthesise` (role `synthesiser`) reads only the findings and builds the methods matrix. A verdict never rests on a video claim alone.
5. `Citations check` checks every quote in the synthesis against its source. An invented quote stops the run as failed.
6. `Verdicts to calibrate` and the shared `calibrate` block give the first five verdicts a confidence.
7. `Judge against the rubric` (role `judge`) scores accuracy, citations, completeness, source quality and efficiency.
8. `Write the review` (role `writer`) writes the review. A low or contested verdict is never the headline; a judge score under 0.7 puts a "weak review" banner on top.
9. `Render and grade` checks the review against `schemas/output.json` and checks every number in its headline and its "could test" lines against the sources.

## Test runs

A run started with `{"fixture": true}` reads `fixtures/sources.json`, twelve synthetic sources on portfolio optimisation, which make two searcher chunks at the default setting. `fixtures/recorded/` holds the answers for the `--fake` switch and the unit tests (`findings.json` answers the searchers in tests only).

## Left out, and why

- The clarifier's questions when he starts it in chat: nothing waits for him (rulings 57 and 77), so the planner records its scope choices as assumptions.
- alphaXiv `discover_papers` and `answer_pdf_queries`: they need the alphaXiv and PDF tools. Searchers read titles and abstracts.
- The video searcher on a browser lease, captions of his creators' videos, and creator cards: they need the QMX Browser.
- The revision round after a judge score under 0.7: the review ships with the banner instead.
- The scheduled monthly variant's new-papers pre-check and the topic memory: variants and workflow memory rows are later packets. Run it with a cron trigger once a variant wants one.
- The dollar cap with reserve-then-refund: the run's token and agent budget stands in.
