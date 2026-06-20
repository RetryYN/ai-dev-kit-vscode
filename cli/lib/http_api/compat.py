from __future__ import annotations

from typing import Any, Callable, Optional


class _CompatNormalizedResponse:
    def __init__(self, payload: Any, status: int) -> None:
        self._payload = payload
        self.status_code = status

    def get_json(self) -> Any:
        return self._payload


def _normalize_response(result: Any):
    if isinstance(result, tuple):
        payload, status = result
        return _CompatNormalizedResponse(payload, status)
    return result


try:
    from flask import Blueprint, Flask, request
except ModuleNotFoundError:  # pragma: no cover - exercised in the current sandbox
    from .envelope import request

    class Blueprint:  # type: ignore[override]
        def __init__(self, name: str, import_name: str) -> None:
            self.name = name
            self.import_name = import_name
            self._routes: dict[tuple[str, str], Callable[..., Any]] = {}

        def route(
            self,
            path: str,
            methods: list[str] | None = None,
        ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            method_list = methods or ["GET"]

            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                for method in method_list:
                    self._routes[(path, method.upper())] = func
                return func

            return decorator


    def _match_route(pattern: str, path: str) -> bool:
        pattern_parts = pattern.strip("/").split("/")
        path_parts = path.strip("/").split("/")
        if len(pattern_parts) != len(path_parts):
            return False
        for pattern_part, path_part in zip(pattern_parts, path_parts):
            if pattern_part.startswith("<") and pattern_part.endswith(">"):
                if not path_part:
                    return False
                continue
            if pattern_part != path_part:
                return False
        return True


    def _extract_route_args(pattern: str, path: str) -> list[str] | None:
        if not _match_route(pattern, path):
            return None
        route_args: list[str] = []
        for pattern_part, path_part in zip(pattern.strip("/").split("/"), path.strip("/").split("/")):
            if pattern_part.startswith("<") and pattern_part.endswith(">"):
                route_args.append(path_part)
        return route_args


    class Flask:  # type: ignore[override]
        _helix_blueprint_routes_patched = False

        def __init__(self, import_name: str) -> None:
            self.import_name = import_name
            self.config: dict[str, Any] = {}
            self._before_request: Optional[Callable[[], Any]] = None
            self._errorhandlers: dict[int, Callable[[Any], Any]] = {}
            self._routes: dict[tuple[str, str], Callable[..., Any]] = {}

        def before_request(self, func: Callable[[], Any]) -> Callable[[], Any]:
            self._before_request = func
            return func

        def errorhandler(self, code: int) -> Callable[[Callable[[Any], Any]], Callable[[Any], Any]]:
            def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
                self._errorhandlers[code] = func
                return func

            return decorator

        def route(
            self,
            path: str,
            methods: list[str] | None = None,
        ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            method_list = methods or ["GET"]

            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                for method in method_list:
                    self._routes[(path, method.upper())] = func
                return func

            return decorator

        def register_blueprint(self, blueprint: Any) -> None:
            self._routes.update(getattr(blueprint, "_routes", {}))
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

        def _dispatch(
            self,
            method: str,
            path: str,
            *,
            headers: Optional[dict[str, str]] = None,
            environ_base: Optional[dict[str, str]] = None,
            json: Any = None,
            query_string: Optional[dict[str, Any]] = None,
        ):
            request.path = path
            request.method = method
            request.remote_addr = (environ_base or {}).get("REMOTE_ADDR", "127.0.0.1")
            request.headers = dict(headers or {})
            request.args = dict(query_string or {})
            request._json_payload = json

            def _get_json(silent: bool = True):
                return getattr(request, "_json_payload", None)

            request.get_json = _get_json  # type: ignore[attr-defined]

            if self.app._before_request is not None:
                gate_result = self.app._before_request()
                if gate_result is not None:
                    return _normalize_response(gate_result)

            route = self.app._routes.get((path, method))
            route_args: list[str] = []
            if route is None:
                for (route_path, route_method), candidate in self.app._routes.items():
                    if route_method != method:
                        continue
                    matched_args = _extract_route_args(route_path, path)
                    if matched_args is not None:
                        route = candidate
                        route_args = matched_args
                        break

            if route is None:
                handler = self.app._errorhandlers.get(404)
                result = handler(None) if handler is not None else ("not found", 404)
                return _normalize_response(result)

            try:
                return _normalize_response(route(*route_args))
            except Exception as exc:
                handler = self.app._errorhandlers.get(500)
                if handler is None:
                    raise
                return _normalize_response(handler(exc))

        def get(
            self,
            path: str,
            headers: Optional[dict[str, str]] = None,
            environ_base: Optional[dict[str, str]] = None,
            query_string: Optional[dict[str, Any]] = None,
        ):
            return self._dispatch(
                "GET",
                path,
                headers=headers,
                environ_base=environ_base,
                query_string=query_string,
            )

        def post(
            self,
            path: str,
            headers: Optional[dict[str, str]] = None,
            environ_base: Optional[dict[str, str]] = None,
            json: Any = None,
            query_string: Optional[dict[str, Any]] = None,
        ):
            return self._dispatch(
                "POST",
                path,
                headers=headers,
                environ_base=environ_base,
                json=json,
                query_string=query_string,
            )
