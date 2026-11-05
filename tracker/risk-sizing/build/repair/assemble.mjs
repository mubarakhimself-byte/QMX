#!/usr/bin/env node
// Builds REPAIR-PLAN.md from plan-parts/ and refuses to write it when a row is lost.
// Run from this folder: node assemble.mjs. Then run check-plan.mjs on the result.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PARTS = path.join(HERE, "plan-parts");
const FINDINGS = "D:/QMX-worktrees/audit-ship/FINDINGS.tsv";
const CODE = "D:/QMX-worktrees/audit-head";
const RULE =
	"Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.";
const ROW_ID = /^[a-z][a-z0-9-]*-n?\d+$/;

const problems = [];
const read = (name) => fs.readFileSync(path.join(PARTS, name), "utf8").replace(/\r\n/g, "\n");

function tsv(text) {
	const rows = [];
	let row = [];
	let cell = "";
	let quoted = false;
	for (let i = 0; i < text.length; i++) {
		const c = text[i];
		if (quoted) {
			if (c === '"' && text[i + 1] === '"') {
				cell += '"';
				i++;
			} else if (c === '"') quoted = false;
			else cell += c;
		} else if (c === '"' && cell === "") quoted = true;
		else if (c === "\t") {
			row.push(cell);
			cell = "";
		} else if (c === "\n") {
			row.push(cell.replace(/\r$/, ""));
			rows.push(row);
			row = [];
			cell = "";
		} else cell += c;
	}
	if (cell || row.length) rows.push([...row, cell]);
	const head = rows.shift();
	return rows.filter((r) => r.length > 1).map((r) => Object.fromEntries(head.map((h, i) => [h, r[i] ?? ""])));
}

const expand = (text) =>
	text
		.replace(/^@@UNIT$/gm, `**Verify, unit.** ${RULE}`)
		.replace(
			/^@@LIVE$/gm,
			`**Verify, live.** ${RULE} Ten lanes on \`haiku\` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu, and the coordinator runs at most one of them. A lane needs no model unless it says so.`,
		)
		.replace(/^@@PERF$/gm, `**Verify, perf.** ${RULE}`)
		.replace(/^@@GATE$/gm, "**Review gate.** None. No screen changes.")
		.replace(/^@@LANES710 (r\d\d)$/gm, (_, id) =>
			[
				`- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder, read its health route, then stop it. No model. Save \`${id}-boot.log\`. Pass when the host answers and stops clean.`,
				`- [ ] Lane 8. Run the PR's new tests three times in a row. No model. Save \`${id}-repeat.log\`. Pass when the three runs agree.`,
				`- [ ] Lane 9. Grep every lane log of this PR for key, token and password values. No model. Save \`${id}-leak.log\`. Pass when none appears.`,
				`- [ ] Lane 10. Remove the throwaway folders and the check worktree, then list processes. No model. Save \`${id}-processes.log\`. Pass when no \`qmx_host\`, \`claude\`, \`node\` or lane process is left.`,
			].join("\n"),
		)
		.replace(/^@@MERGE (r\d\d)$/gm, (_, id) =>
			[
				"**Merge.**",
				"",
				"- [ ] The coordinator's CLEAN verdict at the exact head, or after the one fix round.",
				"- [ ] The skills check passes for this PR's builder and reviewer, and the order check finds `owner-how.md`, `owner-sketch.md` and `owner-red.log` in that order.",
				`- [ ] Lows in \`lows.md\`, new findings justified in \`BACKLOG.md\`, the verdict, head, parent, patch-id and count in \`ledger.tsv\`, and \`S/review/${id}-check-<head8>.md\` on disk.`,
				"- [ ] Appended to the stack. Nothing merges. He lands the stack himself.",
			].join("\n"),
		);

