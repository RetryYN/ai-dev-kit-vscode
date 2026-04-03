# helix plan コマンドガイド

## フロー

`draft -> review -> finalize`

```bash
helix plan draft --title "ユーザー認証 API"
helix plan review --id PLAN-001
helix plan finalize --id PLAN-001
```

補助コマンド:

```bash
helix plan list
helix plan status --id PLAN-001
```

## TL レビューの意味

`review` では TL 観点で以下を判定する。

- 技術妥当性
- リスク（API/DB/認証/外部API/移行/セキュリティ）
- 実装可能性と欠落

判定は `approve` または `needs-attention`。

## なぜ提案前レビューが必要か

- 設計未凍結のまま実装に入るのを防ぐ
- 後戻りコスト（G3 以降のやり直し）を減らす
- 仕様・契約の抜け漏れを先に潰す

`finalize` は `approve` 済みプランのみ許可される。
