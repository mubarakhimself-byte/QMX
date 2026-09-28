// Dev-only facts the runtime gate asserts; no connection to the trading daemon.
import { registerCapabilities, registerStore } from "@reticlehq/browser";
import { get, writable } from "svelte/store";
import type { ChromeState } from "$lib/bootstrap";
import { hostState } from "$lib/host/runtime";
import { shellState } from "$lib/shell/shellState";

const runtime = writable({
  candidateSha: document
    .querySelector('meta[name="qmx-candidate-sha"]')
    ?.getAttribute("content"),
  chromeState: "" as ChromeState | "",
});
registerStore("qmx-bootstrap", {
  getState: () => get(runtime),
  subscribe: (listener) => runtime.subscribe(() => listener()),
});
registerStore("qmx-shell", {
  getState: () => get(shellState),
  subscribe: (listener) => shellState.subscribe(() => listener()),
});
registerStore("qmx-host", {
  getState: () => get(hostState),
  subscribe: (listener) => hostState.subscribe(() => listener()),
});
export function setBootstrapState(chromeState: ChromeState): void {
  runtime.update((value) => ({ ...value, chromeState }));
}
registerCapabilities({
  stores: ["qmx-bootstrap", "qmx-shell", "qmx-host"],
  testids: [
    "fixture-loading",
    "bootstrap-state",
    "bootstrap-skeleton",
    "rail-home",
    "rail-copilot",
    "rail-library",
    "rail-authoring",
    "destination-home",
    "destination-copilot",
    "destination-library",
    "destination-authoring",
    "rail-product-destinations",
    "factory-test-issuers",
    "widget-request-invoke",
    "fixture-missing-capability",
    "typed-incompatibility",
    "host-last-caller",
    "platform-rail",
  ],
  signals: [],
});
