# Lint / Scan Tool Ecosystem 統合計画（FR-GR09 / FR-GR12）

作成日: 2026-05-14  
種類: 設計（PoC 実装計画）  
対象: FR-GR09（lint tool 統合）、FR-GR12（security scan 統合）

参照:
- `docs/v2/L1-REQUIREMENTS.md`
- `docs/v2/A-audit/security-audit.md`
- `docs/v2/A-audit/dependencies-audit.md`
- `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_helix_fill_holes_principle.md`

## 1. 目的

本計画は、lint / scan を単独実行ではなく、`helix` 連携と gate 連動で再現可能にする設計を定義する。

- `docs`, `cli`, `migration`, `schema` の品質チェックを一元的に統合する。
- 検出結果を `helix.db` の `detector_runs` と `fail_fix_log` に記録し、運用可視性を上げる。
- 段階的に fail-close を導入し、初期から開発効率を毀損しない。
- 初回は PoC レベルとして、最小構成で実行経路を確立し、次期で運用を拡張する。

## 2. 参照要件の要約

### 2.1 FR-GR09（lint tool 統合）

- docs lint（markdownlint/vale）
- CLI shell lint（shellcheck/shfmt）
- Python lint（ruff/black/pyright）
- 設定系 lint（yamllint）
- migration lint（sqlfluff）
- JSON schema validation

### 2.2 FR-GR12（security scan 統合）

- secret 検知（gitleaks / trufflehog）
- static security（semgrep）
- CVE（pip-audit / safety / npm audit）

### 2.3 要件起点から導く運用原則

監査系ドキュメントが指摘する課題は「分散した検知」「再現性不足」であるため、PoC では:

1. 実行経路（lint/scan）を一貫化する
2. 検知イベントをDBへ集約する
3. gate へ明確に連動する

を同時に満たす。

## 3. 統合アーキテクチャ

- `pre-commit`: 開発者ローカルで即時検知
- `helix sync --lint`: 一括実行（lint と scan を集約）
- `detector_runs`: 実行結果の構造化保存
- `fail_fix_log`: fail-close または阻止イベントの追跡
- `gates (G2/G3/G4/G6)`: lint/scan 状況の品質判定

イベントフロー:

```text
tool実行 -> 結果変換 -> detector_runs upsert
             -> (失敗種別がfailなら) fail_fix_log 追加
             -> gate 判定へ反映
             -> sync/CI レポートへ出力
```

## 4. lint ツール統合（FR-GR09）

| Tool | 対象 | 設定 | 連携先 |
|---|---|---|---|
| markdownlint-cli | `docs/*.md` | `.markdownlint.json` | pre-commit + G2/G4 |
| vale | `docs/` prose | `.vale.ini`, `styles/` | pre-commit |
| shellcheck | `cli/helix-*` | `.shellcheckrc` | pre-commit + G4 |
| shfmt | `cli/helix-*` | format check 設定 | pre-commit |
| ruff | `cli/lib/*.py` | `pyproject.toml` | pre-commit + G4 |
| black | `cli/lib/*.py` | `pyproject.toml` | pre-commit |
| pyright | `cli/lib/*.py` | `pyrightconfig.json` | G4（任意） |
| yamllint | `cli/config/*.yaml` | `.yamllint.yaml` | pre-commit |
| sqlfluff | `migration/*.sql` | `.sqlfluff` | G3（migration freeze） |
| jsonschema | 各種 JSON | `schema/` | various |

### 4.1 インストール（PoC 版）

#### markdownlint-cli
- npm: `npm install -g markdownlint-cli`
- brew: `brew install markdownlint-cli`
- 確認: `markdownlint --version`

#### vale
- brew: `brew install vale`
- 確認: `vale --version`

#### shellcheck / shfmt
- brew: `brew install shellcheck shfmt`
- apt 系: `apt-get update && apt-get install -y shellcheck`
- 確認: `shellcheck --version`, `shfmt -version`

#### ruff / black / pyright / yamllint / sqlfluff / pip-audit / safety / semgrep
- `pip install ruff black pyright yamllint sqlfluff pip-audit safety semgrep`
- 確認: 各 tool の `--version` コマンド

