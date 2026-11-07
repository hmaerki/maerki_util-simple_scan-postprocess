"""Entry point for simple-scan: Preferences -> Postprocessing -> Script.

simple-scan calls the script with (see README.md):
    $1 mime type, $2 keep original ('true'/'false'), $3 filename,
    $4 'Script arguments' as one single string.

For every scanned image, PostprocessFile writes next to it:
    <stem>_bw16.png and <stem>_indexed32.png
If 'keep original' is 'false', the scanned image is deleted afterwards.

Only images are processed (save as PNG or JPEG in simple-scan): PDF and other
mime types are skipped. The script runs without a terminal: everything is
logged to LOGFILE.
"""

from __future__ import annotations

import logging
import pathlib
import shlex
import sys
import tempfile

from scan_postprocess.postprocess import PostprocessFile

LOGFILE = pathlib.Path(tempfile.gettempdir()) / "postprocess_simple_scan.log"

logger = logging.getLogger("postprocess_simple_scan")


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOGFILE), logging.StreamHandler()],
        force=True,
    )


def main(argv: list[str] | None = None) -> int:
    """Return the exit status: 0 ok or skipped, 1 failed, 2 wrong arguments."""
    args = sys.argv[1:] if argv is None else argv
    _setup_logging()
    if len(args) < 3:
        logger.error(
            "Usage: postprocess_simple_scan <mime type> <keep original true|false>"
            " <filename> [<script arguments>]"
        )
        return 2
    mime_type, keep_original, filename = args[0], args[1], pathlib.Path(args[2])
    arguments = shlex.split(args[3]) if len(args) > 3 else []
    logger.info(
        "mime_type=%s keep_original=%s filename=%s", mime_type, keep_original, filename
    )
    if arguments:
        logger.warning("Script arguments are not used yet, ignored: %s", arguments)

    if not mime_type.startswith("image/"):
        logger.info("Skipped: %s is not an image, save as PNG or JPEG", mime_type)
        return 0

    try:
        scan = PostprocessFile(filename, directory_out=filename.parent)
        scan.postprocess_file()
    except Exception:
        logger.exception("Failed: %s", filename)
        return 1

    for conversion in ("bw", "indexed"):
        logger.info("Written: %s", scan.filename_out(conversion))
    if keep_original == "false":
        filename.unlink()
        logger.info("Deleted the original: %s", filename)
    return 0


if __name__ == "__main__":
    sys.exit(main())
