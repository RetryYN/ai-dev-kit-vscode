# ADR-004: Bash-Python ハイブリッドアーキテクチャ

> Status: Accepted
> Date: 2026-04-05
> Deciders: PM, TL

---

## Context

HELIX CLI は AI エージェント駆動の開発ワークフローを統制するフレームワークであり、以下の 2 つの要件を同時に満たす必要がある:

1. **CLI オーケストレーション**: サブコマンドのディスパッチ、パイプライン連携、外部ツール（codex exec, gh, git）の呼び出し、ファイル操作
2. **構造化データ処理**: YAML/JSON の読み書き、SQLite による永続化、JSON Schema バリデーション、パターンマッチング、品質スコア算出

単一言語ですべてを実装する選択肢と、各要件に適した言語を使い分ける選択肢がある。

---

## Decision

**CLI コマンド層（Layer 2）は Bash、ライブラリ層（Layer 3）は Python** のハイブリッドアーキテクチャを採用する。

| レイヤー | 言語 | 責務 |
|---------|------|------|
| Entry Point (`cli/helix`) | Bash | サブコマンドを `exec` で子プロセスに委譲 |
| CLI Commands (`cli/helix-*`) | Bash | 引数パース、ユーザー対話、lib 呼び出し、出力整形 |
| Lib (`cli/lib/*.py`) | Python | 状態管理、DB 操作、検証、学習、ビルダー |
| Lib (`cli/lib/*.sh`) | Bash | 共通関数（`helix-common.sh`）: パス解決、exit code 定義 |

Bash から Python を呼び出す方式は以下の 2 パターンを使う:

1. **`python3 -c`**: 短い処理（1-2 行の YAML 読み書き）
2. **`python3 module.py args`**: 構造化された処理（DB 操作、バリデーション）

---

## Alternatives

### A1: 全て Python (Click/Typer ベース)

- 利点: 型安全性、テスタビリティ、統一的なエラーハンドリング
- 欠点: 外部ツール呼び出しが subprocess 経由で冗長。シェルスクリプトの透明性が失われる。Python 環境依存が増える

### A2: 全て Bash

- 利点: 依存なし、どこでも動く
- 欠点: SQLite 操作が困難。JSON/YAML パースが脆弱。テストが書きにくい。複雑なデータ構造の処理に限界

### A3: Go / Rust でシングルバイナリ

- 利点: 配布が容易、高速
- 欠点: 開発コストが高い。AI エージェントが生成・修正しにくい。YAML テンプレートとの親和性が低い

---

## Consequences

### 正の影響

- **適材適所**: CLI オーケストレーションは Bash のパイプライン・exec が最適。データ処理は Python の標準ライブラリ（sqlite3, json, re, hashlib）で安全に実装
- **透明性**: 開発者がシェルスクリプトで直接操作できる。`cat .helix/phase.yaml` でフェーズ状態を確認可能
- **AI 親和性**: Bash/Python は AI エージェントが最も得意とする言語。修正・拡張が容易
- **依存最小化**: Python 標準ライブラリのみで動作（PyYAML 不使用、独自 yaml_parser.py）

### 負の影響

- **境界のデータ受け渡し**: Bash-Python 間のデータ受け渡しが環境変数、heredoc Python、標準出力パースに頼る場面がある
- **エラーハンドリング不統一**: `set -eo pipefail` と `set -euo pipefail` が混在。exit code の一貫性に課題
- **テストの二重化**: Python 部分は pytest、Bash 部分は verify スクリプトで別々にテスト

### リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| Bash の複雑化 | ビジネスロジックは Python に寄せる。Bash はオーケストレーションのみ |
| Python バージョン依存 | Python 3.10+ を前提。`from __future__ import annotations` で型ヒント互換 |
| exit code の不統一 | `helix-common.sh` に定義済み exit code を一元管理（TD-006 として追跡中） |

---

## References

- `cli/helix` (Entry Point)
- `cli/lib/helix-common.sh` (共通関数)
- `cli/lib/yaml_parser.py` (PyYAML 不使用の独自パーサー)
- `.helix/reverse/R2-as-is-design.md` (R2 設計復元)
