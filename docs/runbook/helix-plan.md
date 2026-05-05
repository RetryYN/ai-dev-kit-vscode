# Runbook: helix plan (lifecycle)

## 概要

PLAN.yaml の draft / review / finalize ライフサイクル管理。`cli/helix-plan` 本体、schema は `cli/lib/plan_schema.py`。

## 正常系の動作確認

```bash
helix plan draft --plan-id PLAN-NNN --title "..."
# → .helix/plans/PLAN-NNN.yaml + docs/features/PLAN-NNN/{D-API,D-DB,D-ARCH,D-TEST,D-THREAT}/README.md skeleton
helix plan review --id PLAN-NNN
helix plan finalize --id PLAN-NNN
```

## よくある障害パターン

### 1. draft が D-shard skeleton を生成しない

**確認**: `cli/lib/plan_schema.py` の `DESIGN_SHARD_DIRS` と `cli/helix-plan` の skeleton ループが一致しているか。乖離していると一部 shard が抜ける。

### 2. G2 で `insufficient_g2_design_evidence` で fail

**確認**: 対象 PLAN が新 schema (references / artifacts フィールドあり) なら、references 3 件以上 OR docs/features/<plan-id>/D-* 3 件以上が必須。

```bash
python3 cli/lib/plan_schema.py g2-check --project-root .
```

legacy PLAN (PLAN-001〜020 等、references フィールドを持たない) は G2 新規制約の対象外。

### 3. draft で plan id 衝突

**症状**: `--plan-id PLAN-001` 等で既存 ID を指定すると上書きしない。

**対応**: `helix plan list` で既存 ID を確認、新規 ID を指定。

## エスカレーション基準

- schema 互換破壊 (legacy PLAN を強制的に新 schema に移行) → Opus 判断
- G2 静的チェック内容の変更 → TL モード Codex 相談
