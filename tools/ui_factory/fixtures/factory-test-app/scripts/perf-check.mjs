#!/usr/bin/env node
if (process.env.QMX_UI_PERF_REQUIRED === "1") {
  console.error("perf: required by story but no measurement harness recorded");
  process.exit(2);
}
console.log("perf: not required for this unit");
