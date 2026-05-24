---
plan_id: L7-scrum-to-discovery-migration-enumplan
name: L7-scrum-to-discovery-migration-enumplan
title: "L7-scrum-to-discovery-migration-enumplan: runtime dir migration + drive/mode enum 正規化 + Stage activation (Stage 2-4 担当)"
description: scrum→discovery rename の Stage 2-4 (runtime dir migration data 保全 + drive/mode/kind enum 正規化 + HELIX_DISCOVERY_COMPAT_STAGE activation + S0-S4→D0-D4 state machine 分離 + removal timeline stub)
status: draft
process_layer: L7
layer: L7
kind: impl
drive: be
size: L
priority: P1
created: 2026-05-24
revised: 2026-05-24
owner: PM
parent_design: HELIX-workflows/helix-process/discovery-workflow.md
pairs_test_design: []
generates:
  - artifact_path: docs/v2/L7-design/L7-scrum-to-discovery-migration-enum-design.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L7-test-design/L7-scrum-to-discovery-migration-enum-test-design.md
    artifact_type: design_doc
  - artifact_path: cli/lib/discovery_migrate.py
    artifact_type: python_module
  - artifact_path: cli/lib/discovery_compat.py
    artifact_type: python_module
  - artifact_path: cli/helix-discovery (migrate subcommand 拡張)
    artifact_type: cli_extension
  - artifact_path: cli/lib/plan_validator.py (VALID_DRIVES + compat enum 追加)
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_discovery_migrate.py
    artifact_type: test
dependencies:
  parent: L7-helix-workflows-parent-acceptedplan
  requires:
    - L7-scrum-to-discovery-renameplan
  blocks: []
related_docs:
  - HELIX-workflows/helix-process/discovery-workflow.md
  - HELIX-workflows/helix-process/scrum-workflow.md
  - cli/lib/plan_validator.py
  - cli/helix-discovery
  - cli/helix-scrum
  - docs/v2/CONCEPT.md
agent_slots:
  - role: tl-advisor
    slot_label: "TL — runtime migration atomicity 設計・enum 互換契約・Stage activation 仕組み妥当性検証 (R1 adversarial check)"
  - role: se
    slot_label: "SE — cli/lib/discovery_migrate.py 実装 + cli/lib/discovery_compat.py 分離実装 + plan_validator.py retrofit + migrate subcommand + pytest"
  - role: pmo-sonnet
    slot_label: "PMO — 4 artifact 双方向 trace review + A1/A2 scope 境界最終確認"
is_reference: false
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/discovery-workflow.md](../../../HELIX-workflows/helix-process/discovery-workflow.md)
> **前段 PLAN (A1)**: [L7-scrum-to-discovery-renameplan](./L7-scrum-to-discovery-renameplan.md) — CLI/skill/doc alias + Stage 1 deprecated warning に scope 限定
> **本 PLAN の scope**: A1 完遂後の後段。**Stage 2-4 = runtime dir migration (data 保全あり) + drive/mode/kind enum 正規化 + Stage activation 仕組み + S0-S4→D0-D4 state machine 分離 + removal timeline stub** を担う。

### A1/A2 scope 境界

| scope | A1 (前段 PLAN) | A2 (本 PLAN) |
|---|---|---|
| CLI binary 作成 | `cli/helix-discovery` 作成・`cli/helix-scrum` shim 化 | 対象外 (A1 完遂済前提) |
| skill rename | `helix-scrum/` → `helix-discovery/` dir rename | 対象外 (A1 完遂済前提) |
| Stage 1 alias | helix router 両エントリ登録 | 対象外 |
| deprecated warning | stderr warning 出力 (Stage 2) | **本 PLAN: Stage 2 warning の activation 仕組み** |
| runtime dir migration | `cp -r` のみ (A1 時点で一切実装しない) | **本 PLAN: 保全設計 + atomicity + manifest 検証 + smoke** |
| drive/kind enum | VALID_DRIVES に `scrum` 残存のまま A1 終了 | **本 PLAN: `discovery` 追加 + compat 設計** |
| S0-S4 → D0-D4 | 概念整理のみ (doc) | **本 PLAN: state machine 分離 (表示 layer vs DB state)** |
| Stage activation | 言及なし | **本 PLAN: `HELIX_DISCOVERY_COMPAT_STAGE` env + config** |
| removal timeline | §10 carry 記載のみ | **本 PLAN: `L7-helix-scrum-removal-plan` stub 起票** |

### tl-advisor R1 P0/P1 指摘からの導出

本 PLAN は下記 R1 指摘を設計起点とする:

- **P0-2 (runtime migration data 保全)**: `cp -r` のみでは atomicity・部分コピー復旧・manifest 検証・lock・再実行安全性がない。仕様化必要
- **P0-1 (mode/drive/kind 契約)**: `plan_validator.py` の `VALID_KINDS` に `scrum` 不在 / `VALID_DRIVES` に `scrum` あり。`kind: discovery` 単純追加ではなく drive/current_mode/helix size/helix mode/phase.yaml/doctor/command_mapper の互換設計が先
- **P1-1 (Stage activation source)**: `HELIX_DISCOVERY_COMPAT_STAGE` env / config / feature flag の決定的 source と既定値・release 時切替手順
- **P1-7 (removal timeline stub)**: `L7-helix-scrum-removal-plan` stub 起票 (telemetry/grep で旧利用確認条件含む)
- **P2-2 (`helix discovery migrate` UI)**: `--dry-run` と `--status` subcommand 定義
- **P2-3 (既存 `.helix/discovery/` conflict 時 merge 方針)**: backlog.yaml 差分・verify dir conflict・README.deprecated 単独存在 test case
- **P2-5 (S0-S4 → D0-D4 state machine 分離)**: 表示 layer は D0-D4、既存 DB state `S0-S3` や tests は migration 対象外推奨

---

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|---|---|---|---|
| 0 | **前提確認: A1 (L7-scrum-to-discovery-renameplan) 完遂確認** (以下の PASS 条件 全 3 件を機械確認すること。1 件でも FAIL なら本 PLAN は blocked)<br>PASS-1: `test -x cli/helix-discovery` — alias shim が存在して実行可能<br>PASS-2: `grep -q "discovery)" cli/helix` — cli/helix router に discovery routing が登録済<br>PASS-3: `helix discovery --help` が exit 0 で discovery help を表示<br>FAIL 時: A1 完遂を待ち、本 PLAN 着手不可 | PM | □ pending |
| 1 | tl-advisor R1 adversarial check (§2 設計全体) | PM → TL | □ pending |
| 2 | R1 指摘反映 (必要に応じて §2 更新) | PM | □ pending |
| 3 | tl-advisor R2 (R1 needs_revision の場合) | PM → TL | □ pending |
| 4 | Sprint .1 design doc 起草 (docs/v2/L7-design/ + test-design/) | PM → SE docs | □ pending |
| 5 | Sprint .2 cli/lib/discovery_migrate.py 実装 (§2.2 保全設計準拠、migration data movement のみ: copy/manifest/lock/verify) | PM → SE | □ pending |
| 6 | Sprint .3 `helix discovery migrate` subcommand 拡張 (--dry-run / --status / auto) | PM → SE | □ pending |
| 7 | Sprint .4 plan_validator.py VALID_DRIVES + compat enum retrofit (§2.1 準拠) | PM → SE | □ pending |
| 8 | Sprint .5 phase.yaml / helix doctor / command_mapper compat 更新 (§2.1 準拠) | PM → SE | □ pending |
| 9 | Sprint .6 cli/lib/discovery_compat.py 実装 (§2.5 準拠: stage/drive/phase 表示変換を discovery_migrate.py から分離) | PM → SE | □ pending |
| 10 | Sprint .7 S0-S4 → D0-D4 state machine 分離 + Stage activation CLI 組み込み (§2.3 / §2.4 準拠: 表示 layer のみ変更) | PM → SE | □ pending |
| 11 | Sprint .8 `L7-helix-scrum-removal-plan` stub 起票 (§9 carry) | PM | □ pending |
| 12 | 機械チェック: bash -n / shellcheck / python3 -m py_compile / yamllint | SE | □ pending |
| 13 | pytest test_discovery_migrate.py 全 PASS (§5 DoD 参照) | SE | □ pending |
| 14 | migration smoke test 実行 (dry-run → status → execute → verify 4 段) | SE | □ pending |
| 15 | pmo-sonnet 4 artifact 双方向 trace review | PM → PMO | □ pending |
| 16 | commit + push | PM | □ pending |

