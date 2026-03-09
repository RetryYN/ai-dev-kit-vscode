---
name: reverse-analysis
description: 既存コードから設計を逆抽出し、あるべき姿とのギャップを特定して修正計画を立案するリバースエンジニアリングフロー
metadata:
  helix_layer: all
  triggers:
    - 設計書なし・テストなしの既存コード改修時
    - レガシーシステムの現状把握時
    - 技術的負債の全体評価時
    - 新規メンバーのオンボーディング（大規模コードベース理解）
  verification:
    - "R0: evidence_map に対象モジュール 100% 含有"
    - "R1: 観測契約の confidence ≥ high が 80% 以上"
    - "R2: ADR 仮説に contradictions 0 件（未解決）"
    - "R3: PO 検証済み仮説率 ≥ 80%"
    - "R4: gap_register の全項目に routing 割当済み"
compatibility:
  claude: true
  codex: true
---

# Reverse Analysis スキル（HELIX Reverse）

## 概要

既存の HELIX は L1→L8 のフォワードフロー（要件→設計→実装→検証）を前提とする。
本スキルは**逆方向**のフローを定義し、「設計書なし・テストなし・動いてるコード」から設計を復元し、あるべき姿とのギャップを特定して通常 HELIX に接続する。

### 核心の違い

| | Forward HELIX | HELIX Reverse |
|--|---------------|---------------|
| 入力 | 要件（確定事実） | コード（観測対象） |
| 各層の出力 | 定義・決定（凍結対象） | **仮説**（検証対象） |
| ゲートの性質 | 完全性・凍結判定 | **証拠十分性・反証可能性** |
| 差分分析 | 終端（L6/L8） | **各層でインライン実施** |

---

## フロー

```
R0  Evidence Acquisition（証拠収集）
  ↓ RG0  証拠網羅ゲート
R1  Observed Contracts（観測契約抽出）
  ↓ RG1  契約検証ゲート
R2  As-Is Design（現行設計復元）
  ↓ RG2  設計検証ゲート
R3  Intent Hypotheses（意図仮説 + PO検証）
  ↓ RG3  仮説検証ゲート
R4  Gap & Routing（差分集約 + Forward接続）
  ↓
Forward HELIX（Gap 種別で L1/L2/L3/L4 に振り分け）
  ↓
RGC  Gap Closure（ギャップ閉塞検証 + 成果物昇格）
```

**各層は Observe → Hypothesize → Verify の小ループを内包する。**

---

## R0: Evidence Acquisition（証拠収集）

### 目的
コードだけでなく、システムの全体像を構成する証拠を網羅的に収集する。

### 対象（コード以外も含む）
- ソースコード（全モジュール）
- DB 実体（テーブル・インデックス・マイグレーション履歴）
- 設定ファイル（env, config, feature flags）
- ジョブ・バッチ定義（cron, queue workers）
- 外部接続（API クライアント、Webhook、メール送信）
- 権限境界（認証・認可の実装箇所）
- 運用実態（ログ、監視、アラート設定）
- 既存テスト（カバレッジ、テスト種別）
- Git 履歴（変更頻度、ホットスポット）

### 小ループ
1. **Observe**: ファイルツリー・依存グラフ・DB スキーマをスキャン
2. **Hypothesize**: モジュール境界・主要フローを仮識別
3. **Verify**: 実行/テスト実行で仮説を検証。動かせない場合は `unverified` タグ

### 成果物
```yaml
evidence_map:
  modules:
    - name: "auth"
      files: ["src/auth/**"]
      test_coverage: 45%
      doc_coverage: 0%
      external_deps: ["OAuth provider"]
      hotspot_score: high  # Git 変更頻度
  db_schema:
    tables: 42
    migrations: 78
    undocumented_columns: 15
  runtime_topology:
    services: ["api", "worker", "scheduler"]
    external_apis: ["stripe", "sendgrid"]
  unknowns:
    - "src/legacy/processor.py — 500行、テストなし、最終変更2年前"
    - "DB: audit_log テーブルの用途不明"
```

### 担当モデル
- Codex 5.2: 大規模コード精読・スキャン
- Haiku 4.5: 外部依存・ライブラリ調査

