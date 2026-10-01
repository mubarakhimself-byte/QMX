/**
 * Home chrome: work / attention / resume, optional chat, no instance
 * (FR-UI-03/06/10/15; DEC-0470; DEC-0484; DEC-0480; DEC-0477).
 */
import { get, writable } from "svelte/store";
import { FACTORY_TEST_LABEL } from "$lib/bootstrap";
import { paintIncompatibility } from "$lib/host/capabilities";
import { dispatchCancel, type JobHandleState } from "$lib/host/dispatchCancel";
import { dispatchChat } from "$lib/host/dispatchChat";
import { HOME_CHROME_AT_INSPECT, INSPECT_SHA } from "$lib/inspect";
import { listMailbox } from "$lib/host/listMailbox";
import {
  FACTORY_TEST_HOME_INVOKE,
  FACTORY_TEST_MANY_INSTANCE_REFS,
  FACTORY_TEST_ONE_INSTANCE_REFS,
  instanceIdRefs,
  invokeWithSelectedRefs,
  type SelectedRef,
} from "$lib/host/selectedRefs";
import { hostRuntime, type HostRuntime } from "$lib/host/runtime";

export const HOME_PRODUCT_SESSION_REF = "psess:H";

export const HOME_SESSION = {
  product_session_ref: HOME_PRODUCT_SESSION_REF,
  profile: "authoring" as const,
  app_instance_id: null,
};

export const HOME_CHROME_STATES = [
  "empty",
  "loading",
  "unavailable",
  "failed",
  "reconnecting",
  "stale",
  "unknown",
  "populated",
] as const;

export type HomeChromeState = (typeof HOME_CHROME_STATES)[number];

export type ObservationFacts = {
  listingAxis: string;
  diagnosis: string;
  fencing: string;
  fourthProduct: false;
  cancelAuthority: false;
  authorizesLive: false;
  hotSwap: false;
  autoRetryUnknownBlocked: false;
  commandTarget: false;
};

export type JobAttentionRow = {
  kind: "job_handle";
  id: string;
  title: string;
  jobState: JobHandleState;
  resumeTarget?: string;
  originating_product_session_ref?: string;
  refusalText?: string;
  paintedAsFailed: boolean;
};

export type ResumeAttentionRow = {
  kind: "resume";
  id: string;
  title: string;
  resumeTarget: string;
};

export type ObservationAttentionRow = {
  kind: "observation";
  id: string;
  title: string;
  observation: ObservationFacts;
};

export type AttentionRow =
  JobAttentionRow | ResumeAttentionRow | ObservationAttentionRow;

export type ReconnectPlan = {
  kind: "query";
  initialize: { same_producer_id: true };
  snapshots: true;
  wire_attach: true;
  job_handle_reattach: true;
  list_mailbox: true;
  replay_intent: false;
  implies_approval: false;
};

export const HOME_RECONNECT_PLAN: ReconnectPlan = {
  kind: "query",
  initialize: { same_producer_id: true },
  snapshots: true,
  wire_attach: true,
  job_handle_reattach: true,
  list_mailbox: true,
  replay_intent: false,
  implies_approval: false,
};

export const FACTORY_TEST_QUEUED_JOB: JobAttentionRow = {
  kind: "job_handle",
  id: "job:FACTORY-TEST-queued",
  title: `${FACTORY_TEST_LABEL} queued handle`,
  jobState: "queued",
  resumeTarget: "job:FACTORY-TEST-queued",
  originating_product_session_ref: HOME_PRODUCT_SESSION_REF,
  paintedAsFailed: false,
};

export const FACTORY_TEST_FAILED_JOB: JobAttentionRow = {
  kind: "job_handle",
  id: "job:FACTORY-TEST-failed",
  title: `${FACTORY_TEST_LABEL} failed handle`,
  jobState: "failed",
  originating_product_session_ref: HOME_PRODUCT_SESSION_REF,
  refusalText: "typed refusal FACTORY-TEST. Shell remains usable.",
  paintedAsFailed: true,
};

export const FACTORY_TEST_UNKNOWN_JOB: JobAttentionRow = {
  kind: "job_handle",
  id: "job:FACTORY-TEST-unknown",
  title: `${FACTORY_TEST_LABEL} unknown handle`,
  jobState: "unknown",
  paintedAsFailed: false,
};

export const FACTORY_TEST_RESUME: ResumeAttentionRow = {
  kind: "resume",
  id: HOME_PRODUCT_SESSION_REF,
  title: `Resume ${HOME_PRODUCT_SESSION_REF}`,
  resumeTarget: HOME_PRODUCT_SESSION_REF,
};

export const FACTORY_TEST_OBSERVATION: ObservationAttentionRow = {
  kind: "observation",
  id: "obs:FACTORY-TEST-kit",
  title: `${FACTORY_TEST_LABEL} kit diagnosis`,
  observation: {
    listingAxis: "host-health",
    diagnosis: `${FACTORY_TEST_LABEL} diagnosis snapshot`,
    fencing: "AD-25 fencing snapshot",
    fourthProduct: false,
    cancelAuthority: false,
    authorizesLive: false,
    hotSwap: false,
    autoRetryUnknownBlocked: false,
    commandTarget: false,
  },
};

