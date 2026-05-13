# FR-INV19: PM memory feedback drift 監査

最終更新: 2026-05-14  
監査者: Research (Codex)  
不確実性:
- memory 配下は Git 管理外のため、`last updated` は `git log` ではなく mtime を採用した
- `PLAN` の `status=finalized` は「完了前」か「文書凍結済み」のどちらかが運用で揺れている可能性があるため、本文では `drift 候補` として扱う
- 秘密情報検査は pattern scan ベースで、文脈判定まではしていない

## 概要

- 対象: `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/`
- 対象件数: 86 entry (`feedback` 26, `project` 56, `reference` 2, `type 欠落` 2)
- index: `MEMORY.md` 277 行、83 entry 掲載、200 行制限を 77 行超過
- 主要問題:
  - `MEMORY.md` が肥大化し、未掲載 4 件・死リンク 1 件を含む
  - `PLAN-024` 系などで memory の「完了/完遂」と plan registry の `draft` / `finalized` が乖離
  - `type` frontmatter 欠落 2 件
  - 30 日以上未更新の古い memory 7 件
  - feedback の近接重複があり、同一イベントの別メモ化で探索コストが高い

## 選択肢

| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| 現状維持 | 作業コストが最小 | drift と探索コストが増え続ける | 低 |
| index のみ整理 | 200 行制限、死リンク、未掲載を即解消できる | entry 本体の drift / type 欠落は残る | 中 |
| index + entry 正規化 | 探索性、更新性、V2 移行入力をまとめて改善できる | 1 回の棚卸しコストは高い | 高 |

## 推奨

- 推奨は `index + entry 正規化`。
- V2 では `feedback` を「運用ルール」、`project` を「状態スナップショット」、`reference` を「外部知識」に用途固定し、`MEMORY.md` は最新 30 件前後の index に縮退するのが妥当。
- `finalized` 止まりの PLAN completion memory は、plan registry 側の完了運用を先に決めてから一括で `update` か `archive` を判断すべき。

## 監査結果

### 1. 件数 / type 別件数

| type | 件数 |
|---|---:|
| `feedback` | 26 |
| `project` | 56 |
| `reference` | 2 |
| `type 欠落` | 2 |
| **合計** | **86** |

type 欠落:
- `project_2026_05_14_v2_sprint_transformation.md`
- `restructure-plan.md`

### 2. `MEMORY.md` (index) 整合性

| 項目 | 結果 |
|---|---|
| 行数 | 277 |
| 200 行制限 | 超過 |
| index 掲載件数 | 83 |
| 重複 entry | 0 |
| 死リンク | 1 (`cli-layout.md`) |
| 未掲載 | 4 |

未掲載:
- `project_2026_05_11_post_055_057_plan.md`
- `project_helix_vision.md`
- `project_next_wave.md`
- `restructure-plan.md`

補足:
- `cli-layout.md` は memory entry ではなく repo doc への素リンクで、現行 index の entry 一貫性を壊している
- 未掲載 4 件のうち 3 件は古い基礎メモ、1 件は 2026-05-11 の次作業計画で、index の鮮度ルールが曖昧

### 3. drift 検出

`memory` 側で完了/完遂/ release を主張しているのに、plan registry で `draft` / `finalized` / 未登録だったものを drift 候補とした。

