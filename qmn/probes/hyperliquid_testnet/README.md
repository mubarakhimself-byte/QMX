# Hyperliquid testnet probe (C-16)

This folder proves that the trading node can trade Hyperliquid through CCXT before any real money is involved. It trades on Hyperliquid's testnet only. The node's CCXT client refuses to bind mainnet.

## What you do first (gate G-WALLET)

1. On Hyperliquid's own testnet site, open the API page and approve an agent wallet for your testnet account. Hyperliquid shows the agent's private key once. An agent wallet can trade but cannot withdraw, and it expires within 180 days.
2. Put some testnet USDC on that account from Hyperliquid's testnet faucet. The probe trades about 12 USDC of ETH at a time.
3. Add the agent wallet to the node's keys document, `qmx/trading-node-keys` in Credential Manager, as one more entry under `hyperliquid`:

   ```json
   {"address": "<your testnet account address>", "agent_key": "<the agent's private key>", "expires_at": "<its expiry, e.g. 2027-04-30T00:00:00+00:00>"}
   ```

## Run it

From the `qmx-agents` folder of the repo:

```text
uv run --no-sync python ../qmn/probes/hyperliquid_testnet/run.py --plan
uv run --no-sync python ../qmn/probes/hyperliquid_testnet/run.py
```

`--plan` reads the keys document, shows the testnet endpoint and lists the eight marks, with no network call. The second command runs the marks. Each prints PASS or FAIL. The probe closes what it opened at the end and exits 1 if any mark fails. It never prints a key.

A mark that fails because CCXT cannot do it is the signal for a native Hyperliquid client for that mark only. Nothing else changes.

## The offline proof

`offline.py` runs the same client, and the probe's own code, through the real CCXT 4.5.85 class with its network call answered on this machine. It needs no wallet and reaches no venue:

```text
uv run --no-sync python ../qmn/probes/hyperliquid_testnet/offline.py
```
