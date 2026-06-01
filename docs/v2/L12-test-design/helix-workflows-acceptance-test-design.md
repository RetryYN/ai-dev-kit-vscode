---
doc_id: L12-helix-workflows-acceptance-test-design
title: "HELIX-workflows V2 受入テスト設計 (Acceptance Test Design, L3↔L12 pair)"
status: frozen
freeze_evidence: "2026-06-02 L0-L3 review + L4 completion session; TL adversarial check; pair docs L14 L12 created; L4-L9 pair; plan_validator 0 ERROR"
created: 2026-06-02
owner: PM
process_layer: L12
pairs_with: L3
pairs_design: docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
parent_plan: L3-helix-workflows-機能要件plan
related_requirements:
  - docs/v2/L3-requirements/helix-workflows-functional-requirements-detail.md
  - docs/v2/L3-requirements/helix-workflows-business-requirements-detail.md
  - docs/v2/L3-requirements/helix-workflows-nfr-detail.md
---

# 受入テスト設計 (L3↔L12 pair)

## §1 目的と境界

L3 要件 (FR / BR / NFR 詳細) が L12 で受入可能かを、ユーザー / PO 視点の受入基準で検証する。本 doc は scaffold、受入基準、trace を固定し、実テストコード / 実行 / 環境差異の実吸収は L12 デプロイ受入フェーズで行う。

- source で確認した L3 実在 ID: `BR-01..12`、`FR-NSM-01`、`FR-GR-01`、`FR-TDD-01`、`FR-9MODE-01`、`FR-GATE-01`、`FR-IMPACT-01`、`FR-EVT-01`、`FR-4ART-01`、`FR-INV-01`、`FR-CTX-01`、`FR-DRIFT-01`、`FR-PLAN-01`、`FR-DOCTOR-01`、`FR-MIGR-01`、`FR-DOCREVIEW-01`、`FR-CHANGEPROP-01`、`FR-FNREG-01`、`FR-GLOSSARY-01`、`NFR-AV-01..03`、`NFR-PF-01..04`、`NFR-OP-01..08`、`NFR-MG-01..04`、`NFR-SC-01..05`、`NFR-SE-01..03`
- source で確認した既存 AC 参照: `AC-BR-01..12`、`AC-FR-01..14`、`AC-NFR-OP-06`、`AC-NFR-OP-07`、`AC-NFR-OP-08`、`AC-NFR-MG-04`、`AC-NFR-SF-01`
- L3 要件総数は `57` 件 (`BR 12 + FR 18 + NFR 27`)。本設計は `AT-01..57` を割り当て、全 L3 FR 18 件を最低 1 AT 以上でカバーする。

## §2 受入テストケース

