import { describe, expect, it } from "vitest";
import { FACTORY_TEST_CURRENT_CAPABILITIES } from "./capabilities";
import { FACTORY_TEST_GRANTED_OP } from "./dispatchInvoke";
import { createHostRuntime } from "./runtime";
import {
  FACTORY_TEST_HOME_INVOKE,
  FACTORY_TEST_MANY_INSTANCE_REFS,
  FACTORY_TEST_ONE_INSTANCE_REFS,
  instanceIdRefs,
  invokeWithSelectedRefs,
  resolveSelectedInstanceId,
} from "./selectedRefs";

describe("selected_refs instance_id gate", () => {
  it("does not carry instance_id on the Home invoke request", () => {
    expect(FACTORY_TEST_HOME_INVOKE).not.toHaveProperty("instance_id");
  });

  it("accepts exactly one selected_refs kind instance_id", () => {
    const resolved = resolveSelectedInstanceId(FACTORY_TEST_ONE_INSTANCE_REFS);
    expect(resolved.ok).toBe(true);
    if (!resolved.ok) throw new Error("expected one instance_id");
    expect(resolved.instance_id).toBe("instance:FACTORY-TEST-home");
  });

  it("types zero or many instance_id refs as INVALID_INPUT and does not guess", () => {
    const zero = resolveSelectedInstanceId([]);
    expect(zero.ok).toBe(false);
    if (zero.ok) throw new Error("expected refuse");
    expect(zero.incompatibility.code).toBe("INVALID_INPUT");
    expect(zero.incompatibility.hang).toBe(false);

    const many = resolveSelectedInstanceId(FACTORY_TEST_MANY_INSTANCE_REFS);
    expect(instanceIdRefs(FACTORY_TEST_MANY_INSTANCE_REFS)).toHaveLength(2);
    expect(many.ok).toBe(false);
    if (many.ok) throw new Error("expected refuse");
    expect(many.incompatibility.code).toBe("INVALID_INPUT");
  });

  it("refuses Home invoke without guessing first, latest, or all", () => {
    const runtime = createHostRuntime(FACTORY_TEST_CURRENT_CAPABILITIES);
    const zero = invokeWithSelectedRefs(
      { ...FACTORY_TEST_GRANTED_OP, instance_id: "instance:must-not-guess" },
      [],
      runtime,
    );
    expect(zero.ok).toBe(false);
    if (!zero.ok) expect(zero.incompatibility.code).toBe("INVALID_INPUT");
    expect(runtime.wire.transport.calls).toHaveLength(0);

    const many = invokeWithSelectedRefs(
      FACTORY_TEST_HOME_INVOKE,
      FACTORY_TEST_MANY_INSTANCE_REFS,
      runtime,
    );
    expect(many.ok).toBe(false);
    if (!many.ok) expect(many.incompatibility.code).toBe("INVALID_INPUT");
    expect(runtime.wire.transport.calls).toHaveLength(0);
  });

  it("uses the single selected instance_id as envelope instance_id", () => {
    const runtime = createHostRuntime({
      caller_kind: true,
      send_message: true,
    });
    const result = invokeWithSelectedRefs(
      FACTORY_TEST_HOME_INVOKE,
      FACTORY_TEST_ONE_INSTANCE_REFS,
      runtime,
    );
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error("expected send");
    expect(result.value.envelope.instance_id).toBe(
      "instance:FACTORY-TEST-home",
    );
    expect(result.value.issuer).toBe("dispatchInvoke");
  });
});
