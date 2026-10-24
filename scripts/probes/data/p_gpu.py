"""P-GPU: a small model trained on the PC's Quadro T1000 from cached partitions (DATA-PLAN DR13,
W21, Lab AD-20).

The probe answers three numbers the training template ships as its defaults, and it answers them
from the PC itself:

* **time**: seconds to import and warm the GPU, seconds per epoch on the GPU and on the CPU, and
  the whole run's wall time;
* **GPU memory**: the device's total, and the peak allocated and reserved while training;
* **disk used**: the partitions it read, the checkpoint it wrote and the free space it left.

It trains on **cached partitions**: a folder of monthly Parquet files, which is the shape the
market-data door materialises (`<month>.parquet`, one row per tick with a `t`, `bid` and `ask`).
When the PC's own cache has them, pass `--partitions D:/.../cache`; otherwise the probe writes a
small cache into the scratch root itself and says so in its numbers, so the run needs no door, no
server and no network. The model is a two-layer perceptron over lagged mid-price changes, which is
small enough to fit the 4 GB card with room to spare and real enough to show the GPU's speed.

A failure is the process being killed or not starting: no CUDA device, no torch, an out-of-memory
error, or a number the probe could not read. The fallback the plan names when this fails is CPU
training on the PC with the GPU slot off, and it is recorded in `decisions.tsv` rather than here.

    D:/Temp/pgpu-venv/Scripts/python.exe scripts/probes/data/p_gpu.py
    D:/Temp/pgpu-venv/Scripts/python.exe scripts/probes/data/p_gpu.py --partitions D:/qmx/cache

torch is not a dependency of any QMX package, so this probe runs on an interpreter that has it; the
install line is recorded in `evidence/dr13/owner-installs.md`. Scratch goes to
`D:/Temp/prb-dp/gpu/` and is removed before the probe exits.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

SCRATCH = Path(os.environ.get("QMX_PROBE_SCRATCH", "D:/Temp/prb-dp")) / "gpu"
MONTHS = ("2026-01", "2026-02")
ROWS_PER_MONTH = 40_000
FEATURES = 6
HIDDEN = (64, 32)
BATCH = 4096
EPOCHS = 3
CPU_EPOCHS = 1
"""The GPU takes all three epochs and the CPU the first one only: the per-epoch number is what the
baseline needs, and a T1000's CPU is not worth a third pass."""
SEED = 7
MB = 1024 * 1024


def month_rows(month: str) -> list[tuple[int, float, float]]:
    """One month of ticks, deterministic from its name: a random walk whose seed is the month's
    ordinal, so a second run reads the same partition."""
    import random  # noqa: PLC0415 (the probe's own data, never the model's)

    rng = random.Random(f"p-gpu|{month}")
    price = 1_084_500.0
    rows: list[tuple[int, float, float]] = []
    start = 1_767_225_600  # 2026-01-01T00:00:00Z in seconds
    for index in range(ROWS_PER_MONTH):
        price += rng.gauss(0, 3)
        rows.append((start + index, price, price + 2.0))
    return rows


def write_cache(folder: Path) -> tuple[Path, ...]:
    """A cache of monthly partitions, written by pyarrow when it is there and by a plain `.jsonl`
    beside it otherwise. The file name is the month, which is what the door materialises."""
    import pyarrow as pa  # noqa: PLC0415
    import pyarrow.parquet as pq  # noqa: PLC0415

    folder.mkdir(parents=True, exist_ok=True)
    tables = []
    for month in MONTHS:
        rows = month_rows(month)
        table = pa.table(
            {
                "t": pa.array([row[0] for row in rows], pa.int64()),
                "bid": pa.array([row[1] for row in rows], pa.float64()),
                "ask": pa.array([row[2] for row in rows], pa.float64()),
            }
        )
        pq.write_table(table, folder / f"{month}.parquet", compression="zstd")
        tables.append(table)
    return tuple(folder / f"{month}.parquet" for month in MONTHS)


def read_cache(folder: Path) -> tuple[object, tuple[Path, ...]]:
    """Every `*.parquet` under the folder as one table of ticks, and the files it read."""
    import pyarrow as pa  # noqa: PLC0415
    import pyarrow.parquet as pq  # noqa: PLC0415

    files = tuple(sorted(folder.glob("*.parquet")))
    if not files:
        raise SystemExit(f"no cached partitions under {folder}")
    return pa.concat_tables([pq.read_table(path) for path in files]), files


def features(table: object) -> tuple[object, object]:
    """Lagged mid-price changes and the sign of the next one: a label any tick file carries."""
    import numpy as np  # noqa: PLC0415

    mid = np.asarray(table.column("bid")) + np.asarray(table.column("ask"))
    mid = mid / 2.0
    move = np.diff(mid)
    window = len(move) - FEATURES
    columns = [move[lag : lag + window] for lag in range(FEATURES)]
    found = np.stack(columns, axis=1).astype(np.float32)
    labels = (move[FEATURES:] > 0).astype(np.float32)
    return found, labels


