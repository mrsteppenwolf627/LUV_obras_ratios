from pathlib import Path
import subprocess
import sys


def test_inspect_repo_runs():
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "inspect_repo.py"

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Main directories" in result.stdout
    assert "Methodology files" in result.stdout
