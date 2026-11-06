"""Measure the tilt of every raw scan and compare it with README.md.

Outputs, to see the effect of changes in 'scan_postprocess.tilt':

- stdout: one line per scan plus a summary (run 'pytest -s').
- DIRECTORY_SCANS_RESULTS / "tilt.md": the same table. It is committed:
  'git diff' shows which scans changed.
- DIRECTORY_SCANS_RESULTS / "tilt_preview/*.jpg": every scan deskewed with
  the measured tilt and overlaid with horizontal lines. Not committed.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
import time

from PIL import Image, ImageDraw

from scan_postprocess.tilt import TILT_MAX_DEGREES, estimate_tilt

DIRECTORY_SCANS = pathlib.Path(__file__).parent / "scans_0_raw"
FILENAME_README = DIRECTORY_SCANS / "README.md"
DIRECTORY_SCANS_RESULTS = pathlib.Path(__file__).parent / "scans_0_raw_results"
FILENAME_TILT_RESULTS = DIRECTORY_SCANS_RESULTS / "tilt.md"
DIRECTORY_TILT_PREVIEW = DIRECTORY_SCANS_RESULTS / "tilt_preview"

TILT_TOLERANCE_DEGREES = 0.5
PREVIEW_WIDTH = 1240
PREVIEW_LINE_DISTANCE = 40

_RE_SCAN = re.compile(
    r"^- (?P<filename>\S+\.png)"
    r" type=(?P<type>bw|indexed|color)"
    r" tilt=(?P<tilt>-?\d+(\.\d+)?)degrees"
    r" content=(?P<content>machine|hand|images|mix)$"
)


@dataclasses.dataclass(frozen=True)
class ScanAttributes:
    filename: str
    type: str
    tilt: float
    content: str


@dataclasses.dataclass(frozen=True)
class TiltResult:
    attributes: ScanAttributes
    tilt_measured: float

    @property
    def diff(self) -> float:
        return self.tilt_measured - self.attributes.tilt

    @property
    def ok(self) -> bool:
        return abs(self.diff) <= TILT_TOLERANCE_DEGREES

    @property
    def line(self) -> str:
        a = self.attributes
        return (
            f"| {a.filename} | {a.type} | {a.content}"
            f" | {a.tilt:+.2f} | {self.tilt_measured:+.2f} | {self.diff:+.2f}"
            f" | {'ok' if self.ok else 'FAIL'} |"
        )


def read_scan_attributes() -> dict[str, ScanAttributes]:
    attributes: dict[str, ScanAttributes] = {}
    for line in FILENAME_README.read_text().splitlines():
        match = _RE_SCAN.match(line)
        if match is None:
            continue
        a = ScanAttributes(
            filename=match["filename"],
            type=match["type"],
            tilt=float(match["tilt"]),
            content=match["content"],
        )
        attributes[a.filename] = a
    return attributes


def write_preview(image: Image.Image, tilt: float, filename: pathlib.Path) -> None:
    """Deskew with the measured tilt and draw horizontal reference lines."""
    scale = PREVIEW_WIDTH / image.width
    preview = image.convert("RGB").resize(
        (PREVIEW_WIDTH, round(image.height * scale)),
        resample=Image.Resampling.BOX,
    )
    preview = preview.rotate(-tilt, fillcolor="white")
    draw = ImageDraw.Draw(preview)
    for y in range(0, preview.height, PREVIEW_LINE_DISTANCE):
        draw.line((0, y, preview.width, y), fill="red", width=1)
    draw.text((10, 10), f"{filename.stem}: deskewed by {-tilt:+.2f}", fill="blue")
    preview.save(filename, quality=80)


def test_tilt() -> None:
    scan_attributes = read_scan_attributes()
    scan_files = sorted(DIRECTORY_SCANS.glob("*.png"))
    assert sorted(scan_attributes) == [f.name for f in scan_files], (
        f"{FILENAME_README} must list exactly the scans in {DIRECTORY_SCANS}"
    )

    DIRECTORY_TILT_PREVIEW.mkdir(parents=True, exist_ok=True)
    header = [
        "| file | type | content | README.md | measured | diff | result |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    print()
    print("\n".join(header))

    results: list[TiltResult] = []
    start = time.monotonic()
    for filename in scan_files:
        with Image.open(filename) as image:
            # Measured from the pixels of the PNG (Pillow + numpy).
            tilt = estimate_tilt(image)
            write_preview(image, tilt, DIRECTORY_TILT_PREVIEW / f"{filename.stem}.jpg")
        result = TiltResult(
            attributes=scan_attributes[filename.name], tilt_measured=tilt
        )
        results.append(result)
        print(result.line)
    duration_s = time.monotonic() - start

    failed = [r for r in results if not r.ok]
    summary = [
        f"Tolerance: {TILT_TOLERANCE_DEGREES:.2f} degrees",
        f"Failed: {len(failed)} of {len(results)}",
        f"Max abs diff: {max(abs(r.diff) for r in results):.2f} degrees",
        f"Mean abs diff: {sum(abs(r.diff) for r in results) / len(results):.3f} degrees",
    ]
    print()
    print("\n".join(summary))
    # Not written to the results file: it would change on every run.
    print(f"Duration: {duration_s:.1f}s")
    print(f"Results: {FILENAME_TILT_RESULTS}")
    print(f"Previews: {DIRECTORY_TILT_PREVIEW}")

    FILENAME_TILT_RESULTS.write_text(
        "# Tilt results\n\n"
        "Written by tests/scan_postprocess/test_scan_postprocess.py,"
        " tilt in degrees.\n\n"
        + "\n".join(header + [r.line for r in results])
        + "\n\n"
        + "\n".join(f"- {s}" for s in summary)
        + "\n"
    )

    for r in results:
        assert -TILT_MAX_DEGREES <= r.tilt_measured <= TILT_MAX_DEGREES
    assert not failed, "Tilt differs from README.md: " + ", ".join(
        r.attributes.filename for r in failed
    )
