# Dictionary

The dictionary is the reusable, **role-neutral primitive language** of STRATS. A primitive is a concept (session high, liquidity sweep, engulfing completion). It is **not** permanently a trigger, confirmation, or stop — those jobs are assigned later as **role bindings** on a strategy.

## Family folders, not role folders

Organize by **concept family**, not by the job a strategy might assign:

| Family folder | Current file |
|---|---|
| `market-structure-and-location/` | [`locations-and-structure.md`](market-structure-and-location/locations-and-structure.md) |
| `price-action-and-patterns/` | [`triggers-patterns-transitions.md`](price-action-and-patterns/triggers-patterns-transitions.md) |
| `context-regime-and-intermarket/` | [`context-filters-confirmations.md`](context-regime-and-intermarket/context-filters-confirmations.md) |
| `invalidation-exits-and-management/` | [`exits-execution-management.md`](invalidation-exits-and-management/exits-execution-management.md) |

Empty family folders (time/sessions, liquidity/volume, indicators, risk/sizing, execution, market-data, …) are reserved for later appends. Do not invent a parallel dictionary per market.

**Do not fork per market.** Forex, crypto spot, and prop-firm constraints are **tags on strategies** (and overlays in `knowledge/prop-firms`), not separate primitive catalogs.

## Appendable

Add a concept in one of two ways:

1. **Existing family file** — append a new `## slug — Title` entry (or `## slug` if the title is the slug) with the 12 fields below. Match the heading style already in that file so `backend/import_dictionary.py` can parse it. (`###` is fine only if you also update the importer; today's four files use `##`.)
2. **New family** — add a family folder + markdown file in the same heading/field format, then point the importer at it.

### The 12 fields

Every entry uses these `- **Field:**` bullets:

1. Family
2. Aliases
3. Definition
4. Boundaries
5. Observable inputs
6. Recognition semantics
7. Parameters/profiles
8. Eligible roles
9. Market/data constraints
10. Transfer notes
11. Evidence/status
12. Uncertainty/variants

Keep entries role-neutral. Strategy-specific pair/timeframe/session/direction/timing belongs in bindings, not here.

After appending, rebuild: `python backend/import_dictionary.py`.