### legacy スキルとの関係
legacy スキルの「レガシー度判定」「特性テスト」は R0 の**必須技法**として前倒し配置する（後続実行手段ではない）。

---

## R1: Observed Contracts（観測契約抽出）

### 目的
コードから API 契約・DB スキーマ・型定義を**機械的に抽出**し、観測された契約として記録する。

### 対象
- API エンドポイント（ルーティング定義 → リクエスト/レスポンス型）
- DB スキーマ（テーブル定義 → リレーション → 制約）
- 型定義（フロントエンド ↔ バックエンド ↔ DB の型マッピング）
- 内部契約（モジュール間 interface / export）

### テスト設計（characterization probes）は R1 の成果物ではない
R0 の evidence を基に R1 が契約を抽出した後、**characterization tests はその検証手段**として R1→RG1 の間で実行する。契約抽出と検証設計を同層に混ぜない。

### 小ループ
1. **Observe**: ルーティング・ハンドラ・モデル定義から契約を機械抽出
2. **Hypothesize**: 暗黙の契約（undocumented endpoints, hidden constraints）を推定
3. **Verify**: characterization tests / golden master tests で実際の振る舞いと照合

### インライン差分（code ↔ contract）
```yaml
r1_gaps:
  - type: "undocumented_endpoint"
    location: "POST /api/internal/sync"
    confidence: low
    classification: pending  # bug | drift | intentional | unknown
  - type: "schema_drift"
    location: "users.legacy_role column — コードでは未参照"
    confidence: high
    classification: drift
```

### 成果物
```yaml
observed_contracts:
  api:
    endpoints: 47
    documented: 12
    confidence_high: 35
    confidence_low: 12
  db:
    tables: 42
    fk_integrity: 89%
  types:
    fe_be_match: 72%
    be_db_match: 85%
  gaps: [r1_gaps]
```

### 担当モデル
- Codex 5.3: 機械抽出
- Codex 5.4: レビュー / RG1 ゲート判定

---

## R2: As-Is Design（現行設計復元）

### 目的
R1 の観測契約から、システムのアーキテクチャ・設計判断・パターンを復元する。

### 対象
- コンポーネント境界・依存関係グラフ
- データフロー（主要ユースケースのシーケンス）
- エラーハンドリングパターン
- セキュリティ境界（認証・認可の実装パターン）
- ADR 推定（「なぜこうなっているか」の仮説）

### 小ループ
1. **Observe**: R1 の契約 + R0 の証拠からアーキテクチャパターンを抽出
2. **Hypothesize**: 設計判断の意図を推定し ADR 仮説を立てる
3. **Verify**: adversarial-review で仮説を反証テスト

### インライン差分（contract ↔ design）
```yaml
r2_gaps:
  - type: "architectural_violation"
    description: "Controller が直接 DB クエリを実行（Service 層をバイパス）"
    modules: ["src/controllers/report.ts"]
    severity: medium
    classification: drift
  - type: "pattern_inconsistency"
    description: "認証は JWT だが、一部エンドポイントで session cookie を参照"
    severity: high
    classification: unknown  # 意図的? バグ?
```

### 成果物
```yaml
as_is_design:
  architecture:
    style: "Layered (with violations)"
    components: 8
    circular_deps: 2
  adrs:
    - id: "ADR-R001"
      title: "JWT 認証採用"
      confidence: high
      evidence: ["src/middleware/auth.ts", "config/jwt.ts"]
    - id: "ADR-R002"
      title: "PostgreSQL 選択"
      confidence: high
      evidence: ["docker-compose.yml", "migrations/"]
  patterns:
    consistent: ["Repository pattern (80%)", "DTO transform"]
    inconsistent: ["Error handling (3 patterns mixed)"]
  gaps: [r2_gaps]
```

### 担当モデル
- Codex 5.4: 設計復元 + adversarial-review
- Codex 5.3: 補助分析

---

## R3: Intent Hypotheses（意図仮説 + PO検証）

### 目的
R0-R2 の成果物から**ビジネス要件の仮説**を立て、PO に検証を求める。

### 核心の制約
コードから復元できるのは「**観測された振る舞い**」と「**意図の仮説**」であり、要件そのものではない。業務意図・優先順位・UX 判断・将来要件はコードからは復元不能。

