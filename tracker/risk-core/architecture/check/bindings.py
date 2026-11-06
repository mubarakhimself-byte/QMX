"""Reads the spine's concrete bindings in the code: each row is (tip, path, the spine's lines, a pattern that must sit on
them). Reports hold or miss at the named tip, then where the pattern sits now at the newest worktree heads.
Read-only: git show only. Run with a time limit: python -I -B bindings.py"""
import re
import subprocess

REPO = "D:/QMX-worktrees/bld-repair-10"
TIPS = {"J": "a4f64510", "N": "ef011af4", "R": "7ada84ed"}
NEW = {"J": "D:/QMX-worktrees/bld-repair-18", "N": "D:/QMX-worktrees/bld-repair-23", "R": "D:/QMX-worktrees/bld-repair-23"}

UNIT = "qml/src/qml/protocol/unit.py"
API = "qml/src/qml/blocks/api.py"
COMP = "qml/src/qml/compile/compiler.py"
HAND = "qmb/src/qmb/host/unit_handler.py"
ENC = "packages/qmf-venue/src/qmf/venue/encode.py"
RT = "qmn/src/qmn/app/runtime.py"
KINDS = "packages/qmf-data/src/qmf/data/journal_kinds/unit.py"
ROWS = [
    ("J", UNIT, 129, 138, r"class OwnPosition"),
    ("J", UNIT, 444, 444, r"def timer"),
    ("J", UNIT, 671, 671, r"def exits"),
    ("J", UNIT, 686, 686, r"timer\.update\(\{\}\)"),
    ("J", UNIT, 785, 793, r'"equity": account\.equity'),
    ("J", UNIT, 827, 830, r"rounding_residue_r"),
    ("J", API, 105, 109, r"class Size"),
    ("J", API, 182, 186, r"class HaltInstance"),
    ("J", API, 196, 218, r"class CrossUnitHook"),
    ("J", COMP, 100, 100, r"COMPILER_FORMAT_VERSION.*= 4"),
    ("J", COMP, 361, 362, r"risk session agrees its socket"),
    ("J", COMP, 474, 475, r"exit_not_built"),
    ("J", COMP, 484, 485, r"inputs_not_built"),
    ("J", COMP, 491, 494, r"exit_not_built"),
    ("J", COMP, 502, 503, r"stop_not_built"),
    ("J", COMP, 724, 725, r"binding_not_read"),
    ("J", COMP, 869, 870, r"_MOTION_READ"),
    ("J", COMP, 903, 903, r"halts_not_built"),
    ("J", COMP, 933, 934, r"inputs_not_built"),
    ("J", COMP, 998, 999, r"open_positions_not_built"),
    ("J", COMP, 1004, 1005, r"motion_not_built"),
    ("J", COMP, 1011, 1012, r"cadence_not_built"),
    ("J", HAND, 97, 99, r"mfe_r"),
    ("J", HAND, 249, 250, r"mae_r="),
    ("J", HAND, 358, 367, r"def read_surfaces"),
    ("J", HAND, 370, 372, r"def _account"),
    ("J", HAND, 484, 484, r"def mint_intents"),
    ("J", HAND, 724, 724, r"r_after_costs="),
    ("J", ENC, 115, 120, r"_LEVEL_RULES"),
    ("J", ENC, 748, 752, r"relativeStopLoss"),
    ("J", ENC, 748, 752, r"relativeTakeProfit"),
    ("J", ENC, 1029, 1029, r'"takeProfit"'),
    ("J", "packages/qmf-venue/src/qmf/venue/commands.py", 361, 361, r"protective_stop_distance"),
    ("J", "qmb/src/qmb/execution/fill.py", 1327, 1328, r"FillKind\.TARGET, target"),
    ("J", "qmb/src/qmb/results/journal.py", 408, 416, r"exit_kind"),
    ("J", "qmx-agents/packages/qmx-host/src/qmx_host/promote.py", 321, 321, r"def _admit"),
    ("J", "qmx-agents/packages/qmx-host/src/qmx_host/promote.py", 502, 502, r"def _deployment"),
    ("J", "qmx-agents/packages/qmx-host/src/qmx_host/host.py", 2090, 2125, r"_stated_costs"),
    ("J", "qmx-agents/packages/qmx-judge/src/qmx_judge/presets.py", 45, 45, r"min_trades=100"),
    ("J", "qmn/src/qmn/venue/ccxt_client.py", 597, 601, r"return Decimal\(0\)"),
    ("J", "qml/tests/test_unit_refuses.py", 457, 457, r"test_every_field_of_the_schema"),
    ("J", "qml/src/qml/blocks/stdlib/fixed-fraction-at-stop/1/block.py", 50, 54, r"loss_per_lot"),
    ("J", "qmn/src/qmn/seats/dispatch.py", 917, 930, r"signed_offset"),
    ("N", RT, 1018, 1018, r"cross_unit_hook\(command"),
    ("N", RT, 1020, 1020, r"require_venue_resident_protective_stop"),
    ("N", RT, 1066, 1069, r"def cross_unit_hook"),
    ("N", RT, 1278, 1280, r"_past_entry"),
    ("N", RT, 1308, 1309, r"def _move_stop"),
    ("N", RT, 1319, 1321, r"abs\(entry - new_stop\)"),
    ("N", RT, 1722, 1723, r"ClosePartial"),
    ("N", RT, 1757, 1757, r"def protective"),
    ("N", RT, 2359, 2359, r"def _close_scope"),
    ("N", RT, 2531, 2531, r"def guard"),
    ("N", RT, 2602, 2602, r"def risk_stop"),
    ("N", RT, 2654, 2654, r"def _host"),
    ("N", "qmn/src/qmn/app/stand_down.py", 94, 94, r"RISK_STOP"),
    ("N", "qmn/src/qmn/app/operations.py", 241, 258, r"def _scope"),
    ("N", "qmn/src/qmn/protection/effect_matrix.py", 137, 143, r"PLACEHOLDER_KILL_EFFECTS"),
    ("N", "qmn/src/qmn/venue/ctrader_account.py", 698, 699, r"def equity"),
    ("R", KINDS, 43, 73, r"REASON_CODES"),
    ("R", KINDS, 179, 181, r'"would_have"'),
    ("R", "qmn/src/qmn/app/feed_keeper.py", 230, 246, r"."),
]


def show(ref, path, cwd=REPO):
    out = subprocess.run(["git", "-C", cwd, "show", f"{ref}:{path}"], capture_output=True, timeout=30)
    return out.stdout.decode("utf-8", "replace").splitlines() if out.returncode == 0 else None


held = 0
for tip, path, a, b, pat in ROWS:
    lines = show(TIPS[tip], path)
    ok = lines is not None and any(re.search(pat, x) for x in lines[a - 1:b])
    held += bool(ok)
    new = show("HEAD", path, NEW[tip])
    where = [i + 1 for i, x in enumerate(new or ()) if re.search(pat, x)][:3]
    print(f"{'hold' if ok else 'MISS'} {tip} {path.rsplit('/', 1)[-1]}:{a}-{b} /{pat}/ now at {where}")
print(f"{held} of {len(ROWS)} hold at the named tips")
for wt in NEW.values():
    head = subprocess.run(["git", "-C", wt, "log", "-1", "--format=%h"], capture_output=True, timeout=30).stdout.decode().strip()
    print("newest head read:", wt, head)
