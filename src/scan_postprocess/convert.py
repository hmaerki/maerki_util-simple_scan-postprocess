"""Reduce the colors of a preprocessed scan to a small palette.

One processing for both conversions, controlled by ConvertParams. The steps
are numbered as in README_DESIGN.md: step 3 of the full chain.

The colors are reduced first; white and black are decided afterwards on the
palette, from the pixel count of each color group. (Not from brightness
percentiles: a light green background and white text have a similar
brightness, but are two clearly separate color groups.)

3a. Smooth with a gaussian filter (blur_radius, 0: off): removes the scanner
   noise, which would otherwise be spread over many palette colors and spoil
   the compression.
3b. Reduce to color groups: median cut to QUANTIZE_COLORS colors (fine enough
   that a small color, e.g. one orange word on a purple page, gets its own
   colors), then merge colors closer than merge_distance. Without dithering:
   dithering would spoil the compression.
3c. Clean the groups:
   - Edge mixes: the blur and the scanner optics create colors between two
     colors along every edge. A group with too few core pixels (see
     core_mask()) is such a mix and joins the nearest group.
   - At most palette_colors groups: the least frequent join the nearest group.
   - Every group gets the mean color of its core pixels, measured on the
     smoothed image: not the color of its most frequent member, which may be
     a mix.
3d. Stretch. Both conversions first decide whether the background is white:
   the background is the most frequent group; it is white if bright and
   unsaturated (WHITE_MIN_GRAY, WHITE_MAX_SATURATION). Slightly gray or
   tinted is still white. Colored backgrounds (red or green paper, book
   covers) are not white.

   'bw': the background always becomes white and the ink always black, also
   for light text on a dark or colored background. Rationale: printed on a
   black and white printer, the page should need a minimal amount of ink.
   - White background (step3d_stretch()): the ink is the darkest group with
     enough pixels, if dark enough (INK_MAX_GRAY). White point: the
     background gray. Black point: the ink gray.
   - Background not white (step3d_stretch_bw_dark()): the ink is the most
     frequent group differing at least INK_MIN_CONTRAST from the background,
     lighter or darker (light text on dark paper). Background -> white,
     ink -> black; the other groups become the darker the more they differ
     from the background.
   - Stroke width: the pixels of the background group and the pixels near
     the ink (INK_EDGE_DISTANCE) are split anew by their gray, at
     INK_THRESHOLD between ink and background: ink or background, no halo.

   'indexed': only if the background is white (step3d_stretch()); colored
   backgrounds keep their colors as they are.
   - White point: the background color, per channel: grayish or tinted white
     becomes pure white.
   - Black point: the gray of the ink (the darkest group with enough pixels,
     if dark enough), the same for all channels: blue ink stays blue.
   - Stroke width: as for 'bw'.

   Finally colors closer than merge_distance are merged again: shades of
   white after the stretch, core colors that came closer in 3c.

Differences between the conversions: 'bw' (grayscale=True) works on the gray
image, its merge_distance is measured in gray levels; 'indexed' works on RGB,
its merge_distance is the RGB euclidean distance. And step 3d, see above.
"""

from __future__ import annotations

import dataclasses
import math
import pathlib
from typing import Literal

import numpy as np
from PIL import Image, ImageFilter

QUANTIZE_COLORS = 256
"""Step 3b: median cut to this many colors before merging. Median cut splits by
pixel count: cutting directly to palette_colors, a background covering 90% of
the page takes most of the palette and small colored text gets none."""
CORE_DISTANCE = 1
"""Step 3c: a pixel is 'core' if the pixels CORE_DISTANCE left/right/up/down
belong to the same group: it lies inside a flat area or a stroke, not on an
edge. (2 is too strict: thin pen strokes would have no core.)"""
MIN_CORE_PAGE_FRACTION = 0.0002
"""Step 3c: a group with fewer core pixels than this fraction of the page is an
edge mix. Absolute, not relative to the group: a small real color may share
its group with many edge pixels."""
WHITE_MIN_GRAY = 160
"""Step 3d: the background is white only if its gray is at least this..."""
WHITE_MAX_SATURATION = 0.15
"""...and its saturation, (max - min) / max of R, G, B, at most this."""
INK_MAX_GRAY = 110
"""Step 3d: the darkest group is ink (becomes black) only if its gray is at
most this."""
INK_MIN_PAGE_FRACTION = 0.002
"""Step 3d: groups with fewer pixels are ignored when looking for the ink."""
INK_MIN_CONTRAST = 60
"""Step 3d, 'bw' on a background that is not white: a group is ink only if its
gray differs at least this from the background gray (lighter or darker)."""
INK_THRESHOLD = 0.65
"""Step 3d: the stroke width. The edge of a stroke is a ramp from the ink gray
to the background gray. A pixel becomes ink if its gray lies within
INK_THRESHOLD of the way from the ink to the background, otherwise background.
0.5: the middle. Larger: bolder strokes (0.8: the holes of small letters start
to close). Smaller: thinner strokes."""
INK_EDGE_DISTANCE = 2
"""Step 3d: INK_THRESHOLD applies to the pixels of the ink and the background
group and to every pixel at most this far from an ink pixel: the edges of the
strokes, whatever group step 3c gave them (light halos, colored fringes).
Pixels farther away (photos, colored areas) keep their colors."""