### 振る舞い分類
| 分類 | 意味 | 対応 |
|------|------|------|
| **Intended** | PO が「正しい」と確認 | 受入条件として記録 |
| **Accidental** | 意図せず実装された振る舞い | バグとして gap_register に記録 |
| **Unknown** | PO も判断できない | 調査タスクとして gap_register に記録 |
| **Deprecated** | かつて必要だったが今は不要 | 削除候補として gap_register に記録 |

### 小ループ
1. **Observe**: R0-R2 の成果物から主要機能・ユースケースを列挙
2. **Hypothesize**: 各機能のビジネス意図・受入条件を推定
3. **Verify**: PO に仮説を提示し、Intended / Accidental / Unknown / Deprecated を判定

### インライン差分（design ↔ intent）
```yaml
r3_gaps:
  - type: "missing_requirement"
    description: "監査ログ機能が実装されているが、要件として認識されていない"
    po_verdict: intended
    action: "受入条件として正式化"
  - type: "accidental_behavior"
    description: "負の金額での注文が通る"
    po_verdict: accidental
    action: "バグ修正 → L4"
  - type: "deprecated_feature"
    description: "旧 CSV エクスポート — 2年前に UI から削除済みだが API は残存"
    po_verdict: deprecated
    action: "削除候補 → L4"
```

### 成果物
```yaml
intent_hypotheses:
  total_features: 35
  verified:
    intended: 28
    accidental: 3
    deprecated: 2
  unverified:
    unknown: 2
  coverage: 94%  # verified / total
  gaps: [r3_gaps]
```

### 担当モデル
- PM（Opus）: 仮説構造化、PO への提示準備
- TL（Codex 5.4）: accidental vs intended の技術的仕分け
- PO（人間）: 最終判定

---

## R4: Gap & Routing（差分集約 + Forward接続）

### 目的
R0-R3 の各層で発見されたインライン差分を集約し、修正の優先順位と Forward HELIX への接続先を決定する。

### Gap 集約
```yaml
gap_register:
  - gap_id: "GAP-001"
    source_layer: R1
    type: "schema_drift"
    description: "users.legacy_role — 未参照カラム"
    severity: low
    routing: L4  # 削除 = S サイズ実装タスク
  - gap_id: "GAP-002"
    source_layer: R2
    type: "architectural_violation"
    description: "Controller→DB 直接アクセス"
    severity: medium
    routing: L3  # 設計変更を伴うリファクタ
  - gap_id: "GAP-003"
    source_layer: R2
    type: "pattern_inconsistency"
    description: "認証方式の混在（JWT + session cookie）"
    severity: high
    routing: L2  # アーキテクチャ判断が必要
  - gap_id: "GAP-004"
    source_layer: R3
    type: "accidental_behavior"
    description: "負の金額での注文許可"
    severity: critical
    routing: L4  # バグ修正（セキュリティゲート該当）
  - gap_id: "GAP-005"
    source_layer: R3
    type: "missing_requirement"
    description: "GDPR データ削除要件が未定義"
    severity: critical
    routing: L1  # 要件定義から必要
```

### Gap → Forward Routing Matrix

| Gap 種別 | 典型例 | デフォルト接続先 | サイジング |
|---------|--------|----------------|-----------|
| Behavioral Defect | バグ、未検証エッジケース | L4（バグ修正） | 再サイジング |
| Contract Drift | 未参照カラム、undocumented API | L3（契約再設計） | 再サイジング |
| Architectural Debt | パターン不一致、境界違反 | L2（設計見直し） | 再サイジング |
| Requirements Gap | 未定義要件、deprecated 機能 | L1（要件定義 + PO） | 再サイジング |
| Security/Compliance | 脆弱性、法令未対応 | セキュリティゲート強制 | gate-policy 準拠 |

### 修正 vs 再設計の分岐判定

上記テーブルの接続先は**デフォルト**であり、最終 routing は以下の分岐で決定する。

```
Gap を検出
  ├─ 修正（文字列置換・設定変更・局所修正）で解消できるか？
  │   ├─ Yes → 修正コスト vs 再設計コストを比較
  │   │   ├─ 修正コスト ≤ 再設計コスト → **L4 に降格**（修正で十分）
  │   │   └─ 修正コスト > 再設計コスト → デフォルト接続先を維持
  │   └─ No（構造的問題、判断が未定義）→ デフォルト接続先を維持
  └─ Security/Compliance → 常にゲート強制（降格不可）
```

