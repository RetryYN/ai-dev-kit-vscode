---
title: HELIX らせん式 (Spiral) 運用マニュアル
audience: [Operator, PO, PM, TL]
status: draft
created: 2026-05-16
related:
  - PLAN-027-helix-spiral-entries-links
  - PLAN-069-g3-entry-blocker-resolution
  - docs/v2/L2-MASTER.md (§9.5 らせん式)
---

# HELIX らせん式 (Spiral) 運用マニュアル

## §1 概念: DNA 二重らせん構造との対応

### 1.1 HELIX 命名由来

HELIX (Hierarchical Execution and Learning Integration eXperimental framework) の名称は、DNA 二重らせん (Double Helix) 構造に由来する。

DNA 二重らせんは 2 本の strand (鎖) が塩基対で結合し、時間軸に沿って螺旋状に自己組織化する。  
HELIX は以下の 2 strand をそれぞれ対応させる。

| DNA 構造 | HELIX 対応 |
|---|---|
| Strand 1 (テンプレート鎖) | **artifact strand**: 成果物の累積 (D-API / D-DB / D-CONTRACT / code) |
| Strand 2 (コード鎖) | **record strand**: 各 DB event の累積 (entries / links / detector_runs) |
| 塩基対 | **実行者 (Actor)**: PM / TL / SE / PE / PMO / PO が 2 strand を繋ぐ |
| 1 回転 | **1 Sprint**: design artifact pair 1 組が freeze するサイクル |
| 時間軸 | **自己組織化**: 失敗 → memory feedback → 仕組み化のループ |

### 1.2 二重らせんの意味

「成果物を作る」だけでは片方の strand に過ぎない。  
「記録が蓄積し、detector が矛盾を検出し、実行者がフィードバックを受ける」ことで 2 本の strand が噛み合う。

これが HELIX の本質的な価値連鎖: `成果物 (artifact strand) × 記録 (record strand) = 判断の再現可能な蓄積`。

### 1.3 らせん式の 3 軸構造

```
[ 成果物 (artifact strand) ]
  D-API / D-DB / D-CONTRACT
  code_index / design_sprint_entries
        ↕ 実行者 (Actor)
      PM / TL / SE / PE / PMO / PO
        ↕ 記録 (record strand)
  entries / links / detector_runs
  cost_log / session_telemetry
```

ワークフロー式順序: **成果物 → 実行者 → 記録**  
成果物がなければ実行者は動けない。記録は成果物と実行者の後段に置く。DB 設計は最後段。

---

## §2 entries テーブル運用

### 2.1 entries テーブルの役割

`entries` テーブル (helix.db v17+) は、Sprint 内で artifact が作成・更新された事実を 1 行 1 件として蓄積する。  
`code_index` の「コードの存在を記録する」用途と異なり、`entries` は「設計成果物の生成・遷移を記録する」用途。

### 2.2 insert タイミング

各 Sprint で以下の artifact を作成または更新したとき、`entries` に insert する。

| artifact kind | insert タイミング | domain_kind |
|---|---|---|
| D-API draft | SprintA (L3 D-API 起票) | design |
| D-DB draft | SprintB (L3 D-DB 起票) | schema |
| D-CONTRACT draft | SprintC (L3 D-CONTRACT 起票) | design |
| D-API 拡張 draft | SprintE (L3 D-API 拡張) | design |
| D-DB 拡張 draft | SprintF (L3 D-DB 拡張) | schema |
| PLAN.md | PLAN 起票時 | plan |
| test baseline | QA baseline 確定時 | test |
| code implementation | L4 Sprint 実装完了時 | code |

### 2.3 6 軸メタデータ

`entries` の 1 行は以下 6 軸メタデータを持つ。

