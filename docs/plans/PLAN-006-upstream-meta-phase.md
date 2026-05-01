# PLAN-006: 上流フェーズ拡張（メタフェーズ + ドキュメント依存管理） (v3.2)

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

#### 3.1.0 L-1 priority matrix の最小契約 (P2 解消)

L-1 exit の判定基準となる優先順位マトリクスは、各案件で以下の最小列を埋める。

| 列 | 必須 | 内容 |
|---|---|---|
| `artifact` | 必須 | 設計対象成果物 (`PLAN-XXX` / `D-XXX` / `ADR-NNN` 等) |
| `depends_on` | 必須 | 同マトリクス内の依存 artifact 列。空配列も明示 |
| `risk` | 必須 | high / medium / low (default low、medium 以上は理由必須) |
| `blocking_research_route` | 必須 | §3.2.1 の 6 ルートのうち **deferred 不可** (機能 / OSS-required / 検証方式-required) のサブセット。G0.5 / G1R で fail-close 判定対象 |
| `deferred_research_route` | 必須 | §3.2.1 の 6 ルートのうち **deferred 可** (市場 / 技術 / マーケ など) のサブセット。carry 時は `helix-readiness` で追跡 |
| `owner` | 必須 | PM / TL / SE / PG / DBA 等の責任ロール |
| `blocking` | 必須 | true (G2 通過必須) / false (deferred 可) |
| `deferred_level` | 条件付 | `blocking=false` のとき P0/P1/P2/P3 を必須記載 |
| `exit_evidence` | 必須 | この artifact が exit 達成済を示す参照 (path / hash / link) |

判定ルール:

1. `blocking=true` の artifact が全て `exit_evidence` を持っていれば L-1 exit 可。
2. tie-breaker (同 priority): `risk=high` > `medium` > `low`、同 risk 内では `depends_on` 数が多い方が先行。
3. `blocking=false` の artifact は `deferred_level` に応じて `helix readiness defer` で次工程へ carry。
4. G0.5 (企画突合) では `blocking_research_route` (deferred 不可) の DoD 充足のみ fail-close 判定。`deferred_research_route` は warning 扱いで通過、carry に回す。
5. G1R では `blocking_research_route` evidence の網羅率を判定し、`deferred_research_route` は readiness ledger に carry 状態を記録。
6. 矛盾 (depends_on の循環、`blocking=true` かつ `deferred_level` 設定、`blocking_research_route` と `deferred_research_route` の重複など) は lint で reject。

マトリクスは `.helix/research/<id>/l1-priority-matrix.yaml` に保存し、`helix-readiness check --phase L1` の入力源として連携する。

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
| 機能 | L-1 entry 時に必須 | required（全案件） | `.helix/research/<id>/feature.md` | 競合 N≥2 比較 + 実装境界明文化 + 運用条件1件以上（**競合非該当時は §3.2.1a 参照**） | 不可（必須） | DAG Architecture Layer の D-ARCH 章節 |
| 市場 | 利害関係者あり | required（外部利害関係者あり時） / optional（内部のみ） | `.helix/research/<id>/market.md` | 主要利害関係者2件以上 + 失敗シナリオ1件 | 可（P2 で carry） | DAG Plan Layer の README/D-PLAN |
| 技術 | 外部依存変更 or 移行あり | required（依存変更時） / optional（依存固定時） | `.helix/research/<id>/tech.md` | 互換性表 + 移行コスト試算 | 可（P2） | DAG Architecture Layer の ADR |
| OSS | OSS 利用あり | required（OSS あり） / skip（OSS なし） | `.helix/research/<id>/oss.md` | License 表 + 保守 PR 状況 + 成熟度判定 | 不可（required 時） | DAG Architecture Layer の ADR |
| マーケ | 外部公開あり | required（外部公開） / optional（内部利用のみ） | `.helix/research/<id>/marketing.md` | 導入導線 + 期待値設計 + 摩擦項目 | 可（P3） | DAG Plan Layer の README |
| 検証方式 | 実装/性能不確実性 | required（不確実性 high） / optional（low） | `.helix/research/<id>/verification.md` | PoC 計画 + 性能仮説 + 回帰検証手順 | 不可（required 時） | DAG Contract & 運用 Layer の D-CONTRACT |

`required/optional/skip` は L-1 entry 時に決定する。`deferred 可否` の不可ルートが未完なら G1R 通過不可（fail-close）。「設計優先順位への反映先」は L-1 exit 時にリサーチ結果がどの DAG 層・成果物に反映されたかを必ず記録する。

