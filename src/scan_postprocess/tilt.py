"""Estimate the tilt (skew) of a scanned page."""

from __future__ import annotations

import pathlib

import numpy as np
from PIL import Image

TILT_MAX_DEGREES = 5.0
"""Tilts are searched in the range -TILT_MAX_DEGREES .. +TILT_MAX_DEGREES."""

_WORKING_WIDTH = 800
"""The scan is downscaled to this width before analysis (speed)."""


def _ink_mask(image: Image.Image) -> Image.Image:
    """Return a 'L' image: 255 where there is ink, 0 for the background.

    The background is the most frequent gray level. Everything clearly darker
    or lighter is ink, so white text on a colored book cover is found too.
    """
    gray = np.asarray(image.convert("L"), dtype=np.int16)
    histogram = np.bincount(gray.ravel(), minlength=256)
    background = int(np.argmax(histogram))
    ink = np.abs(gray - background) > 60
    return Image.fromarray((ink * 255).astype(np.uint8), mode="L")


def _score(mask: Image.Image, angle_degrees: float) -> float:
    """Sharpness of the row profile after rotating by 'angle_degrees'.

    Text lines and ruled lines become sharp peaks when they are horizontal.
    """
    rotated = mask.rotate(angle_degrees, resample=Image.Resampling.BILINEAR)
    rows = np.asarray(rotated, dtype=np.float64).sum(axis=1)
    return float(np.sum(np.diff(rows) ** 2))


def estimate_tilt(image: Image.Image) -> float:
    """Return the tilt of the page in degrees.

    Positive: the content is rotated counter-clockwise (lines rise to the right).
    To deskew: 'image.rotate(-tilt)'.
    """
    scale = _WORKING_WIDTH / image.width
    small = image.resize(
        (_WORKING_WIDTH, round(image.height * scale)),
        resample=Image.Resampling.BOX,
    )
    mask = _ink_mask(small)

    def best(angles: np.ndarray) -> float:
        scores = [_score(mask, float(a)) for a in angles]
        return float(angles[int(np.argmax(scores))])

    # 'rotate(a)' rotates counter-clockwise: the best 'a' undoes the tilt.
    coarse = best(np.arange(-TILT_MAX_DEGREES, TILT_MAX_DEGREES + 0.01, 0.5))
    fine = best(np.arange(coarse - 0.5, coarse + 0.51, 0.05))
    return round(-fine, 2)


def estimate_tilt_file(filename: pathlib.Path) -> float:
    with Image.open(filename) as image:
        return estimate_tilt(image)
