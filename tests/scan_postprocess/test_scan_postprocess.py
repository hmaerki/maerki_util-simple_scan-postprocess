"""Process every raw scan and compare the results with README.md.

Outputs, to see the effect of changes in 'scan_postprocess':

- stdout: one line per scan plus a summary (run 'pytest -s').
- DIRECTORY_SCANS_RESULTS / "tilt.md", "border.md": the same tables. They are
  committed: 'git diff' shows which scans changed.
- DIRECTORY_SCANS_RESULTS / "tilt_preview/*.png": every scan deskewed with
  the measured tilt and overlaid with horizontal lines. Not committed.
- DIRECTORY_SCANS_RESULTS / "border_preview/*.png": every scan with the
  removed border painted magenta. Not committed.
- DIRECTORY_SCANS_RESULTS / "tilt_border.md": tilt measured on the raw scan
  versus after border removal. Committed.
- DIRECTORY_SCANS_RESULTS / "tilt_border_preview/*.png": every scan with the
  border removed and deskewed (scan_postprocess.postprocess). Not committed.
- DIRECTORY_SCANS_RESULTS / "bw.md": levels and file sizes, every scan
  converted with convert_bw. Committed.
- DIRECTORY_SCANS_RESULTS / "bw_preview/*_bw16.png": every scan,
  postprocessed and converted to GRAY_LEVELS gray levels, full resolution,
  compressed. Not committed.
- DIRECTORY_SCANS_RESULTS / "indexed.md": levels and file sizes, every scan
  converted with convert_indexed. Committed.
- DIRECTORY_SCANS_RESULTS / "indexed_preview/*_color32.png": every scan,
  postprocessed, smoothed, reduced to PALETTE_COLORS colors and
  near-identical colors merged, full resolution, compressed. Not committed.

Every test processes every scan, whatever its 'type' in README.md: this
shows how each conversion behaves on the other types too. The summaries
add subtotals per type.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
import time

from PIL import Image, ImageDraw

from scan_postprocess.border import remove_border
from scan_postprocess.bw import (
    BACKGROUND_COLOR_FRACTION,
    FILENAME_POSTFIX as FILENAME_POSTFIX_BW,
    FOREGROUND_COLOR_FRACTION,
    GRAY_LEVELS,
    convert_bw,
    save_png_compressed,
)
from scan_postprocess.indexed import (
    BLUR_RADIUS,
    FILENAME_POSTFIX as FILENAME_POSTFIX_INDEXED,
    MERGE_DISTANCE,
    PALETTE_COLORS,
    convert_indexed,
)
from scan_postprocess.postprocess import postprocess
from scan_postprocess.tilt import TILT_MAX_DEGREES, estimate_tilt

DIRECTORY_SCANS = pathlib.Path(__file__).parent / "scans_0_raw"
FILENAME_README = DIRECTORY_SCANS / "README.md"
DIRECTORY_SCANS_RESULTS = pathlib.Path(__file__).parent / "scans_0_raw_results"
FILENAME_TILT_RESULTS = DIRECTORY_SCANS_RESULTS / "tilt.md"
DIRECTORY_TILT_PREVIEW = DIRECTORY_SCANS_RESULTS / "tilt_preview"
FILENAME_BORDER_RESULTS = DIRECTORY_SCANS_RESULTS / "border.md"
DIRECTORY_BORDER_PREVIEW = DIRECTORY_SCANS_RESULTS / "border_preview"
FILENAME_TILT_BORDER_RESULTS = DIRECTORY_SCANS_RESULTS / "tilt_border.md"
DIRECTORY_TILT_BORDER_PREVIEW = DIRECTORY_SCANS_RESULTS / "tilt_border_preview"
FILENAME_BW_RESULTS = DIRECTORY_SCANS_RESULTS / "bw.md"
DIRECTORY_BW_PREVIEW = DIRECTORY_SCANS_RESULTS / "bw_preview"
FILENAME_INDEXED_RESULTS = DIRECTORY_SCANS_RESULTS / "indexed.md"
DIRECTORY_INDEXED_PREVIEW = DIRECTORY_SCANS_RESULTS / "indexed_preview"

TILT_TOLERANCE_DEGREES = 0.5
PREVIEW_WIDTH = 1240
PREVIEW_LINE_DISTANCE = 40

BORDER_MIN_PERCENT = 1.0
"""More removed than this: the scan has a border (thin edge lines are less)."""

_RE_SCAN = re.compile(
    r"^- (?P<filename>\S+\.png)"
    r" type=(?P<type>bw|indexed|color)"
    r" tilt=(?P<tilt>-?\d+(\.\d+)?)degrees"
    r" content=(?P<content>machine|hand|images|mix)"
    r" border=(?P<border>yes|no)$"
)


@dataclasses.dataclass(frozen=True)
class ScanAttributes:
    filename: str
    type: str
    tilt: float
    content: str
    border: bool


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
            border=match["border"] == "yes",
        )
        attributes[a.filename] = a
    return attributes


@dataclasses.dataclass(frozen=True)
class BorderResult:
    attributes: ScanAttributes
    border_percent: float
    background_color: tuple[int, int, int]

    @property
    def border_measured(self) -> bool:
        return self.border_percent > BORDER_MIN_PERCENT

    @property
    def ok(self) -> bool:
        return self.border_measured == self.attributes.border

    @property
    def line(self) -> str:
        a = self.attributes
        return (
            f"| {a.filename} | {a.type} | {a.content}"
            f" | {'yes' if a.border else 'no'} | {self.border_percent:.1f}"
            f" | {'yes' if self.border_measured else 'no'}"
            f" | {'ok' if self.ok else 'FAIL'}"
            f" | {self.background_color} |"
        )


def scan_files_and_attributes() -> tuple[list[pathlib.Path], dict[str, ScanAttributes]]:
    scan_attributes = read_scan_attributes()
    scan_files = sorted(DIRECTORY_SCANS.glob("*.png"))
    assert sorted(scan_attributes) == [f.name for f in scan_files], (
        f"{FILENAME_README} must list exactly the scans in {DIRECTORY_SCANS}"
    )
    return scan_files, scan_attributes


def write_results(filename: pathlib.Path, title: str, lines: list[str]) -> None:
    filename.write_text(
        f"# {title}\n\n"
        "Written by tests/scan_postprocess/test_scan_postprocess.py.\n\n"
        + "\n".join(lines)
        + "\n"
    )


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
    preview.save(filename, compress_level=0)


def test_tilt() -> None:
    scan_files, scan_attributes = scan_files_and_attributes()

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
            write_preview(image, tilt, DIRECTORY_TILT_PREVIEW / f"{filename.stem}.png")
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

    write_results(
        FILENAME_TILT_RESULTS,
        "Tilt results (degrees)",
        header + [r.line for r in results] + [""] + [f"- {s}" for s in summary],
    )

    for r in results:
        assert -TILT_MAX_DEGREES <= r.tilt_measured <= TILT_MAX_DEGREES
    assert not failed, "Tilt differs from README.md: " + ", ".join(
        r.attributes.filename for r in failed
    )


def write_border_preview(
    image: Image.Image, mask: Image.Image, filename: pathlib.Path
) -> None:
    """Paint the removed border magenta."""
    preview = image.convert("RGB")
    preview.paste((255, 0, 255), mask=mask)
    scale = PREVIEW_WIDTH / preview.width
    preview = preview.resize(
        (PREVIEW_WIDTH, round(preview.height * scale)),
        resample=Image.Resampling.BOX,
    )
    preview.save(filename, compress_level=0)


def test_border() -> None:
    scan_files, scan_attributes = scan_files_and_attributes()

    DIRECTORY_BORDER_PREVIEW.mkdir(parents=True, exist_ok=True)
    header = [
        "| file | type | content | README.md | removed % | measured | result"
        " | background color |",
        "|---|---|---|---|---:|---|---|---|",
    ]
    print()
    print("\n".join(header))

    results: list[BorderResult] = []
    start = time.monotonic()
    for filename in scan_files:
        with Image.open(filename) as image:
            border = remove_border(image)
            assert border.image.size == image.size, "The image size must not change"
            write_border_preview(
                image, border.mask, DIRECTORY_BORDER_PREVIEW / f"{filename.stem}.png"
            )
        result = BorderResult(
            attributes=scan_attributes[filename.name],
            border_percent=100.0 * border.border_fraction,
            background_color=border.background_color,
        )
        results.append(result)
        print(result.line)
    duration_s = time.monotonic() - start

    failed = [r for r in results if not r.ok]
    summary = [
        f"Border if more than: {BORDER_MIN_PERCENT:.1f}% removed",
        f"Failed: {len(failed)} of {len(results)}",
    ]
    print()
    print("\n".join(summary))
    # Not written to the results file: it would change on every run.
    print(f"Duration: {duration_s:.1f}s")
    print(f"Results: {FILENAME_BORDER_RESULTS}")
    print(f"Previews: {DIRECTORY_BORDER_PREVIEW}")

    write_results(
        FILENAME_BORDER_RESULTS,
        "Border results",
        header + [r.line for r in results] + [""] + [f"- {s}" for s in summary],
    )

    assert not failed, "Border differs from README.md: " + ", ".join(
        r.attributes.filename for r in failed
    )


def test_tilt_border() -> None:
    """Remove the border, then deskew. Compare with the tilt of the raw scan."""
    scan_files, scan_attributes = scan_files_and_attributes()

    DIRECTORY_TILT_BORDER_PREVIEW.mkdir(parents=True, exist_ok=True)
    header = [
        "| file | README.md | tilt raw | tilt after border | change | border % |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    print()
    print("\n".join(header))

    lines: list[str] = []
    start = time.monotonic()
    for filename in scan_files:
        with Image.open(filename) as image:
            tilt_raw = estimate_tilt(image)
            result = postprocess(image)
            assert result.image.size == image.size, "The image size must not change"
        scale = PREVIEW_WIDTH / result.image.width
        result.image.resize(
            (PREVIEW_WIDTH, round(result.image.height * scale)),
            resample=Image.Resampling.BOX,
        ).save(DIRECTORY_TILT_BORDER_PREVIEW / f"{filename.stem}.png", compress_level=0)
        a = scan_attributes[filename.name]
        line = (
            f"| {a.filename} | {a.tilt:+.2f} | {tilt_raw:+.2f}"
            f" | {result.tilt:+.2f} | {result.tilt - tilt_raw:+.2f}"
            f" | {100.0 * result.border_fraction:.1f} |"
        )
        lines.append(line)
        print(line)
    duration_s = time.monotonic() - start

    print()
    # Not written to the results file: it would change on every run.
    print(f"Duration: {duration_s:.1f}s")
    print(f"Results: {FILENAME_TILT_BORDER_RESULTS}")
    print(f"Previews: {DIRECTORY_TILT_BORDER_PREVIEW}")

    write_results(
        FILENAME_TILT_BORDER_RESULTS,
        "Tilt (degrees) on the raw scan versus after border removal",
        header + lines,
    )


def size_totals(sizes: list[tuple[str, int, int]], name: str) -> list[str]:
    """Summary lines from (type, size raw, size converted): total and per type."""
    lines: list[str] = []
    for label, selected in [("Total", sizes)] + [
        (f"Type {t}", [x for x in sizes if x[0] == t])
        for t in ("bw", "indexed", "color")
    ]:
        raw = sum(x[1] for x in selected)
        converted = sum(x[2] for x in selected)
        if converted:
            lines.append(
                f"{label}: raw {raw // 1024} kB, {name} {converted // 1024} kB,"
                f" ratio {raw / converted:.1f}"
            )
    return lines


def test_bw() -> None:
    """Postprocess every scan and convert it to compressed grayscale."""
    scan_files, scan_attributes = scan_files_and_attributes()

    DIRECTORY_BW_PREVIEW.mkdir(parents=True, exist_ok=True)
    header = [
        "| file | type | content | level foreground color | level background color"
        " | raw kB | bw kB | ratio |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    print()
    print("\n".join(header))

    lines: list[str] = []
    sizes: list[tuple[str, int, int]] = []
    start = time.monotonic()
    for filename in scan_files:
        with Image.open(filename) as image:
            postprocessed = postprocess(image)
        bw = convert_bw(postprocessed.image)
        assert bw.image.size == postprocessed.image.size
        assert bw.image.mode == "P"
        assert len(bw.image.getcolors() or []) <= GRAY_LEVELS
        filename_bw = DIRECTORY_BW_PREVIEW / f"{filename.stem}{FILENAME_POSTFIX_BW}.png"
        save_png_compressed(bw.image, filename_bw)

        size_raw = filename.stat().st_size
        size_bw = filename_bw.stat().st_size
        a = scan_attributes[filename.name]
        sizes.append((a.type, size_raw, size_bw))
        line = (
            f"| {a.filename} | {a.type} | {a.content}"
            f" | {bw.level_foreground_color} | {bw.level_background_color}"
            f" | {size_raw // 1024} | {size_bw // 1024}"
            f" | {size_raw / size_bw:.1f} |"
        )
        lines.append(line)
        print(line)
    duration_s = time.monotonic() - start

    summary = [
        f"Background color: {100 * BACKGROUND_COLOR_FRACTION:.0f}% of the pixels,"
        f" foreground color: {100 * FOREGROUND_COLOR_FRACTION:.0f}% of the pixels,"
        f" {GRAY_LEVELS} gray levels",
        *size_totals(sizes, "bw"),
    ]
    print()
    print("\n".join(summary))
    # Not written to the results file: it would change on every run.
    print(f"Duration: {duration_s:.1f}s")
    print(f"Results: {FILENAME_BW_RESULTS}")
    print(f"Previews: {DIRECTORY_BW_PREVIEW}")

    write_results(
        FILENAME_BW_RESULTS,
        "Scans converted to grayscale (bw)",
        header + lines + [""] + [f"- {s}" for s in summary],
    )


def test_indexed() -> None:
    """Postprocess every scan and reduce it to a compressed palette."""
    scan_files, scan_attributes = scan_files_and_attributes()

    DIRECTORY_INDEXED_PREVIEW.mkdir(parents=True, exist_ok=True)
    header = [
        "| file | type | content | level foreground color | level background color"
        " | colors | raw kB | indexed kB | ratio |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    print()
    print("\n".join(header))

    lines: list[str] = []
    sizes: list[tuple[str, int, int]] = []
    start = time.monotonic()
    for filename in scan_files:
        with Image.open(filename) as image:
            postprocessed = postprocess(image)
        indexed = convert_indexed(postprocessed.image)
        assert indexed.image.size == postprocessed.image.size
        assert indexed.image.mode == "P"
        colors = indexed.colors
        assert colors == len(indexed.image.getcolors() or [])
        assert colors <= PALETTE_COLORS
        filename_indexed = (
            DIRECTORY_INDEXED_PREVIEW / f"{filename.stem}{FILENAME_POSTFIX_INDEXED}.png"
        )
        save_png_compressed(indexed.image, filename_indexed, colors=colors)

        size_raw = filename.stat().st_size
        size_indexed = filename_indexed.stat().st_size
        a = scan_attributes[filename.name]
        sizes.append((a.type, size_raw, size_indexed))
        line = (
            f"| {a.filename} | {a.type} | {a.content}"
            f" | {indexed.level_foreground_color} | {indexed.level_background_color}"
            f" | {colors}"
            f" | {size_raw // 1024} | {size_indexed // 1024}"
            f" | {size_raw / size_indexed:.1f} |"
        )
        lines.append(line)
        print(line)
    duration_s = time.monotonic() - start

    summary = [
        f"Background color: {100 * BACKGROUND_COLOR_FRACTION:.0f}% of the pixels,"
        f" foreground color: {100 * FOREGROUND_COLOR_FRACTION:.0f}% of the pixels,"
        f" blur radius {BLUR_RADIUS},"
        f" {PALETTE_COLORS} colors merged at distance {MERGE_DISTANCE}",
        *size_totals(sizes, "indexed"),
    ]
    print()
    print("\n".join(summary))
    # Not written to the results file: it would change on every run.
    print(f"Duration: {duration_s:.1f}s")
    print(f"Results: {FILENAME_INDEXED_RESULTS}")
    print(f"Previews: {DIRECTORY_INDEXED_PREVIEW}")

    write_results(
        FILENAME_INDEXED_RESULTS,
        "Scans reduced to a color palette (indexed)",
        header + lines + [""] + [f"- {s}" for s in summary],
    )
