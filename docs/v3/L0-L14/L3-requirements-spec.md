# HELIX V3 — L3 要件定義

> **status: draft**（TL review → freeze 前）
> 入力: [L1 要求定義](L1-requirements.md)（BR / FR / NFR）
> 対の検証（V-model L3↔L12）: §2 受入テスト設計

本書は L1 の FR/NFR を **検証可能な要件（REQ）+ 受入条件（AC）** へ落とし、各要件に対の受入テスト（AT）を置く。engine の内部構造（テーブル群・detector 一覧）は L4 基本設計で確定するため、本書は **契約・振る舞いの要件**に留める。

---

## 0. 位置づけ

V3 harness の要件を「機械で合否判定できる」形に固める。fork の設計意図を盗むが、AC は **HELIX 独自に観測可能な事実**（DB 行・exit code・detector 出力）で書く（fork との出力 parity ではなく契約で固定＝NFR-V3-05）。

## 1. 要件（REQ）

### 1.1 schema 単一 registry SSoT（← FR-ENG-01）

| REQ | 受入条件（AC） |
|---|---|
| REQ-SCH-01 | 全テーブルの DDL が**単一の registry 定義**から生成される。registry 外で `CREATE TABLE` を書いた箇所が存在しない（grep / static check で 0 件）。 |
| REQ-SCH-02 | `SCHEMA_VERSION` 定数を持ち、schema 変更時に version が上がる。version と実 DDL の不整合を検出できる。 |
| REQ-SCH-03 | **物理 FK は同一 DB 内のみ**。cross-DB FK 宣言が 0 件（NFR-V3-02）。境界越え参照は logical（FK でない列）+ consistency detector で表現。 |

### 1.2 単一 projection-writer（← FR-ENG-02/03, NFR-V3-01）

| REQ | 受入条件（AC） |
|---|---|
| REQ-PRJ-01 | 単一の projection 入口が、定義済み artifact 種別（PLAN/code/FR/設計/test/workflow）を rule で DB へ投影する。投影先テーブルは artifact 種別ごとに一意に決まる。 |
| REQ-PRJ-02 | **idempotent**: 同一入力で 2 回 rebuild → DB 状態が bit 同一（重複行ゼロ）。 |
| REQ-PRJ-03 | **deletion-aware**: artifact を削除して rebuild → 対応 DB 行が消える（orphan 行ゼロ）。 |
| REQ-PRJ-04 | **stale-aware**: artifact 更新で古い投影行を検出/更新（古い内容が残らない）。 |
| REQ-PRJ-05 | 壊れた frontmatter/契約違反 artifact は **fail と warn を分離**して報告（投影を黙って飛ばさない）。 |
| REQ-PRJ-06 | **rebuild ⊥ append_event**（TL C-1）: `rebuild_projection` は projection table のみ TRUNCATE+再投影 / `append_event` は append table へ冪等追記（rebuild 後残存）。`test_results`(current) ≠ `test_result_events`(red→green 履歴)。secret/PII/raw transcript 非保存（TL C-5）。 |

### 1.3 DB 駆動 detector（← FR-ENG-04/05）

| REQ | 受入条件（AC） |
|---|---|
| REQ-DET-01 | detector は **pure-function 3 層**（analyze/load/messages）で「あるべき − 実在 = もれ」を返し、各々 `source_kind`（db_projection/file_snapshot/hybrid）を宣言する。absence（DB row/file 不在・空）でも ok=false（scope-0 silent OK 禁止）。 |
| REQ-DET-02 | doctor 集約は **ok=AND**（1 つでも fail なら全体 fail、fail-close）。I/O 失敗 = ok=false（skip 禁止）。 |
| REQ-DET-03 | detector 出力は機械可読（id / severity / 欠落要素）で、push gate / CI が exit code で判定できる。 |

### 1.4 lint-wiring メタゲート（← FR-ENG-06）