---

## §2 設計判断

### §2.1 drive/kind/mode 契約整理と互換設計

#### 2.1.1 現状の問題

`plan_validator.py` の現在の状態:

```python
# VALID_KINDS (line 13-36): "scrum" は不在
# VALID_DRIVES (line 78-87): "scrum" は存在する
VALID_DRIVES = {
    "be", "fe", "fullstack",
    "scrum",    # ← 旧名称のまま残存
    "db", "agent", "reverse", "poc", "troubleshoot",
}
```

**問題**: `drive: discovery` を使う PLAN は plan_validator で unknown drive として扱われる。
`drive: scrum` の旧 PLAN は valid のまま → rename 中断状態。

#### 2.1.2 drive enum 移行設計

**採用方針: 段階追加 + deprecation warning (breaking change なし)**

```python
# Stage 2 以降で適用する VALID_DRIVES 状態:
VALID_DRIVES = {
    "be", "fe", "fullstack",
    "discovery",   # ← 新規追加 (Stage 2 から valid)
    "scrum",       # ← deprecated (Stage 2: warn-only、Stage 4: 削除)
    "db", "agent", "reverse", "poc", "troubleshoot",
}
DEPRECATED_DRIVES = {
    "scrum": "discovery",   # 旧 → 新 のマッピング
}
```

**plan_validator 変更内容** (Sprint .4 で実装):
1. `DEPRECATED_DRIVES` dict を追加 (旧 drive → 推奨 drive のマッピング)
2. `validate_frontmatter()` 内: `drive in DEPRECATED_DRIVES` → `warn_deprecated()` を呼ぶ (fail-close ではなく warn)
3. `VALID_DRIVES` に `"discovery"` を追加
4. `"scrum"` は Stage 4 まで残す (削除は L7-helix-scrum-removal-plan 担当)

#### 2.1.3 kind 契約 (discovery kind は追加しない)

**設計判断**: `kind: discovery` は追加しない。

根拠:
- `discovery-workflow.md` は「起票 PLAN kind は `poc`」と明記している
- Discovery モードは PLAN の kind ではなく **drive** で表現する (drive: discovery)
- kind に discovery を追加すると「discovery モードの PLAN」vs「discovery という種別の PLAN」が混在して概念が分裂する
- A1/A2 で kind は変更しない。drive: scrum → drive: discovery の移行のみ実施

**VALID_KINDS への変更なし**: kind=impl / poc / refactor 等の既存種別は Discovery モードでも使用可能。

#### 2.1.4 helix size / helix mode / phase.yaml / doctor / command_mapper 互換

| 箇所 | 現状 | 変更内容 | Sprint |
|---|---|---|---|
| `helix size --drive scrum` | scrum を渡すと VALID_DRIVES でヒット | `--drive discovery` も同等に処理。`--drive scrum` は deprecated warn を出して内部で discovery に変換 | Sprint .4 |
| `helix mode` (存在する場合) | scrum → discovery 内部マッピング | command_mapper で `scrum` → `discovery` alias 追加 | Sprint .5 |
| `.helix/phase.yaml` | `current_mode: scrum` 記録可能 | 読み込み時に `scrum` → `discovery` に正規化して返す read compat shim を追加 | Sprint .5 |
| `helix doctor` | VALID_DRIVES で scrum を warn-only 扱い | deprecation warn を doctor レポートに追加 (fail-close は Stage 4 以降) | Sprint .5 |
| `cli/helix` (command_mapper) | scrum → helix-scrum routing | discovery → helix-discovery 追加。scrum → helix-scrum shim 維持 (Stage 4 まで) | A1 完遂済 |

#### 2.1.5 既存 PLAN retrofit (drive: scrum → drive: discovery)

既存 PLAN (`docs/plans/`) で `drive: scrum` を持つ件数を確認し、Stage 2 移行後に一括 retrofit:

```bash
# 確認コマンド:
grep -rl "^drive: scrum" docs/plans/ | wc -l
```

**retrofit 方針**: 本 PLAN Sprint .4 では検出のみ。実際の retrofit は後続 carry (L7-helix-scrum-removal-plan Sprint .1) で一括実施。本 PLAN DoD には含まない。

---

### §2.2 runtime dir migration の data 保全設計 (P0-2 対応)

A1 の `cp -r` のみでは不十分。以下の保全要件を全て満たす `cli/lib/discovery_migrate.py` を実装する。

#### 2.2.1 保全要件一覧

| 要件 | 詳細 |
|---|---|
| **原子性 (atomicity)** | コピー先を `dst.tmp` に書き込み、完全コピー検証後に rename で原子的に最終 dst に昇格 |
| **manifest 検証** | コピー前に src file list と size を記録、コピー後に dst で照合 (count + sha256 hash) |
| **lock** | `.helix/discovery_migrate.lock` で並行実行を防止 (fcntl.flock または sentinel file) |
| **再実行安全性 (idempotent)** | 既に migrate 完了済みの場合は skip (dst 存在 + manifest 一致 で判定)、部分コピー済みの tmp は cleanup してやり直し |
| **失敗時 cleanup** | `dst.tmp` が残る場合は安全に削除して src は無傷で残す |
| **部分コピー復旧** | コピー途中で interrupted された場合、tmp cleanup → 再実行で全コピーを保証 |
| **dst conflict 処理** | `.helix/discovery/` が既存の場合の merge 方針 (§2.2.3 参照) |
| **migration smoke** | migrate 後に `helix discovery backlog list` が正常終了することを確認 |
| **dry-run** | `--dry-run` で実際のコピーは行わず、コピー対象ファイルリスト + 推定サイズを表示 |
| **status** | `--status` で migrate 完了済み / 未実施 / 部分完了 (tmp 残存) を表示 |

#### 2.2.2 migration 実行フロー

> **P0-1 設計原則**: dst が non-empty directory の場合、atomic rename は成立しない。**pseudo-transaction pattern** を採用し、merge case では `dst.tmp` 構築 → `dst.backup-<timestamp>` 退避 → rename の 3 ステップで atomicity を擬似的に保証する。