Conversion = Literal["bw", "indexed"]


@dataclasses.dataclass(frozen=True)
class ConvertParams:
    label: Conversion
    """Name of the conversion: 'bw' or 'indexed'."""
    grayscale: bool
    """True: gray image, gray palette. False: RGB."""
    palette_colors: int
    """Maximum number of colors after the conversion."""
    blur_radius: float
    """Gaussian filter radius in pixels (300 dpi). 0: no smoothing."""
    merge_distance: float
    """Colors closer than this are merged. grayscale: in gray levels.
    Otherwise: RGB euclidean distance."""

    @property
    def filename_postfix(self) -> str:
        """Appended to the stem of the output filename: scan.png -> scan_bw16.png."""
        return f"_{self.label}{self.palette_colors}"


PARAMS_BW = ConvertParams(
    label="bw",
    grayscale=True,
    palette_colors=16,
    blur_radius=0.3,
    merge_distance=24.0,
)
PARAMS_INDEXED = ConvertParams(
    label="indexed",
    grayscale=False,
    palette_colors=32,
    blur_radius=0.3,
    merge_distance=24.0,
)
PARAMS: dict[Conversion, ConvertParams] = {
    params.label: params for params in (PARAMS_BW, PARAMS_INDEXED)
}


class ConvertResult:
    """Convert a preprocessed scan: ConvertResult(image, params).

    The constructor runs the steps 3a to 3d (see the module docstring); the
    result is in the attributes. step4_save() writes it as compressed PNG.
    """

    def __init__(self, image: Image.Image, params: ConvertParams) -> None:
        self.params = params
        self.level_foreground_color = 0
        """Gray of the ink, mapped to black. 0: no ink found or not stretched."""
        self.level_background_color = 255
        """Gray of the background, mapped to white. 255: background not white,
        not stretched."""
        smoothed = self.step3a_smooth(image)
        image_p = self.step3b_reduce(smoothed)
        image_p = self.step3c_clean(smoothed, image_p)
        self.image = self.step3d_stretch(smoothed, image_p)
        """Palette image ('P'), compact palette."""
        self.colors = len(self.image.getcolors() or [])
        """Number of colors in the palette."""

    def step3a_smooth(self, image: Image.Image) -> Image.Image:
        """Step 3a: gray or RGB, gaussian filter."""
        image = image.convert("L" if self.params.grayscale else "RGB")
        if self.params.blur_radius > 0:
            image = image.filter(ImageFilter.GaussianBlur(self.params.blur_radius))
        return image

    def step3b_reduce(self, image: Image.Image) -> Image.Image:
        """Step 3b: median cut to QUANTIZE_COLORS, merge similar colors."""
        image_p = image.convert("RGB").quantize(
            colors=QUANTIZE_COLORS,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.NONE,
        )
        return self.merge_palette(image_p)

    def step3c_clean(self, image: Image.Image, image_p: Image.Image) -> Image.Image:
        """Step 3c: edge mixes and rare groups join the nearest group; every
        group gets the mean color of its core pixels in 'image'."""
        indices = np.asarray(image_p)
        palette = self.get_palette(image_p)
        n = len(palette)
        core_counts = np.bincount(indices[self.core_mask(indices)], minlength=n)
        # merge_palette() sorted by count: 0 is the most frequent, always kept.
        keep = [
            i
            for i in range(n)
            if i == 0 or core_counts[i] >= MIN_CORE_PAGE_FRACTION * indices.size
        ]
        keep = keep[: self.params.palette_colors]
        compare = self.compare_colors(palette)
        distances = np.linalg.norm(compare[:, None, :] - compare[None, keep, :], axis=2)
        mapped = np.argmin(distances, axis=1).astype(np.uint8)[indices]

        # Mean color of the core pixels, recomputed on the joined groups.
        core = self.core_mask(mapped)
        k = len(keep)
        core_counts = np.bincount(mapped[core], minlength=k)
        has_core = core_counts > 0
        new_palette = palette[keep].copy()
        rgb = np.asarray(image.convert("RGB"))
        for channel in range(3):
            sums = np.bincount(
                mapped[core], weights=rgb[..., channel][core], minlength=k
            )
            new_palette[has_core, channel] = sums[has_core] / core_counts[has_core]
        return self.make_image_p(mapped, new_palette)

    def step3d_stretch(self, image: Image.Image, image_p: Image.Image) -> Image.Image:
        """Step 3d: if the background is white: background -> pure white,
        ink -> black, the stroke width set by INK_THRESHOLD ('image': the
        smoothed image)."""
        indices = np.asarray(image_p)
        palette = self.get_palette(image_p)
        counts = np.bincount(indices.ravel(), minlength=len(palette))
        gray = palette @ np.array([0.299, 0.587, 0.114])
        background = palette[0]  # the most frequent, see step3c_clean()
        saturation = (background.max() - background.min()) / max(background.max(), 1)
        if gray[0] < WHITE_MIN_GRAY or saturation > WHITE_MAX_SATURATION:
            if self.params.grayscale:
                # 'bw': background -> white, ink -> black, always.
                return self.step3d_stretch_bw_dark(image, indices, palette, counts)
            # Not white: a colored background, keep the colors. Merge nevertheless:
            # the core colors of step 3c may have come closer together.
            return self.merge_palette(image_p)

        candidates = [
            i
            for i in range(1, len(palette))
            if counts[i] >= INK_MIN_PAGE_FRACTION * indices.size
        ]
        ink = min(candidates, key=lambda i: gray[i], default=None)
        if ink is not None and gray[ink] > INK_MAX_GRAY:
            ink = None
        black = 0.0 if ink is None else gray[ink]
        self.level_foreground_color = round(black)
        self.level_background_color = round(gray[0])

        if ink is not None:
            # Stroke width: split the pixels of the background, the ink and the
            # stroke edges by their gray on the smoothed image.
            limit = gray[ink] + INK_THRESHOLD * (gray[0] - gray[ink])
            pixels_gray = np.asarray(image.convert("L"))
            is_ink = indices == ink
            near_ink = np.asarray(
                Image.fromarray(is_ink.astype(np.uint8) * 255).filter(
                    ImageFilter.MaxFilter(2 * INK_EDGE_DISTANCE + 1)
                )
            ).astype(bool)
            split = (indices == 0) | near_ink
            indices = indices.copy()
            indices[split & (pixels_gray <= limit)] = ink
            indices[split & (pixels_gray > limit)] = 0

        span = np.maximum(background - black, 1.0)
        palette = np.clip((palette - black) / span * 255.0, 0.0, 255.0)
        # Several shades of white (or black) are now near-identical.
        return self.merge_palette(self.make_image_p(indices, palette))

    def step3d_stretch_bw_dark(
        self,
        image: Image.Image,
        indices: np.ndarray,
        palette: np.ndarray,
        counts: np.ndarray,
    ) -> Image.Image:
        """Step 3d, 'bw' only, the background is not white (gray, or a colored
        paper seen in gray), often with light text: the background becomes
        white and the ink black, whether the ink is darker or lighter.
        Rationale: printed on a black and white printer, the page should need
        a minimal amount of ink.

        Ink: the most frequent group differing at least INK_MIN_CONTRAST from
        the background. Every other group becomes the darker the more it
        differs from the background, in either direction:
        |gray - background| / |ink - background| -> white .. black.
        """
        gray = palette[:, 0]
        candidates = [
            i
            for i in range(1, len(palette))
            if counts[i] >= INK_MIN_PAGE_FRACTION * indices.size
            and abs(gray[i] - gray[0]) >= INK_MIN_CONTRAST
        ]
        ink = max(candidates, key=lambda i: counts[i], default=None)
        self.level_background_color = round(gray[0])
        if ink is None:
            # Only the background: white. Everything else keeps its contrast.
            contrast = 255.0
        else:
            contrast = abs(gray[ink] - gray[0])
            self.level_foreground_color = round(gray[ink])
            # Stroke width: as in step3d_stretch(), on the ink side of the limit.
            direction = 1.0 if gray[0] > gray[ink] else -1.0
            limit = gray[ink] + INK_THRESHOLD * (gray[0] - gray[ink])
            pixels_gray = np.asarray(image.convert("L")).astype(np.float64)
            is_ink = indices == ink
            near_ink = np.asarray(
                Image.fromarray(is_ink.astype(np.uint8) * 255).filter(
                    ImageFilter.MaxFilter(2 * INK_EDGE_DISTANCE + 1)
                )
            ).astype(bool)
            split = (indices == 0) | near_ink
            ink_side = (pixels_gray - limit) * direction <= 0
            indices = indices.copy()
            indices[split & ink_side] = ink
            indices[split & ~ink_side] = 0

        darkness = np.clip(np.abs(gray - gray[0]) / contrast, 0.0, 1.0)
        palette = np.repeat((255.0 * (1.0 - darkness))[:, None], 3, axis=1)
        return self.merge_palette(self.make_image_p(indices, palette))

    def step4_save(self, filename: pathlib.Path) -> None:
        """Step 4: save as compressed palette PNG.

        PNG supports 1, 2, 4 or 8 bits: more than 16 colors are stored with 8.
        """
        bits = max(1, math.ceil(math.log2(max(self.colors, 2))))
        bits = next(b for b in (1, 2, 4, 8) if b >= bits)
        self.image.save(filename, optimize=True, compress_level=9, bits=bits)

    def compare_colors(self, palette: np.ndarray) -> np.ndarray:
        """The coordinates for color distances: gray levels or RGB."""
        return palette[:, :1] if self.params.grayscale else palette

    def merge_palette(self, image_p: Image.Image) -> Image.Image:
        """Merge palette colors closer than merge_distance (0: no merging,
        but the palette is still made compact and sorted).

        Greedy: the most frequent colors first. Every color joins the first more
        frequent color within the distance. The returned palette is compact: it
        contains only the remaining colors, the most frequent first.
        """
        indices = np.asarray(image_p)
        palette = self.get_palette(image_p)
        compare = self.compare_colors(palette)
        counts = np.bincount(indices.ravel(), minlength=len(palette))
        used = [int(i) for i in np.argsort(-counts, kind="stable") if counts[i] > 0]

        representatives: list[int] = []
        mapping = np.zeros(256, dtype=np.uint8)
        for i in used:
            for k, r in enumerate(representatives):
                if np.linalg.norm(compare[i] - compare[r]) < self.params.merge_distance:
                    mapping[i] = k
                    break
            else:
                mapping[i] = len(representatives)
                representatives.append(i)
        return self.make_image_p(mapping[indices], palette[representatives])

    @staticmethod
    def core_mask(indices: np.ndarray) -> np.ndarray:
        """True where the pixels CORE_DISTANCE left/right/up/down have the same
        index. The pixels along the image border are never core."""
        d = CORE_DISTANCE
        core = np.zeros(indices.shape, dtype=bool)
        center = indices[d:-d, d:-d]
        core[d:-d, d:-d] = (
            (center == indices[: -2 * d, d:-d])
            & (center == indices[2 * d :, d:-d])
            & (center == indices[d:-d, : -2 * d])
            & (center == indices[d:-d, 2 * d :])
        )
        return core

    @staticmethod
    def get_palette(image_p: Image.Image) -> np.ndarray:
        """The used part of the palette: shape (colors, 3), float."""
        palette = np.array(image_p.getpalette() or [], dtype=np.float64).reshape(-1, 3)
        return palette[: int(np.asarray(image_p).max()) + 1]

    @staticmethod
    def make_image_p(indices: np.ndarray, palette: np.ndarray) -> Image.Image:
        image_p = Image.fromarray(indices.astype(np.uint8), mode="P")
        image_p.putpalette(palette.round().astype(np.uint8).ravel().tolist())
        return image_p
