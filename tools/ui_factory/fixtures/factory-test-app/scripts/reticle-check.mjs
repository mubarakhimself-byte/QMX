#!/usr/bin/env node
// FACTORY-TEST Reticle wrapper. unknown / missing are not passes.
const forced = process.env.QMX_RETICLE_VERDICT || "";
if (forced) {
  if (forced === "yes") {
    console.log("reticle: forced yes (factory-test harness)");
    process.exit(0);
  }
  console.error("reticle: forced", forced);
  process.exit(forced === "unknown" || forced === "missing" ? 2 : 1);
}
console.error(
  "reticle: MCP reticle_act_and_wait/reticle_assert required for user-facing promotion; CLI did not produce a verdict"
);
process.exit(2);
