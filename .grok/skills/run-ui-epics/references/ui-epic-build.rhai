let meta = #{
    name: "ui-epic-build",
    description: "Build every story of one UI epic in its worktree; heavy grok-4.6, light grok-4.5; command evidence gates; grok-4.6 reviews; destination is args.destination_branch",
    when_to_use: "Launched by run-ui-epics after a UI worktree is cut. Pass worktree, branch, destination_branch, stories, quality, factory_cli.",
    phases: [
        #{ title: "Stories", detail: "sequential build, quality evidence, optional runtime" },
        #{ title: "Review", detail: "grok-4.6 review with blocking vs advisory" },
    ],
};

let build_schema = #{
    "type": "object",
    "required": ["changed_files", "commit", "summary"],
    "properties": #{
        changed_files: #{ "type": "array", "items": #{ "type": "string" } },
        commit: #{ "type": "string" },
        summary: #{ "type": "string" },
    },
};
let verify_schema = #{
    "type": "object",
    "required": ["passed", "failures", "evidence_path", "exit_code"],
    "properties": #{
        passed: #{ "type": "boolean" },
        failures: #{ "type": "array", "items": #{ "type": "string" } },
        evidence_path: #{ "type": "string" },
        exit_code: #{ "type": "integer" },
    },
};
let review_schema = #{
    "type": "object",
    "required": ["blocking", "advisory", "summary"],
    "properties": #{
        blocking: #{ "type": "array", "items": #{ "type": "string" } },
        advisory: #{ "type": "array", "items": #{ "type": "string" } },
        summary: #{ "type": "string" },
    },
};

fn ok_map(r) {
    r != () && r.success && r.output != () && type_of(r.output) == "map"
}

fn as_str(x) {
    if x == () {
        ""
    } else if type_of(x) == "string" {
        x
    } else {
        json_encode(x)
    }
}

fn unattended_rules() {
    "UNATTENDED UI FACTORY — the operator is not available and must never be asked. NEVER call ask_user_question. NEVER pause for a human. NEVER ask a clarifying question. Decide from the story, contracts, tests, and docs/lenses/ui. A committed decision beats a blocked question. Do not invent product law. An unresolved contract conflict blocks this unit.\n"
}

if args == () {
    pause("verification", "Pass args: worktree, branch, destination_branch, stories, quality, factory_cli.");
}

let worktree = as_str(args.worktree);
let branch = as_str(args.branch);
let destination = as_str(args.destination_branch);
let stories = args.stories;
let quality = args.quality;
let factory_cli = as_str(args.factory_cli);
if worktree == "" || branch == "" || destination == "" || stories == () || quality == () || factory_cli == "" {
    pause("verification", "Pass worktree, branch, destination_branch, stories, quality, factory_cli.");
}
if destination == "integration" || destination == "main" {
    pause("verification", "destination_branch must be the UI branch, never integration or main.");
}

let review_skill = "";
if args.review_skill != () {
    review_skill = as_str(args.review_skill);
}
let adapter = "";
if args.review_adapter != () {
    adapter = as_str(args.review_adapter);
}
let frontend_entry = "";
if args.frontend_entry != () {
    frontend_entry = as_str(args.frontend_entry);
}

let build_model = "grok-4.5";
if args.build_model != () {
    let bm = as_str(args.build_model);
    if bm == "grok-4.6" || bm == "grok-4.5" {
        build_model = bm;
    }
}

phase("Stories");
let ledger = [];
let stopped = false;
let last_commit = "";
let blocking_all = [];