| memory file | type | last updated | 問題 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|
| `project_2026_05_06_plan022_023_release.md` | project | 2026-05-06 | `PLAN-022` が plan registry で未検出 | update | memory と plan 正本のリンクが切れている |
| `project_2026_05_06_plan024_sprint1.md` | project | 2026-05-07 | `PLAN-024` 完了扱いだが `draft` | update | status 正本と矛盾 |
| `project_2026_05_07_plan027_sprint3_release.md` | project | 2026-05-07 | `PLAN-024` / `PLAN-027` が `draft` | update | completion memory と整合しない |
| `project_2026_05_08_plan024_sprint2_release.md` | project | 2026-05-08 | `PLAN-024` が `draft` | update | 同上 |
| `project_2026_05_08_plan024_sprint3_release.md` | project | 2026-05-08 | `PLAN-024` が `draft` | update | 同上 |
| `project_2026_05_08_overnight_completion.md` | project | 2026-05-08 | `PLAN-029` 完遂扱いだが `finalized` | update | completion と finalized の意味が不一致 |
| `project_2026_05_09_plan030_completion.md` | project | 2026-05-09 | `PLAN-029` / `PLAN-030` が `finalized` | update | 同上 |
| `project_2026_05_09_plan031_completion.md` | project | 2026-05-09 | `PLAN-030` が `finalized` | update | 同上 |
| `project_2026_05_10_plan041_completion.md` | project | 2026-05-10 | `PLAN-001` / `PLAN-024` が `draft` | update | 古い draft plan 参照が残存 |
| `project_2026_05_11_plan053_054_completion.md` | project | 2026-05-11 | `PLAN-053` / `PLAN-054` が `finalized` | keep/update | 直近だが status ルール未統一 |
| `project_2026_05_11_plan055_057_completion.md` | project | 2026-05-11 | `PLAN-055` が `finalized` | keep/update | 同上 |
| `project_2026_05_11_post_055_057_plan.md` | project | 2026-05-11 | `PLAN-055` が `finalized` | keep/update | 次アクションメモが完了 plan を前提にしている |

所見:
- 大半は「memory が誤り」というより、「plan registry の `completed` と `finalized` の使い分けが崩れている」可能性が高い
- V2 では `plan status` の正本に合わせて project memory を自動更新するか、project memory で status を持たない方が安全

### 4. 古い memory

1 か月以上未更新:

| memory file | type | last updated | 問題 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|
| `restructure-plan.md` | type 欠落 | 2026-03-07 | 67 日未更新、index 未掲載 | archive | C→B-lite 再編メモで現行運用から遠い |
| `reference_codex_plugin_cc.md` | reference | 2026-04-01 | 42 日未更新 | archive | plugin 参照メモとして stale |
| `project_helix_v2_deliverable_matrix.md` | project | 2026-04-01 | 42 日未更新 | merge | V2 audit/doc 側へ昇格済みの可能性が高い |
| `project_builder_system.md` | project | 2026-04-02 | 41 日未更新 | archive | 構想メモで現行 core route から外れている |
| `feedback_japanese_first.md` | feedback | 2026-04-03 | 40 日未更新 | keep | ルール自体は still relevant |
| `project_helix_vision.md` | project | 2026-04-04 | 39 日未更新、index 未掲載 | merge | vision は V2 concept 側へ統合すべき |
| `project_next_wave.md` | project | 2026-04-04 | 39 日未更新、index 未掲載 | archive | 待ち行列メモとして古く、現在の PLAN 群へ分解済み |

### 5. 重複 memory / 近接重複

完全重複は見当たらないが、同一イベント由来の近接重複はある。

| memory file | type | last updated | 問題 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|
| `feedback_codex_apply_patch_unreliable.md` | feedback | 2026-05-03 | `PLAN-012` 起点の別 feedback と近接重複 | merge | 「Codex 不信」系の共通原則へまとめられる |
| `feedback_parallel_dispatch_default.md` | feedback | 2026-05-03 | `PLAN-012` 起点の別 feedback と近接重複 | merge | 並列実行原則は独立させるか統合ルール化が必要 |
| `feedback_codex_role_name_cli_vs_memory.md` | feedback | 2026-05-09 | `PLAN-033` 由来で role 運用の別メモと近接 | merge | role 関連 feedback が分散している |
| `feedback_github_minimal_footprint.md` | feedback | 2026-05-10 | `PLAN-033` 由来だが scope は別 | keep | 内容は独立しているが source event は同じ |
| `feedback_no_plan_external_spec_change.md` | feedback | 2026-05-03 | `PLAN-014` 由来の運用ルール | keep | 独立性あり |
| `feedback_thinking_level_for_small_fix.md` | feedback | 2026-05-03 | `PLAN-014` 由来の role 運用 | keep | 独立性あり |

