from typing import Any, Callable, Optional

try:
    from flask import Flask, request
    _HAS_FLASK = True
except ModuleNotFoundError:  # pragma: no cover - exercised in the current sandbox
    _HAS_FLASK = False
    from .envelope import request

    class Flask:  # type: ignore[override]
        def __init__(self, import_name: str) -> None:
            self.import_name = import_name
            self.config: dict[str, Any] = {}
            self._before_request: Optional[Callable[[], Any]] = None
            self._errorhandlers: dict[int, Callable[[Any], Any]] = {}
            self._routes: dict[tuple[str, str], Callable[[], Any]] = {}

        def before_request(self, func: Callable[[], Any]) -> Callable[[], Any]:
            self._before_request = func
            return func

        def errorhandler(self, code: int) -> Callable[[Callable[[Any], Any]], Callable[[Any], Any]]:
            def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
                self._errorhandlers[code] = func
                return func

            return decorator

        def route(self, path: str, methods: list[str] | None = None) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
            method_list = methods or ["GET"]

            def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
                for method in method_list:
                    self._routes[(path, method.upper())] = func
                return func

            return decorator

        def register_blueprint(self, blueprint: Any) -> None:
            return None

        def test_client(self) -> "_CompatClient":
            return _CompatClient(self)

    class _CompatClient:
        def __init__(self, app: Flask) -> None:
            self.app = app

        def __enter__(self) -> "_CompatClient":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, path: str, headers: Optional[dict[str, str]] = None, environ_base: Optional[dict[str, str]] = None):
            request.path = path
            request.method = "GET"
            request.remote_addr = (environ_base or {}).get("REMOTE_ADDR", "127.0.0.1")
            request.headers = dict(headers or {})

            if self.app._before_request is not None:
                gate_result = self.app._before_request()
                if gate_result is not None:
                    return _normalize_response(gate_result)

            route = self.app._routes.get((path, "GET"))
            if route is None:
                handler = self.app._errorhandlers.get(404)
                if handler is not None:
                    return _normalize_response(handler(None))
                return _normalize_response(("not found", 404))

            return _normalize_response(route())


from .auth import require_localhost_and_bearer
from .envelope import error_response, success_response
from .routes import audit, hooks, push_pr, telemetry
from .validation import validate_request_headers

PUBLIC_PATHS = {"/health"}


def _normalize_response(result: Any):
    if isinstance(result, tuple):
        payload, status = result
        return _CompatNormalizedResponse(payload, status)
    return result


class _CompatNormalizedResponse:
    def __init__(self, payload: Any, status: int) -> None:
        self._payload = payload
        self.status_code = status

    def get_json(self) -> Any:
        return self._payload


def create_app() -> Flask:
    app = Flask(__name__)

    @app.before_request
    def _auth_gate():
        validation_response = validate_request_headers(request)
        if validation_response is not None:
            return validation_response

        if request.path in PUBLIC_PATHS:
            return None

        return require_localhost_and_bearer()

    @app.errorhandler(404)
    def _not_found(_error):
        trace_id = request.headers.get("X-Trace-Id", "")
        return error_response("NOT_FOUND", "endpoint not found", trace_id, 404)

    @app.errorhandler(405)
    def _method_not_allowed(_error):
        trace_id = request.headers.get("X-Trace-Id", "")
        return error_response("METHOD_NOT_ALLOWED", "method not allowed", trace_id, 405)

    @app.errorhandler(500)
    def _internal_error(_error):
        trace_id = request.headers.get("X-Trace-Id", "")
        return error_response("INTERNAL_ERROR", "internal server error", trace_id, 500)

    @app.route("/health", methods=["GET"])
    def health():
        return success_response({"status": "ok"}, request.headers.get("X-Trace-Id", ""))

    @app.route("/api/v1/_status", methods=["GET"])
    def status():
        return success_response(
            {"server": "helix-http-api", "version": "0.1.0"},
            request.headers.get("X-Trace-Id", ""),
        )

    app.register_blueprint(audit.bp)
    app.register_blueprint(push_pr.bp)
    app.register_blueprint(hooks.bp)
    app.register_blueprint(telemetry.bp)

    return app