const prs = [];
for (let n = 1; n <= 24; n++) {
	const id = `R${String(n).padStart(2, "0")}`;
	const body = expand(read(`${id.toLowerCase()}.md`));
	const title = body.split("\n")[0].replace(/^## /, "");
	if (!title.endsWith(`(${id})`)) problems.push(`${id}: heading does not end with its id: ${title}`);
	const line = (word) => body.split("\n").find((l) => l.startsWith(word)) ?? "";
	const tokens = (text) => [...text.matchAll(/`([^`]+)`/g)].map((m) => m[1]).filter((t) => ROW_ID.test(t));
	const whole = tokens(line("Rows carried."));
	const inPart = line("Rows in part.")
		.replace(/^Rows in part\.\s*/, "")
		.split(/\.\s+/)
		.flatMap((sentence) => tokens(sentence.split(" by ")[0]));
	const depends = line("**Depends on.**").replace("**Depends on.**", "").trim();
	const proves = line("Proves.").replace("Proves.", "").trim();
	if (!proves) problems.push(`${id}: no Proves line`);
	const rest = body
		.split("\n")
		.filter((l) => !l.startsWith("Rows carried.") && !l.startsWith("Rows in part."))
		.join("\n");
	for (const row of [...whole, ...inPart]) {
		if (!rest.includes(`\`${row}\``)) problems.push(`${id}: row ${row} is on its Rows line and in no box`);
	}
	prs.push({ id, n, title, body, whole, inPart, depends, proves });
}

const seen = new Set();
for (const pr of prs) {
	for (const m of pr.depends.matchAll(/R\d\d/g)) {
		if (!seen.has(m[0])) problems.push(`${pr.id} depends on ${m[0]}, which is not earlier`);
	}
	seen.add(pr.id);
}

const pathsIn = (line) => [...line.matchAll(/`([^`]+)`/g)].map((m) => m[1]).filter((t) => t.includes("/") && !t.includes("<") && !t.includes("*"));
const lsFiles = execFileSync("git", ["-C", CODE, "ls-files"], { encoding: "utf8", maxBuffer: 1 << 28 }).split(/\r?\n/);
const onDisk = new Set(lsFiles);
const exists = (p) => (p.endsWith("/") ? lsFiles.some((f) => f.startsWith(p)) : onDisk.has(p) || lsFiles.some((f) => f.startsWith(`${p}/`)));
const created = new Set();
const deleted = new Set();
const touching = new Map();
for (const pr of prs) {
	const lines = pr.body.split("\n");
	const start = lines.findIndex((l) => l.startsWith("**Files.**"));
	const end = lines.findIndex((l) => l.startsWith("**Build.**"));
	for (const box of lines.slice(start + 1, end).filter((l) => l.startsWith("- [ ]"))) {
		const verb = box.replace("- [ ] ", "").split(" ")[0];
		const found = pathsIn(box);
		if (found.length === 0 && !box.includes("*")) problems.push(`${pr.id}: Files box names no path: ${box.slice(0, 80)}`);
		found.forEach((p, index) => {
			if (!touching.has(p)) touching.set(p, new Set());
			touching.get(p).add(pr.id);
			const known = exists(p) || created.has(p) || [...created].some((c) => c.endsWith("/") && p.startsWith(c));
			const isNew = verb === "Create" || (verb === "Move" && index === 1);
			if (isNew) {
				if (exists(p)) problems.push(`${pr.id}: Create ${p}, which exists at 50c83a4e`);
				created.add(p);
			} else {
				if (!known) problems.push(`${pr.id}: ${verb} ${p}, which does not exist at 50c83a4e and no earlier PR creates`);
				if (deleted.has(p)) problems.push(`${pr.id}: ${verb} ${p}, which an earlier PR deleted`);
				if (verb === "Delete") deleted.add(p);
			}
		});
	}
}

const shared = [...touching.entries()].filter(([, ids]) => ids.size > 1).sort((a, b) => b[1].size - a[1].size || a[0].localeCompare(b[0]));
const appendixC = ["| Path | PRs |", "| --- | --- |", ...shared.map(([p, ids]) => `| \`${p}\` | ${[...ids].join(", ")} |`)].join("\n");

