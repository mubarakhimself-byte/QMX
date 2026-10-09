import asyncio
from pathlib import Path

from macro_bias import refresh


def run() -> None:
    asyncio.run(refresh(Path.cwd()))


if __name__ == "__main__":
    run()
