# ADR-011: helix-test / helix-test-debug の重複管理方針

> Status: Accepted
> Date: 2026-04-14
> Deciders: PM, TL

---

## Context

`cli/helix-test`（1551行）と `cli/helix-test-debug`（1540行）は 99% 同一のコードを持つ。差分は:

- `helix-test-debug` は `set +e` / `set -e` の切り替えで失敗時にも継続実行
- `helix-test-debug` は stderr を抑制しない（デバッグ時に全出力を見るため）
- `helix-test-debug` は個別テストの詳細ログを出力

これは GAP-030 として検出された。

2つのファイルが並存する理由:

- **通常運用**: `helix-test` で最初の失敗で即停止、CI に組み込み
- **デバッグ運用**: `helix-test-debug` で全テストを走らせて失敗箇所を網羅

重複コードの問題:

- 修正時に両方のファイルを更新する必要（同期忘れリスク）
- 差分が把握しにくい（意図的な違いとバグによる違いの区別困難）
- 合計 3091 行のコードが実質的に1つのテストスクリプト

---

## Decision

**現状の2ファイル並存を維持しつつ、共通ロジックを source で抽出するリファクタリングを段階的に実施する**。

### 短期（現在〜次スプリント）

- 現状維持: `helix-test` と `helix-test-debug` の2ファイルを並存
- 修正時のルール: 一方を修正したら必ず他方も更新（pre-commit フック推奨）
- CI では `helix-test` のみ実行（`helix-test-debug` は開発者ローカル用）

### 中期（3-5 スプリント内）

- 共通ライブラリ `cli/lib/helix-test-common.sh` を抽出:
  - 1500行中 1480行は完全同一 → 共通化対象
  - `run_test` / `assert_*` / `test_*_setup` 等のユーティリティ関数
- `helix-test` と `helix-test-debug` は `source cli/lib/helix-test-common.sh` で共通化
- 各ファイルは 50〜100 行程度に縮小（set フラグ設定とエントリポイントのみ）

### 長期（将来スプリント）

- Python ベースのテストランナー（pytest スタイル）への移行を検討
- 現状の Bash ベースは helix-common.sh / yaml_parser.py に強く依存するため、全面移行は慎重に

### 採用しない選択肢

- **即座の統合**（debug 機能をオプションフラグ化）: 1回のリファクタで1500行を書き換えるリスクが大きい
- **helix-test-debug の削除**: デバッグ運用の必要性は明確、削除は機能退行

---

## Alternatives

### A1: helix-test に `--debug` オプション追加して1ファイル化

- 利点: 重複完全排除、保守コスト低
- 欠点: 大規模リファクタ、オプション経路の分岐が複雑化、回帰リスク

### A2: helix-test-debug を即削除

- 利点: 管理対象が1つに
- 欠点: デバッグ機能の退行、全テスト網羅実行ができなくなる

### A3: テストランナーを pytest に全面移行

- 利点: 標準ツール化、並列実行・カバレッジ計測が容易
- 欠点: 既存 Bash 固有テスト（`yaml_parser.py` / `helix-common.sh` 等）の移植コスト大

---

## Consequences

### 正の影響

- **運用継続性**: 既存の CI / 開発フローに影響なし
- **明示的な管理方針**: 2ファイル並存が意図的であることを ADR で記録
- **段階的改善パス**: 共通ライブラリ抽出で重複を機械的に削減する道筋

### 負の影響

- **短期的な重複コスト**: 同期忘れリスクは継続（当面）
- **行数の累積**: 新テスト追加時は両ファイルに追加が必要

### リスクと緩和策

| リスク | 緩和策 |
|--------|--------|
| 同期忘れ | pre-commit フックで `diff cli/helix-test cli/helix-test-debug` の差分を既知パターン以外は警告 |
| デバッグ固有バグ | `helix-test-debug` の固有コード部分（set +e 切替）を minimum に保つ |
| ファイル行数増加 | 1ファイル 2000 行を超えたら共通ライブラリ抽出を優先実施 |

---

## References

- `cli/helix-test`（1551行）
- `cli/helix-test-debug`（1540行）
- [GAP-030](/.helix/reverse/R4-gap-register.md)
- 次アクション: GAP-039/040（helix-debug / helix-verify-all のテスト拡充）と合わせて共通ライブラリ化を検討
