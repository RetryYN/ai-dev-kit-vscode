# HELIX Skill Map

## 正本宣言

- **正本**: SKILL_MAP.md + 各 SKILL.md + ツール設定（`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md`）
- **手順正本**: `tools/ai-coding/references/workflow-core.md` + `tools/ai-coding/references/gate-policy.md`
- **矛盾時**: 実装 > アーカイブ資料（`docs/archive/`）

## 3フェーズ思想

```
Phase 1: 計画（ドキュメント・テスト駆動）  L1 → L2 → L3
Phase 2: 実装（マイクロスプリント）          L4
Phase 3: 仕上げ（デザイン駆動）             L5 → L6 → L7 → L8

Phase R: リバース（既存コード→設計復元）   R0 → R1 → R2 → R3 → R4 → Forward → RGC（閉塞検証）
```

## オーケストレーションフロー

```
【企画】人間が要件提示
  ↓ → requirements-handover, estimation
L1  要件定義（要件構造化 + 受入条件定義）
  ↓ G1   要件完了ゲート         [PM+PO]
  ↓ G1.5 PoC ゲート            [TL+PM]    条件付き
  ↓ G1R  事前調査ゲート         [自動/TL]  条件付き
  ↓ → design-doc, api, db, security, visual-design（方針）
L2  全体設計（方針・アーキテクチャ・visual方針・ADR）
  ↓ G2   設計凍結ゲート         [TL+PM]    ★adversarial-review ★ミニレトロ ★セキュリティ①
  ↓ → api-contract, dependency-map, estimation §8-10
L3  詳細設計 + API契約 + テスト設計 + 工程表
  ↓ G3   実装着手ゲート         [TL+PM]    ★API/Schema Freeze ★事前調査
  ↓ → ai-coding §4
L4  実装（マイクロスプリント: .1a→.1b→.2→.2.5→.3→.4→.5）
  ↓ G4   実装凍結ゲート         [TL+PM]    ★セキュリティ② ★ミニレトロ
  ↓ → visual-design
L5  Visual Refinement（DESIGNER.md 駆動）
  ↓ G5   デザイン凍結ゲート     [TL+PM]    UIなしskip可
  ↓ → verification, testing, quality-lv5
L6  統合検証（E2E・性能・セキュリティ・運用準備）
  ↓ G6   RC判定ゲート（Release Candidate）  [PM+TL+PO]  ★セキュリティ③
  ↓ → deploy, infrastructure, observability-sre
L7  デプロイ（staging → 本番 → watch）
  ↓ G7   安定性ゲート          [自動/PM]    ★セキュリティ④
  ↓ → verification §14
L8  受入（要件 ↔ 最終成果物の突合 → PO最終承認）★ミニレトロ
```

**ゲート詳細・セキュリティ・遷移ルール** → `tools/ai-coding/references/gate-policy.md` 参照

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

**Reverse ゲート詳細** → `tools/ai-coding/references/gate-policy.md §Reverse ゲート` 参照
**Reverse フロー詳細** → `workflow/reverse-analysis/SKILL.md` 参照

## タスクサイジング

3軸の**最大サイズ**を採用:

| 軸 | S | M | L |
|----|---|---|---|
| ファイル数 | 1-3 | 4-10 | 11+ |
| 変更行数 | ~100 | 101-500 | 501+ |
| API/DB変更 | なし | 片方 | 両方 |

## フェーズスキップ決定木

```
├─ S（小規模）
│   ├─ バグ修正 / リファクタ → L4 のみ
│   ├─ 新規小機能 → L2 → L3 → L4 → L6
│   ├─ UI変更 → L2 → L3 → L4 → L5 → L6
│   └─ ドキュメント / 設定 → L4 のみ
│   ※ S案件の L3 は最小版: タスクリスト + 担当割当のみ（API契約・依存マップは省略可）
├─ M（中規模）
│   ├─ API/DB変更なし(UI有) → L2 → L3 → L4 → L5 → L6 → L7 → L8
│   │   G1.5/G1R skip可、G3会議省略可
│   ├─ API/DB変更あり(UI有) → フルフロー
│   ├─ API/DB変更なし(BE) → L2 → L3 → L4 → L6 → L7 → L8
│   │   L5/G5 skip
│   └─ 新規モジュール → L1 → フルフロー
└─ L（大規模）→ フルフロー（純BE: L5/G5 skip）
```

**セキュリティゲート強制条件** → `tools/ai-coding/references/gate-policy.md §セキュリティゲート強制条件` 参照

## スキル群配置（42スキル）

パス: `skills/{カテゴリ}/{スキル名}/SKILL.md`
詳細 I/O → `orchestration-workflow.md` / 遷移条件 → `layer-interface.md`（共に `tools/ai-coding/references/`）

| カテゴリ | スキル |
|---------|--------|
| workflow/ | project-management, dev-policy, estimation, requirements-handover, compliance, design-doc, api-contract, dependency-map, quality-lv5, deploy, dev-setup, incident, observability-sre, postmortem, verification, adversarial-review, context-memory, reverse-analysis |
| common/ | visual-design, design, coding, refactoring, documentation, security, testing, error-fix, performance, code-review, infrastructure, git |
| project/ | ui, api, db |
| advanced/ | tech-selection, i18n, external-api, ai-integration, migration, legacy |
| tools/ | ai-coding, ide-tools |
| integration/ | agent-teams |

## メンテナンス指針

1. スキル追加時: SKILL_MAP.md を更新。500行超 → references/ に分割
2. 重複防止: 追加前に既存スキルとの重複確認
3. 廃止済み: architecture / orchestrator / codex / vscode-plugins → 使用禁止。検出: `rg -wn "orchestrator|architecture|codex|vscode-plugins" skills/`
4. metadata.helix_layer 必須。description は具体的用途を記載（「〇〇関連」禁止）
