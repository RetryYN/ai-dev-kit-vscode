# D-ACC: 受入条件 — helix-budget + auto-thinking Phase B

**Feature**: helix-budget-autothinking
**Verification**: G6 RC ゲート / L8 受入で全件 pass 必須

---

## 0. 判定基準

各受入条件 (AC-*) には次の 3 要素を含む:
- **シナリオ**: いつ / 誰が / 何をしたとき発火するか
- **期待結果**: 具体的な出力・状態 (grep 可能な形式で記述)
- **検証方法**: bats / unit / 手動のいずれかで自動化

合否判定:
- G4: AC-A/B/D/E/F の自動検証項目すべて pass
- G6: AC-A〜G + AC-Q 全 pass
- L8: AC-U は 1 週間運用後に判定 (G7 と連動)

---

## AC-A: 消費取得 (FR-A)

| ID | シナリオ | 期待結果 | 検証方法 |
|----|---------|---------|----------|
| AC-A1 | ユーザーが `helix budget status` を叩く | Claude / Codex 両側の消費 % が stdout に表示される | bats: `helix budget status \| grep -E 'Claude.*%.*Codex.*%'` |
| AC-A2 | ccusage 未インストール環境で `helix budget status` を叩く | JSONL フォールバックで非ゼロ % が出る | bats: `PATH=/tmp/empty helix budget status` |
| AC-A3 | Codex state.db ロック中に呼ぶ | エラーにならず前回キャッシュ値を返す | bats: lock simulation |

## AC-B: ステータス表示 (FR-B)

| ID | 受入条件 | 検証方法 |
|----|---------|----------|
| AC-B1 | `--json` で machine-parseable JSON 出力 | `helix budget status --json | jq .claude.weekly_usage` |
| AC-B2 | `--breakdown` でモデル別消費が表示される | `helix budget status --breakdown | grep -E '5.3\|5.4\|spark'` |
| AC-B3 | 応答時間 < 2 秒 (キャッシュあり) / < 5 秒 (コールド) | `time helix budget status` |

## AC-C: Hook 統合 (FR-C)

| ID | 受入条件 | 検証方法 |
|----|---------|----------|
| AC-C1 | session-start hook が残量ワンライナーを表示する | モック session 起動テスト |
| AC-C2 | 残 < 20% で警告メッセージが出る (exit 0 non-blocking) | 残量 mock 値で発火確認 |
| AC-C3 | `helix init` が既存 settings.json を壊さず hook 追加 | pre/post settings.json の diff で検証 |

## AC-D: Effort 自動判定 (FR-D)

| ID | 受入条件 | 検証方法 |
|----|---------|----------|
| AC-D1 | S タスク (files=1, lines=20) + 実装系 → effort=low/medium 推定 | bats: `helix budget classify --size S --task "typo 修正"` → low |
| AC-D2 | L タスク (files=10+, API+DB 変更) + 設計系 → effort=high/xhigh 推定 | bats: 設計タスクで high 返却 |
| AC-D3 | `--auto-thinking` で helix-codex 実際の CLI 呼び出しが thinking level を上書きする | tool wrapper 内で --thinking 引数を検証 |
| AC-D4 | xhigh + S size で "分割推奨" 警告が出る | bats: 小タスク + xhigh で stderr に分割推奨 |

## AC-E: モデル降格提案 (FR-E)

| ID | 受入条件 | 検証方法 |
|----|---------|----------|
| AC-E1 | Spark 残 < 10% 状態で `helix-codex --role pg` 実行 → 5.4-mini 降格提案 | mock 残量で発火確認 |
| AC-E2 | 5.3 残 < 10% + M サイズ + 雑プロンプト → 5.4 昇格提案 | mock + task text 解析 |
| AC-E3 | 5.4 は原則 hold、降格提案を出さない | bats で 5.4 時は降格 skip |
| AC-E4 | `--yes` で自動適用 / 対話なしで続行 | stdin 閉じた環境で pass |

## AC-F: 統合 + 学習 (FR-F)

| ID | 受入条件 | 検証方法 |
|----|---------|----------|
| AC-F1 | タスク完了後 `skill_usage` に実効 thinking + timeout + 消費量が記録される | `sqlite3 .helix/helix.db "SELECT effort_used,timeout FROM skill_usage"` |
| AC-F2 | `helix log report budget` で週次傾向が表示される | 3 週分のデータで aggregation 動作 |
| AC-F3 | 枯渇検知時に `observed-limits.json` が更新される | 枯渇 simulation 後に JSON キーが増える |
| AC-F4 | ミスマッチ率 (推定 effort ≠ 実効 effort) を report で確認できる | `helix log report budget --accuracy` |

## AC-G: CLI (FR-G)

| ID | 受入条件 |
|----|---------|
| AC-G1 | `helix budget --help` で status / forecast / classify / simulate サブコマンドが表示 |
| AC-G2 | `helix-codex --help` に `--auto-thinking` が追加されている |
| AC-G3 | `helix-skill use --help` に `--auto-thinking` が追加されている |

## AC-Q: 品質 (横断)

| ID | 受入条件 |
|----|---------|
| AC-Q1 | `helix test` 全 PASS (既存 453 + 新規 20-30 = 473-483) |
| AC-Q2 | `helix gate G4` pass (fail-close) |
| AC-Q3 | `helix gate G6` pass |
| AC-Q4 | `security-audit` agent レビューで Critical / High 指摘ゼロ |
| AC-Q5 | 既存 helix-codex / helix-skill / helix-gate が新フラグ無しで従来通り動作 |

## AC-U: ユーザー検証 (L8)

| ID | 受入条件 |
|----|---------|
| AC-U1 | `helix budget status` 出力を見て「残量が一目で分かる」と判定 |
| AC-U2 | 1 週間実運用で枠切れ事故ゼロ (実践編の運用ログで確認) |
| AC-U3 | auto-thinking 有効化で timeout 発生が週あたり 0-1 件に収束 |
| AC-U4 | 降格提案で「提案通り実行して問題なかった」が 80% 以上 |

---

## 合否判定ルール

- G4: AC-A/B/D/E/F の bats / unit 全て pass (= 自動検証項目)
- G6: AC-A〜G + AC-Q 全 pass
- L8: AC-U は 1 週間運用後の振り返りで判定 (G7 安定性ゲートと連動)

AC-U は本実装後のフォローアップ検証。初回リリース時点では AC-A〜Q を合格条件とする。
