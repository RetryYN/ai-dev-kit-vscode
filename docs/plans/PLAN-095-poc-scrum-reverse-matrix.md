---
plan_id: PLAN-095
title: "PLAN-095: PoC = Scrum × Reverse 連携 matrix (Scrum 6 type × Reverse 5 type = 30 cell)"
layer: cross
kind: impl
status: draft
size: M
drive: scrum
created: 2026-05-20
revised: 2026-05-20
owner: PM
workflow_phase: "S0-S4 + R0-R4 cross-layer"
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・matrix 設計最終承認・P0 境界管理"
  - role: pmo-sonnet
    slot_label: "PMO — draft 起票・整合確認・30 cell 表設計レビュー"
  - role: se
    slot_label: "SE — scrum_reverse_matrix.py / poc_validation_log.py / CLI 拡張実装"
  - role: tl-advisor
    slot_label: "TL adversarial check — matrix 設計 review / G3 凍結判定"
generates:
  - artifact_path: cli/helix-scrum
    artifact_type: cli_extension
    description: "--scrum-type <type> / --reverse-merge フラグ追加"
  - artifact_path: cli/helix-reverse
    artifact_type: cli_extension
    description: "--from-scrum / --scrum-hypothesis <id> フラグ追加"
  - artifact_path: cli/lib/scrum_reverse_matrix.py
    artifact_type: python_module
    description: "30 cell matrix lookup / routing rule engine"
  - artifact_path: cli/lib/poc_validation_log.py
    artifact_type: python_module
    description: "poc_validation_log テーブル操作 + history query"
  - artifact_path: cli/lib/tests/test_scrum_reverse_matrix.py
    artifact_type: test
    description: "fake hypothesis fixture + 30 cell mapping 検証"
  - artifact_path: docs/adr/ADR-028-poc-scrum-reverse-matrix-decision.md
    artifact_type: adr_snapshot
    description: "L2 大局判断 snapshot (本 PLAN tree の凍結)"
dependencies:
  parent: PLAN-MM-001
  requires:
    - PLAN-091
    - PLAN-093 (helix doctor + Curator)
    - PLAN-092-posttooluse-plan-auto-register
    - PLAN-MM-001
  blocks: []
related_adr:
  - ADR-028-poc-scrum-reverse-matrix-decision
related_docs:
  - docs/plans/PLAN-MM-001-v5-framework-master-plan.md
  - docs/plans/PLAN-091-v5-framework-core.md
  - docs/v2/V5-plan-outlines.md §PLAN-095
  - CLAUDE.md §V5 framework 18 要素 #14
  - skills/SKILL_MAP.md §HELIX Scrum
  - skills/SKILL_MAP.md §HELIX Reverse / Reverse type matrix
  - helix/HELIX_CORE.md §HELIX Reverse
---

# PLAN-095: PoC = Scrum × Reverse 連携 matrix

> **kind**: impl (framework extension)
> **layer**: cross (S0-S4 + R0-R4 全層に影響)
> **drive**: scrum (workflow_phase: "S0-S4 + R0-R4 cross-layer" で Reverse との interlocked chain を表現)
> **V5 要素**: #14 「PoC = Scrum × Reverse 連携 matrix」(Scrum 6 type × Reverse 5 type = 30 cell)
> **依存**: PLAN-091 (frontmatter 語彙正本) + PLAN-092 (poc_validation_log table の DB 基盤)

---

## §1. 目的

HELIX の Scrum モード (S0-S4 仮説検証) と Reverse モード (R0-R4 設計復元) を独立した孤立フローから **interlocked chain** へ拡張する。

PoC (Scrum) で仮説検証した成果を「どの Reverse type で文書化すべきか」を **30 cell matrix** で機械決定し、`helix scrum decide --confirmed --reverse-merge` で S4 → R0 の自動 routing を実現する。

---

## §2. 背景・課題

### 現状の問題

| 問題 | 詳細 |
|---|---|
| Scrum / Reverse 独立孤立 | S4 `decide --confirmed` 後、Reverse フローへの橋渡しが手動・属人的 |
| PoC 成果の Forward 接続漏れ | 仮説検証で実装した PoC コードが設計文書化されず Forward 本実装で再実装される |
| matrix 判断基準の不在 | どの Scrum type の PoC をどの Reverse type で文書化すべきかの共通ルールがない |
| poc_validation_log 未実装 | helix.db v35 に schema だけ存在し (PLAN-092 generates 経由)、操作 module がない |

