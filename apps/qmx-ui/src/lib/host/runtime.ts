import { get, writable } from "svelte/store";
import { FACTORY_TEST_LABEL } from "$lib/bootstrap";
import {
  FACTORY_TEST_CURRENT_CAPABILITIES,
  FACTORY_TEST_MISSING_CAPABILITIES,
  paintIncompatibility,
  type CapabilitySet,
  type TypedIncompatibility,
} from "./capabilities";
import { dispatchCancel, FACTORY_TEST_CANCEL } from "./dispatchCancel";
import { dispatchChat } from "./dispatchChat";
import { dispatchInvoke, FACTORY_TEST_GRANTED_OP } from "./dispatchInvoke";
import { listMailbox } from "./listMailbox";
import { claimProducer, memoryKv, memoryLocks, mintTabToken } from "./producer";
import { createWireClient, type HostWireClient } from "./wireClient";

export type CallerEventType =
  | "request_invoke"
  | "submit_chat"
  | "submit_invoke"
  | "cancel_display"
  | "cancel_job"
  | "list_mailbox";

export type HostSnapshot = {
  producerId: string;
  lastCallerEvent: CallerEventType | null;
  lastIssuer: "dispatchInvoke" | "dispatchChat" | "dispatchCancel" | null;
  lastIncompatibilityCode: string | null;
  lastIncompatibility: string | null;
  widgetImportedWire: false;
  shellUsable: true;
  chatProceeded: boolean;
  wireCallCount: number;
  lastWireName: string | null;
  capabilitiesLabel: string;
  label: typeof FACTORY_TEST_LABEL;
};

export type HostRuntime = {
  wire: HostWireClient;
  capabilities: CapabilitySet;
  producer_id: string;
};

function snapshotOf(
  runtime: HostRuntime,
  extra: Partial<HostSnapshot>,
): HostSnapshot {
  const lastCall = runtime.wire.transport.calls.at(-1);
  return {
    producerId: runtime.producer_id,
    lastCallerEvent: extra.lastCallerEvent ?? null,
    lastIssuer: extra.lastIssuer ?? null,
    lastIncompatibilityCode: extra.lastIncompatibilityCode ?? null,
    lastIncompatibility: extra.lastIncompatibility ?? null,
    widgetImportedWire: false,
    shellUsable: true,
    chatProceeded: extra.chatProceeded ?? false,
    wireCallCount: runtime.wire.transport.calls.length,
    lastWireName: lastCall?.name ?? null,
    capabilitiesLabel:
      Object.entries(runtime.capabilities)
        .filter(([, on]) => on)
        .map(([name]) => name)
        .join(",") || "none",
    label: FACTORY_TEST_LABEL,
  };
}

function initialSnapshot(): HostSnapshot {
  return {
    producerId: "",
    lastCallerEvent: null,
    lastIssuer: null,
    lastIncompatibilityCode: null,
    lastIncompatibility: null,
    widgetImportedWire: false,
    shellUsable: true,
    chatProceeded: false,
    wireCallCount: 0,
    lastWireName: null,
    capabilitiesLabel: "send_message",
    label: FACTORY_TEST_LABEL,
  };
}

export const hostState = writable<HostSnapshot>(initialSnapshot());

export function createHostRuntime(
  capabilities: CapabilitySet = { ...FACTORY_TEST_CURRENT_CAPABILITIES },
  producer_id = "producer:FACTORY-TEST",
): HostRuntime {
  return {
    wire: createWireClient(),
    capabilities,
    producer_id,
  };
}

export const hostRuntime = createHostRuntime();

function commit(next: HostSnapshot): HostSnapshot {
  hostState.set(next);
  return next;
}

function refuse(
  runtime: HostRuntime,
  event: CallerEventType,
  issuer: HostSnapshot["lastIssuer"],
  incompatibility: TypedIncompatibility,
): HostSnapshot {
  return commit(
    snapshotOf(runtime, {
      lastCallerEvent: event,
      lastIssuer: issuer,
      lastIncompatibilityCode: incompatibility.code,
      lastIncompatibility: paintIncompatibility(incompatibility),
    }),
  );
}

export function getHostState(): HostSnapshot {
  return get(hostState);
}

