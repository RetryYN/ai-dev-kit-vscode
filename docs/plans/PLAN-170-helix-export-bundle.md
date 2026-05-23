---
plan_id: PLAN-170
title: "PLAN-170: helix export bundle (skill / plan / adr archive for offline review)"
layer: L4
kind: impl
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/v2/process/L07-implementation-sprint.md   # ★TODO retrofit pending: L6 機能設計 doc 起草後に差し替え
size: S
drive: be
created: 2026-05-23
owner: PM
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — export 対象資産の棚卸し + MANIFEST.json 仕様確認"
  - role: se
    slot_label: "SE — cli/helix-export 実装 + cli/helix ルーター登録 + bats テスト"
generates:
  - artifact_path: cli/helix-export
    artifact_type: cli_extension
  - artifact_path: cli/tests/test_helix_export.bats
    artifact_type: test
dependencies:
  parent: null
  requires: []
  blocks: []
related_plans:
  - PLAN-169-helix-framework-import-tool
related_docs:
  - docs/commands/index.md
  - docs/architecture/cli-layout.md
---

# PLAN-170: helix export bundle (skill / plan / adr archive for offline review)

> **kind**: impl (helix export CLI 新規実装)
> **layer**: L4
> **drive**: be (CLI 拡張が中心)
> **本 PLAN の役割**: チーム外 review / 監査 / オフライン参照のために、HELIX の skill + PLAN + ADR を 1 archive (.tar.gz) として export する CLI を実装する。bundle には MANIFEST.json (artifact 一覧・hash・summary) と markdown index を含み、外部ツールでも参照しやすい形式にする。WebSearch skip: 汎用 archive / POSIX tar の知識で実装可能な範囲のため。

---

## §0. 背景・問題設定

### 現状の問題

| 問題 | 影響 |
|---|---|
| 監査・外部 review 時に対象資産を個別に送る必要がある | zip / tar をアドホックに作成、再現性なし |
| 共有したい資産の組み合わせが都度変わる | `--include` なしでは全資産を送るしかない |
| 受け取り側が内容を確認する index がない | bundle 内に何が含まれるか不明 |
| hash 検証なしで integrity を確認できない | ファイルが改竄されても気づけない |

### 解決アプローチ

`helix export --output bundle.tar.gz` で archive を生成し、bundle 内に MANIFEST.json を自動生成する。MANIFEST には artifact 一覧・SHA-256 hash・ファイル summary (frontmatter の title / created / status) を含める。

---

## §1. 目的

1. `helix export --output <file>` で skill + PLAN + ADR を archive に bundle する
2. `--include <categories>` で export 対象を選択できる
3. bundle 内に `MANIFEST.json` を自動生成し、artifact 一覧・hash・summary を含める
4. bundle 内に `INDEX.md` を生成し、外部 review ツールで参照可能な markdown 索引を提供する

---

## §2. CLI 仕様

### コマンド形式

```bash
helix export --output bundle.tar.gz \
  [--include skills,plans,adrs] \
  [--format tar.gz|zip]
```

### オプション仕様

| オプション | 説明 | デフォルト |
|---|---|---|
| `--output <file>` | 出力 archive ファイルパス (必須) | — |
| `--include <list>` | カンマ区切りのカテゴリ指定 | all (全カテゴリ) |
| `--format <fmt>` | `tar.gz` または `zip` | `tar.gz` |

### カテゴリ一覧

| カテゴリ名 | 対象パス | 説明 |
|---|---|---|
| `skills` | `skills/` (SKILL.md 全件) | スキル定義 |
| `plans` | `docs/plans/PLAN-*.md` | PLAN 全件 |
| `adrs` | `docs/adr/ADR-*.md` | ADR 全件 |

### bundle 内構造

```
bundle.tar.gz
├── MANIFEST.json          # artifact 一覧 + hash + summary
├── INDEX.md               # markdown 索引 (外部 review 用)
├── skills/
│   └── ... (SKILL.md 全件 or --include skills 対象)
├── plans/
│   └── PLAN-*.md
└── adrs/
    └── ADR-*.md
```

---

## §3. MANIFEST.json 仕様

```json
{
  "generated_at": "2026-05-23T00:00:00Z",
  "helix_version": "v2",
  "categories": ["skills", "plans", "adrs"],
  "artifacts": [
    {
      "path": "plans/PLAN-169-helix-framework-import-tool.md",
      "sha256": "abc123...",
      "title": "PLAN-169: HELIX framework import tool",
      "status": "draft",
      "created": "2026-05-23"
    }
  ]
}
```

hash は `sha256sum` (Linux) / `shasum -a 256` (macOS) で生成、Python `hashlib.sha256` を使って portable に実装する。

---

## §4. 実装方針

