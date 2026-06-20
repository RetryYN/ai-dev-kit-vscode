from .compat import Flask, _CompatClient, _CompatNormalizedResponse, _normalize_response, request


from .auth import require_localhost_and_bearer
from .envelope import error_response, success_response
from .routes import audit, hooks, push_pr, telemetry
from .validation import validate_request_headers

PUBLIC_PATHS = {"/health"}
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
