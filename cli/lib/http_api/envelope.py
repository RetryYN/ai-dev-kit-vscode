from typing import Any

try:
    from flask import jsonify, request
    _HAS_FLASK = True
except ModuleNotFoundError:  # pragma: no cover - exercised in the current sandbox
    _HAS_FLASK = False

    class _CompatRequest:
        def __init__(self) -> None:
            self.headers: dict[str, str] = {}
            self.remote_addr: str = ""
            self.path: str = ""
            self.method: str = ""

    class _CompatResponse:
        def __init__(self, payload: dict[str, Any], status: int) -> None:
            self._payload = payload
            self.status_code = status

        def get_json(self) -> dict[str, Any]:
            return self._payload

    request = _CompatRequest()

    def jsonify(payload: dict[str, Any]) -> dict[str, Any]:
        return payload


def _build_response(payload: dict[str, Any], status: int):
    if _HAS_FLASK:
        return jsonify(payload), status
    return _CompatResponse(payload, status)


def success_response(data: Any, trace_id: str, status: int = 200):
    return _build_response({"data": data, "trace_id": trace_id}, status)


def error_response(code: str, message: str, trace_id: str, status: int):
    return _build_response({"error": {"code": code, "message": message}, "trace_id": trace_id}, status)
