# HELIX フレームワーク完成度レビュー (2026-04-21)

**対象**: improvements/helix-overhaul ブランチ時点 (commit 13b9ba5 まで)
**評価根拠**: helix-budget-autothinking を L1-L8 フルフローで回した実地検証
**評価者**: Opus 4.7 (PM)

---

## 総合評価

**Grade: B+ (82/100)** — 基盤は完成、実運用で浮き彫りになった 7 系統の改善余地あり

| 評価軸 | 点数 | 所見 |
|-------|-----|------|
| ① フェーズ制御 | 14/15 | L1-L8 が機能、ゲートが fail-close で強制 |
| ② ゲート強制 | 11/15 | deliverable + static で 検証するが、G1 が未対応 |
| ③ 成果物駆動 | 14/15 | 16 成果物が 1:1 対応、matrix.yaml で管理 |
| ④ マルチモデル制御 | 12/15 | Codex/Claude 委譲は機能、effort/timeout 調整に余地 |
| ⑤ 自己改善ループ | 10/15 | skill_usage / retro テンプレはあるが、自動分析が薄い |
| ⑥ 日本語ファースト | 15/15 | 全ドキュメント + CLI 日本語で統一、秀逸 |
| ⑦ 開発者体験 | 6/10 | エラーメッセージ丁寧だが CLI 操作量多い |

---

## 1. フェーズ制御 (14/15)

### Good
- L1 → L8 + Phase R + Phase S が明確に分離
- phase.yaml の current_phase 自動遷移 (helix size 後)
- 駆動タイプ 5 種 (be/fe/scrum/fullstack/db/agent) の判定ロジック

### 改善余地
- G5 skip 判定が手動 (be drive + UI なしなら自動 skipped にすべき)

### 対応提案
```python
# cli/helix-gate の G5 判定ロジックに追加
if drive in ('be', 'db') and not has_ui_flag():
    phase_yaml['gates']['G5'] = {'status': 'skipped', 'note': 'auto-skipped: no UI'}
```

---

## 2. ゲート強制 (11/15)

### Good
- G2/G3/G4/G6 は deliverable + static で fail-close
- 見出しチェック (grep) で中身の最小保証
- ミニレトロ自動生成 (Try の owner/due 必須)

### 改善余地 (Critical)
- **G1 が deliverable_gate.py で未対応** → G2 の前提条件チェックで fail 扱い、phase.yaml 手動書き換えが必要
- **G1 の static チェックはあるが deliverable 側の仕組みに入っていない**

### 改善余地 (Medium)
- **D-ARCH / D-VIS-ARCH / D-ADR / ADR の命名揺れ**: gate-checks.yaml と SKILL_MAP.md で要求パスが違う
- **src/features/ 前提の G4/G6 advisory**: CLI 専用プロジェクトでは該当パスが空になる

### 対応提案
```python
# cli/lib/deliverable_gate.py に G1 を追加
GATE_CHOICES = ['G0.5', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7']
# G1: L1 deliverable (D-REQ-F / D-REQ-NF / D-ACC) の存在確認
```

```yaml
# cli/templates/gate-checks.yaml.tmpl の命名統一
# D-VIS-ARCH と D-ARCH のどちらかに正規化 (SKILL_MAP.md 側を D-ARCH に合わせる)
```

```python
# cli/helix-matrix add-feature で --cli-only フラグ追加
# CLI 専用の場合 src/features/ テンプレートは skip
```

---

## 3. 成果物駆動 (14/15)

### Good
- 16 成果物 (L1: 3 + L2: 3 + L3: 6 + L4: 3 + L6: 4 + 先行調査 + retro) が 1:1 対応
- matrix.yaml / doc-map.yaml で自動検出

### 改善余地
- **drift-check が helix.db schema 衝突を事前検知できなかった**: v6 が既に別目的で使用済みだったが、設計段階で指摘されなかった
- phase_guard.py の UNKNOWN_LAYER ハンドリングは機能したが、既存リソース衝突は未カバー

### 対応提案
```python
# cli/lib/phase_guard.py に DB schema check 追加
# L2 設計時に helix_db.py の CURRENT_SCHEMA_VERSION と D-DB の提案 version が衝突しないか検証
```

---

## 4. マルチモデル制御 (12/15)

### Good
- Codex 12 ロール + Claude 11 サブエージェント
- `helix-codex --role X` で thinking level ロール別デフォルト適用
- Phase A (サブエージェント `effort` frontmatter) 完了

### 改善余地 (Critical)
- **Codex 10 分 timeout**: L4 全スプリント (16 時間想定) を単一呼び出しで渡すと timeout 頻発
- **task 分割が手動**: 大タスクの sprint 粒度分割が PM 判断依存

### 改善余地 (High)
- helix-codex に自動分割推奨機能なし (effort=xhigh + M/L size なら分割 suggest)

