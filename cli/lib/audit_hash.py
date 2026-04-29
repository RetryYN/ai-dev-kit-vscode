"""棚卸し A1 の canonical hash 計算 (PLAN-002 v3 凍結済み仕様)。

仕様:
- algo: SHA-256
- canonical: json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
- 入力は redaction 適用 **後** の素値 (本 module は redaction しない)
"""
import hashlib
import json

DECISION_HASH_FIELDS = (
    "candidate_id",
    "schema_version",
    "scope_hash",
    "decision",
    "evidence",
    "rationale",
    "fail_safe_action",
)


def canonical_json(obj) -> str:
    """canonical JSON 文字列を返す (UTF-8 byte 列に encode 可能な形)。"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_of(text: str) -> str:
    """UTF-8 byte 列の SHA-256 hex 文字列。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_decision_hash(decision: dict) -> str:
    """1 decision エントリの decision_hash。

    対象 fields は DECISION_HASH_FIELDS のみ。
    その他 (status, import_run_id, created_at 等) は対象外。
    """
    filtered = {k: decision[k] for k in DECISION_HASH_FIELDS if k in decision}
    return sha256_of(canonical_json(filtered))


def compute_source_hash(yaml_text: str) -> str:
    """decisions.yaml 全体の source_hash (redaction 適用後の text)。"""
    return sha256_of(yaml_text)