```
migrate(src=".helix/scrum/", dst=".helix/discovery/") 実行フロー:

1. lock acquire (.helix/discovery_migrate.lock)
   └─ 取得失敗: "別の migrate が実行中" エラーで exit 1

2. src 存在確認
   ├─ src なし + dst あり: "既に migrate 完了またはデータなし" → status: complete_or_clean
   ├─ src なし + dst なし: "helix scrum データなし" → status: no_data
   └─ src あり: 続行

3. dst.tmp 残存確認
   ├─ dst.tmp あり: "前回の migrate が中断されています。tmp を削除して再実行します" → rm -rf dst.tmp
   └─ なし: 続行

4. manifest 生成 (src)
   manifest = {relative_path: (sha256, size_bytes), ...} for all regular files under src
   ※ 特殊ファイル (FIFO / device / socket / symlink) は fail-close (exit 2 + エラーメッセージ)

5. dst conflict 確認 (P0-1 核心)
   ├─ dst なし: → step 6 (新規 migration、安全)
   ├─ dst 存在 + 空 (empty): → step 6 (empty dir は上書き可能)
   ├─ dst 存在 + manifest hash 一致 (.migration-manifest.json 照合): idempotent skip → exit 0
   │   ※ 2 条件のみ auto-migrate 許可 (dst なし / manifest hash 一致)
   └─ dst 存在 + non-empty + manifest hash 不一致 (conflict):
       ├─ --merge-strategy 未指定 (default): abort → exit 2
       │   エラー: "dst .helix/discovery/ は non-empty です。
       │            helix discovery migrate --status で確認後、
       │            --merge-strategy [keep-dst|keep-src|abort] を明示して実行してください。"
       └─ --merge-strategy 明示: pseudo-transaction merge へ進む (step 5M)

5M. [merge case] pseudo-transaction pattern:
   a. dst.tmp/ に最終形を構築:
      - src/ のファイルを dst.tmp/ へコピー
      - 既存 dst/ のファイルを merge strategy に従って dst.tmp/ へ反映
        (keep-dst: dst のファイルを優先、keep-src: src のファイルを優先)
   b. manifest 検証 (dst.tmp):
      ├─ count/hash mismatch: → cleanup dst.tmp → exit 1
      └─ OK: 続行
   c. 既存 dst/ を dst.backup-<timestamp>/ に rename (atomic、同一 FS 前提)
      └─ rename 失敗: cleanup dst.tmp → exit 1 + "backup rename 失敗"
   d. dst.tmp/ → dst/ に rename (atomic)
      └─ rename 失敗: dst.backup-<timestamp>/ → dst/ に restore → cleanup dst.tmp → exit 1
   e. 成功: dst.backup-<timestamp>/ は 7 日後に削除 (rollback 余地として保持)
      ログ: "[INFO] backup: dst.backup-<timestamp>/ (7 日後に自動削除、rollback 手順: §2.2.4 参照)"
   → step 9 へ

6. [新規 migration case] dst.tmp/ へ全コピー (cp -r src/ dst.tmp/)

7. manifest 検証 (dst.tmp)
   ├─ count mismatch: → cleanup dst.tmp → exit 1 + "コピー不完全: ファイル数不一致"
   ├─ hash/size mismatch: → cleanup dst.tmp → exit 1 + "コピー不完全: hash/size 不一致 [file]"
   └─ OK: 続行

8. 原子 rename: dst.tmp → dst
   ├─ 同一 FS: POSIX atomic rename (os.rename)
   └─ 異 FS (EXDEV): **設定異常として fail-close** (exit 2 + "EXDEV: dst と src が異なる FS 上にあります。.helix/ を同一 FS 上に配置してください")
      ※ P2-2 対応: EXDEV fallback (mv + rm) は採用しない。dst.tmp は dst.parent 配下で同一 FS が保証されるべき

9. src に README.deprecated を配置
   内容: "このディレクトリは .helix/discovery/ へ移行されました (migration: YYYY-MM-DD)。
         helix discovery コマンドを使用してください。"

10. migration manifest を .helix/discovery/.migration-manifest.json に保存
    {"src": ".helix/scrum/", "dst": ".helix/discovery/", "migrated_at": ISO8601, "file_count": N, "total_bytes": N, "manifest_hash": "<sha256 of manifest content>"}

11. migration smoke test
    helix discovery backlog list (終了コード 0 を確認)

12. lock release

13. 完了メッセージ:
    "[OK] migration 完了: .helix/scrum/ → .helix/discovery/ (N files, X bytes)
    旧ディレクトリは .helix/scrum/ に README.deprecated を残して保持します。
    削除する場合: rm -rf .helix/scrum/"
```

#### 2.2.3 dst conflict 時の merge 方針 (P0-1 / P2-3 対応)

> **P0-1 設計原則**: default は **abort** (exit 2)。`--merge-strategy` を明示した場合のみ merge を続行する。merge case は §2.2.2 step 5M の pseudo-transaction pattern で実行する。

`.helix/discovery/` が既に存在する場合の処理:

| ケース | dst の状態 | 対応方針 (P0-1 改訂) |
|---|---|---|
| **A: dst が空** | `.helix/discovery/` は存在するが空 | src からそのままコピー (auto 許可、step 6 へ) |
| **B: dst に migration manifest あり (hash 一致)** | `.helix/discovery/.migration-manifest.json` 存在 + manifest hash 一致 | 既に migrate 完了とみなして skip (idempotent)。`--force` で再実行可 |
| **C: dst に backlog.yaml あり (conflict)** | 独立した backlog.yaml が存在 (manifest hash 不一致) | **default: abort (exit 2)**。`--merge-strategy keep-dst` / `keep-src` 明示時のみ pseudo-transaction merge (step 5M) へ |
| **D: dst に verify/ あり (conflict)** | verify/ ディレクトリが存在 (manifest hash 不一致) | **default: abort (exit 2)**。`--merge-strategy` 明示時のみ pseudo-transaction merge |
| **E: dst に README.deprecated のみ** | README.deprecated のみ存在 | cleanup して src からコピー (README.deprecated は auto 許可) |

**`--merge-strategy` オプション** (conflict 時のみ有効):
- *(未指定、default)*: **abort** — conflict 検出時は exit 2 + 手動指定要求メッセージを出力
- `keep-dst`: dst の既存ファイルを優先。src 固有ファイルのみ追加コピー (pseudo-transaction)
- `keep-src`: src を優先。dst の既存ファイルを上書き (pseudo-transaction)
- `abort`: 明示的に abort 指定 (default と同じ挙動)
- ~~`interactive`~~: 削除 (CI 環境での誤用リスク、ユーザー混乱回避のため非採用)

**auto-migrate で許可されるケース** (P0-2 厳格化):
1. dst なし → 新規 migration (安全)
2. dst 存在 + dst が空 → auto 許可
3. dst 存在 + manifest hash 一致 → idempotent 再実行 (無変更)

**auto-migrate で禁止されるケース** (conflict 時は必ず手動介入):
- dst 存在 + non-empty + manifest hash 不一致 → `helix discovery migrate --status` 表示 + 手動 `--merge-strategy` 要求

**merge 完了後に migration manifest を生成**し、以後の idempotent 判定に使用する。

#### 2.2.4 trigger: auto-migrate (Stage 3) — P0-2 厳格化

Stage 3 activation 時、`helix discovery` コマンド実行時の auto-migrate は **以下の 2 条件のみ**で実行する:

```bash
# cli/helix-discovery の先頭に追加 (Stage 3 のみ):
# P0-2: auto-migrate は「dst なし」または「manifest hash 一致」の場合のみ許可
_auto_migrate_if_safe() {
    local scrum_dir="$HELIX_DIR/scrum"
    local discovery_dir="$HELIX_DIR/discovery"
    local manifest="$discovery_dir/.migration-manifest.json"

    # auto-migrate 許可条件 1: dst なし (新規 migration)
    if [[ -d "$scrum_dir" ]] && [[ ! -d "$discovery_dir" ]]; then
        echo "[INFO] .helix/scrum/ を検出。自動移行を開始します..." >&2
        python3 -m cli.lib.discovery_migrate --auto
        return
    fi

    # auto-migrate 許可条件 2: dst 存在 + manifest hash 一致 (idempotent 再実行)
    if [[ -d "$scrum_dir" ]] && [[ -f "$manifest" ]]; then
        # manifest hash 一致確認は discovery_migrate.py 内部で判定 (hash 不一致は abort)
        python3 -m cli.lib.discovery_migrate --auto
        return
    fi

    # conflict 検出時 (dst 存在 + non-empty + manifest hash 不一致): auto は実行しない
    if [[ -d "$scrum_dir" ]] && [[ -d "$discovery_dir" ]] && [[ ! -f "$manifest" ]]; then
        echo "[WARN] .helix/discovery/ が既に存在し、migration manifest がありません。" >&2
        echo "       helix discovery migrate --status で状態を確認し、" >&2
        echo "       --merge-strategy [keep-dst|keep-src|abort] を明示して実行してください。" >&2
        # auto-migrate は実行しない (conflict は手動介入必須)
    fi
}

if [[ "$(python3 -c 'from cli.lib.discovery_compat import get_compat_stage; print(get_compat_stage())')" -ge 3 ]]; then
    _auto_migrate_if_safe
fi
```

> **P0-2 設計根拠**: `--merge-strategy keep-dst` 固定の auto-migrate は silent merge を引き起こす。conflict 検出時 (dst 存在 + manifest hash 不一致) は必ず手動 `--merge-strategy` 指定を要求する。

---

### §2.3 Stage activation 仕組み (P1-1 対応)

#### 2.3.1 activation source の決定的 source

**採用: 環境変数 + config file の 2 層構造。環境変数が優先。**

```
優先度: HELIX_DISCOVERY_COMPAT_STAGE (env) > .helix/config.yaml#discovery.compat_stage > デフォルト値
```

