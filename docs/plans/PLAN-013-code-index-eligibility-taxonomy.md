# PLAN-013 Code Index Eligibility Taxonomy and PoC Seed Contract

## §1. 目的 / position

PLAN-011 (code-index system) では `helix.db v14` の `code_index` を中心に、コード資産の可視化と再利用判断のための metadata 基盤を導入しました。

PLAN-012 の `--uncovered` と core5 80% gate 導入により、coverage 制御の運用は開始されましたが、現時点では `eligible` 判定が「public symbol」「PoC seed」「再利用候補」を単一概念として混在して扱っており、PoC seed の再利用価値と coverage gate の責務が曖昧なままです。

本 PLAN はこの課題を解消し、以下を実現します。

1. `eligible` を `coverage_eligible` / `private_helper` / `excluded` へ整理し、seed 属性を metadata に分離する。
2. PoC seed 契約を coverage gate から独立させ、coverage は public 対象に限定して管理可能にする。
3. `cli/lib` 全体に対して warning/target の 2 段階運用を導入し、enforce は PLAN-014 以降に分離する。
4. 既存データ (`helix.db v14 code_index`, `.helix/cache/code-catalog.jsonl`) を壊さずに migration する。

本 PLAN は L1 設計として、実装方針を早期確定し、PLAN-013 内では設計凍結と契約化を主目的とします。

今回の方針は TL 5軸レビュー結果で指摘された P1/P2 リスクを反映し、conditional pass で進行します。

### §1.1 位置づけ

PLAN-013 は PLAN-011/PLAN-012 の延長です。対象は以下です。

- `code-index` における母数定義の再設計
- CLI `--uncovered` の bucket ベース拡張契約
- `plan-013.1` / PLAN-014 へつなぐ運用分離設計

対象外は、API 破壊変更や即時の全体 enforce ではありません。

### §1.2 運用前提

- TL レビューが前提で、レビューコメントは PLAN-013 仕様内で吸収する。
- L4 実装は PLAN-013 finalize 後、同 PLAN 内 sprint `.1b` まででも採用可。
- 設計反映後は実装ガードとして `cli/lib` 全体 warning gate を採用し、即時 fail は行わない。

## §2. スコープ

### §2.1 in-scope

- code-index eligible taxonomy の再定義
  - `coverage_eligible`
  - `private_helper`
  - `excluded`
  の 3 bucket
- metadata の直交属性として `seed_candidate` / `seed_promotable` を追加
- PoC seed contract を coverage gate から分離
- `setup.sh` / `skills/agent-skills/hooks/*.sh` / `verify/*.sh` を `excluded` 分類に確定
- `cli/lib` 全体に warning/target 段階の coverage gate ポリシーを導入し、既存 core5 gate と併走
- `helix.db v15` migration と `.helix/cache/code-catalog.jsonl` 再分類ロジックを規定
- PLAN-011/012 既存データへの影響を定量化
- D-CONTRACT / D-DEBT / D-MIGRATION として仕様化
- 受入条件で `--uncovered --bucket all --seed-candidate all --seed-promotable all --scope all` を JSON 3-bucket + metadata 全件分類として固定

### §2.2 out-of-scope

- deferred-findings 18件 (PLAN-002〜005,007 由来 P2) の一括解消
  - PLAN-014 候補へ別途移送
- `cli/lib` 全体 80% 目標の即時 enforce
  - PLAN-014 以降に分離
- private 関数の public 化を伴う API 破壊変更
- core5 80% gate 閾値の変更（固定）
- `--scope` 対象外の repository 横断統合（本 PLAN では実施しない）
- `excluded` の運用対象を固定 3 pattern 以外で拡張する実装（計画的に PLAN-014 で見直し）
- `seed_promotable` の自動 heuristic 運用（PLAN-014 以降）

## §3. 要件 / 設計

本章では設計要件を 7 つの subsection で凍結します。

### §3.1 3-bucket taxonomy + metadata 定義

コード index 対象を以下の 3 bucket と metadata で分離します。

| bucket | 母集団 | 用途 | 判定基準 |
|---|---|---|---|
| `coverage_eligible` | public symbol のみ | core5 / cli-lib coverage gate の母集団 | 関数名が `_` で始まらない、かつファイルが `excluded` 配下でない |
| `private_helper` | private symbol のみ | PoC 探索母集団の候補準備域 | 関数名が `_` で始まる、かつファイルが `excluded` 配下でない |
| `excluded` | operational script | gate 目的外 | `setup.sh` / `skills/agent-skills/hooks/*.sh` / `verify/*.sh` パスにマッチ |

