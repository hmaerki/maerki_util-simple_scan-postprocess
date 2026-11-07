"""Postprocess a scanned page: remove the border, then deskew.

Order:
1. Remove the border (scanner lid, dark edge lines).
2. Estimate the tilt on the border-free image: the straight, axis aligned
   border edges would otherwise pull the estimate towards 0 degrees.
3. Rotate by -tilt. The corners uncovered by the rotation are filled with the
   background color, like the removed border. The image size does not change.
"""

from __future__ import annotations

import dataclasses
import pathlib

from PIL import Image

from scan_postprocess.border import remove_border
from scan_postprocess.tilt import estimate_tilt


@dataclasses.dataclass(frozen=True)
class PostprocessResult:
    image: Image.Image
    tilt: float
    """Tilt in degrees, measured after border removal."""
    border_fraction: float


def postprocess(image: Image.Image) -> PostprocessResult:
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


def postprocess_file(filename: pathlib.Path) -> PostprocessResult:
    with Image.open(filename) as image:
        return postprocess(image)
