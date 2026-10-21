"""`qmx_host`: the one composition root (AD-52). Nothing imports it; `python -m qmx_host` runs it.

Kept free of imports, because `python -m qmx_host` loads this before `__main__` scrubs the
environment.
"""