`metadata` は bucket と直交し、以下を `code-catalog` で保持します。

| metadata | 型 | Default | 用途 |
|---|---|---|---|
| `seed_candidate` | bool | `coverage_eligible: true`, `private_helper: false`, `excluded: false` | recommender / PoC 探索母集団 |
| `seed_promotable` | bool | false | private_helper の public 化候補を手動でマーク |

`coverage_eligible` のデフォルトは `seed_candidate=true`、`private_helper` は `seed_candidate=false`（manual true 化可）、`excluded` は `seed_candidate=false`/`seed_promotable=false` 固定です。

3 pattern（`setup.sh` / `skills/agent-skills/hooks/*.sh` / `verify/*.sh`）は pattern 数であり、対象 entry 数（`setup.sh` 下配下シンボル数、hooks の符号数、verify 多数）とは別集計です。  
`setup.sh` は 8 件、`skills/agent-skills/hooks/*.sh` は 16 件、`verify/*.sh` は多数で、これは path 配下シンボル再集計が前提です。

coverage / seed 母集団:
- coverage gate: `bucket=coverage_eligible`
- seed 探索: `metadata.seed_candidate=true`（`excluded` は除外）

| excluded_patterns | 説明 |
|---|---|
| `setup.sh` | リポジトリ root の install script |
| `skills/agent-skills/hooks/*.sh` | claude code hook script |
| `verify/*.sh` | smoke / E2E 検証スクリプト |

### §3.2 classification schema

本 PLAN では D-CONTRACT として次を凍結します。

- `helix.db v15` において `code_index` テーブルへ `bucket` カラムを追加する。
- 既存の `code_index` 行は migration 時に再分類する。
- `.helix/cache/code-catalog.jsonl`（正本）各 entry に `bucket` / `metadata.seed_candidate` / `metadata.seed_promotable` 属性を保持する。
- `bucket` は `coverage_eligible|private_helper|excluded` の enum 制約を持つ。

```sql
ALTER TABLE code_index
  ADD COLUMN bucket TEXT NOT NULL DEFAULT 'coverage_eligible'
  CHECK (bucket IN ('coverage_eligible', 'private_helper', 'excluded'));
ALTER TABLE code_index
  ADD COLUMN symbol_line INTEGER;
CREATE INDEX IF NOT EXISTS idx_code_index_bucket ON code_index(bucket);
CREATE INDEX IF NOT EXISTS idx_code_index_path_bucket ON code_index(path, bucket);
CREATE INDEX IF NOT EXISTS idx_code_index_path_symbol_line ON code_index(path, symbol_line);
```

```yaml
entry_schema:
  # PLAN-011 既存
  id: string             # 必須、kebab-case dotted
  domain: string         # 必須
  summary: string        # 必須、≤80 char
  since: string | null    # 任意
  related: list[string]   # 任意
  # build 生成
  path: string
  line_no: integer        # v14 互換: @helix:index marker 行（意味変更なし、matching key には不使用）
  symbol_line: integer    # PLAN-013 canonical: def/class/function 定義行 (covered/uncovered matching key)
  source_hash: string
  updated_at: string
  # PLAN-013 追加
  bucket: coverage_eligible|private_helper|excluded
  metadata:
    seed_candidate: true|false
    seed_promotable: true|false
```

migration は PLAN-011 既存項目 `id/domain/summary/since/related/path/line_no/source_hash/updated_at` を不変のまま保ち、`bucket` と `metadata` を additive で付与します。
v14→v15 migration では既存 `line_no`（marker 行）から対応 symbol を再スキャンし、`symbol_line` を補完する。`line_no` は v14 互換のため不変保持。fixture では marker 行と symbol 行がずれるケースを必須とする。
build 時は `path`/`symbol_line` の再取得を前提に再分類を再現可能とする。

再分類ルールは以下を採用します。

1. まず `excluded` 判定を行い、`path` が excluded patterns にマッチした場合は `bucket=excluded` を確定。
   - この場合は `symbol` / `kind` に依存しない。