| AT-ID | 対応要件ID | 受入シナリオ | 受入基準 | 優先度 |
|---|---|---|---|---|
| AT-01 | BR-01 | 新規 PLAN が dogfooding の正本として起票される | Given 整合済み PLAN; When 起票; Then `plan_registry` 登録と gate 完了が観測できる | P1 |
| AT-02 | BR-02 | 4 artifact 欠落 PLAN が retrofit に回る | Given 欠落 PLAN; When doctor 実行; Then stub 生成と再 scan 導線が出る | P1 |
| AT-03 | BR-03 | drift が重大度に応じて収束フローへ送られる | Given 新規 drift; When detector 実行; Then Recovery / Reverse / debt のいずれかへ分類される | P1 |
| AT-04 | BR-04 | 9 mode 作業が Forward へ復帰できる | Given mode closure; When close; Then `mode_transition` と target L が残る | P1 |
| AT-05 | BR-05 | ペア凍結欠落を起票時に止める | Given pair 欠落 doc; When lint; Then fail-close で差戻される | P1 |
| AT-06 | BR-06 | 改修前に影響範囲を可視化できる | Given PLAN 変更; When impact-range; Then 4 artifact 影響一覧が返る | P1 |
| AT-07 | BR-07 | L 工程 entry で AI 配線が強制される | Given L3 entry; When context bundle; Then mandatory skill / command / agent が入る | P1 |
| AT-08 | BR-08 | portable package が採用 project へ展開可能である | Given package; When init 導入; Then dogfooding 開始条件が揃う | P2 |
| AT-09 | BR-09 | 既存資産整理で机上宣言を防ぐ | Given 設計 doc; When review; Then `implementation_status` 欠落は reject される | P1 |
| AT-10 | BR-10 | 段階移行が残量付きで管理される | Given V1/V2 混在; When migration 監査; Then Phase 別残量と kill criteria が見える | P1 |
| AT-11 | BR-11 | 大規模 doc 改定に品質レビューが必ず入る | Given 大規模改定; When gate 前確認; Then doc-reviewer evidence が残る | P1 |
| AT-12 | BR-12 | 上流変更で下流追従漏れを防ぐ | Given ID 更新; When changeprop 検査; Then trace / balance_ratio regression が block される | P1 |
| AT-13 | FR-NSM-01 | PM が V-model 整合スコアを把握できる | Given 集計期間; When query; Then NSM と 6 axes score が返る | P1 |
| AT-14 | FR-GR-01 | Guardrail が逸脱を fail-close する | Given 閾値逸脱; When guardrail 評価; Then `pass/warn/block/throttle` が分離される | P1 |
| AT-15 | FR-TDD-01 | テストアフターが防止される | Given step 飛ばし; When sprint 進行; Then 許可外 step は block される | P1 |
| AT-16 | FR-9MODE-01 | signal から適切な mode 候補が得られる | Given 代表 signal; When route eval; Then 候補と根拠が返る | P1 |
| AT-17 | FR-GATE-01 | gate が静的判定と AI 判定を分離する | Given gate 実行; When static / AI 条件評価; Then verdict 遷移が観測できる | P1 |
| AT-18 | FR-IMPACT-01 | 影響範囲 query が SLA 内に返る | Given PLAN / artifact 起点; When query; Then 中央値 5 秒以内で結果が返る | P1 |
| AT-19 | FR-EVT-01 | mode closure が idempotent に保存される | Given 同一 key; When 2 回 close; Then row 重複なく target L が残る | P1 |
| AT-20 | FR-4ART-01 | 4 artifact 欠落が工程別に検知される | Given trace 欠落; When doctor; Then advisory / warning / blocking が分かれる | P1 |
| AT-21 | FR-INV-01 | 資産 inventory が工程別密度を示す | Given 資産登録; When inventory; Then 工程別件数と未割当が返る | P1 |
| AT-22 | FR-CTX-01 | layer ごとの制約付き context が注入される | Given `L3 + se`; When bundle; Then mandatory / recommended が両方返る | P1 |
| AT-23 | FR-DRIFT-01 | discrepancy が適切な routing 先へ振られる | Given 複数 drift; When drift-check; Then interrupt / recovery / reverse へ分類される | P1 |
| AT-24 | FR-PLAN-01 | PLAN の dependency / generates が追跡される | Given frontmatter; When graph 化; Then broken link と deprecated path が見える | P1 |
| AT-25 | FR-DOCTOR-01 | doctor が横断監査を 1 つに束ねる | Given 複数監査結果; When doctor; Then summary と critical が分離される | P1 |
| AT-26 | FR-MIGR-01 | migration と retrofit が安全に進む | Given migration plan; When 実行; Then destructive 系は manual approval 要求になる | P1 |
| AT-27 | FR-DOCREVIEW-01 | doc 品質レビューが 4 視点で返る | Given 対象 doc; When doc-reviewer 召喚; Then verdict と P0-P3 指摘が返る | P1 |
| AT-28 | FR-CHANGEPROP-01 | change ratchet が品質後戻りを止める | Given 上流 ID 更新; When doctor 3 軸検査; Then regression は fail-close される | P1 |
| AT-29 | FR-FNREG-01 | FR SSoT が参照 drift を検出する | Given FR 参照 doc; When registry check; Then 未定義 / 重複 / drift が出る | P1 |
| AT-30 | FR-GLOSSARY-01 | 用語 SSoT が未定義語とゆれを検出する | Given 用語利用 doc; When glossary check; Then 未定義 0 / ゆれ閾値判定が返る | P1 |
| AT-31 | NFR-AV-01 | CLI が高可用で起動できる | Given 月次運用; When 起動監査; Then 成功率 99.9% 以上を満たす | P1 |
| AT-32 | NFR-AV-02 | `helix.db` が破損なく保全される | Given 運用 / 復旧後; When health check; Then corruption 0 / metadata 欠落 0 を満たす | P1 |
| AT-33 | NFR-AV-03 | 中断時に handover から再開できる | Given session 中断; When handover 発火; Then dump 95% 以上 / 15 分以内再開を満たす | P1 |
| AT-34 | NFR-PF-01 | doctor が許容時間内で完了する | Given 代表規模; When doctor; Then 30 秒以内で完了する | P2 |
| AT-35 | NFR-PF-02 | impact-range が性能目標を満たす | Given 中規模 trace; When query; Then median 5 秒 / p95 10 秒以内を満たす | P2 |
| AT-36 | NFR-PF-03 | 並列 Codex 実行で衝突しない | Given 8 並列; When workspace 実行; Then 衝突 0 件で全 run 完走する | P2 |
| AT-37 | NFR-PF-04 | skeleton PLAN を 1 分以内に起票できる | Given 新規テーマ; When PLAN 起票; Then 初稿生成 1 分以内 / 失敗率 5% 未満 | P2 |
| AT-38 | NFR-OP-01 | stale 資産が月次で archive される | Given stale 資産; When 月次処理; Then archive 実行率 90% 以上を満たす | P2 |
| AT-39 | NFR-OP-02 | 月次 audit が取りこぼしなく回る | Given PLAN / skill / hook; When audit; Then 完遂率 100% / P0 排出率 100% を満たす | P1 |
| AT-40 | NFR-OP-03 | warn 閾値が段階運用できる | Given warn 蓄積; When doctor; Then 50 alert / Phase α exit 20 以下で判定される | P2 |
| AT-41 | NFR-OP-04 | lineage trace 欠損なく追跡できる | Given 主要資産; When lineage 監査; Then 欠損 0 / coverage 100% を満たす | P1 |
| AT-42 | NFR-OP-05 | verify-before-act 違反を出さない | Given memory carry; When 実行前確認; Then verify 実施率 100% / 違反 0 を満たす | P1 |
| AT-43 | NFR-OP-06 | inventory drift が 5% 以下に収まる | Given 週次計測; When inventory 監査; Then drift ≤ 5% / status 列充足 100% を満たす | P1 |
| AT-44 | NFR-OP-07 | doc-reviewer 召喚 coverage を維持する | Given 大規模 doc 改定群; When 週次監査; Then coverage / evidence 残置率 ≥ 95% を満たす | P1 |
| AT-45 | NFR-OP-08 | ratchet が全 commit で有効化される | Given 上流変更 commit; When hook 実行; Then 強制率 100% / trace 切れ 0 を満たす | P1 |
| AT-46 | NFR-MG-01 | retrofit pipeline を再実行できる | Given 同一入力; When 再実行; Then 成功率 95% 以上 / rollback path 保持を満たす | P2 |
| AT-47 | NFR-MG-02 | schema migration が idempotent である | Given 同一 migration; When 再適用; Then 副作用 0 件を満たす | P2 |
| AT-48 | NFR-MG-03 | package 導入初期化が 30 分以内で終わる | Given 採用 project; When bootstrap; Then 30 分以内で利用開始条件が揃う | P2 |
| AT-49 | NFR-MG-04 | Strangler Fig 移行が Phase 管理される | Given Phase α/β/γ; When migration 監査; Then 各残量目標を満たす | P1 |
| AT-50 | NFR-SC-01 | secret / API key が repo に残らない | Given repo scan; When security 監査; Then 検出 0 件である | P1 |
| AT-51 | NFR-SC-02 | repeated regen を検知して止める | Given settings 変動; When commit 前確認; Then diff 確認強制と検知率 100% を満たす | P1 |
| AT-52 | NFR-SC-03 | 非許可 tool 呼び出しを block する | Given PMO / PdM tool 実行; When guard; Then block 率 100% を満たす | P1 |
| AT-53 | NFR-SC-04 | Codex の commit / push guard が破られない | Given Codex 実行; When commit / push 試行; Then 違反 0 件を満たす | P1 |
| AT-54 | NFR-SC-05 | 高リスク変更で人間確認を必須化する | Given 認証 / PII 等; When 実行要求; Then 人間確認率 100% を満たす | P1 |
| AT-55 | NFR-SE-01 | Linux / macOS で主要コマンドが通る | Given OS matrix; When 代表 command 実行; Then 成功率 100% を満たす | P2 |
| AT-56 | NFR-SE-02 | Claude / Codex の両導線が継続可能である | Given 両 runtime; When core entry 実行; Then 継続率 100% を満たす | P1 |
| AT-57 | NFR-SE-03 | 下限 version を常に満たす | Given 環境診断; When version check; Then Python / Bash / SQLite / git 違反 0 件である | P2 |

