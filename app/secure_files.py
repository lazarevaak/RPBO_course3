# app/secure_files.py
import uuid
from pathlib import Path

MAX_SIZE = 2 * 1024 * 1024  # 2 MB
PNG = b"\x89PNG\r\n\x1a\n"
SOI, EOI = b"\xff\xd8", b"\xff\xd9"


def detect_type(data: bytes) -> str | None:
    if data.startswith(PNG):
        return "image/png"
    if data.startswith(SOI) and data.endswith(EOI):
        return "image/jpeg"
    return None


def secure_save(root: Path, data: bytes) -> Path:
    if len(data) > MAX_SIZE:
        raise ValueError("File too large")
    mime = detect_type(data)
    if not mime:
        raise ValueError("Invalid file type")
    root = root.resolve(strict=True)
    ext = ".png" if mime == "image/png" else ".jpg"
    dest = (root / f"{uuid.uuid4()}{ext}").resolve()
    if not str(dest).startswith(str(root)):
        raise ValueError("Path traversal detected")
    if any(p.is_symlink() for p in dest.parents):
        raise ValueError("Symlink parent forbidden")
    dest.write_bytes(data)
    return dest
