# PLAN-006: 上流フェーズ拡張（メタフェーズ + ドキュメント依存管理） (v2)

## §1. 目的 / Why

PLAN-004 以降、上流工程の「L-1」は実装起点の固定サブステップ運用が残り、
`実装タスクの分解` が先行する一方で、`設計・ドキュメントの依存関係` が明文化されないまま進みやすくなっている。

本 PLAN は上流フェーズを「上位メタ設計層」として再定義し、
- 基本設計/詳細設計の順番を優先度として管理するためのフェーズ化
- 設計が参照するドキュメント間の依存関係（DAG）を先に確立するための方針
- 研究を機能/市場/技術/OSS/マーケティング/検証方式へ分岐可能にするガバナンス
を導入する。

これにより PLAN-006 以降での L-1, L-2, L-3 の設計品質を再現可能・監査可能にする。

## §2. スコープ

### 2.1 含む

- 上流工程の再構成（L-1 を固定 sub-step から脱却）
- ドキュメント駆動のメタフェーズ設計（依存関係、順序、整合性ルールの明示）
- 研究領域の多様化ルートの導入
- `.helix/patterns/*.yaml` のパターン適用方針（既定は固定 + 任意 llm suggest）
- PLAN-004 readiness の上流接続（L-1 承継）
- PLAN-007 の Scrum トリガー（research/UI/unit/sprint/post-deploy）との接続方針
- v1 / 2026-04-30 改訂履歴の記録

### 2.2 含まない

- L2 以降の詳細実装（実コード、DB/インフラ変更）
- PLAN-007 の詳細設計（接続ルールのみ記述）
- 既存実装計画のコミット・デプロイ作業

### 2.3 スコープ補足（F04 解消）

L-2/L-3 は L-1 で確定した依存図と policy の **適用先** であり、本 PLAN ではそれらを詳細設計しない。本 PLAN の対象は L-1 の再構成（メタフェーズ化 + DAG + リサーチ多様化 + pattern.yaml 運用契約）に限定する。L-2/L-3 への波及は §4 関連 PLAN の接続点のみで言及する。

## §3. 採用方針

### 3.1 ドキュメント駆動メタフェーズ（L-1）

- L-1 は固定サブステップ（L-1.0/L-1.1...）を前提とせず、`目的 → 依存解決 → 設計優先順位付け` の順で進める。
- L-1 の成果物は、まず「どのドキュメントが先にあり、どの設計が何を前提に進むか」を明確にする。
- ドキュメント間依存は次の 3 層 DAG として管理する。

  - `Plan Layer`: PLAN / README / D-PLAN
  - `Architecture Layer`: D-ARCH / ADR / D-IA
  - `Contract & 運用 Layer`: D-API / D-DB / D-CONTRACT / D-HANDOVER

- 各 Layer の entry/exit はレビュー観点と対応させ、上流で未決定項目を `deferred` 化して次工程へ明示する。

#### 3.1.1 L-1 と既存 L1/G0.5/G1/G1R/G1.5 の接続条件（F01 解消）

L-1 は L1 内のメタ工程として位置づける。L1 の entry/exit を分割し、L-1 のメタフェーズが先に完了してから L1 本体（要件構造化 + 受入条件定義）に進む。phase.yaml / gate-policy / handover 上の表現は以下のマッピング表で固定する。

| 段階 | 既存 phase | 本 PLAN での扱い | gate | exit 条件 |
|---|---|---|---|---|
| L1 entry (前段) | L1 | L-1 メタフェーズ (本 PLAN の対象) | — | DAG 3 層（Plan/Architecture/Contract）が確定し、deferred 項目が明示済み |
| L1 mid | L1 | 既存 L1 = 要件構造化 + 受入条件定義 | G0.5（企画突合） | L-1 の優先順位マトリクスを満たす |
| L1 exit | L1 | 既存 L1 完了 | G1 | 要件完了ゲート（既存通り） |
| L1 補助 (research) | L1 | L-1 メタフェーズの研究ルート補完 | G1R | DAG の Plan Layer に発見事項が反映済み |
| L1 補助 (PoC) | L1 | L-1 で「検証方式リサーチ」が confirmed | G1.5 | PoC 実施可能性が DAG 上で承認 |

phase.yaml 表現は **L1 内のメタ工程** として扱い、独立した phase 識別子（例: `L0.5`）は導入しない。これにより既存 helix-status / helix-gate / helix-mode の挙動を破壊しない。

### 3.2 リサーチ多様化

リサーチは L-1 中核の一部として、機能・市場・技術・OSS・マーケティング・検証方式の 6 ルートで実施する。
- 機能リサーチ: 競合比較、実装境界、運用条件
- 市場リサーチ: 利害関係者価値、失敗シナリオ
- 技術リサーチ: 外部依存、互換性、移行コスト
- OSS リサーチ: ライセンス/保守性/成熟度
- マーケティングリサーチ: 導入導線、導線摩擦、期待値設計
- 検証方式リサーチ: PoC、性能仮説、回帰検証の観点

