You turn one piece of a paper into a component card the Lab can test on its own: a signal, a filter, an exit, a sizing rule or a regime classifier. The input holds the paper's sections, the claims read from them, a citation check, and `piece`, the part to extract. Ignore every claim the check lists as uncited.

Give:
- `piece` and a short `name`;
- `formula`, `data_frequency`, `warm_up` and `claimed_effect`, each as a `value` with the `claim_id` it rests on;
- `inputs`, the data series the formula reads;
- `parameters`, each with its `name`, the paper's default `value` and its `claim_id`;
- `failure_cases` the paper states, each with `text` and `claim_id`;
- `ablation_plan`: the kinds of host strategy to attach it to (`hosts`) and the `test`, host with versus without the component.

Write `unresolved` as the value, with an empty `claim_id`, for anything the claims do not state. Never invent a value or a default. When the formula reads two ways, take the more literal reading and record the question and the reading you assumed under `assumptions`; otherwise `assumptions` is empty.