### 解決アプローチ

Scrum 6 type × Reverse 5 type の **30 cell matrix** を rule table として定義し、CLI 拡張で自動 routing を実現する。

---

## §3. 業界 standard 参照

### 3.1 Web 検索結果 (3 query 並列調査)

**Query 1: "proof of concept hypothesis driven development lifecycle 2026"**

| 参照 | Source URL | 引用箇所 |
|---|---|---|
| Scrum.org — What is a Spike? | https://www.scrum.org/resources/what-is-a-spike | §5 Scrum 6 type 分類の根拠 (spike の公式定義) |
| Agile Alliance — Spikes | https://agilealliance.org/glossary/spikes/ | hypothesis-test / tech-spike / design-spike の分類根拠 |
| Martin Fowler — Exploratory Testing | https://martinfowler.com/bliki/ExploratoryTesting.html | ux-spike の検証アプローチの業界整合 |

**Query 2: "reverse engineering existing code documentation framework 2026"**

| 参照 | Source URL | 引用箇所 |
|---|---|---|
| OMG MOF 2.0 — Model-Driven Architecture | https://www.omg.org/spec/MOF/2.0/PDF | Reverse type: code / design の設計復元モデルの業界根拠 |
| arc42 — Reverse Engineering Integration | https://docs.arc42.org/section-1/ | R0-R4 段階的文書化の業界整合 (arc42 §1 は目的・要件から始める) |
| Refactoring.guru — Design Pattern Catalog | https://refactoring.guru/design-patterns/catalog | Reverse type: normalization (設計 drift 正規化) の参照 |

**Query 3: "Scrum spike PoC validation lifecycle 2026"**

| 参照 | Source URL | 引用箇所 |
|---|---|---|
| SAFe — Spikes | https://www.scaledagileframework.com/spikes/ | perf-spike / security-spike の位置付け (SAFe enabler spike) |
| Mike Cohn — Spikes | https://www.mountaingoatsoftware.com/blog/spikes | Scrum spike の time-box + validated 判定基準 |
| Basecamp Shape Up — Uncertainty Reduction | https://basecamp.com/shapeup/1.5-chapter-06 | PoC → confirmed/rejected 決定フローの業界整合 |

### 3.2 業界 standard との整合まとめ

- **Scrum spike (Scrum.org / SAFe)**: spike は time-boxed な実験であり、結果は confirmed / rejected として Sprint Review で共有する。本 PLAN の Scrum 6 type は spike 分類の体系化。
- **arc42 逆引き設計**: arc42 は既存システムの設計文書化において「目的から始め、制約・コンテキストを明示する」アプローチを採る。本 PLAN の Reverse R0-R4 との整合が取れている。
- **SAFe enabler spike**: perf-spike / security-spike は SAFe の enabler story に相当し、技術的不確実性の解消を目的とする。これは Reverse type: upgrade (新版差分設計) / normalization (drift 解消) と対応する。

---

## §4. V5 framework 担当要素

本 PLAN は V5 18 要素のうち **#14 PoC = Scrum × Reverse 連携 matrix** を実装する。

| V5 要素 | 内容 | 本 PLAN の実装 |
|---|---|---|
| #14 | PoC = Scrum × Reverse 連携 matrix | 30 cell matrix / CLI 拡張 / poc_validation_log module |

関連する隣接要素:
- **#2** (V-model layer × drive matrix): `drive: scrum+reverse` の複合 drive 対応
- **#13** (V-model TDD 駆動): Scrum S2 PoC 実装 → S3 verify でテスト設計 pair が必要
- **#8** (PostToolUse 自動登録): `helix scrum decide --confirmed` 時に poc_validation_log を DB 登録

---

## §5. Scrum 6 type 定義

HELIX Scrum モードで仮説検証を行う際、仮説の性質に応じて以下の 6 type に分類する。

> **注**: この 6 type は `helix scrum` の上位仮説検証フローに対応する新規分類であり、
> 既存の `scrum_trigger.py` の `VALID_SCRUM_TYPES` (poc/ui/unit/sprint/post-deploy) とは別概念。
> 既存 VALID_SCRUM_TYPES は helix.db scrum_trigger テーブルの種別であり、本 6 type はそれより上位の仮説分類レイヤー。

