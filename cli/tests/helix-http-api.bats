#!/usr/bin/env bats

setup() {
  TOOL_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
}

@test "http_api server can create_app and /health returns 200" {
  run python3 - <<PY
import sys
sys.path.insert(0, "${TOOL_ROOT}/cli/lib")
from http_api.server import create_app
app = create_app()
app.config["TESTING"] = True
with app.test_client() as c:
    r = c.get("/health")
    assert r.status_code == 200, r.status_code
    assert r.get_json()["data"]["status"] == "ok"
print("ok")
PY
  [ "$status" -eq 0 ]
  [[ "$output" == *"ok"* ]]
}
