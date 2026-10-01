/**
 * Host list_mailbox query. Missing capability is query_unavailable, not a
 * successful empty mailbox (FR-UI-37; J-UI-13).
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

export type ListMailboxRequest = {
  product_session_ref: string;
};

export type ListMailboxResult =
  | { ok: true; value: { query: "list_mailbox"; ack: WireAck } }
  | { ok: false; incompatibility: TypedIncompatibility };

export function listMailbox(
  request: ListMailboxRequest,
  deps: {
    producer_id: string;
    capabilities: CapabilitySet;
    wire: HostWireClient;
  },
): ListMailboxResult {
  const missing = requireCapability(deps.capabilities, "list_mailbox", "query");
  if (missing) return { ok: false, incompatibility: missing };
  const ack = deps.wire.sendQuery("list_mailbox", {
    producer_id: deps.producer_id,
    id: mintWireId(deps.producer_id),
    payload: { product_session_ref: request.product_session_ref },
  });
  if (isTypedIncompatibility(ack)) {
    return { ok: false, incompatibility: ack };
  }
  return { ok: true, value: { query: "list_mailbox", ack } };
}
