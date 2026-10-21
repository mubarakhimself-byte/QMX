# Nightly diff of the two Libraries

MIGRATION step 5. While `library_save` writes both `library.db` and the Library store, this
workflow diffs them: every old version present in the store, its blob the same hash, and the
latest version of each root the head of `main`. A clean diff passes; any gap fails the run, so a
test run's `test-report` reads `failed`.

Run it with `{"home": "<QMX home>"}`; `store` defaults to `<home>/library`. The cut-over (step 6)
waits for seven clean nightly diffs after the operator lands the migration.
