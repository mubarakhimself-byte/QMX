// The one place that says what each colour means.
export const tone: Record<string, string> = {
  needs: "text-needs",
  run: "text-run",
  up: "text-up",
  down: "text-down",
  idle: "text-idle",
  live: "text-live",
  paper: "text-paper",
};

// Words the backend uses for state, mapped to a tone.
export const wordTone: Record<string, string> = {
  live: "live",
  paper: "paper",
  trading: "up",
  done: "up",
  passed: "up",
  ok: "up",
  running: "run",
  queued: "idle",
  tested: "idle",
  draft: "idle",
  failed: "down",
};

export const stateLabel: Record<string, string> = {
  needs: "Needs you",
  run: "Working",
  up: "Fine",
  down: "Problem",
  idle: "Idle",
  live: "Live",
  paper: "Paper",
};

export const isNumber = (s: string) => /^[+\-−]?[$]?\d/.test(s) || /%$/.test(s);
export const numberTone = (s: string) =>
  /^\+/.test(s) ? "text-up" : /^[-−]\d/.test(s) ? "text-down" : "";
