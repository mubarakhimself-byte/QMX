"""Run Docling alone, in this child process, and print one document's text and locators.

The extract step the upload door and the capture path feed (Library AD-27): it takes a path to
the bytes and the media type, and prints the whole text, one text per page (or one per segment
for audio), its extractor version and the memory it peaked at. Docling does the reading; nothing
else does, and no model from QMX runs here.

The interpreter this runs under is the extraction child, so the memory P-DOCLING measured is a
cap on it, not on the host: `RLIMIT_AS` is set before Docling is imported. A build without
Docling says so and lands nothing rather than guessing at text.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any

try:
    import resource
except ImportError:  # a Windows PC has no RLIMIT_AS; the step's timeout is the only bound
    resource = None  # type: ignore[assignment]

DOCLING_PIN = "2.134.0"
LIMIT_MB = 9216
"""P-DOCLING's 7,334 MB peak plus a quarter of headroom, as a cap on this child (AD-27)."""
HERE = Path(__file__).parents[1]


def cap_memory(limit_mb: int = LIMIT_MB) -> bool:
    """Cap this process's address space before Docling is imported; false where POSIX is absent."""
    if resource is None:
        return False
    try:
        cap = limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
        return True
    except AttributeError, OSError, ValueError:
        return False


def peak_mb() -> int:
    """This child's peak resident memory, which is the number P-DOCLING measured."""
    if resource is None:
        return 0
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) // 1024


def audio_format() -> Any:
    """Docling's audio input format, named where an older build fails with a clear message."""
    from docling.datamodel.base_models import InputFormat  # noqa: PLC0415

    if not hasattr(InputFormat, "AUDIO"):
        raise RuntimeError(f"docling {DOCLING_PIN} has no audio pipeline (InputFormat.AUDIO)")
    return InputFormat.AUDIO


def whole_text(document: Any) -> str:
    """The document's text, whichever export this Docling build offers."""
    for name in ("export_to_text", "export_to_markdown"):
        export = getattr(document, name, None)
        if callable(export):
            return str(export())
    return ""


def page_texts(document: Any) -> list[dict[str, Any]]:
    """One `{page, text}` per page, when the build keeps page-level text."""
    pages = getattr(document, "pages", {}) or {}
    found: list[dict[str, Any]] = []
    for number in sorted(pages):
        page = pages[number]
        export = getattr(page, "export_to_text", None)
        text = str(export(document)) if callable(export) else ""
        found.append({"page": int(number), "text": text})
    return found


def extract(path: Path, kind: str) -> dict[str, Any]:
    """One extraction, with its text, locators, version, seconds and peak memory."""
    capped = cap_memory()
    began = time.perf_counter()
    import docling  # noqa: PLC0415 (the extraction child's own install)
    from docling.document_converter import DocumentConverter  # noqa: PLC0415

    converter = (
        DocumentConverter()
        if kind != "audio"
        else DocumentConverter(allowed_formats=[audio_format()])
    )
    document = converter.convert(str(path)).document
    text = whole_text(document)
    return {
        "status": "extracted",
        "kind": kind,
        "text": text,
        "pages": page_texts(document) if kind != "audio" else [],
        "transcript": text if kind == "audio" else "",
        "frames": [],
        "extractor_version": f"docling-{getattr(docling, '__version__', DOCLING_PIN)}",
        "seconds": round(time.perf_counter() - began, 1),
        "peak_mb": peak_mb(),
        "capped": capped,
    }


def media_kind(path: Path, media_type: str) -> str:
    """Document, audio or image, from the media type and else the suffix."""
    lowered = media_type.lower()
    if lowered.startswith("audio/") or path.suffix.lower() in (".mp3", ".wav", ".m4a", ".flac"):
        return "audio"
    if lowered.startswith("image/") or path.suffix.lower() in (".png", ".jpg", ".jpeg", ".tif"):
        return "image"
    return "pdf"


def main() -> int:
    given = json.load(sys.stdin).get("in") or {}
    if given.get("fixture"):
        fixture = HERE / "fixtures" / "extracted.json"
        print(fixture.read_text("utf-8"))
        return 0
    target = Path(str(given.get("path") or given.get("original") or ""))
    if not target.is_file():
        print(json.dumps({"status": "unavailable", "reason": f"no file at {target}"}))
        return 0
    kind = media_kind(target, str(given.get("media_type") or ""))
    try:
        result = extract(target, kind)
    except ImportError:
        print(
            json.dumps(
                {
                    "status": "unavailable",
                    "reason": f"docling {DOCLING_PIN} is not installed in this python",
                }
            )
        )
        return 0
    except Exception as error:
        print(json.dumps({"status": "failed", "reason": f"{type(error).__name__}: {error}"}))
        return 0
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
