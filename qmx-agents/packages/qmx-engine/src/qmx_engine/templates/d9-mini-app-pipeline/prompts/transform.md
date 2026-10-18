You write the transform between two QMX mini apps whose schemas do not match. The input is the compatibility check: each gap between what the producer gives and what the consumer requires.

Answer with `mapping`: for each field the consumer requires, the producer field path it is read from (`from`, a dot path such as `bias.direction`) or a fixed `value` when the producer has nothing for it, and `why` in a few words. Never invent data the producer does not give: a field with no source stays a gap and goes in `unmapped`.
