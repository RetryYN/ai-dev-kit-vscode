---
doc_id: two-stage-agent-design
title: "HELIX W（2段設計・V字を2回, Phase 合流型）"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# HELIX W（2段設計・V字を2回, Phase 合流型）

## 概要

作る対象が AI エージェントシステムの場合に推奨する2段設計。Forward の Vモデルを Phase 1（一般システム）と Phase 2（エージェント昇華）で2回通すため、V が2つ重なって W 字になる。これを **HELIX W** と呼ぶ。L14 まで一本で通さず、Phase に分けて **L10 で合流** する。一般システムとエージェント昇華をそれぞれ L9（総合テスト）まで作り、L10 以降（仕上げ・本番・運用）は合流して一度だけ通す。

## 適用条件

**AI エージェントシステムを作る場合のみ適用する。** 一般システムで完結するなら、通常の Forward（L0–L14）を一本で通す。

## Phase 構造

```
L0 企画（全体で1回）
   │
   ├─ Phase 1: L1 → L9  （一般システム / drive=be・fe・db・fullstack）
   │            機能・API・ロジックを総合テストまで完成
   │
   ├─ Phase 2: L1 → L9  （エージェント昇華 / drive=agent）
   │            tool・MCP・interface・skill を総合テストまで完成
   │
   └─ Phase 3: L10 → L11 → L12 → L13 → L14  （合流）
                L10 で Phase 1 と Phase 2 を再接続し、
                UX 磨き上げ → 総合レビュー → デプロイ → 運用検証を一度だけ
```

## 各 Phase の内容

| Phase | 工程 | 対象 | drive |
|---|---|---|---|
| Phase 1 | L1–L9 | 一般システム（機能・API・ロジック） | be / fe / db / fullstack |
| Phase 2 | L1–L9 | エージェント昇華（tool / MCP / interface / skill / subagent） | agent |
| Phase 3 | L10–L14 | 合流 → UX 磨き上げ → レビュー → デプロイ → 運用 | 横断 |

L0（企画）は Phase 分けの前に全体で1回。Phase 1 と Phase 2 はともに L1（要求定義）から L9（総合テスト）まで。

## なぜ L9 で区切り L10 で合流するのか

- L9（総合テスト）までで、システムとして機能は完成・検証済みになる。
- L10 以降（UX 磨き上げ・総合レビュー・デプロイ・デプロイ後検証・運用検証）は、最終成果物に対して一度行えばよい。
- 一般システムとエージェント昇華を別々に L14 まで通すと、デプロイ・運用を二重に行う無駄が生じる。L10 で合流して一度だけ本番化・運用する。

## L10 合流点

L10（フロントデザイン / UX 磨き上げ）が再接続点。Phase 1（一般システム）と Phase 2（エージェント昇華）の成果をここで統合し、人間向け UI とエージェント向け interface の両方を統合的に仕上げる。以降の L11–L14 は統合済みの単一成果物を扱う。

## 検証

| 段 | 検証 |
|---|---|
| Phase 1 L8 / L9 | 一般機能のテスト（機能の正しさ） |
| Phase 2 L8 / L9 | エージェント昇華のテスト（tool 契約・MCP スキーマ・axis-14 協調整合） |
| Phase 3 L11 | 統合レビュー（Phase 1 と Phase 2 の合流整合） |

Phase 1 と Phase 2 をそれぞれ L9 まで検証してから L10 で合流するため、「ツールが壊れたままエージェントが呼ぶ」破綻を、合流前に各 Phase で潰せる。

## 既存資産との対応・不足

- Phase 2 の昇華先資産: agent-skills（23）、agents/（サブエージェント定義）、tool / MCP 定義。
- 不足: drive=agent が未定義（be / fe / db / fullstack のみ）。vmodel-semantics への agent drive 追加と、Phase 合流（L9 → L10 再接続）を制御する仕組みが必要。integration-map.md の穴に含む。

## 効果

一般システムを L9 まで完成（Phase 1）、エージェント昇華を L9 まで完成（Phase 2）させ、L10 で合流して一度だけ仕上げ・本番化・運用する。機能の正しさとエージェント利用性を各 Phase で分離検証でき、かつ仕上げ・デプロイ・運用の二重化を避けられる。一般システムを作る通常開発では、この Phase 分けは発生しない。