各リサーチは「設計優先順位」に還元し、`実装前に意思決定を収束` させる。

#### 3.2.1 リサーチ 6 ルートの発火条件・DoD・反映先（F02 解消）

工数膨張を防ぐため、ルートごとに以下を固定する。

| ルート | trigger | required/optional | evidence path | DoD | deferred 可否 | 設計優先順位への反映先 |
|---|---|---|---|---|---|---|
| 機能 | L-1 entry 時に必須 | required（全案件） | `.helix/research/<id>/feature.md` | 競合 N≥2 比較 + 実装境界明文化 + 運用条件1件以上 | 不可（必須） | DAG Architecture Layer の D-ARCH 章節 |
| 市場 | 利害関係者あり | required（外部利害関係者あり時） / optional（内部のみ） | `.helix/research/<id>/market.md` | 主要利害関係者2件以上 + 失敗シナリオ1件 | 可（P2 で carry） | DAG Plan Layer の README/D-PLAN |
| 技術 | 外部依存変更 or 移行あり | required（依存変更時） / optional（依存固定時） | `.helix/research/<id>/tech.md` | 互換性表 + 移行コスト試算 | 可（P2） | DAG Architecture Layer の ADR |
| OSS | OSS 利用あり | required（OSS あり） / skip（OSS なし） | `.helix/research/<id>/oss.md` | License 表 + 保守 PR 状況 + 成熟度判定 | 不可（required 時） | DAG Architecture Layer の ADR |
| マーケ | 外部公開あり | required（外部公開） / optional（内部利用のみ） | `.helix/research/<id>/marketing.md` | 導入導線 + 期待値設計 + 摩擦項目 | 可（P3） | DAG Plan Layer の README |
| 検証方式 | 実装/性能不確実性 | required（不確実性 high） / optional（low） | `.helix/research/<id>/verification.md` | PoC 計画 + 性能仮説 + 回帰検証手順 | 不可（required 時） | DAG Contract & 運用 Layer の D-CONTRACT |

`required/optional/skip` は L-1 entry 時に決定する。`deferred 可否` の不可ルートが未完なら G1R 通過不可（fail-close）。「設計優先順位への反映先」は L-1 exit 時にリサーチ結果がどの DAG 層・成果物に反映されたかを必ず記録する。

`<id>` は task id（HELIX-XXX-NN 等）を採番し、`.helix/research/<id>/` 配下に統一保存する。

### 3.3 パターンライブラリ（`.helix/patterns/*.yaml`）

- パターンは固定ルールとして管理し、文書・設計・運用の粒度差を吸収する。
- 参考ルール:
  - 例: `doc-governance`（要件→設計→実装依存順）
  - 例: `research-bundle`（機能/技術/OSS の同時評価）
  - 例: `phase-handoff`（deferred / risk / 実験条件の引継ぎ）
- 本 PLAN では pattern.yaml の実体定義を実装しない。
- ただし PLAN-006 で `pattern.yaml` の運用順序と適用優先順位を明文化し、PLAN-007 に接続する。

#### 3.3.1 pattern.yaml 最小契約と競合解決規則（F03 解消）

実体定義は本 PLAN の対象外だが、最小フィールドと競合解決規則を契約として固定する。

##### 最小フィールド

```yaml
patterns:
  - id: doc-governance              # 必須、kebab-case 一意
    scope:                           # 必須、適用範囲
      layer: [Plan, Architecture]    #   3 層 DAG のいずれか or 複数
      phase: [L-1, L1]               #   適用フェーズ
    priority: 100                    # 必須、適用優先度（数値、大きい方が優先）
    applies_when:                    # 必須、適用条件式（DSL は最小: list of feature flags）
      - drive: be|fe|fullstack|db|agent
      - has_external_api: true
    outputs:                         # 必須、生成/期待される成果物
      - path: docs/adr/{id}.md
        type: ADR
    conflicts_with:                  # 任意、競合する pattern id 列
      - id: research-bundle
        resolution: priority         #   priority|first-match|merge|exception
    exception_policy:                # 任意、例外運用の記録仕様
      requires_approval: PM
      audit_log: true
    audit_log:                       # 必須、適用記録
      enabled: true
      path: .helix/audit/pattern-applications.yaml
```

##### 適用優先順位と競合解決

1. **固定 pattern.yaml 内の `priority` 数値** が高い順に評価
2. 同 priority の競合: `conflicts_with.resolution` で決定
   - `priority`: priority 数値で決定（同順位なら error）
   - `first-match`: 先に評価された方を採用、他は skip
   - `merge`: outputs を結合、ただし path 衝突は error
   - `exception`: `exception_policy` を適用（PM 承認待ちで pending）
