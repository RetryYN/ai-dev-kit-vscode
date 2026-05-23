---
plan_id: PLAN-218
title: "PLAN-218: HELIX framework npm/pip package export"
kind: impl
layer: cross
drive: be
status: draft
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-169-helix-framework-import-tool.md   # from dependencies.parent
size: L
created: 2026-05-23
owner: PM
agent_slots:
  - role: tl-advisor
    slot_label: "TL — pyproject.toml / package.json 設計・配布方針・ADR 起票判断"
  - role: se
    slot_label: "SE — pyproject.toml / setup.cfg 実装・CLI entry_points 設定・PyPI 発行スクリプト"
  - role: pmo-sonnet
    slot_label: "PMO — 既存 cli/ ファイル構成と package 化範囲の棚卸し・PLAN-169 との境界整合確認"
  - role: qa
    slot_label: "QA — pip install -e . smoke テスト・npm pack 動作確認・CLI エントリポイント疎通"
generates:
  - artifact_path: pyproject.toml
    artifact_type: config
  - artifact_path: npm/package.json
    artifact_type: json_config
  - artifact_path: cli/lib/package_export.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_package_export.py
    artifact_type: test
  - artifact_path: docs/v2/L4-test-design/PLAN-218-test-design.md
    artifact_type: design_doc
dependencies:
  parent: PLAN-169
  requires:
    - PLAN-169
  blocks: []
related_plans:
  - PLAN-169
related_docs:
  - cli/ROLE_MAP.md
  - skills/SKILL_MAP.md
  - helix/HELIX_CORE.md
---

# PLAN-218: HELIX framework npm/pip package export

## L2 凍結 (ADR snapshot)

本 PLAN tree は Python / Node.js の 2 package 系統への同時対応、および `helix` CLI を entry_points として公開する採用判断を含む。これらは L2 大局判断に該当するため、ADR snapshot を併設する。

| ADR | 凍結対象 | Status |
|---|---|---|
| ADR-057 (起票予定) | pip / npm 二系統配布方針・entry_points 設計・CLI wrapper 戦略 | Proposed |

双方向 trace:
- 本 PLAN → ADR-057: frontmatter `related_adr` + 本 section
- ADR-057 → 本 PLAN: ADR-057 `## Related` に「PLAN-218 (実装 PLAN)」を記載

> ADR-057 は L4 着手前に起票する。WebSearch 3 query 必須 (pip package CLI entry_points 設計 / npm bin package 公開手順 / Python CLI framework packaging best practice)。

---

## §0. 背景・問題設定

PLAN-169 では既存 repo への `helix import` CLI を実装したが、外部 project が HELIX framework を利用するには依然として手動クローンまたは import CLI の実行が必要である。

| 課題 | 影響 |
|---|---|
| `pip install helix-framework` が存在しない | 外部 project の導入に手動手順が必要 |
| npm 経由で Node.js project に統合できない | JS/TS エコシステムとの連携が困難 |
| バージョン管理が git tag 依存 | pinning・upgrade の標準手段がない |
| `helix` CLI が PATH に自動追加されない | インストール後の疎通手順が複雑 |

---

## §1. 目的

1. `pyproject.toml` で `helix-framework` Python package を定義し、`pip install helix-framework` で導入可能にする
2. `npm/package.json` で `@helix-framework/helix` Node.js package を定義し、`npm install` で導入可能にする
3. `pip install` 後に `helix` コマンドが `entry_points` 経由で PATH に追加される
4. skill / template / hook / CLAUDE.md が package data として同梱され、`helix import` の source として機能する
5. PLAN-169 `helix import` CLI を package 経由導入時のオンボーディング起点として統合する

---

## §2. パッケージ構成方針

### 2.1 Python package (pip)

```
pyproject.toml
  [project]
    name = "helix-framework"
    version = "0.1.0"
    [project.scripts]
      helix = "helix_framework.cli:main"
  [tool.hatch.build.targets.wheel]
    packages = ["cli", "skills", "helix"]
    include = ["cli/**", "skills/**", "helix/**", "CLAUDE.md"]
```

