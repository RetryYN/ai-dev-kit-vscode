# FR-INV04 FE 弱点分析

## 概要

本メモは、HELIX の FE 関連 capability を既存実装ベースで棚卸しし、`docs/v2/L1-REQUIREMENTS.md` の Phase G「FE 弱点強化」へ投入するための監査結果である。結論は、**FE 設計フローの思想とスキルはあるが、DB schema / detector / CLI command / semantic registry の4層で機械実装が不足している**、である。

評価基準:

- `実装済`: 実コードまたは CLI / gate による機械実装あり
- `部分実装`: スキル・設計書・gate 条件はあるが、機械実装が揃っていない
- `不在`: 要件や構想のみで、実装証拠が見当たらない

不確実性:

- `helix` コマンドはこの実行環境の PATH 上に無く、CLI 実行確認はできていない。そのため本監査は **リポジトリ内のコード・文書の静的読解** に基づく。
- `.helix/audit/codex-runs/*` や `.helix/tmp/*` の生成物は参考にせず、正本は `cli/`, `skills/`, `docs/` を優先した。

## 1. 軸別評価

| 項目 | 現状 | 既存実装 | BE 相当物との差 | V2 Phase G で追加すべき内容 |
|---|---|---|---|---|
| FE 専用 contract type | 部分実装 | `contract_entries` は存在するが `contract_type` は汎用文字列で、現行 registry は `docs/features/**/D-API/*.yaml` だけを scan する。FE 型の extractor は未実装。 | BE は D-API YAML から `contract_entries` へ機械投入できるが、FE は `component_props` / `state_events` / `visual_token` / `a11y_requirement` / `screen_transition` を投入する入口がない。 | `fe_contract_registry`, `state_events_extractor`, `design_token_extractor`, `a11y_contract_extractor`, `screen_transition_registry` |
| FE 専用 detector | 部分実装 | detector は `axis_01`〜`axis_14` まで存在。relation / regression / connection / orchestration など BE 寄りの汎用検査はある。 | BE は contract / code / test / relation を detector 連鎖で見られるが、FE 固有 drift を見る detector 群がない。 | `axis_15_mock_promotion`, `axis_16_design_token_drift`, `axis_17_a11y_regression`, `axis_18_visual_regression`, `axis_19_state_transition_drift` |
| FE 専用 command | 部分実装 | `helix asset` は存在し、Playwright / axe の setup script もある。だが `helix fe ...` namespace や FE 専用検証 command は見当たらない。 | BE は `helix gate`, `helix code`, `helix review`, `contract_registry.py` など機械入口が多い。一方 FE は setup 止まりで、運用 command が薄い。 | `helix fe visual-diff`, `helix fe a11y-check`, `helix fe playwright-run`, `helix fe snapshot-update`, `helix fe state-events-validate` |
| FE drive `vmodel-semantics` 不在 | 不在 | `docs/v2/L1-REQUIREMENTS.md` では `cli/config/vmodel-semantics.yaml` が要件化されているが、実ファイルは未確認。既存 schema に `drive` も未実装。 | BE/QA 側は `design_level`, `test_design_entries`, `design_review`, `test_baseline` まであるが、drive 別意味論が無いので FE lifecycle を表現できない。 | `cli/config/vmodel-semantics.yaml`, `drive` 列追加, `origin_mode`, `evidence_status`, FE semantic validator |
| FE 設計フロー (mock-driven-development) の運用化度 | 部分実装 | `skills/agent-skills/mock-driven-development/SKILL.md` と `skills/project/fe-design/**` に、`mock.html` → `state-events.md` → 契約導出 → `MOCK-*` debt の流れが定義されている。`gate-policy.md` にも G2/G3/G4/G6 条件がある。 | BE 相当物は schema / registry / gate が比較的コード化されているが、mock-driven はスキル依存が強く、debt auto-enqueue や state-events 検証の実装証拠は弱い。 | `mock_debt_enqueuer`, `state_events_schema`, `mock_import_detector`, `mock_hardcode_scanner`, `mock_contract_review_record` |
| FE 5-stage pipeline (wire → mockup → 判断 → 実装 → review) | 不在 | 現行 framework には `mock-driven-development` と `visual-design` はあるが、wire/mockup 画像生成、Opus 判断、Sonnet 実装、5.5 review まで含む固定 pipeline 定義は見当たらない。 | BE には role と gate の結線がある。FE は multi-agent pipeline が運用知として散在し、HELIX の正式 workflow に昇格していない。 | `helix fe pipeline init`, `wire_review_handoff`, `mockup_decision_record`, `fe_role_routing`, `fe_pipeline_scorecard` |
| `visual_design` / `design-tools-web-system` / `DESIGN.md` lint | 部分実装 | `visual-design` は L2/L5 の設計思想を提供。`design-md-lint-integration.md` と `cli/helix-gate` で G5 時の `docs/DESIGN.md` lint fail-close はある。 | BE 相当の gate は DB/contract/test までトレースされるが、FE の visual refinement は `DESIGN.md` lint 中心で、実画面 diff・token drift・a11y 回帰との連動が弱い。 | `design_md_to_token_link`, `g5_visual_evidence_bundle`, `visual_diff_gate`, `design_token_sync_check`, `l5_review_recorder` |

