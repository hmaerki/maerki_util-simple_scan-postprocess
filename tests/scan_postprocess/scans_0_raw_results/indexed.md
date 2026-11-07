# Scans reduced to a color palette (indexed)

Written by tests/scan_postprocess/test_scan_postprocess.py.

| file | type | content | level foreground color | level background color | colors | raw kB | indexed kB | ratio |
|---|---|---|---:|---:|---:|---:|---:|---:|
| scan-01-bw.png | bw | hand | 112 | 227 | 9 | 13548 | 142 | 95.1 |
| scan-02-indexed.png | indexed | hand | 129 | 224 | 13 | 14079 | 259 | 54.3 |
| scan-03-bw.png | bw | hand | 133 | 222 | 16 | 13711 | 298 | 46.0 |
| scan-04-indexed.png | indexed | hand | 98 | 223 | 10 | 13535 | 168 | 80.4 |
| scan-05-color.png | color | mix | 72 | 202 | 24 | 13666 | 319 | 42.7 |
| scan-06-color.png | color | mix | 52 | 162 | 24 | 14261 | 425 | 33.5 |
| scan-07-bw.png | bw | machine | 79 | 219 | 16 | 14277 | 342 | 41.7 |
| scan-08-bw.png | bw | machine | 70 | 192 | 24 | 14762 | 439 | 33.6 |
| scan-09-bw.png | bw | machine | 80 | 218 | 13 | 13548 | 268 | 50.4 |
| scan-10-color.png | color | mix | 51 | 168 | 25 | 15988 | 369 | 43.3 |
| scan-11-indexed.png | indexed | machine | 76 | 223 | 20 | 14146 | 253 | 55.7 |
| scan-12-indexed.png | indexed | machine | 76 | 215 | 19 | 13899 | 272 | 50.9 |
| scan-13-color.png | color | mix | 0 | 255 | 11 | 15859 | 385 | 41.1 |
| scan-14-bw.png | bw | machine | 82 | 209 | 20 | 13626 | 365 | 37.2 |
| scan-15-indexed.png | indexed | machine | 93 | 208 | 21 | 14568 | 385 | 37.8 |
| scan-16-indexed.png | indexed | machine | 54 | 205 | 17 | 14621 | 213 | 68.6 |
| scan-17-indexed.png | indexed | machine | 54 | 202 | 18 | 14630 | 222 | 65.8 |
| scan-18-color.png | color | mix | 70 | 196 | 26 | 13713 | 335 | 40.9 |
| scan-19-color.png | color | mix | 70 | 194 | 25 | 13785 | 326 | 42.2 |
| scan-20-color.png | color | mix | 70 | 195 | 25 | 13800 | 330 | 41.8 |
| scan-21-indexed.png | indexed | machine | 0 | 255 | 6 | 14947 | 103 | 145.0 |
| scan-22-indexed.png | indexed | machine | 0 | 255 | 6 | 17612 | 134 | 131.1 |
| scan-23-indexed.png | indexed | machine | 0 | 255 | 2 | 13230 | 33 | 397.8 |
| scan-24-indexed.png | indexed | machine | 0 | 255 | 3 | 17995 | 101 | 177.8 |

- Background color: 90% of the pixels, foreground color: 1% of the pixels, blur radius 1.0, 32 colors merged at distance 24.0
- Total: raw 347818 kB, indexed 6496 kB, ratio 53.5
- Type bw: raw 83473 kB, indexed 1857 kB, ratio 44.9
- Type indexed: raw 163267 kB, indexed 2147 kB, ratio 76.0
- Type color: raw 101076 kB, indexed 2491 kB, ratio 40.6
