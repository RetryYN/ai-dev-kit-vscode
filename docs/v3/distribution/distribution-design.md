# HELIX V3 — 配布設計（HELIX 公開 API 維持 + harness ADR-005 を後乗せ）

> **status: 再構築中**（[capture §6 ADR-005](../audit/2026-06-26-new-base-comprehensive-capture.md) 整合）
> 出自: **HELIX 既存の配布（`@~/.helix/core` 公開 API）を維持**しつつ、harness ADR-005（GitHub-pull tag-pin 配布 + 中央 Web UI + 4-provider 住所モデル）を **HELIX 独自強化として後乗せ**。**最重要制約 = 公開 API `@~/.helix/core/<path>` 据え置き（破壊禁止）**。
> 接続: [L5 §1 artifact_registry](../L0-L14/L5-detailed-design.md) / [L6 §2 FN-DET-14](../L0-L14/L6-functional-design.md)
> V2 参照（裏取り済 file:line）: `helix/core-manifest.tsv:17-21` / `setup.sh:13-15,79-106` / `cli/lib/tests/test_core_manifest_drift.py:1-95` / `HELIX-workflows/helix-process/document-topology.md:188-207`

## 0. 盗む対象と凍結すべき不変条件

配布は「全 project に効く harness を、clone 位置非依存で消費側へ届ける」機構。V3 でも次を不変として維持する:
1. **公開 API `@~/.helix/core/<path>`**（消費側 loader が直接読む。path 変更 = breaking）。
2. **core-manifest.tsv = 常時注入 core セットの単一 SSoT**（setup.sh / loader に hardcode 禁止）。
3. **配置非依存 mount**（`~/.helix/core` → repo root の symlink で clone 位置を隠蔽）。

## 1. 公開 API の解決機構

- `setup.sh:13-14` が `HELIX_HOME=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)` で clone 位置を非依存解決。`setup.sh:15` の `HELIX_CORE_LINK="$HOME/.helix/core"` を `HELIX_HOME` へ symlink（`setup.sh:79-106`、既存/向き違い/broken を各々分岐＝idempotent）。
- これで `@~/.helix/core/<path>` は常に repo 内同一相対 path に解決される。
- **破壊条件 3 つ**: ①manifest の import-path 書き換え ②`helix/` 対象ファイルの物理移動 ③symlink の向き先変更。いずれも消費側 `~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` の `@import` を silent に未解決化する。

## 2. core-manifest.tsv（SSoT）と scope 合成

- 形式: `<scope>\t<import-path>` の 2 列 TSV（`#` コメント可）。scope ∈ `{common, claude, codex}`。
- 現登録（`core-manifest.tsv:17-21`、裏取り済）: common×3（HELIX_CORE / HELIX_RUNTIME_RULES / HELIX-process-L0-L14）+ claude×1（CLAUDE_RUNTIME_ADAPTER）+ codex×1（CODEX_RUNTIME_ADAPTER）。
- 合成: **Claude 注入 = common + claude**、**Codex 注入 = common + codex**。
- setup.sh の `load_core_imports()`（`setup.sh:40-70`）が manifest を行読みして scope フィルタ → loader へ追記。**import path の hardcode は setup.sh 内に一切なし**（test で機械保証）。

## 3. 4 tier 保存先 + G/P 住所分離 doctrine

| tier | 住所 | 解決 |
|---|---|---|
| MASTER | `<clone>/` | git 管理原本 |
| GLOBAL-CORE | `~/.helix/core/` | MASTER への symlink |
| GLOBAL-STATE | `~/.helix/` | global.db / workspaces（gitignore） |
| PROJECT-STATE | `<project>/.helix/` | project 固有 runtime |
| INJECTION | `~/.claude/CLAUDE.md` 等 | `@~/.helix/core/...` 参照のみ |

- **G/P 住所分離**（`document-topology.md:188-198`）: G（配布物 = `helix/`, `HELIX-workflows/`, `cli/`, `skills/`, `.claude/{agents,hooks,commands}`）と P（project 専用 = `docs/plans/`, `docs/v2/`, `docs/v3/`, `docs/{adr,research}`）。同一内容を両方に書かない、G 正本 → P は参照のみ（drift 防止）。
- 判定一問: 「全 project に配布されて効くか（→ G）」「この repo を作る計画・設計記録か（→ P）」。

## 4. FN-DET-14 dist-api-consistency（多点突合 detector）

V3 は配布回帰を C3 detector で機械検出する。V2 の `test_core_manifest_drift.py`（4 テスト、全行裏取り済）を **detector 仕様まで昇格**する。

| 突合 | 内容 | V2 出自 |
|---|---|---|
| ①schema/scope | manifest 全行が scope ∈ {common,claude,codex} かつ `@~/.helix/core/` prefix | `:69-75` |
| ②setup.sh ⇔ manifest | `load_core_imports()` 出力 = manifest の common+claude と完全一致 + setup.sh に hardcode 不在 | `:78-85` |
| ③loader ⇔ clone-path | loader 全 `@` 行が `@~/ai-dev-kit-vscode/`（clone 直 path）で始まらない | `:88-91` |
| ④manifest ⇔ 配布契約 | manifest common+claude = 配布契約定義と一致 | `:94-95` |
| **⑤（V3 で新設）loader ⇔ manifest 実体** | 実 `~/.claude/CLAUDE.md` が manifest の全 import を**実際に含む**こと | **gap**（②④は定数突合で実 loader 内容と未突合） |

> V3 keystone への接続: 上記突合は artifact_registry（manifest/setup.sh/loader を artifact として投影）への DB query で実装し、file scan に依存しない（FN-DET-14、severity=hard）。⑤は explorer が見つけた現行 gap の埋め。

## 5. 将来移動 policy / install·uninstall 対称性

- **公開 API path の将来移動**（`document-topology.md:200-207`）: メジャー境界 + 旧 path shim ≥2 minor + migration detector + manifest 更新 + drift test の 4 ステップ。V3 では**この policy を再宣言せず document-topology を正本参照**（G↔P drift 防止）。
- **install/uninstall 対称性**: `setup.sh` の `uninstall()`（`:387-491`）が install の全逆操作（CLAUDE.md import 除去 / symlink 削除 / settings.json hook 除去 / PATH 除去 / Codex config 除去）。V3 でも install/uninstall 対称性を**設計時に要件化**（後付け困難）。

## 6. 検証（V-model pair）

- 受入（L3↔L12）: AT-DST-01 manifest に新 import 追加 → setup.sh/loader 自動追従（hardcode 不在）/ AT-DST-02 loader が clone-path 直参照 → FN-DET-14 検出 / AT-DST-03 manifest と実 loader 不一致（⑤）→ 検出。
- 単体（L6↔L7）: FN-DET-14 に UT-DET-14。fixture（manifest/setup.sh/loader の既知行）で 5 突合の境界を突く。

## 7. 未確定

- `~/.helix/global.db` / `workspaces/` / `recipes/` の実在は今回未確認（CLAUDE.md 記述あり・document-topology 実ファイルリスト未登場）→ L7 着手前に実在確認。
- repo 内 `.claude/CLAUDE.md`（loader）と `~/.claude/CLAUDE.md`（注入先）の二重性を V3 設計で明示整理（`test_core_manifest_drift.py:11` の `GLOBAL_CLAUDE_MD` は前者）。
