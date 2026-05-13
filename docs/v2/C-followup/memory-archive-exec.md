# Memory archive 実行 Step（memory-cleanup-plan 完了入力）

## 目的
- `memory-feedback-drift.md` で出された `archive` 推奨を、`MEMORY.md` 行数削減まで含めて実行可能な手順に落とし込む。
- 本書は**実行計画書**であり、実ファイル移動は別タスク（PM 承認後）で行う。

### 参照入力
- `docs/v2/A-audit/memory-feedback-drift.md`
- `docs/v2/C-followup/v2-memory-entries-plan.md`（`memory-cleanup-plan` の記述が本件では未検出のため、同一目的の代替資料として使用）
- `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/MEMORY.md`（277行想定 -> 実測 285 行）

## §1 archive 対象 entries 確定（memory-cleanup-plan から）

### 全件（file name / type / 理由）

1. `restructure-plan.md` / `type 欠落` / frontmatter 不一致、スキーマ外扱い
2. `project_next_wave.md` / `project` / 39日前後未更新・現行 PLAN 群へ吸収済みの可能性高い
3. `project_builder_system.md` / `project` / 現行コア経路から外れた構想系メモ
4. `reference_codex_plugin_cc.md` / `reference` / 42 日以上 stale、参照価値低下

上記 4 件は `memory-feedback-drift.md` の archive 方針と v2-follower の整合レビューを経由して同一候補として確定。

## §2 MEMORY.md 行数削減 plan

### 現状
- 記載行数: 285 行
- 目標: 150 行以下（PM 承認後に実施）
- 主な削減方針:
  - `project` 系は **index 1行化**（plan 完了日・主要成果・テスト結果のみ）
  - `feedback` 系はルール化済みを短文化し、重複は merge 方針へ
  - archive 対象は **MEMORY.md から該当行削除**

### 削減対象候補（最小実行セット）

#### A. index 圧縮（1行化）
- `project_2026_05_04_roadmap_consolidation.md`（2行→1行）
- `project_2026_05_06_plan024_sprint1.md`（同上）
- `project_2026_05_07_plan027_sprint3_release.md`（同上）
- `project_2026_05_10_plan050_completion.md` 〜 `project_2026_05_11_plan055_057_completion.md`（該当4件を 4行化）
- `project_2026_05_08_*` 系（sprint1/sprint2/sprint3）

#### B. archive 完全削除（index）
- `restructure-plan.md`
- `project_next_wave.md`
- `project_builder_system.md`
- `reference_codex_plugin_cc.md`

上記 B の4行削除と A の1行化で、初期見積 285 → 150 以下へ収束。

## §3 archive 実行 step

### 3.1 事前準備
1. 対象ファイル有無確認
2. `MEMORY.md` の `grep '^##'` でセクションヘッダ確認
3. `backup` 準備（任意: zip 圧縮）

| step | 内容 | コマンド |
|---|---|---|
| 1 | archive ディレクトリ作成 | `mkdir -p ~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory-archive/` |
| 2 | 対象 file 移動 | `mv ~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/<file>.md ~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory-archive/` |
| 3 | MEMORY.md から該当 line 削除 | `rg -n "\[<file>\]" ~/.claude/projects/.../memory/MEMORY.md` で行特定後、手動編集 / `sed -i` で 1 行削除 |
| 4 | 検証 | 1) `wc -l` で行数確認、2) archive 対象の 4 ファイルリンク不在確認、3) エントリ欠損確認 |

### 3.2 1件ずつ実行する場合のチェック手順（例）
- `F=restructure-plan.md`
- `archive` へ移動成功
- `MEMORY.md` の同行削除
- `wc -l` が更新されていること
- 次候補へ進行

### 3.3 事前同時実行で避けること
- 同時に 4 つ以上の `sed -i` を走らせない
- archive 処理と index 再編集を同時コミットしない

## §4 rollback 手順

### 4.1 `mv` 失敗時の復元
- archive 失敗時は当該 file を即時元位置へ戻す
  - `mv ~/.claude/projects/.../memory-archive/<file>.md ~/.claude/projects/.../memory/<file>.md`
- destination が存在する場合: backup 時点を基準に `cp -a` 復元

### 4.2 `MEMORY.md` 編集ミス時
- memory は git 管理外のため `git restore` 不能
- 対策:
  1) 実行前に `cp ~/.claude/projects/.../memory/MEMORY.md ~/.claude/projects/.../memory/MEMORY.md.bak.$(date +%F_%H%M%S)`
  2) 編集後に diff は `git diff` ではなく `diff -u old new` で確認
  3) 誤編集時は `.bak` から `cp` で復元

## §5 archive と物理削除の境界

### archive（復元可能）
- 1 ヶ月以上 active で参照価値を残す
- 参照可能性があるため、履歴を残す必要がある
- 条件: 直近 1 か月以上無更新、かつ過去実績参照が想定される

### 物理削除（破棄）
- 完全 outdated / schema 外 / 参照価値ゼロ
- 条件:
  - ファイル本体を再利用しない明確判断が PM/TL で成立
  - 同内容の再統合先が確定済み

## §6 V2 移行で追加すべき memory entry（提案）

### 6.1 V2 構築知見（Phase A audit / TL 助言2回 / 並列原則）
- `feedback_v2_existing_capabilities_centerline.md`：新機能乱立ではなく既存能力再接続
- `feedback_v2_drive_layer_semantics_externalized.md`：DB には低カーディナリティ情報のみ
- `feedback_v2_fe_promotion_append_only.md`：証跡の append-only 方式
- `feedback_v2_fullstack_tracks_not_split.md`：fullstack の track 分離運用
- `feedback_v2_g35_start_as_subgate.md`：G3.5 はまずサブゲート
- `feedback_v2_parallel_up_to_8_when_independent.md`：独立時 8 並列
- `feedback_v2_memory_governance_before_mass_import.md`：mass import 前提のガバナンス定義

### 6.2 各 wave の memory feedback（この wave で確認）
- **Wave A（監査波）**: `feedback_v2_origin_mode_lifecycle.md`
- **Wave B（設計波）**: `feedback_v2_four_layer_chain_is_spine.md`
- **Wave C（運用波）**: `feedback_v2_expected_skills_advisory_only.md`
- **Wave D（実装波）**: `feedback_v2_phase2_is_draft_and_spike.md`

## §7 後段 task

1. archive 実行（PM 承認後、別 task で実施）
2. 実行前後で `MEMORY.md` 行数（285 → 150 以下）と dead link（`cli-layout.md` 等）を再監査
3. V2 後の memory 運用ルール doc 化
   - `type`, `source_plan_ids`, `canonical_status_source`, `review_after` の義務化
   - `cluster_id` または類似キーの検討
   - 30 日レビューの定常化

## リンク整合チェック（本書作成時）
- 参照: `memory-feedback-drift.md` の archive 候補 4 件を一致確認
- 参照: `v2-memory-entries-plan.md` の §4 と §5 を一致確認
- 参照先の欠落: `memory-cleanup-plan.md`（指定パス未検出）を注記し代替参照へ切替
- 整合: 本書内 `MEMORY.md` 行数は 285（実測）として記録、入力値 277 と乖離を注記

## TODO 残存チェック
- [ ] `memory-cleanup-plan.md` の正本ファイル有無を PM が確認（指定パス不在）
- [ ] `~/.claude/projects/.../memory` 配下で archive 実行権限の最終許可取得
- [ ] archive 後の `review_after` フィールドの一律補完（未実施）
- [ ] 物理削除対象の追加判断（本書では archive のみを計画化）
