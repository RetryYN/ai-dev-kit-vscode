# HELIX Skill Map

## 正本宣言

- **正本**: SKILL_MAP.md + 各 SKILL.md + ツール設定（`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md`）
- **工程定義正本**: [`HELIX-workflows/HELIX-process-L0-L14.md`](../HELIX-workflows/HELIX-process-L0-L14.md) (2026-05-24 V2 完全移行確立、commit 35a901c)
- **手順正本**: `skills/tools/ai-coding/references/workflow-core.md` + `skills/tools/ai-coding/references/gate-policy.md`
- **矛盾時**: 実装 > アーカイブ資料（`docs/archive/`）

## V2 完全移行 (2026-05-24、ユーザー指示)

- **HELIX-workflows を正本** とし、docs/v2/process/ は実装文書として同期
- **PLAN は全工程 L0-L14 で起票**、各工程 PLAN は `process_layer` ごとに独立。L7 は実装工程内に複数の `L7-<機能名>plan` を抱える上位概念 (他工程 PLAN の親ではない)
- **PLAN 命名規則**: `L<NN>-○○○plan` (例: `L0-企画書plan` / `L7-helix-workspace-mergeplan`)
- **PLAN 配置**: `docs/plans/L0/` 〜 `docs/plans/L14/` にフォルダ分離
- **PLAN の中身**: 工程表 (作業手順 + 進捗) + 実装計画の 2 要素を内蔵 → 再開可能
- **旧 V1 PLAN は参考扱い、製本にしない**。製本したい場合は V2 命名規則で書き直し (commit f409c55 で `is_reference: true` marked)
- 詳細: docs/v2/process/README.md / HELIX-workflows/HELIX-process-L0-L14.md

## モデル割当（真実は `cli/config/models.yaml`）

| ロール | モデル | thinking |
|--------|--------|--------|
| PM | Opus (Claude Code) | — |
| PMO Sonnet | claude-sonnet-4-6 | medium |
| PMO Haiku | claude-haiku-4-5-20251001 | low |
| TL | gpt-5.5 | high |
| SE | gpt-5.4 | high |
| PE | gpt-5.3-codex-spark / gpt-5.3-codex | low-medium |

## CLI ロール補足（30）

- CLI ロール数は 30 件: `tl`, `se`, `pg`, `qa`, `security`, `dba`, `devops`, `docs`, `research`, `legacy`, `perf`, `fe`, `recommender`, `classifier`, `effort-classifier`, `pmo-sonnet`, `pmo-haiku`, `pdm-tech-innovation`, `pdm-marketing-innovation`, `pdm-innovation-manager`, `impl-sonnet`, `pm-advisor`, `tl-advisor`, `pmo-helix-explorer`, `pmo-helix-scout`, `pmo-project-explorer`, `pmo-project-scout`, `pmo-tech-docs`, `pmo-tech-fork`, `pmo-tech-news`
- `classifier`: タスク記述を分類し、適切なロールや処理系への振り分けを補助する軽量分類ロール
- `recommender`: スキル候補を JSON で返す軽量推挙ロール（`helix skill search` の中核）
- `effort-classifier`: 工数・難易度・規模を分類して見積もりや実行方針の初期判定を補助するロール
- `pmo-helix-explorer`: HELIX framework 内資産詳細探索（skills/templates/cli/docs）
- `pmo-helix-scout`: HELIX 内軽量検索・候補列挙（1 hop 目）
- `pmo-project-explorer`: プロジェクト内資産詳細探索（code/docs/config）
- `pmo-project-scout`: プロジェクト内軽量検索・候補列挙（1 hop 目）
- `pmo-tech-docs`: 設計手法・概念の外部精読
- `pmo-tech-fork`: OSS/plugin 探索・転用判断
- `pmo-tech-news`: 最新 Tech 動向 sweep（週次想定）

## 参考正本（ADR / PLAN）

- `docs/adr/ADR-014-roles-config-format.md`
- `docs/adr/ADR-015-helix-v2-orchestration.md`
- `docs/plans/PLAN-028-helix-v2-orchestration.md`

## 4フェーズ思想 (新 15 工程 L0-L14、commit eeb0530)

```
Phase 0: 企画                               L0
Phase 1: 設計 (ドキュメント・テスト駆動)    L1 → L2 → L3 → L4 → L5 → L6
Phase 2: 実装 (スプリント、PLAN 起票 layer) L7
Phase 3: 検証・磨き上げ                     L8 → L9 → L10 → L11
Phase 4: リリース・運用                     L12 → L13 → L14

Phase R: リバース（既存コード→設計復元）   R0 → R1 → R2 → R3 → R4 → Forward → RGC（閉塞検証）
```

**V-model ペア凍結対応**: L1↔L14, L2↔L10, L3↔L12, L4↔L9, L5↔L8, L6↔L7 (詳細は §オーケストレーションフロー)

## オーケストレーションフロー (新 15 工程 L0-L14、commit eeb0530)

> **正本**: [HELIX-workflows/HELIX-process-L0-L14.md](../HELIX-workflows/HELIX-process-L0-L14.md) (commit 35a901c)
>
> **構造的原則 (2026-05-24 V2 完全移行で訂正)**:
> - PLAN は **機能 (ドキュメント) 単位で全工程 L0-L14 に起票**する
> - **L7 は実装工程内の機能 PLAN (L7-<機能名>plan × N) を管理する上位概念**。L7 工程表が機能順序を定義し、各 L7-<機能名>plan が 1 機能の実装手順書になる。他工程 (L0-L6/L8-L14) の PLAN は独立に起票され、L7 は親ではない
> - PLAN は **工程表 (作業手順 + 進捗) + 実装計画** の 2 要素を内蔵 → 再開可能
> - PLAN 命名規則: **`L<NN>-○○○plan`** (例: L0-企画書plan / L7-helix-workspace-mergeplan)
> - 配置: **`docs/plans/L0/` 〜 `docs/plans/L14/`** にフォルダ分離
> - 旧 V1 PLAN (PLAN-NNN-slug) は **参考扱い、製本にしない**。製本したい場合は V2 命名規則で新規書き直し (commit f409c55 で is_reference: true marked)
>
> **V-model ペア凍結**: 設計工程と検証工程は対で凍結する。
>
> | 設計層 | ↔ | 検証層 |
> |---|---|---|
> | L1 要求定義 (運用テスト設計) | ↔ | L14 運用検証 |
> | L2 画面設計 (UX 期待) | ↔ | L10 FE UX 磨き上げ |
> | L3 要件定義 (受入テスト設計) | ↔ | L12 受入テスト |
> | L4 基本設計 (総合テスト設計) | ↔ | L9 総合テスト |
> | L5 詳細設計 (結合テスト設計) | ↔ | L8 結合テスト |
> | L6 機能設計 (単体テスト設計) | ↔ | L7 単体テスト実装 (Sprint Step 2) |

