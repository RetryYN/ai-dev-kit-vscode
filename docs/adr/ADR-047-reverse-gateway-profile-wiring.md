---
adr_id: ADR-047
title: "Reverse Gateway Profile for Non-Forward Modes (V-model wiring unification)"
status: Proposed
author: PM
owner: PM
created: 2026-05-28
parent_plan: L0-helix-workflows-conceptplan
process_layer: L1
related_design: HELIX-workflows/HELIX-process-L0-L14.md
sibling_adr:
  - ADR-041 (drift type routing, amend 対象)
  - ADR-042 (recommended command, amend 対象)
  - ADR-044 (V2 architecture)
  - ADR-045 (F6-F10 governance)
industry_standards:
  - IEEE 42010:2022 (Architecture Description)
  - V-model (ISO/IEC/IEEE 29148 + 26515)
  - arc42 §9 Design Decisions
  - DDD Bounded Context / Anti-Corruption Layer
  - SDLC Phase Gate
---

# ADR-047: Reverse Gateway Profile for Non-Forward Modes (V-model wiring unification)

## Context

### ユーザー要求（2026-05-28）

- Reverse は V モデル統一ゲートウェイであり、Forward 接続前にプロファイル的に整流することを全体方針として扱うこと。
- 非 Forward 系 9 mode のうち、既存 workflow のみでは Scrum / Incident の明示配線が Reverse 経由であり、他 6 mode は Forward 接続が直接記述されるため、運用ごとに接続語彙が分断されている。
- 配線分断が、`drift` 系の設計トレース、`recommended_command` 系の解釈、Incident/Recovery の例外処理、Research 参照条件の扱いを混在させ、`profile` としての共通言語を阻害している。
- 9 Non-Forward mode の中での接続不一致を、mode 名や signal 名の違いではなく、**profile** による統一的接続契約へ集約したい。

### 既存 ADR 間の前提

- ADR-044 は V2 全体構造の freeze を持つため、接続構造変更は ADR で snapshot 化する必要がある。
- ADR-045 は F6–F10 のガバナンススナップショットであり、追加判断は sibling 関係を明示して追補運用で管理するのが妥当である。
- ADR-041 は drift type 直接分岐を定義しているが、Mode が増えた段階では profile ベースの解釈レイヤを上に載せる必要がある。
- ADR-042 は `recommended_command` の単一構造を定義しているため、複数フェーズ接続を加える場合も破壊的変更は避けなければならない。
- HELIX-workflows V2 の `other modes` 経路は mode と phase が増えるほど複雑化し、`fork pattern` に対する `profile` 的直観が必要になっている。

### 現行実装の要点（`cli/lib/route_engine.py`）

- `route_engine` は `signal -> {mode,kind,subtype}` を先に決め、`drift` 時のみ `drift_type` を上書きする構造。
- `recommended_command` は v1 形式で 1 要素（単一コマンド）として返され、mode と signal の橋渡しを担保する最小データのみを返却している。
- `DRIFT_TYPE_TO_ROUTE` は ADR-041 の原型ルールに近いが、Forward 接続前の profile ステートを表現しきれていない。
- `signal == incident` は env 条件で recovery/troubleshoot を切り替えており、mode 別の mode profile を持つべき層がまだ薄い。
- 現状で `mode=Reverse` 直結と `mode=Forward` 直結（`route_to_next` 前提）が混在し、`doc` ベースの trace で逆方向接続が見えづらい。

### ユーザー追加訂正（本 ADR 反映条件）

1. mode 数は 10（Forward + 9 Non-Forward）で扱う。  
2. Research は参照 doc 体系（既存資産確認）経由時のみ Reverse gateway を通し、机上作業のみは直接 L1 / L4 ADR 接続も許容する。  
3. fork pattern は profile ベースで解釈する。  
4. HELIX W は設計論カテゴリにする（mode カテゴリ外）。  

### 重大な検討結果

- tl-advisor 的見取り（R1 で提示）として「全 mode を機械的に Reverse 接続」すると ADR-041 / ADR-042 と衝突する。  
- Incident/Recovery の即時停止を Reverse 化しない判断も必要で、同時に recommended_command の単一性も保つ必要がある。  
- 従って `Reverse Gateway Profile` が、mode/phase と Forward 接続の間に入ることが必要になる。

