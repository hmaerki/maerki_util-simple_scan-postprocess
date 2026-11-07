# Postprocessing for simple-scan

## Links

* https://gitlab.gnome.org/GNOME/simple-scan
* https://manpages.ubuntu.com/manpages/bionic/man1/simple-scan.1.html
* https://gist.github.com/jacksenechal/53dbf568438b212e7886b168ea4221c3


## Setup in `simple-scan`

![](images/simple-scan-icon.png)

![](images/simple-scan-preferences.png)

simple-scan uses 'Script' as the program name: it does **not** split it into words
and does not use a shell. A command line like `uvx --from ... postprocess_simple_scan`
can therefore not be entered directly; use a small wrapper script:

1. Run

```sh
mkdir -p ~/bin
cat > ~/bin/postprocess_simple_scan.sh <<EOF
#!/bin/sh
exec $(command -v uvx) --from git+https://github.com/hmaerki/maerki_util-simple_scan-postprocess@main postprocess_simple_scan "\$@"
EOF
chmod +x ~/bin/postprocess_simple_scan.sh
```

2. simple-scan: Preferences → Postprocessing:
   * Script: `/home/<user>/bin/postprocess_simple_scan.sh`
   * Script arguments: leave empty
   * Keep original file: as you like
3. simple-scan: save the scan as PNG or JPEG.


## Postprocessing interface of simple-scan

Configured in simple-scan: Preferences → Postprocessing:

* **Script**: the executable to run after a document is saved.
* **Script arguments**: an optional string passed to the script.
* **Keep original file**: passed to the script as a flag; the script decides what to do with it.

After saving, simple-scan runs the script directly (no shell) with these arguments
(source: `src/postprocessor.vala`):

| argument | content | example |
|---|---|---|
| `$1` | mime type of the saved file | `application/pdf`, `image/png`, `image/jpeg` |
| `$2` | keep original file | `true` or `false` |
| `$3` | path of the saved file | `/home/user/Documents/Scanned Document.pdf` |
| `$4` | 'Script arguments' from the preferences | `-l deu+eng` |

Notes:

* `$4` is **one single argument**: simple-scan does not split it into words.
  The script has to split it itself (see the example below).
* 'Keep original file' is only passed to the script as `$2`: what happens to the
  saved file is up to the script.
  `true`: write the result to a new file. `false`: replace the saved file.
* The script runs without a terminal: write errors to a log file.

### Example: OCR with ocrmypdf

Requires `ocrmypdf` (`sudo apt install ocrmypdf`). Make the script executable
(`chmod +x`) and enter its path as 'Script', for example 'Script arguments' `-l deu+eng`.

```bash
#!/usr/bin/env bash
# simple-scan postprocessing: add a text layer to a scanned PDF with ocrmypdf.
#   $1 mime type, $2 keep original (true/false), $3 filename, $4 script arguments
set -euo pipefail

mime_type="$1"
keep_original="$2"
filename="$3"
# $4 is one string: split it into words for ocrmypdf.
read -r -a extra_args <<< "${4:-}"

log=/tmp/simple-scan-ocrmypdf.log

if [[ "$mime_type" != "application/pdf" ]]; then
    echo "$(date): skipped '$filename': $mime_type is not a PDF" >> "$log"
    exit 0
fi

if [[ "$keep_original" == "true" ]]; then
    output="${filename%.pdf}_ocr.pdf"
else
    output="$filename"   # ocrmypdf may write over its input
fi

if ocrmypdf --rotate-pages --deskew "${extra_args[@]}" "$filename" "$output" >> "$log" 2>&1; then
    notify-send "OCR complete" "$output" || true
else
    notify-send "OCR failed" "See $log" || true
    exit 1
fi
```

## Using scan_postprocess as simple-scan script

The entry point `postprocess_simple_scan`
(`src/scan_postprocess/main_postprocess_simple_scan.py`, registered in
`pyproject.toml` under `[project.scripts]`) implements the interface above:

* Writes `<stem>_bw16.png` and `<stem>_indexed32.png` next to the scanned file
  (see `README_DESIGN.md`).
* 'Keep original file' off: the scanned file is deleted after both files are written.
* Only images are processed: in simple-scan, save as **PNG** or **JPEG**.
  PDF and other mime types are skipped.
* 'Script arguments' are not used yet.
* Log file: `/tmp/postprocess_simple_scan.log`.

Run it without installing, with [uv](https://docs.astral.sh/uv/):

```bash
uvx --from git+https://github.com/hmaerki/maerki_util-simple_scan-postprocess@main \
    postprocess_simple_scan image/png true "/home/user/Documents/Scanned Document.png"
```

The first call downloads and builds the package, later calls use the uv cache.

