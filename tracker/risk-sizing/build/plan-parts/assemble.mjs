#!/usr/bin/env node
// Builds ../UNIT-PLAN.md from 00-head.md, the phase files and 90-tail.md.
// Expands the standard blocks, checks every dependency points at an earlier PR,
// and generates the dispatch table and the shared-files appendix.
// Run: node assemble.mjs  (then: node <poteto-mode>/scripts/check-plan.mjs ../UNIT-PLAN.md)
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(here, "..", "UNIT-PLAN.md");
const RULE =
	"Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.";
const ID = /\b(A\d{1,2}[a-d]?|B\d{1,2}[a-c]?|C-\d{2}[a-e]?)\b/g;

const phaseFiles = fs
	.readdirSync(here)
	.filter((f) => /^\d\d-phase-.*\.md$/.test(f))
	.sort();
const head = fs.readFileSync(path.join(here, "00-head.md"), "utf8");
const tail = fs.readFileSync(path.join(here, "90-tail.md"), "utf8");

const problems = [];
const prs = [];

function expandSection(lines, id) {
	const slug = id.toLowerCase().replace(/-/g, "");
	const outLines = [];
	for (const line of lines) {
		if (line === "**Verify, unit.**") outLines.push(`**Verify, unit.** ${RULE}`);
		else if (line === "**Verify, live.**")
			outLines.push(
				`**Verify, live.** ${RULE} Ten lanes on \`haiku\` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them.`,
			);
		else if (line === "**Verify, perf.**") outLines.push(`**Verify, perf.** ${RULE}`);
		else if (line === "@lane1")
			outLines.push(
				`- [ ] Lane 1. Regression against the parent. The coordinator runs \`just ci\` at the PR head under \`D:/QMX-worktrees/.ci-lock\`, with \`TEMP\` and \`TMP\` on \`D:/Temp\`, then reruns any failing test at the parent. Save \`${slug}-ci.log\`. Pass when the head fails nothing the parent passes.`,
			);
		else if (line === "@menu") {
			outLines.push(
				`- [ ] Lane 7. Grep every lane log of this PR for key, token and password values. Save \`${slug}-leak.log\`. Pass when none appears.`,
				`- [ ] Lane 8. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. Save \`${slug}-boot.log\`. Pass when the host answers and stops clean.`,
				`- [ ] Lane 9. Run the PR's new tests three times in a row. Save \`${slug}-repeat.log\`. Pass when the three runs agree.`,
				`- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. Save \`${slug}-processes.log\`. Pass when no \`qmx_host\`, \`claude\`, \`node\` or lane process is left.`,
			);
		} else if (line.startsWith("**Review gate.** ") && !line.startsWith("**Review gate.** None.")) {
			const rest = line.slice("**Review gate.** ".length);
			outLines.push(`**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. ${rest}`);
			outLines.push("");
			outLines.push(
				`- [ ] A fresh Opus reviewer agent (\`model: opus\`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact named above. It writes \`review/${slug}-check-<head8>.md\`, first line CLEAN or NOT CLEAN.`,
			);
			outLines.push(
				"- [ ] No screenshot or video is made, because no PR in this program changes a screen (ruling 45). The operator reviews the whole stack when he lands it.",
			);
		} else if (line === "@merge") {
			outLines.push(
				"**Merge.**",
				"",
				"- [ ] The CLEAN verdict at the exact head, or after the one fix round.",
				"- [ ] Lows in `lows.md`, new findings in `BACKLOG.md` and `IDEAS.md`, the verdict, head, parent and patch-id in `ledger.tsv`.",
				"- [ ] Appended to the stack on `build/unit-system`. Nothing merges. He lands the stack himself.",
			);
		} else outLines.push(line);
	}
	return outLines;
}

