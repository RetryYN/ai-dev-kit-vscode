# V2 移行知見の memory entries 起草計画

最終更新: 2026-05-14  
作成: Research (Codex)  
用途:

1. V2 構築セッションで得た知見を `memory feedback / project entry` 候補として棚卸しする
2. 既存 `MEMORY.md` と重複しない新規 entry の起票対象を整理する
3. Opus PM が実際の memory file 起票可否を判断するための入力正本にする

不確実性:

- `MEMORY.md` は TASK_INPUT 記載の 277 行ではなく、2026-05-14 時点の実測で 279 行だった
- TL 助言ログは複数あるが、本計画では V2 設計判断に直接効く 2026-05-14 の TL advice を主根拠にした
- 本書は起票計画であり、実際の memory file 作成・更新・archive 実行は含まない

---

## §1 V2 構築で得られた知見 (memory entry 候補)

下表は、V2 構築セッションで新規に memory 化する価値が高い候補を列挙したもの。  
命名は暫定であり、最終的な file 名は PM 側で微修正してよい。

| memory file name | type | description | body skeleton | 出典 |
|---|---|---|---|---|
| `feedback_v2_existing_capabilities_centerline.md` | feedback | V2 は新機能乱立ではなく、既存能力を中心線へ再接続する改革で進める | rule: 再実装より再接続を優先 / Why: capability 不足より接続不足が主因 / How to apply: 新要件は既存 capability inventory と capability matrix を先に照合 | `audit-summary.md` DR-002 |
| `feedback_v2_drive_layer_semantics_externalized.md` | feedback | drive × layer の意味論は DB enum に焼かず YAML 外部化する | rule: DB は低カーディナリティ軸のみ保持 / Why: drive 追加や意味変更を migration 化しないため / How to apply: semantic は `vmodel-semantics.yaml` 側で定義し DB は `drive` 列だけ持つ | TL log `20260514-005424-tl-advisor.log`, `L1-REQUIREMENTS.md` FR-V02 |
| `feedback_v2_fe_promotion_append_only.md` | feedback | FE mock promotion は row 更新ではなく append-only lifecycle で追跡する | rule: mock 証跡を上書きしない / Why: G2 evidence 保全と起源監査のため / How to apply: mock_frozen と promoted を別 record で保持し lineage を残す | TL log `20260514-005424-tl-advisor.log`, `L1-REQUIREMENTS.md` FR-VD04 |
| `feedback_v2_fullstack_tracks_not_split.md` | feedback | fullstack は track 並列管理で扱い、BE/FE を別 PLAN に分断しない | rule: `drive=fullstack` は案件種別、`track` は作業線 / Why: contract と state-events の同期点を壊さないため / How to apply: 同一 sprint_id 内で `be|fe|contract|shared` を並列管理する | `L1-REQUIREMENTS.md` §3.8, `CONCEPT.md` |
| `feedback_v2_g35_start_as_subgate.md` | feedback | G3.5 は即 public gate 化せず、まず G3 サブゲート `functional_freeze` から始める | rule: 破壊的 gate 追加は段階導入 / Why: 既存 CLI / docs / Reverse / Scrum 影響が大きいため / How to apply: `helix gate G3 --subgate functional_freeze` で運用実績をためる | `L1-REQUIREMENTS.md` §3.8 |
| `feedback_v2_bulk_fill_after_schema_spine_freeze.md` | feedback | PE bulk fill-in は schema spine 凍結後に限定する | rule: spine 未凍結で量産実装しない / Why: 下流の大量差し戻しを防ぐため / How to apply: `drive/layer/origin_mode/chain` の設計が固まるまで bulk 実装を抑制する | TL log `20260514-005424-tl-advisor.log`, `audit-summary.md` DR-001 |
| `feedback_v2_expected_skills_advisory_only.md` | feedback | `expected_skills` は advisory であり fail-close 化しない | rule: skill 推挙は補助、正本は phase/role/gate / Why: 推挙ミスで作業停止にすると運用硬直化するため / How to apply: skill 未一致は warning に留め、gate 条件とは分離する | `accumulated-knowledge.md` skill 推挙節, `HELIX_CORE.md` |
| `feedback_v2_phase2_is_draft_and_spike.md` | feedback | Phase 2 は draft / design spike として扱い、L2 起票は G1 通過後に行う | rule: 監査知見の固定前に設計正本を量産しない / Why: future state の premature freeze を避けるため / How to apply: Phase A 監査 → G1R/G1 → L2 の順を守る | `audit-summary.md` §1.5, `L1-REQUIREMENTS.md` |
| `feedback_v2_vmodel_score_chain_break_penalty.md` | feedback | V-model score は chain break を明示減点する | rule: 単純平均ではなく chain break penalty を入れる / Why: 4 layer chain は途中切断が本質リスクだから / How to apply: `100 - 15×missing_test_design - 10×missing_baseline - 20×failing_baseline` を初期候補として採用 | TL log `20260514-005424-tl-advisor.log` |
| `feedback_v2_origin_mode_lifecycle.md` | feedback | `origin_mode` は forward / reverse / scrum を分け、reverse は observed→inferred→confirmed を踏む | rule: 起源と確度を分離記録する / Why: Reverse/Scrum 由来の契約を Forward と混同しないため / How to apply: record に `origin_mode`, `evidence_status`, `origin_ref` を持たせる | TL log `20260514-005424-tl-advisor.log`, `L1-REQUIREMENTS.md` FR-VD07 |
| `feedback_v2_four_layer_chain_is_spine.md` | feedback | 4 layer chain は V2 の backbone であり、coverage より先に writer 接続を優先する | rule: `contract → code → test_design → baseline` を先に通す / Why: schema があっても 0 record では運用価値がない / How to apply: writer / view / score / dashboard を spine 起点で設計する | `audit-summary.md` DR-001, `CONCEPT.md` |
| `feedback_v2_pmo_startup_error_tmp_test_helix.md` | feedback | PMO 起動エラー `/tmp/test-helix not found` は stale local settings 起因で、当面は Codex research 代替が妥当 | rule: PMO 経路障害時は research/docs role で代替継続 / Why: wrapper 修正ではなく local settings 起因だったため / How to apply: settings 修正完了までは read-only 調査を Codex で継続する | `pmo-startup-debug.md` |
| `feedback_v2_parallel_up_to_8_when_independent.md` | feedback | 依存なし task は 8 並列まで使い切る | rule: 衝突・後段依存・共有状態更新が無ければ直列化禁止 / Why: V2 構築で 1 task 走行がボトルネックとして顕在化したため / How to apply: plan 分割時に parallel 判定を明示する | `MEMORY.md`, `feedback_max_parallel_8_default.md` |
| `project_v2_phase_a_audit_top20_driver.md` | project | Phase A audit で 20 audit doc / 6,453 行から V2 top-20 driver を抽出した | rule: 調査結果は project snapshot として残す / Why: 次セッション onboarding の核になるため / How to apply: Phase A の結論を設計ドライバ一覧として参照する | `audit-summary.md` §1, §2 |
| `feedback_v2_folder_structure_pm_top3.md` | feedback | folder-structure 整理は PM 判断 top-3 を先に固定してから進める | rule: `.helix` Git 管理、agent-skills vendor 境界、PLAN 正本の三点を先に決める / Why: source-of-truth を先に決めないと整理が drift するため / How to apply: folder cleanup 前に PM 判断項目を ADR/plan へ固定する | `audit-summary.md` §1.5, DR-005, DR-006, DR-007 |
| `feedback_v2_memory_governance_before_mass_import.md` | feedback | V2 知見を memory へ大量投入する前に governance を先に決める | rule: type/index/archive/duplicate/redaction のルールを先に固定 / Why: 既存 memory は 86 entries, index 279 行で既に肥大化しているため / How to apply: 起票前に retention と archive policy を定義する | `memory-feedback-drift.md` |
| `feedback_v2_guard_should_be_enforced_not_documented.md` | feedback | guard/skill/hook ルールは文書化だけでなく fail-close 接続まで持つ | rule: policy は enforcement まで到達して初めて memory 化する / Why: V1 で prompt-only ルールが破られたため / How to apply: memory には `origin -> enforcement -> audit` を残す | `accumulated-knowledge.md`, `audit-summary.md` DR-008 |