`<id>` は task id（HELIX-XXX-NN 等）を採番し、`.helix/research/<id>/` 配下に統一保存する。

#### 3.2.1a 機能リサーチ DoD の代替条件 (P3 解消)

機能リサーチの DoD「競合 N≥2 比較」は外部プロダクト案件を想定した既定値であり、内部運用 / 基盤 / リファクタ案件など **直接競合が存在しない** ケースでは以下の代替を許容する。

| ケース | 代替 DoD | evidence |
|---|---|---|
| 内部運用 / 基盤 / リファクタ | **類似事例 / 既存内部実装 N≥2 の比較** | `feature.md` に「類似機能・既存モジュール」とのトレードオフ表 |
| 競合・類似ともに非該当 (PoC・新規研究領域等) | **`N/A with rationale`** | `feature.md` に非該当理由 + 同等代替が無いことを示す調査範囲 |

代替条件適用時も「実装境界明文化」「運用条件1件以上」は維持する。`N/A with rationale` を用いる場合は **PM 承認** を必須とし `.helix/research/<id>/feature-na-approval.md` に承認者・承認日時・rationale を記録する。承認なしの `N/A` は G1R fail-close。

#### 3.2.2 OSS ルート: License 承認境界 (P2 解消)

OSS ルートの DoD「License 表 + 保守 PR 状況 + 成熟度判定」は **evidence** であり、それ自体は採用判断ではない。OSS の採用 / 削除 / バージョン変更は HELIX エスカレーション境界で人間承認対象とする。

TL は AI ロール (Codex 5.4) のため、ライセンス判断・採用判断は **すべて人間 (PM) が最終承認** する。TL は事前検証 / 提案 / evidence 整備に限定。

| 操作 | TL の役割 | **人間 (PM) 承認** | oss-approval.md | 補足 |
|---|---|---|---|---|
| 新規 OSS 採用 | License 表作成 + supply chain 検証 (CVE / GHSA / package integrity) + 採用提案 | **必須** | 必須（採用判断 + License 種別） | 商用ライセンス・GPL 系統は法務確認も推奨 |
| 既存 OSS のバージョン変更（**security update**: CVE / GHSA 対応） | CVE / GHSA evidence + 差分検証 + 互換性確認 | **必須** (簡易承認可) | 必須（CVE 番号 + 検証 evidence） | 緊急時は事後承認も可、ただし 24h 以内に oss-approval 記録 |
| 既存 OSS のバージョン変更（**機能更新**: 同 license） | License 差分検証 + supply chain 検証 + changelog 検証 | **必須** | 必須（変更 rationale + 検証 evidence） | TL 単独で merge 不可。PM 承認後に依存変更 |
| 既存 OSS の license 変更を伴う変更 | License 互換性評価 + 移行計画提案 | **必須**（法務確認推奨） | 必須（License 互換性 evidence） | License 種別変更（例: MIT → GPL）は影響評価必須 |
| OSS 削除 | 削除影響評価 + 代替提案 | **必須**（PM 通知 + 同意） | 必須（`removed` 注記 + 影響評価） | 監査履歴のために evidence は保持 |

人間 (PM) 承認なしで OSS を追加 / 変更 / 削除すると G1R 通過不可（fail-close）。`oss-approval.md` には承認者・承認日時・License 種別・supply chain 検証 evidence・採用判断根拠を記録する（redaction policy は PLAN-007 §3.5.2 / PLAN-008 §3.6 と同等、auth/PII/secret は redact）。

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
      phase: [L1]                    #   適用フェーズ (L 系のみ。phase.yaml.current_phase の enum と一致)
      gate: [G0.5, G1]               #   適用ゲート (G 系のみ。phase.yaml.gates のキーと一致、任意)
      subphase: [L-1]                #   pattern-local label (§3.1.1 のメタ工程ラベル、phase.yaml には投入しない)
    priority: 100                    # 必須、適用優先度（数値、大きい方が優先）
    applies_when:                    # 必須、適用条件式（最小 DSL、§3.3.2 参照）
      all:                           #   既定は AND、`any:` で OR
        - drive: [be, fe, fullstack, db, agent]   # YAML list = enum メンバ in 判定
        - has_external_api: true                  # scalar = 厳密一致
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

#### 3.3.2 applies_when 最小 DSL (P3 解消)