#### gitleaks / trufflehog / npm audit
- gitleaks: `brew install gitleaks`
- trufflehog: `pip install trufflehog`
- npm audit: `npm -v`（同時に node/npm が前提）
- 確認: `gitleaks version`, `trufflehog --version`, `npm audit`

### 4.2 設定例（各 tool）

#### `.markdownlint.json`
```json
{
  "default": true,
  "MD003": false,
  "MD013": false,
  "MD033": false,
  "no-hard-tabs": true,
  "line-length": false,
  "heading-style": { "style": "atx" }
}
```

#### `.vale.ini`
```ini
StylesPath = styles
MinAlertLevel = warning
[*.md]
BasedOnStyles = proselint, write-good
Vale.Spelling = NO
```

#### `.shellcheckrc`
```bash
external-sources=true
source-path=SCRIPTDIR
enable=all
disable=SC1091
```

#### `pyproject.toml`（ruff / black）
```toml
[tool.ruff]
line-length = 100
target-version = "py312"
extend-exclude = [".venv", ".git"]

[tool.ruff.lint]
select = ["E","F","W","I","UP","B","SIM"]
ignore = ["E501"]

[tool.black]
line-length = 100
target-version = ["py312"]
```

#### `.pyrightconfig.json`
```json
{
  "typeCheckingMode": "basic",
  "pythonVersion": "3.12",
  "reportMissingTypeStubs": "warning",
  "reportUnknownParameterType": "warning"
}
```

#### `.yamllint.yaml`
```yaml
extends: default
ignore: |
  .venv/
  .git/
rules:
  line-length:
    max: 200
  trailing-spaces: { level: warning }
  indentation:
    spaces: 2
    indent-sequences: whatever
```

#### `.sqlfluff`
```ini
[sqlfluff]
dialect = sqlite
exclude_rules = L031,L034
max_line_length = 200
```

#### `.gitleaks.toml`
```toml
title = "gitleaks config"
version = "3"
[[rules]]
id = "api-token"
description = "Generic API key"
regex = '(?i)(api[_-]?key|apikey|access[_-]?token)\\s*[:=]\\s*["\']?[A-Za-z0-9_\\-]{16,}["\']?'
tags = ["secret"]
[[rules]]
id = "private-key"
description = "Private key"
regex = '-----BEGIN (RSA |EC )?PRIVATE KEY-----'
tags = ["secret","private"]
```

#### `semgrep.yaml`
```yaml
rules:
  - id: detect-hardcoded-secret
    pattern: |
      (?i)(secret|api[_-]?key|password)\s*[:=]\s*["'][^"']+["']
    message: "possible hardcoded credential"
    severity: WARNING
    languages: [python, bash]
```

#### `trufflehog.yaml`
```yaml
exclude_paths:
  - .git
  - .venv
scan:
  all_files: true
  include_file_names: ["*.py","*.sh","*.md","*.json","*.yml","*.yaml"]
```

### 4.3 失敗分類と `detector_runs` 反映

| 種別 | status | fail-close |
|---|---|---|
| markdownlint/vale warning | warn | 否（PoC 初期） |
| shellcheck/ruff warning | warn | 原則否 |
| secret 検知 | fail | 即時 |
| semgrep P1 以上 | fail | 即時 |
| pip-audit critical/high | fail | 即時 |

`detector_runs` schema:

- `tool_name`
- `detector_kind`（`lint` / `scan`）
- `target_scope`
- `status`（pass / warn / fail）
- `severity`（low / medium / high / critical）
- `summary_json`（対象ファイル数、件数、推奨対処、実行時間）
- `event_time`

`fail_fix_log` への auto-log:

- 失敗条件を満たした時点で `event_kind='lint_failure'` または `event_kind='scan_failure'`
- `status='open'` で開始し、修正時に `in_progress` / `resolved` へ更新
- `context_json` に `tool`, `file_count`, `first_error`, `run_id` を保存

## 5. security scan 統合（FR-GR12）

### 5.1 対象と用途

- gitleaks: commit / file を横断する secret 検知（即 fail-close）
- trufflehog: credential leak の横断検知（即 fail-close）
- semgrep: static 脆弱性（severity により fail）
- pip-audit / safety: dependency CVE（P0/P1 は fail-close）
- npm audit: Node 依存（該当リポジトリ時のみ）

### 5.2 結果分類

