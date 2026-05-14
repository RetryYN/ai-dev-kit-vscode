# HELIX V2 Phase 2 運用インデックスガイド

本書は V2 Phase 2 拡張として追加された運用レールを 1 枚で把握できるようにした索引です。  
対象は、以下の 4 領域です。

- 停滞防止システム
- PdM Innovation ワークフロー
- PMO 9 ロール
- V-model 強化（`functional_freeze`）

## 1. V2 Phase 2 で増えた機能サマリ

### 1.1 V-model 強化

- `helix vmodel validate / show / list` による設計セマンティクス参照
- `helix gate --subgate functional_freeze --drive <DRIVE>` による機能フリーズ監査
- `fullstack` / `be` / `fe` / `db` の 4 ドライブを前提とした設計進捗チェック

### 1.2 停滞防止（V2.2）

- CLAUDE.md に codex 側の `Ask` フロー制約を追加
- `helix push --gate` / `helix pr --gate` の 6 ゲート自動検証を実装運用化
- PreToolUse hook による AskUserQuestion ガード（TL 承認の有無）

### 1.3 PdM Innovation

- `helix innovation` 系 subcommand を通じた企画レポート生成
- PdM 3 role の並列実行
- `innovation-output.yaml.template` を起点に L1 入力へ接続

### 1.4 PMO 9 ロール

- 企画前評価（pdm-*）と意思決定支援
- docs / project / HELIX 内探索の分担化
- `pmo-tech-*` と `pmo-*` の明示的な呼び分け

## 2. 機能別入口一覧（リンク）

### 2.1 全体

- [stop-prevention.md](./stop-prevention.md)
- [pdm-innovation-workflow.md](./pdm-innovation-workflow.md)
- [pmo-roster.md](./pmo-roster.md)

### 2.2 関連コマンド

- [docs/commands/push.md](../commands/push.md)
- [docs/commands/pr.md](../commands/pr.md)
- [docs/commands/innovation.md](../commands/innovation.md)
- [docs/commands/vmodel.md](../commands/vmodel.md)
- [docs/commands/gate.md](../commands/gate.md)

### 2.3 連携ドキュメント

- [CLAUDE.md](../../CLAUDE.md)
- [cli/templates/plan/innovation-output.yaml.template](../../cli/templates/plan/innovation-output.yaml.template)
- [cli/templates/teams/innovation-team.yaml](../../cli/templates/teams/innovation-team.yaml)
- [skills/advanced/tech-innovation/SKILL.md](../../skills/advanced/tech-innovation/SKILL.md)
- [skills/advanced/marketing-innovation/SKILL.md](../../skills/advanced/marketing-innovation/SKILL.md)
- [skills/advanced/innovation-mgr/SKILL.md](../../skills/advanced/innovation-mgr/SKILL.md)

## 3. 典型 workflow（新規企画 → G0.5 → L1）

以下は新規企画を前提にした標準導線です。

```text
企画受領
  → helix innovation tech / marketing
    → parallel 出力
      → helix innovation synthesize
        → pdm-innovation-manager 統合
          → g0_5_mapping で L1 trace を作成
            → helix gate --subgate functional_freeze
              → helix plan
                → L1 作成
```

### 3.1 目標

- 新規企画の意思決定を `技術/マーケ / 事業施策` で切り分ける
- G0.5 で trace が未完成な状態を防ぐ
- L1 に渡す FR / NFR / AC の粒度を担保する
- 停滞ポイントを `helix push/pr` の 6 ゲート前に潰す

### 3.2 完了条件

1. `innovation-output` が YAML スキーマに沿う
2. G0.5 mapping の trace が 100% カバー
3. `functional_freeze` が主要 drive で pass
4. 6 ゲート前提条件に対する destructive / secret / catalog リスクが解消

## 4. 主要コマンド早見

### 4.1 企画系・設計系

- V2 強化: `helix vmodel list` / `helix vmodel show`
- 機能フリーズ: `helix gate --subgate functional_freeze --plan-id <PLAN> --drive <drive>`
- PdM系導線: `helix innovation team|tech|marketing|synthesize`

### 4.2 停滞防止系

- Push: `helix push --gate --execute`
- PR 作成: `helix pr --gate`
- 自動 merge: `helix pr --gate --auto-merge`

### 4.3 例: vmodel + gate + push 連結

```bash
helix vmodel validate
helix vmodel list --drive be
helix gate --subgate functional_freeze --plan-id PLAN-001 --drive be --size M
helix push --gate --execute
```

```bash
helix innovation team --task "新規企画: X の方向性"
helix pr --gate --auto-merge
```

## 5. 停滞防止と意思決定分担の関係

```text
AskUserQuestion
  └─ 必ず tl-advisor で pre-check した上で再評価
      └─ 例外: 安全監査 / 破壊的変更 / manual-confirm
```

```text
PR / Push
  ├─ gate 機械検証 6 件
  └─ 結果 PASS 後のみ実行
```

```text
企画
  ├─ PdM tech/marketing parallel
  ├─ pmo-* 補助
  └─ pdm-manager 統合
```

## 6. 6 ゲート運用導線（停滞防止）

`helix push / pr` の gate は以下 6 種を対象にします。

1. G-tests
2. G-catalog
3. G-secret
4. G-ff
5. G-attr
6. G-nondestructive

詳細は [stop-prevention.md](./stop-prevention.md) を参照してください。

## 7. ドライブ別運用チェック

### 7.1 `be`

- 既存 API / CLI 実装の設計と機能の整合
- `functional_freeze` は `plan` レコードと `pair` の一致を重点確認

### 7.2 `fe`

- `design/test` ペア監査と `functional_freeze` 前提を明示
- 依存が大きい導線では `sprint` と併用して段階監査

### 7.3 `db`

- スキーマ・移行設計の見直しを `functional_freeze` に合わせて再点検
- `L3` / `L4` の設計証跡とのズレがないことを確認

### 7.4 `fullstack`

- `architecture→detailed→functional` 連鎖の整合
- 重要ペアの `waived` 件はレビュー根拠を明記

## 8. トラブル時の初動

1. **G-nondestructive fail**
   - diff 追加行を再確認
   - `manual-confirm` 付き実行に切替
2. **G-catalog fail**
   - help/docs の同期確認（`helix commands` / command catalog）
3. **G-attr fail**
   - Co-Authored-By の commit 監査
4. **functional_freeze missing**
   - `helix vmodel validate` + `sprint` 進捗補完
5. **pmo 分担不足**
   - `pmo-*` 実行順を見直し、`parallel_stage` を再起動

## 9. 各ドキュメントへの導線

- 停滞防止全体: [stop-prevention.md](./stop-prevention.md)
- PdM Innovation: [pdm-innovation-workflow.md](./pdm-innovation-workflow.md)
- PMO 9ロール: [pmo-roster.md](./pmo-roster.md)
- 実行時参照: [docs/commands/push.md](../commands/push.md), [docs/commands/pr.md](../commands/pr.md), [docs/commands/innovation.md](../commands/innovation.md), [docs/commands/vmodel.md](../commands/vmodel.md), [docs/commands/gate.md](../commands/gate.md)

## 10. 継続運用メモ

1. 運用変更時は `docs/operations` 2次版ではなく本文を先に更新
2. `helix commands` 失敗を起点に `G-catalog` 仕様との同期待ち
3. 新ロール追加は `README のロール × モデル` と `pmo-roster` へ同時反映
4. `task plan` に対応する新規運用なら、`.helix/task-plan.yaml` と `task-id` を明記