## 1.1 Reverse Gateway Profile が必要な理由

### 1.1.1 目的（Operational）

- mode 判定後に同一形式で Forward 接続を受けるための中間表現が必要。
- L0-L14 の workflow 経路を「Direct-to-Forward」から「Gateway-to-Forward」に統一し、SSoT で trace 可能にする。
- `profile` を明示することで、同じ mode でも状況ごとに異なる接続深度（fullback/normalization-lite/conditional など）を安全に表現する。

### 1.1.2 目的（Governance）

- 既存 ADR をいきなり破壊しないために、profile を additive layer として加える。
- 破壊的なルート再定義を避け、`status: Proposed` の状態では既存運用を停止しない。
- 逆引きトレース（ADR-041 / ADR-045 / ADR-044）を維持しつつ、`profile` で mode の実体差分を吸収する。

### 1.1.3 目的（開発流）

- `route_engine` が返す型を拡張するとき、まず ADR で仕様を凍結し、その後 Wave 6 で実装に反映する運用を取れる。
- `profile` 単位で実施順を決めることで、実装順序と検証順序を wave で明示しやすい。

### 1.1.4 目的（フォールトトレランス）

- Incident/Recovery は緊急停止文脈を優先し、`profile` ベースで「skip / post / emergency」などを明示する。
- これにより `recommended_command` は従来の即時停止性を壊さない。
- `profile` があることで、停止優先 route と fullback route の差分を文書化しやすい。

## 1.2 mode 系統分類 (3 系統 + 設計論)

### 1.2.1 3系統の分類

#### A. 必須 profile 系（Reverse gateway 必須）

- Scrum
- Discovery
- Add-feature
- Retrofit

上記 4 mode は、Reverse Gateway Profile を通すことを前提とする。

#### B. 事後 profile 系（収束後のみ）

- Incident
- Recovery

上記 2 mode は、緊急停止中は Reverse gateway をスキップし、収束後に fullback profile を経由する。

#### C. 条件 profile 系（条件付き）

- Refactor
- Research

上記 2 mode は、既定では軽量経路（lite）を採用し、条件成立時に normalization を実施する。

#### D. 設計論特殊系

- HELIX W（設計論カテゴリ）
- Phase 1/Phase 2 は profile 変遷（fullback → normalization）を取るが、mode category には含めない。

### 1.2.2 mode 数の明確化

- 合計 10 mode という定義を採用する（Forward + 9 Non-Forward）。
- 本 ADR は Non-Forward 9 mode を対象に profile を定義し、Forward は gateway 外の既存接続として扱う。

### 1.2.3 プロファイル辞書

本 ADR では以下を `profile` 名として採用する。

- `fullback`  
  - まず逆方向の現象と履歴を収束し、Forward へ再接続する profile
  - 実装後に追記される情報を取り込む profile
- `normalization-lite`  
  - 挙動不変を保つ前提で軽量に同期する profile
  - 追加コストを最小化する profile
- `normalization`  
  - 設計 trace を再整備し、既存資産との齟齬を修正する profile
  - 変更量が大きくなる profile
- `conditional`  
  - 条件満たした場合のみ Reverse に入る profile
  - 机上検討や参照 doc 系では pass-through しやすい profile
- `fullback-post-recovery`  
  - Recovery 後、安定化を確認してから行う profile
- `fullback-post-hotfix`  
  - Incident 後、hotfix 収束を確認してから行う profile

### 1.2.4 profile の状態遷移規約

- `profile` は mode 固有で保存し、mode 追加時にのみ更新する。  
- `required` は mode entry 時点、`conditional` は評価条件時点、`post` は収束条件時点で選択する。  
- `mode profile` と `forward_target` の対応は `route_engine` 契約拡張で明示する。  
- Forward 接続は `recommended_pipeline` により `suggested path` として扱う（ADR-042 の backward compat を維持）。

## 1.3 業界標準対応 (V-model / arc42 / DDD ACL / SDLC Phase Gate)

### 1.3.1 V-model trace

