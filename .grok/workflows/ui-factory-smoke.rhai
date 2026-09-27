let meta = #{
    name: "ui-factory-smoke",
    description: "Bounded live smoke of the UI factory CLI through a Grok workflow agent",
    when_to_use: "Factory self-test only. Not a product epic.",
    phases: [ #{ title: "Smoke", detail: "run factory-selftest profile" } ],
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
    pause("verification", "Pass args.worktree and args.cli.");
}
let worktree = as_str(args.worktree);
let cli = as_str(args.cli);
if worktree == "" || cli == "" {
    pause("verification", "Pass args.worktree and args.cli.");
}

phase("Smoke");
let p = "UNATTENDED FACTORY TEST. Never ask a human. Set cwd to ";
p += worktree;
p += " then run: python ";
p += cli;
p += " quality --worktree ";
p += worktree;
p += " --unit-id ft-smoke --sha smoke --profiles factory-selftest --evidence-dir ";
p += worktree;
p += "/../_ui-factory/evidence";
p += "\npassed is true only if that command exits 0. Return JSON {passed, exit_code, evidence_path}.";

// Catalog rejects agent(..., #{ model: ... }). Inherit session model.
let r = agent(p, #{
    label: "smoke-quality",
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
} else if r != () && r.output != () {
    evidence_path = as_str(r.output);
}
if exit_code != 0 { passed = false; }

let passed_s = "false";
if passed { passed_s = "true"; }
let report = "ui-factory-smoke passed=" + passed_s;
report += " exit_code=" + exit_code.to_string();
let path = write_scratch_file("report.md", report);
complete(#{
    path: path,
    report: report,
    passed: passed,
    exit_code: exit_code,
    evidence_path: evidence_path,
});
