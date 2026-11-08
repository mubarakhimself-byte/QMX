# Find repeated code, clashing names and gaps in the dictionary

The librarian: a scan of the dictionary for code written twice, names two entries share, and entries that lack what their next status needs, each finding with the pins and fingerprints that prove it. It changes nothing. Part B `workflows.md` section 3, "Librarian".

## Steps

1. `Scan the dictionary` (`scripts/scan.py`, zero tokens) reads QML's own entries with their code and the content wave committed beside QML (`qml/catalogue-seed/wave-1/`, faces only). It groups code by fingerprint and proposes one block per repeated cluster, runs QML's corpus check across every entry, and lists each entry the checker refuses or whose next status lacks something. It lands one `librarian-report` artifact on the run's own ref.

## Left out, and why

- Entries only the Library holds (the port's drafts, his own components) and the custom code inside units: a script never opens the Library. The `blocks` rows read them for an agent, and a later step can add them once a workflow can read the Library (`needs: real-library` on the drafts that wait for it).