## 2. 詳細メモ

### 2.1 FE 専用 contract type

- 現行 `contract_entries` schema は `contract_type`, `source_path`, `symbol_id`, `schema_hash`, `design_level` を持つが、FE 特化列や drive 列はない。
- `cli/lib/contract_registry.py` は `docs/features/**/D-API/*.yaml` しか scan せず、OpenAPI / YAML 契約を前提にしている。
- したがって FE の `state-events.md` や design token 定義があっても、registry へ入らず detector や review query の対象にできない。

選択肢:

| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| `contract_entries` を拡張して FE 型を同居 | 既存 query / detector 基盤を再利用できる | extractor を複数追加する必要がある | 高 |
| FE 専用 table を別建て | FE 固有 schema を自由に設計できる | BE/FE の横断 query が複雑化する | 中 |
| 文書運用のまま継続 | 実装コストが低い | 機械検証不能のまま | 低 |

推奨:

- **`contract_entries` 拡張案** を採る。BE 相当物との差分が最小で、Phase G の detector/command と自然に接続できる。

### 2.2 FE 専用 detector

- 実装済 detector は 14 本で、dead/coverage/dup/doc drift/relation graph/regression/connection/orchestration など汎用観点が中心。
- FE 要件で明示された `axis-15`〜`axis-19` は未実装。
- 特に `mock_promotion` と `state_transition_drift` は mock-driven-development と直結するが、現状はスキル文書依存。

選択肢:

| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| axis-15〜19 を独立 detector として追加 | verdict と fail-close 条件を個別管理できる | 実装本数は増える | 高 |
| axis-14 orchestration へ FE ルールを混載 | 既存 detector を流用できる | 責務が肥大化し、診断理由が曖昧 | 中 |
| gate の grep/bash で暫定対応 | 最短で入れられる | 拡張性と再利用性が低い | 中 |

推奨:

- **独立 detector 5 本追加**。あとで dashboard / score 化しやすい。

### 2.3 FE 専用 command

- `docs/commands/index.md` 上、FE 特化 command と言えるのは `helix asset` だけで、これは画像 asset 生成寄り。
- `cli/scripts/setup-playwright.sh`, `cli/scripts/setup-axe.sh` はあるが、実運用 command ではなくセットアップ補助。
- `FR-FE03` のコマンド群は要件化済みだが未実装。

選択肢:

| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| `helix fe` namespace を新設 | FE 関連 command を discover しやすい | ルーティング追加が必要 | 高 |
| 既存 `helix gate/test/verify` に FE option を増設 | 既存導線に乗る | FE 入口が見えづらい | 中 |
| setup script をそのまま使う | 変更最小 | Phase G の capability として弱い | 低 |

推奨:

- **`helix fe` namespace 新設**。最低限 `visual-diff`, `a11y-check`, `playwright-run`, `snapshot-update`, `state-events-validate` を 1 階層にまとめる。

### 2.4 FE drive `vmodel-semantics` 不在

- `docs/v2/L1-REQUIREMENTS.md` は `drive` 列、`vmodel-semantics.yaml`、FE lifecycle semantic を明示している。
- しかし現行実装で確認できた schema は `design_level` 止まりで、drive 別 semantics を保持していない。
- そのため `mock → 本実装 promotion lifecycle` を schema レベルで表現できない。

選択肢:

| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| `vmodel-semantics.yaml` を正本化し DB に `drive` を追加 | 4 drive 共通で semantics を外部化できる | migration が必要 | 高 |
| drive ごとにコードへハードコード | 初期は速い | drift しやすく拡張しづらい | 低 |
| FE だけ別 YAML を持つ | FE 導入は速い | 全体整合が崩れる | 中 |

推奨:

- **共通 `vmodel-semantics.yaml` + DB `drive` 列**。FE だけ特殊扱いせず、V2 の 4 drive 全体で意味論を揃えるべき。

### 2.5 FE 設計フローの運用化度