| REQ | 受入条件（AC） |
|---|---|
| REQ-WIR-01 | 実行口（runtime entrypoint）から到達不能な detector を**死蔵として検出・禁止**する。 |
| REQ-WIR-02 | 意図的除外は **DEFERRED に理由付きで明示**する（暗黙の未配線を許さない）。現状の axis-04/10/13 相当の死蔵が V3 では 0 件 or DEFERRED 明示。 |

### 1.5 baseline ratchet（← FR-ENG-07, NFR-V3-03）

| REQ | 受入条件（AC） |
|---|---|
| REQ-RAT-01 | advisory→fail-close を baseline で段階昇格する。baseline は **縮小のみ可**（増加＝debt 追加を reject）。 |
| REQ-RAT-02 | baseline 初期スナップショットの生成手順が定義され、再現可能。 |

### 1.6 ルール化 doc/workflow 契約（← FR-ENG-08, FR-COR-01, FR-DRV-01, FR-CFG-01）

| REQ | 受入条件（AC） |
|---|---|
| REQ-DOC-01 | doc/workflow が **機械パース可能な契約**（必須 frontmatter / ID 規約 / 必須セクション）を持ち、違反を detector が検出する。 |
| REQ-DOC-02 | 駆動 workflow は **forward_return を機械契約**として持つ（散文依存をやめる）。 |
| REQ-DOC-03 | HELIX 設定が UT workflow 群の契約形式へ差し替えられ、projection-writer で DB 登録される（FR-CFG-01）。 |

### 1.7 HELIX 優位（← FR-FE-01, FR-DST-01, FR-HRN-01）

| REQ | 受入条件（AC） |
|---|---|
| REQ-FE-01 | FE/UI detector が **drive=fe/fullstack で発火**し、UI-absent profile では core gate を阻害しない（waiver）。 |
| REQ-DST-01 | 公開 API `@~/.helix/core/<path>` が**不変**（消費側 loader が読める）。core-manifest ⇔ setup.sh ⇔ loader の一致を検証。 |
| REQ-HRN-01 | agent/role guard + hook が AI 規律を fail-close で機械強制し、worker≠reviewer を分離する。 |

### 1.8 AI 自走・設計テンプレート coverage・改善 loop（← FR-AUTO/TPL/REV/PRM/LRN/UPG）

| REQ | 受入条件（AC） |
|---|---|
| REQ-AUTO-01 | AI 自走 step は `planned/executed/verified/reviewed/learned` の event または projection を残す。未登録 step がある成果は完了扱いにならない。 |
| REQ-AUTO-02 | runtime rules §10 の escalation signal（prod/auth/payment/pii/secret/license/schema/env/external API 等）を検出した場合、auto-run は停止し human approval を要求する。 |
| REQ-TPL-01 | `template_catalog` に source_url / source_kind / doc_kind / layer / required_sections / pair_test_kind / provenance_hash / freshness_status が登録される。 |
| REQ-TPL-02 | `doc_coverage` は template_catalog と artifact_registry から「必要 doc kind − 実在 doc kind」を算出し、coverage gap を detector に渡せる。 |
| REQ-TPL-03 | 外部テンプレート本文の長文複製は保存せず、項目構造・粒度・検証観点へ正規化する。license/permission 判断が必要な template は `requires_human_license_review=true` で gate に上げる。 |
| REQ-REV-01 | review evidence は観点別（architecture/security/test/doc/perf/ux/ops）に保存され、同一観点の unresolved critical/high finding がある場合は gate fail。 |
| REQ-PRM-01 | prompt interpretation は複数視点の解釈（scope/acceptance/risk/test/doc/escalation）を生成し、矛盾・曖昧さ・不足を PLAN 前段 finding にする。 |
| REQ-LRN-01 | detector finding / review finding / postmortem / test_result_event は learning candidate へ正規化され、Forward return か explicit discard reason を持つ。 |
| REQ-UPG-01 | upgrade-assist 駆動 PLAN は version_delta / impact_scope / rollback_condition / staged_gate / forward_return を必須にする。欠落は doc-contract violation。 |

## 2. 受入テスト設計（L3 ↔ L12 pair・対の検証）

