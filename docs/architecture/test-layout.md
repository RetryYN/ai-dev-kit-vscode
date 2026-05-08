# Test Layout

## 概要

HELIX のテストは 2 ディレクトリ構成:

| 配置 | 役割 | 主な対象 |
|------|------|---------|
| `tests/` (project-root) | catalog 公開挙動 + migration end-to-end | 統合テスト、外部公開 API 等 |
| `cli/lib/tests/` | unit (helper / 単一関数) | 内部関数の単体テスト |

## tests/ (project-root)

- 対象: `helix code` catalog 公開挙動、helix.db migration の end-to-end (legacy v14 → v19)
- 件数: 23 (PLAN-031 W-3 完遂時点)
- 実行: `python3 -m pytest tests/ -q`

## cli/lib/tests/

- 対象: cli/lib 配下の helper module 単体 (skill_recommender / helix_db / codex_post_validation 等)
- 件数: 963 (PLAN-031 W-3 完遂時点)
- 実行: `python3 -m pytest cli/lib/tests/ -q`

## 役割分担: test_code_catalog.py の二重配置

`tests/test_code_catalog.py` と `cli/lib/tests/test_code_catalog.py` は **同名だが役割が異なる**:

| ファイル | 役割 | 手段 |
|---------|------|------|
| `tests/test_code_catalog.py` | E2E (catalog 公開挙動 + helix.db migration) | `subprocess + git init` で実 git repo を構築し、catalog 構築フローを end-to-end で検証 |
| `cli/lib/tests/test_code_catalog.py` | unit (parse / classify_bucket 単体) | 直 import で `parse_helix_index_comment` 等の helper 関数を単独検証 |

PLAN-013 で integration の役割境界 (3-bucket taxonomy 検証) を確立しており、両者は **物理削除対象ではなく役割分担として保持する**。

過去 PLAN-032 W-5 で「物理整理は PLAN-033 以降」と書かれたが、PLAN-033 W-3 でこの方針 (役割分担保持) を確定した。

## bats テスト

- 配置: `cli/tests/*.bats`
- 役割: shell スクリプト (cli/helix-* / cli/codex / cli/claude shim) の動作テスト
- 件数: 338 (PLAN-031 W-2 完遂時点)
- 実行: `bats cli/tests/*.bats`

## helix-test (shell-based self-test)

- 配置: `cli/helix-test`
- 役割: HELIX 全体の動作 self-test (init / phase / gate / sprint / agents / codex 等)
- 種別: shell-based (pytest/bats とは別 layer)
- 実行: `cli/helix-test`

## 関連 PLAN

- PLAN-013: 3-bucket taxonomy + tests/ 拡張
- PLAN-031 W-3: helix_db migration create-if-missing
- PLAN-032 W-5: 本ファイル作成
