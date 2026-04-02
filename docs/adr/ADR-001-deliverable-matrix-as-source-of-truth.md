# ADR-001: Deliverable Matrix as Source of Truth

## Status
Accepted

## Context

現行 HELIX はフェーズを活動名ベースで定義しているが、成果物の粒度が粗く、L4 実装中に追加設計が発生しやすい。結果として、設計凍結後に仕様の抜け漏れが発見され、G3 以降のやり直しや暗黙知への依存が起きている。

既存の `.helix/doc-map.yaml` と `.helix/gate-checks.yaml` は運用上重要だが、どの成果物がどのスコープ、どの駆動タイプ、どのレイヤーで必須なのかを宣言的に表現する正本がない。そのため、テンプレート、ゲート判定、実運用状態が別々に進化し、差分や例外の管理が難しい。

HELIX v2 では、フェーズを「活動完了」ではなく「L x 成果物の充足」に再定義する。各ゲートは、対象スコープに要求される成果物集合が宣言上存在し、実行時状態として完了していることを確認して初めて通過できるようにする。

この変更では以下を同時に満たす必要がある。

- 宣言と実行時状態を分離し、正本の不変性を保つこと
- `feature` / `shared` / `platform` の 3 スコープを統一的に扱えること
- `feature` が `shared` を参照するような many-to-many mapping を許容すること
- 既存プロジェクトを即時破壊せず、advisory から block へ段階移行できること
- deliverable status の語彙を標準化し、例外承認を監査可能にすること

## Decision

HELIX v2 では、成果物対照表を中心に据えた document-driven gate へ移行する。ゲート通過条件は「対象 L に必要な成果物が `matrix.yaml` で宣言され、実行時状態で充足していること」とする。

### 1. `matrix.yaml` を spec（宣言）の正本とする

- `matrix.yaml` はプロジェクト単位の成果物対照表とする
- 人間が編集する宣言ファイルであり、不変（immutable）な設計入力として扱う
- `matrix.yaml` には status を含めない
- `matrix.yaml` には少なくとも以下を表現できることを求める
  - 成果物 ID
  - 適用レイヤー（L1-L8）
  - 適用駆動タイプ（be / fe / db / agent）
  - 適用スコープ（feature / shared / platform）
  - 条件付き必須ルール
  - ドキュメント/コードの対応パス
  - 生成対象への写像情報

### 2. runtime state は分離する

- 可変状態は `.helix/state/deliverables.json` に保持する
- 実行時状態には status、更新日時、waive 理由、検証メタデータなどの可変情報を持たせる
- 成果物インスタンスの識別子は原則 `(scope_type, scope_id, level, deliverable_id)` とする
- `.helix/doc-map.yaml` と `.helix/gate-checks.yaml` は `matrix.yaml` から生成する派生物とする
- 生成物は手編集の対象にしない
- これにより、宣言、状態、運用テンプレートの責務を分離する

### 3. 3 スコープモデルを採用する

- `feature`: `docs/features/{id}/` と `src/features/{id}/` を対応づける
- `shared`: `docs/shared/{id}/` と `src/shared/{id}/` を対応づける
- `platform`: `docs/platform/{id}/` と `src/platform/{id}/` または `infra/` を対応づける
- many-to-many mapping を許容する
- 具体例として、`feature` は複数の `shared` を参照できる
- ただし、スコープ依存の循環参照は generator が検出し reject する
- これにより、共通モジュールや基盤を feature ごとの局所設計に押し込まずに管理できる

### 4. 導入は advisory から block へ段階移行する

- Phase 0-1 は advisory のみとする
- この期間は不足成果物や不整合を警告するが、ゲートをブロックしない
- Phase 2-3 は互換生成を有効化しつつ、対象レイヤーと対象スコープを限定して段階的に block する
- Phase 4-5 は完全切替とし、`matrix.yaml` を唯一の宣言入力として扱う
- 既存の `.helix/doc-map.yaml` / `.helix/gate-checks.yaml` を直接保守する運用は終了する

### 5. deliverable status の語彙を標準化する

- status 語彙は `pending` / `in_progress` / `done` / `waived` / `not_applicable` / `partial` とする
- `waived` は理由必須とし、S 案件簡略化や L5 skip などの根拠を残す
- `not_applicable` はスコープや駆動タイプ上そもそも適用外の成果物に使う
- `partial` は一部充足だが gate 通過条件を満たしていない状態として扱う
- block 段階では、対象成果物は原則 `done` / `waived` / `not_applicable` のいずれかでなければゲート通過不可とする

## Consequences

### Positive

- フェーズ完了の定義が活動ベースから成果物ベースへ変わり、G2/G3 の凍結条件が明確になる
- `matrix.yaml` を唯一の宣言入力にすることで、テンプレート、ゲート、運用状態のドリフトを抑制できる
- `feature` / `shared` / `platform` を分けることで、共通資産と個別機能の境界を明示できる
- `waived` を理由必須にすることで、簡略化と未完了を区別できる
- advisory 導入により、既存プロジェクトに破壊的変更を即時強制せず移行できる