| Scrum type | 短縮 | 定義 | 典型仮説例 | time-box 目安 |
|---|---|---|---|---|
| **hypothesis-test** | HT | 新機能・新施策の市場 fit / ユーザー価値を検証する | 「X 機能を追加するとユーザーの retention が 10% 向上する」 | 1-2 Sprint |
| **tech-spike** | TS | 新技術・新ライブラリの実現可能性・統合難易度を検証する | 「gRPC streaming を HELIX CLI に統合できるか」 | 0.5-1 Sprint |
| **design-spike** | DS | UX / アーキテクチャの設計案を PoC レベルで比較検証する | 「event-sourced vs state-store どちらが監査要件を満たすか」 | 0.5-2 Sprint |
| **perf-spike** | PS | latency / throughput / memory の性能目標達成可能性を検証する | 「SQLite ATTACH transaction が 1000 req/s を維持できるか」 | 0.5-1 Sprint |
| **security-spike** | SS | 脅威モデル仮説の実現性・緩和策の有効性を検証する | 「hook bypass 攻撃が exit 2 guard で完全に防げるか」 | 0.5-1 Sprint |
| **ux-spike** | UX | ユーザーの受容性・認知モデルの妥当性を検証する | 「CLI の色付き出力が初回利用者の理解を促進するか」 | 0.5-1 Sprint |

### 5.1 Scrum type の選択フロー

```
仮説を受領
  ├─ 「市場 fit / ビジネス価値」を問う → hypothesis-test
  ├─ 「新技術の実現可能性」を問う → tech-spike
  ├─ 「設計案の優劣」を問う → design-spike
  ├─ 「性能目標の達成可能性」を問う → perf-spike
  ├─ 「セキュリティ脅威の緩和可能性」を問う → security-spike
  └─ 「ユーザー受容性」を問う → ux-spike
```

---

## §6. Reverse 5 type 定義

SKILL_MAP.md §Reverse type matrix に準拠した 5 type (read-only 参照、変更禁止)。

| Reverse type | 短縮 | 起点 | 典型プロジェクト |
|---|---|---|---|
| **code** | CD | 既存コード + DB + 設定 + 運用実態 | R1 契約抽出が中核、R0-R4 全段階実施 |
| **design** | DG | デザイン資産 | R1 skip、R2 で DAG/実装順を起こす |
| **upgrade** | UP | 既存版 + 新版の version diff | R2 設計差分、RGC skip |
| **normalization** | NM | 設計 drift の正規化 | R1 skip、R2 で normalize 設計 |
| **fullback** | FB | 実装完遂後の文書整合 | R0 実装証拠、R1 文書 gap 抽出 |

---

## §7. Scrum × Reverse 30 cell matrix

「どの Scrum type で confirmed された PoC は、どの Reverse type で文書化すべきか」を機械決定する rule table。

> **凡例**:
> - **Primary**: 最優先の Reverse type (--reverse-type を省略した場合のデフォルト)
> - **Alternative**: 状況によって選択可能な代替 Reverse type
> - 「-」: 通常は選択しない (不適切だが技術的には可能)

| Scrum type \ Reverse type | code (CD) | design (DG) | upgrade (UP) | normalization (NM) | fullback (FB) |
|---|---|---|---|---|---|
| **hypothesis-test (HT)** | **Primary** | Alternative | - | - | Alternative |
| **tech-spike (TS)** | Alternative | **Primary** | Alternative | - | - |
| **design-spike (DS)** | - | **Primary** | - | Alternative | Alternative |
| **perf-spike (PS)** | - | - | **Primary** | Alternative | Alternative |
| **security-spike (SS)** | Alternative | Alternative | - | **Primary** | - |
| **ux-spike (UX)** | - | **Primary** | - | Alternative | Alternative |

### 7.1 30 cell ルール詳細

各セルに「採用理由 + R0 での証拠収集方針」を記述する。