---

## §2 想定 entry 候補 (最低 15 件)

以下は実際の起票対象として推奨する 17 件。  
`description` は memory index の 1 行説明を想定し、`出典` は初回起票時に最低限 frontmatter または本文へ残したい根拠を示す。

### 2.1 推奨度 High

| No. | memory file name | type | description | body skeleton | 出典 |
|---:|---|---|---|---|---|
| 1 | `feedback_v2_existing_capabilities_centerline.md` | feedback | V2 は既存能力の再接続を主戦場とする | rule / Why / How to apply | `audit-summary.md` DR-002 |
| 2 | `feedback_v2_drive_layer_semantics_externalized.md` | feedback | drive × layer 意味論は YAML 外部化し DB enum 化を避ける | rule / Why / How to apply | TL log `20260514-005424-tl-advisor.log` |
| 3 | `feedback_v2_fe_promotion_append_only.md` | feedback | FE mock promotion は append-only で扱い証跡を上書きしない | rule / Why / How to apply | TL log `20260514-005424-tl-advisor.log`, `L1-REQUIREMENTS.md` FR-VD04 |
| 4 | `feedback_v2_fullstack_tracks_not_split.md` | feedback | fullstack は be/fe/contract/shared の track 並列で扱う | rule / Why / How to apply | `L1-REQUIREMENTS.md` §3.8 |
| 5 | `feedback_v2_g35_start_as_subgate.md` | feedback | G3.5 は public gate ではなく G3 サブゲートから始める | rule / Why / How to apply | `L1-REQUIREMENTS.md` §3.8 |
| 6 | `feedback_v2_bulk_fill_after_schema_spine_freeze.md` | feedback | bulk fill-in は schema spine 凍結後に限定する | rule / Why / How to apply | TL log `20260514-005424-tl-advisor.log` |
| 7 | `feedback_v2_origin_mode_lifecycle.md` | feedback | origin_mode は forward/reverse/scrum と evidence_status を組みで持つ | rule / Why / How to apply | TL log `20260514-005424-tl-advisor.log`, `reverse-scrum-audit.md` |
| 8 | `feedback_v2_four_layer_chain_is_spine.md` | feedback | 4 layer chain は V2 backbone で、writer 接続が coverage より先 | rule / Why / How to apply | `audit-summary.md` DR-001, `CONCEPT.md` |
| 9 | `feedback_v2_vmodel_score_chain_break_penalty.md` | feedback | score は chain break penalty を入れた減点式で扱う | rule / Why / How to apply | TL log `20260514-005424-tl-advisor.log` |
| 10 | `project_v2_phase_a_audit_top20_driver.md` | project | Phase A 20 doc から top-20 driver を抽出済みという project snapshot | rule / Why / How to apply | `audit-summary.md` §1-2 |

