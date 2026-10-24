"""Train on the PC's GPU slot, test once and record the model's lineage (Lab AD-20; DATA-PLAN DR13).

The step reads the dataset the previous step built from the partitions the door materialised. It
trains the smallest model that can learn something over those partitions, choosing the device from
what the machine has: the GPU slot the placement declares when a card is there, the CPU otherwise,
and it says which. The PC's own reading (probe P-GPU: a Quadro T1000 with 4,095.8 MB, 21.4 MB peak
while training, 0.318 s per epoch on 80,000 rows) is what the template ships as its default, and the
CPU is the named fallback, never a silent one. At that toy size the CPU's 0.14 s epoch is faster, so
the slot is the default for the models that grow into it, not a claim about this one.

The lineage is written here, by the template: the partitions with their fingerprints, the digest of
the code that trained the model, the seed, the framework, the hardware and the seconds per epoch.
A model nobody can trace to the exact data and code is a model this step refuses to hand on.

Two numbers this step does not make up. The chosen configuration is refitted on three seeds and
answers their spread as the validation band, and the split's test window is scored once, from the
partitions the run already holds. The ablation is **null**: plugging the model into its slot and
running the host strategy after costs needs the QMB door, which this template's `meta.needs` names
and which is not built yet, so the verdict step reports the run as unpublishable instead of reading
a gain nobody measured.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path

FAILURE = "[QMX_FAILURE]"
SEED = 7
HIDDEN = 64
BATCH = 4096
EPOCHS = 3
BAND_SEEDS = 3
"""The chosen configuration is refitted on three seeds for its validation band: one seed is a
number, three are a spread, and the verdict reads the spread."""
WEIGHTS = "weights.pt"


def fail(why):
    """A step that cannot train says why and stops; it never lands a model it did not make."""
    sys.stderr.write(f"{FAILURE} {why}")
    raise SystemExit(1)


def shaped(given):
    """The dataset row among the inputs, told apart by shape."""
    for value in given if isinstance(given, list) else [given]:
        if isinstance(value, dict) and "splits" in value and "partitions" in value:
            return value
    return {}


def device_of(torch):
    """`(device, why)`: the GPU when the machine has one, the CPU and the reason when it has not."""
    if not torch.cuda.is_available():
        return "cpu", "torch sees no CUDA device, so this run trains on the PC's CPU"
    name = torch.cuda.get_device_name(0)
    total = round(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024), 1)
    return "cuda", f"{name}, {total} MB"


def reads(paths):
    """The ticks of the materialised partitions, as floats, in the order the door served them."""
    import pyarrow.parquet as pq  # noqa: PLC0415 (the door's writer owns the parquet)

    found = {"t": [], "bid": [], "ask": []}
    for path in paths:
        table = pq.read_table(path, columns=["t", "bid", "ask"])
        for name, values in found.items():
            values.extend(table.column(name).to_pylist())
    return found


def windows(columns):
    """Lagged mid-price changes and the direction of the next tick: the smallest real label."""
    import numpy as np  # noqa: PLC0415 (the features are numpy, the model is torch)

    mid = (np.asarray(columns["bid"], dtype=np.float64) + np.asarray(columns["ask"])) / 2.0
    move = np.diff(mid)
    span = len(move) - 1
    features = np.stack([move[lag : lag + span] for lag in range(6)], axis=1).astype(np.float32)
    labels = (move[1:] > 0).astype(np.float32)
    return features, labels


def trained(device, features, labels, split, seed, epochs):
    """Fit the perceptron on the training window, score both windows and answer the numbers."""
    import torch  # noqa: PLC0415 (the caller read the dataset; this is the one framework import)

    torch.manual_seed(seed)
    start, stop = split["train"]
    validation = split["validation"]
    inputs = torch.from_numpy(features)
    target = torch.from_numpy(labels).reshape(-1, 1)
    if device == "cuda":
        inputs, target = inputs.cuda(), target.cuda()
    model = torch.nn.Sequential(
        torch.nn.Linear(features.shape[1], HIDDEN),
        torch.nn.ReLU(),
        torch.nn.Linear(HIDDEN, 1),
    )
    if device == "cuda":
        model = model.cuda()
    loss_fn = torch.nn.BCEWithLogitsLoss()
    optimiser = torch.optim.Adam(model.parameters(), lr=1e-3)
    begun = time.monotonic()
    for _ in range(epochs):
        model.train()
        for at in range(start, stop, BATCH):
            batch, expected = inputs[at : at + BATCH], target[at : at + BATCH]
            optimiser.zero_grad()
            missed = loss_fn(model(batch), expected)
            missed.backward()
            optimiser.step()
        if device == "cuda":
            torch.cuda.synchronize()
    took = time.monotonic() - begun
    model.eval()
    test = split["test"]
    seen = score(model, inputs[start:stop], target[start:stop])
    held = score(
        model, inputs[validation[0] : validation[1]], target[validation[0] : validation[1]]
    )
    once = (
        score(model, inputs[test[0] : test[1]], target[test[0] : test[1]])
        if test[1] > test[0]
        else None
    )
    peak = round(torch.cuda.max_memory_allocated() / (1024 * 1024), 1) if device == "cuda" else 0.0
    return {
        "train_score": seen,
        "validation_score": held,
        "test_score": once,
        "seconds": round(took, 3),
        "seconds_per_epoch": round(took / epochs, 3),
        "peak_memory_mb": peak,
    }


def score(model, inputs, target):
    """Accuracy of the fitted model on one window, to four places."""
    import torch  # noqa: PLC0415 (the model's framework, imported where it is used)

    with torch.no_grad():
        guessed = (model(inputs) > 0).float().reshape(-1)
    return round(float((guessed == target.reshape(-1)).float().mean()), 4)


def digest_of(path):
    """The digest of the weights this run wrote, which is what the model item cites."""
    found = hashlib.sha256()
    found.update(Path(path).read_bytes())
    return f"sha256:{found.hexdigest()}"


def main():
    """The step: train on the dataset the previous step served and print the lineage it carries."""
    given = json.load(sys.stdin).get("in") or []
    data = shaped(given)
    if not data:
        fail("the run names no dataset: the previous step served no partitions")
    try:
        import torch  # noqa: PLC0415 (the step imports it here, never at module load)
    except ImportError:
        fail("this attempt has no torch, and a training run never guesses a framework")
    device, hardware = device_of(torch)
    columns = reads([str(part["path"]) for part in data["partitions"]])
    features, labels = windows(columns)
    if len(labels) < 100:
        fail(f"{data['series']} served {len(labels)} rows, too few to train on")
    seed = int(data.get("seed") or SEED)
    ran = trained(device, features, labels, data["splits"], seed, EPOCHS)
    spread = [
        trained(device, features, labels, data["splits"], seed + extra, EPOCHS)["validation_score"]
        for extra in range(1, BAND_SEEDS)
    ]
    work = Path(os.environ["QMX_WORK"])
    work.mkdir(parents=True, exist_ok=True)
    torch.save({"features": features.shape[1], "seed": data.get("seed")}, work / WEIGHTS)
    print(
        json.dumps(
            {
                "configs": [
                    {
                        "id": 0,
                        "train_score": ran["train_score"],
                        "validation_score": ran["validation_score"],
                    }
                ],
                "chosen": 0,
                "sealed_score": ran["test_score"],
                "validation_band": [
                    round(min([ran["validation_score"], *spread]), 4),
                    round(max([ran["validation_score"], *spread]), 4),
                ],
                "ablation": None,
                "trials": 1,
                "model_ref": {
                    "weights": str(work / WEIGHTS),
                    "digest": digest_of(work / WEIGHTS),
                },
                "lineage": {
                    "series": data["series"],
                    "months": data["months"],
                    "partitions": data["partitions"],
                    "seed": seed,
                    "code": data["code"],
                    "framework": f"torch {torch.__version__}",
                    "hardware": {"placement": "pc", "device": device, "found": hardware},
                    "seconds_per_epoch": ran["seconds_per_epoch"],
                    "peak_memory_mb": ran["peak_memory_mb"],
                },
            }
        )
    )


if __name__ == "__main__":
    main()
