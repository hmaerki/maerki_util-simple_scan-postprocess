# scan_postprocess: design

## Processing steps

`PostprocessFile.postprocess_file()` (`postprocess.py`) runs these steps in this order.
Every function or method implementing a step is prefixed with `step<number>_`.
The preview directories below `tests/scan_postprocess/scans_0_raw_results` carry the same prefix.

| # | step | function | input |
|---|---|---|---|
| 1 | read | `PostprocessFile.step1_read()` | raw scan |
| 2 | preprocess | `step2_preprocess()` (`postprocess.py`) | runs 2a .. 2c |
| 2a | **border** | `step2a_remove_border()` (`border.py`) | raw scan; the border is painted with the background color |
| 2b | **tilt** | `step2b_estimate_tilt()` (`tilt.py`) | image without the border |
| 2c | rotate (deskew) | `step2c_deskew()` (`postprocess.py`) | the corners are filled with the background color |
| 3 | convert, run twice: `PARAMS["bw"]` and `PARAMS["indexed"]` | `PostprocessFile.step3_convert()`: `ConvertResult(image, params)` (`convert.py`) | the preprocessed image |
| 3a | smooth | `ConvertResult.step3a_smooth()` | blur 1.0 |
| 3b | reduce to color groups | `ConvertResult.step3b_reduce()` | median cut to 256, merge at 24 (bw: gray levels, indexed: RGB) |
| 3c | clean the groups | `ConvertResult.step3c_clean()` | edge mixes join a neighbour, at most 16 / 32, core colors |
| 3d | **stretch**, only on a white background | `ConvertResult.step3d_stretch()` | background -> pure white, ink -> black, colored backgrounds unchanged |
| 4 | save | `PostprocessFile.step4_save()`, `ConvertResult.step4_save()` | |

Why this order:

- **2a before 2b**: with the scanner lid still in the image, its straight, axis aligned
  edges would pull the tilt estimate towards 0 degrees.
- **3 after 2**: the colors must be counted on the final geometry; the lid and the
  corners uncovered by the rotation would distort them.
- **3d after 3b/3c**: white and black are decided on the color groups and their pixel
  counts, not on brightness percentiles: a light green background and white text have
  a similar brightness, but are two separate groups. Stretching after the reduction
  also keeps the scanner noise from being amplified.

## Preview directories

Below `tests/scan_postprocess/scans_0_raw_results`, written by
`tests/scan_postprocess/test_scan_postprocess.py`, not committed:

| directory | step | content |
|---|---|---|
| `step2a_border/` | 2a | raw scan, the removed border painted magenta |
| `step2b_tilt/` | 2b | raw scan deskewed with the measured tilt, horizontal lines overlaid |
| `step2c_tilt_border/` | 2c | border removed and deskewed: the result of step 2 |
| `step4_postprocess/` | 4 | the files written by `PostprocessFile`: `*_bw16.png`, `*_indexed32.png` |
