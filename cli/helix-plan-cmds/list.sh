cmd_list() {
  ensure_dirs
  local status_filter=""
  local kind_filter=""
  local layer_filter=""
  local json=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --status)
        status_filter="$2"
        shift 2
        ;;
      --kind)
        kind_filter="$2"
        shift 2
        ;;
      --layer)
        layer_filter="$2"
        shift 2
        ;;
      --json)
        json=true
        shift
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        echo "エラー: 不明なオプションです: $1" >&2
        exit 1
        ;;
    esac
  done

  python3 - <<'PY' "$PROJECT_ROOT" "$PLAN_DIR" "$status_filter" "$kind_filter" "$layer_filter" "$json"
import json
import sys
from pathlib import Path

import yaml

project_root = Path(sys.argv[1])
plan_dir = Path(sys.argv[2])
status_filter = sys.argv[3]
kind_filter = sys.argv[4]
layer_filter = sys.argv[5]
json_output = sys.argv[6] == "true"
docs_root = project_root / "docs" / "plans"
items: list[dict[str, str]] = []
seen_plan_ids: set[str] = set()


def frontmatter(path: Path) -> dict[str, object] | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            payload = yaml.safe_load("\n".join(lines[1:idx])) or {}
            return payload if isinstance(payload, dict) else None
    return None


def add_item(item: dict[str, str]) -> None:
    plan_id = item["plan_id"]
    if not plan_id or plan_id in seen_plan_ids:
        return
    seen_plan_ids.add(plan_id)
    items.append(item)


if docs_root.exists():
    for path in sorted(docs_root.rglob("*plan.md")):
        data = frontmatter(path)
        if not data:
            continue
        plan_id = data.get("plan_id")
        if not isinstance(plan_id, str) or not plan_id.strip():
            continue
        add_item(
            {
                "plan_id": plan_id,
                "title": str(data.get("title", "")),
                "status": str(data.get("status", "")),
                "layer": str(data.get("layer", "-") or "-"),
                "kind": str(data.get("kind", "")),
                "area": "docs/plans",
                "path": str(path.relative_to(project_root)),
            }
        )

for path in sorted(plan_dir.glob("PLAN-*.yaml")):
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        continue
    plan_id = data.get("id")
    if not isinstance(plan_id, str) or not plan_id.strip():
        continue
    add_item(
        {
            "plan_id": plan_id,
            "title": str(data.get("title", "")),
            "status": str(data.get("status", "")),
            "layer": "-",
            "kind": "legacy",
            "area": ".helix/plans",
            "path": str(path.relative_to(project_root)),
        }
    )

filtered = [
    item
    for item in sorted(items, key=lambda entry: (entry["plan_id"], entry["path"]))
    if (not status_filter or item["status"] == status_filter)
    and (not kind_filter or item["kind"] == kind_filter)
    and (not layer_filter or item["layer"] == layer_filter)
]

if json_output:
    print(json.dumps({"plans": filtered}, ensure_ascii=False, indent=2))
elif not filtered:
    print("プランは登録されていません。")
else:
    print(f"{'Plan ID':<40} | {'Title':<48} | {'Status':<12} | Layer")
    print("-" * 120)
    for item in filtered:
        print(
            f"{item['plan_id']:<40} | {item['title'][:48]:<48} | "
            f"{item['status']:<12} | {item['layer']}"
        )
PY
}
