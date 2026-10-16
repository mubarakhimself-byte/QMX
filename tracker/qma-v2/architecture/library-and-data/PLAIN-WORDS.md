# The Library and remote data, in plain words

**What you asked for.** One Library that keeps everything: units, strategies, bots and bot cards, workflows and their runs, mini apps, skills, methods, papers and videos, notes, backtests. Agents can read and write it. Several agents can work on the same thing without wrecking each other's work. Backups go to your server and your bucket. Work that runs off your PC must reach the same Library and send its logs home.

**What exists today.** Two Libraries in the backend with opposite rules: one only accepts ten trading record kinds and refuses workflows, skills and apps; the other accepts anything but only as JSON, with free-text links and no branches. The screens draw a third version from demo data. None of the three talk to each other.

**The design, in one picture.** The Library works like a photo archive plus a version history:

- Every file (a bot's code, a PDF, a model, a video transcript) is stored once, named by its own fingerprint. Two identical files are one file.
- Every saved thing is a small "card" (we call it an object) that says what kind it is, which files belong to it, what came before it, and what it is related to. Cards are never edited. A change is a new card that points back at the old one. So you can always see every version and nothing is ever lost.
- Each thing has pointers: `main` is the version you trust; variants, agent branches and run branches are other pointers. A workflow run works on its own branch and, when it passes, everything it made lands on `main` by itself, under a per-workflow rule you set once (default: land). Nothing waits for you; the screen shows what landed. The two exceptions: a workflow's self-made improvement becomes the "champion" the scheduler runs but only reaches `main` when you click, and putting a unit on the trading node stays the node's own click. In a chat, when an agent and you changed the same lines, QMX shows both sides next to each other and asks you to pick. It never guesses.
- Relationships are a fixed list of words ("produced by", "tested by", "part of", "cites" and so on). No agent can invent a new kind of link, so the map of how things connect is built by reading the cards, not by asking a model.
- Nothing is deleted. Archiving hides a thing and records why.

**Finding things.** Text search as today, plus a map built from the links. When you ask the copilot a question about the Library, the map decides whether there is a real path from your words to real items first. If there is none, it says so before any model is asked. The model only writes up what the map found, and every sentence cites the item it came from.

**Backups and your PC's disk.** Your PC keeps the catalogue, every card and the files you use often. Your server keeps a full copy and gets every new card right after you save. Your bucket gets a full copy every night, pushed by the server, not by your PC. A big file you have not touched in a while can live only on the server and the bucket and come back when you open it. Your server runs a small restore test every night and a full one every month, so the backup is proven, not assumed.

**Runs off your PC.** A small service on your server, the Hub, speaks the same Library language. A workflow running on the server, or on E2B, Modal or Amp, talks only to the Hub. It gets a one-run pass that lets it write to its own branch and read what it needs, and nothing else. It never sees broker credentials; those stay in Windows Credential Manager on your PC. Money stays read-only. Every remote run carries a sidecar that sends heartbeat, logs, metrics, traces and checkpoints to the Hub. When your PC sleeps, nothing stops. When it wakes, it pulls what happened and pushes what you did.

**The workflow engine.** It reads workflow definitions from the Library, pins the exact version it ran, and writes one run card per run with every artifact linked back. "Tested" means a passing test run is linked, not a tick box someone can flip.

**Where it lives.** On your PC for now. Moving it to your server later is a setting and a six-step procedure, not a rebuild: the screens, the agents and the engine never know which machine answers. Workflow memory (what runs learned, what not to retry, which tools agents wrote) lives in the same Library as cards, so it is backed up and searched like everything else. Market ticks and bars stay out of the Library; a small "dataset card" points at them so every result says exactly which data it used.

**What you decide (five questions, in OPEN-DECISIONS.md).** Whether the Library mirrors or replaces the trading-node registry (mirror, recommended); whether the bucket copy is encrypted (yes, recommended); whether to ship semantic search now (yes, optional and rebuildable); whether to open a public door on the Hub for cloud providers that cannot join your private network (off until you buy such compute); whether a copilot chat still asks you before moving a strategy or app onto `main` (yes, you are there anyway).

**What changes in the docs.** DEC-0271 (Library as a narrow projection) and the "no Library database" rule are replaced; DEC-0443's "uninstalled" becomes "archived"; the workflow docs that said templates are not Library things are reversed. The full list is in DOC-CHANGES.md.
