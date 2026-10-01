/**
 * Unique wire client. Widgets never import this module. Client-bit updates
 * must not write daemon journal files (J-UI-14). Live CT-40 serving is
 * Epic 41–42, not this story.
 */
import {
  typedIncompatibility,
  type CapabilityFamily,
  type TypedIncompatibility,
} from "./capabilities";

export const LIVE_CT40_SERVER_AT_INSPECT = false;

export type SeedCommandName = "send_message";
export type AddableCommandName = "cancel_job";
export type AddableQueryName = "list_mailbox";

export type WireCommandName = SeedCommandName | AddableCommandName;
export type WireQueryName = AddableQueryName;

const COMMAND_NAMES = new Set<string>(["send_message", "cancel_job"]);
const QUERY_NAMES = new Set<string>(["list_mailbox"]);

export type WireCall = {
  family: CapabilityFamily;
  name: string;
  producer_id: string;
  id: string;
  payload: Record<string, unknown>;
};

export type WireAck = {
  ok: true;
  recorded: true;
  hang: false;
  sqliteWrite: false;
};

export type WireTransport = {
  calls: WireCall[];
  send(call: WireCall): WireAck;
};

export function recordingTransport(): WireTransport {
  const calls: WireCall[] = [];
  return {
    calls,
    send(call) {
      calls.push(call);
      return { ok: true, recorded: true, hang: false, sqliteWrite: false };
    },
  };
}

export type HostWireClient = {
  transport: WireTransport;
  sendCommand(
    name: WireCommandName,
    envelope: {
      producer_id: string;
      id: string;
      payload: Record<string, unknown>;
    },
  ): WireAck | TypedIncompatibility;
  sendQuery(
    name: WireQueryName,
    envelope: {
      producer_id: string;
      id: string;
      payload: Record<string, unknown>;
    },
  ): WireAck | TypedIncompatibility;
  submitPublicCall(call: {
    producer_id: string;
    id: string;
    transport: "wire";
    envelope: Record<string, unknown>;
    payload: Record<string, unknown>;
  }): WireAck;
};

function familyMismatch(
  name: string,
  family: CapabilityFamily,
): TypedIncompatibility {
  return typedIncompatibility("family_mismatch", {
    family,
    missing:
      name === "list_mailbox"
        ? "list_mailbox"
        : name === "cancel_job"
          ? "cancel_job"
          : name === "send_message"
            ? "send_message"
            : undefined,
  });
}

export function createWireClient(
  transport: WireTransport = recordingTransport(),
): HostWireClient {
  return {
    transport,
    sendCommand(name, envelope) {
      if (QUERY_NAMES.has(name)) return familyMismatch(name, "command");
      if (!COMMAND_NAMES.has(name)) return familyMismatch(name, "command");
      return transport.send({
        family: "command",
        name,
        producer_id: envelope.producer_id,
        id: envelope.id,
        payload: envelope.payload,
      });
    },
    sendQuery(name, envelope) {
      if (COMMAND_NAMES.has(name)) return familyMismatch(name, "query");
      if (!QUERY_NAMES.has(name)) return familyMismatch(name, "query");
      return transport.send({
        family: "query",
        name,
        producer_id: envelope.producer_id,
        id: envelope.id,
        payload: envelope.payload,
      });
    },
    submitPublicCall(call) {
      return transport.send({
        family: "command",
        name: "public_call",
        producer_id: call.producer_id,
        id: call.id,
        payload: {
          transport: call.transport,
          envelope: call.envelope,
          payload: call.payload,
        },
      });
    },
  };
}

export function isTypedIncompatibility(
  value: WireAck | TypedIncompatibility,
): value is TypedIncompatibility {
  return "kind" in value && value.kind === "incompatibility";
}
