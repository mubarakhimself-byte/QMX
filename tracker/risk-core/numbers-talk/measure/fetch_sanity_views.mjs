// Second views of the Dukascopy data for spot checks:
//  - raw ticks for a few chosen hours (rebuild 1m bars and spread from ticks)
//  - hourly (h1) bid bars for the same days (an independently served aggregate)
// Output: data/sanity_tick_<instrument>_<hourIso>.csv and data/sanity_h1_<instrument>_<day>.csv
import { getHistoricalRates } from 'dukascopy-node';
import { writeFileSync, mkdirSync } from 'node:fs';

// One busy and one quiet hour per period for three instrument families.
const CHECKS = [
  ['eurusd', '2026-10-14T13:00:00Z'], ['eurusd', '2026-10-14T02:00:00Z'], ['eurusd', '2026-01-14T14:00:00Z'],
  ['xauusd', '2026-10-15T14:00:00Z'], ['xauusd', '2026-01-15T15:00:00Z'],
  ['usa500idxusd', '2026-10-13T13:00:00Z'], ['usa500idxusd', '2026-01-13T14:00:00Z'],
  ['deuidxeur', '2026-10-16T08:00:00Z'],
];

mkdirSync('data', { recursive: true });
const common = { format: 'array', useCache: true, cacheFolderPath: 'data/.dukascopy-cache', batchSize: 5, pauseBetweenBatchesMs: 300, retryCount: 3, failAfterRetryCount: true };

for (const [instrument, hourIso] of CHECKS) {
  const from = new Date(hourIso);
  const to = new Date(from.getTime() + 3600_000);
  const ticks = await getHistoricalRates({ ...common, instrument, dates: { from, to }, timeframe: 'tick' });
  const tag = hourIso.slice(0, 13).replace(/[:T]/g, '-');
  writeFileSync(`data/sanity_tick_${instrument}_${tag}.csv`, 'ts,ask,bid,ask_vol,bid_vol\n' + ticks.map(r => r.join(',')).join('\n') + '\n');
  const day = hourIso.slice(0, 10);
  const h1 = await getHistoricalRates({ ...common, instrument, dates: { from: new Date(day + 'T00:00:00Z'), to: new Date(new Date(day + 'T00:00:00Z').getTime() + 86400_000) }, timeframe: 'h1', priceType: 'bid', volumes: true, ignoreFlats: false });
  writeFileSync(`data/sanity_h1_${instrument}_${day}.csv`, 'ts,open,high,low,close,volume\n' + h1.map(r => r.join(',')).join('\n') + '\n');
  console.log(`${instrument} ${hourIso}: ${ticks.length} ticks, ${h1.length} h1 bars`);
}