**環境変数**:
```bash
HELIX_DISCOVERY_COMPAT_STAGE=2   # Stage 2 を有効化 (値: 1, 2, 3, 4)
```

**config file** (`.helix/config.yaml`):
```yaml
discovery:
  compat_stage: 2   # 省略時は デフォルト値
```

**デフォルト値**: `1` (A1 完遂直後は Stage 1 のみ有効)

#### 2.3.2 Stage 別の動作変化

| Stage | `HELIX_DISCOVERY_COMPAT_STAGE` | 動作 |
|---|---|---|
| 1 (Alias) | 1 (default) | `helix scrum` → helix-scrum shim 実行。warning なし |
| 2 (Warning) | 2 | `helix scrum` 実行時に stderr deprecated warning 出力。plan_validator に `scrum` drive deprecation warn |
| 3 (Migration) | 3 | `.helix/scrum/` 存在時に `helix discovery` 起動で auto-migrate (P0-2 厳格化: dst なし / manifest hash 一致 の 2 条件のみ auto 許可、conflict 時は手動介入要求)。`helix scrum` は redirect |
| 4 (Removal) | 4 | `helix scrum` は `command not found` 相当エラー (削除は L7-helix-scrum-removal-plan) |

**注意**: Stage 4 の CLI 削除は本 PLAN スコープ外。`HELIX_DISCOVERY_COMPAT_STAGE=4` を設定した場合は "Stage 4 は L7-helix-scrum-removal-plan で管理されます" というメッセージを出して exit する stub のみ実装する。

#### 2.3.3 release 時の Stage 切替手順

Stage を上げる場合の標準手順:

```
1. ステージングで HELIX_DISCOVERY_COMPAT_STAGE=N+1 を設定
2. helix doctor で warn/fail 確認
3. telemetry / grep で旧 scrum 使用が N% 以下を確認 (Stage 3→4 は §9 の removal plan の条件に依存)
4. .helix/config.yaml の compat_stage を更新してコミット
5. リリースノートに Stage 変更を明記
```

#### 2.3.4 Stage 読み取り関数の実装 (cli/lib/discovery_compat.py に配置、P1-5)

> **P1-5 設計方針**: `get_compat_stage()` および phase/drive 変換関数は `cli/lib/discovery_compat.py` (新規) に配置する。`discovery_migrate.py` は data movement (copy / manifest / lock / verify) に閉じ、`discovery_compat.py` への import は許可する。

```python
# cli/lib/discovery_compat.py (新規、Sprint .6 で実装)

def get_compat_stage() -> int:
    """
    HELIX_DISCOVERY_COMPAT_STAGE env > .helix/config.yaml discovery.compat_stage > デフォルト 1
    """
    env_val = os.environ.get("HELIX_DISCOVERY_COMPAT_STAGE")
    if env_val is not None:
        try:
            stage = int(env_val)
            if stage not in (1, 2, 3, 4):
                raise ValueError(f"invalid stage: {stage}")
            return stage
        except ValueError as e:
            raise ValueError(f"HELIX_DISCOVERY_COMPAT_STAGE 不正値: {e}") from e
    config_path = Path(os.environ.get("HELIX_DIR", ".helix")) / "config.yaml"
    if config_path.exists():
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
        stage = config.get("discovery", {}).get("compat_stage", 1)
        if stage not in (1, 2, 3, 4):
            raise ValueError(f".helix/config.yaml discovery.compat_stage 不正値: {stage}")
        return stage
    return 1  # default

def is_drive_deprecated(drive: str) -> bool:
    """drive が非推奨かどうかを返す"""
    return drive in DEPRECATED_DRIVES

DEPRECATED_DRIVES: dict[str, str] = {
    "scrum": "discovery",   # 旧 drive → 推奨 drive のマッピング
}
```

---

### §2.4 S0-S4 → D0-D4 state machine 分離 (P2-5 対応)

#### 2.4.1 分離方針

**採用: 表示 layer のみ D0-D4 へ移行。DB state は migration 対象外。**

根拠:
- 既存 `helix.db` の state フィールドが `S0` / `S1` / `S2` / `S3` で記録されている
- DB migration は既存データの破壊リスクと migration コストが高い
- tests がDB の `S0-S3` を直接アサートしている件が多数存在する (変更コスト大)
- 表示のみ変える thin shim で十分な UX 改善が得られる

#### 2.4.2 実装: 表示 layer の D 変換

**`cli/lib/discovery_compat.py` に配置 (P1-1 / P1-5 対応)**:

> **P1-1 設計根拠**: `scrum_local.decide_loop()` は S3 を **decided** (Decide/Confirmed) として使用する実装になっている。S4 は DB state として存在しないため、D4 (Forward 接続) は DB state ではなく decide_result から派生して表示する。D4 を DB に書き込まない。

```python
# cli/lib/discovery_compat.py に追記 (Sprint .6 で実装)

# S-phase → D-phase 変換テーブル (P1-1 DB 実装と整合)
# S0-S3 は DB の実データ意味に基づいて定義
PHASE_DISPLAY_MAP = {
    "S0": "D0",  # Backlog 構築
    "S1": "D1",  # Sprint Plan
    "S2": "D2",  # PoC 実装 (Verify は S2 の sub-step として既存実装に合わせる)
    "S3": "D3",  # Decide/Confirmed (scrum_local.decide_loop() が S3 を decided として使用)
    # D4 (Forward 接続) は DB state にしない。decide_result から派生して表示する
    # 逆引き (ユーザー D-phase 入力 → DB write 用 S-phase)
    "D0": "S0", "D1": "S1", "D2": "S2", "D3": "S3",
    # D4 の DB write は禁止 (派生表示のみ)
}

def phase_to_display(phase: str) -> str:
    """DB の S-phase を表示用 D-phase に変換する。D4 は decide_result から派生して呼び出し側で生成する"""
    return PHASE_DISPLAY_MAP.get(phase, phase)

def display_to_phase(display: str) -> str:
    """ユーザー入力の D-phase を DB 書き込み用 S-phase に変換する。D4 は DB write 禁止 (ValueError を raise)"""
    if display == "D4":
        raise ValueError("D4 は DB state ではありません。decide_result から派生して表示します。")
    return PHASE_DISPLAY_MAP.get(display, display)
```

**適用箇所**:
- `cli/helix-discovery` の表示系コマンド (`backlog list`, `sprint show`, `decide`) の出力で `phase_to_display()` を呼ぶ
- ユーザーが `--phase D2` 等を指定した場合、`display_to_phase()` で S-phase に変換してから DB 検索/更新
- `helix doctor` の phase 表示にも適用

#### 2.4.3 DB state は変更しない (明示的除外) + D4 派生表示

- `helix.db` の `phase` カラム値は `S0-S3` のまま維持
- **D4 (Forward 接続) は DB state にしない**: `scrum_local.decide_loop()` が S3 を decided として使うため、D4 は `decide_result` フィールドから派生して表示レイヤーで生成する。DB には書き込まない
- migration script (§2.2) は DB には一切触れない (user data の `.helix/scrum/` dir のみ対象)
- 既存 pytest のアサートは変更しない (S-phase アサートのままで OK)
- D-phase の追加アサートが必要な場合は `phase_to_display()` 経由のアサートとして test_discovery_migrate.py に追加
- `--phase D4` のユーザー入力は `display_to_phase()` で ValueError を raise して使用禁止を明示

### §2.5 discovery_compat.py / discovery_migrate.py 責務分離 (P1-5)

**問題**: `HELIX_DISCOVERY_COMPAT_STAGE` などの stage/drive/phase 変換を `discovery_migrate.py` に置くと module 依存が肥大化し、CLI や plan_validator が migration 本体コードを import する形になる。

**採用: `cli/lib/discovery_compat.py` (新規) に変換系を分離**

| module | 責務 | 公開関数 |
|---|---|---|
| `cli/lib/discovery_compat.py` | stage/drive/phase 表示変換 (変換ロジックのみ、I/O なし) | `get_compat_stage()` / `phase_to_display()` / `display_to_phase()` / `is_drive_deprecated()` |
| `cli/lib/discovery_migrate.py` | data movement のみ (copy / manifest / lock / verify / pseudo-transaction) | `migrate()` / `generate_manifest()` / `verify_manifest()` / `acquire_lock()` / `release_lock()` / `check_conflict()` |

