# ML training run with a holdout

Waits for QMB's doors for agents and the Lab sandbox with its compute (`needs: qmb-door, sandbox`).

Built from card D6 (ML or neural-net training run with a holdout) in `research/methodology/17-templates-dev-pm-lab.md`. It trains a model for a slot (entry, regime, sizing, throttle or his own) without leaking the future and without peeking at the test set, and publishes it only when it held on its sealed test and earns its slot after costs.

## Steps

1. `Settle the slot, label and features` (role `planner`, the card's grill) recommends the slot, the label, its horizon, the features, the model family and how many configurations may be tried, with up to five questions.
2. `Build and split the dataset` (`scripts/dataset.py`) builds the point-in-time dataset, the train, validation and sealed-test splits with purge and embargo, a shuffled-label model, and the compute estimate.
3. `Leakage and cost checks`: the purge is at least the label horizon, every feature ends before its label, shuffled labels score within 0.02 of chance, the sealed test is untouched, and the estimate is within his ask-above number.
4. `No leak and within budget?` stops the run with the problems and nothing trained.
5. `Train, test once and ablate` (`scripts/train.py`) trains up to K configurations on validation, touches the sealed test once on the chosen one, and runs a host strategy with and without the model through D2 and QMB.
6. `Overfit, holdout and ablation verdict` flags a train and validation gap above 0.10, marks a sealed score outside the validation band "did not hold", and publishes only with a gain after costs.
7. `Write the model card` (role `writer`) writes the summary; `Render and grade` checks every number in the scope, the questions and the summary against his goal, the dataset and the training run.

## Left out, and why

- His answers to the questions and his yes above the ask-above number: the run takes the recommended scope and ends with a spend card above his number, because `human_gate` is unavailable.
- Plugging the model into its slot as a published object and its lineage: they need the Lab's model registry and the real Library.
- R7 calibrate across seeds: the training call returns the validation band across seeds instead.
- Loss curves and feature importance as pictures: drawing is UI-side.
- Test fixtures: they come with the sandbox and QMB's doors, whose real output they must match.
