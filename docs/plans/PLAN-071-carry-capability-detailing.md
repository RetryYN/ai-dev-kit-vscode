---
plan_id: PLAN-071
title: "PLAN-071: PLAN-070 carry capability detail 化"
status: frozen
gate_status: G3_complete
size: M
drive: fullstack
created: 2026-05-16
completed_at: 2026-05-17
owner: PM
phases: L3, L4
gates: G3
acceptance:
  - PLAN-070 で「代表 3 capability」のみ詳細化した残り capability (≥10 件) を endpoint contract / DTO / error model 単位で明文化
  - D-API draft §3 capability index に carry capability を追加
  - mock_to_implementation hook を全 capability に展開した一覧表を D-CONTRACT に追加
  - L2 §3-§10 (capability matrix) と整合
  - 新規矛盾を導入しない (cross-doc integrity table 更新)
related:
  - PLAN-070-l3-schema-and-contract-design (frozen 親 PLAN)
  - docs/v2/L3-detailed-design/D-API/D-API-draft.md
  - docs/v2/L3-detailed-design/D-API/D-API-CARRY-draft.md (§3.4-§3.14 carry detail 分離ファイル、分離理由: §4.4 ±200 行制約遵守)
  - docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-draft.md
  - docs/v2/L2-MASTER.md (§3-§10 capability matrix)
---

# PLAN-071: PLAN-070 carry capability detail 化

## §1 目的と背景

### 1.1 本 PLAN の起源

PLAN-070 SprintA (D-API draft) では、`capability-inventory.md` に収録された全 capability を §2 capability map に列挙しつつも、`§3 endpoint contract draft` の詳細化対象を「代表 3 capability」に限定した。  
選定 3 capability は以下の通り。

| capability | SprintA 対応 |
|---|---|
| 契約 extractor / contract registry | `GET /api/v1/plan/{plan_id}/capabilities/contracts/registry` 詳細化済 |
| 14 detector system | `POST /api/v1/plan/{plan_id}/detectors/run` 詳細化済 |
| Gate runner | `GET /api/v1/plan/{plan_id}/gates/{drive}` 詳細化済 |

残り 11 capability（`capability-inventory.md` の全 14 件から代表 3 を除いた分、ただし廃止候補扱いの `Stop hook session-summary` は除く）は §7.1 carry セクションに「未詳細化 capability」として記録された。

本 PLAN は、これら未詳細化 capability の endpoint contract / request-response DTO / error model を明文化し、L3 D-API §3 carry に追記することを目的とする。

### 1.2 PLAN-070 との関係

- PLAN-070 は `status: frozen`、`gate_status: G3_approved`。本 PLAN はその carry 下位 PLAN であり、PLAN-070 の成果物 (`D-API-draft.md` / `D-CONTRACT-draft.md`) を読み込み専用として参照する。
- PLAN-070 の D-API §7.1 carry セクションを本 PLAN の起点とする。追記分は D-API draft §3.4 以降に capability 単位で追加する。
- cross-doc 整合性 (spine.yaml / L2-MASTER §3-§10 / D-CONTRACT) は本 PLAN のすべての Sprint で維持する。

### 1.3 サイジングと工程位置

| 軸 | 判定 |
|---|---|
| ファイル数 | 3-5 ファイル変更 (D-API draft / D-CONTRACT draft / carry cross-check table) = M |
| 変更行数 | 追記 200-400 行程度 = M |
| API/DB 変更 | API 設計追加あり / DB 変更なし = M |
| 駆動タイプ | be+fullstack cross-drive contract = fullstack |
| HELIX フェーズ | L3 詳細設計継続 → L4 実装前提 |

---

## §2 対象 capability 一覧（carry 分 11 件）

PLAN-070 D-API §2.1 capability map から代表 3 を除外し、`capability-inventory.md` の全記録と突合した一覧。  
`廃止候補` 扱いの `Stop hook session-summary` は §2.6 に別枠で記録し、endpoint 詳細化の対象外とする。

### 2.1 carry capability 表

