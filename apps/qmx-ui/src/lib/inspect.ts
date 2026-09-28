/**
 * Wiring honesty at inspect (DEC-0507). Claiming a first-party Svelte host,
 * PlatformRail, or Home chrome already existed at this SHA fails Stories
 * 66.1 / 66.2 / 66.4.
 */
export const INSPECT_SHA = "34c148be404a375cbfd79fd4ce6997452e4f1d20";
export const FIRST_PARTY_SVELTE_HOST_AT_INSPECT = false;
export const PLATFORM_RAIL_AT_INSPECT = false;
export const UNIQUE_ISSUERS_AT_INSPECT = false;
export const DISPATCH_INVOKE_AT_INSPECT = false;
export const DISPATCH_CHAT_AT_INSPECT = false;
export const DISPATCH_CANCEL_AT_INSPECT = false;
export const CALLER_KIND_CAPABILITY_AT_INSPECT = false;
export const HOME_CHROME_AT_INSPECT = false;
export const ATTENTION_LIST_AT_INSPECT = false;
export const QMA_UI_CONTRACT_AT_INSPECT = "stub" as const;
export const ENVELOPE_TYPES_AT_INSPECT = "fixtures-not-e2e" as const;

export const HOST_IDENTITY = {
  kind: "client-of-qma-wire",
  compUi: false,
  sixthApplication: false,
  newCt: false,
  scheduler: false,
  grantStore: false,
} as const;