`applies_when` は以下の最小 DSL に従う。L3 までに pattern lint で文法検証を実装する。

- 最上位は `all:` (AND) / `any:` (OR) のいずれか必須。両方を組み合わせる場合はネスト可。
- 各条件は `<key>: <value>` 形式。
  - `<value>` が **YAML list** の場合: `<key>` の現在値が list のいずれかに **含まれれば true** (in 判定)
  - `<value>` が **scalar** (string/bool/int) の場合: 現在値と **厳密一致** で true
  - `<value>` が **`null`** の場合: `<key>` が **未定義** で true
- ネスト例:
  ```yaml
  applies_when:
    all:
      - drive: [be, fullstack]
      - any:
          - has_external_api: true
          - has_db_migration: true
  ```
- 解釈揺れ防止: 正規表現 / 部分一致 / 比較演算 (`>`, `<`) は最小 DSL に含めない。必要なら L3 以降で `match:` / `compare:` を別フィールドとして拡張提案する。

##### scope の phase / gate / subphase 契約 (P2 解消)

phase.yaml は `current_phase` (L 系) と `gates` (G 系) を別構造で持つため、pattern.yaml も以下のように分離する。

- `scope.phase` は **L 系のみ許可** (`L1`, `L2`, ..., `L8`)。L9-L11 は PLAN-009 の phase.yaml schema 拡張完了後に許可。
- `scope.gate` は **G 系のみ許可** (`G0.5`, `G1`, `G1.5`, `G1R`, `G2`, ..., `G7`)。G9-G11 は PLAN-009 完了後に許可。
- `scope.subphase` は **pattern-local label** (例: `L-1`, `L1.5`)。phase.yaml の状態管理には投入しない。
- pattern engine の解釈: helix-status / helix-gate / handover は `phase.yaml.current_phase` と `phase.yaml.gates` のみを参照し、`scope.subphase` は pattern エンジン内部フィルタにのみ影響。
- 旧記法 (`scope.phase` に L-1 や G 系を含める) は v3 以降禁止。pattern.yaml の lint で reject。
- L9-L11 / G9-G11 を `scope` に投入したい場合は **PLAN-009 の phase.yaml schema 拡張完了** を前提条件として明記し、それまでは pattern を `disabled: true` で待機させる。

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
| 2026-05-02 | v3 | TL レビュー (PLAN-006.json) v2 review 新 finding を解消。P2-1: §3.3.1 pattern.yaml 最小契約で `scope.phase` を phase.yaml enum 一致に限定し、`scope.subphase` を pattern-local label として分離 (L-1 はここに置き phase.yaml には投入しない)。P2-2: §3.2.2 OSS ルート License 承認境界表を追加 (新規採用 / license 変更は PM 必須、同 license バージョン変更は TL、削除は TL + PM 通知、未承認は G1R fail-close)。P3: deferred 台帳の DF-PLAN-006-L1-004/005 を v3 改訂 evidence で resolved 化。 | PM (Opus) |
| 2026-05-02 | v3.1 | TL v3 review 新 finding 解消。P2-1: §3.3.1 で `scope.phase` を L 系のみ・`scope.gate` を G 系のみ・`scope.subphase` を pattern-local label に三分割 (L9-L11 / G9-G11 は PLAN-009 拡張完了が前提)。P2-2: §3.1.0 L-1 priority matrix 最小契約 (artifact / depends_on / risk / required_research_route / owner / blocking / deferred_level / exit_evidence + tie-breaker + lint reject) を追加。P3: §3.2.1a 機能リサーチ DoD の代替条件 (内部基盤 → 類似事例 N≥2 / 競合・類似非該当 → N/A with rationale + PM 承認) を追加。 | PM (Opus) |
| 2026-05-02 | v3.2 | TL v3.1 review finding 解消。P1: §3.2.2 OSS 操作で TL は AI ロールのため**全操作で人間 (PM) 承認を必須**化、CVE/GHSA/supply chain 検証を TL 役割として追加、緊急 security update のみ事後 24h 承認可。P2: §3.1.0 priority matrix を `blocking_research_route` (deferred 不可) と `deferred_research_route` (carry 可) に分け、G0.5 / G1R の fail-close 判定式を明確化。P3: §3.3.2 `applies_when` 最小 DSL (`all` / `any` + list (in 判定) / scalar (厳密一致) / null (未定義)) を追加し、正規表現・比較演算は最小 DSL から除外。 | PM (Opus) |