1. 即 fail-close
   - secret（gitleaks, trufflehog）
   - P0/P1 CVE
2. warning
   - 非 critical の lint 警告
3. denied
   - 依存欠如/実行不可（PoC 初期は block ではなく追跡）

## 6. pre-commit 設計

### 6.1 方針

PoC 段階では直近ツールを local hook で実行し、将来は各言語ランナーへ置換する。

`pre-commit` の hook `id` は本計画で再実装対象。`files` は docs/shell/python/yaml の最小限定で開始。

### 6.2 完全 YAML（最終仕様）

```yaml
repos:
  - repo: local
    hooks:
      - id: helix-markdownlint
        name: helix markdownlint
        entry: helix-lint-proxy markdown
        language: system
        files: '^docs/.*\\.md$'
      - id: helix-vale
        name: helix vale
        entry: helix-lint-proxy vale
        language: system
        files: '^docs/.*\\.md$'
      - id: helix-shellcheck
        name: helix shellcheck
        entry: helix-lint-proxy shell
        language: system
        files: '^cli/helix-.*'
      - id: helix-shfmt
        name: helix shfmt
        entry: helix-lint-proxy shfmt
        language: system
        files: '^cli/helix-.*'
      - id: helix-ruff
        name: helix ruff
        entry: helix-lint-proxy ruff
        language: system
        files: '^cli/lib/.*\\.py$'
      - id: helix-black
        name: helix black
        entry: helix-lint-proxy black
        language: system
        files: '^cli/lib/.*\\.py$'
      - id: helix-yamllint
        name: helix yamllint
        entry: helix-lint-proxy yaml
        language: system
        files: '^cli/config/.*\\.ya?ml$'
      - id: helix-gitleaks
        name: helix gitleaks
        entry: helix-scan-proxy gitleaks
        language: system
      - id: helix-trufflehog
        name: helix trufflehog
        entry: helix-scan-proxy trufflehog
        language: system
      - id: helix-semgrep
        name: helix semgrep
        entry: helix-scan-proxy semgrep
        language: system
        files: '^(cli|docs|migration)/.*$'
      - id: helix-doc-verify
        name: helix doc verify
        entry: helix-doc-verify
        language: system
        files: '^docs/v2/.*\\.md$'
```

### 6.3 注意

- `pass_filenames` は使用せず、proxy 側で対象 glob を再解決する。
- `sqlfluff`, `gitleaks`, `npm audit` は全体走査モードを許容し、必要時のみ `pass_filenames: false` 検討。
- `black`/`ruff` は `--check` で運用し、差分を書き戻さない。

## 7. `helix sync --lint` 連携

### 7.1 追加想定引数

- `--lint`: lint/scan を実行
- `--lint-threshold`: warning/fail 閾値
- `--skip-lint`: lint 抜き実行
- `--skip-scan`: scan 抜き実行
- `--json-output`: 実行結果 JSON を出力

### 7.2 実行フロー

1. 引数解析
2. 対象 scope 決定
3. lint tool 実行
4. scan 実行
5. detector_runs 登録
6. fail-close 条件検知時に fail_fix_log 自動追加
7. gate フィードバック（G2/G3/G4/G6）への返却

### 7.3 しきい値初期値

- `warning_count <= 80` で pass 相当
- `fail_count == 0` で pass
- Phase 4.2 以降: `warning_count <= 30` へ厳格化

### 7.4 ログ例（最小）

```text
{
  "command": "helix sync --lint --lint-threshold 80",
  "tools_run": ["markdownlint", "shellcheck", "yamllint", "ruff", "gitleaks"],
  "detector_runs": {"pass": 120, "warn": 12, "fail": 0},
  "fail_fix_log": []
}
```

## 8. Gate 連動（G2 / G3 / G4 / G6）

- **G2**: docs lint（markdownlint/vale）を設計 doc 品質指標と連動
- **G3**: migration freeze で `sqlfluff` を必須対象化
- **G4**: shellcheck + ruff + semgrep を edit 前後の安全チェックへ
- **G6**: gitleaks + trufflehog + pip-audit を週次含めて強制

判定優先度:

1. `event_kind='scan_failure'`（secret/CVE）最優先
2. `status='fail'` の lint は `warn` より上位
3. `warn` のみで既存 CI を落とさない

## 9. PoC 3 Phase 実装（必須）