#### hypothesis-test × code (Primary)
- **理由**: 市場 fit 検証は実装証拠 (コード + 動作ログ) から設計を復元するのが最適。R0 で PoC 実装コードを証拠収集し、R1 でユーザー動作の観測契約を抽出する。
- **R0 証拠**: PoC 実装コード + A/B test ログ + 計測スクリプト

#### hypothesis-test × design (Alternative)
- **理由**: UX 仮説や情報アーキテクチャ仮説では、デザイン資産 (モックアップ + state-events) から設計を復元する方が効率的。

#### hypothesis-test × fullback (Alternative)
- **理由**: PoC 実装が本実装水準に近い場合、fullback (実装完遂後の文書整合) として扱う。

#### tech-spike × design (Primary)
- **理由**: 技術スパイクの成果はアーキテクチャ判断 (どの技術を選ぶか) に集約される。R2 で設計 DAG を起こして As-Is 設計を復元するのが最適。R1 は skip 可。
- **R0 証拠**: PoC 実装 + 技術比較メモ + benchmark 結果

#### tech-spike × code (Alternative)
- **理由**: スパイクが具体的な実装コード (プロトタイプ) を生成した場合、code type で R1 契約抽出を行う。

#### tech-spike × upgrade (Alternative)
- **理由**: 新技術を既存システムに統合する場合、upgrade type (version diff) で設計差分を文書化する。

#### design-spike × design (Primary)
- **理由**: 設計案比較の成果はアーキテクチャ記録として残すべき。R2 で選択設計の DAG を起こす。
- **R0 証拠**: 設計案 A/B + 比較評価表 + 決定根拠

#### design-spike × normalization (Alternative)
- **理由**: スパイクが既存設計の drift を発見した場合、normalization type で正規化する。

#### design-spike × fullback (Alternative)
- **理由**: 設計スパイクが実装まで完遂した場合、fullback として文書整合を行う。

#### perf-spike × upgrade (Primary)
- **理由**: 性能検証の成果は「新版が old 版に対してどれだけ改善したか」の差分として設計文書化するのが最適。upgrade type の R2 で設計差分を記録する。
- **R0 証拠**: benchmark スクリプト + 計測結果 + 環境設定

#### perf-spike × normalization (Alternative)
- **理由**: 性能スパイクが既存実装の設計 drift (不必要な N+1 クエリ等) を発見した場合、normalization type で正規化設計を起こす。

#### perf-spike × fullback (Alternative)
- **理由**: 性能改善が実装まで完遂した場合、fullback として文書整合を行う。

#### security-spike × normalization (Primary)
- **理由**: セキュリティスパイクの成果は「脅威緩和策を設計に組み込む」正規化として文書化するのが最適。normalization type で drift を解消する。
- **R0 証拠**: 脅威モデル + 攻撃シナリオ再現スクリプト + 緩和策 PoC

#### security-spike × code (Alternative)
- **理由**: スパイクが具体的なガード実装 (hook / middleware) を生成した場合、code type で実装証拠から設計を復元する。

#### security-spike × design (Alternative)
- **理由**: セキュリティアーキテクチャ変更が必要な場合、design type で設計資産から復元する。

#### ux-spike × design (Primary)
- **理由**: UX 検証の成果はデザイン資産 (プロトタイプ + ユーザーフィードバック) から情報アーキテクチャを復元するのが最適。
- **R0 証拠**: プロトタイプ + ユーザーテスト記録 + 改善案メモ

#### ux-spike × normalization (Alternative)
- **理由**: UX スパイクが既存 UX パターンの drift (一貫性の欠如等) を発見した場合、normalization type で正規化する。

#### ux-spike × fullback (Alternative)
- **理由**: UX スパイクが実装まで完遂した場合、fullback として文書整合を行う。

---

## §8. PoC リバース合流 R0-R4 mapping

### 8.1 全体フロー

