# Runbook: helix handover (Opus ↔ Codex 引き継ぎ)

## 概要

セッション跨ぎで BE 実装を継続するためのファイル経由 handover。`.helix/handover/CURRENT.json` を正本とし、Opus / Codex 両セッションで読み書きする。`cli/helix-handover` 本体。

## 正常系の動作確認

```bash
# Opus 側で初期化
helix handover dump --task-id PLAN-NNN-S1 --task-title "..." \
  --files "path1,path2" --tests "pytest tests/..." \
  --next "1. ... 2. ... 3. ..."

# Codex 側で取り込み
helix handover status --json
helix handover update --owner codex

# 完了 / Opus 復帰
helix handover update --status ready_for_review
helix handover resume   # Opus 側
helix handover clear --reason completed
```

## よくある障害パターン

### 1. handover が stale

**症状**: `helix handover status --json` が `stale: true`、`stale_reasons` に理由表示。

**stale 判定基準**:
- 24 時間以上更新なし
- `git head_sha` が記録時と乖離
- `.helix/handover/CURRENT.md` のファイル mtime と JSON が不整合

**対応**:
- 古いセッションが残っていないか確認
- 必要なら `helix handover clear --reason abandoned --force` で破棄

### 2. ESCALATION.md が生成されている

**確認**:
```bash
ls .helix/handover/ESCALATION.md
```

存在する場合 → Codex 側が D-API / D-DB / D-CONTRACT 等の設計判断を要求している。Opus が ESCALATION.md を読んで判断 → 設計更新 → `helix handover update --status in_progress --owner opus` で再開、または `helix handover clear --reason abandoned --force` で破棄。

### 3. resume できない (ready_for_review でない)

**確認**: `helix handover status --json` で `status` を確認。`in_progress` / `ready_for_review` / `blocked` から resume 可能。それ以外 (escalated 等) は先に対処。

## エスカレーション基準

- Codex が D-API / D-DB / D-CONTRACT 変更を escalate してきた → Opus が設計確定後に再開
- handover が頻繁に stale 化する → セッション運用見直し、`helix budget status` で残量確認
