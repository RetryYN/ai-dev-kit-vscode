# helix discovery 判定管理ガイド

`helix discovery` は要件や実現性が未確定なものを、仮説・PoC・検証スクリプト・判定で管理する検証駆動モードです。Forward HELIX に入る前の不確実性を潰すために使います。

> `helix scrum` は 1 release の backward compat alias です。runtime state は Stage 1 では引き続き `.helix/scrum/` を使用します。

## 基本フロー

```bash
helix discovery init
helix discovery backlog add --id H001 --title "仮説" --question "何を検証するか" --acceptance "成功条件"
helix discovery plan --goal "検証ゴール" --hypotheses H001
helix discovery poc --hypothesis H001
helix discovery verify
helix discovery decide --hypothesis H001 --confirmed --strict-promote
helix discovery review
```

## サブコマンド

| サブコマンド | 役割 |
|---|---|
| `init` | Discovery モード初期化 |
| `backlog` | 仮説 backlog 管理 |
| `local` | Forward 内 local loop 管理 |
| `plan` | Sprint 計画 |
| `poc` | PoC 実装委譲 |
| `verify` | 検証スクリプト実行 |
| `decide` | confirmed / rejected / pivot 判定 |
| `review` | sprint review |
| `status` | 現在状態表示 |
| `trigger` | 差し込み trigger 管理 |
| `web-search` | 参考事例メモ保存 |
| `acceptance-design` | 受入条件テンプレ生成 |

## 代表例

```bash
helix discovery local init --layer L4 --hypothesis "wrap smoke" --acceptance "local loop created"
helix discovery trigger detect --scan docs/features --save
helix discovery web-search --query "test" --hypothesis H001
helix discovery acceptance-design --hypothesis H001
```

## 注意

- `confirmed` と `review` は fail-closed です。
- `HELIX_SUPPRESS_LEGACY_WARN=1` を指定すると `helix scrum` alias の warning を抑止できます。
- Stage 1 では runtime state path を変更しません。`.helix/discovery/` への移行は後続 PLAN scope です。
