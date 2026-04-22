#!/usr/bin/env python3
"""HELIX スキル推挙結果を実際の委譲アクションへ変換する。"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redaction import redact_value
import skill_catalog


HELIX_CODEX_BIN = os.environ.get("HELIX_CODEX_BIN", "helix-codex")


def _dispatch_timeout_seconds() -> int:
    raw = os.environ.get("HELIX_DISPATCH_TIMEOUT", "").strip()
    if not raw:
        return 300
    try:
        value = int(raw)
    except ValueError:
        return 300
    return max(1, value)

CLAUDE_NATIVE_AGENTS = {
    "fe-design",
    "fe-component",
    "fe-style",
    "fe-test",
    "fe-a11y",
}

CODEX_ROLES = {
    "tl", "se", "pg", "fe", "qa", "security", "dba", "devops",
    "docs", "research", "legacy", "perf",
}


class DispatcherError(RuntimeError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def _repo_root() -> Path:
    env_root = os.environ.get("HELIX_PROJECT_ROOT", "").strip()
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[2]


def _default_skills_root() -> Path:
    env_root = os.environ.get("HELIX_SKILLS_ROOT", "").strip()
    if env_root:
        return Path(env_root).resolve()
    helix_home = os.environ.get("HELIX_HOME", "").strip()
    if helix_home:
        return (Path(helix_home) / "skills").resolve()
    candidate = Path.home() / "ai-dev-kit-vscode" / "skills"
    if candidate.exists():
        return candidate.resolve()
    return _repo_root() / "skills"


def _default_catalog_path() -> Path:
    return _repo_root() / ".helix" / "cache" / "skill-catalog.json"


def _default_db_path() -> Path:
    return _repo_root() / ".helix" / "helix.db"


def _resolve_skill_md_path(skill: dict, skills_root: Path) -> Path:
    raw = skill.get("path", "")
    if not raw:
        raise DispatcherError(7, f"skill path が未定義: {skill.get('id')}")
    p = Path(raw)
    if p.is_absolute():
        return p
    if raw.startswith("skills/"):
        return skills_root.parent / raw
    return skills_root / raw


def _safe_reference_path(skill_dir: Path, ref: str) -> Path | None:
    if Path(ref).is_absolute():
        sys.stderr.write(f"警告: 絶対パス指定の reference は拒否しました: {ref}\n")
        return None
    try:
        base = skill_dir.resolve()
        candidate = (skill_dir / ref).resolve()
    except (OSError, RuntimeError) as e:
        sys.stderr.write(f"警告: reference パス解決失敗: {ref} ({e})\n")
        return None
    try:
        candidate.relative_to(base)
    except ValueError:
        sys.stderr.write(
            f"警告: reference が skill ディレクトリ外を指しているため拒否しました: {ref}\n"
        )
        return None
    return candidate


def build_context_bundle(skill: dict, references: list[str], skills_root: Path) -> str:
    skill_path = _resolve_skill_md_path(skill, skills_root)
    skill_dir = skill_path.parent

    lines: list[str] = [
        f"# Skill Context Bundle: {skill.get('id', '(unknown)')}",
        "",
        f"- helix_layer: {skill.get('helix_layer', '')}",
        f"- description: {skill.get('description', '')}",
        "",
        "## SKILL.md",
        "",
    ]
    if skill_path.exists():
        lines.append(skill_path.read_text(encoding="utf-8"))
    else:
        sys.stderr.write(f"警告: SKILL.md が見つかりません: {skill_path}\n")
        lines.append(f"(SKILL.md 不在: {skill_path})")

    if references:
        valid_refs: list[tuple[str, Path]] = []
        for ref in references:
            resolved = _safe_reference_path(skill_dir, ref)
            if resolved is not None:
                valid_refs.append((ref, resolved))

        if valid_refs:
            lines.append("")
            lines.append(f"## References ({len(valid_refs)})")
            lines.append("")
            for ref, ref_path in valid_refs:
                lines.append(f"### {ref}")
                lines.append("")
                if ref_path.exists():
                    lines.append(ref_path.read_text(encoding="utf-8"))
                else:
                    sys.stderr.write(f"警告: reference が見つかりません: {ref_path}\n")
                    lines.append(f"(reference 不在: {ref_path})")
                lines.append("")

    return "\n".join(lines)


def determine_agent(skill: dict, recommended_agent: str | None = None) -> dict:
    if recommended_agent:
        return _normalize_agent(recommended_agent)

    skill_id = skill.get("id", "")
    layer = skill.get("helix_layer", "") or ""
    category = skill.get("category", "") or ""

    if "visual-design" in skill_id or skill_id == "design-tools/web-system":
        return _normalize_agent("fe-design")
    if skill_id in ("project/ui", "common/design"):
        return _normalize_agent("fe-component")
    if skill_id == "common/security" or "security" in skill_id:
        return _normalize_agent("helix-codex --role security")
    if skill_id in ("workflow/verification", "common/testing"):
        return _normalize_agent("helix-codex --role qa")
    if skill_id == "advanced/tech-selection":
        return _normalize_agent("helix-codex --role research")
    if "L7" in layer:
        return _normalize_agent("helix-codex --role devops")
    if skill_id.startswith("advanced/legacy") or layer.startswith("R"):
        return _normalize_agent("helix-codex --role legacy")
    if skill_id == "common/performance":
        return _normalize_agent("helix-codex --role perf")
    if skill_id in ("workflow/design-doc", "workflow/api-contract", "workflow/adversarial-review"):
        return _normalize_agent("helix-codex --role tl")
    if category == "writing" or skill_id.startswith("workflow/") and "doc" in skill_id:
        return _normalize_agent("helix-codex --role docs")
    if "db" in skill_id.lower() and "L3" in layer:
        return _normalize_agent("helix-codex --role dba")
    if layer in ("L1", "L2") and category == "workflow":
        return _normalize_agent("helix-codex --role tl")
    if layer == "L4":
        return _normalize_agent("helix-codex --role pg")
    return _normalize_agent("helix-codex --role tl")


def _normalize_agent(spec: str) -> dict:
    spec = spec.strip()
    if spec.startswith("@"):
        name = spec.lstrip("@")
        return _subagent_dict(name)
    if spec in CLAUDE_NATIVE_AGENTS:
        return _subagent_dict(spec)
    if spec.startswith("helix-codex"):
        parts = spec.split()
        role = "pg"
        if "--role" in parts:
            idx = parts.index("--role")
            if idx + 1 < len(parts):
                role = parts[idx + 1]
        return _codex_dict(role)
    if spec in CODEX_ROLES:
        return _codex_dict(spec)
    if spec.startswith("codex:"):
        return _codex_dict(spec.split(":", 1)[1])
    return _codex_dict("pg")


def _subagent_dict(name: str) -> dict:
    return {
        "type": "subagent",
        "name": name,
        "invoke": f"@{name}",
        "is_claude_native": True,
    }


def _codex_dict(role: str) -> dict:
    return {
        "type": "codex",
        "name": role,
        "invoke": f"helix-codex --role {role}",
        "is_claude_native": False,
    }


def _ensure_db_schema(conn: sqlite3.Connection) -> None:
    """helix_db のマイグレーションを適用し、DB を最新スキーマに揃える。"""
    try:
        import helix_db
    except ImportError:
        return
    try:
        # 可能なら helix_db 側の初期化ルーチンをそのまま使う
        ensure_schema = getattr(helix_db, "_ensure_schema", None)
        if callable(ensure_schema):
            ensure_schema(conn)
            return

        # fallback: 空 DB でも基礎テーブル + schema_version + migrate を揃える
        conn.executescript(getattr(helix_db, "SCHEMA", ""))
        conn.executescript(getattr(helix_db, "SCHEMA_VERSION_SCHEMA", ""))
        migrate = getattr(helix_db, "migrate", None)
        if callable(migrate):
            migrate(conn)
    except Exception as e:
        sys.stderr.write(f"警告: DB マイグレーション失敗: {e}\n")


def _insert_usage(db_path: Path, row: dict) -> int:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        _ensure_db_schema(conn)
        cols = list(row.keys())
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO skill_usage ({', '.join(cols)}) VALUES ({placeholders})"
        conn.execute(sql, [row[c] for c in cols])
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()


def _update_usage(db_path: Path, usage_id: int, fields: dict) -> None:
    if not fields:
        return
    conn = sqlite3.connect(str(db_path))
    try:
        _ensure_db_schema(conn)
        # 未知のカラムを skip してエラー回避（旧 DB がマイグレで列追加されるまでの保険）
        existing_cols = {r[1] for r in conn.execute("PRAGMA table_info(skill_usage)")}
        safe_fields = {k: v for k, v in fields.items() if k in existing_cols}
        if not safe_fields:
            return
        sets = ", ".join(f"{k} = ?" for k in safe_fields)
        values = list(safe_fields.values()) + [usage_id]
        conn.execute(f"UPDATE skill_usage SET {sets} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def dispatch(
    skill_id: str,
    task_text: str,
    recommended_agent: str | None,
    references: list[str],
    catalog_path: Path | None = None,
    skills_root: Path | None = None,
    db_path: Path | None = None,
    dry_run: bool = False,
) -> dict:
    catalog_path = catalog_path or _default_catalog_path()
    skills_root = skills_root or _default_skills_root()
    db_path = db_path or _default_db_path()

    try:
        catalog = skill_catalog.load_catalog(catalog_path)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
        catalog = None
    if catalog is None:
        catalog = skill_catalog.build_catalog(skills_root)
        try:
            skill_catalog.save_catalog(catalog, catalog_path)
        except OSError:
            pass

    skill = skill_catalog.find_skill(catalog, skill_id)
    if skill is None:
        raise DispatcherError(7, f"スキルが見つかりません: {skill_id}")

    bundle = build_context_bundle(skill, references or [], skills_root)
    agent = determine_agent(skill, recommended_agent)

    if dry_run:
        return {
            "skill_id": skill_id,
            "usage_id": None,
            "agent": agent,
            "outcome": "plan_only",
            "context_bundle": bundle,
            "context_bundle_lines": bundle.count("\n") + 1,
            "references": references,
            "dry_run": True,
            "stdout": None,
            "stderr": None,
        }

    row = {
        "task_text": redact_value(task_text),
        "skill_id": skill_id,
        "references_used": json.dumps(references or [], ensure_ascii=False),
        "agent_used": agent["invoke"],
        "outcome": "pending",
    }
    usage_id = _insert_usage(db_path, row)

    if agent["is_claude_native"]:
        hint = (
            f"Claude Code のネイティブサブエージェントのため、次のメッセージで\n"
            f"  {agent['invoke']}\n"
            f"を呼び出してください。\n\n"
            f"スキル: {skill_id}\n"
            f"タスク: {task_text}\n"
            f"skill_usage に usage_id={usage_id} を記録しました。"
        )
        _update_usage(db_path, usage_id, {
            "outcome": "delegated_via_mention",
            "completed_at": datetime.now().isoformat(),
        })
        return {
            "skill_id": skill_id,
            "usage_id": usage_id,
            "agent": agent,
            "outcome": "delegated_via_mention",
            "stdout": hint,
            "stderr": None,
            "context_bundle_lines": bundle.count("\n") + 1,
        }

    combined_task = f"{bundle}\n\n# User Task\n\n{task_text}"
    timeout_seconds = _dispatch_timeout_seconds()
    task_tmp: Path | None = None
    try:
        import tempfile
        fd, tmpname = tempfile.mkstemp(prefix="helix-dispatch-", suffix=".md")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(combined_task)
        except Exception:
            os.close(fd) if not os.path.exists(tmpname) else None
            raise
        task_tmp = Path(tmpname)

        codex_cmd = [
            HELIX_CODEX_BIN,
            "--role", agent["name"],
            "--task-file", str(task_tmp),
            "--timeout", str(timeout_seconds),
        ]
        if os.environ.get("HELIX_SKILL_AUTO_THINKING") == "1":
            codex_cmd.append("--auto-thinking")
        proc = subprocess.run(
            codex_cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds + 30,
        )
        outcome = "delegated" if proc.returncode == 0 else "failed"
        _update_usage(db_path, usage_id, {
            "outcome": outcome,
            "result_stdout": redact_value(proc.stdout),
            "result_stderr": redact_value(proc.stderr),
            "completed_at": datetime.now().isoformat(),
        })
        return {
            "skill_id": skill_id,
            "usage_id": usage_id,
            "agent": agent,
            "outcome": outcome,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        _update_usage(db_path, usage_id, {
            "outcome": "timeout",
            "completed_at": datetime.now().isoformat(),
        })
        raise DispatcherError(5, f"helix-codex タイムアウト ({timeout_seconds}s)")
    except FileNotFoundError:
        _update_usage(db_path, usage_id, {
            "outcome": "failed",
            "completed_at": datetime.now().isoformat(),
        })
        raise DispatcherError(3, f"{HELIX_CODEX_BIN} が見つかりません")
    finally:
        if task_tmp is not None:
            try:
                task_tmp.unlink(missing_ok=True)
            except OSError:
                pass


def record_feedback(usage_id: int, feedback: str, db_path: Path | None = None) -> None:
    db_path = db_path or _default_db_path()
    _update_usage(db_path, usage_id, {"user_feedback": feedback})


def _gini_coefficient(values: list[int]) -> float:
    non_negative = [max(0, int(v)) for v in values]
    n = len(non_negative)
    total = sum(non_negative)
    if n == 0 or total == 0:
        return 0.0

    sorted_values = sorted(non_negative)
    weighted_sum = sum((idx + 1) * value for idx, value in enumerate(sorted_values))
    gini = (2.0 * weighted_sum) / (n * total) - (n + 1.0) / n
    return max(0.0, min(1.0, gini))


def _gini_label(gini: float) -> str:
    if gini <= 0.3:
        return "均等"
    if gini <= 0.5:
        return "やや偏り"
    if gini <= 0.7:
        return "偏り大"
    return "集中"


def _load_skill_inventory(
    catalog_path: Path | None = None,
    skills_root: Path | None = None,
) -> dict[str, int]:
    catalog_path = catalog_path or _default_catalog_path()
    skills_root = skills_root or _default_skills_root()

    catalog: dict[str, Any] | None = None
    try:
        catalog = skill_catalog.load_catalog(catalog_path)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
        catalog = None

    if catalog is None:
        try:
            catalog = skill_catalog.build_catalog(skills_root)
        except OSError:
            catalog = None
        else:
            try:
                skill_catalog.save_catalog(catalog, catalog_path)
            except OSError:
                pass

    if not isinstance(catalog, dict):
        return {"total_skills": 0, "total_categories": 0}

    skills = catalog.get("skills", [])
    if not isinstance(skills, list):
        skills = []

    categories: set[str] = set()
    for item in skills:
        if not isinstance(item, dict):
            continue
        category = str(item.get("category", "")).strip()
        if not category:
            skill_id = str(item.get("id", ""))
            category = skill_id.split("/", 1)[0] if "/" in skill_id else "other"
        categories.add(category)

    total_skills = int(catalog.get("skill_count", len(skills)) or 0)
    if total_skills <= 0:
        total_skills = len(skills)

    return {
        "total_skills": total_skills,
        "total_categories": len(categories),
    }


def _empty_stats(total_skills: int, total_categories: int) -> dict[str, Any]:
    return {
        "total": 0,
        "success_rate": 0.0,
        "avg_score": 0.0,
        "top_skills": [],
        "by_category": {},
        "diversity": {
            "unique_skills_used": 0,
            "total_skills": total_skills,
            "coverage_rate": 0.0,
            "gini_coefficient": 0.0,
            "gini_label": _gini_label(0.0),
            "top_skill_share": 0.0,
            "top_skill_id": "",
            "category_count": 0,
            "total_categories": total_categories,
        },
    }


def stats(
    db_path: Path | None = None,
    days: int = 30,
    catalog_path: Path | None = None,
    skills_root: Path | None = None,
) -> dict:
    db_path = db_path or _default_db_path()
    inventory = _load_skill_inventory(catalog_path=catalog_path, skills_root=skills_root)
    total_skills = inventory["total_skills"]
    total_categories = inventory["total_categories"]

    if not db_path.exists():
        return _empty_stats(total_skills, total_categories)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        cutoff = f"datetime('now', '-{int(days)} days')"

        total_row = conn.execute(
            f"SELECT COUNT(*) AS total FROM skill_usage WHERE created_at >= {cutoff}"
        ).fetchone()
        total = total_row["total"] or 0

        if total == 0:
            return _empty_stats(total_skills, total_categories)

        success_row = conn.execute(
            f"SELECT COUNT(*) AS n FROM skill_usage "
            f"WHERE created_at >= {cutoff} "
            f"AND outcome IN ('delegated','delegated_via_mention')"
        ).fetchone()
        success = success_row["n"] or 0

        avg_row = conn.execute(
            f"SELECT AVG(match_score) AS avg_score FROM skill_usage "
            f"WHERE created_at >= {cutoff} AND match_score IS NOT NULL"
        ).fetchone()
        avg_score = float(avg_row["avg_score"] or 0.0)

        usage_rows = conn.execute(
            f"SELECT skill_id, COUNT(*) AS cnt FROM skill_usage "
            f"WHERE created_at >= {cutoff} "
            f"GROUP BY skill_id ORDER BY cnt DESC, skill_id ASC"
        ).fetchall()

        top_rows = usage_rows[:10]
        top = [{"skill_id": r["skill_id"], "count": r["cnt"]} for r in top_rows]
        by_cat: dict[str, int] = {}
        usage_counts: list[int] = []
        top_skill_id = ""
        top_skill_count = 0
        for i, r in enumerate(usage_rows):
            count = int(r["cnt"] or 0)
            usage_counts.append(count)
            cat = r["skill_id"].split("/", 1)[0] if "/" in r["skill_id"] else "other"
            by_cat[cat] = by_cat.get(cat, 0) + count
            if i == 0:
                top_skill_id = str(r["skill_id"] or "")
                top_skill_count = count

        unique_skills_used = len(usage_rows)
        if total_skills > unique_skills_used:
            usage_counts.extend([0] * (total_skills - unique_skills_used))
        gini = _gini_coefficient(usage_counts)
        coverage_rate = (unique_skills_used / total_skills) if total_skills > 0 else 0.0
        top_skill_share = (top_skill_count / total) if total > 0 else 0.0
        category_count = len(by_cat)
        if total_categories <= 0:
            total_categories = category_count

        return {
            "total": total,
            "success_rate": success / total if total else 0.0,
            "avg_score": avg_score,
            "top_skills": top,
            "by_category": by_cat,
            "diversity": {
                "unique_skills_used": unique_skills_used,
                "total_skills": total_skills,
                "coverage_rate": coverage_rate,
                "gini_coefficient": gini,
                "gini_label": _gini_label(gini),
                "top_skill_share": top_skill_share,
                "top_skill_id": top_skill_id,
                "category_count": category_count,
                "total_categories": total_categories,
            },
        }
    finally:
        conn.close()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="HELIX スキル委譲 CLI")
    p.add_argument("--mode", required=True, choices=["dispatch", "feedback", "stats"])
    p.add_argument("--skill-id")
    p.add_argument("--task")
    p.add_argument("--agent", default=None)
    p.add_argument("--references", default="", help="カンマ区切り")
    p.add_argument("--catalog-path", default=None)
    p.add_argument("--skills-root", default=None)
    p.add_argument("--db-path", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--usage-id", type=int)
    p.add_argument("--feedback")
    p.add_argument("--days", type=int, default=30)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    catalog_path = Path(args.catalog_path) if args.catalog_path else None
    skills_root = Path(args.skills_root) if args.skills_root else None
    db_path = Path(args.db_path) if args.db_path else None

    try:
        if args.mode == "dispatch":
            if not args.skill_id or not args.task:
                print("エラー: --skill-id と --task が必須", file=sys.stderr)
                return 64
            refs = [r.strip() for r in args.references.split(",") if r.strip()]
            result = dispatch(
                skill_id=args.skill_id,
                task_text=args.task,
                recommended_agent=args.agent,
                references=refs,
                catalog_path=catalog_path,
                skills_root=skills_root,
                db_path=db_path,
                dry_run=args.dry_run,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"スキル: {args.skill_id}")
                print(f"委譲先: {result['agent']['invoke']} ({result['agent']['type']}, is_claude_native={result['agent']['is_claude_native']})")
                print(f"References ({len(refs)}): {', '.join(refs) if refs else 'なし'}")
                if "context_bundle_lines" in result:
                    print(f"Context Bundle: {result['context_bundle_lines']} 行")
                print(f"Outcome: {result['outcome']}")
                if result.get("usage_id"):
                    print(f"Usage ID: {result['usage_id']}")
                if result.get("stdout"):
                    print("")
                    print(result["stdout"])
            outcome = str(result.get("outcome", ""))
            if outcome in ("delegated", "delegated_via_mention", "plan_only"):
                return 0
            return 1

        if args.mode == "feedback":
            if not args.usage_id or not args.feedback:
                print("エラー: --usage-id と --feedback が必須", file=sys.stderr)
                return 64
            record_feedback(args.usage_id, args.feedback, db_path)
            print(f"feedback recorded: usage_id={args.usage_id}")
            return 0

        if args.mode == "stats":
            result = stats(
                db_path=db_path,
                days=args.days,
                catalog_path=catalog_path,
                skills_root=skills_root,
            )
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"直近 {args.days} 日の使用統計")
                print(f"  total: {result['total']}")
                print(f"  success_rate: {result['success_rate']:.2%}")
                print(f"  avg_score: {result['avg_score']:.2f}")
                if result["top_skills"]:
                    print(f"  top skills:")
                    for s in result["top_skills"]:
                        print(f"    - {s['skill_id']}: {s['count']}")
                if result["by_category"]:
                    print(f"  by category: {result['by_category']}")
                diversity = result.get("diversity", {})
                if isinstance(diversity, dict):
                    unique_used = int(diversity.get("unique_skills_used", 0) or 0)
                    total_skill_count = int(diversity.get("total_skills", 0) or 0)
                    coverage_rate = float(diversity.get("coverage_rate", 0.0) or 0.0)
                    gini = float(diversity.get("gini_coefficient", 0.0) or 0.0)
                    gini_label = str(diversity.get("gini_label", _gini_label(gini)))
                    top_share = float(diversity.get("top_skill_share", 0.0) or 0.0)
                    top_skill_id = str(diversity.get("top_skill_id", "") or "")
                    category_count = int(diversity.get("category_count", 0) or 0)
                    total_category_count = int(diversity.get("total_categories", 0) or 0)

                    print("  diversity:")
                    print(
                        f"    unique_skills: {unique_used} / {total_skill_count} ({coverage_rate:.1%})"
                    )
                    print(f"    gini: {gini:.2f} ({gini_label})")
                    if top_skill_id:
                        print(f"    top_skill_share: {top_share:.1%} ({top_skill_id})")
                    else:
                        print(f"    top_skill_share: {top_share:.1%}")
                    print(f"    category_count: {category_count} / {total_category_count}")
            return 0

    except DispatcherError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return e.code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
