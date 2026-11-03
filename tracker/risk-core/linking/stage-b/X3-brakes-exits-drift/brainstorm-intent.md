# X3 brainstorm intent (headless)

Source: `.memlog.md` in this folder. Working record: `brainstorm-working.md`. Arithmetic: `x3_brake_sim.py`, `out-200.txt`.

## Intent

Give the unit template a brake layer that performs: it trips rarely on a healthy unit at any trade frequency, it lets go by evidence, and its fire record doubles as a decay sensor. Exits are set from each unit's own excursions and proven. Live drift is handled by graded, reversible steps, never by pulling out on one bad day.

## Chosen directions

1. **Fast unit breaker in money or loss points at the unit's own percentile**, over a window of at least ten trades, with a halve step before the bench (H01, H02, H03). Count triggers become event evidence, not brakes.
2. **Two-speed circuit breaker**: the fast trip above, plus a slow sentinel that reads the fire count against the expected band on the unit's card (Basel-style zones), as the calm second key beside a trade CUSUM (H08, H09, H11).
3. **Every brake earns its place**: a registry row with expected fire rate, precision, trip tax and margin over a matched random control; shadow first, enforcement ramps after (H58, H12, H13, H14, H65).
4. **Restores**: half-open probes, settling, retrip back-off, memory ceiling, lockout to his hand after repeated failure (H15, H17).
5. **Cluster and BMS**: one shared-driver event counts once; chorus and burn-rate permits; a BMS breaker that stops entries and flattens only near the buffer (H20-H25).
6. **Isolation on evidence**: two tells per bucket, SQS K of N, peer ejection with a capped share, event windows by measured impact, fail-closed when data is unknown, scope keys for class, region, currency and underlying (H28-H37).
7. **Exits**: stops only where the unit's own persistence supports them; FI cut from winners' MAE and a named falsifying condition; breakeven only where it changes the forecast; exit families per style; exits never blocked (H38-H47).
8. **Drift**: three zones on planned looks; graded demotion with a recorded cause; bad-day classifier; input-first checks; re-promotion as a new episode with his click (H48-H56).

## Constraints carried

Agents never touch money. Only he promotes. Exits are never blocked. The kill switch only goes down by his hand. Brakes outrank accelerators. Every threshold derives from the unit's own record with a stated reason, and he can change how it derives.
