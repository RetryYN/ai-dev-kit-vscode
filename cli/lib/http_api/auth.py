import os

from typing import Optional

from .envelope import error_response, request

LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


def require_localhost_and_bearer() -> Optional[object]:
    trace_id = request.headers.get("X-Trace-Id", "")
    remote = request.remote_addr or ""
    if remote not in LOCAL_HOSTS:
        return error_response("AUTH_FAILED", f"non-localhost peer rejected: {remote}", trace_id, 403)

    expected = os.environ.get("HELIX_HTTP_API_TOKEN", "")
    if not expected:
        return error_response("AUTH_NOT_CONFIGURED", "HELIX_HTTP_API_TOKEN unset", trace_id, 403)

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return error_response("AUTH_FAILED", "missing or malformed Authorization header", trace_id, 403)

    if auth[len("Bearer ") :] != expected:
        return error_response("AUTH_FAILED", "invalid token", trace_id, 403)

    return None