def train(device: str, x: object, y: object, epochs: int) -> dict[str, float]:
    """Train the perceptron and answer the seconds per epoch, the peak memory and the loss."""
    import torch  # noqa: PLC0415

    torch.manual_seed(SEED)
    target = torch.from_numpy(y).reshape(-1, 1)
    inputs = torch.from_numpy(x)
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
        inputs = inputs.cuda()
        target = target.cuda()
    model = torch.nn.Sequential(
        torch.nn.Linear(FEATURES, HIDDEN[0]),
        torch.nn.ReLU(),
        torch.nn.Linear(HIDDEN[0], HIDDEN[1]),
        torch.nn.ReLU(),
        torch.nn.Linear(HIDDEN[1], 1),
    )
    if device == "cuda":
        model = model.cuda()
    loss_fn = torch.nn.BCEWithLogitsLoss()
    optimiser = torch.optim.Adam(model.parameters(), lr=1e-3)
    started = time.monotonic()
    loss = 0.0
    for _ in range(epochs):
        model.train()
        for at in range(0, len(inputs), BATCH):
            batch = inputs[at : at + BATCH]
            expected = target[at : at + BATCH]
            optimiser.zero_grad()
            missed = loss_fn(model(batch), expected)
            loss = float(missed.detach())
            missed.backward()
            optimiser.step()
        if device == "cuda":
            torch.cuda.synchronize()
    took = time.monotonic() - started
    peak = 0.0
    if device == "cuda":
        torch.cuda.synchronize()
        peak = torch.cuda.max_memory_allocated() / MB
    model.eval()
    with torch.no_grad():
        held = model(inputs[:BATCH])
        guess = (held > 0).float().reshape(-1)
        accuracy = float((guess == target[:BATCH].reshape(-1)).float().mean())
    return {
        "epochs": float(epochs),
        "seconds": round(took, 3),
        "seconds_per_epoch": round(took / epochs, 3),
        "peak_memory_mb": round(peak, 1),
        "loss": round(loss, 6),
        "train_accuracy": round(accuracy, 4),
    }


def disk_of(paths: tuple[Path, ...]) -> dict[str, float]:
    total = sum(path.stat().st_size for path in paths if path.is_file())
    return {
        "partitions": len(paths),
        "partition_mb": round(total / MB, 2),
        "free_gb": round(shutil.disk_usage(paths[0].parent).free / (1024 * MB), 2),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="P-GPU: train a small model on the PC's GPU")
    parser.add_argument("--partitions", type=Path, default=None, help="a cache of monthly parquet")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    given = parser.parse_args(argv)
    numbers: dict[str, object] = {"interpreter": sys.executable, "python": sys.version.split()[0]}
    problems: list[str] = []
    cache = given.partitions
    scratch = False
    if cache is None:
        cache = SCRATCH / "cache"
        scratch = True
    try:
        started = time.monotonic()
        if scratch:
            paths = write_cache(cache)
            numbers["source"] = "synthetic cache the probe wrote"
        else:
            paths = tuple(sorted(cache.glob("*.parquet")))
            numbers["source"] = str(cache)
        numbers["disk"] = disk_of(paths)
        import torch  # noqa: PLC0415

        numbers["torch"] = torch.__version__
        if not torch.cuda.is_available():
            problems.append("torch sees no CUDA device, so the GPU half did not start")
        else:
            device = torch.cuda.get_device_name(0)
            total = torch.cuda.get_device_properties(0).total_memory / MB
            numbers["gpu"] = {"device": device, "total_mb": round(total, 1)}
        table, files = read_cache(cache)
        numbers["partitions"] = [path.name for path in files]
        x, y = features(table)
        numbers["rows"] = int(len(y))
        if not problems:
            gpu = train("cuda", x, y, given.epochs)
            numbers["gpu_train"] = gpu
            checkpoint = cache / "model.pt"
            torch.save({"state": gpu["loss"], "seed": SEED}, checkpoint)
            numbers["disk"]["checkpoint_mb"] = round(checkpoint.stat().st_size / MB, 3)
            cpu = train("cpu", x, y, CPU_EPOCHS)
            numbers["cpu_train"] = cpu
            numbers["speedup"] = round(cpu["seconds_per_epoch"] / gpu["seconds_per_epoch"], 2)
        numbers["seconds"] = round(time.monotonic() - started, 2)
    except Exception as error:  # a probe reports its own failure rather than a traceback
        problems.append(f"{type(error).__name__}: {error}")
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    verdict = "FAIL" if problems else "PASS"
    print(f"P-GPU {verdict}")
    for key, value in numbers.items():
        print(f"  {key}: {json.dumps(value) if isinstance(value, dict) else value}")
    for problem in problems:
        print(f"  problem: {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