**依存方向**:
```
cli/helix-discovery  ──import──→  discovery_compat.py (stage 判定、phase 変換)
cli/helix-discovery  ──import──→  discovery_migrate.py (migrate 実行)
discovery_migrate.py ──import──→  discovery_compat.py (phase 変換のみ、逆は禁止)
cli/lib/plan_validator.py ──import──→  discovery_compat.py (deprecated drive 判定)
```

**Sprint 対応**:
- Sprint .2: `discovery_migrate.py` — migration 本体実装 (data movement に閉じる)
- Sprint .6: `discovery_compat.py` — 変換系実装 (get_compat_stage / phase_to_display / display_to_phase / is_drive_deprecated)

**注意**: `discovery_migrate.py` から `discovery_compat.py` への import は許可するが、循環 import になる逆方向 (compat → migrate) は禁止。

---

### §2.6 path 正規化 + symlink fail-close (P1-6)

`--src` / `--dst` 引数の安全検証を `discover_migrate.py` の入口で実施する:

```python
def _validate_path(p: Path, project_root: Path) -> Path:
    """
    project root 配下 .helix/{scrum,discovery} に正規化し、symlink は fail-close で拒否する。
    特殊ファイル (FIFO / device / socket) の含むディレクトリも fail-close。
    """
    resolved = p.resolve(strict=False)
    expected_parents = [
        project_root / ".helix" / "scrum",
        project_root / ".helix" / "discovery",
    ]
    if not any(resolved == ep or ep in resolved.parents for ep in expected_parents):
        raise ValueError(
            f"path outside .helix/{{scrum,discovery}}: {p}\n"
            f"  (resolved: {resolved})"
        )
    # symlink fail-close: p 自身または親ディレクトリが symlink なら拒否
    if p.is_symlink() or any(parent.is_symlink() for parent in p.parents):
        raise ValueError(f"symlink not allowed: {p}")
    return resolved

def _check_special_files(directory: Path) -> None:
    """FIFO / device / socket を含むディレクトリは migration 対象外 (fail-close)"""
    for entry in directory.rglob("*"):
        if entry.stat().st_mode & 0o170000 not in (0o100000, 0o040000):
            # regular file / directory 以外は拒否
            raise ValueError(f"special file not allowed in migration source: {entry}")
```

この検証は `migrate()` の引数受け取り直後に実行し、ロック取得前に完了する。

---

## §3 影響範囲 inventory

> **本 PLAN は A1 完遂後の後段。A1 で変更された箇所は §3 の「A1 済」列に明示する。**

### 3.1 plan_validator.py 変更範囲

| 変更内容 | ファイル | Sprint |
|---|---|---|
| `VALID_DRIVES` に `"discovery"` 追加 | cli/lib/plan_validator.py | .4 |
| `DEPRECATED_DRIVES = {"scrum": "discovery"}` 追加 | cli/lib/plan_validator.py | .4 |
| `validate_frontmatter()` に deprecated drive warn 追加 | cli/lib/plan_validator.py | .4 |
| `"scrum"` は VALID_DRIVES に残存 (Stage 4 まで削除しない) | cli/lib/plan_validator.py | .4 |

### 3.2 cli/lib/discovery_migrate.py (新規) — data movement 専門 (P1-5)

| 機能 | 説明 |
|---|---|
| `_validate_path(p, project_root)` | path 正規化 + symlink fail-close + project root 境界検証 (§2.6) |
| `_check_special_files(directory)` | FIFO / device / socket を含むディレクトリの fail-close 検証 (§2.6) |
| `generate_manifest(src)` | migration 前の file list + (sha256, size_bytes) 生成 |
| `verify_manifest(dst, manifest)` | コピー後の manifest 照合 (count + hash + size) |
| `acquire_lock()` / `release_lock()` | flock ベースの並行 lock |
| `migrate(src, dst, strategy, dry_run, force, auto)` | pseudo-transaction 保全設計準拠の migration 本体 (§2.2.2) |
| `check_conflict(dst)` | dst conflict ケース判定 (§2.2.3) |
| `merge_directories(src, dst, strategy)` | pseudo-transaction merge 方針適用 (§2.2.2 step 5M) |

### 3.2b cli/lib/discovery_compat.py (新規) — 変換系専門 (P1-5)

| 機能 | 説明 |
|---|---|
| `get_compat_stage()` | Stage activation source 読み取り: env > config > default 1 (§2.3.4) |
| `DEPRECATED_DRIVES` | deprecated drive → 推奨 drive マッピング dict |
| `is_drive_deprecated(drive)` | drive が非推奨かどうかを返す |
| `PHASE_DISPLAY_MAP` | S/D phase 変換テーブル (P1-1 整合: S3=Decide/Confirmed、D4 は DB state なし) |
| `phase_to_display(phase)` | DB の S-phase を表示用 D-phase に変換 |
| `display_to_phase(display)` | ユーザー入力の D-phase を DB 書き込み用 S-phase に変換 (D4 は ValueError) |

### 3.3 cli/helix-discovery 変更範囲

| 変更内容 | 対象 | Sprint | A1 状態 |
|---|---|---|---|
| `migrate` subcommand 追加 (`--dry-run` / `--status` / `--auto` / `--merge-strategy`) | cli/helix-discovery | .3 | A1 未実装 |
| Stage 2 warning 実装 (get_compat_stage() 呼び出し) | cli/helix-discovery | .6 | A1 未実装 |
| Stage 3 auto-migrate trigger 追加 | cli/helix-discovery | .6 | A1 未実装 |
| `--phase` 引数の D-phase 受入 (display_to_phase 変換) | cli/helix-discovery | .7 | A1 未実装 |
| backlog list / sprint show の phase 表示 D 変換 | cli/helix-discovery | .7 | A1 未実装 |

### 3.4 phase.yaml + helix doctor + command_mapper

| 対象 | 変更内容 | Sprint |
|---|---|---|
| `.helix/phase.yaml` 読み込み | `current_mode: scrum` → `discovery` に正規化する compat shim (cli/lib 側) | .5 |
| `helix doctor` | drive deprecation warn + stage mismatch warn 追加 | .5 |
| helix router (command_mapper) | A1 完遂済のため変更不要 | — |

### 3.5 test 対象 (P2-4 対応: test file 分割)

| テストファイル | 対象層 | 内容 | Sprint |
|---|---|---|---|
| `cli/lib/tests/test_discovery_compat.py` (新規) | **unit** (I/O なし) | `phase_to_display` / `display_to_phase` (D4 ValueError) / `get_compat_stage` (env / config / default) / `is_drive_deprecated` | .6 |
| `cli/lib/tests/test_discovery_migrate.py` (新規) | **filesystem integration** | migrate 全 case (正常 / dry-run / status / lock / conflict abort / conflict keep-dst / conflict keep-src / idempotent / hash mismatch / partial cleanup / symlink reject / FIFO reject / smoke) | .2-.3 |
| `cli/lib/tests/test_plan_validator_drive.py` (新規 or 既存に追加) | **unit** | discovery drive valid / scrum drive deprecated warn (exit 0) / DEPRECATED_DRIVES mapping | .4 |
| `cli/helix-discovery --migrate` bats (新規 or 既存に追加) | **CLI subprocess** (bats + pytest subprocess) | `--dry-run` / `--status` / `--auto` stage-safe / Stage 3 auto-migrate 条件分岐 | .3 / .6 |

---

## §4 Sprint 分割

### Sprint .1: design doc 起草

**目標**: `docs/v2/L7-design/` と `docs/v2/L7-test-design/` に 4 artifact を作成。

**生成物**:
- `docs/v2/L7-design/L7-scrum-to-discovery-migration-enum-design.md`
- `docs/v2/L7-test-design/L7-scrum-to-discovery-migration-enum-test-design.md`

**内容**:
- 設計 doc: §2.1 drive enum / §2.2 migration 保全 / §2.3 Stage activation / §2.4 D-phase 分離 の設計決定を artifact として永続化
- テスト設計 doc: §5 DoD の受入条件を test case ID 付きで列挙 (MT-001〜MT-030)