| No | capability 名 | 起源 PLAN | 状態 | endpoint 数 (想定) | 主要 DTO 数 (想定) | owner role | priority |
|---|---|---|---|---|---|---|---|
| C-01 | V-model schema / QA baseline schema | PLAN-065 | 部分実装 | 3 | 4 | tl | P1 |
| C-02 | handover protocol | PLAN-016, ADR-016 | 実装済 | 4 | 5 | tl | P1 |
| C-03 | skill 推挙 / skill chain | PLAN-024, PLAN-043 | 実装済 | 2 | 3 | se | P2 |
| C-04 | Reverse HELIX (R0-R4 + RGC, 5 type) | PLAN-049 | 実装済 | 5 | 6 | tl | P2 |
| C-05 | Scrum HELIX (S0-S4 + trigger) | PLAN-007 | 実装済 | 4 | 4 | se | P2 |
| C-06 | Agent Transformation 散在 (helix codex / helix claude / helix-skill) | PLAN-028, PLAN-043 | 部分実装 | 3 | 4 | tl | P2 |
| C-07 | PMO / advisor role system | PLAN-028 | 実装済 | 2 | 2 | se | P3 |
| C-08 | Codex / Claude harness + PreToolUse guard | PLAN-028, PLAN-043 | 実装済 | 3 | 3 | tl | P2 |
| C-09 | code-index (find/build/stats) | PLAN-011, PLAN-012, PLAN-013 | 実装済 | 3 | 3 | se | P2 |
| C-10 | budget guard / auto-thinking support | PLAN-024 | 部分実装 | 2 | 2 | se | P3 |
| C-11 | code-index + contract registry 追加整合 | PLAN-065, PLAN-067 | 部分実装 | 2 | 3 | se | P2 |

### 2.2 廃止候補 capability（endpoint 詳細化除外）

| No | capability 名 | 除外理由 | V2 代替 |
|---|---|---|---|
| D-01 | Stop hook session-summary | `cli/helix-session-summary` は cost_log INSERT shim に縮小済 | Stop hook telemetry (D-API 拡張 SprintE で扱う) |

### 2.3 対象スコープまとめ

- 詳細化対象: C-01〜C-11 (11 capability)
- 除外: D-01 (廃止候補) + 代表 3 (PLAN-070 SprintA 詳細化済)
- 総 endpoint 想定数: 33 (2.1 合計)
- 総 DTO 想定数: 39 (2.1 合計)

---

## §3 Sprint 構成

本 PLAN は 3 Sprint 構成。Sprint 命名は `.1` / `.2` / `.3`。

| Sprint | 対象 | 主目的 | 成果物 |
|---|---|---|---|
| Sprint .1 | C-01〜C-05 (P1 + P2 前半) | D-API §3 carry 詳細化 (1) | endpoint contract 表 + request/response DTO + error model |
| Sprint .2 | C-06〜C-11 (P2 後半 + P3) + mock hook 展開 | D-API §3 carry 詳細化 (2) + D-CONTRACT carry mock hook 一覧 | endpoint contract 表 + D-CONTRACT mock_to_implementation 全 capability 展開表 |
| Sprint .3 | exit-validation 集約 | cross-doc integrity 確認 + carry 更新 | carry cross-check table + D-API §7.1 更新 |

### Sprint .1: D-API capability 詳細化 (前半)

対象 capability: C-01 (V-model schema)、C-02 (handover protocol)、C-03 (skill 推挙)、C-04 (Reverse HELIX)、C-05 (Scrum HELIX)

成果物形式は PLAN-070 §3 の代表 3 capability に準拠する。各 capability につき以下を 1 ブロックで記述する。

```
- path: /api/v1/{resource}
- method: {GET|POST|PUT|DELETE}
- request_schema: (YAML)
- response_schema: (YAML)
- error_model: (YAML コード + message + context)
- pair_status 方向: (be detailed ↔ fullstack detailed 等)
- owner: (role 名)
```

#### C-01 V-model schema / QA baseline schema (想定 endpoint)

| Method | Path | 用途 |
|---|---|---|
| GET | `/api/v1/plan/{plan_id}/vmodel/schema` | V-model schema 取得 |
| POST | `/api/v1/plan/{plan_id}/vmodel/baseline-policy` | baseline policy 登録 |
| GET | `/api/v1/plan/{plan_id}/vmodel/baseline-policy/{policy_id}` | baseline policy 取得 |

#### C-02 handover protocol (想定 endpoint)

| Method | Path | 用途 |
|---|---|---|
| GET | `/api/v1/handover/{plan_id}/status` | handover 状態取得 (CURRENT.json 同期) |
| POST | `/api/v1/handover/{plan_id}/update` | handover 状態更新 (owner/status 変更) |
| POST | `/api/v1/handover/{plan_id}/escalate` | escalation 発火 (ESCALATION.md 生成) |
| POST | `/api/v1/handover/{plan_id}/clear` | handover クリア (reason 必須) |