- ADR を起点にして backward profile（設計側）と forward profile（実装側）を一対一で確認する。
- この ADR では profile を trace の中間語彙として定義し、L1-L4 と L8-L14 のペアで確認しやすい形にする。

### 1.3.2 arc42 §9 Design Decisions

- 設計判断（何故この profile か）を本文の Main Decision と Sub-Decision に分離。
- 代替案（全モード Reverse / 全 mode skip / direct keep）は破綻条件を明記して棄却。
- 変更影響は `Consequences` で positive / negative / neutral の区分として固定。

### 1.3.3 DDD Bounded Context / ACL

- `profile` は gateway context の anti-corruption boundary として扱い、mode の生データを直接 forward が消費しない。
- Legacy contract と新契約の間は ACL（互換 layer）を明示して additive で渡す。
- Forward への接続は `recommended_pipeline` を介して行い、既存 `suggest_command` の意味を保全する。

### 1.3.4 SDLC Phase Gate

- G2/G3 以前の設計凍結と実装開始ゲートの整合を保つため、status: Proposed の間は実装しない運用を維持する。
- Wave 6-8 で route_engine / workflow doc / 検証の順に進めることで段階ゲートを満たす。
- BR-09 / BR-10 / BR-11 / BR-12 を ADR 内で同時検証し、Phase Gate に沿った evidence を残す。

## 現状ワークフロー接続路の観測

### 現行接続の簡易マッピング（`HELIX-process-L0-L14.md` と各 mode doc 参照）

| Mode | 現行接続の要約 | Gateway profile 必要性 |
|---|---|---|
| Scrum | 既存で Reverse 経由の言及あり | 必須（fullback） |
| Discovery | 現行で Reverse を明示する文脈あり | 必須（PoC fullback） |
| Incident | 既存 doc は緊急停止優先 | 事後（post-hotfix） |
| Recovery | 収束フェーズ中心で stop-go を重視 | 事後（post-recovery） |
| Retrofit | 逆接続があるが mode 間で不揃い | 必須（upgrade / normalization） |
| Add-feature | 直感的には design+implementation の二段接続 | 必須（design entry + fullback） |
| Refactor | 挙動不変ケースが多数 | 条件（normalization-lite） |
| Research | 参照 doc や desk-check が主 | 条件（conditional） |
| HELIX W (設計論) | mode category 外 | 設計論として Phase 1/2/3 で profile 記載 |

### forward 入口に対する課題

- 同一 mode 名でも処理内容が異なるため、mode だけでは Forward 接続後の検証責務が推定できない。
- mode ごとに profile を固定すると、`route_engine` の出力と docs 的な接続経路を突き合わせやすい。
- `profile` は mode とドキュメントカテゴリの間で共通語彙になり、`drift` / `recommended_command` の説明力を高める。

## Decision

### Main Decision

「Non-Forward entry modes は Forward L0-L14 接続前に Reverse Gateway Profile を通す」。  
ただし Emergency/収束中例外モードは profile の `post-*` パターンを使い、停止優先を維持する。

### Sub-Decision 1: 必須 profile（4 mode、確実に Reverse gateway 経由）

#### 方針

- Scrum / Discovery / Add-feature / Retrofit は必ず Reverse Gateway Profile を経由する。
- Add-feature は既存の設計と実装断面差を吸収しやすくするため design-entry と fullback を両立する。

#### 詳細

1. Scrum：`fullback` profile  
   - 入力: 進行中の実装差分、user feedback。  
   - 挙動: 実装や doc のずれを逆走査し、再接続。  
   - 出力: `forward_target=driving_plan`（暫定名として扱う）。
   - `recommended_pipeline`: 既存 `suggest_command` を含みつつ 2 段の復旧コマンド列。

2. Discovery：`fullback` profile  
   - 入力: PoC artifact、confirmed PoC。  
   - 挙動: PoC→ADR の整合を取った上で forward 接続。  
   - 出力: `forward_target=discovery_plan`。
   - `recommended_pipeline`: `suggest_command` は保持、加えて検証済み PoC の再接続コマンドを追加。

3. Add-feature：`fullback` profile（design entry + fullback）  
   - 入力: design entry の ADR / ADR-041 / ADR-042 関連文脈。  
   - 挙動: ADR 先行で設計を揃え、実装後に forward 接続後も整合。  
   - 出力: `forward_target=add_feature_plan`。  
   - `profile` では design entry fullback と implementation fullback の 2 段を明示。