2. 非 excluded の場合、build 時の AST/構文スキャンで `symbol` / `kind` を算出して `bucket` を決定。
3. `metadata.seed_promotable=true` は `private_helper` のみ許容。
4. 再分類対象ファイルで path マッチがあれば `excluded` に固定（seed 属性は問わない）。
5. DB は派生 cache。down は `code-catalog.jsonl` 再生成（v14 schema）として成立。

non_indexable_paths:
  inherited_from: PLAN-012
  applied_before: bucket_classification
  patterns:
    - test_*.py
    - tests/**
    - cli/tests/**
    - fixture/**
    - fixtures/**
    - generated/**
    - vendor/**
  bucket: null
  counted_in_bucket_counts: false
  counted_in_coverage: false

- PLAN-012 の対象外 path は PLAN-013 でも bucket 分類前の pre-filter として継承する。
- これらは `coverage_eligible` / `private_helper` / `excluded` のいずれにも分類しない。
- `excluded` bucket は `setup.sh` / `skills/agent-skills/hooks/*.sh` / `verify/*.sh` の固定 3 pattern に限定する。
- この継承により core5 80% gate (45/56) と PLAN-012 の ignore 契約を不変に保つ。

#### §3.2.x bucket 算出規則

- `excluded` 判定は優先: `path` が `setup.sh` / `skills/agent-skills/hooks/*.sh` / `verify/*.sh` のいずれかに一致した場合、`bucket=excluded` とする。
- `excluded` 以外は build 時の AST/構文スキャン結果から以下を決定し、`entry` には `kind` と `symbol` を保存しない。
- 再判定は `path + symbol_line` から当該行を再取得して再構成可能。`line_no` は marker 行として参照のみ。

Python:
- `def name(...)` → `kind=function`、`name` が `_` で始まれば `bucket=private_helper`、それ以外は `bucket=coverage_eligible`
- `class Name(...)` → `kind=class`、`Name` が `_` で始まれば `bucket=private_helper`、それ以外は `bucket=coverage_eligible`

bash:
- `name() { ... }` または `function name { ... }` → `kind=function`、`name` が `_` で始まれば `bucket=private_helper`、それ以外は `bucket=coverage_eligible`

### §3.3 CLI 出力契約

`helix code stats --uncovered` は bucket 拡張を前提に引き続き実装します。

```bash
helix code stats --uncovered [--bucket coverage_eligible|private_helper|excluded|all] [--seed-candidate true|false|all] [--seed-promotable true|false|all] [--scope core5|cli-lib|all]
```

#### §3.3.1 flag 契約

- `--bucket` 省略時の default は `coverage_eligible`
- `--seed-candidate` 省略時の default は `all`
- `--seed-promotable` 省略時の default は `all`
- `--scope` default は **`all`** (現行 `cli/helix-code` argparse `default="all"` と一致、PLAN-012 互換、breaking change なし)。core5 gate を使うときは明示的に `--scope core5` を指定する。
- `--bucket all` は全 bucket（3 値）を横断し、bucket 毎集計を同時返却
- JSON 出力では各 item に `bucket` と `seed_candidate` / `seed_promotable` を追加
- `--uncovered` の **母集団** は build 時 AST/構文スキャンで取得する **全 top-level symbol (Python def/class、bash function)** とする。各 symbol は §3.2 の bucket 算出規則に従って `coverage_eligible` / `private_helper` / `excluded` のいずれかに分類される。
- `--uncovered` の **判定 (covered/uncovered)** は、各 symbol について `.helix/cache/code-catalog.jsonl` に対応する entry (path + symbol_line で同定) があるかで決まる。
- coverage% **指標計算** は `bucket=coverage_eligible` のみを母数として行う (core5 80% gate 等)。`private_helper` / `excluded` の uncovered 列挙は coverage% に**寄与しない**が、`--bucket private_helper` 等で出力可能 (= bucket 横断列挙と coverage 指標は独立した契約)。
- `--uncovered` 出力 schema:
- **uncovered entry** (JSONL に entry なし): `path` / `symbol_line` / `line_no` (= `symbol_line` と同値) / `symbol` / `kind` / `bucket` / `seed_candidate` (default 算出値) / `seed_promotable` (default false 固定)
- **covered entry** (JSONL から取得): `id` / `domain` / `summary` / `since` / `related` / `path` / `line_no` / `symbol_line` / `source_hash` / `updated_at` / `bucket` / `seed_candidate` / `seed_promotable`（`metadata.seed_candidate` / `metadata.seed_promotable` を CLI 境界で item 直下へ flatten）
- uncovered entry の seed metadata **default 算出ルール** (JSONL に entry がないため):
  - `bucket=coverage_eligible` → `seed_candidate=true`、`seed_promotable=false`
  - `bucket=private_helper` → `seed_candidate=false`、`seed_promotable=false` (手動 markup は covered entry のみ可能)
  - `bucket=excluded` → `seed_candidate=false`、`seed_promotable=false` 固定
- `helix.db v15` は `bucket` のみを持つ高速 filter 派生 cache (metadata は **保持しない**、JSONL 専用)。
- DB 直接 SELECT は内部 API とし、外部から見える CLI 契約は JSONL 経由で固定。

#### §3.3.2 PoC seed / 利用経路補足

- CLI flag `--seed-candidate true|false|all` の filter 経路:
  - covered entry: `cli/lib/code_catalog.py` の filter で JSONL tail-load し、各 entry の `metadata.seed_candidate` を参照
  - uncovered entry: §3.3.1 の default 算出ルールで `seed_candidate` / `seed_promotable` を計算してフィルタ
  - 両者を union して `--seed-candidate true` 等の絞り込みを統一的に適用
- `--seed-promotable` も同様 (covered: JSONL metadata、uncovered: default false 固定)。
- DB (helix.db v15) は metadata を保持しないため、seed フィルタは **JSONL + AST default 算出** が source of truth。bucket フィルタは DB / JSONL いずれからも可能だが外部契約上は JSONL 経由。

#### §3.3.3 default 出力

TSV はこれまでどおり 1 行 1 symbol の形式を維持し、末尾に summary を追加します。

- `path`
- `line`
- `symbol`
- `kind`
- `bucket`
- `seed_candidate`
- `seed_promotable`

summary は以下を含む。

- `covered`
- `eligible`
- `coverage_pct`
- `bucket_counts`（3 bucket それぞれの件数）
- `seed_candidate_count`
- `seed_promotable_count`

**CLI JSON 外部契約**: 各 `items[]` は常に flat shape とし、`metadata` object は出力しない。  
covered entry は JSONL 正本の `metadata.seed_candidate` / `metadata.seed_promotable` を読み取り、CLI 境界で `seed_candidate` / `seed_promotable` として item 直下へ flatten する。  
uncovered entry は §3.3.1 の default 算出値を同じ flat field として返す。  
JSONL 内部保存のみ nested metadata を source of truth とする。  

#### §3.3.4 JSON 出力

JSON は以下を含む単一 object とする。

```json
{
  "items": [
    {
      "id": "code-catalog.build_catalog",
      "domain": "cli/lib",
      "summary": "code-catalog entry builder",
      "since": null,
      "related": [],
      "path": "cli/lib/code_catalog.py",
      "line_no": 9,
      "symbol_line": 12,
      "symbol": "build_catalog",
      "kind": "function",
      "bucket": "coverage_eligible",
      "source_hash": "sha256:...",
      "updated_at": "2026-05-03T00:00:00Z",
      "seed_candidate": true,
      "seed_promotable": false
    }
  ],
  "summary": {
    "covered": 0,
    "eligible": 10,
    "coverage_pct": 0,
    "bucket_counts": {
      "coverage_eligible": 0,
      "private_helper": 0,
      "excluded": 0
    },
    "seed_candidate_count": 0,
    "seed_promotable_count": 0
  }
}
```

### §3.4 coverage gate policy

coverage gate policy は 3 段階化します。

1. core5: 既存 80% gate を固定値で維持
2. cli-lib: warning レベルの gate を新設
3. 全体（global）: PLAN-014 以降に deferred

#### §3.4.1 core5 80% gate

- 適用対象: `--scope core5`
- 指標: `coverage_eligible` の coverage
- 閾値: 80（固定）
- 意図: regress 防止
- 変更不可: 本 PLAN 内では変更しない

#### §3.4.2 cli-lib gate (warning/target)

- 適用対象: `--scope cli-lib`
- 実装: `--fail-under` 未指定時は warning 表示のみ（ゼロ閾値）
- 意図: 全体傾向を見える化しつつ、阻害しない

#### §3.4.3 global gate

- 合計 446 entries を扱う global gate は未導入
- PLAN-014 候補として定義
- 実装時の前提: migration で `bucket` を持った状態を前提に再定義

### §3.5 PoC seed contract

PLAN-011 で保有した PoC seed 5件は、`private_helper` として再分類され、`metadata.seed_candidate=true` を付与します。

#### §3.5.1 seed_candidate への分離

PoC seed は `bucket=private_helper` とし、`metadata.seed_candidate=true` に分類し coverage 除外母集団へ接続しない。

#### §3.5.2 seed_promotable の用途

- 当面は metadata ベースのみ
- recommender は `metadata.seed_candidate=true` の entry を候補に使う
- public 化提案は PLAN-014 以降に実装

#### §3.5.3 反映方針

保存先正本は `.helix/cache/code-catalog.jsonl` で、各 entry 直下 `metadata` に `seed_candidate` / `seed_promotable` を保持する。
派生 cache `helix.db v15` は **`bucket` のみ** を保持する高速 filter cache とし、`metadata` は **DB に保存しない** (JSONL 専用)。
`cli/lib/code_catalog.py` の `--seed-candidate` / `--seed-promotable` フィルタは JSONL を tail-load して `metadata.*` を参照する一択。DB 経由の seed フィルタは契約外。
DB は bucket フィルタのみの高速化キャッシュとし、外部可視 API は JSONL 中継に限定する。

### §3.6 既存データへの影響 (D-MIGRATION)

#### §3.6.1 PLAN-011 由来 seed 5件

- 現時点: 5 件は private、`_` 始まり
- 再分類結果: `bucket=private_helper`、`metadata.seed_candidate=true`
- `coverage_eligible` からの除外
- core5 coverage は既存 `45/56` のまま不変

#### §3.6.2 cli/lib 全体

- 残 39 entries（public）は `bucket=coverage_eligible`、`metadata.seed_candidate=true` を保持
- `cli-lib` warning gate で可視化対象にする

#### §3.6.3 operational script

- `setup.sh` 8件を `excluded` 配下へ移動
- `skills/agent-skills/hooks/*.sh` 16件を `excluded` 配下へ移動
- `verify/*.sh` を `excluded` に移動
- 除外対象は §3.1 の `excluded_patterns` として明記

#### §3.6.4 migration 受け入れ条件

- `id/domain/summary/since/related/path/line_no/source_hash/updated_at` を不変として保持し、`bucket`/`metadata` を additive 付与。
- v14 → v15 を batch 変換で実施
- `bucket` カラム追加時に既定値は `coverage_eligible`
- `excluded` 判定後に seed / coverage へ再配分
- 再変換は幾何学的増加なく deterministic を担保
- down は `code-catalog.jsonl` 再生成（v14 schema）で成立
  - 既存 catalog は id stable + 既存フィールド保持が不変条件

### §3.7 deferred-findings 影響評価 (D-DEBT)

deferred-findings 18件は P2 medium と定義し、以下を維持します。

- PLAN-013 の直接対象外
- `accuracy_score` への即時影響は 0
- PLAN-013 完了時も新規 finding が発生しなければ影響なし

本 PLAN では debt burn-down を提案のみ実施し、実装は別 PLAN とします。

## §4. リスク

### R1 バケツ再分類時のキー破壊

`code-catalog` が保有する `symbol` ではなく `path+symbol_line` の再スキャン再現性が migration 品質を支える。

- 対策: v14→v15 migration を fixture 化
- `path + symbol_line` で再取得後に bucket 判定を再現できることを担保
- 再分類後も id 一貫性を担保

### R2 excluded パターンの追加漏れ

運用上、新しい operational script が拡張された際、対象漏れが起きるリスクがあります。

- 対策: glob pattern を明示し、contract 記載の運用手順で追補
- 対策2: excluded_patterns 一覧を review コマンドで確認できるよう運用メモへ追加

### R3 seed_promotable の偏り

heuristic を将来導入した際に bias が発生する可能性があります。

- 対策: PLAN-013 では手動 metadata のみを許容
- 対策2: heuristic 導入を PLAN-014 に明示的に deferred

### R4 cli-lib warning の無視

warning では CI や運用者が見逃すリスクがあります。

- 対策: `--scope cli-lib --uncovered` は CI / PR サマリーで定期採点
- 対策2: PLAN-014 にて fail 化条件と PR 表示ルールを追加

### R5 参照整合性の退行

- `PLAN-012` で定義した `--scope core5` の語意と bucket 運用が混在すると説明負荷が増加する
- 対策: §3.3 と§3.4 を契約として固定し、default 挙動を明文化

## §5. 受入条件

### §5.1 契約凍結条件

- [ ] 3-bucket taxonomy（§3.1）が D-CONTRACT として文書・契約化されている
- [ ] `seed_promotable` と `seed_candidate` の定義と境界が一致している
- [ ] `excluded` 判定パターンが運用文書と実装で一致している

### §5.2 データ移行条件

- [ ] helix.db v15 migration の up/down 両方向が成立している
- [ ] migration 後も `bucket` と既存 id の mapping が再現可能
- [ ] `seed_candidate` と `coverage_eligible` が二重計上しないことを fixture で確認

### §5.3 coverage 回帰条件

- [ ] core5 80% gate が regress しない（45/56 を維持）
- [ ] `--scope core5 --bucket coverage_eligible --fail-under 80` が従来 gate を維持
- [ ] `--scope cli-lib --bucket coverage_eligible --fail-under 0` の exit は 0
- [ ] marker 行 != symbol 行 fixture を含み、`path + symbol_line` matching で false uncovered が発生しない

### §5.4 CLI 仕様条件

- [ ] `helix code stats --uncovered --bucket all --seed-candidate all --seed-promotable all --scope all --json` が 3 bucket 全件分類を返す
- [ ] JSON は `items` と `summary.bucket_counts` を含む
- [ ] default 出力は `bucket` 列を持つ
- [ ] `seed_candidate` / `seed_promotable` が summary/item 両方で返却される
- [ ] JSON `items[]` は flat shape とし、`metadata` object を含まない
- [ ] covered entry も uncovered entry も同じ flat key set (`bucket` / `seed_candidate` / `seed_promotable`) を返す

### §5.5 excluded 検証条件

- [ ] `setup.sh` / `skills/agent-skills/hooks/*.sh` / `verify/*.sh` が `excluded` として分類される
- [ ] `pytest` で fixture を通じて pattern 判定を検証する
- [ ] `non_indexable_paths` (test_*.py 等) は `bucket_counts` のいずれにも計上されない
- [ ] `non_indexable_paths` を含むディレクトリ配下のファイルが pre-filter で除外されることを fixture で確認

### §5.6 PoC seed 分離条件

- [ ] PLAN-011 PoC seed 5件（private）を `bucket=private_helper` / `seed_candidate=true` に再分類
- [ ] `coverage_eligible` への計上が消えていることを fixture で確認
- [ ] 上記で core5 coverage が 45/56 不変であることを示す

### §5.7 warning gate 条件

- [ ] `cli-lib` warning が `--bucket` / `--scope` 出力上で表示される
- [ ] exit code は warning のみで `0` を維持
- [ ] PLAN-014 前提の enforce 条件を別 ticket として明記

### §5.8 運用前提条件

- [ ] `.helix/proposals/` に D-CONTRACT / D-DEBT / migration の差分メモを保存
- [ ] PLAN-012 の deferred 状態 (`PLAN-012` を参照) が引き継がれる
- [ ] `docs/plans` 内リンク更新が成立している

## §6. 工程 / Sprint 構成

PLAN-013 は設計 PLAN として、以下の sprint で回します。

TL: `.1a` まで受け入れ、`.2` 以降は L4 と同時実装化可能。

### §6.1 Sprint .1a（TL レビュー受領後）

- 3 bucket 定義の精緻化
- edge case 洗い出し
- 実装境界の再掲
- D-CONTRACT の term freeze
- 実装不確実性の列挙

#### DoD

- [ ] §3.1〜§3.7 が更新不能な状態で共有
- [ ] review 記録（TL 所見）を反映
- [ ] excluded パスと seed の境界が確定

### §6.2 Sprint .1b（D-CONTRACT / D-DEBT 凍結）

- D-CONTRACT と D-MIGRATION、D-DEBT を文書化
- `helix.db v15` schema と JSON schema の freeze
- migration テスト観点を一覧化
- F1: `symbol_line` schema 追加と matching key 凍結 (`path + symbol_line`)
- F2: CLI JSON 外部契約 flat shape 凍結
- F3: non_indexable_paths pre-filter 継承凍結

#### DoD

- [ ] schema 差分表の承認
- [ ] migration の前提と後退手順が明確
- [ ] `bucket` 判定ロジックが実装不可能要件に対して閉じている

### §6.3 Sprint .2（Migration + fixture）

- migration バッチ作成
- 再分類 fixture 作成

#### DoD

- [ ] v14→v15 再分類が deterministic
- [ ] fixture で 3 bucket 分布が検証可能
- [ ] 既存 catalog 再生成時の互換性を満たす

### §6.4 Sprint .3（CLI flag 実装）

- `--bucket` / `--seed-candidate` / `--seed-promotable` フラグ実装
- classification logic の classification path 追加

#### DoD

- [ ] `coverage_eligible|private_helper|excluded|all` が選択可能
- [ ] `seed-candidate true|false|all` が選択可能
- [ ] `seed-promotable true|false|all` が選択可能
- [ ] `--bucket all` / `--seed-candidate all` / `--seed-promotable all` の JSON/TSV が期待配列を返却
- [ ] `seed_candidate` / `seed_promotable` が API 契約として透過

### §6.5 Sprint .4（テスト追加）

- pytest + bats で 3 bucket 全件を検証
- exit code / warning 表示の分離を検証

#### DoD

- [ ] bucket filter を含む pytest / bats 追加
- [ ] `setup.sh` / `skills/agent-skills/hooks/*.sh` / `verify/*.sh` 除外のテスト追加
- [ ] seed の再分類テストを fixture 化

### §6.6 Sprint .5（運用/文書更新）

- `SKILL_MAP.md` / `HELIX_CORE.md` の運用参照を整理
- plan/運用メモの相互参照更新

#### DoD

- [ ] PLAN-013 の要点が L1-L8 連携で追える
- [ ] 追加ドキュメントの TODO が 0 件
- [ ] レビュー時の参照ポイントが明示

### §6.7 将来工程（PLAN-013.1 以降）

- cli-lib full enforce 実施
- CLI warning を CI policy 化
- seed_promotable heuristic 導入
- deferred-findings burn-down 統合

## §7. 見積 / 工数

- size: M
- 対象ファイル: 6-9 file 想定（設計・契約・migration・fixtures・テスト・運用参照整備）
- 見積 line: 200-420 行変更

### §7.1 要員配分（参考）

- TL レビュー: 30min × 2 回
- SE 実装: 90min（設計反映）
- QA: 60min（受入条件テスト観点）
- docs 反映: 30min（運用メモ含む）

### §7.2 合計

- 設計 Plan 合計: 約 4-5h
- リスク緩衝: +1h（parallel 実装可否確認）
- 予約: PLAN-014 への引き継ぎ観点を別枠管理

### §7.3 依存関係

- PLAN-012 の実装基盤は fixed とみなす
- DB migration 変更は DB 管理者レビューを要する場合は separate gate
- verify スクリプト更新は CI 実行可能性に合わせて連動

### §7.4 同時実施可否

- TL は .1a、.1b を完了後、SE が .2 から parallel で着手可能
- L1-L3 では plan freeze 重視で過剰最適化を抑制
- 失敗時の rollback は migration の down script と再分類ログで戻せる

## §8. 改訂履歴

- v1.5 (2026-05-03): G3 schema freeze として P2 findings F1/F2/F3 を反映 (TL approve)
  - F1: `symbol_line` を新規 schema field として追加 (marker_line と並走)、covered/uncovered matching key を `path + symbol_line` に凍結。`line_no` は v14 互換 marker 行として保持
  - F2: CLI JSON 外部契約を flat `items[]` に統一、JSONL 内部のみ nested `metadata.*` を source of truth として保持
  - F3: PLAN-012 の対象外 path (test_*.py / tests/ / fixture/ / generated/ / vendor/) を non_indexable_paths として bucket 分類前 pre-filter で継承
- v1.4 (2026-05-03): 4 巡目 TL レビュー (verdict=needs-attention, P1=3/P2=0/P3=1) findings 4件 反映
  - F1 P1: `--uncovered` 母集団を **全 top-level symbol** (Python def/class + bash function) に拡張。bucket は §3.2 規則で全 symbol に付与し、coverage% 指標は `coverage_eligible` のみで計算 (= bucket 横断列挙と coverage 指標を独立契約に分離)
  - F2 P1: uncovered entry の seed metadata **default 算出ルール** を §3.3.1 / §3.3.4 で凍結 (coverage_eligible→seed_candidate=true、private_helper/excluded→false)。covered/uncovered 統一フィルタを定義
  - F3 P1: `--scope` default を `core5` → **`all`** に修正 (現行 `cli/helix-code` argparse `default="all"` 互換、breaking change なし)。core5 gate は明示 `--scope core5` を要求
  - F4 P3: 改訂履歴の v1.2 重複を排除し時系列で一意化、付録 B を v1.4 想定の review 状態に更新
- v1.3 (2026-05-03): 3 巡目 TL レビュー (verdict=needs-attention, P1=2/P2=1/P3=0) findings 3件 反映 → v1.4 で再分割解消
- v1.2 (2026-05-03): 2 巡目 TL レビュー (verdict=needs-attention, P1=1/P2=2/P3=2) findings 5件 反映 → v1.3/v1.4 で再分割解消
- v1.1 (2026-05-03): TL 5軸レビュー findings 5件を反映（P1=2, P2=2, P3=1）
  - F1: 3-bucket + 直交 metadata（案Y）へ再設計
  - F2: `.helix/cache/code-catalog.json` から `.helix/cache/code-catalog.jsonl` へ正本統一
  - F3: CLI 契約（bucket 3値 + `--seed-*` flags）と Sprint .3 DoD を統一
  - F4: migration down strategy を `code-catalog.jsonl` 再生成として明記
  - F5: `agent-skills/hooks/*.sh` を `skills/agent-skills/hooks/*.sh` に統一
- v1.0 (2026-05-03): 初版起草。TL 5軸評価で conditional pass。指摘 P1/P2 を本 draft で対応済（4-bucket taxonomy 分離、cli-lib warning level 導入、excluded 分類、deferred findings を別 PLAN とした）。

## 付録 A: PLAN 関連参照

- `docs/plans/PLAN-011-code-index-system.md`
- `docs/plans/PLAN-012-code-index-coverage.md`
- `docs/plans/PLAN-013-code-index-eligibility-taxonomy.md`
- `.helix/proposals/` (bucket / migration / debt メモ)
- `.helix/cache/code-catalog.jsonl`
- `helix.db v14 / v15` (`code_index` schema)

## 付録 B: TL レビュー履歴サマリ

レビュー結果の正本は `.helix/reviews/plans/PLAN-013.json` を参照。本付録は trail として各 round の結論のみ記録する。

| round | version | verdict | P0 | P1 | P2 | P3 | 解消版 |
|---|---|---|---|---|---|---|---|
| 1 | v1.0 | conditional / needs-attention | 0 | 2 | 2 | 1 | v1.1 |
| 2 | v1.1 | needs-attention | 0 | 1 | 2 | 2 | v1.2 |
| 3 | v1.2 | needs-attention | 0 | 2 | 1 | 0 | v1.3 |
| 4 | v1.3 | needs-attention | 0 | 3 | 0 | 1 | v1.4 |
| 5 | v1.4 | **approve** | 0 | 0 | 3 | 1 | finalize |
| - | v1.5 | **schema-freeze** | 0 | 0 | 0 | 0 | G3 凍結 |

v1.5 で schema freeze 到達。v1.4 で残っていた P2 F1/F2/F3 は v1.5 で解消、P3 F4 は v1.4 で解消済:

- P2 F1: `line_no` の canonical semantics (marker_line vs symbol_line) と covered/uncovered matching key を schema freeze で `path + symbol_line` に確定
- P2 F2: CLI JSON 外部契約を flat `items[]` へ確定（metadata は CLI 外部契約から除外、JSONL 内部で nested metadata を保持）
- P2 F3: PLAN-012 の対象外 path (test_*.py / tests/ / fixture/ / generated/ / vendor/) を PLAN-013 の pre-filter として継承

## 付録 C: チェック観点メモ

- リンク整合性: 上記「付録 A」の参照を確認対象とする。
- TODO 残存: 付録更新時点で本文に `TODO|FIXME` を残さない。
- 変更対象: 本 PLAN により本体更新するファイルは以下。
  - `docs/plans/PLAN-013-code-index-eligibility-taxonomy.md`
  - `cli/lib/code_catalog.py`
  - `cli/lib/helix_db.py`
  - `tests/test_code_catalog.py`
  - `bats/test-helix-code.bats`
  - `SKILL_MAP.md` / `HELIX_CORE.md` 追記
