# Phase G FE 弱点強化 詳細実装計画
最終更新: 2026-05-14  
作成: Research (Codex)  
用途: `docs/v2/L1-REQUIREMENTS.md` の `FR-FE01`〜`FR-FE06` を Phase G で着手可能な実装計画へ落とす。  
対象: `cli/lib/extractors/`, `cli/lib/detectors/`, `cli/helix-fe`, `cli/lib/helix_db.py`, `cli/config/vmodel-semantics.yaml`, `cli/tests/`, `cli/lib/tests/`

## 0. 概要
Phase G の狙いは、FE を「スキルと文書に依存する設計フロー」から、「contract registry / detector / command / gate / baseline / semantics が連動する機械実装フロー」へ引き上げることにある。現状の強みは `mock-driven-development` と `visual-design` による設計思想であり、弱みはそれを `contract_entries`, `detector_runs`, `routing_decisions`, `test_baseline`, `vmodel-semantics` に接続する実装が無い点にある。

中心判断は次の 4 点である。
1. FE を別 subsystem にせず、既存 `contract_entries` と detector framework を拡張する。
2. `helix fe` を新設して、setup script 止まりの FE 検証を運用 command に昇格する。
3. G5 は `DESIGN.md lint` 単独 gate から、visual / a11y / mock debt を束ねた evidence bundle gate へ拡張する。
4. FE 5-stage pipeline は新 workflow を起こさず、L2-G6 の既存 HELIX フェーズへ埋め込む。

不確実性:
- `helix` コマンドはこのセッションの PATH 上に無く、CLI 実行確認は未実施。既存コードと文書の静的読解に基づく。
- `.helix/helix.db` の実 schema version は未実行確認であり、schema 拡張点は `cli/lib/helix_db.py` 現行実装から推定した。
- `memory feedback (FE 5-stage pipeline)` の原文 file 名は TASK_INPUT に無いため、ここでは与えられた pipeline 内容だけを根拠に採用する。

## 2. FR-FE01 FE 専用 contract type 5+ 追加
### 2.1 概要
現行 `cli/lib/contract_registry.py` は `docs/features/**/D-API/*.yaml` を scan して `contract_entries` へ投入する実装のみを持つ。Phase G では FE の設計成果物を contract として同列管理できるようにし、detector と review query の入力に昇格させる必要がある。

追加対象 contract type: `component_props`, `state_events`, `visual_token`, `a11y_requirement`, `screen_transition`

### 2.2 選択肢
| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| `contract_entries` へ FE type を同居 | 既存 `find`, detector, score と接続しやすい | source ごとの extractor 設計が必要 | 高 |
| `fe_contract_entries` を新設 | FE 固有メタデータを持ちやすい | 既存 query が流用しにくい | 中 |
| 生成 JSON を file artifact として保持のみ | 実装が速い | DB traceability を失う | 低 |

### 2.3 推奨
`contract_entries` 継続利用を推奨する。追加列が必要な場合も FE 専用 table ではなく、既存 table に最小追加する方が Phase H 以降の cross-drive 検出に有利である。

### 2.4 実装ファイル
| 役割 | 実装ファイル | 内容 |
|---|---|---|
| extractor registry | `cli/lib/contract_registry.py` | scan 対象と dispatch を FE source へ拡張 |
| component props extractor | `cli/lib/extractors/component_props.py` | TypeScript / Vue props 抽出 |
| state events extractor | `cli/lib/extractors/state_events.py` | `state-events.md` パース |
| visual token extractor | `cli/lib/extractors/visual_token.py` | JSON/YAML token 抽出 |
| a11y extractor | `cli/lib/extractors/a11y_requirement.py` | checklist / requirement 抽出 |
| screen transition extractor | `cli/lib/extractors/screen_transition.py` | state machine / flow 定義抽出 |
| DB schema | `cli/lib/helix_db.py` | 必要なら FE contract metadata 列追加 |
| tests | `cli/lib/tests/test_contract_registry.py` | FE contract insert / dedupe / symbol lookup 固定 |

