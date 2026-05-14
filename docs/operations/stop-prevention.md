# 停滞防止システム運用ガイド (V2.2)

## 1. 背景

V2.2 では「PM が一時不在」「会話が長期化したまま意思決定が止まる」「AskUserQuestion が乱発される」という運用上の停滞を防ぐため、技術実装とルールでの二層制御を導入した。

- 人が居ない時間帯に自動化された作業が過信で進みすぎることを防止
- 本質的に destructive な変更を先送りし、失敗時の巻き戻しコストを抑止
- 事前審査がない Ask を減らし、TL 相談済みの実行判断に標準化
- コマンド操作を機械検証で先に通し、CI 的に「何をしてよいか」を明示

## 2. 3-layer 運用構造

### 2.1 Layer 1: CLAUDE.md のルール化

V2.2 では CLAUDE.md に、以下を明示的に追加している。

1. **Ask 前必須 TL 相談 (v2.2)**

   - `AskUserQuestion` 前提条件として、まず tl-advisor で一次判断を通す
   - 例外許容は明示的な事前合意のみ
   - PreToolUse hook と連動し、未通過時は warning を出し実行前確認

2. **Push/PR/Merge 6 ゲート (v2.2)**

   - `helix push/pr --gate` 実行時は以下 6 ゲートを機械検証
   - 一部ゲートは手動補足（manual-confirm）必須
   - `auto-allow` は「自動実行できる安全領域」のみ付与

### 2.2 Layer 2: `helix push --gate` / `helix pr --gate`

- 機能:
  - テスト・カタログ・secret・FF・attrs・non-destructive を事前に検証
  - 不合格時は Push / PR 作成を停止
  - `--execute` で自動実行を試みるかを制御
- 効果:
  - ローカル判断による見落としを減らし、CI 的に同じ判定を再現
  - 人のレビュー不足時にも品質最小線を確保

### 2.3 Layer 3: PreToolUse hook

- AskUserQuestion が呼ばれる際、`tl-advisor` 通過を確認
- 条件:
  - 警告表示（warning）を表示し、実行の可否を再確認
  - destructive / 非自動許可領域は明示フラグなしでは進めない
- 結果:
  - 乱発を抑え、ask-based な詰まりを可視化

## 3. 6 ゲート詳細

| ゲート名 | 目的 | 典型 fail ケース | 対処 |
|---|---|---|---|
| G-tests | 既存回帰・新規テスト不足 | pytest 失敗、未更新テスト | 実装最小変更→再テスト |
| G-catalog | command catalog 同期 | docs/commands と実コマンド不整合 | 命令名/引数を catalog 追従 |
| G-secret | シークレット安全性 | secret-like 文字列のコミット混入 | 値を環境変数化し、除外ルール更新 |
| G-ff | functional_freeze | freeze 条件不足 | `helix gate --subgate functional_freeze` の要件追加 |
| G-attr | 属性・監査属性 | coauthor / メタ未整備 | メタ更新とレビュー同席 |
| G-nondestructive | 破壊性防止 | `rm -rf` 系・DB 破壊系を含む操作 | manual-confirm または分割実行 |

## 4. 利用コマンド

### 4.1 Push / PR の標準

```bash
helix push --gate --execute
```

```bash
helix pr --gate
```

```bash
helix pr --gate --auto-merge
```

### 4.2 自動許可と manual-confirm

`helix` は `--gate` 実行時に可能な限り機械化し、`manual-confirm` が必要なケースは明示する。

- destructive 操作（破壊的ファイル操作、外部への直接破棄）
- secrets 取扱いや環境変数移行
- 不明点のある運用外手順

## 5. TL 相談すべき例 と Ask 許可例

### 5.1 相談すべき例（Ask禁止）

1. 実装方針が 2 方針以上あり、どちらを採用するか未確定
2. `G-secret` / `G-nondestructive` で fail
3. 新規依存追加、CLI 挙動の大規模変更
4. 認証・認可・PII 処理に関係

### 5.2 Ask が許可される例

1. 既知のコマンド呼び出し確認
2. typo やログ出力文字列など低リスクな確認
3. 既に TL 相談済みタスクの再現確認

## 6. destructive operation 例外

以下は原則、`helix` が提示しても必ず人の explicit confirm が必要。

- 本番 DB 破壊・データ再生成系
- ファイル一斉削除（`git clean` / `rm -rf` / 競合再実行）
- サービス停止・設定値変更（CI/クラウド/Secrets を含む）
- 外部 API の突発 write アクション

## 7. 実行例（運用）

### 7.1 通常の Push

```text
ユーザー: 実装完了。テストは一通り通っているはず
エージェント: helix push --gate --execute
結果: G-tests pass, G-catalog pass, G-secret pass, G-ff pass, G-attr pass, G-nondestructive pass
```

### 7.2 PR 作成 + 併走

```bash
helix pr --gate --title "docs: add v2 operation docs"
```

失敗があればコメント化されるため、原因を解消してから再実行。

### 7.3 auto-merge

```bash
helix pr --gate --auto-merge --body "v2 operations docs"
```

auto-merge は前提ゲートが全 pass である場合のみ進行する。

## 8. 参照

- [docs/commands/push.md](../commands/push.md)
- [docs/commands/pr.md](../commands/pr.md)

## 9. コマンド例（CLI 出力）

```bash
$ helix push --gate --execute
> running gate: G-tests
> running gate: G-catalog
> running gate: G-secret
> running gate: G-ff
> running gate: G-attr
> running gate: G-nondestructive
pass: all gates
push: auto-allow executed
```

```bash
$ helix pr --gate --auto-merge
> gate result: PASS all(6)
> pre-merge check: all clear
> creating pull request...
> pull request created: #123
> auto-merge: enabled
```

## 10. 運用メモ

1. gate は「ボトルネック解消」ではなく「失敗予防」を目的とする
2. warn のみで止まるケースは、再現手順・実行根拠を明文化
3. TL 相談は例外なく記録し、運用ログとして残す
4. Ask は不要に増えやすい箇所ほど、先に `--gate` 実行可能性を確認

