"""QMX gateway: one loopback Anthropic Messages endpoint for every CLI process.

Public to qmx-control: `qma_gateway.contract` only (import-linted). Everything
else is the gateway process's private implementation.

Module map:
    contract.py    shared pure types: routes, leases, desired state, events
    sealed.py      the plan credential as an unreadable value
    server.py      process entry, header split, lease auth, routing, cap gate
    lanes.py       plan relay, key lane + per-route adapter, provenance
    translator.py  GPT lane: Anthropic Messages <-> OpenAI Responses on SIWC
    tap.py         response tap: usage meter + money wire gate
"""
