# Study 03 review and limits

Status: source-reviewed design prototype. Native Codex controls are disabled in the current computer-use interface, so its plus menu was not clicked. Earlier local-file browser navigation was policy-blocked; no workaround or alternate browser route was used to verify these studies. User-supplied screenshots are evidence of what was on the user's screen, not a successful agent interaction test.

## Source grounding
- Five supplied PNGs copied without modification and hashed.
- The screenshots identify the tabbed work area, launcher, composer thumbnails, context panel and conversation navigator. Expanded plus-menu contents are not visible.
- Local installed plugin metadata inspected by a lower-end agent. Package/skill/connector/MCP distinctions are grounded there; composer semantics are not. See plugin-reference.md.
- BMAD UX skill/config/spec inspected for design-system guidance. No formal workflow finalization, color proposal or new architectural decision.

## Verification boundary
Inline JavaScript extracted from study 03 and the revised historical study 02 passes Node `--check` (exit 0). New study Markdown links resolve; no external script or stylesheet dependencies were found in either file. This does not establish actual browser rendering, keyboard operation, responsive geometry or Reticle success. No production QMX UI code has been changed.

## Scenarios to exercise
- App Overview → expand dataset → discuss → locate in Library → return to preserved detail → close detail to Overview.
- Filter Dataset, search, inspect snapshot identity and unavailable source. An unavailable item cannot silently be referenced.
- Reference a dataset/result/workflow/app and inspect the different chip identity and action explanation. Open app must remain a distinct action.
- Plus → Tools & plugins → select Research tools. Selection adds a capability chip; no reference chip or automatic execution. Unselecting preserves availability.
- Write/send fixture message, remove next-message context, retain sent context record; tool selection remains until explicitly removed.
- Open saved result in work area, switch document/object tabs, switch bottom/side docking, close without erasing conversation or app state.
- Hide/show app copilot; draft/context/history retained. Library selection and return preserve intended app context.
- Check focus after popover open/close, keyboard paths, screen-reader names, search focus and wide/narrow stacking.

Remaining limitations: one app and one app conversation only; fixture data; no filesystem picker, upload, model, tools, dataset rows, run execution, version picker, permissions, installation, real connections, persistence, authoring or conversation navigator. The wireframe is not a Codex clone and does not prove interoperability with Grok's SDK.
