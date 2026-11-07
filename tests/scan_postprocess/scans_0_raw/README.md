# scans_0_raw

Raw scans: A4, 300 dpi, RGB.

Attributes per scan, read by `tests/scan_postprocess/test_scan_postprocess.py`:

- `type`: what the scan may be reduced to without losing information
  - `bw`: black/gray ink on white paper
  - `indexed`: a few flat colors (blue pen, colored logos, colored book covers)
  - `color`: photos or many colors
- `tilt`: rotation of the content in degrees, range -5 .. 5.
  Positive: counter-clockwise (lines rise to the right). Deskew with `image.rotate(-tilt)`.
- `content`
  - `machine`: printed text
  - `hand`: handwriting / hand drawing
  - `images`: mainly pictures
  - `mix`: printed text combined with photos and signatures
- `border`: `yes` if the scanner lid is visible around the paper.
  Thin dark lines along the image edge do not count.

## Scans

| file | type | tilt | content | border |
|---|---|---:|---|---|
| scan-01-bw.png | bw | -1.7 | hand | no |
| scan-02-indexed.png | indexed | 1.8 | hand | no |
| scan-03-bw.png | bw | 0.0 | hand | no |
| scan-04-indexed.png | indexed | 0.0 | hand | no |
| scan-05-color.png | color | 0.0 | mix | no |
| scan-06-color.png | color | 0.0 | mix | no |
| scan-07-bw.png | bw | 0.0 | machine | no |
| scan-08-bw.png | bw | 0.0 | machine | no |
| scan-09-bw.png | bw | 0.0 | machine | no |
| scan-10-color.png | color | 0.0 | mix | no |
| scan-11-indexed.png | indexed | -0.2 | machine | no |
| scan-12-indexed.png | indexed | 0.2 | machine | no |
| scan-13-color.png | color | 0.0 | mix | no |
| scan-14-bw.png | bw | 0.0 | machine | no |
| scan-15-indexed.png | indexed | -0.5 | machine | no |
| scan-16-indexed.png | indexed | 1.0 | machine | no |
| scan-17-indexed.png | indexed | -1.5 | machine | no |
| scan-18-color.png | color | 0.4 | mix | no |
| scan-19-color.png | color | 1.6 | mix | no |
| scan-20-color.png | color | -1.8 | mix | no |
| scan-21-indexed.png | indexed | 0.0 | machine | yes |
| scan-22-indexed.png | indexed | 0.0 | machine | yes |
| scan-23-indexed.png | indexed | 0.0 | machine | yes |
| scan-24-indexed.png | indexed | 0.5 | machine | yes |
