# FR-INV16: 外部依存 / 脆弱性 監査

最終更新: 2026-05-14  
監査者: Research (Codex)  
不確実性:

- この実行環境では `helix` が PATH 上になく、`helix code find` / `helix review --uncommitted` は未実行。代替として `find` / `grep` / `sed` による read-only 調査を行った。
- `pip-audit` / `safety` / `gh` / `codex` / `claude` / `jq` / `yq` / `sqlite3` / `rg` / `bats` / `shellcheck` / `black` / `ruff` は未導入だったため、脆弱性検出と一部 runtime 実在確認は「未検証」を含む。
- `package.json` / `package-lock.json` は repo 内で確認できず、Node パッケージ依存は「CLI 名や wrapper 前提としての実質依存」が中心である。

## 概要

HELIX の依存リスクは、Python パッケージ数の多さではなく、**CLI / shell / LLM ツール / 外部サービスへの運用依存が広いこと**にある。明示的な Python 依存は `requirements-dev.txt` の 2 件だけだが、実運用では `bash` / `git` / `curl` / `node` / `npm` / `npx` / OpenAI Codex CLI / Anthropic Claude CLI / GitHub への依存が強い。特に LLM CLI と外部 binary の多くが lockfile や version gate なしで扱われており、更新時の破壊的変化を受けやすい。

## 選択肢

### Option A: 現状維持

- メリット: 追加コストが最小。
- デメリット: unpinned な CLI / binary / optional tool の drift が継続し、環境差異で再現性が崩れる。
- 推奨度: 低。

### Option B: V2 で pin と必須/optional の境界を明文化

- メリット: 依存更新時の影響範囲が読める。CI / setup / docs の整合も取りやすい。
- デメリット: setup 手順とテスト環境の見直しが必要。
- 推奨度: 高。

### Option C: shell 依存を減らして Python 標準ライブラリへ寄せる

- メリット: `jq` / `yq` / `rg` / `sqlite3` 非導入環境との差を減らせる。
- デメリット: 既存 shell script の一部置換コストがある。
- 推奨度: 中。

## 推奨

**Option B を主軸、Option C を補助として採用**を推奨する。  
理由は 3 点。

1. repo 直下の Python 依存は少ない一方、実際の運用依存は shell / Node / LLM CLI / GitHub に分散している。
2. 現状は `requirements-dev.txt` が loose pin、Node は lockfile 不在、LLM CLI は wrapper 前提で version 契約が弱い。
3. 依存削減は有効だが、先に「何が必須で、何が optional か」を固定しないと削減優先度を誤る。

## ソース

