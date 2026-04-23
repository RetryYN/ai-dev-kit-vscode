> 目的: G5 で `docs/DESIGN.md` を公式 `design.md lint` で fail-close 検証し、UI 案件の文書契約を安定運用する。

# DESIGN.md lint 統合ガイド（G5 / Phase 1）

## 実行コマンド

```bash
cli/libexec/design-md lint docs/DESIGN.md
```

- version pin は wrapper 側で固定（`@google/design.md@0.1.1`）
- 呼び出し側で `npx @google/design.md@...` を直接実行しない

## Trigger Matrix（drive x ui）

| drive | sprint.ui | lint 実行 |
|---|---|---|
| fe | true/false/未設定 | Yes |
| fullstack | true/false/未設定 | Yes |
| agent | true | Yes |
| agent | false/未設定 | No |
| be | true | Yes |
| be | false/未設定 | No |
| db | true | Yes |
| db | false/未設定 | No |

補足:
- 既存の `be|db + ui=false` auto-skip はそのまま維持
- G5 では auto-skip 判定の後に lint 要否判定を行う

## Verdict Rule（要点）

- `docs/DESIGN.md` 不在（lint 対象時）: FAIL（mandatory）
- lint exit `1`: FAIL（mandatory）
- lint exit `0`: PASS（warning/info は情報表示のみ）
- tool 実行失敗（npx 実行不可、fetch 失敗など）: FAIL（fail-close）

## FAIL パターンと修正手順

### 1) `docs/DESIGN.md` がない

- 症状: `missing required file: docs/DESIGN.md`
- 修正:
  1. `docs/DESIGN.md` を作成
  2. 公式 8 セクション順序を満たす
  3. `colors.primary` と typography token を front matter に追加

### 2) lint exit 1（仕様違反）

- 症状: section order / required token / missing section 系の error
- 修正:
  1. 見出し順序を公式 8 に合わせる
  2. `Shapes` を空にしない（rounded/radius/pill ルールを明示）
  3. HELIX 独自内容は `### HELIX Extension: ...` に移す
  4. 再実行して exit `0` を確認

### 3) ツール実行失敗（fail-close）

- 症状: `npx command not found` / `fetch failed` / 実行時クラッシュ
- 修正:
  1. Node.js / npm / npx の利用可否を確認
  2. ネットワーク・レジストリ到達性を確認
  3. wrapper 単体で `--version` を実行して upstream 応答を確認

## warning / info の読み方

- `[design-md][INFO] warning: ...`:
  - 仕様違反ではないが将来の不整合候補
  - 優先度: 中（次の文書更新時に解消）
- `[design-md][INFO] info: ...`:
  - 補助的な診断情報
  - 優先度: 低（記録のみ）

運用ルール:
- warning/info は gate fail 件数に加算しない
- FAIL 判定は exit code と必須ファイル有無のみで決める

## DB 記録

- `gate_runs.fail_reasons` には既存集計に加えて `design-md-lint` を追記する
- `.helix/gate-checks.yaml` へ埋め込まず、`cli/helix-gate` で専用実装する

## 将来展望（Phase 2/3）

- Phase 2 は L5 `design-md diff` 観測、Phase 3 は L4 `export tailwind` 活用を追加予定。