### Phase 1（基本 lint）

1. `markdownlint-cli` 導入 + `.markdownlint.json` 作成
2. `shellcheck` + `.shellcheckrc` 導入
3. `yamllint` + `.yamllint.yaml` 導入
4. `.pre-commit-config.yaml` を追加（markdown/shell/yaml）
5. `helix sync --lint` の最小実装（warn 記録）

受入:
- `helix sync --lint --help` に該当オプションが追加
- pre-commit 実行時に docs/shell/yaml warning が可視化
- detector_runs へ warning が入る

### Phase 2（Python / scan）

6. `ruff`, `black`, `pyproject.toml` 導入
7. `gitleaks`, `.gitleaks.toml` 導入
8. `semgrep`, `semgrep.yaml` 導入

受入:
- python lint が detector 経路に入る
- secret scan が `fail_fix_log` へ連動
- semgrep rule に対する alert が表示可能

### Phase 3（CVE / evidence）

9. `pip-audit`, `safety` の週次ジョブ整備
10. `detector_runs` / `fail_fix_log` の未記録ケースを潰す

受入:
- CVE 結果が DB 記録される
- fail-close 条件で `event_kind='lint_failure'` / `scan_failure` が残る
- KPI ダッシュボード更新の土台が出来る

## 10. 既存機能との重複調整

- PLAN-024 の design lint と重複しうる `docs` lint は範囲を分離。`docs/v2/C-followup/*` は段階的に除外しつつ、最終統合時に集約。
- `ai-coding lint` は構造重複を担うため代替しない。
- `helix test`（bats/pytest）は `helix sync --lint` 成功後に呼ぶ順序を維持。  
  （PoC 初期は `warning` で進行継続）

## 11. 失敗時対応

- `secret` / `critical CVE`: 即 fail-close、開発者へ通知 + 修正要求
- `missing dependency`: warning とし、CI では一旦許容（`--skip-*` で明示可能）
- `tool 実行タイムアウト`: 失敗として記録し、再実行可能性を保持
- `false positive`: `suppress` 申請で一時除外を追跡し、次期で除去

## 12. KPI

- lint coverage: **80%+**
- secret scan false positive: **5%以下**
- existing suite impact: **最小化（初期 warning 運用）**
- 再現性: 同一実行で同一 summary が再取得可能

## 13. 影響範囲（実装対象）

- 新規: `cli/lib/lint_runner.py`
- 新規: `.pre-commit-config.yaml`
- 新規: `.markdownlint.json`, `.shellcheckrc`, `.yamllint.yaml`, `pyproject.toml`, `.gitleaks.toml`, `semgrep.yaml`, `.pyrightconfig.json`, `trufflehog.yaml`
- 既存変更: `helix sync`, `helix gate`（G2/G3/G4/G6）連携

## 14. リンク整合チェック結果

- `docs/v2/L1-REQUIREMENTS.md`: 存在
- `docs/v2/A-audit/security-audit.md`: 存在
- `docs/v2/A-audit/dependencies-audit.md`: 存在
- `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_helix_fill_holes_principle.md`: 存在

## 15. TODO 残存

- `cli/tools/helix_lint_proxy.py` のプロキシ実装
- `cli/tools/helix_scan_proxy.py` の実装
- `helix-doc-verify` と docs lint の最終例外設定調整
- `requirements-dev.txt` 運用ルール確定
- `--lint-threshold` のデフォルト値再調整（Phase 4.2）
- `npm audit` の適用対象を package.json 規模で再定義
- CI 週次ジョブの実装（pip-audit / safety）

## 16. 参考決定

- 初期は warning 重視で運用し、false positive と実装速度の摩擦を抑える。
- セキュリティ／秘密情報検知は初期から fail-close を堅持し、PoC でも遮断を妥協しない。
- 既存の分散検知を一本化する価値を優先し、初回の完璧性より再現可能性を優先した。

## 17. まとめ

本計画は FR-GR09 / FR-GR12 を 3 フェーズで実行する PoC で、lint/scan ツールを `pre-commit`、`helix sync`、`gates`、`detector_runs`/`fail_fix_log` に接続するものです。  
初期は warning を採用し、Phase 4.2 以降で fail-close を拡張することで、品質と開発速度の両立を実現する。