### 対応提案
- 次期スプリントで auto-thinking Phase B 完成 + task splitter 統合
- helix-skill use が recommender 経由で agent 選択後、Codex ロール時は自動で effort_classifier を挟む

---

## 5. 自己改善ループ (10/15)

### Good
- `skill_usage` テーブル (v7 で effort / timeout / tokens 追加)
- retro テンプレ (`.helix/retros/*.md`) 自動生成
- Try に owner + due 必須

### 改善余地
- **自動分析が薄い**: skill_usage の集計 / 傾向分析は `helix log report` があるが、actionable な改善提案までは出さない
- **retro → debt への自動流し込み未実装**: Try 項目を手動で debt-register に登録する必要あり

### 対応提案
```bash
# 新規 CLI
helix retro close --auto-enqueue  # Try 項目を debt-register に自動登録
helix log analyze --suggest       # skill_usage から改善提案生成
```

---

## 6. 日本語ファースト (15/15)

### Good
- 全ドキュメント・CLI ヘルプ・エラーメッセージ・commit メッセージ日本語統一
- 英語混在は技術用語 (API/SQL等) のみ、可読性高い
- memory / retro / ADR も日本語で thinking 可能

### 改善余地
- なし (完成)

---

## 7. 開発者体験 (6/10)

### Good
- `helix` ディスパッチャで統一インターフェース
- ゲート失敗時のヒント表示
- smoke テストがすぐ書ける

### 改善余地 (High)
- **CLI 操作量が多い**: L1 → L8 で 20+ コマンド実行、ダッシュボード欲しい (project_helix_dashboard_idea の必要性確認)
- **bats が未インストール**: 新規テストは書けるが実行手段がない

### 改善余地 (Medium)
- **Codex 委譲時のプロンプト長が膨らむ**: 参照 memory / ドキュメント多くなりがち
- **エラーからリカバリ手順への導線**: `G1 fail → 手動書き換え` など trial&error が必要

### 対応提案
- project_helix_dashboard_idea.md の優先度を上げる (実践編 #3 候補)
- `helix init --with-bats` で bats 自動インストール
- Codex 委譲時のプロンプト自動圧縮 (context bundle 化)

---

## 総括 & 次期改善キュー

### 🔥 Priority 1 (実践編 #2 で着手)

1. **G1 を deliverable_gate.py に追加** — ゲート fail-close の一貫性
2. **D-ARCH/D-VIS-ARCH 命名揺れを統一** — gate-checks.yaml 側を正規化
3. **auto-thinking Phase B 実装** — Codex timeout 対策の本命
4. **G5 skip 自動判定** — フェーズ制御の自動化

### ⚡ Priority 2 (実践編 #3 候補)

5. **helix dashboard (動的 TUI)** — CLI 操作量削減
6. **helix-codex task splitter** — 大タスク自動分割
7. **helix retro close --auto-enqueue** — 改善サイクル自動化

### 🌱 Priority 3 (将来)

8. **drift-check の schema 衝突検知強化**
9. **pytest 統合 + bats 実行環境整備**
10. **skill_usage 自動分析 + actionable suggest**

---

## HELIX ビジョンとの対比

memory (`project_helix_vision.md`) の 6 つの差別化ポイント:

| 差別化 | 達成度 | 備考 |
|-------|-------|------|
| フェーズ制御 (L1-L8 + Phase Guard) | ✅ 93% | G1/G5 自動化余地 |
| ゲート強制 (deliverable 揃わないと進めない) | ✅ 73% | G1 対応 + 命名揺れで減点 |
| 成果物駆動 (Deliverable Matrix 1:1) | ✅ 93% | drift-check 強化余地 |
| 自己改善ループ (Learning Engine) | ⚠️ 67% | 記録はするが分析が薄い |
| マルチモデル制御 (TL/SE/PG/FE) | ⚠️ 80% | timeout 対策 + auto-thinking 未完 |
| 日本語ファースト | ✅ 100% | 完成 |

**HELIX のビジョン達成度: 84%** (実践検証で +4% の上振れ、残りは Priority 1 で対処)

---

## 結論

HELIX は「基盤は完成、実運用改善フェーズ」に入った。今回の実地検証で「設計→実装→検証→デプロイ」を一気通貫で回せたが、L1/L5 の自動化 + Codex timeout 対応 + 命名揺れの 3 点が日常運用の摩擦を生んでいる。

**次の実践編 #2 は「HELIX 自身の改善」に向け**、本レビューの Priority 1 (4 項目) を L1-L8 で回すのが自然な継続。auto-thinking Phase B は helix-budget の実装拡張として進められるため、feature ブランチも維持したまま着手可能。

---

## 参考

- 本レビュー対象セッション: 6397314f-dcf8-4237-b6c5-d8b852018e89
- 実装コミット: 13b9ba5
- L8 retro: `2026-04-21-L8-helix-budget-autothinking.md`
