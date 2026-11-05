"""Start a real host on a throwaway folder, with no way to reach the real Credential Manager.

A host started any other way wipes the audit's guards at start, then reads the real qmx/control-token.
Only the coordinator uses this. Run it with the check worktree's agents interpreter:

  <worktree>/qmx-agents/.venv/Scripts/python.exe S/tools/safe_host.py <worktree> <port> <folder> [--health-and-stop]

It refuses to start unless the keyring is a throwaway file and the folder's keep list holds it. Without
--health-and-stop it leaves the host running and prints its pid, for the lane to stop afterwards.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
KEEP = {"PYTHON_KEYRING_BACKEND", "PYTHONPATH", "C38_KEYRING_FILE", "UV_CACHE_DIR"}
ALLOWED = ("D:/QMX-worktrees/repair-ship/homes/", "D:/Temp/")


def main(argv):
    worktree, port, folder = Path(argv[1]).resolve(), int(argv[2]), Path(argv[3]).resolve()
    if not folder.as_posix().startswith(ALLOWED):
        raise SystemExit(f"FAIL {folder} is not a throwaway folder; no host was started")
    store = folder.parent / f"{folder.name}-keyring.json"
    os.environ["PYTHON_KEYRING_BACKEND"] = "owner_lane_keyring.FileKeyring"
    os.environ["C38_KEYRING_FILE"] = str(store)
    os.environ["PYTHONPATH"] = os.pathsep.join((str(TOOLS), str(TOOLS / "guard")))
    os.environ["TEMP"] = os.environ["TMP"] = "D:/Temp"
    os.environ["UV_CACHE_DIR"] = "D:/Caches/uv"
    for name in [n for n in os.environ if n.startswith(("CLAUDE", "ANTHROPIC"))]:
        del os.environ[name]
    sys.path.insert(0, str(TOOLS))

    import keyring

    from qma.boot import read_keep_names
    from qmx_home import resolve

    backend = type(keyring.get_keyring()).__name__
    if backend != "FileKeyring":
        raise SystemExit(f"FAIL this process's keyring is {backend}; no host was started")
    folder.parent.mkdir(parents=True, exist_ok=True)
    made = resolve(folder, create=True)
    settings = made.home / "settings.toml"
    settings.write_text(f"[environment]\nkeep = {json.dumps(sorted(KEEP))}\n", "utf-8")
    if not KEEP <= read_keep_names(settings):
        raise SystemExit("FAIL the keep list does not hold the guards; no host was started")
    print("PASS the throwaway keyring and the keep list are in place", flush=True)

    log = open(folder.parent / f"{folder.name}-serve.log", "ab")
    host = subprocess.Popen(
        [sys.executable, "-m", "qmx_host", "serve", "--home", str(folder), "--port", str(port)],
        cwd=worktree / "qmx-agents",
        stdout=log,
        stderr=log,
    )
    print(f"INFO host pid {host.pid}", flush=True)
    if "--health-and-stop" not in argv:
        return 0
    answered = None
    deadline = time.monotonic() + 90
    try:
        while time.monotonic() < deadline and host.poll() is None:
            token = keyring.get_password("qmx/control-token", "control-token")
            request = urllib.request.Request(f"http://127.0.0.1:{port}/api/health", headers={"Authorization": f"Bearer {token}"})
            try:
                with urllib.request.urlopen(request, timeout=3) as response:
                    answered = response.status
                    break
            except (urllib.error.URLError, OSError):
                time.sleep(1)
    finally:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(host.pid)], capture_output=True, check=False)
        log.close()
    print(("PASS" if answered == 200 else "FAIL") + f" the host's health route answered {answered}", flush=True)
    print(("PASS" if store.is_file() and "control-token" in store.read_text("utf-8") else "FAIL") + " the host kept its token in the throwaway file", flush=True)
    return 0 if answered == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