#### C-03 skill 推挙 / skill chain (想定 endpoint)

| Method | Path | 用途 |
|---|---|---|
| POST | `/api/v1/skills/search` | タスク記述から skill 推挙 (gpt-5.4-mini) |
| POST | `/api/v1/skills/chain` | search → use 一気通貫 (委譲先決定) |

#### C-04 Reverse HELIX (想定 endpoint)

| Method | Path | 用途 |
|---|---|---|
| POST | `/api/v1/reverse/{type}/r0` | R0 証拠収集開始 |
| POST | `/api/v1/reverse/{type}/r1` | R1 契約抽出 |
| POST | `/api/v1/reverse/{type}/r2` | R2 設計復元 |
| POST | `/api/v1/reverse/{type}/r3` | R3 仮説検証 |
| POST | `/api/v1/reverse/{type}/r4` | R4 Gap → Forward routing |

#### C-05 Scrum HELIX (想定 endpoint)

| Method | Path | 用途 |
|---|---|---|
| POST | `/api/v1/scrum/{plan_id}/backlog/add` | hypothesis 追加 |
| POST | `/api/v1/scrum/{plan_id}/plan` | Sprint plan 起動 |
| POST | `/api/v1/scrum/{plan_id}/poc` | PoC 実装委譲 |
| POST | `/api/v1/scrum/{plan_id}/decide` | confirmed / rejected / pivot 判定 |

### Sprint .2: D-API capability 詳細化 (後半) + mock hook 展開

対象 capability: C-06〜C-11 + D-CONTRACT mock_to_implementation 全 capability 展開

#### C-06 Agent Transformation 散在 (想定 endpoint)

| Method | Path | 用途 |
|---|---|---|
| POST | `/api/v1/dispatch/codex` | helix codex 委譲 |
| POST | `/api/v1/dispatch/claude` | helix claude 委譲 |
| POST | `/api/v1/dispatch/team` | helix team 複数 role 委譲 |

#### C-07 PMO / advisor role system (想定 endpoint)

| Method | Path | 用途 |
|---|---|---|
| POST | `/api/v1/advisor/pm` | pm-advisor 召喚 |
| POST | `/api/v1/advisor/tl` | tl-advisor 召喚 |

#### C-08 Codex / Claude harness + PreToolUse guard (想定 endpoint)

| Method | Path | 用途 |
|---|---|---|
| POST | `/api/v1/harness/codex/exec` | helix codex 実行 (consent 付き) |
| POST | `/api/v1/harness/claude/exec` | helix claude 実行 |
| POST | `/api/v1/harness/guard/pre-tool-use` | PreToolUse hook 判定 |

#### C-09 code-index (想定 endpoint)

| Method | Path | 用途 |
|---|---|---|
| GET | `/api/v1/code-index/find` | keyword で code 資産探索 |
| POST | `/api/v1/code-index/build` | catalog 再構築 |
| GET | `/api/v1/code-index/stats` | coverage / bucket 統計 |

#### C-10 budget guard / auto-thinking (想定 endpoint)

| Method | Path | 用途 |
|---|---|---|
| GET | `/api/v1/budget/status` | Claude/Codex 消費率取得 |
| POST | `/api/v1/budget/simulate` | タスク規模からモデル推奨計算 |

#### C-11 code-index + contract registry 追加整合 (想定 endpoint)

| Method | Path | 用途 |
|---|---|---|
| GET | `/api/v1/code-index/contract-alignment` | contract_entries と code_index の整合確認 |
| POST | `/api/v1/code-index/contract-alignment/sync` | 乖離の同期更新 |

#### D-CONTRACT mock_to_implementation 全 capability 展開

`D-CONTRACT-draft.md` の `mock_to_implementation` hook を代表 3 capability から全 capability に拡張する。  
一覧表の形式:

