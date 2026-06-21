---
doc_id: db-auto-registration
title: HELIX DB 自動登録機構
status: accepted
implementation_status: design_resolved_impl_pending  # 2026-06-21 design-review: 設計判断は「F1 設計確定」節(F1-1〜F1-5)で確定済、実装は未(Reverse→Add-feature)。下記「実装状態」known_gap は実装の残を示す。status:accepted は設計受理であって全イベント実装完了ではない。
design_review: ../../docs/research/2026-06-21-no-leak-foundation-design-review.md  # §1 cluster A で現状確認、F1 設計確定を本書「F1 設計確定」節に格納、実装 closure=F1(Reverse→Add-feature)
accepted_date: 2026-05-24
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
integration_target:
  docs_path: docs/architecture
  category: 管理・自動化基盤
---

# HELIX DB 自動登録機構

## 概要

PLAN・成果物・コード・テスト・スコアを、イベント駆動で helix_db に自動登録する仕組み。手動登録を排し、Vモデル成果物の一致管理（db-integration.md）の前提を自動で満たす。

## 登録イベントと hook

既存の hook を、登録イベントとして体系化する。

| イベント | hook | 登録対象 |
|---|---|---|
| PLAN 起票 | plan_registry.bulk_import | PLAN（kind / generates / requires） |
| コード変更 | code_catalog | AST → FTS5 インデックス |
| Codex 実行後 | codex_post_hook | 精度スコア（accuracy dimensions） |
| ゲート通過後 | feedback_hook | 5軸フィードバック（Lv1–5） |
| セッション停止 | stop-hook | handover dump（状態保全） |

## 実装状態（2026-06-21 design-review honest-mark）

> 本 doc は設計意図（target）であり、実装は**部分**。design-review（[no-leak foundation](../../docs/research/2026-06-21-no-leak-foundation-design-review.md) §1 cluster A）で確認した現状を honest に記す。**`status: accepted` は設計意図の受理**であって全イベントの実装完了を意味しない（誤読防止）。

| イベント（上表） | 実装状態 | known_gap |
|---|---|---|
| PLAN 起票 → plan_registry | **実装済** | `posttooluse-plan-auto-register.sh` → plan_parser upsert（5 テーブル） |
| コード変更 → code_catalog | **未実装（自動 trigger 不在）** | `helix code rebuild` の手動実行のみ。.py/.sh/test を書いても code_index は更新されない（`code_catalog.py:912`）。SKILL.md だけは PostToolUse hook が rebuild |
| Codex 実行後 → 精度スコア | **条件付き実装**（`helix codex` 経由のみ） | raw CLI 経由では発火しない |
| ゲート通過後 → feedback | **条件付き実装**（`helix gate` 経由のみ） | gate コマンド非経由では発火しない |
| セッション停止 → handover dump | **未配線** | `handover_auto_dump.py` 実装はあるが `stop.sh` から未呼出 |
| generates 宣言 → 自動反映（設計方針） | **未実装** | `plan_generates` に登録 + 存在チェック advisory はあるが、生成→code_catalog/doc 自動反映は無い |

**planned_closure**: F1（登録自動化 + 設計定義の構造化登録）。駆動 = **Reverse（設計-実装乖離の記録）→ Add-feature（実装）**（TL 推奨）。GOAL-C-RIGHTARM-FULLCLOSE 着地後に起票（add-feature count-pin 回避）。closure までは本 doc を target spec として扱い、各イベントを implemented と誤読しない。

## 自動登録フロー

```
イベント発火（起票 / commit / gate pass / Codex 実行 / stop）
   → hook 起動
   → helix_db へ登録（plan_registry / code_catalog / contract_registry / skill_catalog）
   → catalog / registry 更新
```

## F1 設計確定（2026-06-21 design-review 補正）

> 本節は [no-leak foundation design-review](../../docs/research/2026-06-21-no-leak-foundation-design-review.md) の **F1（登録自動化）** が指摘した「target spec はあるが設計判断が未確定」を、**設計レベルで確定**する。上の「実装状態」known_gap 各行に対応する。実装は **Reverse（設計-実装乖離の記録）→ Add-feature**、物理 schema は CLAUDE.md「推測 schema 回避」に従い**登録要求が detector で観測されてから**確定する（先行 schema を作らない）。本機構は G-tier（全 project 配布）であり、本書を設計 SSoT とし、V2 L4-L6（dogfooding 設計）は本書を**参照**して再宣言しない（G-P drift 回避）。

### F1-1 トリガ契約（known_gap「code 変更 → code_catalog 自動 trigger 不在」の設計確定）

登録は「人が DB に書く」でなく「**イベントが hook を起動して増分登録する**」に統一する。これは新規発明でなく、**実証済みパターンの横展開**である（`posttooluse-plan-auto-register.sh`＝PLAN→plan_registry、`posttooluse-skill-catalog-rebuild.sh`＝SKILL.md→skill_catalog が稼働済）。同じ PostToolUse hook 機構を code/test/設計 doc へ拡張する。

