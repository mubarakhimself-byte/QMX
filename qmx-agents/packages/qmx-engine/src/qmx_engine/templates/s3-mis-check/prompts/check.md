You check QMX's MIS, the program that reads each market and says what state it is in. He wants to improve it from the places where a careful trader reads the market differently. The input's `findings` were read by the `read` step from the MIS's reading history: per market and reading, the words it published, and every change point, the time its word changed.

1. For each market in `findings.checked`, read its bars around the change points your own way, with the `data` tools (`data_bars`, `data_features`). Read only the day in `findings.window`.
2. Decide, change point by change point, whether you read the market the same way the MIS did.

Answer:
- `title`: one line naming the day and how many change points you read differently.
- `text`: a short paragraph per market where you disagree, and one line naming the markets where you agree. Use only numbers that appear in `findings`, written as they appear there. Never state a number you read from the bars; say what you see in words ("the range kept widening", "price ran in one direction all morning").
- `receipts`: `["read"]`.
- `disagreements`: one per change point you read differently: its `market`, `reading` and `at` copied exactly from `findings`, `agent_reads` (the word you would have said) and `why`, both in words with no digits.

You propose nothing and change nothing. Each disagreement is an example for him to improve the MIS. Write a date as YYYY-MM-DD and a time as HH:MM, never as words around a bare number.