### 2.2 推奨度 Medium

| No. | memory file name | type | description | body skeleton | 出典 |
|---:|---|---|---|---|---|
| 11 | `feedback_v2_expected_skills_advisory_only.md` | feedback | expected_skills は advisory であり fail-close にしない | rule / Why / How to apply | `accumulated-knowledge.md`, `HELIX_CORE.md` |
| 12 | `feedback_v2_phase2_is_draft_and_spike.md` | feedback | Phase 2 は draft/design spike として先行固定しすぎない | rule / Why / How to apply | `audit-summary.md` §1.5 |
| 13 | `feedback_v2_pmo_startup_error_tmp_test_helix.md` | feedback | PMO 起動障害時は stale local settings を疑い、Codex research で代替する | rule / Why / How to apply | `pmo-startup-debug.md` |
| 14 | `feedback_v2_parallel_up_to_8_when_independent.md` | feedback | 独立 task は 8 並列まで使い切る | rule / Why / How to apply | `MEMORY.md`, `feedback_max_parallel_8_default.md` |
| 15 | `feedback_v2_folder_structure_pm_top3.md` | feedback | folder-structure 整理は PM 判断 top-3 を先に固定する | rule / Why / How to apply | `audit-summary.md` DR-005/006/007 |
| 16 | `feedback_v2_memory_governance_before_mass_import.md` | feedback | memory 追加前に governance を先に固定する | rule / Why / How to apply | `memory-feedback-drift.md` |
| 17 | `feedback_v2_guard_should_be_enforced_not_documented.md` | feedback | guard/hook/policy は文書化だけでなく enforcement と audit まで接続する | rule / Why / How to apply | `accumulated-knowledge.md`, `hooks-commands-subagents.md` |

