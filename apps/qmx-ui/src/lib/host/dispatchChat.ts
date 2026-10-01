/**
 * Unique chat issuer. Issues mailbox send_message. Does not build an
 * InvocationEnvelope, does not require instance_id, and does not call
 * dispatchInvoke (DEC-0484).
 */
import {
  requireCapability,
  type CapabilitySet,
  type TypedIncompatibility,
} from "./capabilities";
import { mintWireId } from "./producer";
import {
  isTypedIncompatibility,
  type HostWireClient,
  type WireAck,
} from "./wireClient";

export type MailboxKind =
  "handoff" | "reply" | "notify" | "status" | "question";

export type SendMessagePayload = {
  product_session_ref?: string;
  body: string;
  kind: MailboxKind;
};

export type ChatRequest = {
  body: string;
  product_session_ref?: string;
  kind?: MailboxKind;
  instance_id?: string;
  grant_id?: string;
  op_id?: string;
  idempotency_key?: string;
  caller_kind?: string;
  command_id?: string;
};

export type ChatOk = {
  issuer: "dispatchChat";
  method: "send_message";
  producer_id: string;
  id: string;
  payload: SendMessagePayload;
  ack: WireAck;
};

export type ChatResult =
  | { ok: true; value: ChatOk }
  | { ok: false; incompatibility: TypedIncompatibility };

export type ChatDeps = {
  producer_id: string;
  capabilities: CapabilitySet;
  wire: HostWireClient;
};

const ENVELOPE_KEYS = [
  "logical_invocation_id",
  "grant_id",
  "op_id",
  "instance_id",
  "idempotency_key",
  "caller_kind",
  "input_hash",
  "command_id",
] as const;

export function dispatchChat(request: ChatRequest, deps: ChatDeps): ChatResult {
  const missing = requireCapability(
    deps.capabilities,
    "send_message",
    "command",
  );
  if (missing) return { ok: false, incompatibility: missing };
  const payload: SendMessagePayload = {
    body: request.body,
    kind: request.kind ?? "handoff",
  };
  if (request.product_session_ref) {
    payload.product_session_ref = request.product_session_ref;
  }
  const id = mintWireId(deps.producer_id);
  const ack = deps.wire.sendCommand("send_message", {
    producer_id: deps.producer_id,
    id,
    payload,
  });
  if (isTypedIncompatibility(ack)) {
    return { ok: false, incompatibility: ack };
  }
  return {
    ok: true,
    value: {
      issuer: "dispatchChat",
      method: "send_message",
      producer_id: deps.producer_id,
      id,
      payload,
      ack,
    },
  };
}

export function chatPayloadHasEnvelopeKeys(payload: object): boolean {
  return ENVELOPE_KEYS.some((key) => key in payload);
}
