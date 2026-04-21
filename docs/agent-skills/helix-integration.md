# HELIX 本体との接続ガイド

> **対象**: HELIX フレームワーク (`~/ai-dev-kit-vscode`) を利用する開発者が、本フォーク `helix-agent-skills` をプロジェクトから呼び出すための手順。

## 接続方式の選択肢

| 方式 | 利点 | 欠点 | 適用場面 |
|------|------|------|---------|
| **A. submodule** | HELIX 本体リポジトリと一体管理、バージョン固定可 | 本体 git 操作の複雑化 | HELIX 本体も開発中の場合 |
| **B. symlink** | 即時反映、軽量 | ローカル限定、他環境で再現性なし | 単一マシン / 個人開発 |
| **C. clone + PATH** | シンプル、独立 | 手動更新が必要 | プラグイン運用 |
| **D. Claude Code plugin** | `/plugin install` で完結 | GitHub push 後のみ利用可 | 公開後の推奨方式 |

---

## 方式 A: submodule (推奨)

HELIX 本体のリポジトリに `vendor/helix-agent-skills` として追加する。

### 追加手順

```bash
cd ~/ai-dev-kit-vscode
git submodule add git@github.com:<YOUR_GITHUB_USER>/helix-agent-skills.git vendor/helix-agent-skills
git submodule update --init --recursive
```

### 更新手順

```bash
cd ~/ai-dev-kit-vscode/vendor/helix-agent-skills
git pull origin helix-integration
cd ~/ai-dev-kit-vscode
git add vendor/helix-agent-skills
git commit -m "chore(skills): helix-agent-skills を <commit-hash> に更新"
```

---

## 方式 B: symlink (開発時)

```bash
cd ~/ai-dev-kit-vscode
mkdir -p vendor
ln -s /home/tenni/agent-skills-helix vendor/helix-agent-skills
```

HELIX 本体のリポジトリで追跡しない (gitignore 推奨):

```bash
echo "vendor/helix-agent-skills" >> ~/ai-dev-kit-vscode/.gitignore
```

---

## 方式 D: Claude Code plugin (公開後)

GitHub に push した後、Claude Code から直接インストール:

```
/plugin marketplace add <YOUR_GITHUB_USER>/helix-agent-skills
/plugin install helix-agent-skills@<YOUR_GITHUB_USER>-helix-agent-skills
```

---

## helix skill コマンドからの認識

HELIX 本体の `helix skill search / list` は `~/ai-dev-kit-vscode/skills/` を skills_root として読む。フォーク側のスキルを認識させるには以下の 2 択:

### 案 1: 本体 skill_catalog.py 拡張 (正攻法)

本体の `cli/lib/skill_catalog.py` に「外部 skills root」対応を追加する PR を発行。
- パス構造の違い (`skills/<category>/<name>/SKILL.md` vs `skills/<name>/SKILL.md`) を吸収
- frontmatter 形式の違い (`metadata.helix_layer` vs `helix_layer`) を両対応
- 環境変数 `HELIX_EXTERNAL_SKILLS_ROOTS` で複数指定可能に

### 案 2: 軽量ラッパースクリプト (短期対応)

フォーク内に CLI スクリプト `cli/helix-skill-search` を追加し、手動検索する。
```bash
cd ~/agent-skills-helix
grep -l "system-design" skills/**/SKILL.md
```

現状は**案 2 を暫定運用**し、PR 経由で案 1 を本体に取り込むのが推奨ルート。

---

## セッション開始 hook の動作

`hooks/session-start.sh` は以下を自動実行:

1. `using-agent-skills` メタスキルを Claude Code セッションに注入
2. HELIX 本体を検出 (`$HELIX_HOME` または `~/ai-dev-kit-vscode`)
3. 検出時に HELIX CLI コマンドリストをメッセージに追加
4. `helix skill search '<task>'` の使用方法を案内

---

## スキル呼び出しの典型フロー

### Claude Code セッションで直接使う

1. セッション開始時に `hooks/session-start.sh` が発火
2. ユーザー指示 → Claude が使用すべきスキルを `using-agent-skills` メタスキルで発見
3. 該当スキルの SKILL.md を読み、手順に従う

### HELIX CLI から Codex ロール委譲と組み合わせる

```bash
# 例: 仕様書作成を tl ロールに委譲、spec-driven-development スキルを参照させる
helix codex --role tl --task "
## 参照スキル
vendor/helix-agent-skills/skills/spec-driven-development/SKILL.md に従い、以下の仕様書を作成:
...
"
```

### Claude Code の slash command から起動

| Command | 連動スキル | HELIX フェーズ |
|---------|-----------|---------------|
| `/spec` | spec-driven-development | L1 / L3 |
| `/plan` | planning-and-task-breakdown | L1-L3 |
| `/build` | incremental-implementation + test-driven-development | L4 |
| `/test` | test-driven-development + browser-testing-with-devtools | L4.3 / L6 |
| `/review` | code-review-and-quality + adversarial-review | G2 / G4 / G6 |
| `/code-simplify` | code-simplification | L4 / L6 |
| `/ship` | shipping-and-launch + fan-out (reviewer/test/security) | L7 |

各コマンドの `## HELIX 連携` セクションに具体的な `helix` CLI コマンドが明記されている。

---

## バージョン管理

- 本フォークのバージョン: `.claude-plugin/plugin.json` の `version` フィールド
- Upstream 追従: `git remote add upstream https://github.com/addyosmani/agent-skills.git` → `git fetch upstream` → マージは **手動で選択的に**
  - 独自カスタマイズ (日本語化 / HELIX frontmatter) との競合は手動解消

---

## ロードマップ

- [ ] 本体 `cli/lib/skill_catalog.py` への外部 skills root 対応 PR
- [ ] `helix skill search` から fork 側 SKILL.md を自動提案
- [ ] バージョン同期ワークフロー (CI で upstream drift 検出)
- [ ] サブモジュール更新の自動 PR (Renovate / Dependabot 類)