**受入条件**: 両 doc が存在し、双方向 reference (§10 参照) が設定されていること。

---

### Sprint .2: cli/lib/discovery_migrate.py 実装 (migration 本体)

**目標**: §2.2 保全設計準拠の migration Python モジュール実装。

**実装対象**:
- `get_compat_stage()` + `PHASE_DISPLAY_MAP` + phase 変換関数
- `generate_manifest()` + `verify_manifest()`
- `acquire_lock()` + `release_lock()`
- `migrate()` (§2.2.2 フロー全ステップ)
- `check_conflict()` + `merge_directories()`

**テスト先行 (TDD)**:
```python
# test_discovery_migrate.py に先行 stub test:
def test_migrate_normal_case(): ...
def test_migrate_dry_run(): ...
def test_migrate_idempotent(): ...
def test_migrate_lock_conflict(): ...
def test_migrate_hash_mismatch_cleanup(): ...
def test_migrate_partial_copy_cleanup(): ...
def test_migrate_dst_conflict_abort(): ...
def test_migrate_dst_conflict_keep_dst(): ...
def test_migrate_dst_conflict_keep_src(): ...
def test_migrate_smoke(): ...
```

**受入条件**: `python3 -m py_compile cli/lib/discovery_migrate.py` PASS + 上記 test 全 PASS。

---

### Sprint .3: `helix discovery migrate` subcommand 実装

**目標**: `cli/helix-discovery` に `migrate` subcommand を追加。

**サブコマンド仕様**:

```
helix discovery migrate [options]

Options:
  --dry-run          実際のコピーは行わず、コピー対象ファイルリストと推定サイズを表示
  --status           migrate 完了済み / 未実施 / 部分完了 (tmp 残存) を表示
  --auto             確認なしで自動実行 (Stage 3 auto-trigger 用)
  --force            既に migrate 完了済みでも再実行 (idempotent skip を無効化)
  --merge-strategy   [keep-dst|keep-src|abort] dst conflict 時の方針 (default: abort)
  --src              src dir (default: .helix/scrum/)
  --dst              dst dir (default: .helix/discovery/)

Examples:
  helix discovery migrate --dry-run        # 移行対象確認
  helix discovery migrate --status         # 移行状態確認
  helix discovery migrate                  # 移行実行 (conflict 時は abort)
  helix discovery migrate --merge-strategy keep-dst  # dst 優先で merge
```

**受入条件**: `bash -n cli/helix-discovery` PASS + `helix discovery migrate --help` 出力確認 + `helix commands check` PASS。

---

### Sprint .4: plan_validator.py VALID_DRIVES retrofit

**目標**: §2.1.2 の drive enum 移行設計を plan_validator に反映。

**変更内容**:
1. `VALID_DRIVES` に `"discovery"` 追加
2. `DEPRECATED_DRIVES` は `cli/lib/discovery_compat.py` から import (重複定義しない)
3. `validate_frontmatter()` 内に deprecated drive 検出 + warn 追加 (P1-2 実装整合):

```python
# plan_validator.py の実装パターン (warn-only、exit 0 維持)
from cli.lib.discovery_compat import DEPRECATED_DRIVES, is_drive_deprecated

# validate_frontmatter() 内:
if is_drive_deprecated(frontmatter.drive):
    new_drive = DEPRECATED_DRIVES[frontmatter.drive]
    # 実装は Finding ではなく warnings リスト方式 (既存 plan_validator.py の warn-only pattern に合わせる)
    warnings.append(
        f"DEPRECATED_DRIVES: '{frontmatter.drive}' は将来削除予定 (Stage 4)、"
        f"drive: {new_drive} に移行推奨"
    )
```

**`DEPRECATED_DRIVES` warning 出力仕様** (P1-2 exit code 明示):
- 出力形式: `"DEPRECATED_DRIVES: '<drive>' は将来削除予定 (Stage 4)、drive: <new_drive> に移行推奨"`
- exit code: **0** (warn-only、fail-close しない)
- Stage 4 での fail-close 昇格は L7-helix-scrum-removal-plan 担当

4. `helix size --drive scrum` の内部変換: `--drive scrum` 指定時に discovery に変換してから処理。warn を stderr に出力。

**受入条件**:
- `drive: discovery` の PLAN が plan_validator でエラーなし
- `drive: scrum` の PLAN が WARN を出し PASS (fail-close ではない)
- 既存 VALID_DRIVES テストが全 PASS

---

### Sprint .5: phase.yaml / helix doctor compat 更新

**目標**: §2.1.4 の compat 更新を実施。

**変更内容**:
1. `phase.yaml` 読み込み compat shim: `current_mode: scrum` → `discovery` 正規化
2. `helix doctor` に drive deprecation warn と Stage mismatch warn 追加

**受入条件**: `helix doctor` 実行で scrum drive PLAN が warn として表示される。`current_mode: scrum` の phase.yaml を読んだ場合に `discovery` として扱われる。

---

### Sprint .6: cli/lib/discovery_compat.py 実装 + Stage activation CLI 組み込み (P1-5)

**目標**: §2.5 に基づき `cli/lib/discovery_compat.py` を新規実装し、Stage activation を cli/helix-discovery と cli/helix-scrum shim に組み込む。

**変更内容**:
1. `cli/lib/discovery_compat.py` 新規実装:
   - `get_compat_stage()` (§2.3.4、env > config > default 1)
   - `DEPRECATED_DRIVES`, `is_drive_deprecated()`
   - `PHASE_DISPLAY_MAP`, `phase_to_display()`, `display_to_phase()` (P1-1 整合: D4 は ValueError)
2. Stage 2 の deprecated warning 出力ロジック (cli/helix-scrum shim、`get_compat_stage()` を import)
3. Stage 3 の auto-migrate trigger (cli/helix-discovery 先頭、P0-2 厳格化版 `_auto_migrate_if_safe()`)
4. Stage 4 stub (L7-helix-scrum-removal-plan へ委譲メッセージ)

**受入条件**:
- `python3 -m py_compile cli/lib/discovery_compat.py` PASS
- `HELIX_DISCOVERY_COMPAT_STAGE=2 helix scrum backlog list` が warning を stderr に出力して正常実行
- `HELIX_DISCOVERY_COMPAT_STAGE=3 helix discovery backlog list` が `.helix/scrum/` 存在 (dst なし) 時に auto-migrate を実行
- `HELIX_DISCOVERY_COMPAT_STAGE=3 helix discovery backlog list` が `.helix/scrum/` + `.helix/discovery/` (conflict) 時は **auto-migrate を実行せず** 手動介入要求メッセージを表示
- `HELIX_DISCOVERY_COMPAT_STAGE=4 helix scrum` が "L7-helix-scrum-removal-plan で管理" メッセージを出して exit 1

---

### Sprint .7: S0-S4 → D0-D4 state machine 分離

**目標**: §2.4 の表示 layer D-phase 変換を CLI に組み込む。

**変更内容**:
1. `cli/helix-discovery` の backlog list / sprint show / decide コマンドの出力で `phase_to_display()` 呼び出し
2. `--phase D2` 等のユーザー入力で `display_to_phase()` 変換
3. `helix doctor` の phase 表示に D 変換適用

**受入条件**:
- `helix discovery backlog list` の Phase 列が D0-D4 で表示
- `helix discovery sprint plan --phase D1` が正常実行 (DB は S1 で書き込み)
- 既存 test の S-phase アサートは変更なし。D-phase アサートのみ追加

---

## §5 DoD + 受入条件

### 機能受入条件

