"""Convert a black/white scan into a contrast stretched grayscale image.

Only for scans of type 'bw' (black or gray ink on white paper). Assumption:
- BACKGROUND_COLOR_FRACTION of the pixels are background (paper): they become
  pure white.
- FOREGROUND_COLOR_FRACTION of the pixels are foreground (ink): they become
  pure black.
The gray levels in between are stretched linearly and reduced to GRAY_LEVELS
levels. The result is a palette image: saved as PNG with log2(GRAY_LEVELS)
bits per pixel.
"""

from __future__ import annotations

import dataclasses
import math
import pathlib

import numpy as np
from PIL import Image

BACKGROUND_COLOR_FRACTION = 0.90
FOREGROUND_COLOR_FRACTION = 0.01
GRAY_LEVELS = 16
"""2, 4, 16 or 256: PNG supports 1, 2, 4 or 8 bits per pixel."""
FILENAME_POSTFIX = f"_bw{GRAY_LEVELS}"
"""Appended to the stem of the output filename: scan.png -> scan_bw16.png."""


@dataclasses.dataclass(frozen=True)
class BwResult:
    image: Image.Image
    """Palette image ('P') with GRAY_LEVELS gray levels from black to white."""
    level_foreground_color: int
    """Gray level of the raw image mapped to 0."""
    level_background_color: int
    """Gray level of the raw image mapped to 255."""
    colors: int = GRAY_LEVELS
    """Palette size: GRAY_LEVELS (some levels may be unused)."""


def stretch_levels(gray: Image.Image) -> tuple[int, int]:
    """Return (level_foreground_color, level_background_color) of a grayscale ('L') image."""
    pixels = np.asarray(gray)
    level_foreground_color = int(
        np.percentile(pixels, 100.0 * FOREGROUND_COLOR_FRACTION)
    )
    level_background_color = int(
        np.percentile(pixels, 100.0 * (1.0 - BACKGROUND_COLOR_FRACTION))
    )
    level_background_color = max(level_background_color, level_foreground_color + 1)
    return level_foreground_color, level_background_color


def stretch_lut(
    level_foreground_color: int, level_background_color: int, steps: int = 256
) -> list[int]:
    """Lookup table: raw level -> stretched level in 0 .. steps-1."""
    raw = np.arange(256, dtype=np.float64)
    stretched = np.clip(
        (raw - level_foreground_color)
        / (level_background_color - level_foreground_color),
        0.0,
        1.0,
    )
    return np.round(stretched * (steps - 1)).astype(np.uint8).tolist()


def convert_bw(image: Image.Image) -> BwResult:
    gray = image.convert("L")
    level_foreground_color, level_background_color = stretch_levels(gray)

    # One lookup table: raw gray level -> stretched -> palette index.
    lut = stretch_lut(level_foreground_color, level_background_color, steps=GRAY_LEVELS)
    indices = gray.point(lut)

    image_p = Image.frombytes("P", indices.size, indices.tobytes())
    palette: list[int] = []
    for i in range(GRAY_LEVELS):
        value = round(i * 255 / (GRAY_LEVELS - 1))
        palette += [value, value, value]
    image_p.putpalette(palette)

    return BwResult(
        image=image_p,
        level_foreground_color=level_foreground_color,
        level_background_color=level_background_color,
    )


def save_png_compressed(
    image: Image.Image, filename: pathlib.Path, colors: int = GRAY_LEVELS
) -> None:
    """PNG supports 1, 2, 4 or 8 bits: more than 16 colors are stored with 8."""
    bits = max(1, math.ceil(math.log2(colors)))
    bits = next(b for b in (1, 2, 4, 8) if b >= bits)
    image.save(filename, optimize=True, compress_level=9, bits=bits)
