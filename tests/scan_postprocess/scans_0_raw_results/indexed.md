# Scans reduced to a color palette (indexed)

Written by tests/scan_postprocess/test_scan_postprocess.py.

| file | type | content | level foreground color | level background color | colors | raw kB | indexed kB | ratio |
|---|---|---|---:|---:|---:|---:|---:|---:|
| scan-01-bw.png | bw | hand | 52 | 230 | 3 | 13548 | 49 | 273.0 |
| scan-02-indexed.png | indexed | hand | 72 | 229 | 4 | 14079 | 78 | 178.4 |
| scan-03-bw.png | bw | hand | 65 | 227 | 5 | 13711 | 189 | 72.4 |
| scan-04-indexed.png | indexed | hand | 58 | 227 | 4 | 13535 | 104 | 129.6 |
| scan-05-color.png | color | mix | 61 | 216 | 5 | 13666 | 274 | 49.8 |
| scan-06-color.png | color | mix | 55 | 217 | 4 | 14261 | 267 | 53.4 |
| scan-07-bw.png | bw | machine | 65 | 228 | 3 | 14277 | 189 | 75.2 |
| scan-08-bw.png | bw | machine | 66 | 228 | 3 | 14762 | 263 | 56.1 |
| scan-09-bw.png | bw | machine | 65 | 226 | 3 | 13548 | 152 | 88.7 |
| scan-10-color.png | color | mix | 29 | 218 | 10 | 15988 | 398 | 40.1 |
| scan-11-indexed.png | indexed | machine | 39 | 230 | 4 | 14146 | 112 | 125.9 |
| scan-12-indexed.png | indexed | machine | 73 | 225 | 3 | 13899 | 109 | 126.7 |
| scan-13-color.png | color | mix | 30 | 226 | 9 | 15859 | 790 | 20.1 |
| scan-14-bw.png | bw | machine | 70 | 226 | 3 | 13626 | 193 | 70.3 |
| scan-15-indexed.png | indexed | machine | 80 | 226 | 2 | 14568 | 87 | 166.1 |
| scan-16-indexed.png | indexed | machine | 31 | 222 | 5 | 14621 | 320 | 45.7 |
| scan-17-indexed.png | indexed | machine | 34 | 222 | 7 | 14630 | 423 | 34.6 |
| scan-18-color.png | color | mix | 56 | 216 | 8 | 13713 | 362 | 37.8 |
| scan-19-color.png | color | mix | 56 | 216 | 7 | 13785 | 290 | 47.5 |
| scan-20-color.png | color | mix | 60 | 216 | 7 | 13800 | 318 | 43.4 |
| scan-21-indexed.png | indexed | machine | 0 | 255 | 6 | 14947 | 137 | 109.0 |
| scan-22-indexed.png | indexed | machine | 0 | 255 | 7 | 17612 | 257 | 68.4 |
| scan-23-indexed.png | indexed | machine | 0 | 255 | 4 | 13230 | 92 | 142.4 |
| scan-24-indexed.png | indexed | machine | 0 | 255 | 4 | 17995 | 109 | 164.7 |

- Blur radius 0.3, at most 32 colors, merged at distance 24.0 (RGB)
- Total: raw 347818 kB, indexed 5573 kB, ratio 62.4
- Type bw: raw 83473 kB, indexed 1038 kB, ratio 80.4
- Type indexed: raw 163267 kB, indexed 1833 kB, ratio 89.1
- Type color: raw 101076 kB, indexed 2701 kB, ratio 37.4
