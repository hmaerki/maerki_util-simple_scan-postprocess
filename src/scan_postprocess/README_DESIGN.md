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
| 3a | smooth | `ConvertResult.step3a_smooth()` | bw: off, indexed: blur 1.0 |
| 3b | measure the levels | `ConvertResult.step3b_measure_levels()` | with the cover guard |
| 3c | **stretch** and reduce to the palette | `ConvertResult.step3c_reduce()` | |
| 3d | merge colors | `ConvertResult.step3d_merge()` | bw: off, indexed: 24 |
| 4 | save | `PostprocessFile.step4_save()`, `ConvertResult.step4_save()` | |

Why this order:

- **2a before 2b**: with the scanner lid still in the image, its straight, axis aligned
  edges would pull the tilt estimate towards 0 degrees.
- **3c after 2**: the levels must be measured on the final geometry; the lid and the
  corners uncovered by the rotation would distort them. In 'indexed' the levels are
  measured after the smoothing (3a): the scanner noise does not count either.

## Preview directories

Below `tests/scan_postprocess/scans_0_raw_results`, written by
`tests/scan_postprocess/test_scan_postprocess.py`, not committed:

| directory | step | content |
|---|---|---|
| `step2a_border/` | 2a | raw scan, the removed border painted magenta |
| `step2b_tilt/` | 2b | raw scan deskewed with the measured tilt, horizontal lines overlaid |
| `step2c_tilt_border/` | 2c | border removed and deskewed: the result of step 2 |
| `step4_postprocess/` | 4 | the files written by `PostprocessFile`: `*_bw16.png`, `*_indexed32.png` |
