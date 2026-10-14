/**
 * Browser-only "what if" maths for pod settings (demo). A curve is replayed
 * return by return with the risk scaled, losses and gains weighted by the
 * sizing method, a drawdown ladder cutting size below the peak, and a kill
 * line that stands the pod down. Nothing here is a real backtest.
 */

/** A drawdown ladder step: at `at`% below the peak, size is multiplied by `mult`. */
export type Step = { at: number; mult: number };

export type Replay = {
  /** Risk relative to the settings the curve was made with (1 = unchanged). */
  scale: number;
  /** Multipliers on winning and losing returns (sizing method character). */
  gain?: number;
  loss?: number;
  ladder?: Step[];
  /** The ladder the input curve already ran with; its cuts are undone first. */
  made?: Step[];
  /** Stand down once the curve is this % below its start. */
  killAt?: number;
};

export function ladderMult(dipPct: number, ladder: Step[] = []): number {
  let m = 1;
  for (const s of ladder) if (dipPct >= s.at) m = Math.min(m, s.mult);
  return m;
}

export function replay(
  curve: number[],
  o: Replay,
): { curve: number[]; stoodDownAt: number | null } {
  const out = [curve[0]];
  let peak = curve[0];
  let madePeak = curve[0];
  let stoodDownAt: number | null = null;
  for (let i = 1; i < curve.length; i++) {
    const prev = out[i - 1];
    if (stoodDownAt !== null) {
      out.push(prev);
      continue;
    }
    const madeDip = ((madePeak - curve[i - 1]) / madePeak) * 100;
    madePeak = Math.max(madePeak, curve[i]);
    const r = (curve[i] / curve[i - 1] - 1) / ladderMult(madeDip, o.made);
    const tilt = r >= 0 ? (o.gain ?? 1) : (o.loss ?? 1);
    const dipPct = ((peak - prev) / peak) * 100;
    const v = prev * (1 + r * o.scale * tilt * ladderMult(dipPct, o.ladder));
    out.push(v);
    peak = Math.max(peak, v);
    if (o.killAt !== undefined && v <= curve[0] * (1 - o.killAt / 100))
      stoodDownAt = i;
  }
  return { curve: out, stoodDownAt };
}

/** Deepest fall from a peak, in % (positive). */
export function deepestDip(values: number[]): number {
  let peak = values[0];
  let worst = 0;
  for (const v of values) {
    peak = Math.max(peak, v);
    worst = Math.max(worst, (peak - v) / peak);
  }
  return worst * 100;
}

/** First to last, in %. */
export const growth = (values: number[]) =>
  (values[values.length - 1] / values[0] - 1) * 100;
