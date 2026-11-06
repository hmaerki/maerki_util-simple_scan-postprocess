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

## Scans

- scan_raw-01.png type=bw tilt=-1.7degrees content=hand
- scan_raw-02.png type=indexed tilt=1.8degrees content=hand
- scan_raw-03.png type=bw tilt=0.0degrees content=hand
- scan_raw-04.png type=indexed tilt=0.0degrees content=hand
- scan_raw-05.png type=color tilt=0.0degrees content=mix
- scan_raw-06.png type=color tilt=0.0degrees content=mix
- scan_raw-07.png type=bw tilt=0.0degrees content=machine
- scan_raw-08.png type=bw tilt=0.0degrees content=machine
- scan_raw-09.png type=bw tilt=0.0degrees content=machine
- scan_raw-10.png type=color tilt=0.0degrees content=mix
- scan_raw-11.png type=indexed tilt=-0.2degrees content=machine
- scan_raw-12.png type=indexed tilt=0.2degrees content=machine
- scan_raw-13.png type=color tilt=0.0degrees content=mix
- scan_raw-14.png type=bw tilt=0.0degrees content=machine
- scan_raw-15.png type=indexed tilt=-0.5degrees content=machine
- scan_raw-16.png type=indexed tilt=1.0degrees content=machine
- scan_raw-17.png type=indexed tilt=-1.5degrees content=machine
- scan_raw-18.png type=color tilt=0.4degrees content=mix
- scan_raw-19.png type=color tilt=1.6degrees content=mix
- scan_raw-20.png type=color tilt=-1.8degrees content=mix
- scan_raw-21.png type=indexed tilt=0.0degrees content=machine
- scan_raw-22.png type=indexed tilt=0.0degrees content=machine
- scan_raw-23.png type=indexed tilt=0.0degrees content=machine
- scan_raw-24.png type=indexed tilt=0.5degrees content=machine