```
【企画フェーズ】
L0  企画書 (北極星指標・市場仮説・PdM 翻案)
  ↓ G0.5 企画突合ゲート       [PM]
  ↓ → requirements-handover, requirements-deriver, doc-system-architect

【設計フェーズ (Phase 1)】
L1  要求定義 + 運用テスト設計 (機能要求 + IPA × ISO 25010 非機能 + 受入条件 + ★運用テスト)
  ↓ G1   要求完了ゲート         [PM+PO]
  ↓ G1.5 PoC ゲート            [TL+PM]    条件付き
  ↓ G1R  事前調査ゲート         [TL]      条件付き
  ↓ → design-doc, visual-design (information / layout / ux)
L2  画面設計 + フロント UI + ワイヤーモック (DESIGN.md / mock.html / state-events.md)
  ↓ G2   画面凍結ゲート         [TL+PM]    ★mock UX 承認 ★MOCK-* auto-enqueue
  ↓ → api-contract, requirements-deriver
L3  要件定義 + 受入テスト設計 (FR/NFR 詳細 + ★受入テスト設計)
  ↓ G3   要件凍結ゲート         [PM+PO]   ★V-model L3↔L12 受入テスト pair freeze
  ↓ → design-doc, api-contract
L4  基本設計 + 総合テスト設計 (アーキテクチャ + ADR + ★総合テスト設計)
  ↓ G4   基本設計凍結ゲート     [TL+PM]   ★adversarial-review ★セキュリティ① ★V-model L4↔L9 pair freeze
  ↓ → design-doc, api-contract, dependency-map
L5  詳細設計 + 結合テスト設計 (D-API / D-DB / 詳細フロー + ★結合テスト設計)
  ↓ G5   詳細設計凍結ゲート     [TL]      ★API/Schema Freeze ★V-model L5↔L8 pair freeze
  ↓ → design-doc, api-contract, schedule-wbs
L6  機能設計 + 単体テスト設計 (関数 / endpoint schema + ★単体テスト設計)
  ↓ G6   機能設計凍結ゲート     [TL]      ★V-model L6↔L7-test pair freeze ★parent_design 凍結

【実装フェーズ (Phase 2、L7 = 機能 PLAN 上位概念。他工程 PLAN は §V2 完全移行 参照)】
L7  実装スプリント (kind=impl PLAN-NNN 起票、process_layer=L7)
    Step 1: PLAN (sprint 計画、parent_design + pairs_test_design 参照)
    Step 2: 単体テスト実装 (L6 機能設計から pair freeze)
    Step 3: 本体実装 (TDD)
    Step 4: 設計・テスト・実装 3 点レビュー
    Step 5: テストパターン追加 (QA 観点)
    Step 6: テスト実施 (回帰)
    Step 7: 修正 / 実装完了
  ↓ G7   実装完了ゲート         [TL+PM]   ★セキュリティ② ★ミニレトロ ★4 artifact trace
  ↓ → verification

【検証フェーズ (Phase 3)】
L8  結合テスト + 依存関係解消 (L5 詳細設計↔結合テスト設計 pair execute)
  ↓ G8   結合検証ゲート         [TL]
L9  総合テスト + 依存関係解消 (L4 基本設計↔総合テスト設計 pair execute)
  ↓ G9   総合検証ゲート         [TL+PM]   ★セキュリティ③ ★E2E/perf/security
  ↓ → visual-design, god-writing
L10 フロント UX 磨き上げ (DESIGNER.md / ビジュアル磨き / コピー磨き) — L2↔L10 pair execute
  ↓ G10  UX 磨き上げゲート      [TL+PM]   UI なし skip 可
L11 総合レビュー + ユーザー検証 + 要件巻き取り (PO 検証 + 要件 drift 解消)
  ↓ G11  RC 判定ゲート          [PM+TL+PO]
  ↓ G11.5 Pre-Release 本番直前確認 [TL+PM]  ★rollback/monitoring/on-call

【リリースフェーズ (Phase 4)】
L12 デプロイ + 受入テスト + 環境差異巻き取り (L3 要件↔L12 受入 pair execute)
  ↓ G12  デプロイ受入ゲート     [PM+PO]   ★セキュリティ④
  ↓ → observability-sre
L13 デプロイ後検証 + 実環境運用 (smoke / canary / 初期インシデント対応)
  ↓ G13  安定性ゲート           [自動/PM] fail-close
  ↓ → postmortem, innovation-mgr
L14 運用検証 + 機能改善 (L1 運用テスト pair execute → 次イテレーション L0 input)
  ↓ G14  運用学習完了ゲート     [PM]      fail-close
```

**ゲート詳細・セキュリティ・遷移ルール** → `skills/tools/ai-coding/references/gate-policy.md` 参照

### 入口モード一覧 (HELIX-workflows、2026-05-24 V2 完全移行で確立)

正本: [HELIX-workflows/HELIX-process-L0-L14.md §他モード](../HELIX-workflows/HELIX-process-L0-L14.md) + [helix-process/README.md](../HELIX-workflows/helix-process/README.md)

Forward HELIX (L0-L14) を中核とし、入口に応じて 9 mode + 2 工程専門 workflow を使い分ける。**全モードは最終的に Forward の L0-L14 ドキュメント体系へ収束・昇華する**。

正本 table は [HELIX-process-L0-L14.md §他モード](../HELIX-workflows/HELIX-process-L0-L14.md) を参照。本 section は HELIX framework 側の **入口判定アンカー** として最小情報のみ持つ。

| モード | 入口 | 正本 | Forward 接続 |
|---|---|---|---|
| **Forward** | 要件・設計・契約が確定 | [HELIX-process-L0-L14.md](../HELIX-workflows/HELIX-process-L0-L14.md) | (本体) |
| **Scrum** (アジャイル) | 要件をユーザーと反復で固める | [scrum-workflow.md](../HELIX-workflows/helix-process/scrum-workflow.md) | 完成機能を Reverse fullback で文書化 → L0-L14 |
| **Discovery** | 計画上の不明点・実現性検証 (Reverse と組合せ可) | [discovery-workflow.md](../HELIX-workflows/helix-process/discovery-workflow.md) | confirmed → L1/L3/L4-L6 へ昇格 |
| **Reverse** | 既存コード・設計の逆引き | [reverse-workflow.md](../HELIX-workflows/helix-process/reverse-workflow.md) | R4 routing → L1/L3/L4/L7/L8-L11 |
| **Incident** | 本番障害の緊急対応 (hotfix) | [incident-workflow.md](../HELIX-workflows/helix-process/incident-workflow.md) | 暫定収束後、恒久対策を L1/L3/L4-L6、postmortem を L14 |
| **Add-feature** | 既存システムへの差分追補 | [add-feature-workflow.md](../HELIX-workflows/helix-process/add-feature-workflow.md) | add-design / add-impl を L4-L7 に追補 → L0-L14 体系へ統合 |

#### 新 4 mode (workflow doc 正本、入口判定 anchor のみ)

table 二重化を避けるため詳細は正本へ委譲する。CLI 整備状況と運用方針のみ本 section に記載:

- **Refactor** ([refactor-workflow.md](../HELIX-workflows/helix-process/refactor-workflow.md)) — 振る舞い不変の構造改善。**dedicated CLI 未整備**。PLAN kind=`refactor` + workflow doc で運用。Forward 接続は L7 内部、既存 L8/L9 テストを保護網として流用
- **Retrofit** ([retrofit-workflow.md](../HELIX-workflows/helix-process/retrofit-workflow.md)) — 依存・基盤の段階改修・移行。**dedicated CLI 未整備**。PLAN kind=`retrofit` + retrofit-matrix + config で運用。L4/L5 追補 + L8/L9 回帰、要件変更時のみ L1/L3 へ戻す
- **Research** ([research-workflow.md](../HELIX-workflows/helix-process/research-workflow.md)) — 実装前の技術調査・意思決定。**`helix research` CLI あり**。PLAN kind=`research` + ADR + research-memo で運用。Discovery (作って試す) との分岐: 「調べて決める」が Research
- **Recovery** ([recovery-workflow.md](../HELIX-workflows/helix-process/recovery-workflow.md)) — AI エージェントの暴走・独断専行のガード+収束。**dedicated CLI 未整備**。PLAN kind=`recovery` + recovery-log + stop-hook + cutover_orchestrator で運用。発火条件 4 種 (想定外大規模変更 / 工程逸脱 / 認識ズレ蓄積 / 予算超過)