| ID | 条件 | 対応 Sprint |
|---|---|---|
| AC-1 | `drive: discovery` の PLAN が plan_validator でエラーなし | .4 |
| AC-2 | `drive: scrum` の PLAN が WARN を出し pass (fail-close なし) | .4 |
| AC-3 | `helix discovery migrate --dry-run` が対象ファイルリストを出力して exit 0 | .3 |
| AC-4 | `helix discovery migrate --status` が状態 (complete/pending/partial) を出力 | .3 |
| AC-5 | `helix discovery migrate` の正常実行: manifest 照合 PASS + src → dst 完全コピー + README.deprecated 配置 | .2-.3 |
| AC-6 | 部分コピー後 interrupt → 再実行で tmp cleanup + 完全再コピー成功 | .2 |
| AC-7 | hash mismatch 検出時に dst.tmp cleanup + src 無傷 + exit 1 | .2 |
| AC-8 | lock 競合時に "別の migrate が実行中" エラーで exit 1 | .2 |
| AC-9 | dst conflict (backlog.yaml 存在) + `--merge-strategy` 未指定 で **abort** (exit 2 + 手動介入要求メッセージ) | .2 |
| AC-9b | dst conflict + `--merge-strategy keep-dst` で pseudo-transaction merge 成功 (dst.backup-* 生成確認) | .2 |
| AC-10 | dst conflict + `--merge-strategy keep-src` で src 優先 merge 成功 | .2 |
| AC-10b | merge 失敗時 (backup rename 失敗): dst.backup-* → dst restore + dst.tmp cleanup 確認 | .2 |
| AC-11 | idempotent: 2 回目 migrate は skip (manifest hash 一致確認) | .2 |
| AC-11b | Stage 3 auto-migrate: dst なし → auto 実行、dst 存在 + conflict → 手動介入要求 (auto 不実行) | .6 |
| AC-11c | symlink / FIFO / device が src に含まれる場合 fail-close (exit 2) | .2 |
| AC-11d | EXDEV (異 FS) 検出時 fail-close (exit 2 + 設定異常メッセージ) | .2 |
| AC-12 | `HELIX_DISCOVERY_COMPAT_STAGE=2 helix scrum` が warning + 正常実行 | .6 |
| AC-13 | `HELIX_DISCOVERY_COMPAT_STAGE=3 helix discovery` が `.helix/scrum/` 存在時に auto-migrate | .6 |
| AC-14 | `HELIX_DISCOVERY_COMPAT_STAGE=1` (default) では warning なし | .6 |
| AC-15 | `helix discovery backlog list` の Phase 列が D0-D4 表示 | .7 |
| AC-16 | `--phase D2` 指定で正常実行 (DB write は S2) | .7 |
| AC-17 | `helix doctor` に drive deprecation warn が表示 | .5 |
| AC-18 | `.helix/phase.yaml` の `current_mode: scrum` が `discovery` に正規化 | .5 |

### 機械チェック受入条件

| ID | 条件 |
|---|---|
| MC-1 | `python3 -m py_compile cli/lib/discovery_migrate.py` PASS |
| MC-2 | `bash -n cli/helix-discovery` PASS |
| MC-3 | `shellcheck cli/helix-discovery` (SC2034/SC2086 以外) PASS |
| MC-4 | `yamllint .helix/config.yaml` (存在する場合) PASS |
| MC-5 | `pytest cli/lib/tests/test_discovery_migrate.py -v` 全 PASS |
| MC-6 | `pytest cli/lib/tests/ -q` 回帰全 PASS (既存 test 含む) |
| MC-7 | `helix commands check` PASS |
| MC-8 | `helix doctor` で本 PLAN 由来の fail なし (warn は許容) |

---

## §6 risk + mitigation

| risk | 影響 | 確率 | mitigation |
|---|---|---|---|
| **data loss (merge case)**: pseudo-transaction の backup rename 後に dst.tmp → dst rename が失敗し、dst が空になる | P0 | 低 (backup → restore で復旧) | §2.2.2 step 5M d の restore ロジックで自動復旧。backup rename 自体が失敗した場合は dst.tmp cleanup + exit 1 (dst は無傷) |
| **data loss (non-merge case)**: migration 中の interrupt でユーザーデータが消滅 | P0 | 低 (正常系は発生しない) | dst.tmp + manifest 検証 + src 残存方針。src は migrate 完了後も削除しない (§2.2.2 step 9 は README.deprecated のみ配置) |
| **P0-2 silent merge**: Stage 3 auto-migrate が conflict 時に keep-dst で上書きする | P0 | 低 (P0-2 修正後) | §2.2.4 の `_auto_migrate_if_safe()` で conflict 検出時は auto 不実行 + 手動介入要求。auto は dst なし / manifest hash 一致の 2 条件のみ |
| **EXDEV (異 FS)**: `dst.tmp → dst` が異なるファイルシステム上で発生 | P1 | 低 (通常 .helix/ は同一 FS) | **fail-close** (exit 2 + 設定異常メッセージ)。P2-2 対応: `mv + rm` fallback は採用しない。.helix/ を同一 FS 上に配置することを設定要件とする |
| **hash collision**: sha256 hash が偶然一致して破損ファイルを PASS とする | P2 | 極低 | size (bytes) も合わせて照合することで実質ゼロ |
| **Stage activation 不一致**: env と config の Stage が噛み合わず、Stage 2 が production で誤発火 | P1 | 中 (設定ミス) | デフォルト値を Stage 1 に設定 (§2.3.1)。Stage を上げる前に staging で動作確認を手順化 (§2.3.3) |
| **S0-S4 DB state が D-phase と不一致**: 表示が D0-D4 になっても DB が S0-S3 のままで混乱 | P2 | 低 (分離設計で正常) | `phase_to_display()` を通じた thin shim 設計を文書化 (§2.4 参照)。DB を変更しない設計を PLAN に明示 |
| **A1 との scope 重複**: migrate 関連のコードが A1 で一部実装されて衝突 | P1 | 低 (A1 では cp -r 実装なし) | 本 PLAN §0 scope 境界表でA1 が migrate を実装しないことを明示。A1 レビュー時に確認 |
| **plan_validator DEPRECATED_DRIVES 追加で既存 test fail**: scrum drive が warn になることで既存 test の assertion が変わる | P2 | 中 | Sprint .4 で既存テストを確認し、warn 対応の assertion に更新する carry を明示 |
| **L7-helix-scrum-removal-plan stub 未起票**: removal timeline が宙に浮く | P2 | 低 | Sprint .8 で stub 起票を DoD に含める (§9 参照) |

---

## §7 V3 接続契約 (Stage activation source + migration trigger)

### 7.1 外部との接続インターフェース (P1-5 分離後)

本 PLAN が提供するインターフェースは以下の 2 module。後続 PLAN (L7-helix-scrum-removal-plan 等) は本 PLAN の成果物に依存する。

```python
# cli/lib/discovery_compat.py が公開する契約 (変換系、P1-5)

# 1. Stage activation source
def get_compat_stage() -> int:
    """
    返り値: 1 | 2 | 3 | 4
    source: HELIX_DISCOVERY_COMPAT_STAGE env > .helix/config.yaml > 1 (default)
    例外: ValueError (不正値)
    """

# 2. Phase 変換 (P1-1 整合: D4 は ValueError)
def phase_to_display(phase: str) -> str:
    """DB の S-phase → 表示用 D-phase (S0→D0, S1→D1, S2→D2, S3→D3)。D4 は呼び出し側で decide_result から生成"""

def display_to_phase(display: str) -> str:
    """ユーザー入力の D-phase → DB 書き込み用 S-phase。D4 指定時は ValueError"""

# 3. Deprecated drive 判定
DEPRECATED_DRIVES: dict[str, str]  # {"scrum": "discovery"}
def is_drive_deprecated(drive: str) -> bool: ...


# cli/lib/discovery_migrate.py が公開する契約 (data movement 専門、P1-5)

# 4. migration 実行
def migrate(
    src: Path,
    dst: Path,
    strategy: Literal["keep-dst", "keep-src", "abort"] = "abort",
    dry_run: bool = False,
    force: bool = False,
    auto: bool = False,
) -> MigrateResult:
    """
    P0-1: dst non-empty + strategy 未指定 → abort (exit 2)
    P0-1: merge case → pseudo-transaction (dst.tmp 構築 → dst.backup-<ts> 退避 → rename)
    P0-2: auto=True 時は dst なし / manifest hash 一致 の 2 条件のみ実行、conflict は abort
    返り値: MigrateResult(status, files_copied, bytes_copied, errors)
    status: "complete" | "skipped" | "dry_run" | "failed" | "aborted"
    """
```

### 7.2 Stage 3 auto-trigger の発火条件 (P0-2 厳格化後)