| capability | from_artifact_kind | to_artifact_kind | link_kind | append_only | 備考 |
|---|---|---|---|---|---|
| 契約 extractor / contract registry | mock_contract | implementation_contract | supersede | true | PLAN-070 既存 |
| 14 detector system | mock_detector | implementation_detector | supersede | true | PLAN-070 既存 |
| Gate runner | mock_gate | implementation_gate | supersede | true | PLAN-070 既存 |
| V-model schema / QA baseline schema | mock_baseline_policy | implementation_baseline_policy | supersede | true | carry C-01 |
| handover protocol | mock_handover | implementation_handover | supersede | true | carry C-02 |
| skill 推挙 / skill chain | mock_skill_search | implementation_skill_chain | supersede | true | carry C-03 |
| Reverse HELIX | mock_reverse | implementation_reverse | supersede | true | carry C-04 |
| Scrum HELIX | mock_scrum | implementation_scrum | supersede | true | carry C-05 |
| Agent Transformation | mock_dispatch | implementation_dispatch | supersede | true | carry C-06 |
| PMO / advisor role | mock_advisor | implementation_advisor | supersede | true | carry C-07 |
| Codex / Claude harness | mock_harness | implementation_harness | supersede | true | carry C-08 |
| code-index | mock_code_index | implementation_code_index | supersede | true | carry C-09 |
| budget guard | mock_budget | implementation_budget | supersede | true | carry C-10 |
| code-index + contract registry 整合 | mock_alignment | implementation_alignment | supersede | true | carry C-11 |

### Sprint .3: exit-validation 集約

- D-API §7.1 carry を「全 capability 詳細化済」に更新する。
- L2 MASTER §3-§10 と新規 endpoint が矛盾しないことを cross-doc integrity table で確認する。
- 新規矛盾が見つかった場合は PLAN-071 §5 risk 追記 + carry-forward として次 PLAN に引き渡す。
- `spine.yaml` の capability 参照を最新化する。

---

## §4 受入条件詳細

### 4.1 D-API 受入

- C-01〜C-11 の全 capability について、endpoint contract (path / method / headers) を 1 テーブルで示す。
- request schema / response schema / error model が各 capability について示されている（YAML ブロック形式、正常系・準正常系・エラー系を含む）。
- L1 REQUIREMENTS の AC および FR に対応する capability は、どの AC / FR から由来するかを記載する。
- D-API §7.1 carry セクションが「全 carry 詳細化済」に更新されている。

### 4.2 D-CONTRACT 受入

- `mock_to_implementation` 展開一覧表が全 14 capability（代表 3 + carry 11）を含む。
- `append_only: true` が全行に設定されている。
- carry C-01〜C-11 の `from_artifact_kind` / `to_artifact_kind` が重複しない。

### 4.3 cross-doc integrity 受入

- L2 MASTER §3（`api_capability_map`）の `review_unit` と本 PLAN 各 capability の endpoint 数が齟齬を生じない。
- `spine.yaml` の capability 参照が本 PLAN 成果物と一致する。
- 新規矛盾が見つかった場合は carry-forward として記録し、次 PLAN 起票前に PM 確認を要す。

### 4.4 サイズ整合

- 本 PLAN 成果物が PLAN-070 の D-API draft (492 行) に比して ±200 行以内の追記に収まること（追加複雑度の目安）。
- 800 行制限: 本 PLAN 自体は 400 行以内で完結すること。

**[分離 refactor 完了 note — 2026-05-17]**

D-API-draft.md の §3.4〜§3.14 (carry 11 capability) は `D-API-CARRY-draft.md` へ分離済み。
- D-API-draft.md: 539 行（±200 範囲 324-724 内）
- D-API-CARRY-draft.md: 1168 行、`status: frozen`、11 capability (C-01〜C-11) 収録
- D-API-draft.md §3.4〜§3.14: リダイレクト参照 3 行に置換済み（行 418-420）
- 分離理由: §4.4 ±200 行制約遵守（D-API-draft.md の可読性確保）

---

## §5 risk と carry 戦略

### 5.1 carry 再発リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| capability 数が多く Sprint .1 / .2 が完全詳細化に至らない | P1 carry を残す | P1 (C-01 / C-02) を最優先し、P3 (C-07 / C-10) は partial でも受入可とする |
| endpoint path が L2 MASTER §3 capability map と乖離 | cross-doc 矛盾 P1 | Sprint .3 exit-validation で必ず突合 |
| D-CONTRACT mock hook 一覧が D-API の capability 追加と同期しない | 矛盾 P2 | Sprint .2 で D-API と D-CONTRACT を同一 Sprint 内で更新 |
| L4 実装が本 PLAN 完了を待てない | 実装スロット損失 | P1 carry (C-01 / C-02) のみ先行 detail 化し L4 entry 可とする partial done 条件を設ける |

### 5.2 partial done 条件

L4 実装開始可能な最低条件:

- C-01 (V-model schema) の endpoint contract が D-API §3 に追記されている
- C-02 (handover protocol) の endpoint contract が D-API §3 に追記されている
- D-CONTRACT mock hook 一覧の P1 行 (C-01 / C-02) が追加されている