> **CLI 未整備の警告**: Refactor / Retrofit / Recovery は `helix refactor` / `helix retrofit` / `helix recovery` 等の CLI が存在しない。エージェントが叩いて失敗するリスク回避のため、必ず workflow doc 正本 + PLAN kind / template で扱う。CLI 契約整理は後続 ADR / PLAN 候補。

#### 特殊 workflow / HELIX W

入口判定 mode と異なる **特殊設計**: AI エージェントシステム構築時のみの 2 段 V 字。9 mode 表に並べない。

- **HELIX W** ([two-stage-agent-design.md](../HELIX-workflows/helix-process/two-stage-agent-design.md)) — Phase1 (一般システム、be/fe/db/fullstack、L1-L9) + Phase2 (agent、L1-L9) + Phase3 (合流、L10-L14)。`drive=agent` 起動・検出方式は integration-map 解消の後続 PLAN 候補

#### 工程専門ワークフロー (FE/UX、HELIX FE 弱点補強)

入口判定モードではなく、特定工程 (L2/L10) の進め方を専門化したもの。

| 専門 workflow | 対応工程 | 正本 | 補強する FE detector |
|---|---|---|---|
| 画面設計 (UI/ワイヤー) | L2 画面設計 | [screen-design-workflow.md](../HELIX-workflows/helix-process/screen-design-workflow.md) | state-transition-drift / mock-promotion |
| フロントデザイン (UX/ビジュアル) | L10 UX 磨き上げ | [frontend-design-workflow.md](../HELIX-workflows/helix-process/frontend-design-workflow.md) | design-token-drift / a11y-regression / visual-regression |

L2 (左腕) でワイヤー設計、L10 (右腕) で UX 磨き上げ、V-model 上のペア関係。

> **責務整理 (重要、L7-scrum-to-discovery-renameplan 完了後)**: `helix discovery` CLI / `agent-skills/helix-discovery` skill が正本であり、`helix scrum` / `agent-skills/helix-scrum` は legacy alias である。HELIX-workflows の新 Scrum (アジャイル) は別概念で、検証駆動の Discovery とは区別する。

### ワークフロー文書統合 cross-reference

helix-process/ 45 file の中央 INDEX 兼 appendix は [docs/architecture/helix-workflows-appendix.md](../docs/architecture/helix-workflows-appendix.md) を参照する。
domain 別の導線は `docs/{adr,research,runbook,rollback,postmortem,slo,design}/helix-workflows-appendix.md` に集約する。

### HELIX Reverse（既存コードからの逆引き設計）

```
【既存コード】設計書なし・テストなしのシステム
  ↓ → reverse-analysis, legacy
R0  Evidence Acquisition（コード+DB+設定+運用実態の証拠収集）
  ↓ RG0  証拠網羅ゲート           [TL]
  ↓ → api-contract, verification
R1  Observed Contracts（API/DB/型の機械抽出 + characterization tests）
  ↓ RG1  契約検証ゲート           [TL]
  ↓ → design-doc, adversarial-review
R2  As-Is Design（アーキテクチャ復元 + ADR推定）
  ↓ RG2  設計検証ゲート           [TL + adversarial-review]
R3  Intent Hypotheses（要件仮説 + PO検証）
  ↓ RG3  仮説検証ゲート           [PM+PO+TL]
R4  Gap & Routing（差分集約 → Forward HELIX に接続）
  ↓
Forward HELIX（Gap種別で L1/L2/L3/L4 に振り分け）
```

#### Reverse type matrix

| Type | 起点 | R0 | R1 | R2 | R3 | R4 | RGC |
|------|------|----|----|----|----|----|-----|
| code | レガシーコード | 証拠収集 | 契約抽出 | 設計復元 | 仮説検証 | Gap → Forward | 閉塞検証 |
| design | デザイン資産 | 資産収集 | skip | DAG/順序 | PO 検証 | Forward routing | 閉塞検証 |
| upgrade | 既存 system + 新版 | version diff | 影響分析 | 設計差分 | risk 評価 | Forward routing | upgrade RGC skip |
| normalization | 設計 drift | drift 検出 | skip | normalize 設計 | PO 確認 | Forward routing | 閉塞検証 |
| fullback | 実装完遂後 | 実装証拠 | 文書 gap 抽出 | alignment 設計 | 文書 PO 確認 | Forward routing | 閉塞検証 |

#### Reverse type notes

- code: 既存コード・DB・設定・運用実態を起点に、観測契約から設計と意図を復元する。R1 の契約抽出が中核で、既存 code 型の標準経路は維持する。
- design: デザイン資産起点。R1 の既存コード契約抽出は行わず skip し、R2 で DAG/実装順を起こして R3 で PO 検証へ進む。
- upgrade: 既存版と新版の差分が起点。R0 で version diff を取り、R2 で設計差分、R4 で Forward 案件を決める。gap closure は upgrade 完了として Forward 側で評価するため RGC は skip。
- normalization: 設計 drift の正規化が起点。R1 は skip し、R2 で normalize 設計、R3 で PO 確認、R4 で Forward routing に接続する。
- fullback: 実装完遂後の文書整合が起点。R0 で実装証拠、R1 で文書 gap、R2 で alignment 設計、R3 で文書 PO 確認、R4 で closure routing を行う。

**Reverse ゲート詳細** → `skills/tools/ai-coding/references/gate-policy.md §Reverse ゲート` 参照
**Reverse フロー詳細** → `workflow/reverse-analysis/SKILL.md` 参照

### HELIX Discovery（検証駆動 / 要件未確定時、旧: HELIX Scrum）

> **責務整理 (2026-05-25)**: 本 section は HELIX-workflows の **Discovery ワークフロー** (仮説検証 / PoC / verify scripts) を扱う。`helix discovery` / `agent-skills/helix-discovery` が正本で、`helix scrum` / `agent-skills/helix-scrum` は 1 release の backward compat alias である。HELIX-workflows の新「Scrum」 (アジャイル Scrum、ユーザー要件すり合わせ反復開発) とは別概念。runtime state は A1 では `.helix/scrum/` を継続利用する。詳細は [discovery-workflow.md](../HELIX-workflows/helix-process/discovery-workflow.md)。


```
【仮説・要件不確実】実現可能性不明・PoC 要・技術検証必要
  ↓ helix size --uncertain → discovery 判定 / または helix discovery init を直接起動
D0  Backlog 構築（仮説一覧 + 検証質問 + 成功条件）
  ↓ helix discovery backlog add
D1  Sprint Plan（ゴール + 対象仮説選定）
  ↓ helix discovery plan
D2  PoC 実装（Codex に委譲、verify/ スクリプト化）
  ↓ helix discovery poc --hypothesis H001
D3  Verify（全検証スクリプト実行 → リグレッション蓄積）
  ↓ helix discovery verify
D4  Decide（confirmed / rejected / pivot）
  ↓ helix discovery decide --hypothesis H001 --confirmed
  ↓
Forward HELIX（確定仮説を L1 要件に昇格 → helix size で fe/be/fullstack 再判定）
```