### 2.5 `contract_entries` への INSERT 経路
推奨 insert 経路は 1 本化する。
1. `contract_registry.py init` または将来の `helix fe state-events-validate --register` が extractor を呼ぶ。
2. extractor は `contract_type`, `source_path`, `symbol_id`, `version`, `schema_hash`, `introduced_plan`, `raw_spec` を返す。
3. `bulk_insert()` は FE type も既存 dedupe ルールで `contract_entries` に挿入する。
4. `symbol_id` 命名は `fe.<feature>.<artifact>.<name>` 形式に寄せる。
5. `raw_spec` は extractor 後の canonical JSON を格納し、detector はこれを比較対象に使う。

### 2.6 extractor 詳細
#### component_props
- 対象: `*.tsx`, `*.ts` の props interface/type alias、`*.vue` の `defineProps`, `props:`
- 抽出単位: 1 component surface = 1 contract row、`symbol_id` は `fe.component_props.<relative_component_path>`
- 不確実性: AST 導入可否は未確認。MVP は構文制限付き抽出が現実的

#### state_events
- 対象: `state-events.md`
- 抽出内容: state 名、event 名、guard、side effect、transition graph
- `raw_spec`: transitions 配列を canonical JSON 化

#### visual_token
- 対象: `tokens.json`, `design-tokens.yaml`, theme file 群
- 抽出内容: color / spacing / typography / radius / motion、hash 比較は token key/value の canonical sort

#### a11y_requirement
- 対象: a11y checklist markdown、component-level WCAG requirement doc
- 抽出内容: requirement id、target screen/component、severity、expected test kind

#### screen_transition
- 対象: state machine 図由来 YAML/JSON、`state-events.md` からの派生 graph
- 抽出内容: screen -> screen、trigger、condition、forbidden transition

### 2.7 Phase 紐付け
| Phase | 対象 | 理由 |
|---|---|---|
| G.1 | `component_props`, `state_events`, `visual_token` | detector/command の最小閉ループを作りやすい |
| G.2 | `a11y_requirement`, `screen_transition` | a11y/playwright/state drift と同時導入が自然 |

### 2.8 実装ステップ
1. `contract_registry.py` に FE source scan dispatcher を追加する。
2. `cli/lib/extractors/` に 5 file を追加し、共通返却 shape を固定する。
3. FE source path 規約を `docs/v2/B-design/vmodel-semantics-fe-draft.yaml` と整合させる。
4. `test_contract_registry.py` に FE insert / duplicate / find の 3 系統を追加する。
5. G.1 完了時点で `component_props`, `state_events`, `visual_token` の 3 type が DB query 可能な状態を acceptance とする。
6. G.2 で `a11y_requirement`, `screen_transition` を追加し、state/a11y detector の入力を閉じる。

### 2.9 リスク
- TS/Vue parser を重くしすぎると CLI 依存追加が増える。MVP は構文制限付き抽出が妥当。
- `state-events.md` は naming 揺れが既に監査で見つかっているため、extractor 実装前に artifact ID と実 file 名の分離ルールを固定する必要がある。

## 3. FR-FE02 FE 専用 detector axis-15〜19
### 3.1 概要
既存 detector registry は `axis_01`〜`axis_14` のみであり、FE 固有 drift を機械的に fail-close できない。Phase G では mock-driven と visual refinement を gate 連動させるため、5 本の detector を追加する。

対象 axis: `axis-15-mock-promotion`, `axis-16-design-token-drift`, `axis-17-a11y-regression`, `axis-18-visual-regression`, `axis-19-state-transition-drift`

### 3.2 選択肢
| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| detector 5 本を独立実装 | verdict と threshold を個別制御できる | file 数は増える | 高 |
| axis-14 / axis-11 へ FE ロジックを内包 | 既存 file を流用できる | 診断責務が曖昧になる | 中 |
| G5/G6 shell check に埋め込む | 最短で動く | DB 記録と dashboard が弱い | 低 |

### 3.3 推奨
独立 5 detector 実装を推奨する。理由は、Phase G 後に false positive 調整・warning 運用・gate 昇格を個別に扱えるからである。

