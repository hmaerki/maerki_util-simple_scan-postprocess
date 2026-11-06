from __future__ import annotations

import dataclasses
import pathlib
import re

import pytest

from scan_postprocess.tilt import TILT_MAX_DEGREES, estimate_tilt_file

DIRECTORY_SCANS = pathlib.Path(__file__).parent / "scans_0_raw"
FILENAME_README = DIRECTORY_SCANS / "README.md"

TILT_TOLERANCE_DEGREES = 0.5

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


SCAN_ATTRIBUTES = read_scan_attributes()
SCAN_FILES = sorted(DIRECTORY_SCANS.glob("*.png"))


def test_readme_lists_all_scans() -> None:
    assert sorted(SCAN_ATTRIBUTES) == [f.name for f in SCAN_FILES]


@pytest.mark.parametrize("filename", SCAN_FILES, ids=lambda f: f.name)
def test_tilt(filename: pathlib.Path) -> None:
    # Measured from the pixels of the PNG (Pillow + numpy).
    tilt = estimate_tilt_file(filename)
    # Expected value as documented in README.md.
    expected = SCAN_ATTRIBUTES[filename.name]
    print(
        f"\n{filename.name}:"
        f" measured_from_png={tilt:+.2f}degrees"
        f" README.md={expected.tilt:+.2f}degrees"
        f" diff={tilt - expected.tilt:+.2f}degrees"
    )
    assert -TILT_MAX_DEGREES <= tilt <= TILT_MAX_DEGREES
    assert tilt == pytest.approx(expected.tilt, abs=TILT_TOLERANCE_DEGREES)