for story in stories {
    if stopped {
        let sid_skip = as_str(story.id);
        ledger.push(#{ story: sid_skip, commit: "", passed: false, reason: "skipped — earlier story red" });
    } else {
        let sid = as_str(story.id);
        let title = as_str(story.title);
        let brief = as_str(story.brief);
        let already = as_str(story.already_commit);
        let user_facing = "false";
        if story.user_facing == true {
            user_facing = "true";
        }
        let commit = "";
        let build_ok = false;
        if already != "" {
            commit = already;
            last_commit = already;
            build_ok = true;
            log("Resuming story " + sid + " at " + already + " — skip rebuild, run quality");
        } else {
            log("Building story " + sid + ": " + title);
            let bp = unattended_rules();
            bp += "Work ONLY inside this worktree. Set the working directory there first. Never touch the shared laptop checkout or backend epic worktrees.\nWorktree: ";
            bp += worktree;
            bp += "\nBranch: ";
            bp += branch;
            bp += "\nDestination branch (do not merge here yourself): ";
            bp += destination;
            bp += "\nStory ";
            bp += sid;
            bp += ": ";
            bp += title;
            bp += "\n";
            bp += brief;
            bp += "\nRead docs/AGENTS.md, ADR-0026, and docs/lenses/ui/ from the worktree. ";
            if frontend_entry != "" {
                bp += "Read this frontend entry and follow it: ";
                bp += frontend_entry;
                bp += " ";
            }
            bp += "Preserve distinct main-copilot and application interiors, original storyboard layout intent, optional app copilot, meaningful widget content, expand/return, independent conversation histories, visual/headless/mixed capabilities, and loading/empty/error/stale/reconnecting/denied states. Local fixtures must be labeled FACTORY-TEST. ";
            bp += "When done: git add of intended files && git commit -m \"story ";
            bp += sid;
            bp += ": <one-line summary>\" with a plain one-liner — no attribution lines. ";
            bp += "Return JSON {changed_files, commit, summary}. Use tools. An empty changed_files list is valid only after you have looked.";
            let build = agent(bp, #{
                label: "build:" + sid,
                phase: "Stories",
                model: build_model,
                capability_mode: "all",
                output_schema: build_schema,
            });
            if ok_map(build) {
                commit = as_str(build.output.commit);
                build_ok = commit != "";
            }
        }
        if !build_ok {
            log("Build failed for story " + sid);
            ledger.push(#{ story: sid, commit: commit, passed: false, reason: "build failed" });
            stopped = true;
        } else {
            last_commit = commit;
            let round = 0;
            let passed = false;
            let failures_text = "not run";
            while round < 4 && !passed {
                let vp = unattended_rules();
                vp += "In this worktree RUN the factory CLI. Do not judge by reading code. Set cwd to the worktree.\n";
                vp += factory_cli;
                vp += " quality --worktree ";
                vp += worktree;
                vp += " --unit-id ";
                vp += sid;
                vp += " --sha ";
                vp += commit;
                if user_facing == "true" {
                    vp += " --user-facing";
                }
                vp += "\n";
                vp += "passed is true only if the CLI exits 0 AND evidence JSON exists AND every command exit_code is 0. ";
                vp += "If the CLI is missing, passed=false and missing_tool. Return JSON {passed, failures, evidence_path, exit_code}.";
                let verify = agent(vp, #{
                    label: "verify:" + sid + "." + round.to_string(),
                    phase: "Stories",
                    model: "grok-4.5",
                    capability_mode: "execute",
                    output_schema: verify_schema,
                });
                let exit_code = 1;
                if ok_map(verify) {
                    passed = verify.output.passed == true;
                    exit_code = verify.output.exit_code;
                    if exit_code != 0 {
                        passed = false;
                    }
                    if verify.output.failures != () {
                        failures_text = json_encode(verify.output.failures);
                    } else if passed {
                        failures_text = "[]";
                    } else {
                        failures_text = "[\"verify returned passed=false with no failures quoted\"]";
                    }
                } else {
                    passed = false;
                    failures_text = "[\"verify agent failed or returned no object\"]";
                }
                if !passed && round < 3 {
                    log("Quality red for " + sid + " round " + round.to_string() + " — sending fix");
                    let fp = unattended_rules();
                    fp += "Work ONLY inside ";
                    fp += worktree;
                    fp += " — set cwd there. Fix ONLY these quality failures, then commit a plain one-liner:\n";
                    fp += failures_text;
                    fp += "\nReturn JSON {changed_files, commit, summary}.";
                    let fixr = agent(fp, #{
                        label: "fix:" + sid + "." + round.to_string(),
                        phase: "Stories",
                        model: build_model,
                        capability_mode: "all",
                        output_schema: build_schema,
                    });
                    if ok_map(fixr) {
                        let fc = as_str(fixr.output.commit);
                        if fc != "" {
                            last_commit = fc;
                            commit = fc;
                        }
                    }
                }
                round += 1;
            }
            ledger.push(#{ story: sid, commit: commit, passed: passed, reason: failures_text });
            if !passed {
                log("Story " + sid + " still red after quality loop — stopping epic");
                stopped = true;
            } else {
                log("Story " + sid + " green at " + commit);
            }
        }
    }
}