**判断基準**: gap の種別ではなく「修正と再設計のどちらのメリットが大きいか」で routing する。Architectural Debt でも10箇所の文字列置換で解消するなら L4、Behavioral Defect でも設計前提の変更が必要なら L2/L3 に昇格する。

### 優先順位決定
1. **Critical（即時）**: セキュリティ脆弱性、データ損失リスク、法令違反
2. **High（次イテレーション）**: ビジネスクリティカルなバグ、主要フローの設計問題
3. **Medium（計画的）**: 技術的負債、パターン不一致、テスト不足
4. **Low（バックログ）**: コスメティック、未参照コード、ドキュメント不足

### 成果物
```yaml
remediation_plan:
  total_gaps: 42
  by_routing:
    L1: 3   # 要件定義から
    L2: 5   # 設計見直し
    L3: 8   # 契約再設計
    L4: 26  # 実装修正
  by_severity:
    critical: 4
    high: 8
    medium: 18
    low: 12
  iteration_1:  # 最初のイテレーションで対応する Gap
    - "GAP-004: 負の金額バグ修正 (L4, critical)"
    - "GAP-005: GDPR 要件定義 (L1, critical)"
    - "GAP-003: 認証方式統一 (L2, high)"
```

### 担当モデル
- PM（Opus）: 優先順位決定、イテレーション計画
- TL（Codex 5.4）: routing 判定、技術的優先度評価

---

## RGC: Gap Closure（ギャップ閉塞検証 + 成果物昇格）

### 目的
Forward HELIX で修正を実行した後、**gap_register の各項目が本当に閉じたか**を検証し、Reverse で復元した仮説成果物を正式な設計ドキュメントに昇格させる。

### なぜ必要か
Forward HELIX の L6（統合検証）/ L8（受入）は「Forward の要件に対する検証」であり、「Reverse で発見した gap に対する検証」ではない。gap_register は Forward の L1 要件とは別系統の成果物であるため、独立した閉塞確認が必要。

### フロー

```
Forward HELIX 完了（L6/L8 pass）
  ↓
RGC-1  Gap 閉塞検証
  ↓
RGC-2  成果物昇格
  ↓
RGC-3  残存 Gap 判定
```

### RGC-1: Gap 閉塞検証

gap_register の各項目に対して、修正が実際に gap を閉じたかを検証する。

```yaml
gap_closure:
  - gap_id: "GAP-001"
    status: closed
    evidence: "users.legacy_role カラム削除済み、マイグレーション適用済み"
    verified_by: TL
  - gap_id: "GAP-002"
    status: closed
    evidence: "Controller→Service→Repository パターンに統一、テスト追加済み"
    verified_by: TL
  - gap_id: "GAP-004"
    status: closed
    evidence: "金額バリデーション追加、負値テスト追加、E2E pass"
    verified_by: TL
  - gap_id: "GAP-003"
    status: partial
    evidence: "JWT 統一は完了、session cookie 削除は次イテレーション"
    remaining: "旧 session 互換の廃止（移行期間中）"
    verified_by: TL
```

**検証手段（gap 種別別）**:

| Gap 種別 | 閉塞検証の手段 |
|---------|---------------|
| Behavioral Defect | テスト追加 + pass 確認 |
| Contract Drift | R1 の characterization tests 再実行で差分 0 |
| Architectural Debt | R2 のパターン分析再実行で violation 0 |
| Requirements Gap | R3 の PO 検証で intended 確認 |
| Security/Compliance | セキュリティゲート（gate-policy.md）準拠 |

### RGC-2: 成果物昇格

Reverse で作成した**仮説成果物**を、Forward の正式成果物に昇格させる。

| Reverse 成果物 | 昇格先 | 条件 |
|---------------|--------|------|
| observed_contracts（R1） | API 契約書（L3 正本） | RG1 pass + gap 閉塞 |
| as_is_design（R2） | 設計書（L2 正本） | RG2 pass + gap 閉塞 |
| intent_hypotheses（R3） | 要件リスト（L1 正本） | RG3 pass + PO 承認 |
| gap_register（R4） | debt_register に残存分移管 | 全 gap に status 付与 |

