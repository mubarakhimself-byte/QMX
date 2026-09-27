#!/usr/bin/env node
// FACTORY-TEST: missing backend is incomplete, never a silent pass.
if (process.env.QMX_UI_BACKEND_REQUIRED === "1") {
  const url = process.env.QMX_UI_BACKEND_URL || "";
  if (!url) {
    console.error("contract: backend required but QMX_UI_BACKEND_URL empty");
    process.exit(2);
  }
  try {
    const res = await fetch(url);
    if (!res.ok) {
      console.error("contract: backend status", res.status);
      process.exit(1);
    }
    const body = await res.text();
    if (!body.includes("revision") && !body.includes("qmb")) {
      console.error("contract: backend did not identify itself");
      process.exit(1);
    }
  } catch (err) {
    console.error("contract: backend unreachable", err);
    process.exit(2);
  }
}
console.log("contract: fixture-only (not product backend integration)");
