import { SAMPLE_ORIGIN } from "$lib/origin";
import { SETUP_COPY } from "$lib/spawn";

export const FACTORY_TEST_LABEL = "FACTORY-TEST";

export type ChromeState =
  | "empty"
  | "loading"
  | "error"
  | "populated"
  | "stale"
  | "reconnecting"
  | "denied";

export const CHROME_STATES: readonly ChromeState[] = [
  "empty",
  "loading",
  "error",
  "populated",
  "stale",
  "reconnecting",
  "denied",
];

export type PackCapability = "visual" | "headless" | "mixed";

/** pairing_record_id is journal identity, never the Authorization value. */
export const FACTORY_TEST_PAIRING = {
  label: FACTORY_TEST_LABEL,
  pairing_record_id: "pairing:FACTORY-TEST-record",
  pending_code_shown_once: true,
  origin: SAMPLE_ORIGIN,
} as const;

export function stateCopy(state: ChromeState): string {
  switch (state) {
    case "empty":
      return SETUP_COPY;
    case "loading":
      return "Waiting for confirm. Pairing is a later host verb; this host does not issue a pairing_proof.";
    case "error":
      return "Origin-only issuance refused. Expired proof. Daemon discarded bytes at inspect (DEC-0507).";
    case "populated":
      return `${FACTORY_TEST_LABEL} paired fixture. initialize capabilities are listed when the live wire exists. pairing_record_id is not Authorization.`;
    case "stale":
      return "Stale snapshot. Badge the last observed mailbox; do not paint as failed.";
    case "reconnecting":
      return "Reconnecting. Distinct from failed. Reconnect is a query, not a new spawn.";
    case "denied":
      return "Denied. Typed refusal. Shell remains usable. Origin never issues pairing_proof.";
  }
}

export function parseFixtureState(raw: string | null): ChromeState {
  if (raw && (CHROME_STATES as readonly string[]).includes(raw)) {
    return raw as ChromeState;
  }
  return "empty";
}
