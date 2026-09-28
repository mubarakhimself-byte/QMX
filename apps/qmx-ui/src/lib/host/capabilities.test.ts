import { describe, expect, it } from "vitest";
import {
  FACTORY_TEST_CURRENT_CAPABILITIES,
  paintIncompatibility,
  requireCapability,
} from "./capabilities";

describe("capabilities", () => {
  it("types missing caller_kind as caller_kind_unsupported", () => {
    const miss = requireCapability(
      FACTORY_TEST_CURRENT_CAPABILITIES,
      "caller_kind",
      "initialize",
    );
    expect(miss?.code).toBe("caller_kind_unsupported");
    expect(miss?.hang).toBe(false);
    expect(miss?.emptySuccess).toBe(false);
    expect(miss?.shellUsable).toBe(true);
  });

  it("types missing list_mailbox as query_unavailable, not empty success", () => {
    const miss = requireCapability(
      FACTORY_TEST_CURRENT_CAPABILITIES,
      "list_mailbox",
      "query",
    );
    expect(miss?.code).toBe("query_unavailable");
    expect(miss?.missing).toBe("list_mailbox");
    expect(paintIncompatibility(miss!)).toMatch(/Not a hang/);
  });

  it("types missing cancel_job as command_unavailable", () => {
    const miss = requireCapability(
      FACTORY_TEST_CURRENT_CAPABILITIES,
      "cancel_job",
      "command",
    );
    expect(miss?.code).toBe("command_unavailable");
    expect(miss?.missing).toBe("cancel_job");
  });

  it("lets seed send_message proceed while caller_kind is absent", () => {
    expect(
      requireCapability(
        FACTORY_TEST_CURRENT_CAPABILITIES,
        "send_message",
        "command",
      ),
    ).toBeNull();
  });
});
