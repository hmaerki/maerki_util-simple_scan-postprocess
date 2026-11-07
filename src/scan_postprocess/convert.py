"""Reduce the colors of a postprocessed scan to a small palette.

One processing for both conversions, controlled by ConvertParams:
1. Smooth with a gaussian filter (blur_radius, 0: off): removes the scanner
   noise, which would otherwise be spread over many palette colors and spoil
   the compression.
2. Measure the foreground and background color levels on the grayscale image:
   - BACKGROUND_COLOR_FRACTION of the pixels are background (paper): they
     become pure white.
   - FOREGROUND_COLOR_FRACTION of the pixels are foreground (ink): they become
     pure black.
   Exception: colored pages (book covers) have no white paper. The measured
   levels are then close together (less than min_stretch_range) and the image
   is not stretched: level_foreground_color=0, level_background_color=255.
3. Stretch linearly with these levels and reduce to palette_colors colors.
   The only logical difference between the conversions:
   - grayscale=True ('bw'): the gray image is stretched; the palette is fixed,
     palette_colors evenly spaced grays from black to white.
   - grayscale=False ('indexed'): every RGB channel is stretched, the hues are
     kept; the palette is adaptive (median cut), without dithering (dithering
     would spoil the compression).
4. Merge near-identical palette colors (closer than merge_distance, 0: off):
   a flat background is often split into several shades.
"""

from __future__ import annotations

import dataclasses
import math
import pathlib
from typing import Literal

import numpy as np
from PIL import Image, ImageFilter

BACKGROUND_COLOR_FRACTION = 0.90
FOREGROUND_COLOR_FRACTION = 0.01

Conversion = Literal["bw", "indexed"]


@dataclasses.dataclass(frozen=True)
class ConvertParams:
    label: Conversion
    """Name of the conversion: 'bw' or 'indexed'."""
    grayscale: bool
    """True: gray image, fixed gray palette. False: RGB, adaptive palette."""
    palette_colors: int
    """grayscale: 2, 4, 16 or 256 (PNG supports 1, 2, 4 or 8 bits per pixel).
    Otherwise the number of colors before merging."""
    blur_radius: float
    """Gaussian filter radius in pixels (300 dpi). 0: no smoothing."""
    merge_distance: float
    """Palette colors closer than this (RGB euclidean) are merged. 0: no merging."""
    min_stretch_range: int
    """Smaller level_background_color - level_foreground_color: no white paper,
    do not stretch. 0: always stretch."""

    @property
    def filename_postfix(self) -> str:
        """Appended to the stem of the output filename: scan.png -> scan_bw16.png."""
        return f"_{self.label}{self.palette_colors}"


PARAMS_BW = ConvertParams(
    label="bw",
    grayscale=True,
    palette_colors=16,
    blur_radius=0.0,
    merge_distance=0.0,
    min_stretch_range=64,
)
PARAMS_INDEXED = ConvertParams(
    label="indexed",
    grayscale=False,
    palette_colors=32,
    blur_radius=1.0,
    merge_distance=24.0,
    min_stretch_range=64,
)
PARAMS: dict[Conversion, ConvertParams] = {
    params.label: params for params in (PARAMS_BW, PARAMS_INDEXED)
}


class ConvertResult:
    """Convert a postprocessed scan: ConvertResult(image, params).

    The constructor runs the steps 1 to 4 (see the module docstring); the
    result is in the attributes. save() writes it as compressed PNG.
    """

    def __init__(self, image: Image.Image, params: ConvertParams) -> None:
        self.params = params
        smoothed = self._smooth(image)
        self.level_foreground_color, self.level_background_color = self._measure_levels(
            smoothed
        )
        """Gray level of the raw image mapped to 0 and to 255."""
        self.image, self.colors = self._merge(self._reduce(smoothed))
        """Palette image ('P'). Palette size: grayscale palette_colors (some
        levels may be unused), otherwise the number of colors after merging."""

    def _smooth(self, image: Image.Image) -> Image.Image:
        """Step 1: gray or RGB, gaussian filter."""
        image = image.convert("L" if self.params.grayscale else "RGB")
        if self.params.blur_radius > 0:
            image = image.filter(ImageFilter.GaussianBlur(self.params.blur_radius))
        return image

    def _measure_levels(self, image: Image.Image) -> tuple[int, int]:
        """Step 2: measure the levels, always on the gray image."""
        gray = image if self.params.grayscale else image.convert("L")
        level_foreground_color, level_background_color = self.stretch_levels(gray)
        if (
            level_background_color - level_foreground_color
            < self.params.min_stretch_range
        ):
            return 0, 255
        return level_foreground_color, level_background_color

    def _reduce(self, image: Image.Image) -> Image.Image:
        """Step 3: stretch and reduce to a palette."""
        if self.params.grayscale:
            # One lookup table: raw gray level -> stretched -> palette index.
            lut = self.stretch_lut(
                self.level_foreground_color,
                self.level_background_color,
                steps=self.params.palette_colors,
            )
            indices = image.point(lut)
            image_p = Image.frombytes("P", indices.size, indices.tobytes())
            image_p.putpalette(self.gray_palette(self.params.palette_colors))
            return image_p
        lut = self.stretch_lut(self.level_foreground_color, self.level_background_color)
        return image.point(lut * 3).quantize(
            colors=self.params.palette_colors,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.NONE,
        )

    def _merge(self, image_p: Image.Image) -> tuple[Image.Image, int]:
        """Step 4: merge near-identical colors. Returns (image, colors)."""
        if self.params.merge_distance > 0:
            image_p = self.merge_palette(image_p, self.params.merge_distance)
            return image_p, len(image_p.getcolors() or [])
        return image_p, self.params.palette_colors

    def save(self, filename: pathlib.Path) -> None:
        """Save as compressed palette PNG.

        PNG supports 1, 2, 4 or 8 bits: more than 16 colors are stored with 8.
        """
        bits = max(1, math.ceil(math.log2(self.colors)))
        bits = next(b for b in (1, 2, 4, 8) if b >= bits)
        self.image.save(filename, optimize=True, compress_level=9, bits=bits)

    @staticmethod
    def stretch_levels(gray: Image.Image) -> tuple[int, int]:
        """Return (level_foreground_color, level_background_color) of a
        grayscale ('L') image."""
        pixels = np.asarray(gray)
        level_foreground_color = int(
            np.percentile(pixels, 100.0 * FOREGROUND_COLOR_FRACTION)
        )
        level_background_color = int(
            np.percentile(pixels, 100.0 * (1.0 - BACKGROUND_COLOR_FRACTION))
        )
        level_background_color = max(level_background_color, level_foreground_color + 1)
        return level_foreground_color, level_background_color

    @staticmethod
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

    @staticmethod
    def gray_palette(colors: int) -> list[int]:
        """'colors' evenly spaced grays from black to white, flat RGB list."""
        palette: list[int] = []
        for i in range(colors):
            value = round(i * 255 / (colors - 1))
            palette += [value, value, value]
        return palette

    @staticmethod
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
