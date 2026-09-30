"""Legacy JSONL transport for the local AUTOWORK service.

The desktop application now uses :mod:`api` as its primary transport. This
entry point remains available for compatibility with scripts that already use
the original one-request/one-response JSONL protocol.
"""

from __future__ import annotations

import json
import sys
from contextlib import redirect_stdout

from service import AutoworkService


SERVICE = AutoworkService()


def reply(request_id: str, *, result: object | None = None, error: str | None = None) -> None:
    message = {"id": request_id, "ok": error is None}
    if error is None:
        message["result"] = result
    else:
        message["error"] = error
    print(json.dumps(message, ensure_ascii=False), flush=True)


def handle(request: dict[str, object]) -> object:
    action = request.get("action")
    payload = request.get("payload")
    with redirect_stdout(sys.stderr):
        return SERVICE.handle(str(action), payload)


def main() -> None:
    from api import configure_logging
    configure_logging()
    print(json.dumps({"event": "ready", "service": "AUTOWORK"}), flush=True)
    for raw_line in sys.stdin:
        if not raw_line.strip():
            continue
        request = None
        try:
            request = json.loads(raw_line)
            request_id = str(request["id"])
            reply(request_id, result=handle(request))
        except Exception as error:  # Keep the process alive for the next request.
            request_id = str(request.get("id", "unknown")) if isinstance(request, dict) else "unknown"
            reply(request_id, error=str(error))


if __name__ == "__main__":
    main()
