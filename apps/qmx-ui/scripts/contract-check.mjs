#!/usr/bin/env node
if (process.env.QMX_UI_BACKEND_REQUIRED === "1") {
  console.error(
    "contract: live CT-40 is adoption of Epic 41–42; Story 66.1 does not claim a live daemon",
  );
  process.exit(2);
}
console.log(
  "contract: isolated scaffold only; inspect SHA had no live CT-40 server (DEC-0507)",
);