| 軸名 | 型 | 意味 | 例 |
|---|---|---|---|
| `origin` | text | 記録の起点 | `sprint` / `manual` / `seed` |
| `lifecycle` | text | ライフサイクル段階 | `initial` / `addition` / `modification` / `migration` / `deprecation` / `removed` |
| `domain_kind` | text | 技術領域 | `design` / `plan` / `code` / `schema` / `test` / `review` / `evidence` |
| `pair` | text | 対応ペア ID | `design_sprint_entries.id` 等 |
| `direction` | text | 流れ方向 | `forward` / `reverse` / `forward_after_reverse` |
| `source` | text | 起源ファイルパス | `docs/v2/L3-detailed-design/D-API/D-API-draft.md` |

### 2.4 CLI 操作

```bash
# entries 検索
helix entry search --domain-kind design --lifecycle initial

# entries 詳細表示
helix entry show <entry_id>

# entries 統計
helix entry stats --by domain

# entries 検証 (pair 漏れ / link 欠落 を検出)
helix entry verify
```

### 2.5 D-API 起票時の具体的手順

1. D-API draft を作成 (`docs/v2/L3-detailed-design/D-API/D-API-draft.md`)
2. `helix entry link-add` で artifact の link を登録（§3 参照）
3. `helix entry stats` で coverage matrix を確認
4. `helix entry verify` で pair 漏れがないことを確認

---

## §3 links テーブル運用

### 3.1 links テーブルの役割

`links` テーブルは、`entries` 同士の依存・根拠・参照関係を記録する。  
artifact が「何に基づいて」「何を置き換えるか」「何と整合するか」を追跡できる。

### 3.2 link_kind 一覧

| link_kind | 意味 | 使用場面 |
|---|---|---|
| `mock_to_implementation` | mock artifact を implementation が置き換える | FE mock → 本実装昇格 / D-API mock → 実 API 実装 |
| `supersede` | 新成果物が旧成果物を更新する | D-API draft v1 → v2 に更新 |
| `cross_drive_consistency` | 異なる drive 間の整合 | be D-API と fullstack D-CONTRACT の整合 |
| `plan_to_artifact` | PLAN が artifact の根拠 | PLAN-070 → D-API-draft.md |
| `test_pair` | design と test が対をなす | D-API design entry → D-API test entry |

### 3.3 CLI 操作

```bash
# link 追加
helix entry link-add \
  --source <entry_id_1> \
  --target <entry_id_2> \
  --kind mock_to_implementation

# link 一覧
helix entry link-list --source <entry_id>

# coverage matrix 表示 (design × test ペアの充足率)
helix entry matrix
```

### 3.4 mock_to_implementation の登録手順

FE mock を本実装に昇格させる場合:

```bash
# 1. mock entry の検索
helix entry search --domain-kind design --lifecycle initial --source "docs/*/mock*"

# 2. implementation entry の検索
helix entry search --domain-kind code --lifecycle addition

# 3. link 追加
helix entry link-add \
  --source <mock_entry_id> \
  --target <impl_entry_id> \
  --kind mock_to_implementation
```

---

## §4 detector 連動

### 4.1 detector が entries/links を読む仕組み

HELIX の 14 detector (axis-01〜axis-14) は `helix-detect` 経由で起動し、`entries` / `links` テーブルを参照して矛盾・欠落を検出する。  
検出結果は `detector_runs` テーブルに記録される。

### 4.2 entries/links を参照する detector

`docs/v2/L2-MASTER.md` §11 detector matrix から entries/links 参照のある detector を抜粋:

| detector | axis | entries/links 参照内容 |
|---|---|---|
| axis-07-contract-drift | 07 | entries の design artifact と links の contract reference の乖離検出 |
| axis-08-plan-integrity | 08 | PLAN entries と artifact entries の plan_to_artifact link 欠落検出 |
| axis-12-connection-deficiency | 12 | cross_drive_consistency link の欠落 (be ↔ fullstack 整合漏れ) |
| axis-14-orchestration-integrity | 14 | handover entries の pair 状態と links の整合確認 |
| axis-02-coverage-erosion | 02 | test_pair link の欠落 (design entry に test pair がない) |
| axis-10-relation-graph | 10 | links の依存グラフに循環や孤立 node がないか確認 |

