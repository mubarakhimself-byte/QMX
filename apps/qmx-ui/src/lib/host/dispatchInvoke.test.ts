import { describe, expect, it } from "vitest";
import { FACTORY_TEST_CURRENT_CAPABILITIES } from "./capabilities";
import { FACTORY_TEST_GRANTED_OP, dispatchInvoke } from "./dispatchInvoke";
import { createHostRuntime } from "./runtime";

describe("dispatchInvoke", () => {
  it("is the only path that builds InvocationEnvelope and refuses without caller_kind", () => {
    const runtime = createHostRuntime(FACTORY_TEST_CURRENT_CAPABILITIES);
    const result = dispatchInvoke(FACTORY_TEST_GRANTED_OP, runtime);
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error("expected refuse");
    expect(result.incompatibility.code).toBe("caller_kind_unsupported");
    expect(result.incompatibility.hang).toBe(false);
    expect(result.envelope?.instance_id).toBe("instance:FACTORY-TEST");
    expect(result.envelope?.caller_kind).toBe("user");
    expect(result.envelope?.idempotency_key).toMatch(/^idem:/);
    expect(runtime.wire.transport.calls).toHaveLength(0);
  });

  it("requires instance_id and forbids caller_kind=widget", () => {
    const runtime = createHostRuntime({ caller_kind: true });
    const missingInstance = dispatchInvoke(
      { ...FACTORY_TEST_GRANTED_OP, instance_id: undefined },
      runtime,
    );
    expect(missingInstance.ok).toBe(false);
    if (!missingInstance.ok) {
      expect(missingInstance.incompatibility.code).toBe("instance_id_required");
    }
    const widget = dispatchInvoke(
      { ...FACTORY_TEST_GRANTED_OP, caller_kind: "widget" },
      runtime,
    );
    expect(widget.ok).toBe(false);
    if (!widget.ok) {
      expect(widget.incompatibility.code).toBe("caller_kind_forbidden");
    }
  });

  it("submits a wire public call once caller_kind is advertised", () => {
    const runtime = createHostRuntime({
      caller_kind: true,
      send_message: true,
    });
    const result = dispatchInvoke(FACTORY_TEST_GRANTED_OP, runtime);
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error("expected send");
    expect(result.value.issuer).toBe("dispatchInvoke");
    expect(result.value.sent).toBe(true);
    expect(result.value.envelope.call_depth).toBe(0);
    expect(runtime.wire.transport.calls[0]?.payload).toMatchObject({
      transport: "wire",
    });
  });
});