### Sprint .1: pmo-sonnet — 資産棚卸し + 仕様確認

担当: pmo-sonnet

```bash
# export 対象の規模確認
find skills/ -name "SKILL.md" | wc -l
ls docs/plans/PLAN-*.md | wc -l
ls docs/adr/ADR-*.md | wc -l
```

出力: 各カテゴリの file 数 + frontmatter parse 可能な field 一覧 (title / status / created)

### Sprint .2: se — cli/helix-export 実装

担当: se

実装ファイル:
- `cli/helix-export` (Bash、メイン CLI)
  - getopts で `--output` / `--include` / `--format` をパース
  - Python `helix_export_bundle.py` をインライン script で呼び出すか、inline Python ヒアドキュメントで実装
- cli/helix routing 登録 (2 行追加)

**実装核心部 (Python inline)**:

```python
import hashlib, json, tarfile, zipfile, re
from pathlib import Path
from datetime import datetime, timezone

def collect_artifacts(helix_home, categories):
    """カテゴリ別にファイルリストを収集"""
    files = []
    if "skills" in categories:
        files.extend(Path(helix_home, "skills").rglob("SKILL.md"))
    if "plans" in categories:
        files.extend(Path(helix_home, "docs/plans").glob("PLAN-*.md"))
    if "adrs" in categories:
        files.extend(Path(helix_home, "docs/adr").glob("ADR-*.md"))
    return files

def sha256_file(path):
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def extract_frontmatter_fields(path):
    """title / status / created を frontmatter から抽出 (yaml.safe_load 不使用、正規表現で軽量抽出)"""
    text = path.read_text(encoding="utf-8")
    title   = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE)
    status  = re.search(r'^status:\s*(\S+)', text, re.MULTILINE)
    created = re.search(r'^created:\s*(\S+)', text, re.MULTILINE)
    return {
        "title":   title.group(1).strip() if title else None,
        "status":  status.group(1) if status else None,
        "created": created.group(1) if created else None,
    }
```

cli/helix routing 登録:

```bash
export) exec "$HELIX_CLI_DIR/helix-export" "$@" ;;
```

---

## §5. Sprint 計画

| Sprint | 内容 | 担当 | 完了条件 |
|---|---|---|---|
| **Sprint .1** | 資産棚卸し + MANIFEST 仕様確認 | pmo-sonnet | カテゴリ別 file 数・frontmatter field 確認 |
| **Sprint .2** | cli/helix-export 実装 + routing 登録 + bats テスト | se | `bash -n` PASS + bats 全 PASS + `helix commands` に export 表示 |

---

## §6. DoD (Definition of Done)

1. `helix export --output /tmp/bundle.tar.gz` が archive を生成する
2. archive 内に `MANIFEST.json` と `INDEX.md` が存在する
3. `--include plans` が plans/ のみを archive に含む
4. `--format zip` で .zip 形式でも出力できる
5. `helix commands` に `export` が表示される
6. `bash -n cli/helix-export` PASS
7. bats テスト全 PASS
8. `python3 cli/lib/plan_validator.py docs/plans/PLAN-170-*.md` PASS

---

## §7. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 (本 file) | docs/plans/PLAN-170-*.md |
| ② 実装コード | Sprint .2 で生成 | cli/helix-export |
| ③ テスト設計 | Sprint .2 で起票 | docs/v2/L4-test-design/PLAN-170-test-design.md |
| ④ テストコード | Sprint .2 実装 | cli/tests/test_helix_export.bats |

**双方向 reference**:
- 本 PLAN (①) → 実装 (②): `generates.artifact_path` に明記
- 実装 (②) → 本 PLAN (①): cli/helix-export 先頭 comment に `# PLAN-170` 明記
- 本 PLAN (①) → テスト設計 (③): Sprint .2 起票後に §7 に追記
- テスト設計 (③) → 本 PLAN (①): frontmatter `related_plans: [PLAN-170]` 明記

---

## §8. リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| skills/ が大量 SKILL.md で archive サイズが大きい | bundle が 10MB を超えてメール添付等で送れない | `--include` で対象を絞ることを推奨、README に記載 |
| frontmatter 正規表現抽出が YAML 複数行値で誤動作 | MANIFEST の title が空や不正になる | 抽出失敗時は `null` を設定し、WARN を stderr に出力して処理継続 |
| Python バージョン差異 (tarfile API) | 古い Python 3.8 で動作しない | `tarfile.open` の標準 API のみ使用、3.8 互換で実装 |
| `helix export` と `helix import` の命名が対称に見えるが機能が非対称 | ユーザーが `import ↔ export` で逆方向操作を期待する | help 文に「export はアーカイブ生成専用、import は新規 repo への framework 導入」を明記 |
