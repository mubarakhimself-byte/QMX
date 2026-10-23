"""P-DOCLING: Docling 2.134.0's time and peak memory for a 400-page PDF and one hour of audio.

Both legs run on the server's own CPU, each in a child process in its own session, so the memory
figure is that run's peak resident memory and a killed child is visible as a signal exit code
rather than a swallowed exception.

The PDF is a public GNU manual, sliced to its first 400 pages when a page library is available
(so the run is the same 400 pages every time); the audio is a public LibriVox chapter of about an
hour. Both downloads are kept under the probe root and reused, so a rerun measures Docling and
not the network.

Run it on the server as `qmx` from `/srv/qmx/check/prb-ds/checkout`:

    /srv/qmx/check/prb-ds/venv-docling/bin/python scripts/probes/data/p_docling.py

`--pdf-only` and `--audio-only` narrow the run to one leg. A Docling build with no audio pipeline
prints the audio leg as `not run` with that reason instead of inventing a number.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Final

import server_common as common

PROBE: Final[str] = "P-DOCLING"
DOCLING_PIN: Final[str] = "2.134.0"
PDF_URL: Final[str] = "https://www.gnu.org/software/emacs/manual/pdf/emacs.pdf"
"""GNU Emacs manual: public, stable, and longer than 400 pages, so the slice is always full."""
PDF_PAGES: Final[int] = 400
AUDIO_URL: Final[str] = (
    "https://archive.org/download/itineraire_2208_librivox/itineraire_05_chateaubriand.mp3"
)
"""One 63-minute public-domain LibriVox chapter, so the leg is one file of about an hour."""
SUMMARY: Final[Path] = common.PROBE_ROOT / "logs" / "p_docling-work.json"
DOWNLOADS: Final[Path] = common.PROBE_ROOT / "downloads"


def download(url: str, target: Path, log: common.Log) -> Path:
    """Fetch `url` once. A second run reuses the file, so Docling is what gets measured."""
    existed = target.exists()
    common.download_file(url, target)
    log.say(
        f"{'reuse' if existed else 'download'} {url if not existed else target} "
        f"({target.stat().st_size // 1024} KB)"
    )
    return target


def slice_pdf(source: Path, target: Path, pages: int, log: common.Log) -> Path:
    """The first `pages` pages as their own PDF, when a page library can write one."""
    try:
        from pypdf import PdfReader, PdfWriter  # noqa: PLC0415
    except ImportError:
        log.say("no pypdf in this venv: the whole document is the PDF leg")
        return source
    reader = PdfReader(str(source))
    if len(reader.pages) < pages:
        log.say(f"the source has {len(reader.pages)} pages, under {pages}: using all of them")
        pages = len(reader.pages)
    writer = PdfWriter()
    for page in reader.pages[:pages]:
        writer.add_page(page)
    with target.open("wb") as out:
        writer.write(out)
    log.say(f"slice: {pages} pages into {target}")
    return target


def work(kind: str, source: Path) -> int:
    """One measured extraction, in the child. Writes its own summary for the parent to judge."""
    summary: dict[str, object] = {"kind": kind, "started": False, "errors": []}
    began = time.perf_counter()
    try:
        import docling  # noqa: PLC0415 - the probe's venv imports it, not the checkout
        from docling.document_converter import DocumentConverter  # noqa: PLC0415

        summary["docling_version"] = getattr(docling, "__version__", DOCLING_PIN)
        converter = (
            DocumentConverter()
            if kind == "pdf"
            else DocumentConverter(allowed_formats=[_audio_format()])
        )
        summary["started"] = True
        document = converter.convert(str(source)).document
        summary["pages"] = len(getattr(document, "pages", {}) or {})
        summary["seconds"] = round(time.perf_counter() - began, 1)
        summary["peak_mb"] = common.group_peak_mb(__import__("os").getpgrp())
        summary["chars"] = len(document.export_to_markdown())
    except Exception as error:
        summary["errors"].append(f"{type(error).__name__}: {error}")
        summary["seconds"] = round(time.perf_counter() - began, 1)
    finally:
        SUMMARY.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary))
    return 0 if summary["started"] and not summary["errors"] else 1


def _audio_format() -> object:
    """Docling's audio input format, named here so an older build fails with a clear message."""
    from docling.datamodel.base_models import InputFormat  # noqa: PLC0415

    if not hasattr(InputFormat, "AUDIO"):
        raise RuntimeError(f"docling {DOCLING_PIN} has no audio pipeline (InputFormat.AUDIO)")
    return InputFormat.AUDIO


