# PLAN-012: コード index 未カバレッジ計測 (v1.4)

## §1. 目的 / position

PLAN-011: コード index 登録システム (v1.3) は、コードメタデータの規約整備と catalog 構築を実装し、`--uncovered` は **PLAN-011.1**（本PLAN-012）として完全 deferred した状態を維持した。根拠は PLAN-011 §3.6 の v1.3 を参照する。

PLAN-011 は `code-catalog` の PoC スケルトン（catalog entry 10件）を `cli/lib 5 + cli/scripts 5` で構築し、実運用の coverage 概念が未確立のまま終了した。PLAN-012 はここから一歩進め、

- tracked ファイルを母数とした symbol 単位の coverage 定義
- `helix code stats --uncovered` の実装と CI 向けゲート条件（`--fail-under`）
- 既存 `cli/` 配下への `@helix:index` 追加運用

を実施し、`code-catalog` の実効性を確保する。

計画は PLAN-011 §3.6 で defer されていた以下を引き受ける。

- `stats --uncovered` の一覧表示と coverage 算出
- エラー時/不足時の退出コード設計
- 既存 tracked シンボルの母数設計（coverage 指標の正当化）
- 既存コードへの metadata 追加実行計画

## §2. スコープ

### §2.1 in-scope

- `helix code stats --uncovered` 実装
  - 機能: 未カバレッジ symbol 一覧 + covered / eligible / coverage % を summary で出力
  - 出力: default TSV、`--json` 指定時 JSON object
- `--fail-under <percent>` フラグ実装（初版）
  - default 0
  - `--fail-under > 0` 時のみ不足時 exit 2
- `@helix:index` 付与実装（**core 5 ファイル限定**, 実測 2026-05-03）:
  - `cli/lib/code_catalog.py` (public=8)
  - `cli/lib/code_recommender.py` (public=3)
  - `cli/lib/helix_db.py` (public=29)
  - `cli/lib/skill_catalog.py` (public=8)
  - `cli/lib/skill_dispatcher.py` (public=7)
  - 合計母数: **55 public symbol** / 80% 目標 = **44 個 covered**
  - PoC seed (PLAN-011) の 10 件 (code_catalog 5 + skill_catalog 5) からの拡張
- `.gitignore` を起点にした ignore 契約（初版）
  - tracked 抽出は `git ls-files`
  - tests fixture / generated / vendor を追加除外
  - `.md/.bats` の構文判定除外は PLAN-011 v1.2 方針を継続

### §2.2 out-of-scope

- 専用 `.helixignore` 実装（PLAN-012 では将来拡張）
- TRACKED_SUFFIXES 外拡張（`.md/.bats` は引き続き除外）
- **`cli/helix-*` (suffixless) スクリプトへの metadata 付与**: 現行 `TRACKED_SUFFIXES` (`.py`/`.sh`) の対象外であり、suffixless 対応は scope creep となるため将来 PLAN へ deferred
- **core 5 ファイル以外の `cli/lib/*.py` (残り 46 ファイル, 約 303 public symbol)**: 将来 PLAN へ段階的 deferred (本 PLAN は pilot として core 5 で 80% 達成を確立する)
- repo 横断の stats 計測
- 他リポジトリの catalog 連携
- DB スキーマ変更、`helix.db v14` 変更
- 既存 CLI コマンド以外の新規統合インタフェース追加

## §3. 要件 / 設計

### §3.1 母数（eligible symbol）定義

#### CLI 全体としての母数定義 (`stats --uncovered` 動作仕様)

- 対象ファイル: `TRACKED_SUFFIXES` 準拠（`.py` / `.sh`）
- 対象抽出: `git ls-files`
- symbol 定義（**public symbol**）:
  - `.py`: top-level `def` / `class`（`_` で始まるシンボル名を除外）
  - `.sh`: top-level `function NAME()` または `NAME() {` 形式（`_` で始まるシンボル名を除外）
- 対象外:
  - `test_*.py`, `*.bats`
  - `.md`
  - 生成物（generated/ vendor/ fixture/ tests/ cli/tests/）
  - CLI 未対応拡張子

#### 本 PLAN scope の coverage 目標母数