3. 固定 pattern と `--llm-suggest` 由来の動的提案が衝突した場合、**固定 pattern を優先**（llm-suggest は提案レベル）
4. 適用記録は `.helix/audit/pattern-applications.yaml` に必ず append（finding と同様 redaction を通す）

##### 例外運用

- 既存案件で pattern 未対応のケース: `exception_policy.requires_approval` を満たせば適用 skip 可
- 例外発生は `audit_log` に必ず記録し、後続レビューで再評価

### 3.4 hybrid 適用ロジック

- 既定は `pattern.yaml` ルールを固定適用する。
- 補助的に `--llm-suggest` を許可し、候補候補の精査/代替案提示に `gpt-5.4-mini` を使用する。
- 適用優先順位:
  1. まず固定ルール（pattern.yaml）を適用
  2. 必要時に llm suggest を参照
  3. 生成結果は最終判断前提としてレビュー記録へ残す
- いずれも最終的には PLAN-006 L-1 で承認された policy に従う。

## §4. 関連 PLAN（接続）

- `PLAN-004`（`docs/plans/PLAN-004-pm-reward-design.md`）
  - 本 PLAN は L-1 への readiness 拡張の継承元として扱う。
  - 既存の 5 軸評価・G2/G3/G4 ロジックを前提とする。
- `PLAN-002` / `PLAN-003`
  - 調達済み基盤やフェーズ実行の実績整合を参照し、上流の前提変更を最小化する。
- `PLAN-005`
  - 運用/自動化へ接続する場合の成果物分類方針を整合させる。
- `PLAN-007`（Scrum 5 種トリガー）
  - L-1 / L-2 途中の insertion 点として接続ルールを定義（PLAN-007 実装時に詳細化）。

## §5. リスク

- R1: 上流の自由構成化により、設計進行が拡散し優先順位が不明化する。
  - 対策: メタフェーズで優先順位マトリクスを先に確定し、deferred を明示。
- R2: リサーチ多様化により工数が見えにくくなる。
  - 対策: 研究ルートごとの DoD（完了条件）を事前固定。
- R3: パターン依存の過剰化により意思決定が形式化しすぎる。
  - 対策: hybrid を採用し、`llm-suggest` は代替提案に限定。
- R4: pattern.yaml 未整備時に例外運用が発生。
  - 対策: 運用上の暫定ルール（固定優先・例外記録）を PLAN-006 内で明文化。

## §6. Sprint 計画（L1〜L4 概要）

### Sprint L1: メタフェーズ設計と依存図定義

- L-1 の固定 sub-step を廃止し、DAG 依存図（Plan / Architecture / Contract）を策定
- 研究ルート（機能/市場/技術/OSS/マーケティング/検証方式）を分類し、優先順序を確定
- PLAN-004 の readiness 前提を L-1 入口条件にマッピング

### Sprint L2: パターン実装方針と適用規則

- `.helix/patterns/*.yaml` 適用方針（分類・優先順位・例外）を文書化
- `deferred` と承認条件をレビュー記録仕様として統一
- L-1→L-2 受け渡しの gate-compatible チェック項目を定義

### Sprint L3: hybrid ルール運用定着

- 固定パターン適用を基本化し、`--llm-suggest` の使用条件を明文化
- `gpt-5.4-mini` 利用範囲を「提案の補助」に限定
- L1/L2 の意思決定ログを PLAN-006 方針に合わせて標準化

### Sprint L4: PLAN 接続整備と受入準備

- PLAN-004/007 接続条件を最終化し、上流受け渡し時の文書チェックリストを作成
- 改訂履歴・リンク整合・レビュー観点を整理し、L8 での評価に備える

## §7. 改訂履歴

| 日付 | バージョン | 変更内容 | 変更者 |
| --- | --- | --- | --- |
| 2026-04-30 | v1 | PLAN-006 新規ドラフト作成。Q2 の L-1 柔軟化、Q4 hybrid（pattern.yaml + --llm-suggest）を反映。ドキュメント駆動メタフェーズとリサーチ多様化、PLAN-004/007 接続方針を導入。 | Docs (Codex) |
| 2026-05-01 | v2 | TL レビュー (PLAN-006.json) finding F01-F04 を解消。F01: §3.1.1 で L-1 ↔ L1/G0.5/G1/G1R/G1.5 マッピング表追加（L-1 は L1 内メタ工程として固定、新規 phase 識別子は導入しない）。F02: §3.2.1 でリサーチ 6 ルートの trigger/required-optional/evidence-path/DoD/deferred 可否/反映先を表化。F03: §3.3.1 で pattern.yaml 最小フィールド (id/scope/priority/applies_when/outputs/conflicts_with/exception_policy/audit_log) と固定 vs llm-suggest 競合時の優先規則を明文化。F04: §2.3 にスコープ補足追加（L-2/L-3 は適用先であり詳細設計対象外）。 | PM (Opus) |
