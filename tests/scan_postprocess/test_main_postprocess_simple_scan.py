"""Call the simple-scan entry point like simple-scan does."""

from __future__ import annotations

import pathlib
import shutil

from scan_postprocess.main_postprocess_simple_scan import main

FILENAME_SCAN = pathlib.Path(__file__).parent / "scans_0_raw" / "scan-01-bw.png"


def _copy_scan(tmp_path: pathlib.Path) -> pathlib.Path:
    filename = tmp_path / "Scanned Document.png"
    shutil.copyfile(FILENAME_SCAN, filename)
    return filename


def test_keep_original(tmp_path: pathlib.Path) -> None:
    filename = _copy_scan(tmp_path)
    assert main(["image/png", "true", str(filename), ""]) == 0
    assert filename.exists()
    assert (tmp_path / "Scanned Document_bw16.png").exists()
    assert (tmp_path / "Scanned Document_indexed32.png").exists()


def test_delete_original(tmp_path: pathlib.Path) -> None:
    filename = _copy_scan(tmp_path)
    assert main(["image/png", "false", str(filename)]) == 0
    assert not filename.exists()
    assert (tmp_path / "Scanned Document_bw16.png").exists()
    assert (tmp_path / "Scanned Document_indexed32.png").exists()


def test_skip_pdf(tmp_path: pathlib.Path) -> None:
    filename = tmp_path / "Scanned Document.pdf"
    filename.write_bytes(b"%PDF-1.4")
    assert main(["application/pdf", "false", str(filename)]) == 0
    assert filename.exists(), "A skipped file must not be deleted"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["Scanned Document.pdf"]


def test_wrong_arguments() -> None:
    assert main([]) == 2
