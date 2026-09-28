// Dev-only facts the runtime gate asserts; no connection to the trading daemon.
import { registerCapabilities, registerStore } from "@reticlehq/browser";
import { get, writable } from "svelte/store";
import type { ChromeState } from "$lib/bootstrap";

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
export function setBootstrapState(chromeState: ChromeState): void {
  runtime.update((value) => ({ ...value, chromeState }));
}
registerCapabilities({
  stores: ["qmx-bootstrap"],
  testids: ["fixture-loading", "bootstrap-state", "bootstrap-skeleton"],
  signals: [],
});