**昇格 = 以降の Forward フローで正本として参照可能になる。**
次回の Forward 開発は L1 要件リスト（昇格済み）をベースに開始できる。

### RGC-3: 残存 Gap 判定

| 状態 | 対応 |
|------|------|
| 全 gap closed | Reverse 完了。成果物昇格して終了 |
| partial / open あり | 残存 gap を **debt_register に移管**。次イテレーションで Forward HELIX 継続 |
| 新規 gap 発見 | 修正中に発見した新たな問題 → gap_register に追記し、次イテレーションで R4 routing |

### 担当モデル
- TL（Codex 5.4）: gap 閉塞の技術検証
- PM（Opus）: 成果物昇格判定、残存 gap のイテレーション計画
- PO（人間）: R3 成果物の昇格承認

---

## Reverse サイジング

Forward の file/line 軸ではなく、Reverse 固有の 5 軸で判定する。3 軸以上の最大サイズを採用。

| 軸 | S | M | L |
|----|---|---|---|
| モジュール境界数 | 1-3 | 4-10 | 11+ |
| 外部 IF 数 | 0-1 | 2-5 | 6+ |
| テスト/ドキュメント欠損度 | テストあり・docs 不足 | テスト部分的・docs なし | テストなし・docs なし |
| Runtime unknowns | なし | 一部（config/env 依存） | 多数（undocumented behavior） |
| Criticality | 内部ツール | ユーザー向け | 収益/コンプライアンス |

### フェーズスキップ決定木

```
├─ S（小規模）
│   └─ R0 → R1 → R4（R2/R3 skip — 設計復元・意図検証は不要）
├─ M（中規模）
│   ├─ PO 意図が明確 → R0 → R1 → R2 → R4（R3 skip）
│   └─ PO 意図が不明 → フルフロー
└─ L（大規模）→ フルフロー R0 → R1 → R2 → R3 → R4
```

---

## ゲート定義

ゲート詳細は `gate-policy.md §Reverse ゲート` を参照。

### ゲート設計原則（Forward との非対称性）

| | Forward ゲート | Reverse ゲート |
|--|---------------|---------------|
| 判定軸 | 定義の完全性 / 凍結可否 | 証拠の十分性 / 仮説の反証可能性 |
| 必須指標 | 成果物の存在・網羅性 | **coverage, confidence, contradictions, unknowns** |
| Fail 時 | 差戻し | 追加証拠収集 or 仮説修正 |

---

## 既存スキルとの関係

| 既存スキル | Reverse での使い方 |
|-----------|-------------------|
| legacy | R0 の必須技法（レガシー度判定、特性テスト） |
| verification | RG0-RG3 + RGC の検証基盤（verification/SKILL.md §15） |
| adversarial-review | RG2 の設計仮説反証 |
| api-contract | R1 の契約抽出フォーマット参照 |
| refactoring | R4 → Forward 接続後の実行手段 |
| migration | R4 → Forward 接続後の大規模移行手段 |
| code-review | R1/R2 のパターン分析補助 |

---

## チェックリスト

### Reverse 開始前

```
[ ] 対象システムのスコープが明確
[ ] アクセス権限（コード、DB、設定、ログ）確保済み
[ ] PO の参加コミットメント確認（R3 で必須）
[ ] Reverse サイジング完了
```

### R4 完了後

```
[ ] gap_register の全項目に routing 割当済み
[ ] 優先順位が PO/TL と合意済み
[ ] 最初のイテレーション計画が Forward HELIX フローに接続済み
[ ] 復元成果物（contracts, design, hypotheses）がドキュメント化済み
```

### RGC 完了後（Forward 修正後）

```
[ ] gap_register の全項目に closed / partial / open ステータス付与
[ ] closed 項目に evidence 記録済み
[ ] 仮説成果物の昇格判定完了（observed_contracts → API契約、as_is_design → 設計書、intent_hypotheses → 要件リスト）
[ ] 残存 gap は debt_register に移管済み
[ ] 新規発見 gap は gap_register に追記 + 次イテレーション routing 済み
```