| AT-ID | 受入シナリオ | 対応 REQ |
|---|---|---|
| AT-V3-01 | registry 外 `CREATE TABLE` を 1 つ追加 → static check が fail | REQ-SCH-01 |
| AT-V3-02 | cross-DB FK を宣言 → schema check が fail | REQ-SCH-03 |
| AT-V3-03 | 同一入力で rebuild 2 回 → DB diff が空 | REQ-PRJ-02 |
| AT-V3-04 | artifact 削除 → rebuild → 対応行が消える | REQ-PRJ-03 |
| AT-V3-05 | artifact 更新 → 古い投影が残らない | REQ-PRJ-04 |
| AT-V3-06 | DB から 1 件の「あるべき」を抜く → detector がもれを検出 | REQ-DET-01 |
| AT-V3-07 | 1 detector を fail させる → doctor 全体が fail（ok=AND） | REQ-DET-02 |
| AT-V3-08 | 配線していない detector を追加 → lint-wiring が fail | REQ-WIR-01 |
| AT-V3-09 | baseline を増やす変更 → ratchet が reject | REQ-RAT-01 |
| AT-V3-10 | frontmatter 契約違反 doc → detector が検出 | REQ-DOC-01 |
| AT-V3-11 | forward_return 欠落の駆動 PLAN → 検出 | REQ-DOC-02 |
| AT-V3-12 | UI-absent profile → FE detector が core gate を阻害しない | REQ-FE-01 |
| AT-V3-13 | `@~/.helix/core` パス参照 → 解決できる（公開 API 回帰なし） | REQ-DST-01 |
| AT-V3-14 | template_catalog に要求定義/基本設計/詳細設計/DB/画面/テスト仕様の template を登録 → doc_coverage が layer 別 gap を返す | REQ-TPL-01/02 |
| AT-V3-15 | 外部テンプレートに license_note 不明を登録 → human license review flag が立ち、自動採用を block | REQ-TPL-03 |
| AT-V3-16 | security review finding critical 未解決 → gate が fail。解決 evidence 追加 → pass | REQ-REV-01 |
| AT-V3-17 | prompt に認証/PII/本番影響を含める → interpretation loop が escalation finding を生成し auto-run 停止 | REQ-AUTO-02, REQ-PRM-01 |
| AT-V3-18 | finding を learning candidate 化するが forward_return 欠落 → reject。Forward L に戻すと登録 | REQ-LRN-01 |
| AT-V3-19 | upgrade-assist PLAN から rollback_condition を抜く → doc-contract detector が fail | REQ-UPG-01 |

## 3. トレース（FR → REQ → AT）

| FR | REQ | AT |
|---|---|---|
| FR-ENG-01 | REQ-SCH-01/02/03 | AT-01/02 |
| FR-ENG-02/03 | REQ-PRJ-01〜05 | AT-03/04/05 |
| FR-ENG-04/05 | REQ-DET-01/02/03 | AT-06/07 |
| FR-ENG-06 | REQ-WIR-01/02 | AT-08 |
| FR-ENG-07 | REQ-RAT-01/02 | AT-09 |
| FR-ENG-08 / FR-CFG-01 | REQ-DOC-01/02/03 | AT-10/11 |
| FR-FE-01 | REQ-FE-01 | AT-12 |
| FR-DST-01 | REQ-DST-01 | AT-13 |
| FR-HRN-01 | REQ-HRN-01 | （L4 で結合観点へ） |
| FR-AUTO-01/02 | REQ-AUTO-01/02 | AT-17 |
| FR-TPL-01/02/03 | REQ-TPL-01/02/03 | AT-14/15 |
| FR-REV-01 | REQ-REV-01 | AT-16 |
| FR-PRM-01 | REQ-PRM-01 | AT-17 |
| FR-LRN-01 | REQ-LRN-01 | AT-18 |
| FR-UPG-01 | REQ-UPG-01 | AT-19 |

## 4. 次工程

→ **L4 基本設計**（engine のテーブル群・projection rule・detector 分類を fork 抽出を反映して確定。総合テスト設計と対）。
