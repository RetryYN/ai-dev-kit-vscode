# HELIX フレームワーク完成度レビュー v2 (2026-04-21 強化後)

**対象**: improvements/helix-overhaul @ 4cbd5fb
**前回評価**: Grade B+ (82/100) @ 13b9ba5
**強化施策**: P1-1~4 の 4 件
**本次評価**: Grade A- (91/100)

---

## 再評価サマリ

| 評価軸 | v1 | v2 | 変化 | 備考 |
|-------|----|----|----|------|
| ① フェーズ制御 | 14/15 | **15/15** | +1 | G5 auto-skip 実装 |
| ② ゲート強制 | 11/15 | **14/15** | +3 | G1 対応 + 命名整理 |
| ③ 成果物駆動 | 14/15 | 14/15 | 0 | drift-check 改善余地残る |
| ④ マルチモデル制御 | 12/15 | **14/15** | +2 | auto-thinking Phase B 完了 |
| ⑤ 自己改善ループ | 10/15 | 10/15 | 0 | Priority 2 で扱う |
| ⑥ 日本語ファースト | 15/15 | 15/15 | 0 | 維持 |
| ⑦ 開発者体験 | 6/10 | **9/10** | +3 | --auto-thinking で CLI 操作軽減 |

**合計**: 82 → **91** (Grade A-)

---

## 解消された findings

### ✅ 1. G1 が deliverable_gate.py で未対応
**v2 対応**: `cli/lib/deliverable_gate.py` の `GATE_LAYERS` に G1 を追加
- G1 の deliverable 検証 (L1 成果物: D-REQ-F / D-REQ-NF / D-ACC) が fail-close で機能
- phase.yaml の手動書き換えが不要
- 検証: `helix gate G1 --static-only` → `deliverable: 3/3 done -> PASS`

### ✅ 2. D-ARCH / D-VIS-ARCH 命名揺れ (実態は駆動タイプ別の正規配置)
**v2 対応**:
- `cli/templates/rules/structure.yaml` に使い分けコメント追加
  - D-ARCH: be/db/agent 駆動 (一般アーキ)
  - D-VIS-ARCH: fe/fullstack 駆動 (visual アーキ)
  - D-DATA-ARCH: db 駆動
  - D-ORCH-ARCH: agent 駆動
- helix-budget-autothinking の重複ディレクトリ (D-VIS-ARCH/, ADR/) 削除
- エージェントの誤配置を防ぐ指針明記

### ✅ 3. G5 skip 手動判定
**v2 対応**: `cli/helix-gate` に auto-skipped ロジック
- drive=be or db かつ sprint.ui != true なら G5 を自動 skipped
- phase.yaml 手動書き換え不要、G6 に進める
- 既存の "G5 ui=false skip" テストも含めて 473/473 PASS

### ✅ 4. Codex timeout 対策 (auto-thinking Phase B)
**v2 対応**: `cli/lib/effort_classifier.py` に LLM 境界値判定
- ルールベース score が境界値 (3/4/7/8/12/13) なら gpt-5.4-mini 呼び出し
- 保守的採用 (max(rule, LLM))
- SHA256 ベース 1h キャッシュで API コスト削減
- `helix-codex --auto-thinking` / `helix-skill use --auto-thinking` 統合
- HELIX_SKILL_AUTO_THINKING 環境変数で dispatcher 経路も自動伝播

---

## 残存 findings (v2 以降)

### ⚠️ Medium (Priority 2)

#### 3-1. drift-check の DB schema 衝突検知
- `CURRENT_SCHEMA_VERSION` 既存値と設計の提案値を事前比較する仕組みがない
- 対策: L2 設計時に phase_guard.py で schema version チェック

#### 7-1. bats 実行環境未整備
- bats ファイルは作成したが WSL2 に未インストール
- 対策: `helix init --with-bats` で npm install -g bats-core 自動化

#### 5-1. 自己改善ループの自動分析
- skill_usage に記録されるが、actionable な提案までは出さない
- retro の Try → debt-register 自動流し込みが未実装
- 対策: `helix retro close --auto-enqueue` / `helix log analyze --suggest`

### 🌱 Low (Priority 3)

- ダッシュボード (project_helix_dashboard_idea)
- ccusage 精密 JSON parse
- state.db 実スキーマ調査
- pytest 統合

---

## 強化の効果測定

### 定量

| 指標 | v1 | v2 | 変化 |
|-----|----|----|----|
| helix test 件数 | 467 | **473** | +6 新規テスト |
| 既存テスト破壊 | 0 | 0 | 非破壊継続 |
| 新規コード | +700 行 | +210 行 | +200 行で大きな効果 |
| ゲート手動介入 | G1/G5 で発生 | **なし** | phase.yaml 手動書き換え不要 |

### 定性

- **Developer Experience**: auto-thinking により `helix-codex --role se --task ... --auto-thinking` だけで適切な thinking 自動設定
- **Gate 信頼性**: G1 が deliverable レイヤで fail-close、強制力が一貫
- **Schema 進化耐性**: helix.db v6→v7 の成功事例で次回以降安全
- **複数モデル制御**: HELIX_SKILL_AUTO_THINKING で dispatcher 経路も自動化、誤操作リスク減

---

## ビジョン対比 (v2)

| 差別化 | v1 | v2 | 達成度 |
|-------|----|----|-------|
| フェーズ制御 | 93% | **100%** | +7 完成 |
| ゲート強制 | 73% | **93%** | +20 大幅改善 |
| 成果物駆動 | 93% | 93% | 維持 |
| 自己改善ループ | 67% | 67% | Priority 2 で対応 |
| マルチモデル制御 | 80% | **93%** | +13 Phase B 完成 |
| 日本語ファースト | 100% | 100% | 維持 |

**HELIX ビジョン達成度**: 84% → **91%** (+7)

---

## 次期改善キュー (Priority 2 / 実践編 #3 候補)

1. **helix dashboard (動的 TUI)** — 開発者体験の残り 1/10 を埋める
2. **drift-check の schema 衝突検知** — L2 → L4 で事前検知
3. **retro auto-enqueue** — 自己改善ループ 67 → 85% 狙い
4. **bats 実行環境** — smoke テスト一本化

---

## 結論

HELIX は **Grade A- (91/100)** に到達。主要な摩擦 4 件を解消し、日常運用でゲート手動介入がなくなった。次の改善ターゲットは「自己改善ループの自動分析」と「動的 UI」の 2 軸。

- ビジョン達成度 91% — 基盤 + 運用の両輪が揃った
- 残る 9% は「観測 → 学習 → 提案」の自動化 (Priority 2)
- Grade A (95+) を目指すなら Priority 2 の完遂が条件

---

## 参考

- 前回レビュー: `.helix/retros/2026-04-21-helix-maturity-review.md` (local only)
- 強化コミット: 4cbd5fb
- 強化施策の適用対象: improvements/helix-overhaul