const spawnTable = [
	"| # | Id | PR | Depends on | Proving check |",
	"| --- | --- | --- | --- | --- |",
	...prs.map((pr) => `| ${pr.n} | ${pr.id} | ${pr.title.replace(/ \(R\d\d\)$/, "")} | ${pr.depends.replace(/`/g, "").replace(/\.$/, "")} | ${pr.proves.replace(/\.$/, "")} |`),
].join("\n");

const rows = tsv(fs.readFileSync(FINDINGS, "utf8"));
const byId = new Map(rows.map((r) => [r.id, r]));
const newRows = tsv(read("rows-new.tsv"));
const newIds = new Map(newRows.map((r) => [r.id, r]));
const outRows = tsv(read("rows-out.tsv"));
const outIds = new Map(outRows.map((r) => [r.id, r]));
const placedWhole = new Map();
const placedPart = new Map();
const add = (map, row, id) => {
	if (!map.has(row)) map.set(row, []);
	map.get(row).push(id);
};
for (const pr of prs) {
	pr.whole.forEach((r) => add(placedWhole, r, pr.id));
	pr.inPart.forEach((r) => add(placedPart, r, pr.id));
}
for (const row of [...placedWhole.keys(), ...placedPart.keys()]) {
	if (!byId.has(row) && !newIds.has(row)) problems.push(`row ${row} is on a Rows line and in no table`);
}
const placedIn = (row) => [...(placedWhole.get(row) ?? []), ...(placedPart.get(row) ?? []).map((id) => `${id} in part`)].join(", ");
const clean = (text, max) => {
	const t = String(text ?? "")
		.replace(/[\u2013\u2014]/g, ",")
		.replace(/[\u2018\u2019]/g, "'")
		.replace(/[\u201c\u201d]/g, '"')
		.replace(/`/g, "")
		.replace(/\|/g, ",")
		.replace(/:\s/g, ", ")
		.replace(/\s+/g, " ")
		.trim();
	if (t.length <= max) return t;
	return `${t.slice(0, max).replace(/\s+\S*$/, "")} and so on`;
};

const musts = rows.filter((r) => r.grade === "must");
const shoulds = rows.filter((r) => r.grade === "should");
const leaves = rows.filter((r) => r.grade === "leave");
const newMusts = newRows.filter((r) => r.grade === "must");
for (const r of [...musts, ...newMusts]) {
	if (!placedWhole.has(r.id) && !placedPart.has(r.id)) problems.push(`must row ${r.id} has no PR`);
	if (placedPart.has(r.id) && !placedWhole.has(r.id) && !outIds.has(r.id)) problems.push(`must row ${r.id} is placed in part, and rows-out.tsv does not say where the rest goes`);
}
for (const r of shoulds) {
	const here = placedWhole.has(r.id) || placedPart.has(r.id);
	if (!here && !outIds.has(r.id)) problems.push(`should row ${r.id} has neither a PR nor a reason in rows-out.tsv`);
	if (placedWhole.has(r.id) && outIds.has(r.id)) problems.push(`should row ${r.id} is placed whole and also listed as out`);
	if (placedPart.has(r.id) && !placedWhole.has(r.id) && !outIds.has(r.id)) problems.push(`should row ${r.id} is placed in part, and rows-out.tsv does not say where the rest goes`);
}
for (const r of newRows) {
	if (!placedWhole.has(r.id) && !placedPart.has(r.id) && !outIds.has(r.id)) problems.push(`new row ${r.id} has neither a PR nor a reason in rows-out.tsv`);
}
for (const r of outRows) {
	if (!byId.has(r.id) && !newIds.has(r.id)) problems.push(`rows-out.tsv names ${r.id}, which is in no table`);
	if (!r.reason) problems.push(`rows-out.tsv gives ${r.id} no reason`);
}