```bash
# cli/helix-discovery が Stage 3 で使用する発火条件 (§2.2.4 の _auto_migrate_if_safe() 参照):
# 条件 1: dst なし → auto 実行
# 条件 2: manifest hash 一致 → auto 実行 (idempotent)
# conflict (dst 存在 + non-empty + manifest hash 不一致) → 手動介入要求、auto 不実行
[ "$(python3 -c 'from cli.lib.discovery_compat import get_compat_stage; print(get_compat_stage())')" -ge 3 ] \
  && _auto_migrate_if_safe
```

### 7.3 removal plan への委譲条件

`L7-helix-scrum-removal-plan` は以下の条件を確認して Stage 4 へ移行する:
1. `HELIX_DISCOVERY_COMPAT_STAGE=3` の状態で全ユーザーの migration 完了を telemetry / grep で確認
2. `helix doctor` で `drive: scrum` の PLAN が 0 件になっていること
3. `cli/helix-scrum` へのアクセスが閾値以下 (log 確認)

これらは本 PLAN では stub として記述し、実際の条件数値は removal plan で定義する。

---

## §8 関連 doc + 関連 PLAN

| 種別 | 参照先 | 関係 |
|---|---|---|
| 前段 PLAN (A1) | [L7-scrum-to-discovery-renameplan.md](./L7-scrum-to-discovery-renameplan.md) | A1 完遂後に本 PLAN 着手。CLI binary は A1 が生成 |
| 正本設計 | HELIX-workflows/helix-process/discovery-workflow.md | PLAN kind / drive / フェーズ定義の正本 |
| 旧 Scrum workflow | HELIX-workflows/helix-process/scrum-workflow.md | legacy 互換 + 責務整理の参照 |
| plan_validator | cli/lib/plan_validator.py | §3.1 変更対象。VALID_DRIVES 正本 |
| HELIX_CORE.md §HELIX Scrum | helix/HELIX_CORE.md (line ~245) | S0-S4 → D0-D4 の概念整理の参照元 |
| SKILL_MAP.md §HELIX Scrum | skills/SKILL_MAP.md (line ~247) | "将来の rename は別 PLAN carry" 根拠 |
| parent PLAN | L7-helix-workflows-parent-acceptedplan | 親工程管理 PLAN |
| 後続 PLAN (stub) | L7-helix-scrum-removal-plan (§9 で起票) | Stage 4 removal の担当 PLAN |
| ADR scope 外 (明示) | ADR-041 / ADR-042 / ADR-043 | **本 PLAN は ADR-041/042/043 の影響範囲外**。本 PLAN は drive enum 正規化 + runtime dir migration のみ担当。route_engine 拡張 (drift_type / recommended_command / Mode enum) は別 PLAN C' 担当 |

---

## §9 carry + 残課題

### 本 PLAN 完遂後に別 PLAN で管理する carry

| ID | carry 内容 | 担当 PLAN | 優先度 |
|---|---|---|---|
| C-1 | **`L7-helix-scrum-removal-plan` stub 起票** (Stage 4 entry 条件・telemetry 確認条件・fail-close 昇格条件を定義) | Sprint .8 で stub 起票。詳細実装は removal plan 担当 | P1 |
| C-2 | 既存 PLAN の `drive: scrum` を `drive: discovery` に一括 retrofit | L7-helix-scrum-removal-plan Sprint .1 | P2 |
| C-3 | `drive: scrum` の DEPRECATED_DRIVES warn を fail-close に昇格 (Stage 4) | L7-helix-scrum-removal-plan | P2 |
| C-4 | `cli/helix-scrum` CLI binary の削除 + router エントリ削除 | L7-helix-scrum-removal-plan | P2 |
| C-5 | DB state migration (S-phase → D-phase) の実施可否判断 (本 PLAN では non-target、将来判断) | 別 ADR / PLAN | P3 |
| C-6 | `skills/agent-skills/helix-scrum/SKILL.md` の `helix_layer: [S0-S4]` → `[D0-D4]` 更新 | A1 範囲外の確認。A1 commit 後に確認、未更新なら追加 carry | P2 |

### `L7-helix-scrum-removal-plan` stub の最小構成 (Sprint .8 で起票)

```markdown
---
plan_id: L7-helix-scrum-removal-plan
name: L7-helix-scrum-removal-plan
description: helix-scrum CLI の Stage 4 removal + drive:scrum PLAN retrofit + DB compat 終了
status: stub
process_layer: L7
kind: impl
drive: be
size: M
priority: P3
created: 2026-05-24
---

## §0 stub 宣言

本 PLAN は L7-scrum-to-discovery-migration-enumplan §9 C-1 から派生した stub。
実装着手条件 (Stage 4 entry 条件):
- HELIX_DISCOVERY_COMPAT_STAGE=3 で全ユーザー migration 完了確認 (telemetry)
- helix doctor で drive: scrum の PLAN が 0 件
- cli/helix-scrum へのアクセスが X% 以下 (log 閾値は実装時に定義)

実装内容 (着手時に詳細化):
- drive: scrum → discovery 一括 retrofit (docs/plans/ 全件)
- DEPRECATED_DRIVES warn → fail-close 昇格
- cli/helix-scrum binary 削除 + router エントリ削除
- .helix/scrum/ 旧 dir サポート終了 (README.deprecated のみ残す)
```

---

## §10 4 artifact 双方向 trace

HELIX V-model 4 artifact 双方向 trace 原則 (`HELIX_CORE.md §設計⇔テスト対応`) に準拠する。

```
① 設計 doc                          ←対応→  ③ テスト設計 doc
docs/v2/L7-design/                           docs/v2/L7-test-design/
L7-scrum-to-discovery-migration-            L7-scrum-to-discovery-migration-
  enum-design.md                              enum-test-design.md
         ↓ 実装                                       ↓ 実装
② 実装コード                        ←対応→  ④ テストコード
cli/lib/discovery_migrate.py                 cli/lib/tests/test_discovery_migrate.py
cli/helix-discovery (migrate+Stage)         cli/lib/tests/test_plan_validator_drive.py
cli/lib/plan_validator.py (retrofit)        cli/lib/tests/test_phase_display.py
```

### trace reference 明示

| Artifact | 対応する artifact | reference 方法 |
|---|---|---|
| ① 設計 doc | ③ テスト設計 doc | `# テスト設計: docs/v2/L7-test-design/L7-scrum-to-discovery-migration-enum-test-design.md` |
| ① 設計 doc | ② 実装コード | `# 実装: cli/lib/discovery_migrate.py, cli/helix-discovery, cli/lib/plan_validator.py` |
| ② 実装コード | ① 設計 doc | docstring `# 契約: docs/v2/L7-design/L7-scrum-to-discovery-migration-enum-design.md §2.X` |
| ③ テスト設計 doc | ① 設計 doc | `# 対象設計: docs/v2/L7-design/L7-scrum-to-discovery-migration-enum-design.md` |
| ③ テスト設計 doc | ④ テストコード | `# テスト実装: cli/lib/tests/test_discovery_migrate.py MT-001〜MT-030` |
| ④ テストコード | ③ テスト設計 doc | docstring `# DoD 検証: L7-scrum-to-discovery-migration-enum-test-design.md MT-XXX` |

### 4 artifact 存在確認 (Sprint .1 完了後にチェック)

```bash
# 4 artifact 存在確認スクリプト:
ls docs/v2/L7-design/L7-scrum-to-discovery-migration-enum-design.md && echo "① OK"
ls cli/lib/discovery_migrate.py 2>/dev/null && echo "② OK" || echo "② pending (Sprint .2 以降)"
ls docs/v2/L7-test-design/L7-scrum-to-discovery-migration-enum-test-design.md && echo "③ OK"
ls cli/lib/tests/test_discovery_migrate.py 2>/dev/null && echo "④ OK" || echo "④ pending (Sprint .2 以降)"
```

---

*本 PLAN は A1 (L7-scrum-to-discovery-renameplan) 完遂後に着手する。A1 が Stage 1 (CLI alias) を担い、本 A2 が Stage 2-4 (runtime migration + enum + Stage activation) を担う。scope 重複なし。*
