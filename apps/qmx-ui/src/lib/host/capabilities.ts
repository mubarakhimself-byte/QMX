/**
 * initialize advertised capabilities (AR-UI-06). Missing method is a typed
 * incompatibility (J-UI-13), never a hang and never a successful empty.
 */

export const INITIALIZE_CAPABILITY_NAMES = [
  "pairing",
  "list_mailbox",
  "cancel_job",
  "caller_kind",
  "stage_artifact",
  "transfer_artifact",
  "transfer_complete",
  "pack_ui_request",
  "get_pack_ui_request",
  "save_editor_draft",
  "get_editor_draft_head",
  "publish_editor_draft",
] as const;

export type InitializeCapabilityName =
  (typeof INITIALIZE_CAPABILITY_NAMES)[number];

/** Seed CT-40 command; Home send_message still proceeds without caller_kind. */
export type SeedCommandName = "send_message";

export type CapabilityName = InitializeCapabilityName | SeedCommandName;

export type CapabilityFamily = "command" | "query" | "initialize";

export type CapabilitySet = Partial<Record<CapabilityName, boolean>>;

export type IncompatibilityCode =
  | "caller_kind_unsupported"
  | "query_unavailable"
  | "command_unavailable"
  | "family_mismatch"
  | "instance_id_required"
  | "originating_session_required"
  | "caller_kind_forbidden";

export type TypedIncompatibility = {
  kind: "incompatibility";
  code: IncompatibilityCode;
  missing?: CapabilityName | "instance_id" | "originating_product_session_ref";
  family?: CapabilityFamily;
  hang: false;
  emptySuccess: false;
  shellUsable: true;
};

export const FACTORY_TEST_CURRENT_CAPABILITIES: CapabilitySet = {
  send_message: true,
  caller_kind: false,
  list_mailbox: false,
  cancel_job: false,
  pairing: false,
};

export const FACTORY_TEST_MISSING_CAPABILITIES: CapabilitySet = {
  send_message: false,
  caller_kind: false,
  list_mailbox: false,
  cancel_job: false,
  pairing: false,
};

export function hasCapability(
  caps: CapabilitySet,
  name: CapabilityName,
): boolean {
  return caps[name] === true;
}

export function typedIncompatibility(
  code: IncompatibilityCode,
  extra: {
    missing?: TypedIncompatibility["missing"];
    family?: CapabilityFamily;
  } = {},
): TypedIncompatibility {
  return {
    kind: "incompatibility",
    code,
    hang: false,
    emptySuccess: false,
    shellUsable: true,
    ...extra,
  };
}

export function requireCapability(
  caps: CapabilitySet,
  name: CapabilityName,
  family: CapabilityFamily,
): TypedIncompatibility | null {
  if (hasCapability(caps, name)) return null;
  if (name === "caller_kind") {
    return typedIncompatibility("caller_kind_unsupported", {
      missing: "caller_kind",
      family: "initialize",
    });
  }
  if (family === "query") {
    return typedIncompatibility("query_unavailable", {
      missing: name,
      family,
    });
  }
  if (family === "command") {
    return typedIncompatibility("command_unavailable", {
      missing: name,
      family,
    });
  }
  return typedIncompatibility("family_mismatch", { missing: name, family });
}

export function paintIncompatibility(value: TypedIncompatibility): string {
  const missing = value.missing ? ` missing=${value.missing}` : "";
  return `typed incompatibility ${value.code}${missing}. Not a hang. Not a successful empty. Shell remains usable.`;
}
