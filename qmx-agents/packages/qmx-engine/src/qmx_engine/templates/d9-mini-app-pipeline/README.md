# Connect one mini app's output to another

Waits for the host's app operations: the apps and pipelines doors (`needs: app-op`).

Built from card D9 (mini-app-to-mini-app data pipeline) in `research/methodology/17-templates-dev-pm-lab.md`. "When macro-daily-bias publishes, feed it to my session-filter app." Apps talk only through typed artifacts and the host's event bus, so the pipeline is a contract: the schemas must match or a tested transform bridges them, and nothing runs until he enables it.

## Steps

1. `Plan the wiring` (role `planner`) names the producer and what it emits, the consumer and what it accepts, whether the consumer waits, and up to three questions.
2. `Both apps and their schemas` (`scripts/apps.py`) reads both apps, their enabled state and versions, the producer's `provides` and the consumer's `feeds` schemas, and a recorded producer artifact.
3. `Schema compatibility` (zero tokens) checks, field by field, that everything the consumer requires the producer always gives, with the same type.
4. `Schemas compatible?` sends a mismatch to `Write the transform` (role `builder`, transforms only), which maps each required field to a producer field and leaves a field with no source unmapped, never invented.
5. `Contract test on recorded fixtures` validates the recorded artifact against the producer's schema, passes it through the transform, and validates the result against the consumer's schema.
6. `Pipeline folder and enable card` writes the wiring as data pinned to both versions and gives an enable card only to a passed contract test. `Render and grade` checks every number in the questions against his request, the apps read and the folder.

## Left out, and why

- The shadow run on live artifacts for a set period: it needs the host's event bus and a running producer.
- Enabling the pipeline and adding its trigger row: enabling is his act, and no workflow node may create a trigger; the card names the trigger it would run on.
- An external webhook in, with its signed `qmx/*` secret: he enters secrets himself; the webhook route is the host's.
- A schema break pausing the pipeline with a D8 card: it needs the pipeline running under the host.
- Test fixtures: they come with the host's apps door, whose real schemas they must match.