4. Retrofit：`fullback` profile（upgrade/normalization）  
   - 入力: 既存資産 drift、asset migration。  
   - 挙動: ADR-041 の既存 direct routing を保持し、profile 層で migration 断面を補う。  
   - 出力: `forward_target=retrofit_plan`。  
   - `recommended_pipeline`: `suggest_command` の前後に normalization check を追加可能（additive）。

#### 受け入れ条件（required）

- 各 mode で Reverse Gateway Profile が必須として明記される。
- `profile`=fullback の定義が docs と route_engine で同義となる。
- ADR-041 で定義された drift routing との整合が維持される。

### Sub-Decision 2: 事後 profile（2 mode、緊急対応中 skip、収束後のみ）

#### 方針

- Incident と Recovery は初動で即時停止優先のため、`post` プロファイルを採用し、収束後のみ Reverse gateway へ入る。

#### 詳細

1. Incident：`post-hotfix fullback` profile  
   - 目的: hotfix 対応優先のため、Reverse gateway を即時スキップし、hotfix 完了後に post-hotfix fullback に入る。  
   - `forward_target`: `incident_plan`。  
   - `recommended_pipeline`: `suggest_command` は既存維持、post リカバリ手順を pipeline 追記。

2. Recovery：`post-recovery fullback` profile  
   - 目的: 暴走収束中に routing を増やさず、収束後に正規化。  
   - `forward_target`: `recovery_plan`。  
   - `recommended_pipeline`: `suggest_command` は既存維持、収束確認後に復旧ルート。

#### 受け入れ条件

- 収束中は reverse skip が許容されることを明示し、post 判定条件（収束トリガ）を定義する。
- Recovery / Incident の初動速度が低下しない。

### Sub-Decision 3: 条件 profile（2 mode、特定条件のみ）

#### 方針

- Refactor と Research は前提条件を満たした時のみ normalization / reverse を行う。
- 既定時は軽量 profile を採用して、無駄な Reverse 実行を避ける。

#### 詳細

1. Refactor：`PLAN driven + normalization-lite` profile  
   - **運用 pattern (ユーザー指摘 2026-05-28、5 step)**:
     1. **`kind: refactor` PLAN を先に起票** (本体 doc 修正前)
     2. PLAN で **破壊点 / デグレ可能性 / 影響範囲 (影響 module / 既存テスト保護網 / rollback evidence)** を構造化記述
     3. **本体 doc 確定** (tl-advisor adversarial → TL approve → PLAN finalize)
     4. **PLAN に基づき本体 doc 修正実施** (PM / Codex docs)
     5. 設計 trace 変更時のみ **Reverse normalization-lite** (trace 整合のため)
   - 効果: 破壊点 / デグレが PLAN trace で辿れる、後から見直しやすい (機械的 R0-R4 強制より軽量 + 安全)
   - 条件:
     - 挙動変更なしケース: lite のみ（軽量、Reverse skip）  
     - 設計 trace 変更ケース: normalization を追加  
     - ADR 整合不一致: normalization に昇格  
   - `forward_target`: `refactor_plan`  
   - `recommended_pipeline`: `suggest_command` まず維持し、必要時のみ normalization 系 pipeline を追加

2. Research：`conditional` profile  
   - 条件:
     - 既存資産調査を要する場合のみ Reverse  
     - ADR と現行 doc の齟齬検出時のみ Reverse  
     - 机上検討/情報収集のみは直接 L1/L4 ADR 接続  
   - `forward_target`: `research_plan`  
   - `recommended_pipeline`: 机上 path は pipeline 追記なし、調査依存時に追加

#### 受け入れ条件

- 条件評価ロジックが可観測であること（手順・条件を文書に保持）。
- 条件未成立時の pass-through が明示されること。

### Sub-Decision 4: HELIX W 特殊扱い（設計論カテゴリ）

#### 方針

- HELIX W（2-stage agent design）は mode カテゴリから除外し、設計論カテゴリとして扱う。
- Phase 1/Phase 2 と Phase 3 合流を profile 遷移で明記する。

