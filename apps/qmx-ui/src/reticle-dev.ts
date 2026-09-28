// Dev-only facts the runtime gate asserts; no connection to the trading daemon.
import { registerCapabilities, registerStore } from "@reticlehq/browser";

registerStore("qmx-bootstrap", () => ({
  candidateSha: document
    .querySelector('meta[name="qmx-candidate-sha"]')
    ?.getAttribute("content"),
  chromeState: document
    .querySelector('[data-testid="bootstrap-state"]')
    ?.getAttribute("data-state"),
}));
registerCapabilities({
  stores: ["qmx-bootstrap"],
  testids: ["fixture-loading", "bootstrap-state", "bootstrap-skeleton"],
  signals: [],
});