- [`requirements-dev.txt`](/home/tenni/ai-dev-kit-vscode/requirements-dev.txt:1)
- [`cli/config/models.yaml`](/home/tenni/ai-dev-kit-vscode/cli/config/models.yaml:1)
- [`cli/codex`](/home/tenni/ai-dev-kit-vscode/cli/codex:1)
- [`cli/claude`](/home/tenni/ai-dev-kit-vscode/cli/claude:1)
- [`cli/helix-codex`](/home/tenni/ai-dev-kit-vscode/cli/helix-codex:1)
- [`cli/helix-claude`](/home/tenni/ai-dev-kit-vscode/cli/helix-claude:1)
- [`cli/lib/llm_guard.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/llm_guard.py:1)
- [`cli/lib/yaml_parser.py`](/home/tenni/ai-dev-kit-vscode/cli/lib/yaml_parser.py:1)
- [`scripts/git-hooks/pre-commit`](/home/tenni/ai-dev-kit-vscode/scripts/git-hooks/pre-commit:1)
- [`scripts/install-git-hooks.sh`](/home/tenni/ai-dev-kit-vscode/scripts/install-git-hooks.sh:1)
- [`docs/v2/A-audit/security-audit.md`](/home/tenni/ai-dev-kit-vscode/docs/v2/A-audit/security-audit.md:1)

## 依存台帳

| 依存名 | カテゴリ | 用途 | 版数固定 | 必須度 | 代替可能性 | 脆弱性 risk | V2 変更計画 | 理由 |
|---|---|---|---|---|---|---|---|---|
| `python3` | Python | HELIX の Python CLI / hook / parser 実行基盤 | unpinned | 必須 | low | unknown | pin | 実行実測は `Python 3.12.3` だが repo 契約は固定されていない |
| `pytest>=7.0` | Python | Python テスト実行 | loose (`>=`) | 推奨 | high | unknown | pin | `requirements-dev.txt` は下限のみで再現性が弱い |
| `coverage>=7.0` | Python | coverage 計測 | loose (`>=`) | 推奨 | mid | unknown | pin | CI/ローカル差分で出力が揺れうる |
| `sqlite3` module | Python | `.helix/helix.db` 操作 | N/A | 必須 | low | unknown | as-is | Python 標準ライブラリ依存で置換余地は低い |
| `json` / `pathlib` 等 stdlib | Python | wrapper / parser / telemetry の基礎処理 | N/A | 必須 | low | unknown | as-is | 標準ライブラリ中心設計は妥当 |
| `bash` | shell | 全主要 wrapper / script の実行シェル | unpinned | 必須 | low | unknown | pin | 実スクリプトの shebang が `bash` 前提 |
| `git` | shell | hook / diff / repo 状態取得 | unpinned | 必須 | low | unknown | pin | ほぼ全フローで使用 |
| `grep` | shell | ガード・検索・検査 | unpinned | 必須 | mid | unknown | as-is | POSIX 互換で代替可だが依存は強い |
| `find` | shell | ファイル探索 | unpinned | 必須 | mid | unknown | as-is | `rg` 不在時の代替にもなる |
| `wc` | shell | bytes / line count 算出 | unpinned | 必須 | high | unknown | as-is | 代替容易 |
| `sed` | shell | conf / output 整形 | unpinned | 必須 | mid | unknown | as-is | GNU/BSD 差異は要注意 |
| `xargs` | shell | 一括検索 / lint 補助 | unpinned | 推奨 | high | unknown | as-is | 必須ではないが実査で多用 |
| `realpath` | shell | shim の自己解決・path 安全化 | unpinned | 必須 | mid | unknown | as-is | portability 差異はあるが安全上重要 |
| `timeout` | shell | `helix-claude` の execute timeout | unpinned | 推奨 | high | unknown | as-is | GNU coreutils 依存がある |
| `curl` | shell | 外部 URL チェック / 文書取得の実質依存 | unpinned | 推奨 | mid | unknown | pin | docs / local settings に散見される |
| `sqlite3` binary | shell | DB 直接調査・verify 補助 | unpinned | 推奨 | mid | unknown | as-is | verify / local settings で参照。実環境には未導入 |
| `jq` | shell | JSON 整形・補助 | unpinned | optional | high | unknown | deprecate | 参照はあるが必須 runtime ではない |
| `yq` | shell | YAML 補助 | unpinned | optional | high | unknown | deprecate | `yaml_parser.py` で一部代替済み |
| `rg` (ripgrep) | shell | 高速コード検索 | unpinned | 推奨 | high | unknown | as-is | 推奨だが無くても `find` / `grep` で代替可 |
| `tree` | shell | 可視化用 | unpinned | optional | high | unknown | deprecate | UX 向上用途のみ |
| `fd` | shell | 高速 file search | unpinned | optional | high | unknown | deprecate | `find` で代替可能 |
| `bat` | shell | pretty print | unpinned | optional | high | unknown | deprecate | 不在でも運用可能 |
| `node` | Node | npm / npx / CLI package 実行基盤 | unpinned | 推奨 | low | unknown | pin | 実環境は `v22.22.0`、repo 契約は未固定 |
| `npm` | Node | package runner / install 経路 | unpinned | 推奨 | mid | unknown | pin | `@openai/codex` 等の配布経路候補 |
| `npx` | Node | 一時実行経路 (`@openai/codex` 等) | unpinned | 推奨 | mid | unknown | pin | `llm_guard.py` が package runner を明示的に検査 |
| `package.json` / `package-lock.json` | Node | Node 依存管理 | N/A | optional | high | unknown | new | repo に不在。Node 依存の再現性が弱い原因 |
| `@openai/codex` | LLM | raw Codex CLI 実体 | unpinned | 推奨 | low | unknown | pin | `cli/codex` / `llm_guard.py` が前提化 |
| `@anthropic-ai/claude-code` | LLM | raw Claude CLI 実体 | unpinned | 推奨 | low | unknown | pin | `cli/claude` / `llm_guard.py` が前提化 |
| `gpt-5.5` | LLM | TL / QA / advisor 用モデル | unpinned | 必須 | low | unknown | as-is | `models.yaml` に固定名あり、provider 側変更の影響を受ける |
| `gpt-5.4` | LLM | SE / research / security 等 | unpinned | 必須 | mid | unknown | as-is | 役割面の依存が強い |
| `gpt-5.3-codex` | LLM | default primary / dba / devops | unpinned | 必須 | mid | unknown | as-is | default_primary に指定 |
| `gpt-5.3-codex-spark` | LLM | pg / docs 高速実装 | unpinned | 推奨 | mid | unknown | as-is | fallback chain にも登場 |
| `gpt-5.4-mini` | LLM | recommender / classifier fallback | unpinned | 推奨 | mid | unknown | as-is | budget / classifier 系で参照 |
| `claude-sonnet-4-6` | LLM | PMO / impl-sonnet | unpinned | 推奨 | mid | unknown | as-is | Claude 系委譲の中核 |
| `claude-haiku-4-5-20251001` | LLM | PMO 軽作業 | unpinned | optional | high | unknown | as-is | docs/light task 向け |
| `claude-opus-4-7` | LLM | pm-advisor | unpinned | optional | mid | unknown | as-is | advisory 用で lock-in は中程度 |
| `GitHub` | 外部 | PR / issue / Actions / raw content 参照 | unpinned | 必須 | low | unknown | as-is | docs・hooks・運用フロー全体で前提化 |
| `github.com` | 外部 | repo / raw content の参照先 | unpinned | 必須 | mid | unknown | as-is | settings / docs / scripts に登場 |
| `api.github.com` | 外部 | GitHub API fetch | unpinned | 推奨 | mid | unknown | as-is | local settings に許可ドメインあり |
| `raw.githubusercontent.com` | 外部 | raw README / script 取得 | unpinned | 推奨 | mid | unknown | as-is | mirror 的参照先として使用痕跡あり |
| `SSH key` | 外部 | Git / remote access の認証前提 | N/A | 推奨 | low | unknown | as-is | `llm_guard.py` が `--sshlogin` を検査し、運用依存を示す |
| `pytest` command | dev | テスト実行コマンド | unpinned | 推奨 | high | unknown | pin | requirements 上は存在するが環境には未導入 |
| `bats` | dev | shell test | unpinned | 推奨 | mid | unknown | pin | verify / docs で前提化、実環境未導入 |
| `shellcheck` | dev | shell lint | unpinned | 推奨 | mid | unknown | pin | 品質基準上の依存だが未導入 |
| `black` | dev | formatter | unpinned | optional | high | unknown | deprecate | repo 実依存は弱い、未導入 |
| `ruff` | dev | lint / format | unpinned | optional | high | unknown | pin | 将来統一先としては有望だが未整備 |
| `pip-audit` | dev | Python 脆弱性監査 | unpinned | 推奨 | high | unknown | pin | task 要件にはあるが未導入 |
| `safety` | dev | Python 脆弱性監査 | unpinned | optional | high | unknown | deprecate | `pip-audit` と役割重複、未導入 |
| `gh` | dev | GitHub CLI 補助 | unpinned | optional | mid | unknown | as-is | plugin / docs では重要だが core runtime 必須ではない |

## 監査メモ

### Python 依存

- 明示的な repo 管理依存は `requirements-dev.txt` の `pytest>=7.0`, `coverage>=7.0` のみ。
- `cli/lib/yaml_parser.py` は PyYAML 依存を避ける方針で、これは依存削減として良い。
- 実行環境の `pip list` には `pytest==9.0.3`, `PyYAML==6.0.1`, `requests==2.31.0` などがあるが、repo 管理ではなく環境依存なので **HELIX の direct dependency とは断定しない**。

### shell / system 依存

- HELIX は shell wrapper が厚く、`bash` と `git` は実質コア依存。
- `jq` / `yq` / `sqlite3` / `rg` / `tree` / `fd` / `bat` は optional/推奨寄りだが、環境差異を招きやすい。
- `sed` / `realpath` / `timeout` のような「文書には出にくい実質依存」がある。

### Node / npm 依存

- repo 内に `package.json` / `package-lock.json` がないため、Node package version を lock できていない。
- その一方で `@openai/codex` / `@anthropic-ai/claude-code` を package runner 経由で扱う前提ロジックは存在する。

### LLM API / SDK 依存

- hard-code された model 名は `cli/config/models.yaml` 以外にも test / docs / fallback 設定に散在する。
- provider SDK を直接 import しているのではなく、CLI wrapper 依存が主体。
- version gate は弱く、CLI 実体が見つからない場合は wrapper が失敗する設計。

### 外部サービス依存

- GitHub 依存は repo 運用と監査フローの両面で強い。
- OpenAI / Anthropic 自体への direct HTTP endpoint hard-code は今回の範囲では明確に確認できなかった。
- `github.com` / `api.github.com` / `raw.githubusercontent.com` への到達性が悪い環境では一部運用が詰まる。

## 依存件数集計

| カテゴリ | 件数 |
|---|---:|
| Python | 5 |
| shell | 17 |
| Node | 4 |
| LLM | 9 |
| 外部 | 5 |
| dev | 7 |
| **合計** | **47** |

## unpinned 一覧 (V2 で pin 必須)

- `python3`
- `bash`
- `git`
- `curl`
- `node`
- `npm`
- `npx`
- `@openai/codex`
- `@anthropic-ai/claude-code`
- `pytest` command
- `bats`
- `shellcheck`
- `ruff`
- `pip-audit`

## known CVE 一覧

- 今回の監査では **確定した known CVE は列挙できなかった**。
- 理由: `pip-audit` / `safety` 未導入、`npm audit` 対象ファイル不在、外部脆弱性 DB への照会もこの作業では未実施。
- したがって、多くの依存の `脆弱性 risk` は `unknown` とした。

## 置換困難 (low) top-5

1. `python3`
2. `bash`
3. `git`
4. `@openai/codex`
5. `GitHub`

## V2 で依存削減候補 top-10

1. `jq`
2. `yq`
3. `tree`
4. `fd`
5. `bat`
6. `black`
7. `safety`
8. `gh`
9. `curl` の一部 manual fetch
10. `sqlite3` binary

## 推奨アクション

1. `requirements-dev.txt` を strict pin 化し、Python version も明記する。
2. `package.json` / lockfile を導入するか、Node 依存を「非公式補助」に格下げして docs で明示する。
3. `@openai/codex` と `@anthropic-ai/claude-code` の許容 version range を文書化する。
4. `pip-audit` を dev dependency として導入し、CI で fail-close にする。
5. `jq` / `yq` / `sqlite3` / `gh` の必須/optional を setup guide に分離して書く。
