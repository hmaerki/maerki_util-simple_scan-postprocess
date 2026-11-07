"""Convert a scan with a few flat colors into a contrast stretched palette image.

Only for scans of type 'indexed' (blue pen, colored logos, colored book
covers). Processed like 'bw' (see scan_postprocess.bw), with these steps:
1. Smooth with a gaussian filter (BLUR_RADIUS): removes the scanner noise,
   which would otherwise be spread over many palette colors and spoil the
   compression.
2. Measure the foreground and background color levels on the grayscale image
   and stretch every RGB channel with these levels: the paper becomes white,
   the hues are kept.
   Exception: colored pages (book covers) have no white paper. The measured
   levels are then close together (less than MIN_STRETCH_RANGE) and the image
   is not stretched: level_foreground_color=0, level_background_color=255.
3. Reduce to an adaptive palette of PALETTE_COLORS colors, without dithering
   (dithering would spoil the compression).
4. Merge near-identical palette colors (closer than MERGE_DISTANCE): a flat
   background is often split into several shades. The final number of colors
   is typically 4 .. 21.
"""

from __future__ import annotations

import dataclasses

import numpy as np
from PIL import Image, ImageFilter

from scan_postprocess.bw import stretch_levels, stretch_lut

BLUR_RADIUS = 1.0
"""Gaussian filter radius in pixels (300 dpi)."""
PALETTE_COLORS = 32
"""Number of colors before merging."""
MERGE_DISTANCE = 24.0
"""Palette colors closer than this (RGB euclidean) are merged."""
MIN_STRETCH_RANGE = 64
"""Smaller level_background_color - level_foreground_color: no white paper, do
not stretch."""
FILENAME_POSTFIX = f"_color{PALETTE_COLORS}"
"""Appended to the stem of the output filename: scan.png -> scan_color32.png."""


@dataclasses.dataclass(frozen=True)
class IndexedResult:
    image: Image.Image
    """Palette image ('P') with 'colors' colors, at most PALETTE_COLORS."""
    colors: int
    """Number of colors after merging."""
    level_foreground_color: int
    """Gray level of the raw image mapped to 0."""
    level_background_color: int
    """Gray level of the raw image mapped to 255."""


def merge_palette(image_p: Image.Image, distance: float) -> Image.Image:
    """Merge palette colors closer than 'distance' (RGB euclidean).

    Greedy: the most frequent colors first. Every color joins the first more
    frequent color within 'distance'. The returned palette is compact: it
    contains only the remaining colors, the most frequent first.
    """
    indices = np.asarray(image_p)
    palette_flat = image_p.getpalette() or []
    palette = np.array(palette_flat, dtype=np.float64).reshape(-1, 3)
    counts = np.bincount(indices.ravel(), minlength=len(palette))
    used = [int(i) for i in np.argsort(-counts, kind="stable") if counts[i] > 0]

    representatives: list[int] = []
    mapping = np.zeros(256, dtype=np.uint8)
    for i in used:
        for k, r in enumerate(representatives):
            if np.linalg.norm(palette[i] - palette[r]) < distance:
                mapping[i] = k
                break
        else:
            mapping[i] = len(representatives)
            representatives.append(i)

    merged = Image.fromarray(mapping[indices], mode="P")
    merged.putpalette(
        palette[representatives].round().astype(np.uint8).ravel().tolist()
    )
    return merged


def convert_indexed(image: Image.Image) -> IndexedResult:
    rgb = image.convert("RGB")
    smoothed = rgb.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))

    level_foreground_color, level_background_color = stretch_levels(
        smoothed.convert("L")
    )
    if level_background_color - level_foreground_color < MIN_STRETCH_RANGE:
        level_foreground_color, level_background_color = 0, 255
    lut = stretch_lut(level_foreground_color, level_background_color)
    stretched = smoothed.point(lut * 3)

    quantized = stretched.quantize(
        colors=PALETTE_COLORS,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    merged = merge_palette(quantized, MERGE_DISTANCE)
    return IndexedResult(
        image=merged,
        colors=len(merged.getcolors() or []),
        level_foreground_color=level_foreground_color,
        level_background_color=level_background_color,
    )