#### 詳細

- Phase 1/2 完了後: `fullback`  
- Phase 3 合流前: `normalization`  
- L10 合流時に design-target を統合し、mode category の通常 routing テンプレートは使わない。

#### 受け入れ条件

- Workflow 文書に mode 非該当の明記があること。
- Profile 遷移が「設計論としての方法記述」だけで固定されること。

### Sub-Decision 5: ADR-041 amendment（drift type routing 保持）

#### 方針

- ADR-041 の direct routing は profile 内に保持する。
- 既存 routing 条件（`code_smell` → Refactor、`structural` → Refactor、`dependency_outdated` → Retrofit、`upgrade` → Retrofit、`config_drift` → Retrofit）は status 変化させず残す。

#### 詳細

- ADR-041 direct routing を削るのではなく、mode profile で内包化する。
- `drift` 由来の `drift_type` は profile 選定時の追加次元として扱い、ADR-041 との衝突を回避する。
- ADR-041 status は「Accepted with conditions」とし、conditions は `ADR-047` に保存する。
- ADR-041 の sibling relation を本文に明記する（sibling_adr）。
- ADR-041 amendment は ADR-047 を親として扱う。

#### 受け入れ条件

- ADR-041 と ADR-047 の参照関係がリンクで成立する。
- 既存 ADR-041 で定義された分岐が route_engine で壊れない見立て（将来 Wave 6 実装で担保）。

### Sub-Decision 6: ADR-042 amendment（recommended_command 拡張）

#### 方針

- ADR-042 の `recommended_command` 単一構造は backward compat を保持。
- Reverse → Forward の複合配線は v2 の additive field 追加で対応する。

#### 追加フィールド

1. `gateway: ReverseGatewayProfile | null`  
   - profile 名前、必須/事後/条件の種類、理由、例外条件を保持。
2. `forward_target: ForwardConnectionTarget | null`  
   - 接続先の Forward 対象（plan/doc/command など）を明示。
3. `recommended_pipeline: list[Command] | null`  
   - `suggest_command` を維持しつつ、profile 追加時の pipeline を記録。

#### 既存互換

- 現行 `suggest_command` は変更しない（文字列意味を維持）。  
- `recommended_command` は既存利用者向けに shape 破壊を避ける。  
- ADR-042 の提案を破壊しないため、`gateway` / `forward_target` / `recommended_pipeline` は additive。  
- `route_engine` v2 移行は Wave 6 carry とし、本 ADR 単体では実装方針を固定のみとする。

#### 受け入れ条件

- ADR-042 の既存受け取り先（非 v2）に影響を与えない。
- `gateway` / `forward_target` / `recommended_pipeline` は空値許容（`null`）で移行可能。

## Routing Design (Reverse Gateway Profile)

### 追加的 route model（ADR-047 提案）

```text
RouteDecision
  signal
  mode
  kind
  subtype
  drift_type
  gateway_profile (nullable)
  forward_target (nullable)
  recommended_pipeline (nullable list<command>)
  suggest_command (existing string)
  recommended_command (existing object, backward compat)
```

### Gateway Profile と mode の対応表（規定値）

| mode | profile | required | reason | recommended_target |
|---|---|---|---|---|
| Scrum | fullback | true | 実装と記録の同期 | Scrum plan |
| Discovery | fullback | true | PoC と ADR 同期 | Discovery plan |
| Incident | post-hotfix fullback | cond | 初動停止優先 | Incident plan |
| Recovery | post-recovery fullback | cond | 収束優先 | Recovery plan |
| Retrofit | fullback | true | 資産更新と互換保全 | Retrofit plan |
| Add-feature | fullback | true | 設計入口 + 実装後 fullback | Add-feature plan |
| Refactor | normalization-lite | false | 挙動不変ケース優先 | Refactor plan |
| Research | conditional | false | 齟齬時のみ | Research plan |
| HELIX W | normalization (design) | N/A | 設計論 | なし |

### 例外ルール

- Incident と Recovery は収束前は profile 適用を `skip`。  
- Research の直接 ADR 接続は条件未成立なら許容。  
- Refactor は設計 trace 変更時のみ normalization に昇格。  
- Add-feature の fullback には design-entry の前提を持ち、実装後再接続を明記。  