実測 2026-05-03: cli/lib/*.py (test_* 除く) は 51 ファイル / public symbol 358 個。本 PLAN は pilot として **core 5 ファイル (55 public symbol)** に限定し、その内 80% (= 44 個) を covered にする。

| ファイル | public symbol | 既 covered (PoC, public のみ) |
|---|---:|---:|
| cli/lib/code_catalog.py | 9 *1 | 5 |
| cli/lib/code_recommender.py | 3 | 0 |
| cli/lib/helix_db.py | 29 | 0 |
| cli/lib/skill_catalog.py | 8 | 0 *2 |
| cli/lib/skill_dispatcher.py | 7 | 0 |
| **合計** | **56** | **5** |

*1: SE Sprint .2 で `compute_uncovered` 等の public 関数が +1 追加されたため 9.
*2: PLAN-011 PoC seed (`_strip_quotes` / `_parse_scalar` 等) は **アンダースコア始まりの private 関数** に付与されたため、PLAN-012 contract の eligible (public symbol) からは除外される。

追加付与目標: **40 個以上** (5 + 40 = 45 = **80.4%** of 56, gate 80% pass)。

### §3.2 covered 判定

Sprint .1a contract 凍結 (`.helix/proposals/PLAN-012-sprint1a-contracts.md`):

- **canonical**: 対象 symbol 定義行の **直前 1 行** が `# @helix:index id=...` のコメント行である場合 covered。
- **救済**: 直前が連続コメントブロック（空行・コード行を挟まない `#` 始まり連続行）の中に `# @helix:index ...` 行があれば covered (デコレータや annotation がある場合の救済).
- **対象外**: docstring 内 (`"""..."""` 内) の `@helix:index` 文字列は parser 対象外 (covered としない).
- **判定 parser**: covered 判定は **redaction を適用しない** marker payload parser を用いる (`_is_index_marker_valid` 等)。 `parse_helix_index_comment` (build 時用、redaction 含む) は coverage 判定に使わない。
  - 理由: 32+ 連続英数字 (例: 36 文字の長い snake_case 関数名) を `should_redact` が secret_like_value と誤判定して None を返すため、文法上 valid な metadata でも uncovered になってしまう。
  - 判定基準: `id` / `domain` / `summary` の 3 fields が parse できれば covered とみなす (redaction は build 時に別途適用)。
- 同一 symbol に重複 id がある場合、id 正規化を通過した最初の行を採用し、重複は warning として計測から除外。

### §3.3 --uncovered 出力仕様

#### default (stdout, TSV)

各 uncovered を 1 行 TSV で出力した後、最終行に summary を表示する。

```
<path>\t<line>\t<symbol>\t<kind>
<path>\t<line>\t<symbol>\t<kind>
...
summary: covered=<N> eligible=<M> coverage=<PCT>%
```

- `kind` は `function|class`
- 並び順: `path` 昇順 → `line` 昇順
- ヘッダ行なし
- summary 行は uncovered の有無に関わらず常に最終行に出力

#### --json (stdout)

単一 JSON object を出力する。

```json
{
  "items": [
    {"path": "cli/lib/code_catalog.py", "line": 88, "symbol": "parse_helix_index_comment", "kind": "function"}
  ],
  "summary": {
    "covered": 0,
    "eligible": 10,
    "coverage_pct": 0.0
  }
}
```

- `json.dumps(..., ensure_ascii=False, sort_keys=False)` で出力。末尾改行 1。
- `coverage_pct` は小数 1 位 (`round(x, 1)`)。
- `items` は default と同じ並び順 (path 昇順 → line 昇順)。

#### stderr

usage error 時のみ argparse メッセージを stderr に出力。それ以外の経路では stderr に何も出さない (covered/uncovered の情報は全て stdout に出力)。

#### 将来拡張 (実装範囲外)

`--by domain` は将来拡張案として言及のみ。本 PLAN scope では実装しない。

### §3.4 --fail-under 契約 (with --scope)

Sprint .1a contract 凍結 (`.helix/proposals/PLAN-012-sprint1a-contracts.md`):

#### --scope オプション (新設)

- `--scope all` (default): cli/lib/*.py 全体 (51 files / 358 public symbol) を表示・計算対象
- `--scope core5`: 本 PLAN scope の core 5 ファイル (55 public symbol) のみを表示・計算対象

`--scope` は表示対象と `--fail-under` の母数を同時に決定する (A 案採用)。

#### --fail-under

- `--fail-under` default `0`
  - 未指定または 0 の場合: coverage 不足があっても `exit 0`
- `--fail-under N`（1-100）:
  - **--scope の coverage_pct** が `N` 未満なら `exit 2`
- 成功終了条件:
  - `exit 0`: coverage 判定 pass または未指定時
  - `exit 64`: usage error（argparse 不正引数。既存 helix-code 慣例を踏襲）
  - `exit 2`: `--fail-under` 違反
- `exit 1` は使用しない。

#### 本 PLAN 受入 gate

`helix code stats --uncovered --scope core5 --fail-under 80` を Sprint .4 受入 gate として固定。core 5 の coverage が 80% 未満なら exit 2 で fail。

### §3.5 ignore 契約

- トラック対象抽出:
  - `git ls-files` により tracked ファイルをベースライン取得
  - `git ls-files` は tracked ファイルのみ返すため `.gitignore` 再評価を行わない
- 追加除外パターン（本PLAN）:
  - `tests/`
  - `cli/tests/`
  - `fixture/`
  - `generated/`
  - `vendor/`
    - これら path 配下は `.py/.sh` でも除外
- `PLAN-011 v1.2` の `.md/.bats` 除外ポリシーを維持
- 将来 `.helixignore` 導入は PLAN-012 外。

### §3.6 metadata 付与計画

本 PLAN は pilot として **core 5 ファイル (55 public symbol)** に scope を絞る。Phase 2 (cli/helix-* / 残り 46 cli/lib) は将来 PLAN へ deferred。

#### 対象 5 ファイルと付与目標

| ファイル | public | 既 covered (public) | 追加目標 | 達成後 |
|---|---:|---:|---:|---:|
| code_catalog.py | 9 | 5 | 3 | 8/9 (89%) |
| code_recommender.py | 3 | 0 | 3 | 3/3 (100%) |
| helix_db.py | 29 | 0 | 22 | 22/29 (76%) |
| skill_catalog.py | 8 | 0 | 7 | 7/8 (87%) |
| skill_dispatcher.py | 7 | 0 | 5 | 5/7 (71%) |
| **合計** | **56** | **5** | **40** | **45/56 (80.4%)** |

PoC seed (PLAN-011) の public symbol covered = 5 (code_catalog.py のみ) + 40 件追加 = 45 件 → 80.4% で gate pass。

skill_catalog.py の PoC seed (`_strip_quotes` 等 5 件) は `_` 始まり関数なので eligible 外 (private). PLAN-012 では public 関数 7 件に新規付与する。

#### 付与方針

- `parse_helix_index_comment` の canonical grammar (PLAN-011 v1.3 §3.1) に準拠
- **id 命名規則: kebab-case dotted (Sprint .1a contract 凍結, PLAN-011 seed 準拠)**
  - 形式: `<module-kebab>.<symbol-kebab>` (アンダースコアはハイフンに置換)
  - 例: `code_catalog.py` の `parse_helix_index_comment` → `code-catalog.parse-helix-index-comment`
  - 例: `helix_db.py` の `init_db` → `helix-db.init-db`
  - 例: `code_recommender.py` の `find_candidates` → `code-recommender.find-candidates`
- domain: `cli/lib`
- summary: 1 行で日本語の簡潔な目的記述 (PLAN-011 v1.3 §3.1 grammar)

#### 段階的 deferred (out-of-scope)

- 残り 46 ファイル の cli/lib/*.py (約 303 public symbol) → 将来 PLAN
- `cli/helix-*` (suffixless) → 将来 PLAN (TRACKED_SUFFIXES 拡張が前提)

### §3.7 DB / catalog / cache への影響

- `helix.db v14` スキーマは維持（変更なし）
- JSONL 正本フォーマットは変更しない
- cache key 設計（既存 `code-index`）は変更しない
- `--uncovered` のみを追加で CLI 参照レイヤへ反映

## §4. リスク

- 目標（80%）が高く、短期間で symbol 追加が追い付かない
  - 対応: 本フェーズは `cli/lib/*.py` を最小単位とし、`cli/helix-*` は Phase2 へ分離。
  - 低達成時は sprint 内で暫定目標（例: 70%）へ調整し、次 PLAN へ carry。
- fixture / generated 誤検知による統計ノイズ
  - 対応: ignore 契約を `.gitignore` + 追加パターンで固定し、E2E で証明。
- metadata の id 命名ぶれ
  - 対応: PLAN-011 §3.1 grammar に準拠した書式 lint 併用。
  - 併せて既存 docs/fixtures の sample を更新し、再現率と誤検知率を抑える。
- exit code の CI 統合誤用
  - 対応: 運用メモに exit 0 / 2 / 64 の意味、`--fail-under` 使用条件、CI での判定位置を明記。

## §5. 受入条件

- [ ] `helix code stats --uncovered` が tracked `.py/.sh` の uncovered symbol を一覧化できること
- [ ] summary に `covered / eligible / coverage` が表示されること
- [ ] `--json` 形式が有効で `{"items": [...], "summary": {...}}` を返すこと
- [ ] `--fail-under N` 時、coverage 不足時に `exit 2` となること
- [ ] `--fail-under 0` 時は未指定時と同様に `exit 0` となること
- [ ] **core 5 ファイル** (code_catalog.py / code_recommender.py / helix_db.py / skill_catalog.py / skill_dispatcher.py) の eligible public symbol coverage が **80% 以上** (= 44/55 以上) であること
- [ ] `helix code stats --uncovered --scope core5 --fail-under 80` が `exit 0` で成功 (Sprint .4 受入 gate)
- [ ] `helix-test` 全 PASS（shell + pytest + bats）
- [ ] `pytest cli/lib/tests/test_code_catalog.py` に uncovered logic の test が追加され PASS すること
- [ ] `bats cli/tests/test-helix-code.bats` の `--uncovered` / `--fail-under` E2E が追加され PASS すること
- [ ] PLAN-011 §3.6 の「`PLAN-011.1`」ステータスが `closed` へ更新されていること
- [ ] `PLAN-011` 参照（`PLAN-011 §3.6`）の deferred 状態が本PLANで引き継がれていること

### 受入条件（運用）

- [ ] `--fail-under` を使う CI ジョブと使わないジョブを分離
- [ ] `--uncovered` 出力を運用 runbook と evidence に保存
- [ ] `coverage` 計算式と母数定義（public symbol / top-level）のドキュメント整合をレビューで担保

## §6. 工程 / Sprint 構成

TL sprint_plan（採用）: `.1a → .1b → .2 → .3 → .4 → .5`

### .1a 現行資産・eligible/symbol 定義 / ignore 契約固定

- DoD
  - `code_catalog` / `helix-code` / テストの現状振り返り
  - `eligible` symbol 仕様（.py, .sh, tracked 前提, symbol 定義）を実装仕様書化
  - ignore を `.gitignore` と fixtures/generated/vendor の明示仕様に固定
- Evidence
  - 仕様レビュー結果（docs）
  - 既存テスト実行ログ（現状）

### .1b `--uncovered` 出力仕様・exit code・coverage式の設計

- DoD
  - default/JSON 形式定義完了
  - `--fail-under` 初期仕様確定
  - coverage 算式（`covered / eligible`）を明文化
- Evidence
  - 受入条件に反映した要件表
  - CLI 契約差分レポート

### .2 `--uncovered` 実装

- DoD
  - local scan のみで uncovered 一覧を生成
  - `exit 0 / 2 / 64` 振る舞いを実装
  - summary を末尾固定表示
- Evidence
  - pytest 単体で logic path 検証
  - bats で基本 CLI 出力検証

### .3 metadata 付与（cli/lib 優先）

- DoD
  - `cli/lib/*.py` の主要関数へ `@helix:index` 付与
  - カバレッジ 80% 到達の実質見積を同時確定
- Evidence
  - symbol 一覧差分（before/after）
  - 覆面率計算結果（phase1時点）

### .4 テスト実装・実行（pytest/bats/helix-test）

- DoD
  - `uncovered logic` unit テストを追加
  - ignore、exit code、JSON 形式の E2E を網羅
  - fixture/ generated/vendor 除外検証を追加
- Evidence
  - `pytest cli/lib/tests/test_code_catalog.py`
  - `bats cli/tests/test-helix-code.bats`
  - `helix-test` 実行結果

### .5 docs/運用メモ更新

- DoD
  - PLAN/README/運用メモ（coverage report evidence）更新
  - 証跡保存手順と運用時の解釈を統一
- Evidence
  - 更新済み docs の diff
  - 実測 coverage report の添付（または path 記載）

## §7. 見積 / 工数

- size: M
- 想定時間: **4-6h**
- 母数: core 5 ファイル / public symbol 55 / 追加目標 34 個
- 変更ファイル想定: **約 10**
  - `cli/helix-code` (`stats --uncovered` + `--fail-under` 追加)
  - `cli/lib/code_catalog.py` (uncovered logic 追加)
  - `cli/lib/tests/test_code_catalog.py` (unit test 追加)
  - `cli/tests/test-helix-code.bats` (E2E test 追加)
  - core 5 ファイル (`code_catalog.py` / `code_recommender.py` / `helix_db.py` / `skill_catalog.py` / `skill_dispatcher.py`) への metadata 追加
- Breath/Depth は L3 で設定済みの既存値を維持
  - density 4
  - depth 3

## §8. 改訂履歴

- v1.4 (2026-05-03): Sprint .2 実装 + Sprint .3 metadata 付与で発見された実態に同期。(1) skill_catalog.py の PoC seed 5 件は `_` 始まり関数 (private) のため eligible 外と確定 → §3.1 / §3.6 表の既 covered 数を 10 → 5 に修正。(2) `compute_uncovered` の covered 判定で `parse_helix_index_comment` を用いると 32+ 連続英数字を含む summary (例: `historical_to_active_audit_decision`) が `should_redact` の `_LONG_TOKEN_PATTERN` で False uncovered になる bug 発覚 → §3.2 covered 判定で `_is_index_marker_valid` (redaction 非適用 の文法 valid 判定) を採用と契約凍結。(3) 追加付与目標を 34 → 40 件 (45/56 = 80.4% gate pass) に再設定。
- v1.3 (2026-05-03): Sprint .1a contract (`.helix/proposals/PLAN-012-sprint1a-contracts.md`) 凍結に同期。(1) §3.2 covered 判定 = 直前 1 行 canonical + 連続コメント救済 + docstring 内対象外。(2) §3.4 `--scope` (all/core5) 新設、`--fail-under` を `--scope` の coverage_pct に対する閾値判定に固定、本 PLAN 受入 gate = `--scope core5 --fail-under 80`。(3) §3.6 id 命名 = kebab-case dotted (PLAN-011 seed 準拠)。
- v1.2 (2026-05-03): TL 第二回レビュー P0/P2x2 解消。(1) Phase 2 (cli/helix-*) を out-of-scope へ移動、suffixless と TRACKED_SUFFIXES の構造矛盾を解消。(2) 母数を実測値で固定 — cli/lib/*.py 全体 51 ファイル / 358 public symbol のうち, 本 PLAN scope は core 5 ファイル / 55 symbol / 80% = 44 個目標。(3) §3.3 `--uncovered` 出力契約を default (TSV + 末尾 summary 行) と --json (items+summary object) で完全分離、stderr は usage error のみと明示。
- v1.1 (2026-05-03): TL 第一回 P0/P2x2/P3 finding 解消。eligible を `tracked .py/.sh` の **public symbol**（top-level、`_` で始まるもの除外）へ確定、`--json` を items+summary object 形式へ確定、exit code を `64/0/2` に統一し、ignore を path ベースで明文化（`tests/` `cli/tests/` `fixture/` `generated/` `vendor/` 追加除外）。  
- v1.0 (2026-05-03): 初版 draft. PLAN-011 §3.6 の deferred 記載を引き継ぎ、本PLAN（coverage 80% 目標、`--uncovered`, `--fail-under`）を採択。TL findings（exit code, .gitignore, eligible 数式）を反映。
