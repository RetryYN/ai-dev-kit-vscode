---
name: retrofit
description: 既存システムの依存更新・基盤移行・構成変更を、要件を保ったまま段階的に実施する改修モード。retrofit-matrix + config を生成し L4-L9 追補で Forward HELIX に接続する
metadata:
  helix_layer: L4-L9
  category: workflow
  triggers:
    - 依存・フレームワーク・基盤の更新または移行時
    - レガシー脱却・構成変更が必要なとき
    - 要件は概ね維持したまま環境を移すとき
    - PLAN kind=retrofit 起票時
    - retrofit-matrix 作成時
    - 段階移行・並行稼働設計時
    - データ整合性・ロールバック計画が必要なとき
  verification:
    - "retrofit-matrix に旧→新の対応マッピングが全件記載"
    - "移行計画にロールバック手順が明記"
    - "段階移行の各フェーズに回帰テスト実行が紐付く"
    - "検証ゲート (L8/L9) 通過後に旧環境廃止"
compatibility:
  claude: true
  codex: true
---

# Retrofit スキル（改修・移行モード）

## 目的

既存システムの依存・基盤・構成を、**要件を変えずに** 新環境へ段階的に移行する。

振る舞いの不変を保ちながら環境・構造の移行を完遂し、移行後の状態を L8/L9 回帰テストで保証する。

正本: [HELIX-workflows/helix-process/retrofit-workflow.md](../../../HELIX-workflows/helix-process/retrofit-workflow.md)

---

## 責務境界（重要）

近接する 4 つのモード・スキルとの境界を厳密に分ける。

| スキル / モード | 守備範囲 | Retrofit との違い |
|---|---|---|
| `workflow/retrofit`（本スキル） | 依存・基盤・構成の移行、要件は維持 | 機能を増やさない、コード内部構造の変更にとどまらない |
| `common/refactoring` | コード内部の構造改善、外部振る舞い不変 | ファイル・モジュール単位の内部整理であり、環境移行は対象外 |
| `advanced/migration` | データ移行・DB マイグレーション中核 | DB / データ移行の実装詳細を担当、Retrofit の Step 4 で連携 |
| `workflow/reverse-analysis` (upgrade type) | 既存 system + 新版の影響評価 (R0-R4) | 設計の gap を確認する前段。Retrofit の Step 2 (影響評価) に合流 |

使い分けルール:

- **コード内部だけの整理** → `common/refactoring`
- **新機能追加を伴う** → `workflow/add-feature-workflow` (Add-feature モード)
- **既存コードから設計を復元して把握する** → `workflow/reverse-analysis`
- **DB / データ移行の実装詳細** → `advanced/migration` (Retrofit Step 4 から呼ぶ)
- **依存・基盤・構成の移行で要件を維持** → 本スキル (`workflow/retrofit`)

---

## 使用タイミング

以下のいずれかに該当したら適用する。

- フレームワーク・ライブラリの major バージョンアップ
- 実行環境の移行（Python 3.9 → 3.12、Node 18 → 22 等）
- インフラ移行（オンプレ → クラウド、コンテナ化、ランタイム変更）
- 設定ファイル・秘密情報管理の構成変更
- モノリス → マイクロサービス等の段階的アーキテクチャ移行
- CI/CD パイプラインの基盤移行

該当しない場合は「Retrofit スキップ（理由: ...）」を記録して Forward に戻す。

---

## 位置づけ（モード比較）

| 観点 | Forward（新規） | Retrofit（改修・移行） | Refactor（構造改善） |
|---|---|---|---|
| 目的 | 新機能を作る | 環境・構成を移す | コード内部を整理する |
| 要件変更 | あり | なし（概ね維持） | なし |
| PLAN kind | design / impl | retrofit | refactor |
| 成果物 | design + module | retrofit-matrix + config | （設計文書不要） |
| Forward 接続 | L4-L7 主体 | L4/L5 追補 → L8/L9 回帰 | G4 後に commit |

---

## 基本フロー