const appendixE = [];
appendixE.push("### Every must row and its PR", "");
appendixE.push("| Row | Placed in | The rest waits for | What |", "| --- | --- | --- | --- |");
for (const r of musts) appendixE.push(`| \`${r.id}\` | ${placedIn(r.id)} | ${clean(outIds.get(r.id)?.reason ?? "nothing, the row closes here", 70)} | ${clean(r.what, 110)} |`);
appendixE.push("", "### New rows from the grounding reports", "");
appendixE.push("| Row | Grade | Source | Placed in, or waits for | What |", "| --- | --- | --- | --- | --- |");
for (const r of newRows) {
	const where = placedIn(r.id) || clean(outIds.get(r.id)?.reason ?? "", 70);
	appendixE.push(`| \`${r.id}\` | ${r.grade} | ${clean(r.source, 40)} | ${where} | ${clean(r.what, 110)} |`);
}
appendixE.push("", "### Every should row with its PR, or the reason it stays out", "");
appendixE.push("| Row | Kind | Placed in | The rest, or the reason it stays out |", "| --- | --- | --- | --- |");
for (const r of shoulds) appendixE.push(`| \`${r.id}\` | ${r.kind} | ${placedIn(r.id) || "not in this body"} | ${clean(outIds.get(r.id)?.reason ?? "nothing left over", 110)} |`);
const leftLeaves = leaves.filter((r) => !placedWhole.has(r.id) && !placedPart.has(r.id));
const touchedLeaves = leaves.filter((r) => placedWhole.has(r.id) || placedPart.has(r.id));
appendixE.push("", "### Every leave row", "");
appendixE.push(
	`These ${leftLeaves.length} rows stay in \`A/FINDINGS.tsv\`, left out on purpose unless a PR touches the line anyway. ${leftLeaves.map((r) => `\`${r.id}\``).join(", ")}.`,
	"",
	`These ${touchedLeaves.length} rows are closed because a PR touches their line anyway. ${touchedLeaves.map((r) => `\`${r.id}\` in ${placedIn(r.id)}`).join(", ")}.`,
);
const testDelete = rows.filter((r) => r.kind === "test-delete");
const lines = (list) => list.reduce((sum, r) => sum + (Number(r.removable_lines) || 0), 0);
const deletedHere = testDelete.filter((r) => placedWhole.has(r.id) || placedPart.has(r.id));
const keptHere = testDelete.filter((r) => !placedWhole.has(r.id) && !placedPart.has(r.id));
appendixE.push(
	"",
	"### The test-delete rows",
	"",
	`${testDelete.length} rows hold ${lines(testDelete)} lines. ${deletedHere.length} rows, ${lines(deletedHere)} lines, go in the PRs that touch their files. ${keptHere.length} rows, ${lines(keptHere)} lines, stay, because no PR touches them. ${keptHere.map((r) => `\`${r.id}\``).join(", ")}.`,
);
const mustPlaced = musts.filter((r) => placedWhole.has(r.id) || placedPart.has(r.id)).length;
const newMustPlaced = newMusts.filter((r) => placedWhole.has(r.id) || placedPart.has(r.id)).length;
const shouldPlaced = shoulds.filter((r) => placedWhole.has(r.id) || placedPart.has(r.id)).length;
const counts = `must rows ${mustPlaced} of ${musts.length} placed, new must rows ${newMustPlaced} of ${newMusts.length} placed, should rows ${shouldPlaced} of ${shoulds.length} placed and ${shoulds.length - shouldPlaced} out with a reason, leave rows ${touchedLeaves.length} touched and ${leftLeaves.length} left`;
appendixE.unshift(`\`assemble.mjs\` generates this appendix from \`A/FINDINGS.tsv\`, the Rows lines of each section, \`plan-parts/rows-new.tsv\` and \`plan-parts/rows-out.tsv\`, and it refuses to write the plan if a must or should row has no home. The count at this build is ${counts}.`, "");

let plan = read("00-head.md").replace("@spawn-table", spawnTable);
plan += prs.map((pr) => pr.body.trimEnd()).join("\n\n");
plan += `\n\n${read("80-close.md").trimEnd()}\n\n`;
plan += read("90-appendices.md").replace("@appendix-c", appendixC).replace("@appendix-e", appendixE.join("\n"));

if (problems.length) {
	for (const p of problems) console.error(p);
	console.error(`${problems.length} problems, plan not written`);
	process.exit(1);
}
fs.writeFileSync(path.join(HERE, "REPAIR-PLAN.md"), `${plan.trimEnd()}\n`);
console.log(counts);
console.log(`${testDelete.length} test-delete rows, ${lines(testDelete)} lines, ${deletedHere.length} rows placed`);
console.log(`${shared.length} shared paths in Appendix C`);
