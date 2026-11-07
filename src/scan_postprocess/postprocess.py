"""Postprocess a scanned page: the full chain from the raw scan to the file.

postprocess_file() runs every step in this order:
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
4. save(): compressed palette PNG, named <stem><postfix>.png, for example
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


@dataclasses.dataclass(frozen=True)
class PostprocessFileResult:
    postprocessed: PostprocessResult
    """Result of step 2: border removed and deskewed."""
    converted: ConvertResult
    """Result of step 3: colors reduced."""
    filename_out: pathlib.Path
    """The file written in step 4."""


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


def filename_postfix(conversion: Conversion) -> str:
    if conversion == "bw":
        return bw.FILENAME_POSTFIX
    if conversion == "indexed":
        return indexed.FILENAME_POSTFIX
    raise ValueError(f"Unknown conversion: {conversion!r}")


def filename_output(
    filename: pathlib.Path, directory_out: pathlib.Path, conversion: Conversion
) -> pathlib.Path:
    """scans/scan-01-bw.png -> <directory_out>/scan-01-bw_bw16.png"""
    return directory_out / f"{filename.stem}{filename_postfix(conversion)}.png"


def save(converted: ConvertResult, filename_out: pathlib.Path) -> None:
    """Step 4: save as compressed palette PNG."""
    bw.save_png_compressed(converted.image, filename_out, colors=converted.colors)


def postprocess_file(
    filename: pathlib.Path, directory_out: pathlib.Path, conversion: Conversion
) -> PostprocessFileResult:
    """The full chain: read, postprocess, convert, save."""
    with Image.open(filename) as image:
        postprocessed = postprocess(image)
    converted = convert(postprocessed.image, conversion)
    directory_out.mkdir(parents=True, exist_ok=True)
    filename_out = filename_output(filename, directory_out, conversion)
    save(converted, filename_out)
    return PostprocessFileResult(
        postprocessed=postprocessed,
        converted=converted,
        filename_out=filename_out,
    )
