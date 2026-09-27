let meta = #{
    name: "ui-factory-lifecycle",
    description: "Bounded synthetic factory lifecycle: fail, resume, occupied promote, reticle block",
    when_to_use: "Factory repair proof only. Not a product epic.",
    phases: [
        #{ title: "Lifecycle", detail: "CLI lifecycle plus one live quality agent" },
    ],
};

let verify_schema = #{
    "type": "object",
    "required": ["passed", "exit_code", "evidence_path"],
    "properties": #{
        passed: #{ "type": "boolean" },
        exit_code: #{ "type": "integer" },
        evidence_path: #{ "type": "string" },
    },
};

fn as_str(x) {
    if x == () { "" } else if type_of(x) == "string" { x } else { json_encode(x) }
}

if args == () {
    pause("verification", "Pass worktree and cli.");
}
let worktree = as_str(args.worktree);
let cli = as_str(args.cli);
if worktree == "" || cli == "" {
    pause("verification", "Pass args.worktree and args.cli.");
}

phase("Lifecycle");
let prep = "UNATTENDED. Never ask a human. cwd=";
prep += worktree;
prep += " Run: python ";
prep += cli;
prep += " lifecycle --mode synthetic";
prep += "\nThen run quality against the printed fixture_repo with --user-facing and NO reticle file.";
prep += " That quality must fail. Return JSON {passed:false, exit_code, evidence_path} for the negative Reticle control.";
prep += " Do not launch product epics.";

let r = agent(prep, #{
    label: "lifecycle",
    capability_mode: "execute",
    output_schema: verify_schema,
});

let passed = false;
let exit_code = 1;
let evidence_path = "";
if r != () && r.success && r.output != () {
    passed = r.output.passed == true;
    exit_code = r.output.exit_code;
    evidence_path = as_str(r.output.evidence_path);
}
let report = "ui-factory-lifecycle agent_passed=" ;
if passed { report += "true"; } else { report += "false"; }
report += " exit_code=" + exit_code.to_string();
report += " evidence=" + evidence_path;
let path = write_scratch_file("report.md", report);
complete(#{
    path: path,
    report: report,
    passed: passed,
    exit_code: exit_code,
    evidence_path: evidence_path,
});