### 事業影響の観測

- profile 追加によりドキュメントの routing 断面が統一される。  
- route_engine v2 では `gateway` 判定を route result に追加して trace しやすくする。  
- docs 側は workflow doc の forward 接続節の wording を「Reverse Gateway Profile + Forward 接続」に更新する。  
- skills / core doc 側は同期で ADR-sibling を更新する。

### ADR-041 / ADR-042 との突合

- ADR-041: `drift_type` direct routing を削除せず profile 内で保持する。  
- ADR-042: `suggest_command`（単一）を維持しつつ `recommended_pipeline` を追加で補足する。  
- ADR-041 amendment と ADR-042 amendment は互いの衝突しない実装方針として両立する。  
- ADR-041 と ADR-042 の明示的 sibling 関係を本文と frontmatter で固定する。  

## Consequences

### Positive

- doc 体系の SSoT 単一化: Reverse Gateway Profile を通して mode 別の差分を profile で吸収し、接続の起点が統一される。
- V-model trace 機械検証性向上: mode ごとに profile を明示し、`drift` / 非 drift の接続先を trace しやすくする。
- fork pattern の整合: ユーザー指摘の profile ベース fork を採用し、実装経路が予測可能になる。
- ADR-041/042 amendment により既存判断の可逆性を維持する。
- Incident / Recovery の収束優先方針を破らず、危機時 throughput を確保できる。
- 研究系は条件付きとし、不必要な逆再接続を回避できる。

### Negative

- 修正影響範囲が拡大する（ADR 側だけでなく docs/cli 同時更新）。
- route_engine 契約 v2 移行（`gateway`/`forward_target`/`recommended_pipeline`）の実装が必要。  
- `profile` 導入により仕様説明文言が増え、初見学習コストが上がる。
- 既存 PLAN tree（L0-L14 全工程）は legacy contract 扱いとするため、当面は再 routing されない。
- 実装対象ではあるが ADR-047 単体では実施しないため、wave の進捗依存が発生する。

### 中立

- ADR-046（L5 詳細設計 snapshot）は ADR-047 採択後の起票が妥当であり、順番として自然。
- ADR-047 で profile ルールを固定することで、後続 ADR が追従しやすくなる。

## Compliance Matrix

| Compliance 観点 | 本 ADR の対応 |
|---|---|
| BR-09 parent design freeze 回避 | ADR-041/042 を amendment で追補し、本体不変更（non-destructive）で実現 |
| BR-10 ADR snapshot 必須 | 本 ADR は Reverse Gateway Profile を snapshot として固定 |
| BR-11 sibling ADR 明示 | sibling_adr field で ADR-041/042/044/045 を明示し、本文でもクロス参照 |
| BR-12 ratchet baseline | 修正影響範囲を ratchet 化（本 ADR の `Impact` と `Implementation Plan` に整理） |
| V-model L4↔L8 pair freeze | profile が L4↔L8 trace を明示し、Reverse→Forward 再接続の trace を明確化 |
| Design Governance | ADR-047 で mode 追加判断を統一し、追加 ADR の sibling_adr 要件を満たす |
| Contract Backward compatibility | ADR-042 の backward compat 原則を維持（`suggest_command` 不変更） |
| Auditability | profile、forward_target、pipeline の 3 組を evidence として追跡可能 |
| Traceability | `gateway`、`forward_target`、`recommended_pipeline` を ADR と workflow doc の相互参照で固定 |
| Anti-regression | Fullback / conditional / lite を明文化し、全 mode で逆方向の回帰条件を分離 |

## Implementation Plan (Wave 6-8、本 ADR 完成後)

### Wave 6: route_engine 契約拡張（本 ADR 対応）

1. RouteResult / 推奨出力に以下の additive field を追加:
   - `gateway: ReverseGatewayProfile | null`
   - `forward_target: ForwardConnectionTarget | null`
   - `recommended_pipeline: list[Command] | null`
