from typing import Any
from uuid import uuid4

from fastapi import Request


def problem_json(
    request: Request,
    status: int,
    title: str,
    detail: Any | None = None,
    type_: str = "about:blank",
) -> dict[str, Any]:
    cid = getattr(request.state, "request_id", str(uuid4()))
    return {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "instance": str(request.url),
        "correlation_id": cid,
    }