```
[Scrum モード]
S0: Backlog 構築 (仮説一覧 + 検証質問 + 成功条件)
  ↓ helix scrum init --scrum-type <type>
S1: Sprint Plan (ゴール + 対象仮説選定)
  ↓ helix scrum plan --scrum-type <type>
S2: PoC 実装 (Codex 委譲、verify/ スクリプト化)
  ↓ helix scrum poc --hypothesis <id>
S3: Verify (全検証スクリプト実行 → リグレッション蓄積)
  ↓ helix scrum verify
S4: Decide (confirmed / rejected / pivot)
  ↓ helix scrum decide --confirmed --reverse-merge [--reverse-type <type>]
       │
       ▼
[matrix lookup: scrum_type × decide_result → reverse_type]
       │
       ▼
[Reverse モード — 自動 routing]
R0: Evidence Acquisition (PoC 証拠収集)
  ↓ helix reverse <type> --from-scrum --scrum-hypothesis <id>
R1: Observed Contracts (API/DB/型の抽出)
  ↓ (scrum_type によっては skip)
R2: As-Is Design (設計復元)
  ↓
R3: Intent Hypotheses (意図仮説 + PO 検証)
  ↓
R4: Gap & Routing (差分 → Forward HELIX 接続)
  ↓
Forward HELIX (L1/L2/L3/L4 に振り分け)
```

### 8.2 R1 skip 判定

Scrum type に応じて R1 (Observed Contracts) を skip するかを matrix で決定する。

| Scrum type | Primary Reverse type | R1 実施 | skip 理由 |
|---|---|---|---|
| hypothesis-test | code | 実施 | 実装コードから契約抽出が必須 |
| tech-spike | design | skip | アーキテクチャ記録が目的、コード契約抽出不要 |
| design-spike | design | skip | デザイン資産から DAG 復元が主目的 |
| perf-spike | upgrade | 実施 | 新旧版の差分として契約変化を記録 |
| security-spike | normalization | 実施 | セキュリティ契約の正規化に必要 |
| ux-spike | design | skip | UX 資産から情報 IA 復元が主目的 |

### 8.3 CLI コマンドシーケンス例

**例 1: tech-spike confirmed → design type Reverse**

```bash
# S0-S3: 仮説検証
helix scrum init --scrum-type tech-spike
helix scrum backlog add --hypothesis H001 --title "gRPC streaming 統合可能性"
helix scrum plan
helix scrum poc --hypothesis H001
helix scrum verify
# S4: 確定 + Reverse 自動 routing
helix scrum decide --confirmed --reverse-merge --scrum-type tech-spike
# → matrix lookup: tech-spike × confirmed → design type (Primary)
# → 自動実行: helix reverse design --from-scrum --scrum-hypothesis H001
```

**例 2: hypothesis-test confirmed → code type Reverse**

```bash
helix scrum init --scrum-type hypothesis-test
helix scrum backlog add --hypothesis H002 --title "retention 向上機能"
helix scrum decide --confirmed --reverse-merge --scrum-type hypothesis-test
# → matrix lookup: hypothesis-test × confirmed → code type (Primary)
# → 自動実行: helix reverse code --from-scrum --scrum-hypothesis H002
```

**例 3: reverse-type を明示指定する場合**

```bash
# design-spike の PoC が実装まで完遂したので fullback を使う
helix scrum decide --confirmed --reverse-merge --scrum-type design-spike --reverse-type fullback
# → matrix check: design-spike × fullback → Alternative (許可)
```

---

## §9. CLI 拡張設計

### 9.1 helix scrum 拡張

#### 新規フラグ

```
helix scrum init --scrum-type <type>
  <type>: hypothesis-test | tech-spike | design-spike | perf-spike | security-spike | ux-spike
  省略時: hypothesis-test (default)

helix scrum decide --confirmed --reverse-merge [--scrum-type <type>] [--reverse-type <type>]
  --reverse-merge: Reverse モードへの自動 routing を有効化
  --scrum-type:    30 cell matrix lookup のキー (省略時は backlog から推定)
  --reverse-type:  matrix のデフォルトを override (Alternative の明示選択時)
```

#### 動作仕様

1. `--reverse-merge` が指定された場合、matrix lookup で Reverse type を決定
2. Primary の Reverse type を `helix reverse <type> --from-scrum --scrum-hypothesis <id>` で自動実行
3. `--reverse-type` が指定された場合、matrix で Alternative として許可されているか検証してから実行
4. poc_validation_log に `{hypothesis_id, scrum_type, reverse_type, result, timestamp}` を記録

### 9.2 helix reverse 拡張

#### 新規フラグ (from-scrum サブコマンドへの追加)