### 3.4 実装ファイル
| axis | 実装ファイル | 主入力 |
|---|---|---|
| 15 | `cli/lib/detectors/axis_15_mock_promotion.py` | `contract_entries`, mock debt, promoted lineage |
| 16 | `cli/lib/detectors/axis_16_design_token_drift.py` | visual token contract, current token file |
| 17 | `cli/lib/detectors/axis_17_a11y_regression.py` | axe baseline, a11y requirement |
| 18 | `cli/lib/detectors/axis_18_visual_regression.py` | screenshot baseline, snapshot diff result |
| 19 | `cli/lib/detectors/axis_19_state_transition_drift.py` | `state_events`, screen transition, runtime test result |

追加更新:
- `cli/lib/detectors/registry.py`
- `cli/lib/tests/` 配下の detector test
- 必要なら `cli/lib/helix_db.py` の `detector_runs` 参照拡張

### 3.5 各 axis 詳細
#### axis-15 mock-promotion
- 検査: `mock_frozen` から `promoted` への append-only lineage と production への mock 混入有無
- 入力: `component_props`, `state_events`, `screen_transition`, mock debt record, FE semantics promotion lifecycle
- threshold: MVP は promoted lineage 欠落 1 件以上で `failed`、拡張で orphan mock 件数を config 化
- fail-close: G2 warning、G4 は `MOCK-HARDCODE` / `MOCK-CODE-LEAK` 未解消で fail、G6 は `MOCK-DERIVED-CONTRACT` 未解消で fail

#### axis-16 design-token-drift
- 検査: mock/design token baseline と実装 token の差分
- 入力: `visual_token` contract rows、実 token file、`DESIGN.md` 参照 token name
- threshold: semantic token key 削除は fail、value 変更は severity 別に warn/fail
- fail-close: G4 architecture/detailed drift で fail、G5 design bundle 不整合で fail

#### axis-17 a11y-regression
- 検査: axe-core baseline と現行結果を比較し FE regression を検知
- 入力: `a11y_requirement`、axe result JSON、screen inventory
- threshold: critical/serious violation 増分 > 0 で fail、minor 増分のみは warning 可
- fail-close: G4 detailed/functional の critical 増分、G6 release candidate では serious も fail

#### axis-18 visual-regression
- 検査: snapshot diff / screenshot diff による視覚差分
- 入力: baseline snapshot、current render、allowed diff threshold
- threshold: pixel diff ratio または perceptual diff score。初版は screen 単位固定値
- fail-close: G4 critical screen diff、G6 full review bundle の 1 要素として fail-close

#### axis-19 state-transition-drift
- 検査: `state_events` / `screen_transition` と runtime 遷移の不一致
- 入力: state-events contract、transition graph、Playwright 遷移 trace
- threshold: undocumented transition 1 件以上、または missing expected transition 1 件以上で fail
- fail-close: G1/G2/G3 では warning 許容、G4 で contract/runtime 不整合は fail

### 3.6 G ゲート連動
| Gate | 自動実行 detector | 判定 |
|---|---|---|
| G2 | axis-15, axis-19 | mock freeze 時点の drift 早期検知 |
| G3 | axis-16, axis-17, axis-19 | detailed contract 凍結の妥当性確認 |
| G4 | axis-15〜19 全部 | FE 実装凍結の主検査 |
| G5 | axis-15, axis-16, axis-18 | visual refinement gate |
| G6 | axis-17, axis-18, axis-19 | bundle review / RC 判定 |

### 3.7 実装ステップ
1. `registry.py` に 5 detector import と descriptor を追加する。
2. 各 detector は `BaseDetector` 継承で JSON output と `detector_runs` 記録を既存流儀に合わせる。
3. G.1 では axis-15,16,19 を MVP として追加する。
4. G.2 では axis-17,18 を追加し、a11y/visual baseline と接続する。
5. G.3 で G5/G6 との auto-run wiring を調整する。
6. false positive を避けるため、初版 threshold は config 定数化し hard-code を避ける。

### 3.8 リスク
- visual regression は baseline 更新 UX が無いと運用不能なので、FR-FE03 とセットで実装する必要がある。
- a11y/visual/state trace は外部ツール実行結果に依存するため、初版は result file を入力とする thin detector に留めるのが安全である。

