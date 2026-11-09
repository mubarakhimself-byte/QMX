#!/usr/bin/env bash
# Download every Dukascopy instrument for both periods, one at a time, each capped at 15 minutes.
cd "$(dirname "$0")"
for inst in ${INSTRUMENTS:-eurusd gbpusd usdjpy xauusd usa500idxusd usatechidxusd deuidxeur jpnidxjpy hkgidxhkd ausidxaud gbridxgbp eusidxeur}; do
  for p in a b; do
    timeout 900 node fetch_dukascopy.mjs "$inst" "$p" || echo "FAILED $inst $p"
  done
done
echo DONE