```
helix reverse from-scrum --scrum-loop-id <id> [--reverse-type <type>] [--scrum-hypothesis <id>]
  --scrum-hypothesis:  Scrum backlog の hypothesis ID (H001 等)
  --reverse-type:     matrix で決定された Reverse type (省略時は from-scrum が推定)
```

> **注**: `from-scrum` サブコマンドは既存実装済み (`cmd_from_scrum` / `reverse_local.init_from_scrum`)。
> `--scrum-hypothesis` フラグを追加し、poc_validation_log との連携を追加する。

### 9.3 matrix lookup アルゴリズム

```python
# scrum_reverse_matrix.py の中核ロジック (概要)
MATRIX = {
    ("hypothesis-test", "code"):          "primary",
    ("hypothesis-test", "design"):        "alternative",
    ("hypothesis-test", "fullback"):      "alternative",
    ("tech-spike",      "design"):        "primary",
    ("tech-spike",      "code"):          "alternative",
    ("tech-spike",      "upgrade"):       "alternative",
    ("design-spike",    "design"):        "primary",
    ("design-spike",    "normalization"): "alternative",
    ("design-spike",    "fullback"):      "alternative",
    ("perf-spike",      "upgrade"):       "primary",
    ("perf-spike",      "normalization"): "alternative",
    ("perf-spike",      "fullback"):      "alternative",
    ("security-spike",  "normalization"): "primary",
    ("security-spike",  "code"):          "alternative",
    ("security-spike",  "design"):        "alternative",
    ("ux-spike",        "design"):        "primary",
    ("ux-spike",        "normalization"): "alternative",
    ("ux-spike",        "fullback"):      "alternative",
}

def lookup_primary(scrum_type: str) -> str:
    """Get Primary Reverse type for a given Scrum type."""
    for (st, rt), role in MATRIX.items():
        if st == scrum_type and role == "primary":
            return rt
    raise ValueError(f"No primary mapping for scrum_type={scrum_type}")

def validate_routing(scrum_type: str, reverse_type: str) -> bool:
    """Return True if the reverse_type is Primary or Alternative for the given scrum_type."""
    return MATRIX.get((scrum_type, reverse_type)) in ("primary", "alternative")
```

---

## §10. 段階導入計画

### Phase 1 (P1): matrix 表 doc 化 (本 PLAN §7 = 完了)

- 30 cell matrix を docs として確定
- ADR-028 で L2 大局判断を凍結
- tl-advisor adversarial check を通過させて matrix 設計を固める

**成果物**: PLAN-095.md §7 + ADR-028.md

### Phase 2 (P2): CLI 拡張実装

- `cli/helix-scrum`: `--scrum-type` + `--reverse-merge` フラグ追加
- `cli/helix-reverse`: `--scrum-hypothesis` フラグ追加
- `cli/lib/scrum_reverse_matrix.py`: matrix lookup engine 実装
- `cli/lib/poc_validation_log.py`: poc_validation_log テーブル操作 module 実装
- 実装委譲: Codex se

**着手条件**: PLAN-092 (helix.db v35 poc_validation_log table) が実装済みであること

### Phase 3 (P3): テスト実装 + poc_validation_log 自動記録

- `cli/lib/tests/test_scrum_reverse_matrix.py`: 30 cell mapping 検証 (fake hypothesis fixture)
- `helix scrum decide --confirmed --reverse-merge` E2E シナリオテスト
- poc_validation_log への自動記録動作確認
- py_compile + pytest で全回帰確認

---

## §11. テスト戦略

### 11.1 単体テスト: test_scrum_reverse_matrix.py

```python
# テストケース構成 (fake hypothesis fixture 使用)
class TestMatrixLookup:
    def test_lookup_primary_hypothesis_test(self):
        assert lookup_primary("hypothesis-test") == "code"

    def test_lookup_primary_tech_spike(self):
        assert lookup_primary("tech-spike") == "design"

    def test_lookup_primary_design_spike(self):
        assert lookup_primary("design-spike") == "design"

    def test_lookup_primary_perf_spike(self):
        assert lookup_primary("perf-spike") == "upgrade"

    def test_lookup_primary_security_spike(self):
        assert lookup_primary("security-spike") == "normalization"

    def test_lookup_primary_ux_spike(self):
        assert lookup_primary("ux-spike") == "design"

    def test_validate_routing_primary(self):
        assert validate_routing("hypothesis-test", "code") is True

    def test_validate_routing_alternative(self):
        assert validate_routing("hypothesis-test", "design") is True

    def test_validate_routing_invalid(self):
        assert validate_routing("hypothesis-test", "upgrade") is False

    # 全 30 cell を検証 (18 Primary/Alternative + 12 無効セル)
    def test_all_30_cells(self):
        # Primary: 6 cells
        # Alternative: 12 cells
        # Invalid: 12 cells
        ...
```

