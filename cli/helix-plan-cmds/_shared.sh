PLAN_DIR="$HELIX_DIR/plans"
MINI_PLAN_DIR="$HELIX_DIR/mini-plans"
REVIEW_DIR="$HELIX_DIR/reviews/plans"
PLAN_FRONTMATTER="$SCRIPT_DIR/lib/plan_frontmatter.py"
HELIX_CODEX="${HELIX_CODEX:-$SCRIPT_DIR/helix-codex}"
REVIEW_SCHEMA="$SCRIPT_DIR/schemas/review-output.schema.json"
PLAN_LINT="$SCRIPT_DIR/lib/plan_lint.py"
PLAN_VALIDATOR="$SCRIPT_DIR/lib/plan_validator.py"
DEPS_HELPER="${DEPS_HELPER:-$SCRIPT_DIR/lib/plan_deps_helper.py}"
GENERATES_HELPER="${GENERATES_HELPER:-$SCRIPT_DIR/lib/plan_deps_helper.py}"

ensure_dirs() {
  mkdir -p "$PLAN_DIR" "$MINI_PLAN_DIR" "$REVIEW_DIR"
}

validate_plan_id() {
  local id="$1"
  if [[ ! "$id" =~ ^PLAN-[0-9]{3,}$ ]]; then
    echo "エラー: 不正な plan id です: $id (例: PLAN-001)" >&2
    exit 1
  fi
}

validate_mini_plan_id() {
  local id="$1"
  if [[ ! "$id" =~ ^MPLAN-[0-9]{3,}$ ]]; then
    echo "エラー: 不正な mini plan id です: $id (例: MPLAN-001)" >&2
    exit 1
  fi
}

validate_parent_plan_id() {
  local id="$1"
  if [[ ! "$id" =~ ^(PLAN|MPLAN)-[0-9]{3,}$ ]]; then
    echo "エラー: 不正な parent plan id です: $id (例: PLAN-001 or MPLAN-001)" >&2
    exit 1
  fi
}

plan_file_path() {
  local id="$1"
  echo "$PLAN_DIR/$id.yaml"
}

ensure_plan_exists() {
  local id="$1"
  local plan_file
  plan_file="$(plan_file_path "$id")"
  if [[ ! -f "$plan_file" ]]; then
    echo "エラー: プランが見つかりません: $id" >&2
    exit 1
  fi
}

yaml_read() {
  local file="$1"
  local dotpath="$2"
  python3 "$YAML_PARSER" read "$file" "$dotpath" 2>/dev/null || true
}

yaml_write() {
  local file="$1"
  local dotpath="$2"
  local value="$3"
  python3 "$YAML_PARSER" write "$file" "$dotpath" "$value" >/dev/null 2>&1
}

next_plan_id() {
  local max_num=0
  local f base num
  shopt -s nullglob
  for f in "$PLAN_DIR"/PLAN-*.yaml; do
    base="$(basename "$f" .yaml)"
    num="${base#PLAN-}"
    if [[ "$num" =~ ^[0-9]+$ ]]; then
      num=$((10#$num))
      if (( num > max_num )); then
        max_num=$num
      fi
    fi
  done
  shopt -u nullglob
  printf "PLAN-%03d" $((max_num + 1))
}

next_mini_plan_id() {
  python3 - <<'PY' "$SCRIPT_DIR/lib" "$MINI_PLAN_DIR"
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])

import plan_schema

print(plan_schema.next_mini_plan_id(Path(sys.argv[2])))
PY
}

check_mini_plan_cycle() {
  local child_plan_id="$1"
  local parent_plan_id="$2"
  python3 - <<'PY' "$SCRIPT_DIR/lib" "$PROJECT_ROOT" "$child_plan_id" "$parent_plan_id"
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])

import plan_schema

cycle = plan_schema.detect_mini_plan_cycle(Path(sys.argv[2]), sys.argv[3], sys.argv[4])
if cycle:
    print(" -> ".join(cycle))
    sys.exit(1)
PY
}

record_mini_plan_relation() {
  local parent_plan_id="$1"
  local child_plan_id="$2"
  local mini_plan_rel="$3"
  python3 - <<'PY' "$SCRIPT_DIR/lib" "$HELIX_DIR/helix.db" "$parent_plan_id" "$child_plan_id" "$mini_plan_rel"
import json
import sys
from pathlib import Path

lib_dir = Path(sys.argv[1])
db_path = sys.argv[2]
parent_plan_id = sys.argv[3]
child_plan_id = sys.argv[4]
mini_plan_rel = sys.argv[5]
sys.path.insert(0, str(lib_dir))

import helix_db


def entry_id(plan_id: str) -> str:
    prefix = "mini-plan" if plan_id.startswith("MPLAN-") else "plan"
    return f"{prefix}:{plan_id}"


def metadata_json(plan_id: str, parent_plan_id: str | None, child_plan_id: str | None, kind: str) -> str:
    payload = {
        "plan_id": plan_id,
        "parent_plan_id": parent_plan_id,
        "child_plan_id": child_plan_id,
        "kind": kind,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


conn = helix_db._connect(str(db_path))
try:
    helix_db._ensure_schema(conn)
    parent_entry_id = entry_id(parent_plan_id)
    child_entry_id = entry_id(child_plan_id)
    conn.execute(
        """
        INSERT OR IGNORE INTO entries
            (id, axis, lifecycle, ref, metadata, updated_at)
        VALUES
            (?, 'plan', 'initial', ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            parent_entry_id,
            f"plan:{parent_plan_id}",
            metadata_json(parent_plan_id, None, child_plan_id, "parent-plan"),
        ),
    )
    conn.execute(
        """
        INSERT INTO entries
            (id, axis, lifecycle, parent_entry_id, ref, metadata, updated_at)
        VALUES
            (?, 'plan', 'addition', ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            child_entry_id,
            parent_entry_id,
            mini_plan_rel,
            metadata_json(child_plan_id, parent_plan_id, child_plan_id, "mini-plan"),
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO links (from_id, to_id, kind, metadata)
        VALUES (?, ?, 'derives_from', ?)
        """,
        (
            child_entry_id,
            parent_entry_id,
            json.dumps(
                {"parent_plan_id": parent_plan_id, "child_plan_id": child_plan_id},
                ensure_ascii=False,
                sort_keys=True,
            ),
        ),
    )
    conn.commit()
finally:
    conn.close()
PY
}