配布物:
- `cli/`: Python helper modules + bash CLI (scripts として配置)
- `skills/`: SKILL_MAP.md + SKILL.md 群
- `helix/`: HELIX_CORE.md + CODEX_TL_MODE.md
- entry_point: `helix` → `helix_framework.cli:main` (既存 cli/helix を wrap)

### 2.2 Node.js package (npm)

```json
{
  "name": "@helix-framework/helix",
  "version": "0.1.0",
  "bin": { "helix": "./bin/helix.js" },
  "files": ["bin/", "skills/", "helix/", "CLAUDE.md"]
}
```

`bin/helix.js` は `python3 -m helix_framework.cli` を spawn する thin wrapper。

### 2.3 HELIX_HOME 解決

package 経由インストール時、`HELIX_HOME` は `pip show helix-framework` の Location から自動解決する。`cli/helix` の先頭で `HELIX_HOME` 未設定時は package install 先をフォールバック先として使用する。

---

## §3. 実装 Sprint 計画

### Sprint .1: pmo-sonnet — 棚卸し + 境界確認

担当: pmo-sonnet

確認事項:
- `cli/` 以下の Python module 一覧と package 化対象ファイル数
- PLAN-169 `helix import` との role 分担 (import CLI は本 PLAN の package に同梱)
- 既存 `cli/helix` bash entry の Python wrapper 化可否

出力: package 化対象ファイルリスト + PLAN-169 境界整合メモ

### Sprint .2: tl-advisor — 設計凍結

担当: tl-advisor

設計対象:
- `pyproject.toml` 全フィールド (hatchling / setuptools 選択含む)
- `npm/package.json` 構造
- `helix_framework/cli.py` entry_point wrapper 設計
- `HELIX_HOME` 自動解決ロジック
- ADR-057 起票トリガ

### Sprint .3: se — pyproject.toml + npm/package.json 実装

担当: se

実装ファイル:
- `pyproject.toml`
- `helix_framework/__init__.py` + `helix_framework/cli.py`
- `npm/package.json` + `npm/bin/helix.js`
- `cli/lib/package_export.py` (HELIX_HOME resolve + version 取得 helper)

### Sprint .4: qa — smoke テスト + bats

担当: qa

```bash
# pip install -e . で CLI 疎通確認
pip install -e . --quiet
helix help

# npm pack + bin 疎通確認
cd npm && npm pack && npm install -g helix-framework-*.tgz
helix help

# HELIX_HOME 自動解決確認
unset HELIX_HOME && helix version
```

---

## §4. DoD (Definition of Done)

1. `pip install -e .` 後に `helix help` が動作する
2. `npm pack` が `@helix-framework/helix-*.tgz` を生成する
3. `python3 -m py_compile helix_framework/cli.py` PASS
4. `pytest cli/lib/tests/test_package_export.py` 全 PASS
5. `helix import --target /tmp/test` が package 同梱 skill を source として動作する
6. `python3 cli/lib/plan_validator.py docs/plans/PLAN-218-*.md` PASS
7. ADR-057 起票済 (L2 凍結)

---

## §5. V-model 4 artifact trace

| Artifact | 状態 | ファイル |
|---|---|---|
| ① 設計 (本 PLAN) | 存在 | docs/plans/PLAN-218-*.md |
| ② 実装コード | Sprint .3 で生成 | pyproject.toml / npm/package.json / helix_framework/ |
| ③ テスト設計 | Sprint .4 で起票 | docs/v2/L4-test-design/PLAN-218-test-design.md |
| ④ テストコード | Sprint .4 実装 | cli/lib/tests/test_package_export.py |

---

## §6. リスク

| リスク | 影響 | 緩和策 |
|---|---|---|
| bash CLI が pip wheel に含まれない | `helix` コマンドが未動作 | `entry_points` で Python wrapper を経由し bash を spawn する二段構成 |
| `HELIX_HOME` が package install 先と開発 clone 先で競合 | skill / template の参照先が混在 | env var 優先、未設定時 package location を self-resolve |
| skills/ の大量ファイルが wheel サイズを増大 | pip install が遅い | `.whl` 含有 skill は最小 core set に絞り、追加は `helix import` で対応 |
| npm wrapper が Python 未インストール環境で失敗 | Node.js only 環境で動作しない | preflight check で Python 3.9+ の存在を確認し、不在時は案内メッセージを出力 |
