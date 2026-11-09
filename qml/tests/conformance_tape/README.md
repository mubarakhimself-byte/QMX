# Conformance tapes

A tape is one recorded run, small enough to read, of the two things a host supplies to a unit:
**the proposals it prices** and **the facts it prices them on**. Replaying a tape through two
hosts must give one decision, so a tape is how K9 tests 1 and 13 are checked: the same decision
in both hosts, and the tape through every driver that exists.

A tape is not a product. The proposal tape that would replay a unit's entries under a different
risk section is methodology's tool and this build ships no writer for it (`AD-18`). What lives
here is a test fixture with a documented shape.

## Shape

```json
{
  "equity": "100000",
  "fraction": "0.005",
  "entries": [
    {"market_id": "fx.eurusd", "side": "long", "entry_price": "1.10000", "stop": "1.09500",
     "instant": 1740954600000000000, "record": "qml/tests/fixtures/records/eurusd.json"}
  ]
}
```

- `equity` and `fraction` are the account fact and the sizing number every entry is priced at.
- `entries[].record` names the instrument record, so a tape is read without a deployment.
- `instant` is one instant for the whole tape: the facts are what a host knew at it.

**RC-08's tape is recorded in `qmn/tests/test_conformance_tape.py`**, as the `TAPE` constant
built from the four markets `qmn/tests/test_app_rate_fact.py` already drives. It is a constant
and not a file because the row it proves is still growing: RC-15 adds risk events and
would-have rows to the journal, RC-28 adds costs to the fill, and RC-63 reserves the proposal
row. A file frozen in this PR would be rewritten by the next three. The tape becomes a file when
its shape stops moving, and this note moves with it.

## The rule

Replaying one tape through QMB and through the node must give **equal signal rows**. Only
**fills, costs and latency** may differ, because those are what the venue and the clock add
after the decision. `test_k9_1_and_13_same_trail_in_both_hosts` compares the two journals' whole
`signal` bodies, not a subset, so a field that drifts out of one host's row fails the tape.

**One limit, stated so a later tape does not mistake it for a bug.** A conversion market's rate
fact is stamped with the host that supplied it (`qmb:replay` in `qmb/host/facts.py:98`,
`node:feed` in `qmn/app/facts.py:75`). Two hosts therefore store different `source` strings for
the same rate, and a byte-equal comparison is only meaningful over markets whose quote currency
is the account's own, where the rate is the exact `1` with no port to name. RC-08's tape is
recorded over those. Widening the tape to a conversion market needs the rate fact's source to
stop naming the host first; that is a change to `AD-15`'s fact surface, not to the row.
