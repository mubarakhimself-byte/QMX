import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { dispatchCancel, FACTORY_TEST_CANCEL } from "./dispatchCancel";
import { resetCommandSeqForTests } from "./producer";
import { createHostRuntime } from "./runtime";

const here = dirname(fileURLToPath(import.meta.url));

describe("dispatchCancel", () => {
  it("is typed incompatibility when cancel_job is missing", () => {
    const runtime = createHostRuntime();
    const result = dispatchCancel(FACTORY_TEST_CANCEL, runtime);
    expect(result.ok).toBe(false);
    if (result.ok) throw new Error("expected refuse");
    expect(result.incompatibility.code).toBe("command_unavailable");
    expect(result.incompatibility.missing).toBe("cancel_job");
    expect(result.incompatibility.hang).toBe(false);
    expect(runtime.wire.transport.calls).toHaveLength(0);
  });

  it("issues cancel_job with command_id unique per psess, not stop_run", () => {
    resetCommandSeqForTests();
    const runtime = createHostRuntime({ cancel_job: true });
    runtime.producer_id = "producer:a";
    const first = dispatchCancel(FACTORY_TEST_CANCEL, runtime);
    const other = createHostRuntime({ cancel_job: true });
    other.producer_id = "producer:b";
    const second = dispatchCancel(FACTORY_TEST_CANCEL, other);
    expect(first.ok).toBe(true);
    expect(second.ok).toBe(true);
    if (!first.ok || !second.ok) throw new Error("expected send");
    expect(first.value.method).toBe("cancel_job");
    expect(first.value.payload.command_id).not.toBe(
      second.value.payload.command_id,
    );
    expect(first.value.payload).not.toHaveProperty("idempotency_key");
    const src = readFileSync(join(here, "dispatchCancel.ts"), "utf8");
    expect(src).not.toMatch(/sendCommand\(["']stop_run/);
    expect(src).not.toMatch(/from ["'].*dispatchInvoke/);
    expect(src).not.toMatch(/dispatchInvoke\(/);
    expect(src).not.toMatch(/cancel_display\(/);
  });

  it("refuses UI cancel when originating_product_session_ref is absent", () => {
    const runtime = createHostRuntime({ cancel_job: true });
    const result = dispatchCancel(
      { ...FACTORY_TEST_CANCEL, originating_product_session_ref: undefined },
      runtime,
    );
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.incompatibility.code).toBe("originating_session_required");
    }
  });
});