- mock-driven-development は思想・成果物・debt lifecycle まで定義されている。
- `gate-policy.md` にも G2/G3/G4/G6 の FE 追加条件がある。
- ただし、これを registry / detector / command へ落とした実装証拠は限定的で、現時点では **強い設計だが弱い機械化** である。

推奨:

- mock-driven-development を Phase G の中核に据え、文書スキルではなく **機械検証可能な FE contract workflow** へ昇格させる。

### 2.6 FE 5-stage pipeline

- 調査対象の「wire → mockup → 判断 → 実装 → review」は、既存 HELIX 文書では明示的 workflow として確認できなかった。
- 既存は `visual-design` と `mock-driven-development` の組み合わせで近いことはできるが、モデル役割分担と成果物 handoff の標準化は未整備。

推奨:

- `Phase G` で **pipeline 契約そのものを capability 化** する。人の記憶や運用ノウハウに依存させない。

### 2.7 Visual Refinement / DESIGN.md lint

- `visual-design` は L2/L5 の役割を明確化しており、`DESIGNER.md` / IA / layout / ux / L5 refinement の概念は強い。
- `design-md lint` は `cli/helix-gate` に fail-close 実装がある。
- ただし lint 対象は `docs/DESIGN.md` の構造整合であり、実画面差分や a11y regressions までは見ていない。

推奨:

- G5 を `DESIGN.md lint` 単体 gate から、**visual evidence bundle gate** へ拡張する。

## 3. 集計

- 不在: 2 件
- 部分実装: 5 件
- 実装済: 0 件

補足:

- 「部分実装」は、設計思想やスキルはあるが、BE 相当の機械化が足りない状態を指す。
- 最も深刻な不足は、`contract registry` と `detector` と `semantic registry` の 3 点が FE で連鎖していないこと。

## 4. Phase G で追加すべき capability Top 5

1. `cli/config/vmodel-semantics.yaml` + DB `drive` 列 + FE semantic validator  
   理由: FE lifecycle を schema に落とさない限り、以後の detector / gate / dashboard が安定しない。
2. FE contract registry 拡張  
   理由: `state_events`, `component_props`, `visual_token`, `a11y_requirement`, `screen_transition` を `contract_entries` に入れないと、BE 同等の traceability が成立しない。
3. FE detector 5 本 (`axis-15`〜`axis-19`)  
   理由: mock-driven と visual refinement を fail-close にするための観測基盤。
4. `helix fe` command namespace  
   理由: setup script ではなく運用 command に昇格させ、FE team が discover できる入口を作る必要がある。
5. G5 visual evidence bundle  
   理由: `DESIGN.md` lint 単独では visual / token / a11y drift を抑えられない。

## 5. FE 5-stage pipeline を HELIX に組み込む方針案

推奨方針は、**mock-driven-development を中核に、wire/mockup/review を capability 化して L2-G6 に接続する** ことである。

最小構成:

1. L2 で `wire` と `mockup` を成果物化する  
   `wire.md` または wire image、`.helix/mock/<feature>/mock.html`、`state-events.md` をセットで正本化する。
2. G2 で「判断」を記録する  
   UX 承認だけでなく、採用理由・却下理由・保留論点を `mockup_decision_record` として残す。
3. L3 で `state-events.md` から FE contract を registry 化する  
   ここで `component_props`, `state_events`, `screen_transition` を `contract_entries` に登録する。
4. L4-G4 で mock promotion を detector 管理する  
   `mock_promotion`, `mock_hardcode`, `mock_code_leak`, `state_transition_drift` を fail-close にする。
5. L5-G6 で visual / a11y / playright を review bundle 化する  
   `DESIGN.md lint`, visual diff, axe, Playwright 結果を 1 つの evidence bundle として gate 評価する。

この構成なら、現行 HELIX の BE 優位な V-model を壊さず、FE だけを例外処理にせず拡張できる。推奨は **新規 FE subsystem を別建てするのではなく、既存 V-model を FE 方向に一般化すること** である。

## 6. ソース

- `cli/lib/helix_db.py`
- `cli/lib/contract_registry.py`
- `cli/lib/detectors/registry.py`
- `cli/lib/detectors/axis_14_orchestration.py`
- `cli/helix-gate`
- `docs/commands/index.md`
- `docs/v2/L1-REQUIREMENTS.md`
- `docs/agent-skills/README.md`
- `skills/agent-skills/mock-driven-development/SKILL.md`
- `skills/project/ui/SKILL.md`
- `skills/common/visual-design/SKILL.md`
- `skills/common/visual-design/references/design-md-lint-integration.md`
