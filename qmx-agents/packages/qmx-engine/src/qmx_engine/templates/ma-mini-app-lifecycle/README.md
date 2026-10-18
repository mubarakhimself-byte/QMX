# MA Mini app lifecycle

Waits for the Lab sandbox and the host's app operations: list, consumers and `qmx app check` (`needs: sandbox, app-op`).

Built from cards D7 (mini app: create, check, publish, gated) and D8 (mini app: maintain, version, deprecate, archive) in `research/methodology/17-templates-dev-pm-lab.md`. He describes an app roughly; QMX builds it as a plugin folder, proves it with `qmx app check`, and ends with an install card for his click. A change builds a new version; retiring an app archives it with its blast radius, and nothing is ever deleted.

## Steps

1. `Read the request` (zero tokens) takes create, change, deprecate or archive. There is no delete.
2. `Existing apps and consumers` (`scripts/apps.py`) reads the apps that already do it, the Lab objects it would read, and a named app's lifecycle, versions and consumers.
3. `Build or retire?` sends create and change to the build path, deprecate and archive to `Deprecate or archive card`.
4. `Settle what the app does` (role `planner`, the card's grill) recommends what it shows, its slot, what it reads and provides, its schedule, tools and risk class, with up to five questions.
5. `Scaffold the app folder` refuses a money tool or the money risk class and starts the folder at lifecycle `draft`; a change is a new draft version. `Scaffold allowed?` stops a refused one before any build.
6. `Build tests first, then the app` (role `builder`, 40 turns) writes unit and contract tests, then the MCP server and widgets.
7. `Run qmx app check` (`scripts/check.py`) runs every check line, the render check with four prop states and screenshots, and the shadow line.
8. `Install card` appears only when every line is pass or needs-human; it installs disabled. `Review against the interview` (role `reviewer`, the card's validator) blocks an app that does not do what he asked.
9. `Deprecate or archive card` needs what replaces a deprecated app, and every live consumer rewired or accepted as stale before an archive; versions, evidence, logs and artifacts are kept.
10. `Render and grade` checks every number in the review against the apps read, the check report and the card.

## Left out, and why

- The arena of two or three widget prototypes and his pick: it needs the sandbox's render on sample props and his pick on the Apps page.
- D8's health path (probe, incidents deduped by error signature, the doctor, restarts inside the breaker policy): it needs the app-op health door and its monitor events; this template handles his change, deprecate and archive requests.
- The install, publish, deprecate and archive acts themselves: each card waits for his approval, because `human_gate` is unavailable and those acts are his.
- Lessons into the `build-mini-app` and `debug-app` skills: workflow memory rows are not used yet.
- Test fixtures: they come with the host's app check, whose real report shape they must match.
