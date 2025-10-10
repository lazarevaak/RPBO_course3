import subprocess
import sys
from pathlib import Path


def test_coverage_threshold():
    """NFR-07: Проверка, что покрытие тестами ≥ 80 %."""
    exclude = Path(__file__).name
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--cov=app",
        "--cov-report=term",
        "--cov-fail-under=80",
        "-k",
        f"not {exclude}",
    ]
    process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
    code = process.wait()
    if code == 0:
        print("\nNFR-07: покрытие тестами ≥ 80 % — выполнено")
    else:
        sys.exit("\nНедостаточное покрытие тестами (менее 80 %)")


if __name__ == "__main__":
    test_coverage_threshold()