### 2.3 既存 `MEMORY.md` との関係

- 既に近いものがある:
  - `feedback_max_parallel_8_default.md`
  - `project_2026_05_14_v2_sprint_transformation.md`
- ただし本計画の候補は、既存 entry の「V2 全体ルール化」または「出典整理版」として再起票または merge update の価値がある
- 特に `parallel`, `append-only`, `functional_freeze`, `origin_mode`, `4 layer chain` は V2 監査・TL advice・L1 要件の 3 系統で裏付けが揃っており、独立 memory として再利用性が高い

---

## §3 既存 entry の update 候補

### 3.1 `MEMORY.md` index 整理

現状:

- `MEMORY.md` 実測 279 行
- `memory-feedback-drift.md` では 277 行時点で 200 行制限を 77 行超過
- 86 entry に対し index 掲載は 83、未掲載 4、死リンク 1

更新方針:

1. index は「最新 30 件前後 + 永続ルール数件」へ縮退する
2. project completion 系の長文 1 行を圧縮し、詳細は個別 file に退避する
3. type 欠落 entry を補正し、死リンクを除去する
4. 目標は 150 行前後。厳密な 150 未満は archive/merge 実施後に再集計する

### 3.2 V1 PLAN 完了 entry の 1 行 index 化

優先対象:

- `project_2026_05_10_*`
- `project_2026_05_11_*`
- `project_2026_05_03_*`
- `project_2026_05_06_*` 〜 `2026_05_09_*`

更新ルール:

- index には `PLAN-ID / 完了日 / 1 行結果 / 代表テスト結果` のみ残す
- 詳細な commit 数、grade 推移、逐次 review round は個別 project entry に残す
- project entry 本体を消さず、index だけ軽くする

### 3.3 重複 entry の merge 候補

優先 merge 候補:

- `feedback_parallel_dispatch_default.md` + `feedback_max_parallel_8_default.md`
- role 関連 feedback 群
- Codex distrust / verification distrust 群

merge 指針:

- 事故単位ではなく rule 単位で統合する
- merge 後は旧 file を archive 候補へ回す
- `cluster_id` 相当の追跡子を将来導入する前提で、出典は本文に残す

---

## §4 memory archive 推奨 (memory-archive-exec と整合)

`memory-feedback-drift.md` の archive 推奨を基準に、V2 観点で再確認した結果は以下の通り。

### 4.1 archive 維持推奨

| memory file | 現判定 | 理由 |
|---|---|---|
| `restructure-plan.md` | archive 維持 | 2026-03-07 起点で type 欠落、現行 schema 外 |
| `project_next_wave.md` | archive 維持 | 待ち行列メモで現行 PLAN 群へ分解済みの可能性が高い |
| `project_builder_system.md` | archive 維持 | 構想メモで current core route から外れている |
| `reference_codex_plugin_cc.md` | archive 維持 | plugin 参照メモとして stale |

### 4.2 archive ではなく merge/update を検討

| memory file | 提案 | 理由 |
|---|---|---|
| `project_helix_v2_deliverable_matrix.md` | merge | V2 audit/doc 側へ昇格済みの可能性が高い |
| `project_helix_vision.md` | merge | vision は `CONCEPT.md` / V2 docs へ統合する方が自然 |
| `project_2026_05_14_v2_sprint_transformation.md` | update | 直近で重要、ただし top-level `type` 欠落補正が必要 |

### 4.3 追加 archive 候補

