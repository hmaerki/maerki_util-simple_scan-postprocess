"""Postprocess a scanned page: the full chain from the raw scan to the file.

PostprocessFile.postprocess_file() runs every step in this order:
1. Read the raw scan.
2. postprocess(): geometry.
   a. Remove the border (scanner lid, dark edge lines), paint it with the
      background color (scan_postprocess.border).
   b. Estimate the tilt on the border-free image: the straight, axis aligned
      border edges would otherwise pull the estimate towards 0 degrees
      (scan_postprocess.tilt).
   c. Rotate by -tilt. The corners uncovered by the rotation are filled with
      the background color, like the removed border. The image size does not
      change.
3. Reduce the colors, both conversions (scan_postprocess.convert):
   - "bw": 16 gray levels.
   - "indexed": smooth, up to 32 colors, merge similar colors.
4. PostprocessFile.save(): both as compressed palette PNG, named
   <stem><postfix>.png, for example scan-01-bw_bw16.png and
   scan-01-bw_indexed32.png.
"""

from __future__ import annotations

import dataclasses
import pathlib

from PIL import Image

from scan_postprocess.border import remove_border
from scan_postprocess.convert import Conversion, ConvertResult, PARAMS
from scan_postprocess.tilt import estimate_tilt


@dataclasses.dataclass(frozen=True)
class PostprocessResult:
    image: Image.Image
    tilt: float
    """Tilt in degrees, measured after border removal."""
    border_fraction: float


def postprocess(image: Image.Image) -> PostprocessResult:
    """Step 2: remove the border, then deskew."""
    border = remove_border(image)
    tilt = estimate_tilt(border.image)
    deskewed = border.image.rotate(
        -tilt,
        resample=Image.Resampling.BICUBIC,
        fillcolor=border.background_color,
    )
    assert deskewed.size == image.size
    return PostprocessResult(
        image=deskewed,
        tilt=tilt,
        border_fraction=border.border_fraction,
    )


class PostprocessFile:
    """The full chain for one scan file: read, postprocess, convert, save.

    Every scan is converted both to 'bw' and to 'indexed'.

    Usage:
        scan = PostprocessFile(filename, directory_out)
        scan.postprocess_file()
        scan.converted_bw.image, scan.filename_out("bw")
    """

    def __init__(self, filename: pathlib.Path, directory_out: pathlib.Path) -> None:
        self.filename = filename
        self.directory_out = directory_out
        self.postprocessed: PostprocessResult | None = None
        """Result of step 2: border removed and deskewed."""
        self.converted_bw: ConvertResult | None = None
        """Result of step 3, 'bw': 16 gray levels."""
        self.converted_indexed: ConvertResult | None = None
        """Result of step 3, 'indexed': up to 32 colors."""

    def filename_out(self, conversion: Conversion) -> pathlib.Path:
        """scans/scan-01-bw.png -> <directory_out>/scan-01-bw_bw16.png"""
        postfix = PARAMS[conversion].filename_postfix
        return self.directory_out / f"{self.filename.stem}{postfix}.png"

    def postprocess_file(self) -> None:
        """The full chain: read, postprocess, convert, save."""
        with Image.open(self.filename) as image:
            self.postprocessed = postprocess(image)
        self.converted_bw = ConvertResult(self.postprocessed.image, PARAMS["bw"])
        self.converted_indexed = ConvertResult(
            self.postprocessed.image, PARAMS["indexed"]
        )
        self.save()

    def save(self) -> None:
        """Step 4: save both conversions as compressed palette PNG."""
        assert self.converted_bw is not None, "Call postprocess_file() first"
        assert self.converted_indexed is not None, "Call postprocess_file() first"
        self.directory_out.mkdir(parents=True, exist_ok=True)
        for converted in (self.converted_bw, self.converted_indexed):
            converted.save(self.filename_out(converted.params.label))
