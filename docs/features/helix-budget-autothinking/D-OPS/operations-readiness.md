# D-OPS: 運用準備チェックリスト — helix-budget + auto-thinking

**Feature**: helix-budget-autothinking
**Target**: HELIX CLI 開発者 + ユーザー (本人運用)
**Date**: 2026-04-21

---

## 1. 運用手順

### 1.1 インストール

```bash
# HELIX 本体更新 (git pull 等、既存手順)
cd ~/ai-dev-kit-vscode
git pull

# DB マイグレーション (v6 → v7)
cp .helix/helix.db .helix/helix.db.backup-v6-$(date +%Y%m%d)
python3 -c "
import sys; sys.path.insert(0, 'cli/lib')
import helix_db
helix_db.init_db('.helix/helix.db')  # idempotent に v7 まで進む
"

# 動作確認
~/ai-dev-kit-vscode/cli/helix budget status
```

### 1.2 日常運用

```bash
# 毎朝の残量確認
helix budget status

# 週次予測
helix budget forecast --days 7

# 高負荷タスク投入前の簡易判定
helix budget classify --task "..." --role se --size L

# モデル選定の簡易統合シミュレーション
helix budget simulate --task "..." --role se --size M

# キャッシュクリア (強制再取得したい時)
helix budget cache clear
helix budget status --no-cache
```

### 1.3 optional セットアップ

```bash
# ccusage 導入 (推奨、より精密な消費取得)
npm install -g ccusage

# ユーザー固有ルール上書き
mkdir -p ~/.config/helix
cp cli/config/model-fallback.yaml ~/.config/helix/model-fallback.yaml
vim ~/.config/helix/model-fallback.yaml
```

---

## 2. アラート

### 2.1 警告レベル

本 feature では以下のレベルで警告:

| 条件 | レベル | 行動指針 |
|-----|-------|---------|
| 週次 80%+ | warning | 軽量タスクへ切替検討 |
| 週次 95%+ | critical | タスク保留 or モデル降格 |
| モデル 90%+ | fallback 提案 | 提案モデルで続行 or 手動切替 |
| migration 失敗 | critical | backup 復元、sqlite version 確認 |
| ccusage timeout 10s | warning | fallback 動作、ccusage 最新化 |

### 2.2 アラートチャンネル

- `helix budget status` 実行時の stdout / stderr
- session-start hook (次期スプリント実装時) の セッション開始メッセージ
- (将来) `helix log report budget` の週次サマリ
- `budget_events` テーブルへの永続記録

### 2.3 監視スクリプト例

```bash
# 残 < 20% で macOS 通知
weekly=$(helix budget status --json | jq '.claude.weekly_remaining_pct')
if [ "$weekly" -lt 20 ]; then
  osascript -e 'display notification "Claude 残 < 20%" with title "HELIX"'
fi
```

---

## 3. 復旧手順

### 3.1 DB migration 失敗

**症状**: `helix budget status` が `sqlite3.OperationalError` で失敗

**復旧**:
```bash
# 1. backup 確認
ls -lah .helix/helix.db.backup-v6-*

# 2. backup から復元
cp .helix/helix.db.backup-v6-YYYYMMDD .helix/helix.db

# 3. helix test で既存機能確認
~/ai-dev-kit-vscode/cli/helix test

# 4. 原因調査 (SQLite バージョン / 権限 / 容量)
sqlite3 --version
df -h .helix/
```

### 3.2 キャッシュ破損

**症状**: `helix budget status` の数値が明らかに異常

**復旧**:
```bash
helix budget cache clear
helix budget status --no-cache
```

### 3.3 model-fallback.yaml 破損

**症状**: `WARN [parse error]` が stderr に出る

**復旧**:
```bash
# HELIX ビルトインに戻す (ユーザー設定優先、ビルトインは常に生きる)
mv ~/.config/helix/model-fallback.yaml ~/.config/helix/model-fallback.yaml.backup
# 次回呼び出しで cli/config/model-fallback.yaml (ビルトイン) が自動採用される
```

### 3.4 ccusage 挙動異常

**症状**: JSON parse エラー or timeout 頻発

**復旧**:
```bash
# JSONL fallback に強制切替
PATH=$(echo $PATH | tr ':' '\n' | grep -v ccusage | tr '\n' ':') helix budget status
# または
npm uninstall -g ccusage  # 完全に fallback 運用
```

### 3.5 feature 全撤退

**症状**: 本 feature が HELIX 全体を破壊している場合 (想定外)

**復旧**:
```bash
# 本 feature の commit を revert
cd ~/ai-dev-kit-vscode
git log --oneline | grep helix-budget
git revert <commit-sha>

# DB は v6 に戻す (SQLite 3.35+ なら DROP COLUMN 可)
cp .helix/helix.db.backup-v6-YYYYMMDD .helix/helix.db

# テスト確認
./cli/helix test
```

---

## 4. 連絡先

- **開発者**: tenni (yoshiyuki0907yn@gmail.com)
- **Issue tracker**: HELIX 本体と同じ (GitHub issues 想定、未整備)
- **緊急連絡**: N/A (個人運用)
- **ドキュメント更新**: memory 系 (`project_helix_budget.md`) + 本ドキュメント

---

## 5. リリース前チェックリスト

L7 デプロイ前に以下を確認:

- [x] helix test 全 PASS (467/467)
- [x] G4 gate PASS
- [x] G6 gate PASS (本 G6 で検証中)
- [x] security-audit Critical/High ゼロ
- [x] security-audit Medium 指摘対応済み
- [x] `.gitignore` に `.helix/budget/` 追加済み
- [x] backup 手順確認済み (§3.1)
- [x] ドキュメント整備 (D-REQ-F / D-ACC / D-ARCH / D-ADR / D-THREAT / D-API / D-DB / D-TEST / D-PLAN / D-E2E / D-PERF / D-SECV / D-OPS)
- [ ] CLAUDE.md / SKILL_MAP.md 更新 (次期スプリント)
- [ ] memory 更新 (`project_2026_04_21_release.md` に追記)

---

## 6. ロールバック導線 (まとめ)

| 影響範囲 | 手段 | 所要 |
|---------|------|------|
| 機能のみ | git revert + cache clear | 1 分 |
| DB も戻す | git revert + backup 復元 | 3 分 |
| Sprint 粒度 | atomic commit の revert | 1 分 |
| hook のみ | `python3 cli/lib/merge_settings.py --remove` | 30 秒 |

Sprint 粒度の atomic commit は工程表 (D-PLAN §5) に明示。
