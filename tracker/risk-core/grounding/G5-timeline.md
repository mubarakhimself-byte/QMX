# G5: Timeline of the risk and sizing thinking

The lead's own synthesis of G1 to G4, 2026-11-01. It shows what each stage added, what it dropped and why, so the design starts from the whole arc rather than the latest file. Sources are the G files; see them for paths.

## The stages

| When | Where | Sizing idea | Risk per trade in practice | What it added | What it dropped |
|---|---|---|---|---|---|
| Apr–May 2026 | QMX-discussion vault (the "old system") | Half-Kelly × 9 multipliers (house money ×1.5, reverse house money, session, rating, ...) → lowest of 6 caps; sized off current equity on every trade | **0.5 % (scalper) / 0.8 % (ORB)** on paper: the cap almost always binds. The lost code probably ran at **~2 %** (cap never applied, Gap 1) with house money able to reach 2.25× | Session-to-session compounding (no per-session cap, "not negotiable"); house money, reverse house money; 10/5/3 % daily loss by account band; 3 slots; two-strike breaker; one-shot breakeven stop; Monte Carlo, PBO and Kelly-from-paper tests | — (first version). Code lost in the laptop crash |
| Jul 2026 | GitBook Book/BMS core | Kill-line ladder: runway = equity − kill line; ÷ 5 periods; ÷ (bench 2 × safety 2 × mean loss 0.35R) = dollars per R; capped by a "trust-bounded" Kelly; cost/edge ≤ 0.10 veto | **8.6 %** ($500 seed, $200 kill line → $42.86 per R) | Kill line and sizing share one number; R frozen at entry; seed cap 2.5× with sweep and re-seed; benches; Book/BMS hierarchy | Compounding between cycles (forbidden); the multiplier stacks ("dead list") |
| Aug 2026 | `docs/` corpus | Same ladder shape, units only | **None**: every number is a blank that blocks live money | B split (bench count vs loss allowance); exit preservation; broker stop on every order; kill switch that only a human lowers | Kelly cap, viability veto, cap-and-sweep numbers. QMX-discussion barred as a source (20 Aug) |
| Sep 2026 | ChatGPT sitting (`Coding-formulas-strategies.md`) | — | — | His "session capital" picture: Tokyo capital ≠ London capital ≠ New York capital; "house money + reverse house money made the system insane... it can't lose" | A "legacy pilot" simulation that judged itself unfaithful |
| 5–12 Oct | QRMX session (`df6630a9`) | "Brand-new system": the July ladder at 40 % kill line + old compounding per session + fast invalidation | **~8.6 %** ($300 → $26 a full stop, $9 an FI cut, $36 a day) | Loss points (1 per full stop, the cut's size per FI; 2 a day benches); reverse-house-money tiers by points; house money = part of today's winnings; Kelly as a ceiling; ramp to Kelly over a month; fortnightly review; the **unit** idea (8 Oct); run-01 simulations | The old 0.5 % clamp (shown to make house money inert) |
| 13 Oct | `b3275c9d` | — | — | All instruments; IC Markets Seychelles 1:1000, so leverage stops limiting R; "numbers are configurable, nothing in stone" | 30:1 leverage caps on R |
| 15–20 Oct | "Risk & sizing QML redesign" (`ea2b5af9`) | Cushion sizing from first principles: r ≤ 2·EV·D / (s²·ln(1/ε)); Kelly ≈ EV/s² as a ceiling; score n·EV²/s² | Derived, not set | The maths that makes house money and reverse house money fall out of the cushion; ε (acceptable kill-line odds) asked, never answered | Maths deprioritised on 17 Oct ("define the unit first"); MIS turned into a router |
| 20–29 Oct | "Agent team for MT5 article analysis" (`155c9835`) → unit-system design | — | — | MQL5 risk articles (risk-of-ruin, drawdown limits, Kelly + Monte Carlo); research numbers: kill-line odds at full/half/quarter Kelly 60/22/3 %; CUSUM ~240 trades; house money only on serially correlated records; ratchet belongs on the floor. Rulings: only he promotes; one automatic move (a risk rule stopping a unit); unit owns sizing and exits; pod ≈ BMS | Grow-back and house money deferred to this session; auto-live siblings rejected |
| 30–31 Oct | Unit plan (`tracker/risk-sizing`) | Risk socket: sizer, exits, halts, cross-unit hook; calibrated numbers (AD-22) | **0.5 % placeholder** | The machinery for numbers that move (range, step, minimum count, shrink, journal row per move) without saying which risk numbers move | — |
| 1 Nov | This session | Seed: 8 % rather than 1 % | — | Combine old + Book/BMS; nothing set in stone; scenario maths; old folder usable | — |

## The arc in one paragraph

Two engines keep replacing each other. The April engine was **many trades, small fixed risk, compounding off current equity**, dressed in machinery (Kelly, nine multipliers) that the caps mostly overrode. The July/October engine was **risk the seed hard against a kill line (~8.6 % per R), bank the wins**, with almost no adaptive machinery. Each generation dropped the other's growth engine: July forbade compounding between cycles; August blanked all numbers; the unit plan placed a 0.5 % stand-in. His "radioactive" memory most likely comes from the April *code* (about 2 % per trade, house money stacking) across many sessions a day, not from the written April spec. The one idea that can hold both is the October cushion maths: size from the distance to the floor, so the size grows with profits (house money) and shrinks near the floor (reverse house money) by one formula. The self-configuring unit (his 8 Oct idea, still never shown concretely) is the layer on top: which inputs of that formula move with the unit's own record.

## Threads still open across the whole arc

1. The risk level itself: 0.5 % (April spec), ~2 % (April code), 8.6 % (July/October), 8 % (his seed). The research says 8 % is ~0.8 Kelly for a good scalper edge and ruinous if the edge is half what was measured.
2. ε, how often touching the kill line is acceptable: asked three times; he reframed rather than answered.
3. Compounding between cycles (April yes, July no, cap-and-sweep later "concept agreed").
4. Account-level brakes: April had 10/5/3 % per day; July/August have only the kill line; code has neither.
5. Several units on one account: April had slots and a family budget; Book/BMS has no allocator; the unit plan sizes each unit from the whole account.
6. Stop loss vs fast invalidation only: never settled.
7. What "self-configuring" means in numbers: never shown.
