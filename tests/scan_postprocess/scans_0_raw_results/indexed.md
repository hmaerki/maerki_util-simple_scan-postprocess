# Indexed scans reduced to a color palette

Written by tests/scan_postprocess/test_scan_postprocess.py.

| file | content | level black | level white | colors | raw kB | indexed kB | ratio |
|---|---|---:|---:|---:|---:|---:|---:|
| scan_raw-02.png | hand | 129 | 224 | 13 | 14079 | 260 | 54.1 |
| scan_raw-04.png | hand | 98 | 223 | 10 | 13535 | 168 | 80.4 |
| scan_raw-11.png | machine | 76 | 223 | 20 | 14146 | 253 | 55.9 |
| scan_raw-12.png | machine | 76 | 215 | 19 | 13899 | 272 | 50.9 |
| scan_raw-15.png | machine | 93 | 208 | 21 | 14568 | 385 | 37.8 |
| scan_raw-16.png | machine | 54 | 205 | 17 | 14621 | 213 | 68.6 |
| scan_raw-17.png | machine | 54 | 202 | 18 | 14630 | 223 | 65.4 |
| scan_raw-21.png | machine | 0 | 255 | 7 | 14947 | 107 | 139.1 |
| scan_raw-22.png | machine | 0 | 255 | 8 | 17612 | 143 | 123.1 |
| scan_raw-23.png | machine | 0 | 255 | 4 | 13230 | 75 | 175.4 |
| scan_raw-24.png | machine | 0 | 255 | 5 | 17995 | 161 | 111.7 |

- White: 90% of the pixels, black: 1% of the pixels, blur radius 1.0, 32 colors merged at distance 24.0
- Total: raw 163267 kB, indexed 2264 kB, ratio 72.1
