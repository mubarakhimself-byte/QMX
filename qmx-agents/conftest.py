"""Keep automatic parallel runs within the laptop's memory budget."""

import os

import pytest


@pytest.hookimpl(optionalhook=True)
def pytest_xdist_auto_num_workers() -> int:
    return min(2, os.process_cpu_count() or 1)