2. `suggest_command` は v1 互換で維持。
3. `recommended_command` の既存フィールドは維持し、v2 での拡張は `gateway` 系で補完。
4. `DRIFT_TYPE_TO_ROUTE` と `SIGNAL_TO_MODE` の挙動を ADR-047 準拠で整える。
5. テスト観点:
   - route 期待値テスト（mode ごと）
   - profile 判定テスト
   - backward compatibility テスト（`suggest_command` を使い続ける）

### Wave 7: workflow docs + CLI 同期

1. HELIX-workflows/helix-process/{8 mode}-workflow.md の「Forward 接続」節を更新し、「Reverse Gateway Profile + Forward 接続」に統一。
2. `HELIX-process-L0-L14.md` §他モード table に `profile 種別` 列を追加。
3. `skills/SKILL_MAP.md`、`helix/HELIX_CORE.md`、`CLAUDE.md`、`AGENTS.md` の整合更新（設計ロールの読み替え・参照更新）。
4. README / docs 索引のリンクを `ADR-047` と整合。

### Wave 8: 検証

1. route_engine matrix tests（mode×profile×drift）。
2. reverse multitype tests（schema/contract/code_smell/structural/dependency_outdated など）。
3. mode-specific E2E（Scrum/Discovery/Incident/Recovery/Refactor/Research/Add-feature/Retrofit）。
4. ADR-041/ADR-042 変更影響検証と回帰テスト。

## 詳細 trace 仕様（参考）

### Route Engine 連携例

#### 例 1: Refactor（振る舞い不変）

- signal: user_feedback_iteration  
- drift_type: none  
- mode: Refactor  
- profile: normalization-lite（条件未満）  
- gateway: normalization-lite profile  
- forward_target: refactor_plan  
- recommended_pipeline: `[suggest_command]`（既存 command のまま）

#### 例 2: Refactor（設計 trace 変更）

- signal: code_smell  
- mode: Refactor  
- drift_type: structural  
- profile: normalization-lite -> normalization  
- gateway: normalization-lite（初期）  
- forward_target: refactor_plan  
- recommended_pipeline: `[suggest_command, "helix lint --strict", "helix task catalog"]`

#### 例 3: Incident（本番停止）

- signal: production_incident  
- mode: incident  
- profile: post-hotfix fullback  
- gateway: null（収束後）  
- forward_target: incident_plan（収束後のみ）  
- recommended_pipeline: post-hotfix 手順を追加（既存 suggestion 維持）

#### 例 4: Discovery（PoC 成立）

- signal: unknown_design  
- mode: Reverse  
- profile: fullback  
- gateway: fullback  
- forward_target: discovery_plan  
- recommended_pipeline: PoC verified + ADR 反映

### profile 選定チェックリスト

1. この mode が必須 profile か。  
2. 緊急停止中か。  
3. ADR と現行 doc の齟齬有無。  
4. 挙動変更の有無。  
5. 確認済み `drift_type` と一致するか。  
6. `suggest_command` は保持できるか。  
7. 既存 `drift_type` ルート（ADR-041）との衝突有無。  
8. 収束後の post 判定が明文化されているか。  

### ADR-041 補完マップ

- `code_smell` → Refactor（`normalization-lite` が既定）
- `structural` → Refactor（必要時 normalization）
- `dependency_outdated` → Retrofit（`fullback`）
- `upgrade` → Retrofit（`fullback`）
- `config_drift` → Retrofit（`fullback`）
- `schema` → Reverse（`fullback`）
- `contract` → Reverse（`fullback`）

### ADR-042 補完マップ

- `suggested_command`（string）: 既存互換のためそのまま保持  
- `recommended_pipeline`（list）: profile 指定時にのみ追加  
- `forward_target`: Forward 接続先の同定
- `gateway`: profile 判定の明示

## ADR-047 で確定しない事項（Carry）

- Q1: 既存 PLAN tree（L0-L14）を legacy contract 扱いする期間と終了条件はいつまでか。
- Q2: route_engine v2 の strict mode（新契約を必須化）をいつ開始するか。
- Q3: profile 切り替えの動的判定（ユーザー設定 / 自動推奨）を次 PLAN で扱うか。
- Q4: Non-Forward 9 mode の名称（`scrum_agile` と `scrum` の綴り差）を profile 層でどこまで吸収するか。
- Q5: HELIX W の design-phase の具体的 `fullback` / `normalization` 入替え条件を誰が承認するか。

