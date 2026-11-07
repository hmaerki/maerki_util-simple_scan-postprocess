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
3. convert(): reduce the colors, depending on 'conversion'.
   - "bw": 16 gray levels (scan_postprocess.bw).
   - "indexed": smooth, up to 32 colors, merge similar colors
     (scan_postprocess.indexed).
4. PostprocessFile.save(): compressed palette PNG, named <stem><postfix>.png, for example
   scan-01-bw_bw16.png.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import Literal

from PIL import Image

from scan_postprocess import bw, indexed
from scan_postprocess.border import remove_border
from scan_postprocess.tilt import estimate_tilt

Conversion = Literal["bw", "indexed"]

ConvertResult = bw.BwResult | indexed.IndexedResult


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


def convert(image: Image.Image, conversion: Conversion) -> ConvertResult:
    """Step 3: reduce the colors."""
    if conversion == "bw":
        return bw.convert_bw(image)
    if conversion == "indexed":
        return indexed.convert_indexed(image)
    raise ValueError(f"Unknown conversion: {conversion!r}")


class PostprocessFile:
    """The full chain for one scan file: read, postprocess, convert, save.

    Usage:
        scan = PostprocessFile(filename, directory_out, "bw")
        scan.postprocess_file()
        scan.converted.image, scan.filename_out
    """

    def __init__(
        self,
        filename: pathlib.Path,
        directory_out: pathlib.Path,
        conversion: Conversion,
    ) -> None:
        self.filename = filename
        self.directory_out = directory_out
        self.conversion = conversion
        self.postprocessed: PostprocessResult | None = None
        """Result of step 2: border removed and deskewed."""
        self.converted: ConvertResult | None = None
        """Result of step 3: colors reduced."""

    @property
    def filename_postfix(self) -> str:
        if self.conversion == "bw":
            return bw.FILENAME_POSTFIX
        if self.conversion == "indexed":
            return indexed.FILENAME_POSTFIX
        raise ValueError(f"Unknown conversion: {self.conversion!r}")

    @property
    def filename_out(self) -> pathlib.Path:
        """scans/scan-01-bw.png -> <directory_out>/scan-01-bw_bw16.png"""
        return self.directory_out / f"{self.filename.stem}{self.filename_postfix}.png"

    def postprocess_file(self) -> None:
        """The full chain: read, postprocess, convert, save."""
        with Image.open(self.filename) as image:
            self.postprocessed = postprocess(image)
        self.converted = convert(self.postprocessed.image, self.conversion)
        self.save()

    def save(self) -> None:
        """Step 4: save as compressed palette PNG."""
        assert self.converted is not None, "Call postprocess_file() first"
        self.directory_out.mkdir(parents=True, exist_ok=True)
        bw.save_png_compressed(
            self.converted.image, self.filename_out, colors=self.converted.colors
        )
