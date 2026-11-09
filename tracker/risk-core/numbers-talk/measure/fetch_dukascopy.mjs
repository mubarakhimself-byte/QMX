// Download Dukascopy 1-minute bid and ask bars with dukascopy-node.
// Usage: node fetch_dukascopy.mjs <instrument> <period> [from] [to]
//   period = a | b | test   (a = last 90 days, b = 2025-11-01..2026-02-28)
// Output: data/duka_<instrument>_<period>_<bid|ask>.csv  (ts_ms,open,high,low,close,volume)
// Timestamps from Dukascopy are UTC epoch milliseconds (bar start).
import { getHistoricalRates } from 'dukascopy-node';
import { writeFileSync, mkdirSync } from 'node:fs';

const PERIODS = {
  a: ['2026-08-11', '2026-11-09'], // 90 days: Aug 11 .. Nov 8 inclusive (end is exclusive)
  b: ['2025-11-01', '2026-03-01'], // Nov 1 2025 .. Feb 28 2026 inclusive
};

const [instrument, period, fromArg, toArg] = process.argv.slice(2);
const [from, to] = fromArg ? [fromArg, toArg] : PERIODS[period];
if (!instrument || !from || !to) {
  console.error('usage: node fetch_dukascopy.mjs <instrument> <a|b|test> [from to]');
  process.exit(2);
}
mkdirSync('data', { recursive: true });

for (const priceType of ['bid', 'ask']) {
  const t0 = Date.now();
  const rows = await getHistoricalRates({
    instrument,
    dates: { from: new Date(from + 'T00:00:00Z'), to: new Date(to + 'T00:00:00Z') },
    timeframe: 'm1',
    priceType,
    volumes: true,
    ignoreFlats: false, // keep no-tick minutes; analysis flags them (volume 0) itself
    format: 'array',
    useCache: true,
    cacheFolderPath: 'data/.dukascopy-cache',
    batchSize: 10,
    pauseBetweenBatchesMs: 300,
    retryCount: 3,
    failAfterRetryCount: true,
  });
  const out = `data/duka_${instrument}_${period}_${priceType}.csv`;
  writeFileSync(out, 'ts,open,high,low,close,volume\n' + rows.map(r => r.join(',')).join('\n') + '\n');
  console.log(`${out}: ${rows.length} bars, first ${new Date(rows[0]?.[0]).toISOString()}, last ${new Date(rows.at(-1)?.[0]).toISOString()}, ${((Date.now() - t0) / 1000).toFixed(1)}s`);
}