## リスク登録

- ADR-047 では ADR-041/ADR-042 の amend として扱うため、実装フェーズでの解釈差が一時的に発生する可能性。
- docs 側更新タイミングがずれると、`profile` の一次情報が workflow doc と乖離する可能性。
- Wave 6 が遅延すると、Wave 7 の Forward 接続表現更新が一時的に inconsistent になる。
- `post-*` profile の判定が不透明だと Incident/Recovery の意図が読みにくくなるため、実装前に条件定義を厳格化する必要あり。

## リンク整合

- ADR-044: `docs/adr/ADR-044-helix-workflows-v2-architecture-snapshot.md`  
- ADR-045: `docs/adr/ADR-045-helix-f6-f10-governance-snapshot.md`  
- ADR-041: `docs/adr/ADR-041-drift-type-7-categories-routing-decision.md`  
- ADR-042: `docs/adr/ADR-042-recommended-command-machine-vs-display-decision.md`  
- V2 workflow: `HELIX-workflows/HELIX-process-L0-L14.md`  
- mode docs: `HELIX-workflows/helix-process/{scrum,discovery,incident,add-feature,refactor,retrofit,research,recovery}-workflow.md`  
- HELIX W: `HELIX-workflows/helix-process/two-stage-agent-design.md`  
- implementation: `cli/lib/route_engine.py`  
- design skeleton: `/home/tenni/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/draft_reverse_v_model_gateway_wiring.md`  

### Link check policy for docs

- Link 参照は本 ADR の運用範囲に限定し、更新時は 5 兄弟 ADR と V2 workflow を最短で一括確認する。  
- リンクが壊れるリスクは高くなるため、ADR-047 の導入後に link integrity を実行する。  
- ADR の frontmatter および本文リンクは 2 系統（frontmatter / section body）で重複参照し可読性を担保する。

## 未解決項目確認

- 本 ADR は実装を含まない新規記録であるため、未完了項目は 0 件を期待する。  
- 追加判断（mode 名揺れ、wave strict 時期、動的判定）は Carry として管理し、本文外追加判断としない。  
- 実装側の未処理項目は Wave 6 以降で `route_engine` + workflow doc 側に分離して残す。  

## 決定履歴

- 2026-05-28: ADR-047 を Proposed として作成。  
- 2026-05-28: `mode 数 = 10` と `Research` 条件 profile を採用。  
- 2026-05-28: `Incident/Recovery` を事後 profile で停止優先化。  
- 2026-05-28: ADR-041 及び ADR-042 を amendment 対象として同時参照。  
- 2026-05-28: `gateway` / `forward_target` / `recommended_pipeline` の additive 提案に合意。  

## Appendix A: profile 単語出現補助（監査可視性）

この Appendix は profile を本文全体で高頻度利用し、監査時の語彙追跡を容易にする。

- profile が forward 接続を明示する中継語である。
- fullback profile が scrum で必要である。
- fullback profile が discovery で必要である。
- normalization-lite profile が refactor の既定である。
- post-hotfix fullback profile は incident の停止優先を壊さない。
- post-recovery fullback profile は recovery 収束優先を壊さない。
- conditional profile は research 条件付きで活かされる。
- normalization profile は設計差分が確定した場合に使う。
- profile の選定は drift と mode と ADR-041 と ADR-042 の一致性で行う。
- profile と forward_target を同時記録すると trace が明確化される。
- profile 外の direct 接続は例外時のみ許容する。
- profile と gateway を切り離さない。
- profile を使うと profile 由来の監査 evidence が増える。
- profile 名を明示することで fork pattern が説明しやすくなる。
- profile 追加時は ADR-047 の方針を再確認する。
- profile 適用の必須性は mode 10 全体で固定される。
- profile 前提で ADR-041 amendment と ADR-042 amendment を同時管理する。
- profile に依存しない suggest_command は既存の互換性を支える。
- profile は backward compat を阻害しない。
- profile は設計論カテゴリ（HELIX W）では方法論記述へ写像される。
- profile を中心に docs と route_engine を同調させる。
- profile と recommended_pipeline の 3 組は wave6以降の実装キーとなる。
