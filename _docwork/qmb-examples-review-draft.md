# QMB analysis example provenance review (draft)

Both examples passed tuple copies of journal rows to project(). The current
reader contract requires CT29ProjectionSource locators so project() can reopen
CT10/12, CT13 and terminals. The examples now require an explicit trusted
operator module:function and runtime root. They pass its CT32 and durable reader
locator to project; there is no fabricated default, test import in a shipped
example, or reader guard relaxation.

The subprocess tests use a provider-free operator fixture that persists a real
recorded replay and returns its reader locator. All prior example assertions
remain. Evidence: examples-durable/pytest.txt: 2 passed; analysis-reviewed/
pytest.txt: 47 passed (projection, compare, homes and source-integrity suites,
including refusal of copied rows); qmb-types-example/output.txt: zero errors.
Self-review: no shared public projection or CT47 implementation edits.