**Scrum モードの特徴**:
- Forward HELIX のフェーズ進行 (L1-L14) は走らない。runtime state は `.helix/scrum/` 配下で独立管理 (A1 scope)
- verify/*.sh は毎回全実行 → リグレッション検出
- `decide --confirmed` で Forward HELIX に接続
- `db` / `agent` エッジケースでも「仮説検証フェーズ」として scrum 前段利用可能

## readiness と carry rule

PLAN-004 v5 連動として、L1-L14 の entry/exit に readiness 条件を含める。

- P0: gate stop（即修正）
- P1: gate stop OR carry（PM承認）
- P2: 次 L 開始まで or debt として `.helix/audit/deferred-findings.yaml` へ carry
- P3: 任意 carry

deferred-finding は accuracy_score に反映し、G1-G11 の評価算定に加算（減点）する。  
（重みは既定の deferred レベル係数を参照）

## タスクサイジング

3軸の**最大サイズ**を採用:

| 軸 | S | M | L |
|----|---|---|---|
| ファイル数 | 1-3 | 4-10 | 11+ |
| 変更行数 | ~100 | 101-500 | 501+ |
| API/DB変更 | なし | 片方 | 両方 |

## 駆動タイプ

`helix size --drive <type>` で明示指定、または `--ui/--api/--db/--uncertain` フラグで自動判定。L2〜L5 の中身とゲート判定基準が変わる。

### 主要 4 パターン (通常はこの 4 択)

| 駆動タイプ | 起点 | 典型プロジェクト |
|-----------|------|----------------|
| **be**（デフォルト） | API/ロジック | 業務系、解析系、SaaS バックエンド |
| **fe** | デザイン/UX → モック駆動 | LP、EC、ダッシュボード、UX重視プロダクト |
| **scrum** | 仮説検証（要件不確実） | PoC、新規事業、技術検証、リサーチ系 |
| **fullstack** | BE+FE同時（Twin Track） | SaaS、EC、ダッシュボード + API |

### エッジケース (特殊起点)

| 駆動タイプ | 起点 | 典型プロジェクト |
|-----------|------|----------------|
| **db** | スキーマ/データモデル | マスタ管理、ERP、データ基盤 |
| **agent** | ツール/プロンプト | AI アプリ、自動化、ワークフロー |

### 自動判定ロジック (`helix size` のフラグベース)

```
--uncertain あり                   → scrum (Phase S / 検証駆動)
--ui + (--api or --db) あり        → fullstack (Twin Track)
--ui のみ                          → fe (モック駆動)
--api or --db あり                 → be
フラグなし                         → be (デフォルト)
```

明示 `--drive <type>` 指定は常に最優先。`db` / `agent` は明示指定のみ。

### 駆動タイプ別 L2〜L11

| フェーズ | be | fe | db | fullstack | agent |
|---------|----|----|----|-----------|----|
| L2 設計 | API設計・アーキテクチャ・ADR | **モック駆動設計**（方針+トークン+`mock.html`+`state-events.md`） | ER図・スキーマ設計 | BE方針+FE方針（**mock含む**）+接続契約方針（同時策定） | ツール定義・プロンプト設計 |
| L3 詳細 | API契約+DB+工程表 | TL が `state-events.md` から **API契約導出**+DB+工程表 | マイグレーション+API契約+工程表 | D-API+D-UI+D-CONTRACT+D-DB+D-STATE+**mock**+工程表 | ツール契約+統合テスト設計+工程表 |
| L6 機能設計 | API実装詳細 + 単体テスト観点 | FE API契約導出 + イベント連携 + モック準備 | スキーマ変更影響 + 単体確認観点 | 接続/変換 API + FE 連携 | ツール入出力 + 状態遷移 |
| L7 実装順 (旧 L4) | ロジック→API→FE | BE（契約ベース）∥ FE（**モック→本実装昇格**）→ 統合 | スキーマ→CRUD→API→FE | Phase A: BE Sprint ∥ FE Sprint（**mockを起点**）→ Phase B: L7-L8 結合 (旧 L4.5) | ツール→オーケストレーション→UI |
| L5 重み | 薄い（表示確認） | **厚い**（デザイン駆動） | 薄い（管理画面確認） | 標準（結合後にVisual Refinement） | 会話UI/デモ確認 |
| L8 結合テスト | 依存関係解消 + 結合観点 | モック→本実装の接続検証 | 永続化を含む結合確認 | エンドポイント/画面連携の結合確認 | ツール呼び出しと外部連携の結合確認 |
| L9 Run-1（デプロイ検証） | 標準 | 標準 | 薄い | 標準 | 薄い |
| L10 Run-2（観測） | 薄い | 標準 | 薄い | 標準 | 薄い |
| L11 Run-3（運用学習） | 標準 | 標準 | 薄い | 標準 | 標準 |
| G2 凍結 | API設計凍結 | **モック凍結**（UX承認 + MOCK-* auto-enqueue 発火） | スキーマ凍結 | 接続契約方針凍結（BE+FE+Contract三点セット） + MOCK-* auto-enqueue | ツール定義凍結 |
| G3 着手 | API/Schema Freeze | **モック+API/Schema Freeze** | Migration Freeze | API/Schema/UI/Contract全凍結 | Tool Contract Freeze |
| G4 追加条件 | — | **MOCK-HARDCODE + MOCK-CODE-LEAK resolved 必須** | — | 同左（fe同等） | — |
| G6 追加条件 | — | **MOCK-DERIVED-CONTRACT resolved 必須** | — | 同左（fe同等） | — |

auto-thinking は opt-in flag、default は role conf の `codex_thinking`。

> **UI / fullstack の詳細フロー**（L2 ステップ内訳 / TL 契約導出手順 / モック由来 debt ライフサイクル / 責務分担表 / アンチパターン）→ `skills/project/ui/references` 配下を参照

### L5 要否の判定

| 駆動タイプ | L5 必要条件 |
|-----------|------------|
| be | `--ui` 有りのときのみ |
| fe | **常に必要**（FE駆動の核心） |
| db | `--ui` 有りのときのみ |
| fullstack | **常に必要**（結合後の Visual Refinement） |
| agent | **常に必要**（会話UI/デモ） |

## フェーズスキップ決定木

駆動タイプで L5 の要否が変わる（上記参照）。それ以外の判定ロジックは共通:

```
├─ S（小規模）
│   ├─ バグ修正 / リファクタ / ドキュメント → L4 のみ
│   ├─ 新規小機能 / 新モジュール → L1 → L2 → L3 → L4 → (L5) → L6
│   └─ UI変更 → L2 → L3 → L4 → L5 → L6
│   ※ S案件の L1/L3 は最小版: 目的+受入条件+タスクリスト
│   ※ 新機能は S でも L1（要件定義）を飛ばさない
├─ M（中規模）
│   ├─ 新機能/新モジュール → L1 → フルフロー
│   ├─ API/DB変更あり → L1 → L2 → L3 → L4 → (L5) → L6 → L7 → L8
│   ├─ API/DB変更なし + L5要 → L1 → L2 → L3 → L4 → L5 → L6 → L7 → L8
│   │   G1.5/G1R skip可、G3会議省略可
│   └─ バグ修正/リファクタ → L2 → L3 → L4 → (L5) → L6 → L7 → L8
└─ L（大規模）
    ├─ L5要 → フルフロー
    └─ L5不要 → フルフロー（L5/G5 skip）
```

(L5) = 駆動タイプの L5 要否判定に従う

Run 工程（L9-L11）の適用可否:
- 本番運用あり: G9-G11 を必須適用
- PoC / 検証寄り: 本番影響がなければ Run は skip 可

fullstack 追加条件:
- L7 は Phase A（BE Sprint ∥ FE Sprint）→ Phase B（L7-L8 結合、旧 L4.5）
- L5 は常に必要（結合後の Visual Refinement）

**セキュリティゲート強制条件** → `skills/tools/ai-coding/references/gate-policy.md §セキュリティゲート強制条件` 参照

## スキル群配置（118スキル）

パス: `skills/{カテゴリ}/{スキル名}/SKILL.md`
詳細 I/O → `orchestration-workflow.md` / 遷移条件 → `layer-interface.md`（共に `skills/tools/ai-coding/references/`）

| カテゴリ | スキル |
|---------|--------|
| workflow/ | project-management, dev-policy, estimation, requirements-handover, compliance, design-doc, api-contract, dependency-map, quality-lv5, deploy, dev-setup, incident, observability-sre, postmortem, verification, adversarial-review, context-memory, reverse-analysis, **research**, **poc**, **gate-planning**, **schedule-wbs**, **threat-model**, **runbook**, **debt-register**, **reverse-r0**, **reverse-r1**, **reverse-r2**, **reverse-r3**, **reverse-r4**, **reverse-rgc**, **doc-system-architect**, **requirements-deriver**, **retrofit**, **detection-routing**, **learning-engine**, **cross-detection**, **layer-context-injection**, **review-stage-routing** |
| common/ | visual-design, design, coding, refactoring, documentation, security, testing, error-fix, performance, code-review, infrastructure, git |
| project/ | ui, api, db |
| advanced/ | tech-selection, i18n, external-api, ai-integration, migration, legacy, **tech-innovation**, **marketing-innovation**, **innovation-mgr** |
| tools/ | ai-coding, ide-tools, **web-search**, **ai-search** |
| integration/ | agent-teams, **agent-design**, **agent-cost-design** |
| writing/ | japanese, explain, story, presentation, social, **god-writing** |
| design-tools/ | diagram, web-system, pptx, graphic, character, **gpt-image** |
| automation/ | site-mapping, browser-script, flow-optimize, scheduler, job-queue, lock, init-setup, observability |
| **agent-skills/** | idea-refine, spec-driven-development, planning-and-task-breakdown, incremental-implementation, test-driven-development, context-engineering, source-driven-development, frontend-ui-engineering, api-and-interface-design, browser-testing-with-devtools, debugging-and-error-recovery, code-review-and-quality, security-and-hardening, performance-optimization, ci-cd-and-automation, deprecation-and-migration, documentation-and-adrs, shipping-and-launch, using-agent-skills, **system-design-sizing**, **technical-writing**, **mock-driven-development**, **helix-discovery**, **helix-scrum** |

**2026-04-17 追加分** (20スキル):
- workflow/: research (G1R)・poc (G1.5)・gate-planning (G0.5/G1.5)・schedule-wbs (L3)・threat-model (G2)・runbook (L6)・debt-register (G4)・reverse-r0〜r4 + reverse-rgc (R0-R4 + RGC)
- project/: ui/design-doc を経由する経路を継続し、FE 系サブエージェント個別運用は v2 方針で停止
- tools/: web-search (native WebSearch + WebFetch)・ai-search (Haiku 4.5 委譲)

**2026-04-22 追加分** (25スキル、agent-skills/ カテゴリ新設):
- 上流由来 19 (addyosmani/agent-skills MIT、日本語化済): idea-refine / spec-driven-development / planning-and-task-breakdown / incremental-implementation / test-driven-development / context-engineering / source-driven-development / frontend-ui-engineering / api-and-interface-design / browser-testing-with-devtools / debugging-and-error-recovery / code-review-and-quality / security-and-hardening / performance-optimization / ci-cd-and-automation / deprecation-and-migration / documentation-and-adrs / shipping-and-launch / using-agent-skills (メタ)
- HELIX 独自 discovery skill: system-design-sizing (donnemartin/system-design-primer MIT 根拠)・technical-writing (Google Tech Writing CC-BY 根拠)・mock-driven-development (FE 駆動核心)・helix-discovery (D0-D4 仮説検証)。`helix-scrum` は legacy alias として維持
- 除外 3 (本体 workflow/ に既存): adversarial-review / debt-register / reverse-analysis
- 付随: .claude-plugin/ (marketplace 配布用)・.claude/commands/ 7 本 (slash commands)・addyosmani/agent-skills 由来の 3 役（code-reviewer / security-audit / qa-test）は .claude/agents/ に統合（現在の .claude/agents/ は 19 エージェント構成: be-api / be-logic / code-reviewer / db-schema / devops-deploy / qa-test / security-audit / pmo-sonnet / pmo-haiku / pdm-tech-innovation / pdm-marketing-innovation / pdm-innovation-manager / pmo-helix-explorer / pmo-helix-scout / pmo-project-explorer / pmo-project-scout / pmo-tech-docs / pmo-tech-fork / pmo-tech-news）・agent-skills/references/ 5 checklist・agent-skills/hooks/ (session-start)
- 統合ガイド: docs/agent-skills/README.md・docs/agent-skills/skill-anatomy.md

既存 `workflow/reverse-analysis` は各 reverse-r* へのルーターに縮小。既存 `project/ui` は UI 参照インデックスとして残存。

**2026-05-08 追加分** (1スキル、ユーザー自作):
- integration/: **agent-design** (AIエージェント設計の判断軸 11 本 = 要素・骨格・思考指定・出力指定・スキーマ・前段制約・後段責務の連鎖、`型 = 要素定義 + フレーム化` の還元式と縛りの 3 階層を中核とする L2/L3 設計概論)

**2026-05-13 追加分** (1スキル、ユーザー自作):
- integration/: **agent-cost-design** (AIエージェント構築のコスト予算・ガードレール確定スキル。8 references = multi-vendor / fallback-policy / retry-design / flow-design / cost-estimation / test-budget / guardrail-impl / budget-monitoring を Phase 0-5 順序で参照。1.2 倍上振れ係数固定、80% 到達で追加予算申請、ハードリミットはラッパー層実装が中核原則。L1/L2/L3 エージェント設計の前段必須)

**2026-05-23 追加分** (4スキル、ユーザー素材を pmo-sonnet で HELIX format 化):
- workflow/: **doc-system-architect** (ドキュメント体系のメタ設計スキル。変数判断 4 軸 [決定の不可逆性/読み手/変更頻度/再現可能性] + 業界標準への整合 [ISO/IEC/IEEE 42010:2022 / arc42 / C4 / ADR Nygard / Diátaxis / IPA 非機能要求グレード 2018 / Keep a Changelog / 12-factor / Runbook] の二段で「何を・どこまで・どの粒度で書くか」を導出。Why > What > How の優先順位、Single Source of Truth、確定までは軽メモ。要件未確定項目は確認リストとして分離)
- workflow/: **requirements-deriver** (機能要件→非機能要件導出スキル。「複数/顧客/組織/テナント/SaaS/決済/個人情報/連携/24時間/大量」シグナル → R1-R14 ルール → IPA 非機能要求グレード 2018 (6 大項目) × ISO/IEC 25010 (8 特性) 二軸タグ → 分離レベル/冗長構成/認証方式まで展開。AI のシングルテナント固定化を防ぐ L1 関所。doc-system-architect の子スキル)
- writing/: **god-writing** (フロントエンド / LP / SEO / コピー / 心理 / UX / 日本語修辞 / ロジック / 技術文書 を 9 カテゴリ + 97 references で統合する神レベルライティング統合スキル。AIDA / PAS / BAB framework [27% conversion 向上事例] + 心理 trigger [emotional/social proof/urgency/trust] + UX 3 原則 [Clear/Concise/Contextual、Slack onboarding 93% 完遂事例] + E-E-A-T/LLMO + 日本語修辞。既存 writing/japanese 等は基礎用途で残置、本 skill は LP/FE 応用用途)
- design-tools/: **gpt-image** (GPT Image 2 (2026/04/21 リリース、Codex CLI default、$imagegen built-in skill) で アイキャッチ / 図解 / LP ヒーロー画像を構造化プロンプト生成する実装層スキル。最大 16 reference images / 1K-4K / 多言語 99% typography / Thinking mode で reasoning built-in。helix codex --role docs 委譲か Codex CLI 内 $imagegen 起動。DALL-E 3 retired 後継)

### 責務境界クリア化（テスト・検証・品質系の使い分け）

3スキルが近接領域だが層が異なる。発火順に整理:

| スキル | フェーズ | 役割 |
|--------|---------|------|
| `common/testing` | **L4** 実装時 | テストケース作成・テストテンプレート (unit/integration/E2E の書き方) |
| `workflow/quality-lv5` | **L6** 統合検証 | テスト品質を Lv1-5 で評価・テストピラミッド比率・カバレッジ目標の判定 |
| `workflow/verification` | **all** (L1〜L11 + R0-R4 + RGC) | Spec駆動検証・L8-L11 仕様/運用突合・Reverse RG0-RG3/RGC ゲート検証基盤 |

使い分けルール:
- **テストを書く**: `common/testing` のみ参照
- **テスト品質の合否判定**: `workflow/quality-lv5` (G4/G6 ゲート時)
- **成果物 ↔ 要件の突合検証**: `workflow/verification` (L1 受入条件 / L8 受入 / Reverse ゲート)

### 責務境界クリア化 (AIエージェント設計系の使い分け)

近接する 4 スキルがあるが層が異なる。**判断に迷ったときに開く reference** という共通機能を持つので境界を明示:

| スキル | 守備範囲 | 利用タイミング |
|--------|---------|---------------|
| `integration/agent-cost-design` | **エージェント着手前のコスト予算・ガードレール確定** (生成フロー / マルチベンダー / コスト見積 / 予算監視) | L1 受領直後〜L2 設計前。**設計・実装に着手する前に必ず** 通る前段ゲート |
| `integration/agent-design` | **個別 LLM agent / task** の structural design (要素・骨格・前段制約・後段責務) | L2 ADR / L3 D-API / L4 基本設計で **判断に迷ったとき** 該当 axis を開く |
| `integration/agent-teams` | **複数 agent の協調・分業** | agent-design で個別設計後、複数 agent をチーム化するとき |
| `agent-skills/spec-driven-development` | **仕様駆動開発全般** (LLM 限定なし) | spec → 実装の上位プロセス。agent-design はその LLM 特化版 |

使い分けルール:
- **エージェント構築タスク受領 → 着手前**: `integration/agent-cost-design` (Phase 0-5 でコスト/予算/ガードレール確定が最優先)
- **個別 LLM agent の設計判断で迷う**: `integration/agent-design` (axis 11 本から該当を引く)
- **複数 agent の協調設計**: `integration/agent-teams`
- **LLM agent 以外も含む仕様駆動**: `agent-skills/spec-driven-development`
- **D-API / D-CONTRACT の HELIX 正本**: `workflow/api-contract` (agent-design axis 07 から接続)

エージェント構築の標準フロー: **agent-cost-design (前段) → agent-design (個別構造) → agent-teams (協調)**。コストガードを通さずに structural design へ進まない。

### 責務境界クリア化 (ドキュメント体系・要件導出系の使い分け、2026-05-23 追加)

doc-system-architect が親スキル、requirements-deriver は子スキル。L1 / L2 で開く順序が決まっている:

| スキル | 守備範囲 | 起動タイミング |
|--------|---------|---------------|
| `workflow/doc-system-architect` | **ドキュメント体系の設計判断** (何を・どこまで・どの粒度で書くか / 業界標準への整合) | L1 受領直後〜L2 entry。新規プロジェクト立ち上げ・ドキュメント整理時に **必ず** 通る前段ゲート |
| `workflow/requirements-deriver` | **機能要件 → 非機能要件導出** (IPA × ISO 25010 二軸 / R1-R14 シグナル) | L1 要件定義の核心。機能要件 doc から非機能要件を機械的に展開 (質問ゼロ、欠落のみ確認リスト) |
| `workflow/requirements-handover` | **要件曖昧時の確認 protocol / 引継ぎチェックリスト** | 要件 doc 自体が曖昧な時に先行 (requirements-deriver の前段) |
| `workflow/design-doc` | **L2/L3 個別設計書本体** (D-API / D-DB / D-CONTRACT / D-STATE) の作成 | 上記スキル群の出力を入力に、個別設計書を書く実行スキル |
| `common/documentation` | **README / ADR / 技術文書テンプレート** | doc-system-architect が「採用標準」と決めた個別 doc を書く時 |

使い分けルール:
- **要件 doc が曖昧** → `requirements-handover` (協議が先)
- **要件はあるが体系全体を決めたい** → `doc-system-architect` (メタ層、何書くか決める)
- **要件から非機能要件を導出** → `requirements-deriver` (R1-R14 自動展開)
- **個別 doc 本体作成** → `design-doc` / `documentation`

標準フロー: **requirements-handover (協議 if 曖昧) → doc-system-architect (体系設計) → requirements-deriver (非機能要件導出) → design-doc / documentation (個別本体)**。

### 責務境界クリア化 (LP / FE / 画像生成・統合ライティング系の使い分け、2026-05-23 追加)

god-writing は writing/ 統合層、既存 writing/* は基礎層。gpt-image は LP / SEO 記事の画像生成専用:

| スキル | 守備範囲 | 起動タイミング |
|--------|---------|---------------|
| `writing/god-writing` | **9 カテゴリ統合** (copywriting / psychology / sales / seo / ux / logical / japanese / technical / philosophy + meta + interview = 97 references) で LP / FE / SEO 記事 / セールスコピー / UX 文章を起草 | LP / FE / セールスページ作成、SEO 記事マーケ、コンバージョン重視コピー、エラーメッセージ / オンボーディング microcopy |
| `writing/japanese` | **基礎日本語**: 文法 / 漢字仮名 / 句読点 / textlint 統合 lint | 基礎日本語 lint 用途 (god-writing references/japanese/basic/ は基礎踏襲、本 skill は応用層) |
| `writing/explain` | **技術文書 4 部構成 + EEAT コンテンツ品質監査** | 技術ブログ・チュートリアル系 (god-writing references/technical/ と一部重複、explain は SEO 記事の核心) |
| `writing/social` | **SNS 投稿テンプレート + GEO 設計** | SNS 単発投稿 (god-writing references/copywriting/social-copy.md と一部重複、social は SNS チャネル特化) |
| `writing/story` | **ストーリーテリング** | ストーリー単体 (god-writing references/copywriting/storytelling.md と一部重複) |
| `writing/presentation` | **プレゼン資料** | slide 用途 (god-writing 範囲外) |
| `design-tools/gpt-image` | **GPT Image 2 (Codex CLI default) で画像生成** (アイキャッチ / 図解 / LP ヒーロー画像) | LP / SEO 記事の画像が必要な時、Codex CLI 内 $imagegen 起動時、brand asset (16 ref images) を style anchor として使う時 |
| `design-tools/diagram` | **図解の設計 (10 種類の図解タイプ理論)** | 図解の **設計層** (gpt-image は実装層) |
| `design-tools/graphic` | **コード生成型グラフィック (Satori 等)** | code で SVG/PNG 生成する時 (gpt-image は AI 生成型) |
| `design-tools/web-system` | **shadcn/ui デザインシステム + デザイントークン 3 層** | UI コンポーネント層 (god-writing は文章層、両者は LP で組み合わせる) |
| `common/visual-design` | **ビジュアル設計原則 / DESIGN.md / a11y / データ Viz** | 全体ビジュアル方針 (gpt-image / web-system / graphic の上位) |

使い分けルール:
- **基礎日本語 lint** → `writing/japanese`
- **技術ブログ / チュートリアル** → `writing/explain`
- **SNS 単発投稿** → `writing/social`
- **LP / FE / セールスコピー / UX writing / 心理 trigger 統合** → **`writing/god-writing`** (本 PR で追加)
- **LP / 記事の画像生成** → **`design-tools/gpt-image`** (本 PR で追加、Codex 委譲)
- **UI コンポーネント設計** → `design-tools/web-system` + `common/visual-design`

god-writing は **既存 writing/* との重複** を許容して導入 (基礎用途は既存 skill / 応用 LP 用途は god-writing の棲み分け)。将来統合候補は別 PLAN で検討。

### 責務境界クリア化 (code-review 系の使い分け、2026-05-23 追加 / 2026-05-25 review-stage-routing 追加)

code-review は 4 系統で目的が分かれる (観点と分業を別軸で扱う):

| スキル | 守備範囲 | 起動タイミング |
|--------|---------|---------------|
| `common/code-review` | HELIX L7 / G7 連携 (旧 L4/G4) の **base skill** (OWASP セキュリティ / パフォーマンス / 設計観点 / Critical/High 0 達成基準) + **Google eng-practices reviewer guide** (references/google-reviewer-guide.md、LGTM/Nit/Blocking ラベル、健全性ベース判定) | レビュアー視点で承認可否 (LGTM / LGTM with nits / Changes requested) を判定するとき。HELIX gate 連携時 (実装完了ゲート = G7) |
| `workflow/review-stage-routing` | **6 段階 (Format/Lint/Style/Logic/Design/Architecture) × ロール (PM/TL/SE/PE/QA/security) 分業境界** + 逆説ルール (AI ゼロ指摘領域こそ上位ロールが見る) + ADR 降下 | helix review / code-reviewer agent / adversarial-review の起動順と責任分界を決めるとき。AI と人間の境界線確定時。観点・判定は common/code-review に委譲、本 skill は分業のみ (ai-code-review-kit/helix-integration/ 由来、2026-05-25 取り込み) |
| `agent-skills/code-review-and-quality` | **5 軸 review** (Correctness / Readability / Architecture / Security / Performance) (addyosmani/agent-skills MIT 由来、英語) | 多次元評価が必要なとき。author / reviewer 区別なく汎用 review |
| `workflow/adversarial-review` | G2/G4/G6 ゲート前の **adversarial check** (悪魔の代弁者役) | gate 通過前に意図的に反対意見を集めて穴を探すとき |

使い分けルール:
- **HELIX L7/G7 (旧 L4/G4) で承認可否判定** → `common/code-review` (Google reviewer guide 統合、実装完了ゲート連携)
- **段階 × ロール 分業境界決定** → `workflow/review-stage-routing` (観点は common/code-review に委譲、分業のみ)
- **5 軸で多次元評価** → `agent-skills/code-review-and-quality`
- **ゲート前 adversarial check** → `workflow/adversarial-review`
- **author 視点 (変更を作成する側)** → 別 skill (現在は `agent-skills/source-driven-development` 等を併用)

common/code-review に Google eng-practices reviewer guide を統合した経緯: 「健全性ベース判定 + LGTM/Nit/Blocking ラベル」は HELIX 既存 skill に明示的に存在しなかったため、common/code-review/references/ に reviewer 専用 reference として追加 (2026-05-23、SKILL (1).md 統合)。

review-stage-routing を追加した経緯: 「コードレビューを 6 段階 × ロール分業」モデル (Zenn 出典 + 2026/05 ツール動向 ai-code-review-kit/) は観点 (common/code-review が正本) と独立した**分業軸**で価値を持つため、両者を併存させる。本 skill は新ゲートも CLI も追加せず、helix review / G2 / G4 / code-reviewer agent の起動順と責任分界に被せるレイヤとして機能する (2026-05-25、ai-code-review-kit/helix-integration/ 取り込み)。

### 既存スキル強化メモ（description 更新）

```yaml
common/security:
  description: セキュリティ対策で環境別設定ガイド・認証認可実装パターン・脆弱性対策チェックリストとOWASP検証手順・秘密情報スキャン・AI生成コード品質チェックを提供
common/error-fix:
  description: エラー修正で体系的デバッグ手順・失敗パターンレジストリ運用・危険コマンドガードを提供
common/visual-design:
  description: ビジュアル設計原則・AI品質チェックに加え、DESIGN.md 9セクション形式ブランド参照（JP24件+EN10件）・IA/モーション/UXパターン/a11y/データViz論を references/ で提供
design-tools/web-system:
  description: shadcn/uiデザインシステム構築に加え、デザイントークン3層設計・スケール策定プロセス・DESIGN.md形式のD-VIS-ARCH適用手順を references/ で提供
workflow/observability-sre:
  description: SLO/SLI設計・構造化ログ・ダッシュボード・AIエージェントメトリクスに加え、リアルタイム監視設計とD-OBSテンプレートを提供
workflow/verification:
  description: L1〜V-L6検証に加えて、D-API/D-CONTRACT/D-DB起点のSpec駆動検証とL8仕様突合チェックを提供
tools/ai-coding:
  description: AIコーディング運用に加えて、GitHub ActionsでのCI/CDエージェント統合パターンを提供
integration/agent-teams:
  description: 複数エージェント協調運用に加えて、n8n/Dify発想のビジュアルワークフロー設計を提供
automation/site-mapping:
  description: Crawl4AI中心のサイト構造抽出に加えて、Firecrawl代替クローラーの使い分けと安全運用を提供
common/performance:
  description: パフォーマンス最適化指針に加えてAIセッション記録/再生と学習連携の運用手順を提供
writing/explain:
  description: 4部構成テンプレートに加えてEEATベースのコンテンツ品質監査チェックを提供
writing/social:
  description: SNS投稿テンプレートに加えてGEO（生成エンジン最適化）の設計指針を提供
automation/browser-script:
  description: Playwright記録からのE2E化に加えてaxe-coreによるアクセシビリティ自動検証を提供
```

## V-model 4 artifact 双方向 trace (2026-05-17 確立 / 訂正)

詳細は `helix/HELIX_CORE.md §設計⇔テスト対応`。

要点:
- 4 artifact は **別文書**: ① 設計 / ② 実装コード / ③ テスト設計 / ④ テストコード
- 各 artifact は **双方向 reference** で対応関係を明示 (設計⇔テスト設計、設計⇔実装、テスト設計⇔テストコード)
- L2 → 総合テスト設計、L3 → 結合テスト設計、機能設計 → 単体テスト設計、L1 → 受入テスト設計
- 2 つ以上を 1 文書に統合することは V-model 違反 (例: D-API EXT 内にテスト設計埋め込み)
- G2/G3/G4 ゲートで 4 artifact 揃いを確認 (PLAN-075 Phase 5 で自動 lint 化予定)

## 工程別 subagent 起動マップ (PLAN-076、2026-05-17 確立)

詳細は `helix/HELIX_CORE.md §工程別 subagent 起動マップ`。

要点:
- subagent 14 種を 2 分類: **mandatory by phase (10 種)** + **on-demand by judgment (4 種)**
- mandatory は工程必須、`helix agent fire-mandatory --phase Lx` で一括投入、helix.db で audit
- on-demand は free will、`helix agent suggest` で候補提示
- G2/G3/G4 ゲートで mandatory 呼び出し audit (PLAN-076 Phase 5 で fail-close)

## Sprint Plan 標準構造 (PLAN-077、2026-05-17 確立)

詳細は `helix/HELIX_CORE.md §Sprint Plan 標準構造`。

要点:
- L7 実装中の Sprint Plan が標準 8 ステップに固定化される
- **mandatory in sprint**: 機械チェック (py_compile / lint) + テスト起動 (該当 test / 全回帰) + レビュー (セルフ / pmo-sonnet)
- **on-demand in sprint**: security audit / perf test / tl-advisor 等
- Sprint Exit 前に mandatory 全通過必須、`helix sprint complete --auto-check` で機械化

## メンテナンス指針

1. スキル追加時: SKILL_MAP.md を更新。500行超 → references/ に分割
2. 重複防止: 追加前に既存スキルとの重複確認
3. 廃止済みスキル名: architecture / orchestrator / codex / vscode-plugins → **スキル名としての参照**禁止（ツール名 `helix review`・メタデータ `codex: true`・YAML キー `architecture:` は正当な用法）。検出: `rg -wn "orchestrator" skills/ --glob '!SKILL_MAP.md'`
4. metadata.helix_layer 必須。description は具体的用途を記載（「〇〇関連」禁止）

## 自動推挙システム（gpt-5.4-mini）

全 116 スキル + 229+ references を LLM マッチングで自動推挙する CLI を搭載。

```bash
helix skill list [--layer L2] [--category common] [--json]
helix skill show <skill-id> [--with-content]
helix skill catalog rebuild             # SKILL.md frontmatter + references 冒頭 blockquote を parse
helix skill search "<task>" [-n 5]      # Codex gpt-5.4-mini で推挙
helix skill use <id> --task "..." [--dry-run] [--agent NAME] [--references PATHS]
helix skill chain "<task>" [-n 1]       # search → use の一気通貫
helix skill stats [--days 30]           # 使用統計（skill_usage テーブル）
helix budget
helix recipe <learn|promote|discover|list>  # learn/promote/discover は deprecated
helix handover resume
```

### 推挙の仕組み
- catalog: `.helix/cache/skill-catalog.json`（SKILL.md frontmatter + references 冒頭 `> 目的:` blockquote を機械抽出）
- エンジン: `gpt-5.4-mini` (`cli/roles/recommender.conf`、thinking=low)
- プロンプト: `cli/templates/prompts/skill-search.md`（9種の agent 決定マッピング含む）
- キャッシュ: `.helix/cache/recommendations/<sha256>.json` で 1 時間保存
- 使用履歴: `helix.db` (v5) の `skill_usage` テーブル

### 委譲の自動化
`helix skill use` は recommender が選んだ agent へ委譲する:
- `tl` / `se` / `pe` / `qa` / `security` / `dba` / `devops` / `docs` / `research` / `legacy` / `perf` は Codex ロール（`helix codex --role X --task "<bundle>\n\n<task>"` で自動実行）
- PMO 系は `helix claude --role pmo` 系へ委譲し、FE 設計は TL→PM チェック後に PMO 経由の整合運用へ回す

### 実装ファイル
- `cli/lib/skill_catalog.py` — catalog 生成・読み込み（SKILL.md + references parser）
- `cli/lib/skill_recommender.py` — Codex 呼び出し・キャッシュ
- `cli/lib/skill_dispatcher.py` — context bundle 作成・委譲・DB 記録・stats
- `cli/helix-skill` — bash ディスパッチャ (list/show/catalog/search/use/chain/stats)
- `cli/roles/recommender.conf` — gpt-5.4-mini ロール定義
- `cli/templates/prompts/skill-search.md` — LLM プロンプトテンプレート

## コードインデックス（PLAN-011 + PLAN-012 + PLAN-013）

既存コードに `# @helix:index ...` メタデータを付与し、検索・重複検知・統計を可能にする `helix code` 系 CLI。skill catalog と同じ枠組みをコード資産へ拡張する。

```bash
helix code build                                        # 全 tracked files を走査し catalog を再構築
helix code find "<query>" [-n 5]                        # gpt-5.4-mini で流用候補を探索
helix code show <id>                                    # path / line / metadata を表示
helix code dup [--threshold 0.85] [--domain <name>]     # 同一 domain 内の重複候補を検出
helix code stats [--by domain|since]                    # domain / since / bucket / uncovered 別の集計
helix code stats --uncovered [--scope core5|cli-lib|all] [--bucket coverage_eligible|private_helper|excluded|all] [--seed-candidate true|false|all] [--seed-promotable true|false|all] [--fail-under N] # PLAN-012/013
helix code list [--domain <name>] [--json]              # entry 一覧
```

メタデータ規約:
- Python: `# @helix:index id=code-catalog.parse-frontmatter domain=cli/lib summary=YAML frontmatterをdictに展開`
- bash: `# @helix:index id=helix-code.build domain=cli summary=code-catalogを再構築`

関連 PLAN: PLAN-011（catalog skeleton） + PLAN-012（coverage gate） + PLAN-013（taxonomy）

3-bucket taxonomy 概要:
- coverage_eligible: 公開 symbol、coverage gate の母集団（core5 は 80% gate）
- private_helper: 非公開 symbol（`_` 始まり）、PoC seed 候補
- excluded: `setup.sh` / `skills/agent-skills/hooks/*.sh` / `verify/*.sh` の固定 3 pattern
- non_indexable_paths: `tests/*.py` / `fixture/*` / `generated/*` / `vendor/*`（bucket 分類前 pre-filter）
- helix.db schema: v14 → v15（`bucket` / `symbol_line` を追加）

PLAN-013 運用フロー（L1-L14 追跡）:
- L7 entry: `helix code find` / `helix code stats --uncovered --bucket coverage_eligible` で既存資産を確認
- L7 implementation: 新規 public symbol は `coverage_eligible`、`_` 始まり helper は `private_helper` に分類
- L7 build: `helix code build` で catalog を再生成し `bucket` / `symbol_line` / metadata を自動付与
- G7: `helix code stats --scope core5 --bucket coverage_eligible --fail-under 80` を実施して coverage gate