### 11.2 テスト設計 trace

| テスト設計 | 対応する設計 artifact | DoD |
|---|---|---|
| test_scrum_reverse_matrix.py | 本 PLAN §7 (30 cell matrix) | 30 cell 全件 pass |
| E2E シナリオ (helix scrum decide) | §8 (PoC リバース合流フロー) | --reverse-merge で Reverse 自動起動 |
| poc_validation_log 記録テスト | §9 (CLI 拡張設計) + PLAN-092 DB schema | log 記録 + query 取得 pass |

---

## §12. DoD (Definition of Done)

### Phase 1 (doc 化)
- [ ] 30 cell matrix が §7 に確定記述済み
- [ ] ADR-028 起票完了 + tl-advisor adversarial check 通過
- [ ] PLAN-091 の frontmatter 語彙と整合している

### Phase 2 (CLI 実装)
- [ ] `helix scrum init --scrum-type tech-spike` が動作する
- [ ] `helix scrum decide --confirmed --reverse-merge` が Primary Reverse type を自動起動する
- [ ] `--reverse-type` を Alternative で指定した場合に許可され、Primary 以外を指定した場合に reject する
- [ ] scrum_reverse_matrix.py が py_compile を通過する
- [ ] poc_validation_log.py が py_compile を通過する

### Phase 3 (テスト)
- [ ] test_scrum_reverse_matrix.py が 30 cell 全件 pass する
- [ ] `pytest cli/lib/tests/test_scrum_reverse_matrix.py` が pass する
- [ ] 全回帰 `cli/helix test` が pass する

---

## §13. V-model 4 artifact trace

```
① 設計 (本 PLAN §7 30 cell matrix + §8 フロー図)
   ←対応→
③ テスト設計 (別 file 計画: docs/v2/L4-test-design/PLAN-095-unit-test-design.md、別 session 起票。本 PLAN §11 はテスト戦略概要のみ)

② 実装コード (cli/lib/scrum_reverse_matrix.py / cli/helix-scrum 拡張)
   ←対応→
④ テストコード (cli/lib/tests/test_scrum_reverse_matrix.py)
```

| Artifact | ファイル | 双方向 reference |
|---|---|---|
| ① 設計 | 本 PLAN §7-§9 | → ③ テスト設計: 本 PLAN §11 |
| ② 実装コード | cli/lib/scrum_reverse_matrix.py | → ① 設計: 本 PLAN §7 30 cell matrix |
| ③ テスト設計 | docs/v2/L4-test-design/PLAN-095-unit-test-design.md (別 session 起票予定) | → ① 設計: 本 PLAN §7 30 cell matrix / → ④ テストコード: test_scrum_reverse_matrix.py。本 PLAN §11 はテスト戦略概要のみ、詳細ケース設計は別 file |
| ④ テストコード | cli/lib/tests/test_scrum_reverse_matrix.py | → ③ テスト設計: 本 PLAN §11 DoD |

---

## §14. 関連

- **親 PLAN**: [PLAN-MM-001](PLAN-MM-001-v5-framework-master-plan.md)
- **前段 PLAN**: [PLAN-091](PLAN-091-v5-framework-core.md) (frontmatter 語彙正本)
- **DB 基盤**: [PLAN-092](PLAN-092-posttooluse-plan-auto-register.md) (poc_validation_log table)
- **ADR snapshot**: [ADR-028](../adr/ADR-028-poc-scrum-reverse-matrix-decision.md)
- **Scrum フロー**: skills/SKILL_MAP.md §HELIX Scrum
- **Reverse type matrix**: skills/SKILL_MAP.md §Reverse type matrix
- **既存 CLI**: cli/helix-scrum / cli/helix-reverse
- **既存 lib**: cli/lib/scrum_local.py / cli/lib/reverse_local.py