## §3 trace matrix

| 要件ID | AT-ID |
|---|---|
| BR-01 | AT-01 |
| BR-02 | AT-02 |
| BR-03 | AT-03 |
| BR-04 | AT-04 |
| BR-05 | AT-05 |
| BR-06 | AT-06 |
| BR-07 | AT-07 |
| BR-08 | AT-08 |
| BR-09 | AT-09 |
| BR-10 | AT-10 |
| BR-11 | AT-11 |
| BR-12 | AT-12 |
| FR-NSM-01 | AT-13 |
| FR-GR-01 | AT-14 |
| FR-TDD-01 | AT-15 |
| FR-9MODE-01 | AT-16 |
| FR-GATE-01 | AT-17 |
| FR-IMPACT-01 | AT-18 |
| FR-EVT-01 | AT-19 |
| FR-4ART-01 | AT-20 |
| FR-INV-01 | AT-21 |
| FR-CTX-01 | AT-22 |
| FR-DRIFT-01 | AT-23 |
| FR-PLAN-01 | AT-24 |
| FR-DOCTOR-01 | AT-25 |
| FR-MIGR-01 | AT-26 |
| FR-DOCREVIEW-01 | AT-27 |
| FR-CHANGEPROP-01 | AT-28 |
| FR-FNREG-01 | AT-29 |
| FR-GLOSSARY-01 | AT-30 |
| NFR-AV-01 | AT-31 |
| NFR-AV-02 | AT-32 |
| NFR-AV-03 | AT-33 |
| NFR-PF-01 | AT-34 |
| NFR-PF-02 | AT-35 |
| NFR-PF-03 | AT-36 |
| NFR-PF-04 | AT-37 |
| NFR-OP-01 | AT-38 |
| NFR-OP-02 | AT-39 |
| NFR-OP-03 | AT-40 |
| NFR-OP-04 | AT-41 |
| NFR-OP-05 | AT-42 |
| NFR-OP-06 | AT-43 |
| NFR-OP-07 | AT-44 |
| NFR-OP-08 | AT-45 |
| NFR-MG-01 | AT-46 |
| NFR-MG-02 | AT-47 |
| NFR-MG-03 | AT-48 |
| NFR-MG-04 | AT-49 |
| NFR-SC-01 | AT-50 |
| NFR-SC-02 | AT-51 |
| NFR-SC-03 | AT-52 |
| NFR-SC-04 | AT-53 |
| NFR-SC-05 | AT-54 |
| NFR-SE-01 | AT-55 |
| NFR-SE-02 | AT-56 |
| NFR-SE-03 | AT-57 |

- L3 functional 要件 `18` 件はすべて最低 `1` AT を持つ。
- L3 要件総数 `57`、AT 総数 `57`、`balance_ratio = 57 / 57 = 1.00`。

## §4 carry

- `AC-FR-15..18`、`AC-NFR-*` の詳細 naming は L12 実行時に本 AT 設計を正本として補完する。
- 採用 project 実環境、OS matrix、並列 Codex 実行、migration 残量は staging / production 同等環境で再計測する。
- `NFR-SF-01` は L3 NFR 本文では再導出観点のため、本 doc では `AT-49` / `AT-54` にまたがる安全観点として実行時 evidence を束ねる。
