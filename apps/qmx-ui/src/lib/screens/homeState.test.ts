import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it } from "vitest";
import { chatPayloadHasEnvelopeKeys } from "../host/dispatchChat";
import {
  ATTENTION_LIST_AT_INSPECT,
  HOME_CHROME_AT_INSPECT,
  INSPECT_SHA,
} from "../inspect";
import { createHostRuntime } from "../host/runtime";
import { PRODUCT_SESSION_PROFILES } from "../shell/destinations";
import {
  FACTORY_TEST_OBSERVATION,
  FACTORY_TEST_QUEUED_JOB,
  HOME_CHROME_STATES,
  HOME_PRODUCT_SESSION_REF,
  HOME_RECONNECT_PLAN,
  HOME_SESSION,
  applyHomeFixture,
  cancelHomeJob,
  getHomeState,
  homeStateCopy,
  reconnectHome,
  resetHomeState,
  resumeHome,
  sendHomeChat,
  setHomeChromeState,
  submitHomeInvoke,
} from "./homeState";

const srcRoot = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

afterEach(() => {
  resetHomeState();
});

describe("Home attention chrome", () => {
  it("proves Home after this story and absent at inspect", () => {
    expect(INSPECT_SHA).toBe("34c148be404a375cbfd79fd4ce6997452e4f1d20");
    expect(HOME_CHROME_AT_INSPECT).toBe(false);
    expect(ATTENTION_LIST_AT_INSPECT).toBe(false);
    expect(existsSync(join(srcRoot, "lib/screens/Home.svelte"))).toBe(true);
    expect(existsSync(join(srcRoot, "lib/shell/AttentionList.svelte"))).toBe(
      true,
    );
    const home = readFileSync(join(srcRoot, "lib/screens/Home.svelte"), "utf8");
    const state = readFileSync(
      join(srcRoot, "lib/screens/homeState.ts"),
      "utf8",
    );
    expect(home).toContain('data-testid="destination-home"');
    expect(home).toContain("sendHomeChat");
    expect(home).not.toContain("destination-copilot");
    expect(home).not.toMatch(/from ["']qmb/);
    expect(state).toContain("dispatchChat");
    expect(state).not.toMatch(/from ["'][^"']*wireClient/);
  });

  it("keeps Home independent of Copilot with authoring profile only", () => {
    const snapshot = getHomeState();
    expect(snapshot.profile).toBe("authoring");
    expect(snapshot.isCopilot).toBe(false);
    expect(HOME_SESSION.app_instance_id).toBeNull();
    expect(PRODUCT_SESSION_PROFILES).toEqual(["authoring", "app-use"]);
    expect(HOME_CHROME_STATES).toEqual([
      "empty",
      "loading",
      "unavailable",
      "failed",
      "reconnecting",
      "stale",
      "unknown",
      "populated",
    ]);
  });

  it("sends Home chat through dispatchChat without minting an instance", () => {
    const runtime = createHostRuntime();
    const snapshot = sendHomeChat("hello from Home", runtime);
    expect(snapshot.chatProceeded).toBe(true);
    expect(snapshot.lastIssuer).toBe("dispatchChat");
    expect(snapshot.appInstanceId).toBeNull();
    expect(snapshot.mintedSyntheticInstance).toBe(false);
    const call = runtime.wire.transport.calls[0];
    expect(call?.name).toBe("send_message");
    expect(call?.payload).not.toHaveProperty("instance_id");
    expect(call?.payload).toMatchObject({
      product_session_ref: HOME_PRODUCT_SESSION_REF,
      body: "hello from Home",
    });
    expect(chatPayloadHasEnvelopeKeys(call?.payload ?? {})).toBe(false);
  });

  it("refuses invoke with zero or many instance_id refs as INVALID_INPUT", () => {
    const runtime = createHostRuntime();
    const zero = submitHomeInvoke(runtime);
    expect(zero.lastIncompatibilityCode).toBe("INVALID_INPUT");
    expect(zero.guessedInstance).toBe(false);
    expect(zero.selectedInstanceRefCount).toBe(0);
    expect(runtime.wire.transport.calls).toHaveLength(0);

    applyHomeFixture("selected-refs-many");
    const many = submitHomeInvoke(runtime);
    expect(many.selectedInstanceRefCount).toBe(2);
    expect(many.lastIncompatibilityCode).toBe("INVALID_INPUT");
    expect(many.guessedInstance).toBe(false);
    expect(runtime.wire.transport.calls).toHaveLength(0);
  });

  it("keeps loading empty unavailable failed reconnecting stale unknown distinct", () => {
    expect(new Set(HOME_CHROME_STATES).size).toBe(HOME_CHROME_STATES.length);
    expect(homeStateCopy("reconnecting")).toMatch(/Distinct from failed/);
    expect(homeStateCopy("unknown")).toMatch(/Not failed/);
    expect(homeStateCopy("empty")).toMatch(/One action/);
    expect(HOME_RECONNECT_PLAN.kind).toBe("query");
    expect(HOME_RECONNECT_PLAN.replay_intent).toBe(false);
    expect(HOME_RECONNECT_PLAN.implies_approval).toBe(false);
    expect(HOME_RECONNECT_PLAN.initialize.same_producer_id).toBe(true);

    setHomeChromeState("unknown");
    expect(getHomeState().unknownPaintedAsFailed).toBe(false);
    expect(getHomeState().rows[0]).toMatchObject({
      jobState: "unknown",
      paintedAsFailed: false,
    });

    setHomeChromeState("failed");
    expect(getHomeState().chromeState).toBe("failed");
    expect(getHomeState().chromeState).not.toBe("reconnecting");
  });

  it("treats observation as not a fourth product and not cancel authority", () => {
    setHomeChromeState("populated");
    const snapshot = getHomeState();
    expect(snapshot.observationIsProduct).toBe(false);
    expect(snapshot.observationIsCancelAuthority).toBe(false);
    expect(FACTORY_TEST_OBSERVATION.observation.cancelAuthority).toBe(false);
    expect(FACTORY_TEST_OBSERVATION.observation.fourthProduct).toBe(false);
    expect(FACTORY_TEST_OBSERVATION.observation.authorizesLive).toBe(false);
    expect(FACTORY_TEST_OBSERVATION.observation.commandTarget).toBe(false);
    const before = cancelHomeJob(FACTORY_TEST_OBSERVATION, createHostRuntime());
    expect(before.lastIssuer).toBeNull();
  });

  it("reconnects as a query and does not treat missing list_mailbox as empty", () => {
    const runtime = createHostRuntime();
    setHomeChromeState("reconnecting");
    const snapshot = reconnectHome(runtime);
    expect(snapshot.chromeState).toBe("reconnecting");
    expect(snapshot.chromeState).not.toBe("failed");
    expect(snapshot.lastIncompatibilityCode).toBe("query_unavailable");
    expect(snapshot.mailboxEmptySuccess).toBe(false);
    expect(runtime.wire.transport.calls).toHaveLength(0);
    expect(HOME_RECONNECT_PLAN.replay_intent).toBe(false);
  });

  it("resumes an existing psess or JobHandle without invoking", () => {
    const runtime = createHostRuntime();
    const snapshot = resumeHome(FACTORY_TEST_QUEUED_JOB.id);
    expect(snapshot.lastResumeTarget).toBe("job:FACTORY-TEST-queued");
    expect(snapshot.lastIssuer).toBeNull();
    expect(runtime.wire.transport.calls).toHaveLength(0);
  });
});
