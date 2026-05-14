from pathlib import Path
import shutil
import uuid

from scripts.hash_files import collect_hashes


def _make_root() -> Path:
    base = Path(__file__).resolve().parents[2] / ".tmp_tests"
    base.mkdir(exist_ok=True)
    root = base / f"hash_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def test_collect_hashes_detects_duplicates():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)

        (samples / "a.txt").write_text("same-content", encoding="utf-8")
        (samples / "b.txt").write_text("same-content", encoding="utf-8")
        (samples / "c.txt").write_text("other-content", encoding="utf-8")

        report = collect_hashes(root, Path("data/samples"))

        assert report["exists"] is True
        assert report["files_count_total"] == 3
        assert report["sample_files_count"] == 3
        assert len(report["duplicates_by_hash"]) == 1
        assert report["duplicates_by_hash"][0]["count"] == 2
    finally:
        _cleanup(root)


def test_collect_hashes_empty_samples():
    root = _make_root()
    try:
        (root / "data" / "samples").mkdir(parents=True)

        report = collect_hashes(root, Path("data/samples"))

        assert report["exists"] is True
        assert report["files_count_total"] == 0
        assert report["sample_files_count"] == 0
        assert report["duplicates_by_hash"] == []
    finally:
        _cleanup(root)


def test_collect_hashes_excludes_gitkeep_from_sample_count():
    root = _make_root()
    try:
        samples = root / "data" / "samples"
        samples.mkdir(parents=True)
        (samples / ".gitkeep").write_text("", encoding="utf-8")
        (samples / "real.bc3").write_text("~K|sample", encoding="utf-8")

        report = collect_hashes(root, Path("data/samples"))

        assert report["files_count_total"] == 2
        assert report["sample_files_count"] == 1
        assert report["ignored_files_count"] == 1
        gitkeep_entry = next(f for f in report["files"] if f["filename"] == ".gitkeep")
        assert gitkeep_entry["is_ignored"] is True
    finally:
        _cleanup(root)