export const HOME_FIXTURE_NAMES = [
  ...HOME_CHROME_STATES,
  "selected-refs-many",
  "selected-refs-one",
] as const;

export type HomeFixtureName = (typeof HOME_FIXTURE_NAMES)[number];

export type HomeSnapshot = {
  chromeState: HomeChromeState;
  profile: "authoring";
  isCopilot: false;
  appInstanceId: null;
  mintedSyntheticInstance: false;
  guessedInstance: false;
  selectedRefs: SelectedRef[];
  selectedInstanceRefCount: number;
  rows: AttentionRow[];
  lastIssuer: "dispatchInvoke" | "dispatchChat" | "dispatchCancel" | null;
  lastIncompatibilityCode: string | null;
  lastIncompatibility: string | null;
  chatProceeded: boolean;
  lastResumeTarget: string | null;
  mailboxEmptySuccess: false;
  observationIsProduct: false;
  observationIsCancelAuthority: false;
  unknownPaintedAsFailed: false;
  reconnect: ReconnectPlan;
  producerId: string;
  label: typeof FACTORY_TEST_LABEL;
  inspectSha: typeof INSPECT_SHA;
  homeChromeAtInspect: false;
};

function rowsForState(state: HomeChromeState): AttentionRow[] {
  switch (state) {
    case "populated":
    case "stale":
    case "reconnecting":
      return [
        FACTORY_TEST_QUEUED_JOB,
        FACTORY_TEST_FAILED_JOB,
        FACTORY_TEST_RESUME,
        FACTORY_TEST_OBSERVATION,
      ];
    case "failed":
      return [FACTORY_TEST_FAILED_JOB];
    case "unknown":
      return [FACTORY_TEST_UNKNOWN_JOB];
    default:
      return [];
  }
}

function snapshotFrom(
  partial: Partial<HomeSnapshot> &
    Pick<HomeSnapshot, "chromeState" | "selectedRefs" | "rows">,
): HomeSnapshot {
  const selectedRefs = partial.selectedRefs;
  return {
    chromeState: partial.chromeState,
    profile: "authoring",
    isCopilot: false,
    appInstanceId: null,
    mintedSyntheticInstance: false,
    guessedInstance: false,
    selectedRefs,
    selectedInstanceRefCount: instanceIdRefs(selectedRefs).length,
    rows: partial.rows,
    lastIssuer: partial.lastIssuer ?? null,
    lastIncompatibilityCode: partial.lastIncompatibilityCode ?? null,
    lastIncompatibility: partial.lastIncompatibility ?? null,
    chatProceeded: partial.chatProceeded ?? false,
    lastResumeTarget: partial.lastResumeTarget ?? null,
    mailboxEmptySuccess: false,
    observationIsProduct: false,
    observationIsCancelAuthority: false,
    unknownPaintedAsFailed: false,
    reconnect: HOME_RECONNECT_PLAN,
    producerId: partial.producerId ?? hostRuntime.producer_id,
    label: FACTORY_TEST_LABEL,
    inspectSha: INSPECT_SHA,
    homeChromeAtInspect: HOME_CHROME_AT_INSPECT,
  };
}

function initialSnapshot(): HomeSnapshot {
  return snapshotFrom({
    chromeState: "empty",
    selectedRefs: [],
    rows: [],
  });
}

export const homeState = writable<HomeSnapshot>(initialSnapshot());

function commit(next: HomeSnapshot): HomeSnapshot {
  homeState.set(next);
  return next;
}

export function getHomeState(): HomeSnapshot {
  return get(homeState);
}

export function resetHomeState(): HomeSnapshot {
  return commit(initialSnapshot());
}

export function homeStateCopy(state: HomeChromeState): string {
  switch (state) {
    case "empty":
      return "No running work. One action to start Copilot or Authoring.";
    case "loading":
      return "Loading attention. Skeletons stay inside this list.";
    case "unavailable":
      return "Home unavailable. Identity plus reason. Not a successful empty mailbox.";
    case "failed":
      return "Typed refusal. Shell remains usable.";
    case "reconnecting":
      return "Reconnecting. Distinct from failed. Reconnect is a query: initialize same producer_id, snapshots, wire.attach, JobHandle.reattach, list_mailbox. Does not replay intent. Does not imply approval.";
    case "stale":
      return "Stale snapshot. Badge the last observed attention; do not paint as failed.";
    case "unknown":
      return "unknown. Not failed. Not painted as failed.";
    case "populated":
      return "Attention rows plus optional Home chat. Observation is not a fourth product.";
  }
}

export function parseHomeFixture(raw: string | null): HomeFixtureName | null {
  if (raw && (HOME_FIXTURE_NAMES as readonly string[]).includes(raw)) {
    return raw as HomeFixtureName;
  }
  return null;
}