```
Step 1: 現状把握
  ↓
Step 2: 影響評価（retrofit-matrix 作成）
  ↓
Step 3: 移行計画（段階・順序・ロールバック）
  ↓
Step 4: 段階移行（config 更新・並行稼働）
  ↓
Step 5: 検証（回帰・性能・データ整合性）
  ↓
Forward 接続（L4/L5 追補 → L8/L9 回帰）
```

---

## Step 1: 現状把握

移行対象の構造・依存を把握する。

確認項目:

- 移行対象コンポーネント / モジュール一覧
- 現行の依存バージョン一覧（`requirements.txt` / `package.json` 等）
- 外部 API・DB スキーマ・設定ファイルの依存関係
- 既存テストカバレッジ（回帰テストの有無と範囲）

出力:

- 現状スナップショット（移行対象一覧 + 依存グラフ概要）

Reverse upgrade type (R0-R1) を先行させると影響評価精度が上がる。不確実性が高い場合は `helix codex --role tl --task "retrofit現状把握"` で TL に依頼する。

---

## Step 2: 影響評価（retrofit-matrix 作成）

移行の影響範囲を retrofit-matrix に整理する。

```markdown
# retrofit-matrix: {slug}

| 対象 | 旧バージョン / 旧構成 | 新バージョン / 新構成 | 影響範囲 | 優先度 | 備考 |
|------|----------------------|----------------------|----------|--------|------|
| 例: FastAPI | 0.99.x | 0.115.x | routes/*.py, middleware/ | High | startup_event → lifespan 変更 |
| 例: Python | 3.9 | 3.12 | 全体 | Critical | type hint 変更, asyncio 挙動 |
```

フィールド定義:

- **影響範囲**: ファイルパス / モジュール名を具体的に記載
- **優先度**: Critical / High / Medium / Low（影響が広いほど先に移行）
- **備考**: 破壊的変更の要点、Migration guide URL

生成先: `docs/plans/<slug>-retrofit-matrix.md`

---

## Step 3: 移行計画

段階・順序・ロールバック手順を決める。

### 段階設計

原則として「影響範囲が小さく・依存が少ないもの」から移行する。

```yaml
# retrofit-plan.yaml
phases:
  - id: phase-1
    name: 開発環境・CI 先行移行
    targets:
      - pyenv / .python-version
      - requirements-dev.txt
      - .github/workflows/ci.yml
    rollback: git revert + pyenv local <旧バージョン>
    acceptance:
      - CI pipeline が新環境で全 PASS
  - id: phase-2
    name: ライブラリ段階更新
    targets:
      - requirements.txt の Major 更新対象
    rollback: pip install -r requirements.lock (旧)
    acceptance:
      - pytest 全件 PASS
      - import エラー 0 件
  - id: phase-3
    name: 本番環境移行
    targets:
      - Dockerfile / runtime.txt
      - 本番設定ファイル
    rollback: blue-green デプロイの旧環境へ切り戻し
    acceptance:
      - smoke test PASS
      - SLO 24h 安定確認
```

### ロールバック要件

- 各フェーズに **独立したロールバック手順** を持つ
- ロールバック手順は事前に演練（dry-run）する
- 本番移行は blue-green または canary を原則とする

---

## Step 4: 段階移行（config 更新・並行稼働）

計画に従い、フェーズごとに移行を実施する。

実施パターン:

| パターン | 適用場面 | 特徴 |
|---|---|---|
| 逐次移行 | 依存が連鎖する場合 | 安全だが時間がかかる |
| 並行稼働 | 旧・新環境を同時維持できる場合 | リスクが低いが維持コスト高 |
| feature flag | ライブラリ切り替えを段階適用 | ロールバックが容易 |
| ストラングラーフィグ | モノリス → マイクロ移行 | 長期化するが安全 |

実行:

```bash
# Codex TL へ移行実装を委譲する場合
helix codex --role tl --task "retrofit Step 4: <phase-N> 移行実装" \
  --reference-doc docs/plans/<slug>-retrofit-matrix.md

# SE への実装委譲
helix codex --role se --task "retrofit config 更新: <対象ファイル>"
```

---

## Step 5: 検証

移行後の品質を 3 観点で確認する。

### 5-1 回帰テスト

