/**
 * Unique cancel issuer. Issues addable cancel_job (chrome contract). Not seed
 * stop_run, not a second dispatchInvoke, not ConversationPane.cancel_display.
 * Does not implement the daemon command (Epic 73).
 */
import {
  requireCapability,
  typedIncompatibility,
  type CapabilitySet,
  type TypedIncompatibility,
} from "./capabilities";
import { mintCommandId, mintWireId, nextCommandSeq } from "./producer";
import {
  isTypedIncompatibility,
  type HostWireClient,
  type WireAck,
} from "./wireClient";

export type JobHandleState =
  | "queued"
  | "running"
  | "done"
  | "failed"
  | "cancelled"
  | "aborted"
  | "unknown";

export type CancelRequest = {
  handle_id: string;
  logical_run_id: string;
  attempt_id: number;
  expected_state: JobHandleState;
  originating_product_session_ref?: string;
};

export type CancelJobPayload = {
  handle_id: string;
  logical_run_id: string;
  attempt_id: number;
  command_id: string;
  expected_state: JobHandleState;
  originating_product_session_ref: string;
};

export type CancelOk = {
  issuer: "dispatchCancel";
  method: "cancel_job";
  payload: CancelJobPayload;
  ack: WireAck;
};

export type CancelResult =
  | { ok: true; value: CancelOk }
  | { ok: false; incompatibility: TypedIncompatibility };

export type CancelDeps = {
  producer_id: string;
  capabilities: CapabilitySet;
  wire: HostWireClient;
};

export const FACTORY_TEST_CANCEL: CancelRequest = {
  handle_id: "job:FACTORY-TEST",
  logical_run_id: "run:FACTORY-TEST",
  attempt_id: 1,
  expected_state: "queued",
  originating_product_session_ref: "psess:FACTORY-TEST",
};

export function dispatchCancel(
  request: CancelRequest,
  deps: CancelDeps,
): CancelResult {
  const missing = requireCapability(deps.capabilities, "cancel_job", "command");
  if (missing) return { ok: false, incompatibility: missing };
  if (!request.originating_product_session_ref) {
    return {
      ok: false,
      incompatibility: typedIncompatibility("originating_session_required", {
        missing: "originating_product_session_ref",
        family: "command",
      }),
    };
  }
  const psess = request.originating_product_session_ref;
  const payload: CancelJobPayload = {
    handle_id: request.handle_id,
    logical_run_id: request.logical_run_id,
    attempt_id: request.attempt_id,
    command_id: mintCommandId(psess, deps.producer_id, nextCommandSeq(psess)),
    expected_state: request.expected_state,
    originating_product_session_ref: psess,
  };
  const ack = deps.wire.sendCommand("cancel_job", {
    producer_id: deps.producer_id,
    id: mintWireId(deps.producer_id),
    payload,
  });
  if (isTypedIncompatibility(ack)) {
    return { ok: false, incompatibility: ack };
  }
  return {
    ok: true,
    value: { issuer: "dispatchCancel", method: "cancel_job", payload, ack },
  };
}
