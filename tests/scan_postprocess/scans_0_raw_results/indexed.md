# Scans reduced to a color palette (indexed)

Written by tests/scan_postprocess/test_scan_postprocess.py.

| file | type | content | level foreground color | level background color | colors | raw kB | indexed kB | ratio |
|---|---|---|---:|---:|---:|---:|---:|---:|
| scan-01-bw.png | bw | hand | 67 | 230 | 4 | 13548 | 47 | 284.5 |
| scan-02-indexed.png | indexed | hand | 85 | 228 | 6 | 14079 | 120 | 116.5 |
| scan-03-bw.png | bw | hand | 0 | 227 | 6 | 13711 | 152 | 89.7 |
| scan-04-indexed.png | indexed | hand | 72 | 227 | 4 | 13535 | 79 | 170.9 |
| scan-05-color.png | color | mix | 66 | 216 | 9 | 13666 | 291 | 46.9 |
| scan-06-color.png | color | mix | 51 | 216 | 11 | 14261 | 420 | 33.9 |
| scan-07-bw.png | bw | machine | 56 | 228 | 4 | 14277 | 121 | 117.6 |
| scan-08-bw.png | bw | machine | 79 | 228 | 3 | 14762 | 170 | 86.5 |
| scan-09-bw.png | bw | machine | 77 | 225 | 4 | 13548 | 144 | 93.6 |
| scan-10-color.png | color | mix | 41 | 218 | 23 | 15988 | 382 | 41.8 |
| scan-11-indexed.png | indexed | machine | 64 | 230 | 5 | 14146 | 151 | 93.3 |
| scan-12-indexed.png | indexed | machine | 62 | 225 | 5 | 13899 | 154 | 90.0 |
| scan-13-color.png | color | mix | 39 | 226 | 31 | 15859 | 486 | 32.6 |
| scan-14-bw.png | bw | machine | 84 | 226 | 3 | 13626 | 145 | 93.6 |
| scan-15-indexed.png | indexed | machine | 98 | 225 | 2 | 14568 | 85 | 171.2 |
| scan-16-indexed.png | indexed | machine | 34 | 221 | 5 | 14621 | 157 | 92.8 |
| scan-17-indexed.png | indexed | machine | 34 | 221 | 8 | 14630 | 234 | 62.4 |
| scan-18-color.png | color | mix | 58 | 215 | 11 | 13713 | 324 | 42.2 |
| scan-19-color.png | color | mix | 58 | 215 | 11 | 13785 | 339 | 40.6 |
| scan-20-color.png | color | mix | 63 | 216 | 10 | 13800 | 320 | 43.0 |
| scan-21-indexed.png | indexed | machine | 0 | 255 | 6 | 14947 | 124 | 119.6 |
| scan-22-indexed.png | indexed | machine | 0 | 255 | 8 | 17612 | 162 | 108.3 |
| scan-23-indexed.png | indexed | machine | 0 | 255 | 5 | 13230 | 86 | 153.6 |
| scan-24-indexed.png | indexed | machine | 0 | 255 | 5 | 17995 | 108 | 166.5 |

- Blur radius 1.0, at most 32 colors, merged at distance 24.0 (RGB)
- Total: raw 347818 kB, indexed 4813 kB, ratio 72.3
- Type bw: raw 83473 kB, indexed 782 kB, ratio 106.6
- Type indexed: raw 163267 kB, indexed 1465 kB, ratio 111.4
- Type color: raw 101076 kB, indexed 2565 kB, ratio 39.4
