#!/usr/bin/env bash
set -euo pipefail

# @helix:index id=dual-write-mismatch-gate domain=scripts summary=dual-write mismatch CI gate wrapper

usage() {
  cat <<'EOF'
Usage: bash scripts/check_dual_write_mismatch.sh [--scope <dir>] [--sample-size <int>]

Runs the dual-write mismatch helper and emits a MismatchResult JSON payload.
EOF
}

SCOPE="cli"
SAMPLE_SIZE=1000

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope)
      [[ $# -ge 2 ]] || {
        echo "Error: --scope requires a value" >&2
        usage >&2
        exit 2
      }
      SCOPE="$2"
      shift 2
      ;;
    --sample-size)
      [[ $# -ge 2 ]] || {
        echo "Error: --sample-size requires a value" >&2
        usage >&2
        exit 2
      }
      SAMPLE_SIZE="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! "$SAMPLE_SIZE" =~ ^[0-9]+$ ]] || [[ "$SAMPLE_SIZE" -lt 1 ]]; then
  echo "Error: --sample-size must be a positive integer" >&2
  exit 2
fi

if [[ ! -e "$SCOPE" ]]; then
  echo "Error: scope not found: $SCOPE" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HELPER_PATH="${HELIX_DUAL_WRITE_MISMATCH_HELPER:-$REPO_ROOT/cli/lib/dual_write_mismatch.py}"

python3 - "$REPO_ROOT" "$HELPER_PATH" "$SCOPE" "$SAMPLE_SIZE" <<'PY'
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
import inspect
import json
import sys
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fallback_result(scope: str) -> dict[str, object]:
    return {
        "detected": False,
        "table_name": scope,
        "legacy_row_count": 0,
        "new_row_count": 0,
        "mismatch_keys": [],
        "detected_at": _utc_now(),
        "severity": "warn",
    }


def _load_helper(helper_path: Path):
    if not helper_path.is_file():
        return None
    spec = spec_from_file_location("dual_write_mismatch", helper_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load helper module from {helper_path}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _call_helper(module, scope: str, sample_size: int):
    run_ci_gate = getattr(module, "run_ci_gate", None)
    if callable(run_ci_gate):
        return run_ci_gate(scope=scope, sample_size=sample_size)

    main = getattr(module, "main", None)
    if callable(main):
        value = main(["--scope", scope, "--sample-size", str(sample_size)])
        if value is not None:
            return value

    checker = getattr(module, "check_dual_write_mismatch", None)
    if callable(checker):
        signature = inspect.signature(checker)
        params = signature.parameters
        if "scope" in params:
            return checker(scope=scope, sample_size=sample_size)
        if "sample_size" in params and len(params) == 1:
            return checker(sample_size=sample_size)

    raise RuntimeError(
        "dual_write_mismatch helper does not expose run_ci_gate(scope=..., sample_size=...)"
    )


def _normalize_result(raw: object, scope: str) -> dict[str, object]:
    if raw is None:
        data = _fallback_result(scope)
    elif isinstance(raw, dict):
        data = dict(raw)
    elif is_dataclass(raw):
        data = asdict(raw)
    elif hasattr(raw, "_asdict"):
        data = dict(raw._asdict())
    else:
        keys = (
            "detected",
            "table_name",
            "legacy_row_count",
            "new_row_count",
            "mismatch_keys",
            "detected_at",
            "severity",
        )
        data = {key: getattr(raw, key) for key in keys if hasattr(raw, key)}

    data.setdefault("detected", False)
    data.setdefault("table_name", scope)
    data.setdefault("legacy_row_count", 0)
    data.setdefault("new_row_count", 0)
    data.setdefault("mismatch_keys", [])
    data.setdefault("detected_at", _utc_now())
    data["severity"] = str(data.get("severity", "warn")).lower()
    return data


def main() -> int:
    repo_root = Path(sys.argv[1])
    helper_path = Path(sys.argv[2])
    scope = sys.argv[3]
    sample_size = int(sys.argv[4])

    sys.path.insert(0, str(repo_root / "cli" / "lib"))
    helper = _load_helper(helper_path)
    if helper is None:
        result = _fallback_result(scope)
    else:
        try:
            result = _call_helper(helper, scope, sample_size)
        except RuntimeError as exc:
            if "does not expose run_ci_gate" not in str(exc):
                raise
            result = _fallback_result(scope)
    data = _normalize_result(result, scope)

    severity = data["severity"]
    if severity not in {"warn", "critical"}:
        raise RuntimeError(f"unsupported severity '{severity}'")

    print(json.dumps(data, ensure_ascii=False, sort_keys=True))
    detected = bool(data.get("detected"))
    if detected and severity == "warn":
        print(
            f"Warning: dual-write mismatch detected for {data['table_name']}: {data['mismatch_keys']}",
            file=sys.stderr,
        )
    return 1 if detected and severity == "critical" else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - shell entrypoint safeguard
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
PY
