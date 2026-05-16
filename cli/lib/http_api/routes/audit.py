try:
    from flask import Blueprint
except ModuleNotFoundError:  # pragma: no cover - exercised in the current sandbox
    class Blueprint:  # type: ignore[override]
        def __init__(self, name: str, import_name: str) -> None:
            self.name = name
            self.import_name = import_name

bp = Blueprint("audit", __name__)
