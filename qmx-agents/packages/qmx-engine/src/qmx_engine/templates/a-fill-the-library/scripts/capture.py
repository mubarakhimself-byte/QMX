"""Funnel stage 2, neutral capture. A video gets its captions through `yt-dlp`, native ones first,
then automatic ones, and nothing else: Whisper needs a key, so a video with no captions is recorded
as `no captions` and the run goes on without it. A note is kept as written. A paper, a TradingView
script or another link is recorded as not captured, naming the tool it needs. A fixture run reads
`fixtures/captions.json`, where a null transcript stands for a video with no captions.

Prints every row, captured or not, with its transcript segments (seconds) or text."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

NEEDS = {
    "paper": "not captured: PDF to text needs the PDF tool",
    "tradingview": "not captured: a TradingView page needs the browser",
    "link": "not captured: a web page needs the browser",
}


def segments_of(path):
    events = json.loads(path.read_text("utf-8")).get("events", [])
    found = []
    for event in events:
        text = " ".join("".join(s.get("utf8", "") for s in event.get("segs") or []).split())
        if text:
            start = event.get("tStartMs", 0) / 1000
            end = start + event.get("dDurationMs", 0) / 1000
            found.append({"start": start, "end": end, "text": text})
    return found


def captions(row):
    """The video's segments and which captions they are, or why there are none."""
    tool = shutil.which("yt-dlp")
    if tool is None:
        return None, "no captions: yt-dlp is not installed"
    out = Path("captions")
    out.mkdir(exist_ok=True)
    kinds = (("--write-subs", "native captions"), ("--write-auto-subs", "automatic captions"))
    for flag, label in kinds:
        name = str(out / f"{row['id']}.%(ext)s")
        argv = [tool, "--skip-download", flag, "--sub-langs", "en.*,en", "--sub-format", "json3"]
        argv += ["-o", name, row["locator"]]
        subprocess.run(argv, capture_output=True, timeout=120, check=False)
        found = sorted(out.glob(f"{row['id']}*.json3"))
        if found:
            return segments_of(found[0]), label
    return None, "no captions"


given = json.load(sys.stdin)["in"]
fixture = None
if given.get("fixture"):
    path = Path(__file__).parents[1] / "fixtures" / "captions.json"
    fixture = json.loads(path.read_text("utf-8"))["captions"]
captured = []
for listed in given["inventory"]:
    row = dict(listed)
    if row["kind"] == "note":
        row |= {"capture": "as written", "text": row["locator"]}
    elif row["kind"] != "video":
        row["capture"] = NEEDS[row["kind"]]
    else:
        if fixture is not None:
            found = fixture.get(row["locator"])
            segments, label = (found, "native captions") if found else (None, "no captions")
        else:
            segments, label = captions(row)
        row["capture"] = label
        if segments:
            row["segments"] = segments
    captured.append(row)
print(json.dumps(captured))
