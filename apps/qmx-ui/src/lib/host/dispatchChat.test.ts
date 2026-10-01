import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { chatPayloadHasEnvelopeKeys, dispatchChat } from "./dispatchChat";
import { createHostRuntime } from "./runtime";

const here = dirname(fileURLToPath(import.meta.url));

describe("dispatchChat", () => {
  it("issues send_message without instance_id or InvocationEnvelope keys", () => {
    const runtime = createHostRuntime();
    const result = dispatchChat(
      {
        body: "hello",
        product_session_ref: "psess:H",
        instance_id: "instance:must-not-be-required",
        grant_id: "grant:ignored",
        idempotency_key: "idem:ignored",
        caller_kind: "user",
        command_id: "cmd:ignored",
      },
      runtime,
    );
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error("expected send");
    expect(result.value.method).toBe("send_message");
    expect(result.value.payload).not.toHaveProperty("instance_id");
    expect(result.value.payload).not.toHaveProperty("idempotency_key");
    expect(result.value.payload).not.toHaveProperty("command_id");
    expect(chatPayloadHasEnvelopeKeys(result.value.payload)).toBe(false);
    expect(runtime.wire.transport.calls[0]?.name).toBe("send_message");
  });

  it("does not import or call dispatchInvoke", () => {
    const src = readFileSync(join(here, "dispatchChat.ts"), "utf8");
    expect(src).not.toMatch(/from ["'].*dispatchInvoke/);
    expect(src).not.toMatch(/buildInvocationEnvelope/);
    expect(src).not.toMatch(/idempotency_key:/);
  });

  it("refuses when send_message is missing, without hanging", () => {
    const runtime = createHostRuntime({ send_message: false });
    const result = dispatchChat({ body: "hello" }, runtime);
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error("expected refuse");
    expect(result.incompatibility.code).toBe("command_unavailable");
    expect(result.incompatibility.hang).toBe(false);
    expect(runtime.wire.transport.calls).toHaveLength(0);
  });
});
