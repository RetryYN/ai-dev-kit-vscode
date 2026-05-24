# HELIX 取り込みメモ — review-stage-routing

前回作成した独立版（6段階コードレビュー スキル／ワークフロー）を、ai-dev-kit-vscode（HELIX）の
実際の規約・既存資産に合わせて再パッケージしたもの。新機能や新ゲートは追加していない。

## 何を変えたか（独立版 → HELIX 準拠版）

| 観点 | 独立版（前回） | HELIX 準拠版（今回） |
|---|---|---|
| 位置づけ | 独立した6段階レビュースキル | 既存 code-review の上に被せる「分業境界レイヤ」 |
| 観点定義 | 6段階内に観点を内包 | common/code-review（5軸+Google）に委譲、重複排除 |
| 判定ラベル | Approve可/条件付き/保留 | LGTM / LGTM with nits / Changes requested に統一 |
| AI比率 | 段階別の目安 | HELIX ロール（PM/TL/SE/PE/QA/security）への実割当に変換 |
| サブエージェント | 独自 logic/design/security-reviewer | 既存 code-reviewer / security-audit を再利用 |
| スキル形式 | name+description のみ | metadata.helix_layer/triggers/verification + compatibility + 責務分離 |
| ワークフロー形式 | 自由形式 md | doc_id/status/owner/parent/integration_target フロントマター |
| reviewコマンド | 独自 review_report.py | 既存 helix review（codex ラッパー）の出力を段階分離 |
| 逆説ルール | 独立スキル内 | 維持（本レイヤの中核として残す。PLAN-NNN 照合に接続） |

要点: 6段階の「観点」は HELIX に既存（重複するので捨てた）。残した固有価値は
**段階→ロール分業**と**逆説ルール**と**ADR 降下**の3つだけ。

## 既存資産との衝突チェック

- `skills/common/code-review`（観点・判定の正本）→ 参照のみ。再定義なし
- `.claude/agents/code-reviewer`（5軸）→ 一次評価器として再利用
- `helix review` = codex review ラッパー（観点なし）→ 出力を段階分離する被せ方
- `skills/workflow/adversarial-review`（G2）→ Stage 5/6 高リスク時にエスカレーション
- `skills/workflow/{security,threat-model,verification,quality-lv5}` → 各 Stage から参照
- ゲート G2（設計凍結）/ G4（実装凍結）→ 既存ゲートに乗せる。新ゲートなし

## ファイルと配置先

```
helix-integration/
├── skills/workflow/review-stage-routing/SKILL.md
│     → リポジトリの skills/workflow/review-stage-routing/ にコピー
└── HELIX-workflows/helix-process/review-stage-routing.md
      → リポジトリの HELIX-workflows/helix-process/ にコピー
```

## 取り込み手順

1. 2ファイルを上記の配置先にコピーする。
2. `skills/SKILL_MAP.md` の workflow カテゴリに `review-stage-routing` を1行追記する
   （責務: 6段階×ロール分業境界。観点は common/code-review に委譲、と明記）。
3. `skills/common/code-review/SKILL.md` の「責務分離」記述に、
   本スキルへの参照（段階→ロール分業は review-stage-routing 側）を1行追記する。
4. `helix skill` のカタログ再構築フック（posttooluse-skill-catalog-rebuild.sh）が
   走ることを確認する。
5. 必要なら `HELIX-process-L0-L14.md` の L4/G4 記述から本ワークフローへリンクを張る。

## 取り込み前に PM 判断が要る点

- 本レイヤを **helix review に自動発火させるか**（Sprint .2/.5 連動）、PM 任意発火に留めるか。
  自動化するなら helix-review の実装に「段階分離」ステップを足す改修が必要になるため、
  まず任意発火で運用し、効果を見てから自動化するのが安全。
- 既存 code-reviewer の5軸と6段階の対応表（本スキル記載）で運用上の齟齬が出ないか、
  最初の数 PR でレビューして調整する。

## 残した独立版の扱い

独立版（汎用）はキット内の `../standalone/code-review-skill/` と
`../standalone/CODE_REVIEW_WORKFLOW.md` に同梱。HELIX 外の汎用環境
（素の Claude Code / 他プロジェクト）向けとして使える。HELIX 内では本準拠版（helix-integration/）を使う。
2系統の関係はキット直下の `../README.md` を参照。
