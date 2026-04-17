---
name: reverse-analysis
description: Reverse フロー全体のルーター
metadata:
  helix_layer: R0
  triggers:
    - 設計書なし・テストなしの既存コード改修時
    - レガシーシステムの現状把握時
    - 技術的負債の全体評価時
    - 新規メンバーのオンボーディング（大規模コードベース理解）
    - R0-R4 各フェーズの詳細は各 reverse-r* スキルを参照
  verification:
    - "R0: evidence_map に対象モジュール 100% 含有"
    - "R1: 観測契約の confidence ≥ high が 80% 以上"
    - "R2: ADR 仮説に contradictions 0 件（未解決）"
    - "R3: PO 検証済み仮説率 ≥ 80%"
    - "R4: gap_register の全項目に routing 割当済み"
compatibility:
  claude: true
  codex: true
---

# Reverse Analysis Router

Reverse HELIX は「既存コードという観測事実」から設計と意図を逆方向に復元し、差分を Forward HELIX に安全に接続するための流れである。本スキルは全体像と入口を提供し、各フェーズの実行詳細は専用スキルへ委譲する。

## Reverse フロー全体図

```mermaid
flowchart TD
  R0["R0 Evidence Acquisition"] --> RG0["RG0"]
  RG0 --> R1["R1 Observed Contracts"] --> RG1["RG1"]
  RG1 --> R2["R2 As-Is Design"] --> RG2["RG2"]
  RG2 --> R3["R3 Intent Hypotheses"] --> RG3["RG3"]
  RG3 --> R4["R4 Gap & Routing"] --> FWD["Forward HELIX (L1-L4)"]
  FWD --> RGC["RGC Gap Closure"]
```

## フェーズ別ルーティング

| フェーズ | 担当スキル | パス |
|---|---|---|
| R0 Evidence Acquisition | reverse-r0 | [skills/workflow/reverse-r0/SKILL.md](skills/workflow/reverse-r0/SKILL.md) |
| R1 Observed Contracts | reverse-r1 | [skills/workflow/reverse-r1/SKILL.md](skills/workflow/reverse-r1/SKILL.md) |
| R2 As-Is Design | reverse-r2 | [skills/workflow/reverse-r2/SKILL.md](skills/workflow/reverse-r2/SKILL.md) |
| R3 Intent Hypotheses | reverse-r3 | [skills/workflow/reverse-r3/SKILL.md](skills/workflow/reverse-r3/SKILL.md) |
| R4 Gap & Routing | reverse-r4 | [skills/workflow/reverse-r4/SKILL.md](skills/workflow/reverse-r4/SKILL.md) |
| RGC Gap Closure | reverse-rgc | [skills/workflow/reverse-rgc/SKILL.md](skills/workflow/reverse-rgc/SKILL.md) |

## 使い分けガイド

全体の進め方・フェーズ間の接続・実行順を把握したい場合は本スキルを読む。個別フェーズに着手する場合は必ず対応する `reverse-r*` スキルを読み、そこで定義された入出力・検証・ゲート条件に従う。

後方互換: 旧 `reverse-analysis` に含まれていた L1-L8 含む詳細記述は、各 `reverse-r*` / `reverse-rgc` スキルへ移設済み。
