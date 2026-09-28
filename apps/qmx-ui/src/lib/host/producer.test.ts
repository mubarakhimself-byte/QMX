import { describe, expect, it } from "vitest";
import {
  PRODUCER_SESSION_KEY,
  claimProducer,
  memoryKv,
  memoryLocks,
  mintCommandId,
  mintIdempotencyKey,
} from "./producer";

describe("producer_id per chrome tab", () => {
  it("mints one producer_id and reuses it on same-tab reload", () => {
    const session = memoryKv();
    const locks = memoryLocks();
    const first = claimProducer({
      session,
      locks,
      tabToken: "tab-1",
      mint: () => "producer:one",
    });
    expect(first.producer_id).toBe("producer:one");
    expect(first.source).toBe("fresh");
    expect(first.sharedLiveForbidden).toBe(true);
    const reload = claimProducer({
      session,
      locks,
      tabToken: "tab-1",
      mint: () => "producer:other",
    });
    expect(reload.producer_id).toBe("producer:one");
    expect(reload.source).toBe("same-tab-reload");
  });

  it("refuses to share a live producer_id with a cloned tab", () => {
    const locks = memoryLocks();
    const tab1 = claimProducer({
      session: memoryKv(),
      locks,
      tabToken: "tab-1",
      mint: () => "producer:live",
    });
    const clonedSession = memoryKv({
      [PRODUCER_SESSION_KEY]: tab1.producer_id,
    });
    const tab2 = claimProducer({
      session: clonedSession,
      locks,
      tabToken: "tab-2",
      mint: () => "producer:clone",
    });
    expect(tab2.source).toBe("cloned-replaced");
    expect(tab2.producer_id).toBe("producer:clone");
    expect(tab2.producer_id).not.toBe(tab1.producer_id);
  });

  it("keeps command_id unique per psess across tabs and idempotency_key invoke-only", () => {
    const cmdA = mintCommandId("psess:H", "producer:a", 1);
    const cmdB = mintCommandId("psess:H", "producer:b", 1);
    expect(cmdA).not.toBe(cmdB);
    expect(cmdA).toContain("psess:H");
    expect(mintIdempotencyKey("producer:a", "inv:1")).toMatch(/^idem:/);
  });
});