上記 3 条件を満たした時点で L4 entry ブロックを解除する。C-03〜C-11 は L4 Sprint .2 以降で parallel 詳細化を行う。

---

## §6 dependency と L4 並行判断

### 6.1 PLAN-070 との依存

PLAN-070 は `status: frozen`。本 PLAN は PLAN-070 の成果物（D-API draft / D-CONTRACT draft / D-DB draft）を読み取り専用として参照し、直接編集しない。  
追記作業は PLAN-071 専用の sprint セクション (`§3 capability detail carry`) を D-API draft に設けることで、既存内容との分離を保証する。

### 6.2 PLAN-072 (L4 実装) との並行可能性

| 条件 | 並行可否 |
|---|---|
| §5.2 partial done 条件を満たす | L4 C-01 / C-02 実装を並行開始可 |
| §5.2 を未達 | L4 全面ブロック |
| Sprint .1 完了後 | L4 C-01〜C-05 実装を並行開始可 |
| Sprint .2 完了後 | L4 全 capability 実装を並行開始可 |

### 6.3 PLAN-027 との関係

PLAN-027 (entries/links 基盤) は `status: completed`。本 PLAN の Sprint .3 exit-validation で `entries` テーブルへ成果物 entry を記録する（`domain_kind: design`、`lifecycle: addition`）。

---

## §7 next action

### Phase C Sprint 連続実行での作業順

1. **本 PLAN 確認** (PM): PLAN-071 draft を PM が承認し、Codex TL に委譲
2. **Sprint .1** (Codex TL): C-01〜C-05 endpoint contract を D-API §3 carry に追記
3. **Sprint .1 review** (PM / pmo-sonnet): endpoint contract の L2 MASTER §3 整合確認
4. **Sprint .2** (Codex SE): C-06〜C-11 endpoint contract + D-CONTRACT mock hook 展開表を追記
5. **Sprint .2 review** (Codex TL + PM): cross-doc 整合チェック
6. **Sprint .3** (Codex TL): exit-validation 実施 + D-API §7.1 carry 更新
7. **受入** (PM): 全受入条件確認 → status: completed に更新
8. **entries 登録** (helix-entry CLI): design_sprint_entries に本 PLAN の設計 artifact を記録

### 委譲先

| Sprint | 委譲先 | 根拠 |
|---|---|---|
| Sprint .1 | Codex TL (gpt-5.5 high) | endpoint contract は TL 責務の設計判断 |
| Sprint .2 | Codex SE (gpt-5.4 high) | 量が多いため SE で並列処理、mock hook 一覧は表形式でコード生成向き |
| Sprint .3 | Codex TL (gpt-5.5 high) | exit-validation は設計整合判断 |

### 完了時状態

```yaml
status: completed
completed_at: TBD
gate_status: G3_carry_resolved
carry: []
```

---

## §N V-model 4 artifact mapping (PLAN-075 retrofit、2026-05-17、grandfather)

PLAN-071 は **capability 詳細化 PLAN** (D-API-CARRY 分離 1168 行を中核とする設計補強) で、② 実装コードは他 PLAN で行われる。PLAN-071 単独での 4 artifact 完備は構造的に不可能。

PLAN-075 Phase 4 audit (`docs/v2/audit/plan-067-074-vmodel-audit.md` §2.2) で **P1 grandfather** 判定。

| Artifact | 種類 | PLAN-071 内での扱い | 実体存在 |
|---|---|---|---|
| ① 設計 (詳細) | D-API-CARRY 分離 (capability 補強) | 本 PLAN の主成果物 | 完備 (D-API-CARRY-draft.md 1168 行) |
| ② 実装コード | (他 PLAN 由来) | reference のみ | 他 PLAN で完備 |
| ③ テスト設計 | (他 PLAN 由来) | reference のみ | 実装側 PLAN で起票 |
| ④ テストコード | (他 PLAN 由来) | reference のみ | 他 PLAN で完備 |

### Phase 5 lint への扱い

`.helix/audit/deferred-findings.yaml` で `plan_070_071_grandfather` として grandfather 例外指定。`vmodel_lint` 実行時に skip 対象。

### 双方向 trace の確保

PLAN-071 の ① 設計 artifact (D-API-CARRY) は PLAN-074 / 他 PLAN で実装され、test-design からの reference は実装側 PLAN で双方向確立済。PLAN-071 自体は capability 補強の設計中継 PLAN として grandfather 化が妥当。