let n_stories = stories.len();
let n_green = 0;
for row in ledger {
    if row.passed == true {
        n_green += 1;
    }
}
let all_green = n_green == n_stories && n_stories > 0 && !stopped;

phase("Review");
let rp = unattended_rules();
rp += "Advisory+blocking code review. Change nothing.\nWorktree: ";
rp += worktree;
rp += "\nBranch: ";
rp += branch;
rp += "\nCompare against ";
rp += destination;
rp += " not integration. Run git diff ";
rp += destination;
rp += "...HEAD (cwd=worktree). ";
rp += "Blocking findings need file:line evidence of a defect that violates the story AC, a contract, or accessibility/runtime proof. ";
rp += "Empty blocking list is valid after you inspected the diff. Do not manufacture findings to meet a quota. ";
if adapter != "" {
    rp += "Read this factory adapter and follow it (it replaces interactive BMAD checkpoints): ";
    rp += adapter;
    rp += " ";
}
if review_skill != "" {
    rp += "The upstream review skill path is ";
    rp += review_skill;
    rp += " — use its layer prompts only through the adapter.";
}
rp += " Return JSON {blocking, advisory, summary}.";

let review = agent(rp, #{
    label: "review",
    phase: "Review",
    model: "grok-4.6",
    capability_mode: "execute",
    output_schema: review_schema,
});

let review_text = "";
let blocking = [];
if ok_map(review) {
    review_text = as_str(review.output.summary);
    if review.output.blocking != () {
        blocking = review.output.blocking;
    }
    review_text += "\n" + json_encode(review.output);
} else {
    review_text = "review agent failed or returned nothing";
    all_green = false;
}
if blocking.len() > 0 {
    all_green = false;
    log("Blocking review findings — all_green=false");
}

let report = "# ui-epic-build\n\n";
report += "branch: ";
report += branch;
report += "\ndestination: ";
report += destination;
report += "\nworktree: ";
report += worktree;
report += "\nall_green: ";
if all_green {
    report += "true";
} else {
    report += "false";
}
report += "\nstories green: ";
report += n_green.to_string();
report += "/";
report += n_stories.to_string();
report += "\n\n## Ledger\n\n";
for row in ledger {
    report += "- ";
    report += as_str(row.story);
    report += " passed=";
    if row.passed == true {
        report += "true";
    } else {
        report += "false";
    }
    report += " commit=";
    report += as_str(row.commit);
    report += "\n";
}
report += "\n## Review\n\n";
report += review_text;
report += "\n";

let ags = "false";
if all_green { ags = "true"; }
let report_path = write_scratch_file("report.md", report);
log(n_green.to_string() + "/" + n_stories.to_string() + " stories green; all_green=" + ags);
complete(#{
    path: report_path,
    report: report,
    ledger: ledger,
    all_green: all_green,
    review: review_text,
    blocking: blocking,
    branch: branch,
    destination_branch: destination,
    worktree: worktree,
});