```bash
# 全回帰テスト
helix test

# 対象モジュールに絞った回帰
pytest <module>/ -v --tb=short
```

合格基準:

- 移行前と同一のテスト結果（fail 件数の増加なし）
- 新規 warning の抑制（DeprecationWarning 等を要確認）

### 5-2 性能テスト

移行前後で SLO に影響する性能劣化がないことを確認する。

- baseline: 移行前の p50 / p95 latency
- threshold: 移行後の劣化率 ≤ 5%（チームの SLO 定義に準拠）

### 5-3 データ整合性確認（DB 移行を伴う場合）

```bash
# migration の整合性確認
helix codex --role dba --task "retrofit データ整合性チェック: <対象テーブル>"
```

確認項目:

- マイグレーション前後のレコード件数一致
- NULL / 型変換の不整合なし
- 外部キー制約の成立

---

## 起票する PLAN kind

```yaml
# PLAN frontmatter（V2 形式）
kind: retrofit
process_layer: L4
generates:
  - artifact_type: retrofit-matrix
    path: docs/plans/<slug>-retrofit-matrix.md
  - artifact_type: config
    path: cli/config/<slug>.yaml
dependencies:
  requires:
    - <前段 PLAN の ID（現状把握・Reverse upgrade type 等）>
```

逸脱が発生した場合の kind 対応は `HELIX-workflows/helix-process/deviation-plan-map.md` を参照する。

---

## Forward 接続

```
Retrofit 完了
  ↓
L4 基本設計追補（アーキテクチャ変更を伴う場合）
L5 詳細設計追補（API / DB 変更を伴う場合）
  ↓
L8 結合テスト（依存変更の結合検証）
L9 総合テスト（回帰・性能・E2E の全量確認）
  ↓
[要件が変わる場合のみ]
  → L1 要件定義 / L3 要件定義 へ差戻し
```

接続ルール:

- 要件変更なし → L4/L5 追補のみ（L1/L3 差戻し不要）
- インターフェース変更あり → L5 詳細設計 (D-API) を追補してから L7 実装
- 要件そのものが変わる → L1 または L3 へ差戻し、Forward を最初から通す

---

## エスカレーション基準

以下は人間確認にエスカレーションする。

- 本番データの不可逆変換（削除・型変換・暗号化変更）
- 認証・認可・決済・PII に触れる移行
- ロールバック手順が機能しない
- 移行後の性能劣化が SLO 閾値を超える
- 要件が「概ね維持」の範囲を超えると判断される

エスカレーション提出物:

- retrofit-matrix の現状（問題箇所を明示）
- 試みたロールバック手順とその結果
- 推奨対処案と代替案

---

## 完了チェック（実務用）

- retrofit-matrix が `docs/plans/<slug>-retrofit-matrix.md` に存在する
- 各 phase にロールバック手順が明記されている
- L8 結合テストが PASS している
- L9 総合テスト（回帰）が PASS している
- 旧環境・旧設定の廃止が記録されている

---

## 関連スキル / コマンド

| スキル / コマンド | 用途 |
|---|---|
| `workflow/reverse-analysis` (upgrade type) | 影響評価の前段（旧→新の差分を R0-R4 で把握） |
| `advanced/migration` | DB / データ移行の実装詳細 |
| `common/refactoring` | コード内部整理（Retrofit と組み合わせ可） |
| `workflow/verification` | L8/L9 回帰テスト設計 |
| `workflow/observability-sre` | 移行後の SLO 監視 |
| `helix codex --role tl` | 設計・移行計画の実施 |
| `helix codex --role se` | 移行実装の委譲 |
| `helix codex --role dba` | DB 移行・整合性確認 |

---

## references

- [retrofit-workflow.md（正本）](../../../HELIX-workflows/helix-process/retrofit-workflow.md)
- [deviation-plan-map.md（kind 逸脱対応）](../../../HELIX-workflows/helix-process/deviation-plan-map.md)
- [reverse-analysis SKILL.md（upgrade type 前段）](../reverse-analysis/SKILL.md)
- [references/retrofit-matrix-template.md（matrix テンプレート詳細）](references/retrofit-matrix-template.md)