def judge(legs: dict[str, dict[str, object]], runs: dict[str, common.ChildRun]) -> common.Report:
    report = common.Report(PROBE)
    for kind, run in runs.items():
        summary = legs.get(kind, {})
        prefix = kind
        report.numbers[f"{prefix}_version"] = summary.get("docling_version", DOCLING_PIN)
        report.numbers[f"{prefix}_seconds"] = summary.get("seconds", run.seconds)
        report.numbers[f"{prefix}_peak_mb"] = run.peak_mb or summary.get("peak_mb")
        if kind == "pdf":
            report.numbers["pdf_pages"] = summary.get("pages")
        if kind == "audio":
            report.numbers["audio_chars"] = summary.get("chars")
        if summary.get("errors"):
            report.fail(f"{kind}: {summary['errors'][0]}")
        elif run.returncode < 0:
            report.fail(f"{kind}: the process was killed (signal {-run.returncode})")
        elif not summary.get("started"):
            report.fail(f"{kind}: docling does not start")
        else:
            report.note(
                f"{kind}: {summary.get('seconds', run.seconds)} s, {run.peak_mb} MB peak, "
                f"exit {run.returncode}"
            )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-url", default=PDF_URL)
    parser.add_argument("--audio-url", default=AUDIO_URL)
    parser.add_argument("--pages", type=int, default=PDF_PAGES)
    parser.add_argument("--pdf-only", action="store_true")
    parser.add_argument("--audio-only", action="store_true")
    parser.add_argument("--timeout", type=float, default=3600.0)
    parser.add_argument("--work", choices=("pdf", "audio"), default=None)
    parser.add_argument("--source", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.work is not None:
        if args.source is None:
            parser.error("--work needs --source")
        return work(args.work, args.source)

    log = common.Log("prb-ds-docling")
    try:
        legs: dict[str, dict[str, object]] = {}
        runs: dict[str, common.ChildRun] = {}
        if not args.audio_only:
            source = slice_pdf(
                download(args.pdf_url, DOWNLOADS / "p_docling.pdf", log),
                DOWNLOADS / "p_docling-400.pdf",
                args.pages,
                log,
            )
            runs["pdf"] = common.run_child(
                "prb-ds-docling-pdf",
                [sys.executable, str(Path(__file__)), "--work", "pdf", "--source", str(source)],
                timeout_s=args.timeout,
            )
            legs["pdf"] = _summary(log, "pdf")
        if not args.pdf_only:
            audio = download(args.audio_url, DOWNLOADS / "p_docling-audio.mp3", log)
            runs["audio"] = common.run_child(
                "prb-ds-docling-audio",
                [sys.executable, str(Path(__file__)), "--work", "audio", "--source", str(audio)],
                timeout_s=args.timeout,
            )
            legs["audio"] = _summary(log, "audio")
        report = judge(legs, runs)
        for kind, run in runs.items():
            log.say(f"{kind}: exit {run.returncode} in {run.seconds} s, log {run.log}")
        return report.render()
    finally:
        log.close()


def _summary(log: common.Log, kind: str) -> dict[str, object]:
    if not SUMMARY.exists():
        log.say(f"{kind}: the child wrote no summary at {SUMMARY}")
        return {}
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    log.say(f"{kind}: {json.dumps(summary)}")
    return summary


if __name__ == "__main__":
    raise SystemExit(main())
