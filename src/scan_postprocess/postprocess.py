"""Postprocess a scanned page: the full chain from the raw scan to the file.

PostprocessFile.postprocess_file() runs every step in this order (see
README_DESIGN.md). Every function or method implementing a step is prefixed
with step<number>_.
1. step1_read(): read the raw scan.
2. step2_preprocess(): geometry.
   a. step2a_remove_border(): remove the border (scanner lid, dark edge
      lines), paint it with the background color (scan_postprocess.border).
   b. step2b_estimate_tilt(): estimate the tilt on the border-free image: the
      straight, axis aligned border edges would otherwise pull the estimate
      towards 0 degrees (scan_postprocess.tilt).
   c. step2c_deskew(): rotate by -tilt. The corners uncovered by the rotation
      are filled with the background color, like the removed border. The
      image size does not change.
3. step3_convert(): reduce the colors, both conversions
   (scan_postprocess.convert, steps 3a .. 3d):
   - "bw": 16 gray levels.
   - "indexed": smooth, up to 32 colors, merge similar colors.
4. step4_save(): both as compressed palette PNG, named <stem><postfix>.png,
   for example scan-01-bw_bw16.png and scan-01-bw_indexed32.png.
"""

from __future__ import annotations

import dataclasses
import pathlib

from PIL import Image

from scan_postprocess.border import step2a_remove_border
from scan_postprocess.convert import Conversion, ConvertResult, PARAMS
from scan_postprocess.tilt import step2b_estimate_tilt


@dataclasses.dataclass(frozen=True)
class PreprocessResult:
    image: Image.Image
    tilt: float
    """Tilt in degrees, measured after border removal."""
    border_fraction: float


def step2c_deskew(
    image: Image.Image, tilt: float, fillcolor: tuple[int, int, int]
) -> Image.Image:
    """Step 2c: rotate by -tilt, fill the uncovered corners with 'fillcolor'."""
    deskewed = image.rotate(
        -tilt,
        resample=Image.Resampling.BICUBIC,
        fillcolor=fillcolor,
    )
    assert deskewed.size == image.size
    return deskewed


def step2_preprocess(image: Image.Image) -> PreprocessResult:
    """Step 2: remove the border, then deskew."""
    border = step2a_remove_border(image)
    tilt = step2b_estimate_tilt(border.image)
    deskewed = step2c_deskew(border.image, tilt, border.background_color)
    return PreprocessResult(
        image=deskewed,
        tilt=tilt,
        border_fraction=border.border_fraction,
    )


class PostprocessFile:
    """The full chain for one scan file: read, preprocess, convert, save.

    Every scan is converted both to 'bw' and to 'indexed'.

    Usage:
        scan = PostprocessFile(filename, directory_out)
        scan.postprocess_file()
        scan.converted_bw.image, scan.filename_out("bw")
    """

    def __init__(self, filename: pathlib.Path, directory_out: pathlib.Path) -> None:
        self.filename = filename
        self.directory_out = directory_out
        self.preprocessed: PreprocessResult | None = None
        """Result of step 2: border removed and deskewed."""
        self.converted_bw: ConvertResult | None = None
        """Result of step 3, 'bw': 16 gray levels."""
        self.converted_indexed: ConvertResult | None = None
        """Result of step 3, 'indexed': up to 32 colors."""

    def filename_out(self, conversion: Conversion) -> pathlib.Path:
        """scans/scan-01-bw.png -> <directory_out>/scan-01-bw_bw16.png"""
        postfix = PARAMS[conversion].filename_postfix
        return self.directory_out / f"{self.filename.stem}{postfix}.png"

    def postprocess_file(self) -> None:
        """The full chain: read, preprocess, convert, save."""
        image = self.step1_read()
        self.preprocessed = step2_preprocess(image)
        self.step3_convert()
        self.step4_save()

    def step1_read(self) -> Image.Image:
        """Step 1: read the raw scan."""
        with Image.open(self.filename) as image:
            return image.copy()

    def step3_convert(self) -> None:
        """Step 3: convert to 'bw' and to 'indexed'."""
        assert self.preprocessed is not None, "Call step2_preprocess() first"
        self.converted_bw = ConvertResult(
            self.preprocessed.image,
            PARAMS["bw"],
        )
        self.converted_indexed = ConvertResult(
            self.preprocessed.image,
            PARAMS["indexed"],
        )

    def step4_save(self) -> None:
        """Step 4: save both conversions as compressed palette PNG."""
        assert self.converted_bw is not None, "Call step3_convert() first"
        assert self.converted_indexed is not None, "Call step3_convert() first"
        self.directory_out.mkdir(parents=True, exist_ok=True)
        for converted in (self.converted_bw, self.converted_indexed):
            converted.step4_save(self.filename_out(converted.params.label))
