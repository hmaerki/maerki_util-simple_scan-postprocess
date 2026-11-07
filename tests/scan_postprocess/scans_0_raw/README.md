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

- scan-01-bw.png type=bw tilt=-1.7degrees content=hand border=no
- scan-02-indexed.png type=indexed tilt=1.8degrees content=hand border=no
- scan-03-bw.png type=bw tilt=0.0degrees content=hand border=no
- scan-04-indexed.png type=indexed tilt=0.0degrees content=hand border=no
- scan-05-color.png type=color tilt=0.0degrees content=mix border=no
- scan-06-color.png type=color tilt=0.0degrees content=mix border=no
- scan-07-bw.png type=bw tilt=0.0degrees content=machine border=no
- scan-08-bw.png type=bw tilt=0.0degrees content=machine border=no
- scan-09-bw.png type=bw tilt=0.0degrees content=machine border=no
- scan-10-color.png type=color tilt=0.0degrees content=mix border=no
- scan-11-indexed.png type=indexed tilt=-0.2degrees content=machine border=no
- scan-12-indexed.png type=indexed tilt=0.2degrees content=machine border=no
- scan-13-color.png type=color tilt=0.0degrees content=mix border=no
- scan-14-bw.png type=bw tilt=0.0degrees content=machine border=no
- scan-15-indexed.png type=indexed tilt=-0.5degrees content=machine border=no
- scan-16-indexed.png type=indexed tilt=1.0degrees content=machine border=no
- scan-17-indexed.png type=indexed tilt=-1.5degrees content=machine border=no
- scan-18-color.png type=color tilt=0.4degrees content=mix border=no
- scan-19-color.png type=color tilt=1.6degrees content=mix border=no
- scan-20-color.png type=color tilt=-1.8degrees content=mix border=no
- scan-21-indexed.png type=indexed tilt=0.0degrees content=machine border=yes
- scan-22-indexed.png type=indexed tilt=0.0degrees content=machine border=yes
- scan-23-indexed.png type=indexed tilt=0.0degrees content=machine border=yes
- scan-24-indexed.png type=indexed tilt=0.5degrees content=machine border=yes