## 4. FR-FE03 FE 専用 command 5+ 追加
### 4.1 概要
FE 側は `setup-playwright.sh`, `setup-axe.sh`, `helix asset` までは存在するが、日常運用で使う `helix fe ...` 導線がない。Phase G では FE 検証 command を 1 namespace に集約し、dry-run と detector/gate 連携の入口にする。

対象 command:
- `helix fe visual-diff`
- `helix fe a11y-check`
- `helix fe playwright-run`
- `helix fe snapshot-update`
- `helix fe state-events-validate`

### 4.2 選択肢
| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| `cli/helix-fe` 新設 | discoverability が高い | route file が増える | 高 |
| `helix test/gate` に FE option を追加 | 既存 command 流儀に寄る | FE command として見つけづらい | 中 |
| shell script 群のまま運用 | 実装が最小 | dry-run と gate 連動が弱い | 低 |

### 4.3 推奨
`cli/helix-fe` 新設を推奨する。entry を独立させつつ、内部では既存 `helix-test`, `helix-gate`, detector, contract extractor を呼ぶ thin router とする。

### 4.4 entry script と内部呼び出し
| command | entry | 内部呼び出し候補 | dry-run |
|---|---|---|---|
| visual-diff | `cli/helix-fe` | snapshot tool + axis-18 input JSON 出力 | 対象 screen と baseline path のみ表示 |
| a11y-check | `cli/helix-fe` | axe runner + axis-17 input JSON 出力 | 対象 page / config のみ表示 |
| playwright-run | `cli/helix-fe` | Playwright suite 実行 | 実行対象 spec 一覧のみ表示 |
| snapshot-update | `cli/helix-fe` | baseline file 更新 | 更新対象一覧と件数のみ表示 |
| state-events-validate | `cli/helix-fe` | `state_events` extractor + graph validator + optional register | パース結果要約のみ表示 |

### 4.5 argparse 仕様
共通オプション:
- `--feature <name>`, `--stage <planning|requirement|architecture|detailed|functional>`, `--plan-id <PLAN-NNN>`, `--dry-run`, `--json`, `--baseline <name|path>`

個別追加:
- `visual-diff`: `--screen`, `--update-baseline`
- `a11y-check`: `--url`, `--severity-threshold`
- `playwright-run`: `--spec`, `--headed`
- `snapshot-update`: `--all`, `--screen`
- `state-events-validate`: `--path`, `--register`, `--strict`

### 4.6 Phase 紐付け
| Phase | command | 理由 |
|---|---|---|
| G.1 | `state-events-validate`, `playwright-run`, `visual-diff` | state/runtime/visual の MVP 閉ループ |
| G.2 | `a11y-check`, `snapshot-update` | baseline 運用と a11y を追加 |

### 4.7 実装ステップ
1. `cli/helix-fe` を bash または Python で新設する。
2. subcommand parser を実装し、まずは dry-run と command help を成立させる。
3. `state-events-validate` を最初に実装し、FR-FE01 の extractor と接続する。
4. `playwright-run` / `visual-diff` は result file 出力までを MVP にする。
5. `a11y-check` / `snapshot-update` を G.2 で追加する。
6. `docs/commands/index.md` に `helix fe` namespace を追記する。
7. `cli/tests/test-helix-fe*.bats` を追加して help / dry-run / invalid args を固定する。

### 4.8 リスク
- 実際の FE 実行環境が repo 外にある場合、command 自体は thin wrapper とし、path/URL 指定を外出しにする必要がある。
- Playwright / axe の install を command 内で自動化すると責務が肥大化するため、setup は既存 script 継続、運用は `helix fe` に分離すべきである。

## 5. FR-FE04 G5 visual refinement gate 運用化
### 5.1 概要
現行 G5 は `DESIGN.md lint` の統合が中心で、mock debt 未解消や visual drift を fail-close にする構造が薄い。Phase G では G5 を FE 専用 evidence bundle gate へ拡張し、未解消 mock/design drift を通さない。