export function setProducerId(producerId: string): HostSnapshot {
  hostRuntime.producer_id = producerId;
  const current = get(hostState);
  return commit({ ...current, producerId });
}

export function applyMissingCapabilityFixture(): HostSnapshot {
  hostRuntime.capabilities = { ...FACTORY_TEST_MISSING_CAPABILITIES };
  hostRuntime.capabilities.send_message = true;
  const invoked = dispatchInvoke(FACTORY_TEST_GRANTED_OP, hostRuntime);
  const chatted = dispatchChat(
    {
      body: `${FACTORY_TEST_LABEL} home chat without instance`,
      product_session_ref: "psess:FACTORY-TEST",
    },
    hostRuntime,
  );
  if (!invoked.ok) {
    return commit(
      snapshotOf(hostRuntime, {
        lastCallerEvent: "submit_invoke",
        lastIssuer: "dispatchInvoke",
        lastIncompatibilityCode: invoked.incompatibility.code,
        lastIncompatibility: paintIncompatibility(invoked.incompatibility),
        chatProceeded: chatted.ok,
      }),
    );
  }
  return commit(
    snapshotOf(hostRuntime, {
      lastCallerEvent: "submit_invoke",
      lastIssuer: "dispatchInvoke",
      chatProceeded: chatted.ok,
    }),
  );
}

export function handleRequestInvoke(): HostSnapshot {
  const result = dispatchInvoke(FACTORY_TEST_GRANTED_OP, hostRuntime);
  if (!result.ok) {
    return refuse(
      hostRuntime,
      "request_invoke",
      "dispatchInvoke",
      result.incompatibility,
    );
  }
  return commit(
    snapshotOf(hostRuntime, {
      lastCallerEvent: "request_invoke",
      lastIssuer: "dispatchInvoke",
    }),
  );
}

export function handleSubmitInvoke(): HostSnapshot {
  const result = dispatchInvoke(FACTORY_TEST_GRANTED_OP, hostRuntime);
  if (!result.ok) {
    return refuse(
      hostRuntime,
      "submit_invoke",
      "dispatchInvoke",
      result.incompatibility,
    );
  }
  return commit(
    snapshotOf(hostRuntime, {
      lastCallerEvent: "submit_invoke",
      lastIssuer: "dispatchInvoke",
    }),
  );
}

export function handleSubmitChat(): HostSnapshot {
  const result = dispatchChat(
    {
      body: `${FACTORY_TEST_LABEL} composer chat`,
      product_session_ref: "psess:FACTORY-TEST",
    },
    hostRuntime,
  );
  if (!result.ok) {
    return refuse(
      hostRuntime,
      "submit_chat",
      "dispatchChat",
      result.incompatibility,
    );
  }
  return commit(
    snapshotOf(hostRuntime, {
      lastCallerEvent: "submit_chat",
      lastIssuer: "dispatchChat",
      chatProceeded: true,
    }),
  );
}

export function handleCancelJob(): HostSnapshot {
  const result = dispatchCancel(FACTORY_TEST_CANCEL, hostRuntime);
  if (!result.ok) {
    return refuse(
      hostRuntime,
      "cancel_job",
      "dispatchCancel",
      result.incompatibility,
    );
  }
  return commit(
    snapshotOf(hostRuntime, {
      lastCallerEvent: "cancel_job",
      lastIssuer: "dispatchCancel",
    }),
  );
}

export function handleCancelDisplay(): HostSnapshot {
  return commit(
    snapshotOf(hostRuntime, {
      lastCallerEvent: "cancel_display",
      lastIssuer: null,
    }),
  );
}

export function handleListMailbox(): HostSnapshot {
  const result = listMailbox(
    { product_session_ref: "psess:FACTORY-TEST" },
    hostRuntime,
  );
  if (!result.ok) {
    return refuse(hostRuntime, "list_mailbox", null, result.incompatibility);
  }
  return commit(
    snapshotOf(hostRuntime, {
      lastCallerEvent: "list_mailbox",
    }),
  );
}

export function claimTestProducer(): HostSnapshot {
  const claim = claimProducer({
    session: memoryKv(),
    locks: memoryLocks(),
    tabToken: mintTabToken(),
  });
  return setProducerId(claim.producer_id);
}