所見:
- 問題は重複そのものより、「同一イベントから複数の feedback を切る基準」が未定義なこと
- V2 では `feedback cluster_id` か `source_plan_ids` を frontmatter に持たせると検索性が上がる

### 6. 未昇格 / type 不整合

| memory file | type | last updated | 問題 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|
| `project_2026_05_14_v2_sprint_transformation.md` | type 欠落 | 2026-05-14 | frontmatter は `metadata.type=project` だが top-level `type` 欠落 | update | 現行集計系が拾えない |
| `restructure-plan.md` | type 欠落 | 2026-03-07 | frontmatter 自体がなく分類不能 | archive | 現行 memory schema 外 |
| `project_helix_vision.md` | project | 2026-04-04 | vision/原則メモで `reference` 寄り | merge | V2 concept へ昇格した方が自然 |
| `project_next_wave.md` | project | 2026-04-04 | 待ち行列メモで `project` より backlog/reference 寄り | archive | 現行 PLAN へ分解済みの可能性が高い |

### 7. 依存切れ

| memory file | type | last updated | 問題 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|
| `project_2026_05_11_plan050_completion.md` | project | 2026-05-11 | `[[ rc==0 ]]` を wiki link と誤認識 | update | コード片が link parser と衝突 |

index 側の死リンク:

| memory file | type | last updated | 問題 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|
| `MEMORY.md` | index | 2026-05-14 読取時 | `cli-layout.md` への死リンク | update | memory entry 参照規約から外れている |

### 8. 秘密情報含有

- 高確度の credential / token / API key は未検出
- ただし `project_2026_05_09_plan032_completion.md` に `user@example.com` / `password123` 等のサンプル認証情報が含まれる

判定:

| memory file | type | last updated | 問題 | V2 変更計画 | 理由 |
|---|---|---|---|---|---|
| `project_2026_05_09_plan032_completion.md` | project | 2026-05-09 | サンプル認証値を含むため除外推奨候補 | update | 実 credential ではない可能性が高いが、memory には不要 |

補足:
- 内容は example/test data に見えるため即 `delete` 断定はしない
- V2 では「認証値・メール形式・個人情報形式は memory に複写しない」を明文化すべき

## archive 推奨一覧

- `restructure-plan.md`
- `project_next_wave.md`
- `project_builder_system.md`
- `reference_codex_plugin_cc.md`

## V2 で新規追加すべき memory

- V2 memory schema ルール
  - `type`, `source_plan_ids`, `cluster_id`, `canonical_status_source`, `review_after`
- TL 助言の昇格メモ
  - `tl_advice_v2_sprint_transformation`
  - `tl_advice_memory_governance`
- Phase A 結論メモ
  - `v2_phase_a_decisions`
- drift 監査メモ
  - `memory_governance_findings_2026_05`

## V2 後の memory 運用ルール案

1. `MEMORY.md` は最新 30 件前後の index に縮め、全件台帳は別ファイルへ分離する
2. 全 entry に top-level frontmatter `name`, `description`, `type`, `originSessionId` を必須化する
3. `project` は status を直接持たず、`canonical_status_source` で `plan_id` や doc 正本を参照する
4. 同一イベントから複数 feedback を作る場合は `cluster_id` を共有する
5. 30 日以上未更新の entry には `review_after` を入れ、棚卸し時に `keep/update/archive/delete` を強制判定する
6. wiki link は entry 名だけに限定し、コード片で `[[...]]` を使わない
7. credential / PII / テスト認証値は memory に複写しない。必要なら「除外推奨」とだけ記録する

## ソース

- `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/MEMORY.md`
- `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/*.md`
- `docs/plans/PLAN-*.md`
- `.helix/plans/PLAN-*.yaml`
- `helix plan status --id PLAN-024`
- `helix plan status --id PLAN-029`
- `helix plan status --id PLAN-053`
- `helix plan status --id PLAN-055`
- `helix plan status --id PLAN-060`
- `rg`, `find`, `wc -l`, `python3` による frontmatter / link / plan ref / stale 集計