### 5.2 選択肢
| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| G5 を visual evidence bundle gate 化 | FE gate の意味が明確になる | 実装範囲が広い | 高 |
| 既存 `DESIGN.md lint` 維持 + detector warning のみ | 既存差分が小さい | fail-close 要件を満たしにくい | 中 |
| G4/G6 に吸収して G5 を薄くする | gate 数を増やさない | FE drive の独自性が消える | 低 |

### 5.3 推奨
G5 は残しつつ意味を強化する。推奨 bundle は次の 4 点である。
1. `DESIGN.md lint`
2. `axis-16-design-token-drift`
3. `axis-18-visual-regression`
4. 未解消 `MOCK-*` debt の有無

### 5.4 実装ポイント
- `routing_decisions` に `MOCK-* auto-enqueue` を記録する。
- G5 開始時に未解消 `MOCK-*` を query し、残件があれば fail-close。
- `cli/helix-gate` の G5 判定に FE bundle branch を追加する。
- `docs/DESIGN.md` lint はそのまま bundle 要素として残す。

### 5.5 推奨 fail-close 条件
| 条件 | 判定 |
|---|---|
| `MOCK-HARDCODE` 未解消 | fail |
| `MOCK-CODE-LEAK` 未解消 | fail |
| token drift critical | fail |
| visual regression critical | fail |
| `DESIGN.md` lint fail | fail |
| visual diff minor only | warning |

### 5.6 実装ステップ
1. G5 で参照する FE debt type を定義する。
2. mock promotion detector から `routing_decisions` enqueue record を出す。
3. `helix-gate` G5 branch に bundle 集約ロジックを追加する。
4. `test_helix_gate_g5_design_md.bats` 相当の FE 拡張テストを追加する。
5. G.3 完了条件を「G5 が FE evidence bundle を読んで fail-close できる」とする。

### 5.7 リスク
- `routing_decisions` schema の現状詳細はこの場で確認できていないため、既存 queue table の再利用可否は実装時要確認。
- G5 に載せすぎると G4/G6 と責務が重複する。visual refinement に直接効くものだけに絞るべきである。

## 6. FR-FE05 FE test_baseline test_kind 拡張
### 6.1 概要
FE detector を運用するには、`test_baseline` または同等 schema が snapshot / visual / Playwright / axe を基準値として保持できなければならない。Phase G では FE test kind を schema に追加し、`helix test` との接続点を作る。

### 6.2 選択肢
| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| `test_baseline` へ kind 追加 | V-model 4 layer chain を維持できる | migration が必要 | 高 |
| FE baseline table 別建て | FE 固有メタデータを持ちやすい | score/view 連携が複雑 | 中 |
| result file を detector が直接読む | 実装は早い | baseline 履歴が散逸する | 低 |

### 6.3 推奨
`test_baseline` 拡張を推奨する。FR-VD09 の chain を FE にも通すには、contract -> code -> test_design -> test_baseline を別 table に分けない方が良い。

### 6.4 追加 test_kind
- `snapshot`
- `visual_regression`
- `playwright`
- `axe_a11y`

### 6.5 推奨 schema 拡張
- `test_kind` enum/validation 拡張
- baseline artifact path、result summary JSON、severity summary、screen / route / component key

### 6.6 `helix test` との連動
推奨連動方針:
1. `helix fe ...` が result JSON を出力する。
2. `helix test` は FE result collector を optional で読む。
3. collector は `test_baseline` へ bulk insert/update を行う。
4. detector は `test_baseline` を一次参照し、raw result file を二次参照する。

### 6.7 実装ファイル
| 役割 | ファイル |
|---|---|
| schema migration | `cli/lib/helix_db.py` |
| FE baseline writer | `cli/lib/fe_test_baseline.py` または `helix-fe` 内 helper |
| CLI routing | `cli/helix-test`, `cli/helix-fe` |
| tests | `cli/lib/tests/test_helix_db.py`, `cli/tests/test-helix-fe*.bats` |

### 6.8 実装ステップ
1. schema 拡張で FE test kind を受理できるようにする。
2. `playwright`, `axe_a11y`, `snapshot`, `visual_regression` の最小 record shape を固定する。
3. `helix fe` 実行結果から baseline writer を呼ぶ。
4. `helix test` では FE baseline 書き込みを optional 統合する。
5. G.2 の完了条件を「4 kind が schema と command の両方で認識される」とする。