### 4.3 detector 発火タイミング

```bash
# Sprint 完了後に全 detector を実行
helix detect run --all

# 特定 axis のみ実行
helix detect run --axis axis-07-contract-drift

# 結果サマリ表示
helix detect report --latest
```

### 4.4 P0 矛盾への対応

detector が P0 (gate stop) 判定を出した場合:

1. `helix detect report --latest` で詳細確認
2. 対象 entries / links の修正 (artifact 更新 or link 追加)
3. `helix entry verify` で再検証
4. `helix detect run --axis <axis>` で単体再確認
5. 全 detector clean を確認後、gate 通過判定へ

---

## §5 1 Sprint 1 回転

### 5.1 Sprint = らせん 1 回転の意味

1 Sprint で以下の流れが 1 回転する。

```
[Sprint 開始]
   ↓
Sprint plan 策定 (PLAN.md 更新 / task-plan.yaml 更新)
   ↓
artifact 作成 (D-API / D-DB / code 等)
   ↓
entries 登録 (helix entry)
   ↓
links 追加 (mock_to_implementation / test_pair 等)
   ↓
detector 実行 (helix detect run)
   ↓
矛盾修正 (P0 stop, P1 carry 判断)
   ↓
pair status → freeze (functional_freeze)
   ↓
[Sprint 終了 = らせん 1 回転完了]
```

### 5.2 design artifact pair 1 組の完成条件

| 条件 | 確認コマンド |
|---|---|
| design entry が登録されている | `helix entry search --domain-kind design` |
| test_pair link が設定されている | `helix entry link-list --source <design_entry_id>` |
| detector が clean (P0 なし) | `helix detect report --latest` |
| pair_status が frozen | `helix gate run --subgate functional_freeze` |

### 5.3 Sprint 完了判定

```bash
# Sprint 完了の一括チェック (exit gate)
helix gate run --gate G3 --subgate functional_freeze --plan-id <PLAN_ID>
```

G3 functional_freeze が PASS になることで Sprint の artifact pair が確定し、次 Sprint に進む。

---

## §6 自己組織化: 穴を埋めていくシステム

### 6.1 HELIX の根本原則

HELIX は「穴を埋めていくシステム」である。

1. **失敗事象を観測** (detector / memory feedback / gate fail)
2. **対策を 3 種検討** (scan 仕組み / 既存ツール組込 / 構造的設計変更)
3. **L1/L2 に組込** (要件・設計レベルで仕組み化)
4. **即時 PoC** (scrum mode / verify スクリプト)
5. **V2 Phase で本格統合** (L4 実装 → L6 統合検証)

### 6.2 らせん式自己組織化のサイクル

```
Sprint N
  artifact strand: D-API-draft.md (v1 作成)
  record strand:   entries insert → link 追加 → detector 発火
  実行者:         axis-07 が contract drift を P1 で検出
         ↓ 次 Sprint へ carry
Sprint N+1
  artifact strand: D-API-draft.md (v2 carry 修正)
  record strand:   entries update → new link → detector 再実行
  実行者:         axis-07 が clean → freeze
         ↓ らせん 1 回転完成 + 知識の蓄積
```

### 6.3 memory feedback との統合

失敗から得た知識は `.claude/agent-memory/pmo-sonnet/` に記録される。  
feedback memory → HELIX の仕組み化 → entries/links として構造化記録 → detector 常時監視  
という経路で、単なる「メモ」が「自動検知システム」に昇格する。

### 6.4 自己組織化の実例

| 失敗事象 | memory feedback | 仕組み化 |
|---|---|---|
| Codex が新 public function に @helix:index 付与忘れ | feedback_codex_new_function_helix_index_missing.md | helix code stats --fail-under 80 gate 追加 |
| PLAN 番号衝突 | feedback_opus_plan_number_collision_check.md | 起票前 ls docs/plans/ 確認必須化 |
| audit-only failure 3 度連続 | PLAN-048 で codex_post_validation runtime 追加 | helix-codex footer に diff_lines 自動追記 |