現時点では追加 archive 候補を強く推奨しない。  
理由:

- V2 関連の新規 feedback/project はまだ新鮮で、先に merge/index 圧縮の方が効果が高い
- まず既存 4 件の archive と type/index 整理を先行すべき

---

## §5 V2 後の memory 運用ルール

### 5.1 type 別 retention policy

| type | 役割 | 保持方針 |
|---|---|---|
| `feedback` | 再発防止ルール | 原則 keep。重複時は merge |
| `project` | セッション/リリース snapshot | 30 日後に index 圧縮対象。詳細 file は keep/archive 判定 |
| `reference` | 外部参照・設計参照 | stale 化しやすいため 30-60 日で review |

### 5.2 月次 archive cycle

1. 月次で stale scan を実施する
2. `review_after` 到来 entry を `keep/update/merge/archive` に強制分類する
3. archive 実行時は `MEMORY.md` index と dead link を同時更新する
4. monthly scan の結果は summary memory ではなく follow-up doc にまとめる

### 5.3 duplicate check

新規 memory 起票前に最低限確認すること:

1. 同一 rule を既存 `feedback_*.md` が持っていないか
2. 同一 event 由来の近接 entry がないか
3. index だけ長文化していないか
4. rule 化に耐えない単発メモでないか

推奨 metadata:

- `type`
- `source_plan_ids`
- `source_docs`
- `canonical_status_source`
- `review_after`
- 将来拡張として `cluster_id`

### 5.4 秘密情報 redaction

ルール:

- credential / token / email / password 形式の文字列を memory に複写しない
- 例示が必要な場合は `sample credential`, `redacted email` など抽象化して書く
- 実値ではなくても、認証サンプル値は原則 memory へ残さない

既知注意点:

- `memory-feedback-drift.md` は `project_2026_05_09_plan032_completion.md` に sample 認証値が含まれる可能性を指摘している
- V2 では「除外理由だけ残し、値は残さない」運用へ寄せるべき

---

## 推奨

優先順は次の通り。

1. `feedback_v2_drive_layer_semantics_externalized.md`
2. `feedback_v2_fe_promotion_append_only.md`
3. `feedback_v2_fullstack_tracks_not_split.md`
4. `feedback_v2_g35_start_as_subgate.md`
5. `feedback_v2_origin_mode_lifecycle.md`
6. `feedback_v2_four_layer_chain_is_spine.md`
7. `feedback_v2_memory_governance_before_mass_import.md`
8. `project_v2_phase_a_audit_top20_driver.md`

理由:

- V2 の設計判断を将来セッションへ持ち越すうえで、`drive/layer`, `append-only`, `subgate`, `origin_mode`, `4 layer chain` が最も再利用性が高い
- memory 運用自体が肥大化しているため、V2 技術知見の起票と同時に governance entry を入れる必要がある
- PMO 起動障害や 8 並列原則は有用だが、V2 核設計よりは二次優先に置ける

---

## ソース

- [docs/v2/A-audit/audit-summary.md](/home/tenni/ai-dev-kit-vscode/docs/v2/A-audit/audit-summary.md:1)
- [docs/v2/A-audit/accumulated-knowledge.md](/home/tenni/ai-dev-kit-vscode/docs/v2/A-audit/accumulated-knowledge.md:1)
- [docs/v2/A-audit/memory-feedback-drift.md](/home/tenni/ai-dev-kit-vscode/docs/v2/A-audit/memory-feedback-drift.md:1)
- [docs/v2/CONCEPT.md](/home/tenni/ai-dev-kit-vscode/docs/v2/CONCEPT.md:1)
- [docs/v2/L1-REQUIREMENTS.md](/home/tenni/ai-dev-kit-vscode/docs/v2/L1-REQUIREMENTS.md:1)
- [docs/v2/C-followup/pmo-startup-debug.md](/home/tenni/ai-dev-kit-vscode/docs/v2/C-followup/pmo-startup-debug.md:1)
- `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/MEMORY.md`
- `.helix/audit/codex-runs/20260514-005424-tl-advisor.log`