### 6.9 リスク
- schema version が v21 前提と要件で書かれているため、Phase 3 側の migration 完了待ちが前提になる。
- baseline file の保存場所を決めないと DB だけ増えて再現性が落ちる。path 規約をセットで決める必要がある。

## 7. FR-FE06 FE drive vmodel-semantics.yaml entries
### 7.1 概要
`docs/v2/B-design/vmodel-semantics-fe-draft.yaml` は FE draft として十分に豊富だが、まだ `cli/config/vmodel-semantics.yaml` の正本には統合されていない。Phase G では FE semantics を draft から実装用 config へ昇格し、contract / detector / command / gate を 1 つの semantic source に接続する。

### 7.2 選択肢
| 選択肢 | メリット | デメリット | 推奨度 |
|---|---|---|---|
| `cli/config/vmodel-semantics.yaml` に統合 | drive 横断で一貫する | draft 整合チェックが必要 | 高 |
| FE 専用 config のまま持つ | 移行は速い | fullstack との接続が弱い | 中 |
| config を持たず code へ埋め込む | 実装速度は出る | drift しやすい | 低 |

### 7.3 推奨
G1 通過後に FE draft を共通 `vmodel-semantics.yaml` へ統合する。fullstack draft にも `axis-15`, `axis-18`, `axis-19` の一部参照が既にあり、別 config に分離する理由が弱い。

### 7.4 統合時の重点項目
- mock -> implementation promotion lifecycle
- layer 別 artifacts
- layer 別 detectors
- layer 別 command hints
- `requires_functional_freeze`
- owner role mapping

### 7.5 実装ステップ
1. draft の naming 揺れを整理する。
2. `state-events.md` のような実 file 名は artifact ID と分離する。
3. `drives.fe.layers.*` を共通 config に移植する。
4. `helix gate --pair-check --drive fe` 側が参照できるよう loader を整える。
5. fullstack との shared artifact 命名も同時に合わせる。
6. G.4 完了時に FE 5-stage pipeline を semantics 上で参照可能にする。

### 7.6 リスク
- draft は設計スパイク前提なので、そのまま code に凍結すると不要な暫定命名が残る可能性がある。
- `cross-drive-integrity-check.md` で指摘済みの naming drift を先に解かないと、FE semantics 統合後に fullstack 側へ負債を増やす。

## 8. FE 5-stage pipeline 組み込み
### 8.1 概要
memory feedback の要旨は次の 5 段で FE を運用することである。
1. wire (`5.5`)
2. mockup 画像 (`5.5`)
3. 判断 (Opus)
4. 実装 (Sonnet)
5. review (`5.5`)

本計画では、これを独立 workflow とせず既存 HELIX フェーズへ埋め込む。

### 8.2 埋め込み方針
| HELIX phase | 追加する FE 能力 |
|---|---|
| L2 design | wire / mockup を成果物化 |
| G2 | `mockup_decision_record` 必須 |
| L3 | TL が `state-events.md` から FE contract 抽出 |
| L4 | `mock_promotion`, `mock_hardcode`, `mock_code_leak`, `state_transition_drift` fail-close |
| L5 | visual / a11y / Playwright bundle review |

### 8.3 推奨成果物
- `wire.md` または wire image
- `.helix/mock/<feature>/mock.html`
- `state-events.md`
- `mockup_decision_record`
- FE contract rows
- visual/a11y/playwright baseline bundle

### 8.4 推奨理由
- pipeline を artifact/gate に落とすことで、人依存の FE ノウハウを capability に変換できる。
- `Opus 判断` を gate 証跡へ残せるため、mock 採否の監査可能性が上がる。
- `state-events.md` が L3 で contract 抽出されるため、設計と実装の同期点が明確になる。

### 8.5 不確実性
- 実際のモデル分担は環境やコスト制約で変わりうるため、本計画では role hint として扱い、gate 必須条件にはしない。