export function applyHomeFixture(raw: string | null): HomeSnapshot {
  const name = parseHomeFixture(raw);
  if (!name) return get(homeState);
  const current = get(homeState);
  if (name === "selected-refs-many") {
    return commit(
      snapshotFrom({
        ...current,
        selectedRefs: FACTORY_TEST_MANY_INSTANCE_REFS,
      }),
    );
  }
  if (name === "selected-refs-one") {
    return commit(
      snapshotFrom({
        ...current,
        selectedRefs: FACTORY_TEST_ONE_INSTANCE_REFS,
      }),
    );
  }
  return commit(
    snapshotFrom({
      ...current,
      chromeState: name,
      rows: rowsForState(name),
    }),
  );
}

export function setHomeChromeState(state: HomeChromeState): HomeSnapshot {
  const current = get(homeState);
  return commit(
    snapshotFrom({
      ...current,
      chromeState: state,
      rows: rowsForState(state),
    }),
  );
}

export function sendHomeChat(
  body = `${FACTORY_TEST_LABEL} home chat without instance`,
  runtime: HostRuntime = hostRuntime,
): HomeSnapshot {
  const current = get(homeState);
  const result = dispatchChat(
    { body, product_session_ref: HOME_PRODUCT_SESSION_REF },
    runtime,
  );
  if (!result.ok) {
    return commit(
      snapshotFrom({
        ...current,
        lastIssuer: "dispatchChat",
        lastIncompatibilityCode: result.incompatibility.code,
        lastIncompatibility: paintIncompatibility(result.incompatibility),
        chatProceeded: false,
        producerId: runtime.producer_id,
      }),
    );
  }
  return commit(
    snapshotFrom({
      ...current,
      lastIssuer: "dispatchChat",
      lastIncompatibilityCode: null,
      lastIncompatibility: null,
      chatProceeded: true,
      producerId: runtime.producer_id,
    }),
  );
}

export function submitHomeInvoke(
  runtime: HostRuntime = hostRuntime,
): HomeSnapshot {
  const current = get(homeState);
  const result = invokeWithSelectedRefs(
    FACTORY_TEST_HOME_INVOKE,
    current.selectedRefs,
    runtime,
  );
  if (!result.ok) {
    return commit(
      snapshotFrom({
        ...current,
        lastIssuer: "dispatchInvoke",
        lastIncompatibilityCode: result.incompatibility.code,
        lastIncompatibility: paintIncompatibility(result.incompatibility),
        producerId: runtime.producer_id,
      }),
    );
  }
  return commit(
    snapshotFrom({
      ...current,
      lastIssuer: "dispatchInvoke",
      lastIncompatibilityCode: null,
      lastIncompatibility: null,
      producerId: runtime.producer_id,
    }),
  );
}

export function resumeHome(target: string): HomeSnapshot {
  const current = get(homeState);
  return commit(
    snapshotFrom({
      ...current,
      lastResumeTarget: target,
    }),
  );
}

export function cancelHomeJob(
  row: AttentionRow,
  runtime: HostRuntime = hostRuntime,
): HomeSnapshot {
  const current = get(homeState);
  if (row.kind !== "job_handle" || !row.originating_product_session_ref) {
    return current;
  }
  const result = dispatchCancel(
    {
      handle_id: row.id,
      logical_run_id: `run:${row.id}`,
      attempt_id: 1,
      expected_state: row.jobState,
      originating_product_session_ref: row.originating_product_session_ref,
    },
    runtime,
  );
  if (!result.ok) {
    return commit(
      snapshotFrom({
        ...current,
        lastIssuer: "dispatchCancel",
        lastIncompatibilityCode: result.incompatibility.code,
        lastIncompatibility: paintIncompatibility(result.incompatibility),
        producerId: runtime.producer_id,
      }),
    );
  }
  return commit(
    snapshotFrom({
      ...current,
      lastIssuer: "dispatchCancel",
      lastIncompatibilityCode: null,
      lastIncompatibility: null,
      producerId: runtime.producer_id,
    }),
  );
}

export function reconnectHome(
  runtime: HostRuntime = hostRuntime,
): HomeSnapshot {
  const current = get(homeState);
  const mailbox = listMailbox(
    { product_session_ref: HOME_PRODUCT_SESSION_REF },
    runtime,
  );
  if (!mailbox.ok) {
    const chromeState =
      current.chromeState === "reconnecting" ? "reconnecting" : "unavailable";
    return commit(
      snapshotFrom({
        ...current,
        chromeState,
        lastIssuer: null,
        lastIncompatibilityCode: mailbox.incompatibility.code,
        lastIncompatibility: paintIncompatibility(mailbox.incompatibility),
        producerId: runtime.producer_id,
      }),
    );
  }
  return commit(
    snapshotFrom({
      ...current,
      lastIssuer: null,
      lastIncompatibilityCode: null,
      lastIncompatibility: null,
      producerId: runtime.producer_id,
    }),
  );
}