### Negative

- 宣言ファイル、runtime state、生成物の 3 層を維持するため、初期実装と運用の複雑性は増える
- 既存の手編集前提フローは移行が必要になる
- many-to-many mapping を許容することで、説明責任と可視化の難易度が上がる
- 成果物カタログが増える分、S/M 案件では過剰運用になりやすい

### Risks

- `matrix.yaml` の記述力が不足すると、例外ルールが runtime 側に漏れ、再び二重正本化する
- 生成処理が不安定だと、`.helix/doc-map.yaml` と `.helix/gate-checks.yaml` の差分がレビュー負荷になる
- `waived` の運用が甘いと、実質的な未完了を正当化する抜け道になる
- 段階導入中は advisory と block の判定境界が混在するため、ユーザー教育とログ整備が必要になる

## Deliverable Catalog v1

成果物 ID は以下を正本とし、各プロジェクトの `matrix.yaml` はこのカタログをベースに required / conditional / not_applicable を宣言する。

### L1 要件定義

| ID | 名称 | 適用 | 備考 |
|---|---|---|---|
| D-REQ-F | 機能要件一覧 | 全駆動タイプ | 必須 |
| D-REQ-NF | 非機能要件 | 全駆動タイプ | 可用性・セキュリティ・性能・運用保守性を含む |
| D-ACC | 受入条件 | 全駆動タイプ | 必須 |
| D-RES | 事前調査レポート | 全駆動タイプ | G1R 該当時のみ条件付き必須 |

### L2 全体設計

| ID | 名称 | 適用 | 備考 |
|---|---|---|---|
| D-ARCH | アーキテクチャ設計 | 全駆動タイプ | 必須 |
| D-ADR | Architecture Decision Record | 全駆動タイプ | 必須 |
| D-THREAT | 脅威モデル | 全駆動タイプ | 必須 |
| D-VIS-ARCH | Visual アーキテクチャ | fe | fe のみ必須 |
| D-DATA-ARCH | データアーキテクチャ | db | db のみ必須 |
| D-ORCH-ARCH | オーケストレーション設計 | agent | agent のみ必須 |

### L3 詳細設計

| 駆動タイプ | 成果物 ID |
|---|---|
| be | D-API, D-DB, D-MIG-PLAN, D-DEP, D-TEST, D-PLAN |
| fe | D-UI, D-STATE, D-API-CONS, D-DEP, D-TEST, D-PLAN |
| db | D-DB, D-MIG-PLAN, D-DATA-ACCESS, D-DEP, D-TEST, D-PLAN |
| fullstack | D-API, D-UI, D-CONTRACT, D-DB, D-STATE, D-DEP, D-TEST, D-PLAN |
| agent | D-TOOL, D-PROMPT, D-EVAL-PLAN, D-DEP, D-TEST, D-PLAN |

### L4 実装

| 駆動タイプ | 成果物 ID |
|---|---|
| be | D-IMPL, D-MIG, D-CONFIG |
| db | D-IMPL, D-MIG, D-CONFIG |
| fe | D-IMPL, D-CONFIG |
| fullstack | D-IMPL（BE+FE）, D-MIG, D-CONFIG |
| agent | D-IMPL, D-CONFIG |

### L5 Visual Refinement

| 駆動タイプ | 成果物 ID | 備考 |
|---|---|---|
| be | D-VIS, D-A11Y | `--ui` 時のみ |
| db | D-VIS, D-A11Y | `--ui` 時のみ |
| fe | D-VIS, D-A11Y, D-UX-SIGNOFF | 必須 |
| agent | D-VIS, D-A11Y, D-DEMO | 必須 |

### L6 統合検証

| 駆動タイプ | 成果物 ID |
|---|---|
| be | D-E2E, D-PERF, D-SECV, D-OPS |
| fe | D-E2E, D-PERF, D-A11Y-VERIFY, D-OPS |
| db | D-E2E, D-DATA-VERIFY, D-PERF, D-SECV, D-OPS |
| agent | D-E2E, D-EVAL, D-PERF, D-SECV, D-OPS |

### L7 デプロイ

| ID | 名称 | 適用 |
|---|---|---|
| D-DEPLOY | デプロイ成果物 | 全駆動タイプ |
| D-RELNOTE | リリースノート | 全駆動タイプ |
| D-OBS | 監視・可観測性成果物 | 全駆動タイプ |

### L8 受入

| ID | 名称 | 適用 |
|---|---|---|
| D-UAT | User Acceptance Test 成果物 | 全駆動タイプ |
| D-HANDOVER | 引継ぎ成果物 | 全駆動タイプ |
| D-RETRO | レトロスペクティブ | 全駆動タイプ |
