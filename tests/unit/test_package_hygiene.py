# SPDX-License-Identifier: MIT
import os
import zipfile
import pytest
from scripts.build_submission_zip import should_exclude, scan_file_for_secrets, build_submission_zip

def test_should_exclude_rules():
    assert should_exclude(".git/config") is True
    assert should_exclude(".pytest_cache/v/cache") is True
    assert should_exclude("bin/toxiproxy-server.exe") is True
    assert should_exclude("__pycache__/test.pyc") is True
    assert should_exclude("reports/fault_run.json") is True
    assert should_exclude("reports/README.md") is False
    assert should_exclude("reports/.gitkeep") is False
    assert should_exclude("app/main.py") is False

def test_secret_scanner_detects_tokens():
    clean_bytes = b"def test_foo(): pass"
    assert len(scan_file_for_secrets(clean_bytes, "clean.py")) == 0

    # Dynamically constructed to test detection without storing literal pattern in repo
    mock_token = b"glpat-" + b"mocksecrettoken1234567890"
    assert len(scan_file_for_secrets(mock_token, "leak.py")) > 0

def test_build_submission_zip_creates_valid_archive(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app").mkdir()
    (src / "app" / "main.py").write_text("print('hello')", encoding="utf-8")
    (src / "bin").mkdir()
    (src / "bin" / "toxiproxy.exe").write_text("fake binary", encoding="utf-8")

    out_zip = str(tmp_path / "test-sub.zip")
    zip_path, size, sha = build_submission_zip(str(src), out_zip)
    assert os.path.exists(zip_path)
    assert size > 0
    assert len(sha) == 64

    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        assert "app/main.py" in names
        assert not any("bin" in n for n in names)
