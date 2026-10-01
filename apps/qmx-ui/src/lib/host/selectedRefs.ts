/**
 * Home/Authoring invoke gate (FR-UI-06; DEC-0463). Exactly one selected_refs
 * kind instance_id. Zero or many is INVALID_INPUT. The host does not guess
 * latest, first, or all. Envelope instance_id remains required on invoke.
 */
import { FACTORY_TEST_LABEL } from "$lib/bootstrap";
import {
  typedIncompatibility,
  type TypedIncompatibility,
} from "./capabilities";
import {
  FACTORY_TEST_GRANTED_OP,
  dispatchInvoke,
  type InvokeDeps,
  type InvokeRequest,
  type InvokeResult,
} from "./dispatchInvoke";

export type SelectedRef = {
  kind: string;
  value: string;
};

export type SelectedRefs = readonly SelectedRef[];

export const INSTANCE_ID_REF_KIND = "instance_id" as const;

export const FACTORY_TEST_HOME_INVOKE: InvokeRequest = {
  op_id: FACTORY_TEST_GRANTED_OP.op_id,
  op_version: FACTORY_TEST_GRANTED_OP.op_version,
  grant_id: FACTORY_TEST_GRANTED_OP.grant_id,
  contribution: FACTORY_TEST_GRANTED_OP.contribution,
  config_revision: FACTORY_TEST_GRANTED_OP.config_revision,
  effect_class: FACTORY_TEST_GRANTED_OP.effect_class,
  reconcile_policy: FACTORY_TEST_GRANTED_OP.reconcile_policy,
  input_hash: FACTORY_TEST_GRANTED_OP.input_hash,
  input: { label: FACTORY_TEST_LABEL },
  caller_kind: "user",
  caller_session_ref: "psess:H",
};

export const FACTORY_TEST_ONE_INSTANCE_REFS: SelectedRef[] = [
  { kind: INSTANCE_ID_REF_KIND, value: "instance:FACTORY-TEST-home" },
];

export const FACTORY_TEST_MANY_INSTANCE_REFS: SelectedRef[] = [
  { kind: INSTANCE_ID_REF_KIND, value: "instance:FACTORY-TEST-first" },
  { kind: INSTANCE_ID_REF_KIND, value: "instance:FACTORY-TEST-latest" },
  { kind: "template", value: "template:FACTORY-TEST" },
];

export function instanceIdRefs(refs: SelectedRefs): SelectedRef[] {
  return refs.filter((ref) => ref.kind === INSTANCE_ID_REF_KIND);
}

export function resolveSelectedInstanceId(
  refs: SelectedRefs,
):
  | { ok: true; instance_id: string }
  | { ok: false; incompatibility: TypedIncompatibility } {
  const instances = instanceIdRefs(refs);
  if (instances.length === 1) {
    return { ok: true, instance_id: instances[0].value };
  }
  return {
    ok: false,
    incompatibility: typedIncompatibility("INVALID_INPUT", {
      missing: instances.length === 0 ? "instance_id" : undefined,
      family: "command",
    }),
  };
}

export function invokeWithSelectedRefs(
  request: InvokeRequest,
  selectedRefs: SelectedRefs,
  deps: InvokeDeps,
): InvokeResult {
  const resolved = resolveSelectedInstanceId(selectedRefs);
  if (!resolved.ok) {
    return { ok: false, incompatibility: resolved.incompatibility };
  }
  return dispatchInvoke(
    { ...request, instance_id: resolved.instance_id },
    deps,
  );
}
