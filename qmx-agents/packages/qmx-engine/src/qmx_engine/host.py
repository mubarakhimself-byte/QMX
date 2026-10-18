"""`python -m qmx_engine.host`: forwards to `qmx_host` for one release (AD-52), then goes (DEL2)."""

import runpy

if __name__ == "__main__":
    runpy.run_module("qmx_host", run_name="__main__", alter_sys=True)
