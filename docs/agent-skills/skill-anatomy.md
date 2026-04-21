# Skill Anatomy (HELIX 版)

本ドキュメントは `helix-agent-skills` の SKILL.md の構造とフォーマットを定義する。新規スキル作成時や既存スキル理解時の指針として参照すること。

> **Upstream**: [addyosmani/agent-skills/docs/skill-anatomy.md](https://github.com/addyosmani/agent-skills/blob/main/docs/skill-anatomy.md) (MIT)
> 本フォークでは日本語化 + HELIX frontmatter 拡張仕様 + HELIX 9 フェーズ連携を追加。

---

## ファイル配置

全スキルは `skills/` 配下の独立ディレクトリに配置する:

```
skills/
  skill-name/
    SKILL.md           # 必須: スキル定義
    supporting-file.md # 任意: 参照資料 (100 行超時のみ)
```

---

## SKILL.md フォーマット

### Frontmatter (必須)

```yaml
---
name: skill-name-with-hyphens
description: 〇〇を通じてエージェントを導く。△△のときに使う。
helix_layer: [L1, L3]                    # HELIX レイヤ (必須)
helix_gate: [G0.5, G1]                   # 関連ゲート (任意)
codex_role: tl                           # 推奨 Codex ロール (必須)
tier: 1                                  # 優先度 1/2/3 (必須)
upstream: addyosmani/agent-skills        # フォーク元 (任意)
---
```

#### フィールド仕様

| フィールド | 必須 | 値 | 説明 |
|-----------|------|-----|------|
| `name` | ✅ | kebab-case | ディレクトリ名と一致させる |
| `description` | ✅ | 最大 1024 字 | 「何を」「いつ使うか」を日本語で。手順はここには書かない |
| `helix_layer` | ✅ | `[L1-L8]` / `[R0-R4]` / `[S0-S4]` | 配列で複数指定可 |
| `helix_gate` | — | `[G0.5, G1, G1.5, G1R, G2-G7, RG0-RG3]` | 関連ゲート |
| `codex_role` | ✅ | `tl/se/pg/fe/qa/security/dba/devops/docs/research/legacy/perf` | `cli/ROLE_MAP.md` 参照 |
| `tier` | ✅ | `1` / `2` / `3` | 1=HELIX 強化に即効、2=中、3=既存 HELIX と重複 |
| `upstream` | — | `<org>/<repo>` | フォーク元を示す (本家スキルのみ) |

**なぜ重要か**: `helix skill search` が frontmatter を読んで自動推挙する。`helix_layer` と `codex_role` がないと推挙の精度が落ちる。

### 標準セクション

```markdown
# スキルタイトル

## Overview (概要)
このスキルが何をし、なぜ重要かを 1-2 文で。

## When to Use (発火条件)
- 箇条書きで発火条件 (症状、タスク種別)
- 使ってはいけないケース

## Process (手順 / ワークフロー / ステップ)
主要な手順を番号付きで。コード例や ASCII フローチャートを適宜。

## Specific Techniques (任意)
具体的なシナリオ向けの詳細ガイド、コード例、テンプレート、設定例。

## Common Rationalizations (よくある言い訳)
| 言い訳 | 実態 |
|--------|------|
| エージェントがステップをスキップする理由 | なぜその言い訳が誤りか |

## Red Flags (危険信号)
- スキルが無視されているときに現れる行動パターン
- レビュー時に警戒すべき兆候

## Verification (検証)
スキルの工程完了を確認するチェックリスト:
- [ ] 退出条件
- [ ] 成果物エビデンス
```

---

## 各節の目的

### Overview
スキルのエレベーターピッチ。「このスキルは何をし、なぜ従うべきか」に答える。

### When to Use
人間とエージェントがこのスキルを適用すべきか判断するための節。発火条件 (Use when) と除外条件 (NOT for) の両方を書く。

### Process
スキルの核心。エージェントが従うステップバイステップの手順。抽象論でなく**具体的かつ実行可能**に書く。

- **良い例**: 「`npm test` を実行し全テストが PASS することを確認」
- **悪い例**: 「テストが通ることを確認する」

### Common Rationalizations
優れたスキルの最大の特徴。「あとでテスト書きます」「これは単純だから spec 不要」等、エージェントが手順を飛ばす言い訳と、その反論を対にして記述する。

### Red Flags
スキルが破られている観測可能な兆候。コードレビュー / 自己監視で活用する。

### Verification
退出条件。各チェックボックスはエビデンス (テスト出力・ビルド結果・スクリーンショット等) で検証可能であること。

---

## 補助ファイル

以下の場合のみ作成する:
- 参照資料が 100 行を超える (SKILL.md 本体を軽く保つ)
- コードツール / スクリプトが必要
- チェックリストが長く別ファイル化する価値がある

50 行以下のパターン・原則はインラインに書く。

---

## 執筆原則

1. **手順 > 知識**: スキルはワークフロー、リファレンスドキュメントではない
2. **具体 > 抽象**: 「`npm test` 実行」が「テストを通す」に勝る
3. **エビデンス > 前提**: 検証項目は必ず証拠を要求する
4. **反 rationalization**: スキップ可能な手順には必ず反論を添える
5. **progressive disclosure**: SKILL.md は入口、補助は必要時のみ読み込む
6. **トークン意識**: 削っても挙動が変わらない節は削る

---

## 命名規約

- スキルディレクトリ: `lowercase-hyphen-separated`
- スキルファイル: `SKILL.md` (常に大文字)
- 補助ファイル: `lowercase-hyphen-separated.md`
- References: `references/` 配下に集約 (スキルディレクトリ内には置かない)

---

## スキル間参照

他スキルを名前で参照する:

```markdown
テスト作成時は `test-driven-development` スキルに従う。
ビルドが壊れたら `debugging-and-error-recovery` スキルを使う。
```

スキル間で内容を複製しない。参照とリンクで結合すること。

---

## HELIX 連携チェックリスト

新規 SKILL.md を追加・既存 SKILL.md を改訂する際:

- [ ] frontmatter に `helix_layer` / `codex_role` / `tier` を記入
- [ ] description が日本語で、「〇〇のときに使う」形式
- [ ] Rationalizations / Red Flags / Verification の 3 節を備える
- [ ] 100 行超の補助は別ファイル化
- [ ] `helix skill catalog rebuild` で認識されることを確認 (HELIX 本体統合後)
- [ ] 上流 (addyosmani/agent-skills) 由来の場合は `upstream` フィールド記入
