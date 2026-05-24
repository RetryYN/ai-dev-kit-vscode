#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../" && pwd)"

export HELIX_PROJECT_ROOT="${HELIX_PROJECT_ROOT:-$PROJECT_ROOT}"
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

RECOVERY_CURRENT="$HELIX_PROJECT_ROOT/.helix/recovery/CURRENT.json"

if [[ ! -f "$RECOVERY_CURRENT" ]]; then
  exit 0
fi

STATUS="$(
  python3 - "$RECOVERY_CURRENT" <<'PY' 2>/dev/null || true
import json
import sys

try:
    payload = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception:
    print("")
else:
    print(str(payload.get("status") or ""))
PY
)"

if [[ "$STATUS" != "active" ]]; then
  exit 0
fi

python3 - <<'PY'
from cli.lib.recovery_workflow_engine import snapshot_on_stop

snapshot_on_stop()
PY

echo "[HELIX Recovery] 停止を検出。recovery session (active) の状態を snapshot しました。"
echo "[HELIX Recovery] 推奨: /compact を実行してから次の作業を開始してください。"
