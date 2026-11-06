"""Convert a black/white scan into a contrast stretched grayscale image.

Only for scans of type 'bw' (black or gray ink on white paper). Assumption:
- WHITE_FRACTION of the pixels are paper: they become pure white.
- BLACK_FRACTION of the pixels are ink: they become pure black.
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

WHITE_FRACTION = 0.90
BLACK_FRACTION = 0.01
GRAY_LEVELS = 16
"""2, 4, 16 or 256: PNG supports 1, 2, 4 or 8 bits per pixel."""


@dataclasses.dataclass(frozen=True)
class BwResult:
    image: Image.Image
    """Palette image ('P') with GRAY_LEVELS gray levels from black to white."""
    level_black: int
    """Gray level of the raw image mapped to 0."""
    level_white: int
    """Gray level of the raw image mapped to 255."""


def convert_bw(image: Image.Image) -> BwResult:
    gray = image.convert("L")
    pixels = np.asarray(gray)
    level_black = int(np.percentile(pixels, 100.0 * BLACK_FRACTION))
    level_white = int(np.percentile(pixels, 100.0 * (1.0 - WHITE_FRACTION)))
    level_white = max(level_white, level_black + 1)

    # One lookup table: raw gray level -> stretched -> palette index.
    raw = np.arange(256, dtype=np.float64)
    stretched = np.clip((raw - level_black) / (level_white - level_black), 0.0, 1.0)
    lut = np.round(stretched * (GRAY_LEVELS - 1)).astype(np.uint8)
    indices = gray.point(lut.tolist())

    image_p = Image.frombytes("P", indices.size, indices.tobytes())
    palette: list[int] = []
    for i in range(GRAY_LEVELS):
        value = round(i * 255 / (GRAY_LEVELS - 1))
        palette += [value, value, value]
    image_p.putpalette(palette)

    return BwResult(
        image=image_p,
        level_black=level_black,
        level_white=level_white,
    )


def save_png_compressed(image: Image.Image, filename: pathlib.Path) -> None:
    bits = max(1, math.ceil(math.log2(GRAY_LEVELS)))
    image.save(filename, optimize=True, compress_level=9, bits=bits)