## 9. Phase G 実装ステップ
### 9.1 Phase G.1 MVP
対象:
- contract type 3: `component_props`, `state_events`, `visual_token`
- detector 3: `axis-15`, `axis-16`, `axis-19`
- command 3: `state-events-validate`, `playwright-run`, `visual-diff`

完了条件:
- FE contract 3 種が `contract_entries` へ投入可能
- detector 3 本が registry で起動可能
- `helix fe` 3 command が dry-run と help を持つ
- G2/G4 に最小連動

### 9.2 Phase G.2 拡張
対象:
- contract type 2: `a11y_requirement`, `screen_transition`
- detector 2: `axis-17`, `axis-18`
- command 2: `a11y-check`, `snapshot-update`
- test_baseline kind 4 種

完了条件:
- a11y/state transition まで chain が閉じる
- baseline 保存と detector 参照が接続される

### 9.3 Phase G.3 G5 運用化
対象:
- `MOCK-* auto-enqueue`
- G5 evidence bundle
- `DESIGN.md` lint 既存統合の拡張

完了条件:
- G5 が FE debt / visual drift / token drift を fail-close できる

### 9.4 Phase G.4 FE pipeline HELIX 統合
対象:
- FE 5-stage pipeline の phase/gate 接続
- `vmodel-semantics.yaml` への FE 統合
- role / artifact / detector / command hint の整備

完了条件:
- FE drive を L2-G6 で一気通貫に説明・検証可能

## 10. 依存関係
| 依存 | 内容 | 本計画への影響 |
|---|---|---|
| Phase 2 | V-model 強化完了 | FE semantics の統合先が必要 |
| Phase 3 | `helix.db` v21 / test_baseline schema 拡張 | FR-FE05 の前提 |
| Phase 4 | detector framework 完成 | FR-FE02 の土台 |

依存解釈:
- FR-FE01/03 は G.1 から先行可能。
- FR-FE05/06 は schema/config 側の整備を待つ依存が強い。
- FR-FE04 は detector と debt queue の両方が必要なため G.3 に置くのが妥当。

## 11. 推奨優先順位
1. `state_events` extractor + `helix fe state-events-validate`
2. `visual_token` extractor + `axis-16-design-token-drift`
3. `axis-15-mock-promotion`
4. `helix fe visual-diff`
5. FE baseline kind 拡張
6. `axis-17` / `axis-18`
7. G5 evidence bundle
8. FE semantics 正本統合

理由:
- FE の契約同期点は `state-events` が最重要であり、ここが無いと mock-driven と runtime drift の両方が宙に浮く。
- visual token と mock promotion は FE 独自 drift を最小構成で表しやすく、MVP として価値が高い。
- a11y/visual baseline は command と schema の両方が必要なので 2 段目が妥当である。

## 12. ソース
- `docs/v2/L1-REQUIREMENTS.md` `FR-FE01`〜`FR-FE06`
- `docs/v2/A-audit/fe-weakness-analysis.md`
- `docs/v2/B-design/vmodel-semantics-fe-draft.yaml`
- `docs/v2/C-followup/detector-drive-layer-mapping.md`
- `docs/v2/B-design/cross-drive-integrity-check.md`
- `cli/lib/contract_registry.py`
- `cli/lib/detectors/registry.py`
- `cli/lib/helix_db.py`
- `cli/helix-gate`
- `cli/helix-test`
- `docs/commands/index.md`

## 13. 推奨
推奨は次の構成である。
- Phase G.1 で `state_events` / `visual_token` / `component_props` を DB へ入れ、`axis-15/16/19` と `helix fe` 3 command を先に通す。
- Phase G.2 で a11y/visual baseline と `axis-17/18`、`test_baseline` 拡張を追加し、FE runtime verify を閉じる。
- Phase G.3 で G5 を visual evidence bundle gate へ拡張する。
- Phase G.4 で FE 5-stage pipeline と `vmodel-semantics.yaml` 統合を完了する。

この順序なら、FE 弱点強化を「contract -> detector -> command -> gate -> baseline -> semantics」の spine として段階的に固められる。最重要の先行実装は `state-events.md` を contract 化する入口であり、ここを外すと後続の detector と gate はいずれも暫定運用に留まる。
