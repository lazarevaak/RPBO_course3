import re
from pathlib import Path

SUSPICIOUS_PATTERNS = [
    r"\.execute\(",
    r"\.executescript\(",
    r"text\(",
    r"f[\"'].*(SELECT|INSERT|UPDATE|DELETE).*?[\"']",
]


def test_no_raw_sql_in_app_code():
    """NFR-04: Проверка, что в проекте не используется raw SQL."""
    app_dir = Path("app")
    py_files = list(app_dir.rglob("*.py"))
    violations = []

    for file_path in py_files:
        text = file_path.read_text(encoding="utf-8")
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                violations.append(f"{file_path}: содержит {pattern}")

    if violations:
        print("\n Найдены потенциально небезопасные SQL-вызовы:")
        for v in violations:
            print("  -", v)

    assert not violations, "Обнаружены небезопасные SQL-вызовы!"