| イベント（Edit/Write 対象） | トリガ hook | 登録動作 |
|---|---|---|
| `cli/**/*.py`, `cli/**/*.sh`（tests 除く） | code 登録 hook（新規） | code_catalog の**該当ファイル増分** rebuild |
| `cli/**/tests/**`, `cli/tests/**` | test 登録 hook（新規） | test 索引の増分更新 |
| `docs/v2/L6-*/**.md`（機能設計） | 設計定義登録 hook（新規） | FN-ID + DbC を構造化登録（F1-3） |
| `cli/config/functional-registry.yaml` | view 同期 hook（新規） | md view 再生成（F1-2） |

- **increment vs full**: トリガは**該当ファイル単位の増分**を既定（write ごと全 rebuild は高コスト）。full rebuild は on-demand（`helix code rebuild`）と CI 定期に限定。増分 key / 冪等性は実装時（L5 相当）に確定。
- **失敗時**: 登録 hook 失敗は **advisory（write を止めない）** を既定とし、未登録分は `source_scan_vs_registry` detector が後段 fail-close で拾う**二段構え**（hook 失敗で開発を止めない / 漏れは検出される）。

### F1-2 SSoT 一本化（known_gap「functional-registry 二重手動」の設計確定）

- **正本（machine SSoT）**: `cli/config/functional-registry.yaml`（現 577 entries、detector が読む）。
- **派生 view**: `docs/v2/L3-requirements/helix-workflows-functional-registry.md` は yaml から**生成**する read-only view とし、**手編集しない**。
- **同期方向**: yaml → md（生成のみ）。md → yaml の手動反映は**廃止**（二重手動の根絶＝編集点を yaml 1 箇所に）。
- 移行: 既存 md の手書き差分は一度 yaml へ吸収（Reverse で乖離記録）後、md を generated view へ切替。

### F1-3 設計定義の登録（known_gap「設計定義（DbC/FN-spec/MOD/NFR）未登録」の設計確定）

- 登録単位を「**ID 行**」から「**定義内容**」へ拡張する。現状 `design_id_existence` detector は L6 doc の実在を検査するが、DbC（requires/ensures/invariant）本文・FN-spec の中身は DB 非構造化＝定義の機械証明が ID 実在止まり。
- 登録対象（**境界のみ固定**）: L6 機能設計 doc の **FN-ID ↔ DbC 三要素 ↔ source 関数** の対応。
- **物理 schema は defer**: CLAUDE.md「DB 拡張は永続化要求が観測されてから schema 確定」に従い、本書は**登録対象と粒度**のみ固定。テーブル列・正規化は登録要求が detector で観測されてから確定する。

### F1-4 generates 反映（known_gap「generates 宣言 → 自動反映 未実装」の設計確定）

- PLAN frontmatter の `generates`（artifact_path）で宣言した成果物が生成されたら、F1-1 表の対象種別に従って code_catalog / design_def 登録へ**自動反映**する（現状は `plan_generates` 存在チェック advisory 止まり）。

### F1-5 検証（自動登録が満たすべき条件＝実装時の合格基準）

| 観点 | 合格条件 |
|---|---|
| code 増分登録 | 新規 .py を write → 該当 hook 発火 → code_catalog に当該 module/関数が現れる |
| SSoT 単一性 | yaml 編集 → md view 再生成で一致。md 手編集は view 差分として検出される |
| 設計定義登録 | L6 doc に FN + DbC 追加 → design_def 登録に当該 FN の三要素対応が現れる |
| coverage 前提 | 上記登録後、whole-source ⊆ design の unknown=0 / orphan=0 が**追加手作業なし**で保たれる |
| 失敗時二段構え | 登録 hook を意図的に失敗させても write は通り、`source_scan_vs_registry` が後段で未登録を検出する |

> **F1 税の実証（本設計の動機）**: design-review 中、F3 detector 追加・add-feature PLAN 起票・本 F1 設計 doc の V2 登録 のいずれも、count-pin / objective audit / 設計 asset inventory への**手動同期**を要し、設計 doc 1 本の登録が audit lattice 全体へ波及した。この税こそ F1 が機械化すべき対象であり、F1 完了までは新規登録に手動コストが残る（= foundation-first の定量根拠）。

## 設計方針

- 登録は「人が DB に書く」のではなく「イベントが hook を起動して書く」形に統一する。
- 各モードの逸脱 PLAN（reverse / poc / recovery 等）も、起票時に plan_registry へ自動取り込みする（deviation-plan-map.md）。
- generates で宣言した成果物が生成されたら、code_catalog / doc に自動反映する。

## 効果

- 手動登録漏れを排除し、DB が常に最新の成果物・スコアを保持する。
- db-integration の一致管理（doc ⇔ code ⇔ test ⇔ coverage）と drift 検出の前提が、追加作業なしで揃う。
- 自動登録で充実した DB が、次の「検出 → モード連携」（detection-routing.md）の入力になる。