function filesOf(lines) {
	const start = lines.indexOf("**Files.**");
	const end = lines.indexOf("**Build.**");
	if (start === -1 || end === -1) return [];
	const found = new Set();
	for (const line of lines.slice(start, end)) {
		if (!line.startsWith("- [ ]")) continue;
		for (const m of line.matchAll(/`([^`]+)`/g)) {
			let p = m[1].trim();
			if (/\s/.test(p) || !/^(qml|qmb|qmn|packages|extensions|qmx-agents|tools|examples|scripts)\//.test(p)) continue;
			p = p.replace(/:\d+(-\d+)?$/, "").replace(/^\.\//, "");
			const brace = p.match(/^(.*)\{([^}]+)\}(.*)$/);
			const expanded = brace ? brace[2].split(",").map((x) => brace[1] + x + brace[3]) : [p];
			for (let q of expanded) {
				const cut = q.search(/[<*]/);
				if (cut !== -1) q = q.slice(0, q.lastIndexOf("/", cut) + 1);
				if (q) found.add(q);
			}
		}
	}
	return [...found];
}

const body = [];
for (const file of phaseFiles) {
	const text = fs.readFileSync(path.join(here, file), "utf8").replace(/\r\n/g, "\n").trimEnd();
	const sections = text.split(/\n(?=## )/);
	for (const section of sections) {
		const lines = section.split("\n");
		const title = lines[0];
		const m = title.match(/^## (.*) \(([^)]+)\)$/);
		if (!m) {
			problems.push(`${file}: section "${title}" has no (ID) at the end of its title`);
			continue;
		}
		const id = m[2];
		const phase = (section.match(/^Phase (\d)/m) || [])[1] ?? "?";
		const dependsLine = lines.find((l) => l.startsWith("**Depends on.**")) ?? "";
		const deps = [...new Set([...dependsLine.matchAll(ID)].map((x) => x[1]))].filter((d) => d !== id);
		prs.push({ id, title: m[1], phase, deps, files: filesOf(lines), file });
		body.push(expandSection(lines, id).join("\n"));
	}
}

const index = new Map(prs.map((p, i) => [p.id, i]));
if (index.size !== prs.length) problems.push("duplicate PR ids");
for (const [i, pr] of prs.entries()) {
	if (pr.phase === "?") problems.push(`${pr.id}: preamble does not start with "Phase N"`);
	if (pr.files.length === 0) problems.push(`${pr.id}: Files block names no path`);
	for (const d of pr.deps) {
		if (!index.has(d)) problems.push(`${pr.id}: depends on unknown id ${d}`);
		else if (index.get(d) > i) problems.push(`${pr.id}: depends on ${d}, which comes later`);
	}
}

const table = ["| # | Id | Phase | PR | Depends on |", "|---|---|---|---|---|"];
for (const [i, pr] of prs.entries()) {
	table.push(`| ${i + 1} | ${pr.id} | ${pr.phase} | ${pr.title} | ${pr.deps.length ? pr.deps.join(", ") : "none"} |`);
}

const touches = (a, b) => a === b || (a.endsWith("/") && b.startsWith(a)) || (b.endsWith("/") && a.startsWith(b));
const rows = [];
for (const pr of prs) {
	const clashes = prs.filter((other) => other !== pr && pr.files.some((a) => other.files.some((b) => touches(a, b))));
	if (clashes.length === 0) continue;
	const shared = [...new Set(clashes.flatMap((other) => pr.files.filter((a) => other.files.some((b) => touches(a, b)))))];
	rows.push(`| ${pr.id} | ${clashes.map((c) => c.id).join(", ")} | ${shared.map((s) => `\`${s}\``).join(", ")} |`);
}
const shared = ["| PR | Never runs beside | Its shared paths |", "|---|---|---|", ...rows];

const plan = [
	head.replace(/\r\n/g, "\n").trimEnd().replace("@spawn-table", table.join("\n")),
	...body,
	tail.replace(/\r\n/g, "\n").trimEnd().replace("@files-shared", shared.join("\n")),
].join("\n\n");
fs.writeFileSync(out, `${plan}\n`);

console.log(`${prs.length} PRs from ${phaseFiles.length} phase files, ${rows.length} PRs share a path, ${plan.split("\n").length} lines`);
for (const p of problems) console.error(p);
process.exit(problems.length ? 1 : 0);
