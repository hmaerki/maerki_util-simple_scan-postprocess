"""Remove the scanner border around a scanned page.

The border is everything outside the paper: the scanner lid (neutral gray)
and dark lines along the image edges. It is painted white, the image size
does not change.
"""

from __future__ import annotations

import dataclasses
import pathlib

import numpy as np
from PIL import Image

_WORKING_WIDTH = 620
"""The mask is computed on a downscaled image (speed)."""

FILL_COLOR = (255, 255, 255)

_EDGE_BAND = 0.03
"""Width of the band along the image edge where the lid color is sampled."""

_DARK_LINE_BAND = 0.01
"""Dark pixels within this band (fraction of width) along the edge are border."""

_DARK_THRESHOLD = 90
_NEUTRAL_CHROMA = 25
"""max(R,G,B) - min(R,G,B) below this: neutral gray."""

_LID_TOLERANCE = 30
"""Pixels within this distance to the lid gray belong to the lid."""

_PAGE_LID_MIN_DISTANCE = 40
"""The lid is only detected if the page color differs at least this much."""

_GROW_PIXELS = 1
"""Grow the mask (working resolution) to also remove the shadow at the paper edge."""


@dataclasses.dataclass(frozen=True)
class BorderResult:
    image: Image.Image
    mask: Image.Image
    """'L' image, full size: 255 where the border was removed."""

    @property
    def border_fraction(self) -> float:
        return float(np.count_nonzero(np.asarray(self.mask))) / (
            self.mask.width * self.mask.height
        )


def _reconstruct(seed: np.ndarray, allowed: np.ndarray) -> np.ndarray:
    """Grow 'seed' within 'allowed' (4-connectivity) until it stops changing."""
    region = seed & allowed
    while True:
        grown = region.copy()
        grown[1:, :] |= region[:-1, :]
        grown[:-1, :] |= region[1:, :]
        grown[:, 1:] |= region[:, :-1]
        grown[:, :-1] |= region[:, 1:]
        grown &= allowed
        if np.array_equal(grown, region):
            return region
        region = grown


def _dominant_color(rgb: np.ndarray) -> np.ndarray:
    """Return the most frequent color (quantized to 16 levels per channel)."""
    quantized = (rgb // 16).reshape(-1, 3)
    keys = quantized[:, 0] * 256 + quantized[:, 1] * 16 + quantized[:, 2]
    key = int(np.argmax(np.bincount(keys)))
    return np.array([key // 256, (key // 16) % 16, key % 16]) * 16 + 8


def _grow(mask: np.ndarray, pixels: int) -> np.ndarray:
    for _ in range(pixels):
        grown = mask.copy()
        grown[1:, :] |= mask[:-1, :]
        grown[:-1, :] |= mask[1:, :]
        grown[:, 1:] |= mask[:, :-1]
        grown[:, :-1] |= mask[:, 1:]
        mask = grown
    return mask


def border_mask(image: Image.Image) -> Image.Image:
    """Return a full size 'L' mask: 255 for border pixels."""
    scale = _WORKING_WIDTH / image.width
    small = image.convert("RGB").resize(
        (_WORKING_WIDTH, round(image.height * scale)),
        resample=Image.Resampling.BOX,
    )
    rgb = np.asarray(small, dtype=np.int16)
    h, w, _ = rgb.shape
    gray = rgb.mean(axis=2)
    chroma = rgb.max(axis=2) - rgb.min(axis=2)

    edge = np.zeros((h, w), dtype=bool)
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True

    # Dark lines along the edges (shadow of the paper edge, lid frame).
    band = max(1, round(_DARK_LINE_BAND * w))
    near_edge = np.zeros((h, w), dtype=bool)
    near_edge[:band, :] = near_edge[-band:, :] = True
    near_edge[:, :band] = near_edge[:, -band:] = True
    dark = (gray < _DARK_THRESHOLD) & near_edge
    border = _reconstruct(edge, dark)

    # Scanner lid: neutral gray, connected to the edge.
    lid_band = max(2, round(_EDGE_BAND * w))
    outer = np.zeros((h, w), dtype=bool)
    outer[:lid_band, :] = outer[-lid_band:, :] = True
    outer[:, :lid_band] = outer[:, -lid_band:] = True
    neutral = chroma < _NEUTRAL_CHROMA
    candidates = outer & neutral & ~dark
    if np.any(candidates):
        lid_rgb = np.median(rgb[candidates], axis=0)
        # The lid is only distinguishable if the paper has another color.
        # White paper on a white lid: nothing to remove.
        page_rgb = _dominant_color(rgb)
        if np.abs(page_rgb - lid_rgb).max() >= _PAGE_LID_MIN_DISTANCE:
            # The lid is not evenly lit: use the range of the sampled grays.
            low, high = np.percentile(gray[candidates], [2, 98])
            lid = (
                neutral & (gray > low - _LID_TOLERANCE) & (gray < high + _LID_TOLERANCE)
            )
            border |= _reconstruct(edge | border, lid | border)

    border = _grow(border, _GROW_PIXELS) if np.any(border) else border
    mask_small = Image.fromarray((border * 255).astype(np.uint8), mode="L")
    return mask_small.resize(image.size, resample=Image.Resampling.NEAREST)


def remove_border(image: Image.Image) -> BorderResult:
    """Paint the border white. The returned image has the same size."""
    mask = border_mask(image)
    result = image.convert("RGB")
    result.paste(FILL_COLOR, mask=mask)
    assert result.size == image.size
    return BorderResult(image=result, mask=mask)


def remove_border_file(filename: pathlib.Path) -> BorderResult:
    with Image.open(filename) as image:
        return remove_border(image)
