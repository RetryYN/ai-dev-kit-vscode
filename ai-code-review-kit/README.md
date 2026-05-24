# AI Code Review Kit

コードレビューを6段階（Format / Lint / Style / Logic / Design / Architecture）に分け、
AIと人間（および各ロール）の境界を「問題の性質」で切り分けるレビューキット。
出典の6段階モデルを、2026年5月時点の最新ツール動向で情報補強したもの。

2系統を同梱している。**目的に応じてどちらか一方を使う**（両方を同時に入れる必要はない）。

```
ai-code-review-kit/
├── README.md                ← このファイル（2系統の地図）
├── standalone/              ← 汎用版：素の Claude Code / 他プロジェクト向け
│   ├── CODE_REVIEW_WORKFLOW.md
│   └── code-review-skill/
└── helix-integration/       ← HELIX準拠版：ai-dev-kit-vscode (HELIX) 取り込み用
    ├── INTEGRATION-NOTES.md
    ├── skills/workflow/review-stage-routing/SKILL.md
    └── HELIX-workflows/helix-process/review-stage-routing.md
```

## どちらを使うか

| | standalone（汎用版） | helix-integration（HELIX準拠版） |
|---|---|---|
| 対象 | 既存レビュー体系を持たない環境 | ai-dev-kit-vscode (HELIX) |
| 観点定義 | キット内に内包（6段階＋ベンチマーク） | 既存 common/code-review に委譲 |
| 提供物 | スキル・サブエージェント・pre-commit・集計スクリプト一式 | 段階×ロール分業の被せレイヤ2ファイル |
| 判定ラベル | Approve可 / 条件付き / 保留 | LGTM / LGTM with nits / Changes requested |
| ロール割当 | AI比率の目安 | PM/TL/SE/PE/QA/security の実割当 |

判定ラベルが2系統で異なるのは**意図的**。汎用版は単体で完結する独自ラベル、
HELIX版は既存 `common/code-review`（Google eng-practices）に揃えて重複と矛盾を避けている。

## 2系統の関係（整合性）

両系統は同じ6段階モデルと同じ核心原則を共有する。差異は「観点を内包するか、既存に委譲するか」だけ。

共有する核心原則:
- 6段階は「正解の一意性」で切る。一意でなくなるほどAI比率が下がり上位の責任が上がる。
- **逆説ルール**: AIが指摘した箇所はAIに任せ、AIが指摘しなかった箇所こそ人間（上位ロール）が念入りに見る。
- **ADR降下**: ADR化するとArchitecture判断の一部がDesign/Logicに降り、AI委譲範囲が広がる。
- AI比率（60%等）は目安であって定量ゲートではない。AIのゼロ指摘をApproveの根拠にしない。

HELIX版は汎用版から「6段階のうち既存にない固有価値（段階→ロール分業・逆説ルール・ADR降下）」だけを抽出し、
観点と判定は HELIX 既存資産に委譲する形に再パッケージしたもの。
変換の詳細は `helix-integration/INTEGRATION-NOTES.md` の差分表を参照。

## クイックスタート

### standalone を使う場合

1. `standalone/code-review-skill/` をスキルとして登録（`SKILL.md` 起点）。
2. Stage 1-2 を固める: `standalone/code-review-skill/scripts/precommit-gate.sh` を `.git/hooks/pre-commit` に。
3. 詳細は `standalone/code-review-skill/README.md` と `standalone/CODE_REVIEW_WORKFLOW.md`。

### helix-integration を使う場合

1. `helix-integration/skills/...` と `helix-integration/HELIX-workflows/...` をリポジトリの同名パスにコピー。
2. 取り込み手順・既存資産との衝突チェック・PM判断事項は `helix-integration/INTEGRATION-NOTES.md`。

## 出典と情報補強

6段階モデルは Zenn 記事「コードレビューを6段階にしたら、AIと人間の分業が見えた」を基に、
2026年5月時点のAIレビューツール動向（CodeRabbit / GitHub Copilot Code Review / Greptile、
Claude Code の公式 Code Review・/ultrareview・自作サブエージェントの3経路）で補強している。
ベンチマーク数値はツール世代で陳腐化が早いため、四半期ごとの見直しを前提とする。