---

## §7 オペレーション例: 1 Sprint の具体的な流れ

### 前提

- PLAN: PLAN-071 Sprint .1 (D-API carry capability 詳細化)
- Actor: Codex TL (gpt-5.5 high)
- 対象 artifact: D-API-draft.md §3 carry 追記

### Step 1: Sprint 開始前確認

```bash
# handover 状態確認
helix handover status --json

# 工程表確認
helix plan status --plan-id PLAN-071

# 既存 entries 確認
helix entry stats --by domain
```

### Step 2: artifact 作成

```bash
# Codex TL に委譲
helix codex --role tl --consent approved \
  --plan-id PLAN-071 --l4-sprint ".1" \
  --task "D-API draft §3 に C-01/C-02 endpoint contract を追記せよ"
```

### Step 3: entries 登録

```bash
# D-API draft の entries を登録 (helix code build 後に自動 sync 可能)
helix entry search --source "docs/v2/L3-detailed-design/D-API/D-API-draft.md"

# 不足があれば手動 insert (helix-entry CLI)
helix entry link-add \
  --source <plan_entry_id> \
  --target <d_api_entry_id> \
  --kind plan_to_artifact
```

### Step 4: links 追加

```bash
# design entry と test_pair の link を確認
helix entry matrix

# cross_drive_consistency link (be ↔ fullstack) を追加
helix entry link-add \
  --source <be_d_api_entry_id> \
  --target <fullstack_d_contract_entry_id> \
  --kind cross_drive_consistency
```

### Step 5: detector 実行

```bash
# 全 detector 実行
helix detect run --all

# レポート確認
helix detect report --latest
```

P0 が出た場合は §4.4 の手順で修正。P1/P2 は carry 判断。

### Step 6: functional_freeze 確認

```bash
# pair_status → frozen 判定
helix gate run --gate G3 --subgate functional_freeze \
  --plan-id PLAN-071 --drive be

# 全 drive で PASS を確認
helix gate run --gate G3 --subgate functional_freeze \
  --plan-id PLAN-071 --drive fullstack
```

### Step 7: Sprint 完了報告

HELIX 適用結果フォーマット:

```markdown
HELIX 適用結果 (PLAN-071 Sprint .1)
- size: M
- phases: L3
- skills: workflow/api-contract, workflow/verification
- gates: G3 functional_freeze passed (be + fullstack)
- evidence:
  - D-API draft §3 C-01 / C-02 追記確認 (helix entry show <id>)
  - detector clean (0 P0, axis-07/08/12/14 green)
  - helix entry matrix: design × test pair 充足
- risks: C-03〜C-05 は Sprint .2 carry (partial done 条件は達成)
```

---

## 付録 A: よく使う CLI コマンド早見表

| 用途 | コマンド |
|---|---|
| entries 検索 | `helix entry search --domain-kind design` |
| entries 詳細 | `helix entry show <id>` |
| link 追加 | `helix entry link-add --source <id> --target <id> --kind <kind>` |
| link 一覧 | `helix entry link-list --source <id>` |
| coverage matrix | `helix entry matrix` |
| entries 検証 | `helix entry verify` |
| 全 detector 実行 | `helix detect run --all` |
| detector レポート | `helix detect report --latest` |
| functional_freeze | `helix gate run --gate G3 --subgate functional_freeze --plan-id <id>` |
| handover 状態 | `helix handover status --json` |
| Sprint 状態 | `helix plan status --plan-id <id>` |

## 付録 B: link_kind 使い分け早見表

| シナリオ | link_kind |
|---|---|
| FE mock → 本実装昇格 | `mock_to_implementation` |
| D-API v1 → v2 更新 | `supersede` |
| be D-API ↔ fullstack D-CONTRACT 整合 | `cross_drive_consistency` |
| PLAN → artifact の根拠 | `plan_to_artifact` |
| design entry → test entry | `test_pair` |
