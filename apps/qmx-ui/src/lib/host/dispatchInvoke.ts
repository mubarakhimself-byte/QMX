/**
 * Unique invoke issuer. Only path that builds parent-AD-24 InvocationEnvelope.
 * Until Epic 60.3 caller_kind is advertised, pack invoke is typed
 * caller_kind_unsupported. There is no caller_kind=widget.
 */
import { FACTORY_TEST_LABEL } from "$lib/bootstrap";
import {
  requireCapability,
  typedIncompatibility,
  type CapabilitySet,
  type TypedIncompatibility,
} from "./capabilities";
import {
  mintIdempotencyKey,
  mintLogicalInvocationId,
  mintWireId,
} from "./producer";
import {
  isTypedIncompatibility,
  type HostWireClient,
  type WireAck,
} from "./wireClient";

export const CALLER_KINDS = ["user", "agent", "workflow"] as const;
export type CallerKind = (typeof CALLER_KINDS)[number];
export const FORBIDDEN_CALLER_KINDS = ["widget"] as const;

export type EffectClass =
  | "none"
  | "read"
  | "append-evidence"
  | "mutate-config"
  | "place-run"
  | "external-egress";

export type ReconcilePolicy =
  "query-then-decide" | "unknown-manual" | "never-retry";

export type InvocationEnvelope = {
  logical_invocation_id: string;
  attempt_id: number;
  op_id: string;
  op_version: number;
  contribution: { qualified_id: string; package_version: string };
  instance_id: string;
  config_revision: number;
  grant_id: string;
  effect_class: EffectClass;
  idempotency_key: string;
  reconcile_policy: ReconcilePolicy;
  input_hash: string;
  call_depth: 0;
  caller_kind: CallerKind;
  caller_session_ref?: string;
};

export type InvokeRequest = {
  op_id: string;
  op_version: number;
  instance_id?: string;
  grant_id: string;
  contribution: { qualified_id: string; package_version: string };
  config_revision: number;
  effect_class: EffectClass;
  reconcile_policy: ReconcilePolicy;
  /** Opaque hash supplied by the host; this client does not compute fp1. */
  input_hash: string;
  input?: Record<string, unknown>;
  caller_kind?: string;
  caller_session_ref?: string;
};

export type InvokeOk = {
  issuer: "dispatchInvoke";
  envelope: InvocationEnvelope;
  sent: boolean;
  ack?: WireAck;
};

export type InvokeResult =
  | { ok: true; value: InvokeOk }
  | {
      ok: false;
      incompatibility: TypedIncompatibility;
      envelope?: InvocationEnvelope;
    };

export type InvokeDeps = {
  producer_id: string;
  capabilities: CapabilitySet;
  wire: HostWireClient;
};

export const FACTORY_TEST_GRANTED_OP: InvokeRequest = {
  op_id: "qmx.factory_test.start",
  op_version: 1,
  instance_id: "instance:FACTORY-TEST",
  grant_id: "grant:FACTORY-TEST",
  contribution: {
    qualified_id: "factory-test:qmx-ui",
    package_version: "0.0.0",
  },
  config_revision: 0,
  effect_class: "read",
  reconcile_policy: "never-retry",
  input_hash: "FACTORY-TEST-input",
  input: { label: FACTORY_TEST_LABEL },
  caller_kind: "user",
  caller_session_ref: "psess:FACTORY-TEST",
};

function isCallerKind(value: string | undefined): value is CallerKind {
  return (
    value !== undefined && (CALLER_KINDS as readonly string[]).includes(value)
  );
}

export function buildInvocationEnvelope(
  request: InvokeRequest,
  producerId: string,
): InvocationEnvelope | TypedIncompatibility {
  if (
    request.caller_kind !== undefined &&
    (FORBIDDEN_CALLER_KINDS as readonly string[]).includes(request.caller_kind)
  ) {
    return typedIncompatibility("caller_kind_forbidden", {
      family: "initialize",
    });
  }
  const callerKind = isCallerKind(request.caller_kind)
    ? request.caller_kind
    : "user";
  if (!request.instance_id) {
    return typedIncompatibility("instance_id_required", {
      missing: "instance_id",
    });
  }
  const logical = mintLogicalInvocationId(producerId);
  const envelope: InvocationEnvelope = {
    logical_invocation_id: logical,
    attempt_id: 1,
    op_id: request.op_id,
    op_version: request.op_version,
    contribution: request.contribution,
    instance_id: request.instance_id,
    config_revision: request.config_revision,
    grant_id: request.grant_id,
    effect_class: request.effect_class,
    idempotency_key: mintIdempotencyKey(producerId, logical),
    reconcile_policy: request.reconcile_policy,
    input_hash: request.input_hash,
    call_depth: 0,
    caller_kind: callerKind,
  };
  if (request.caller_session_ref) {
    envelope.caller_session_ref = request.caller_session_ref;
  }
  return envelope;
}

export function dispatchInvoke(
  request: InvokeRequest,
  deps: InvokeDeps,
): InvokeResult {
  const built = buildInvocationEnvelope(request, deps.producer_id);
  if ("kind" in built) {
    return { ok: false, incompatibility: built };
  }
  const missingKind = requireCapability(
    deps.capabilities,
    "caller_kind",
    "initialize",
  );
  if (missingKind) {
    return { ok: false, incompatibility: missingKind, envelope: built };
  }
  const ack = deps.wire.submitPublicCall({
    producer_id: deps.producer_id,
    id: mintWireId(deps.producer_id),
    transport: "wire",
    envelope: built,
    payload: request.input ?? {},
  });
  if (isTypedIncompatibility(ack)) {
    return { ok: false, incompatibility: ack, envelope: built };
  }
  return {
    ok: true,
    value: { issuer: "dispatchInvoke", envelope: built, sent: true, ack },
  };
}
