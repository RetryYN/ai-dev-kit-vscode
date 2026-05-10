cmd_import() {
  local import_from_frontmatter=false
  local dry_run=false
  local force=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --from-frontmatter)
        import_from_frontmatter=true
        shift
        ;;
      --dry-run)
        dry_run=true
        shift
        ;;
      --force)
        force=true
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

  if [[ "$import_from_frontmatter" == false ]]; then
    import_from_frontmatter=true
  fi

  ensure_dirs

  python3 - <<'PY' "$PROJECT_ROOT" "$PLAN_DIR" "$SCRIPT_DIR/lib" "$dry_run" "$force"
import sys
from pathlib import Path

project_root = Path(sys.argv[1])
plan_dir = Path(sys.argv[2])
lib_dir = Path(sys.argv[3])
dry_run = sys.argv[4] == "true"
force = sys.argv[5] == "true"

if str(lib_dir) not in sys.path:
    sys.path.insert(0, str(lib_dir))

import plan_frontmatter
import yaml_parser


VALID_STATUSES = {"completed", "finalized"}


def _normalize_timestamp(value: object) -> str | None:
    if value in (None, "", "null"):
        return None
    text = str(value).strip()
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return f"{text}T00:00:00Z"
    return text


def _plan_id_from_frontmatter(frontmatter: dict, docs_path: Path) -> str | None:
    plan_id = frontmatter.get("plan_id")
    if isinstance(plan_id, str) and plan_id.startswith("PLAN-"):
        return plan_id
    prefix = docs_path.stem.split("-", 2)
    if len(prefix) >= 2:
        candidate = f"{prefix[0]}-{prefix[1]}"
        if candidate.startswith("PLAN-"):
            return candidate
    return None


def _build_plan_yaml(frontmatter: dict, docs_rel: str, plan_id: str) -> str:
    created = _normalize_timestamp(frontmatter.get("created"))
    if created is None:
        raise SystemExit(f"エラー: {docs_rel}: created が必要です")
    finalized = _normalize_timestamp(frontmatter.get("finalized")) or created
    title = frontmatter.get("title") or plan_id
    data = {
        "id": plan_id,
        "title": title,
        "status": "finalized",
        "created_at": created,
        "source_file": docs_rel,
        "references": [],
        "artifacts": [],
        "finalized_at": finalized,
        "review": {
            "status": "approve",
            "reviewed_at": created,
            "review_file": None,
        },
    }
    return yaml_parser.dump_yaml(data) + "\n"


docs_dir = project_root / "docs" / "plans"
if not docs_dir.is_dir():
    raise SystemExit("エラー: docs/plans が見つかりません")

plan_dir.mkdir(parents=True, exist_ok=True)
for docs_path in sorted(docs_dir.glob("PLAN-*.md")):
    docs_rel = docs_path.relative_to(project_root).as_posix()
    text = docs_path.read_text(encoding="utf-8")
    try:
        frontmatter, _body = plan_frontmatter._parse_frontmatter(text)
    except plan_frontmatter.PlanFrontmatterError as exc:
        if "must start with YAML frontmatter" in str(exc):
            print(f"skip no-frontmatter {docs_rel}")
            continue
        raise SystemExit(f"エラー: {docs_rel}: {exc}")

    status = str(frontmatter.get("status") or "").strip()
    if status not in VALID_STATUSES:
        print(f"skip status={status or 'missing'} {docs_rel}")
        continue

    plan_id = _plan_id_from_frontmatter(frontmatter, docs_path)
    if not plan_id:
        raise SystemExit(f"エラー: {docs_rel}: plan_id を特定できません")

    plan_path = plan_dir / f"{plan_id}.yaml"
    if plan_path.exists() and not force:
        print(f"skip exists {plan_path.relative_to(project_root).as_posix()}")
        continue

    rendered = _build_plan_yaml(frontmatter, docs_rel, plan_id)
    action = "overwrite" if plan_path.exists() else "create"
    if dry_run:
        print(f"dry-run {action} {plan_path.relative_to(project_root).as_posix()} <- {docs_rel}")
        continue

    plan_path.write_text(rendered, encoding="utf-8")
    print(f"{action} {plan_path.relative_to(project_root).as_posix()} <- {docs_rel}")
PY
}
