from pathlib import Path
import subprocess
import sys


def test_validate_context_ok():
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "validate_context.py"

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK:" in result.stdout
