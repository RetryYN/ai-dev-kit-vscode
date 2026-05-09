build_review_prompt() {
  local plan_id="$1"
  local title="$2"
  local source_file="$3"
  local prompt=""

  if [[ -n "$source_file" && "$source_file" != "null" ]]; then
    local source_path="$source_file"
    if [[ "$source_path" != /* ]]; then
      source_path="$PROJECT_ROOT/$source_path"
    fi
    if [[ -f "$source_path" ]]; then
      local source_preview
      source_preview="$(python3 - <<'PY' "$source_path"
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="replace")
limit = 24000
print(text[:limit])
PY
)"
      prompt=$(cat <<EOF
設計提案レビューを実施せよ。出力は review-output.schema.json 準拠の JSON のみとする。

対象プラン:
- id: $plan_id
- title: $title
- source_file: $source_file

【PLAN レビューの位置づけ】
本レビューは PLAN レベル (実装計画の方向性凍結) を対象とする。Schema/API Freeze (G3) や Implementation Freeze (G4) ではない。
G3/G4 は別途 helix-gate G3/G4 で評価される。PLAN レビューでは「この計画の方向性で実装着手して良いか」を判定する。

評価観点:
- 技術妥当性 (採用技術・アーキテクチャ方針が妥当か)
- リスク特定 (API/DB/認証/外部API/移行/セキュリティの主要リスクが洗い出されているか)
- 実装可能性 (致命的な実現不可項目や前提崩壊がないか)
- スコープ整合 (PLAN タイトル・目的とスコープが一致しているか)

【判定基準】
- approve: 以下を全て満たす場合
  - 構造的矛盾・前提崩壊・スコープ越境・致命的セキュリティ欠陥がない (= P0 ゼロ)
  - 主要な技術判断とリスクが特定されている
  - 計画の方向性で実装着手して良い
- needs-attention: 以下のいずれかを満たす場合のみ
  - 構造的矛盾 (本文内の記述が互いに両立しない、後段成果物の前提を満たせない)
  - 計画の前提崩壊 (依存する事実が誤っている、未確定事項が中核に残っている)
  - スコープ越境 (PLAN タイトル・目的と実体が一致しない)
  - 致命的セキュリティ欠陥 (秘匿情報漏洩経路、認証バイパスなど)

【findings の severity 区分】
- high (P1): approve を阻害する構造的問題。P1 ありなら needs-attention。
- medium (P2): G3/G4 までに解決すべき重要事項。P2 のみなら approve 可 (P0/P1 ゼロが前提)。
- low (P3): G3/G4 までに解決すべき推奨事項。
- info: 軽微な改善提案。

【重要】DDL CHECK 制約の細部、canonical input の bit-level 仕様、transaction 境界の詳細、
file mode の具体値、fixture の網羅、preflight 順序の細部などは「G3 Schema Freeze で凍結すべき詳細」に該当する。
これらは PLAN レビューでは P2/P3 として扱い、approve の阻害要因にしない。
ただし、これらが「本文内で互いに矛盾している」「PLAN として方向性が立たない」場合は P1 とする。

返却要件:
- JSON オブジェクトのみ
- verdict は approve または needs-attention
- findings は file/line_start/line_end/confidence/recommendation を含める
- summary に「P0/P1/P2/P3 の件数」と「approve 判定の根拠 or 阻害要因」を明記

設計案本文:
$source_preview
EOF
)
    else
      prompt=$(cat <<EOF
設計提案レビューを実施せよ。出力は review-output.schema.json 準拠の JSON のみとする。

対象プラン:
- id: $plan_id
- title: $title
- source_file: $source_file (ファイル未検出のためタイトルベースで判断)

【PLAN レビューの位置づけ】
本レビューは PLAN レベル (実装計画の方向性凍結) を対象とする。Schema/API Freeze (G3) ではない。

評価観点:
- 技術妥当性
- リスク（API/DB/認証/外部API/移行/セキュリティ）
- 実装可能性と欠落事項

【判定基準】
- approve: 構造的矛盾・前提崩壊・スコープ越境・致命的セキュリティ欠陥がなく (P0 ゼロ)、主要な技術判断が特定されている。
- needs-attention: 上記いずれかが該当する場合のみ。詳細仕様の未凍結 (G3 で扱う事項) は P2/P3 として approve を阻害しない。

返却要件:
- JSON オブジェクトのみ
- verdict は approve または needs-attention
- findings は file/line_start/line_end/confidence/recommendation を含める
- summary に「P0/P1/P2/P3 の件数」と「approve 判定の根拠 or 阻害要因」を明記
EOF
)
    fi
  else
    prompt=$(cat <<EOF
設計提案レビューを実施せよ。出力は review-output.schema.json 準拠の JSON のみとする。

対象プラン:
- id: $plan_id
- title: $title

【PLAN レビューの位置づけ】
本レビューは PLAN レベル (実装計画の方向性凍結) を対象とする。Schema/API Freeze (G3) ではない。

評価観点:
- 技術妥当性
- リスク（API/DB/認証/外部API/移行/セキュリティ）
- 実装可能性と欠落事項

【判定基準】
- approve: 構造的矛盾・前提崩壊・スコープ越境・致命的セキュリティ欠陥がなく (P0 ゼロ)、主要な技術判断が特定されている。
- needs-attention: 上記いずれかが該当する場合のみ。詳細仕様の未凍結 (G3 で扱う事項) は P2/P3 として approve を阻害しない。

返却要件:
- JSON オブジェクトのみ
- verdict は approve または needs-attention
- findings は file/line_start/line_end/confidence/recommendation を含める
- summary に「P0/P1/P2/P3 の件数」と「approve 判定の根拠 or 阻害要因」を明記
EOF
)
  fi

  printf "%s" "$prompt"
}

extract_and_validate_review_json() {
  local raw_output_file="$1"
  local out_json_file="$2"
  python3 - <<'PY' "$raw_output_file" "$out_json_file" "$REVIEW_SCHEMA" "$SCRIPT_DIR/lib"
import json
import sys
from pathlib import Path

raw_file = Path(sys.argv[1])
out_file = Path(sys.argv[2])
schema_file = Path(sys.argv[3])
lib_dir = Path(sys.argv[4])
sys.path.insert(0, str(lib_dir))

import review_output

try:
    valid = review_output.extract_normalized_review_json(
        raw_file.read_text(encoding="utf-8", errors="replace"),
        review_output.load_schema(schema_file),
    )
except review_output.ReviewOutputError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(1)

out_file.parent.mkdir(parents=True, exist_ok=True)
out_file.write_text(json.dumps(valid, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(valid.get("verdict", ""))
PY
}

record_plan_review_scores() {
  local plan_id="$1"
  local review_file="$2"
  python3 - <<'PY' "$SCRIPT_DIR/lib" "$HELIX_DIR/helix.db" "$plan_id" "$review_file" || true
import json
import sys
from pathlib import Path

lib_dir = Path(sys.argv[1])
db_path = Path(sys.argv[2])
plan_id = sys.argv[3]
review_file = Path(sys.argv[4])
sys.path.insert(0, str(lib_dir))

import helix_db

payload = json.loads(review_file.read_text(encoding="utf-8"))
evidence = f"source=helix-plan review\nreview_file={review_file}"
reviewer = "codex-review:tl"
conn = helix_db._connect(str(db_path))
try:
    helix_db._ensure_schema(conn)
    conn.execute(
        "DELETE FROM accuracy_score WHERE plan_id = ? AND gate = ? AND reviewer = ?",
        (plan_id, "PLAN_REVIEW", reviewer),
    )
    conn.commit()
finally:
    conn.close()

for score in payload.get("overall_scores", []):
    helix_db.record_accuracy_score(
        str(db_path),
        plan_id=plan_id,
        gate="PLAN_REVIEW",
        dimension=score["dimension"],
        level=score["level"],
        comment=score.get("comment", ""),
        evidence=evidence,
        reviewer=reviewer,
    )
PY
}

cmd_review() {
  local plan_id=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --id)
        plan_id="$2"
        shift 2
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

  if [[ -z "$plan_id" ]]; then
    echo "エラー: --id は必須です" >&2
    exit 1
  fi
  validate_plan_id "$plan_id"
  ensure_plan_exists "$plan_id"
  ensure_dirs

  local plan_file
  plan_file="$(plan_file_path "$plan_id")"

  local current_status
  current_status="$(yaml_read "$plan_file" "status")"
  if [[ "$current_status" != "draft" && "$current_status" != "reviewed" && "$current_status" != "rejected" ]]; then
    echo "エラー: review 可能な status は draft/reviewed/rejected のみです (現在: $current_status)" >&2
    exit 1
  fi

  local title source_file review_prompt
  title="$(yaml_read "$plan_file" "title")"
  source_file="$(yaml_read "$plan_file" "source_file")"
  review_prompt="$(build_review_prompt "$plan_id" "$title" "$source_file")"

  local raw_output_file review_output
  raw_output_file="$(mktemp /tmp/helix-plan-review-XXXXXX.log)"
  trap 'rm -f "$raw_output_file"' RETURN

  echo "[helix-plan] PM → TL レビュー委譲（Codex 5.4）"

  set +e
  review_output=$("$HELIX_CODEX" --role tl --task "$review_prompt" 2>&1)
  local cmd_exit=$?
  set -e
  printf "%s\n" "$review_output" > "$raw_output_file"

  if [[ $cmd_exit -ne 0 ]]; then
    echo "エラー: TL review の実行に失敗しました (exit=$cmd_exit)" >&2
    tail -n 20 "$raw_output_file" >&2
    exit $cmd_exit
  fi

  local review_file review_rel verdict reviewed_at
  review_file="$REVIEW_DIR/$plan_id.json"
  review_rel=".helix/reviews/plans/$plan_id.json"
  verdict="$(extract_and_validate_review_json "$raw_output_file" "$review_file")"
  record_plan_review_scores "$plan_id" "$review_file"
  reviewed_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  yaml_write "$plan_file" "review.status" "$verdict"
  yaml_write "$plan_file" "review.reviewed_at" "$reviewed_at"
  yaml_write "$plan_file" "review.review_file" "$review_rel"

  if [[ "$verdict" == "approve" ]]; then
    yaml_write "$plan_file" "status" "reviewed"
  else
    yaml_write "$plan_file" "status" "rejected"
  fi

  echo "レビュー完了: $plan_id ($verdict)"
  echo "保存: ${review_file#$PROJECT_ROOT/}"
}
