---
doc_id: folder-structure-review
title: "フォルダ構成レビューと再構成"
status: draft
created: 2026-05-24
owner: PM
parent: ../HELIX-process-L0-L14.md
---

# フォルダ構成レビューと再構成

## 現状フォルダ構成（リポジトリ）

- トップ: AGENTS.md / CLAUDE.md / README.md / cli / docs / harness / helix / skills / src / tests / verify / workflows / scripts
- cli（726 files）: lib（393, うち detectors 17）/ templates（97）/ config / libexec / roles / prompts / schemas / scripts / tests
- docs（472 files）: adr / research / architecture / design / features / plans / requirements / runbook / slo / rollback / postmortem / qa / security-review / specs ほか30以上
- tests（分散 307 files）: cli/lib/tests(213) / cli/tests(82) / tests(9) / .claude/hooks/tests(3)

## チェック済み領域（これまでの点検）

detector（axis 14 + FE 5 stub）/ template（plan kind 11, docs L1–L5）/ command（71）/ skill（111）/ vmodel-semantics / 一部の cli/lib（agent_mandatory, learning_engine, skill_catalog, command_catalog 等）。

## チェックが行き届いていない領域（点検漏れ）

| 領域 | 規模 | 状況 |
|---|---|---|
| docs/ | 472 files | 最大の未点検。adr（8本）/ research / runbook（9）/ slo / rollback / postmortem に実体あり |
| tests 分散 | 307 files / 4箇所 | cli/lib/tests(213) / cli/tests(82) / tests(9) / .claude/hooks/tests(3) |
| cli/lib | 393 files | detector(17) 以外（plan / skill / scrum / audit / codex / code / agent / vmodel 等）が大半未点検 |
| トップ機能 dir | — | harness（g4-gate-harness）/ helix（HELIX_CORE, CODEX_TL_MODE）/ verify（番号付き検証スクリプト）/ workflows（l4-sprint-workflow）/ src / scripts |
| .claude / libexec / roles / prompts / schemas | — | Claude Code 連携・hook・補助 |

## 前回報告の訂正（実体確認による）

- ADR: docs/adr に既存8本（ADR-001〜008）と慣行が存在。前回「ADR が穴」は「雛形テンプレートのみ無し、置き場・慣行はある」に訂正する。
- research: docs/research に実体（PLAN-029-research-findings）。research-memo の置き場は docs/research。

## フォルダ再構成のまとめ（統合方針）

helix-process/（本セッションの42ファイル、現状フラット）は、新規フォルダを増やさず、既存の docs/ 構造へ統合できる。

| helix-process/ の文書 | 統合先 docs/ |
|---|---|
| L0–L14 工程（15） | docs/requirements / docs/design / docs/specs |
| モードワークフロー（9） | docs/design または docs/architecture |
| 工程専門（screen / frontend） | docs/design |
| 管理・自動化ドキュメント | docs/architecture または docs/design |
| 検出・学習・注入の各設計 | docs/architecture |
| Recovery / Incident 運用 | docs/runbook / docs/rollback / docs/postmortem / docs/slo（既存） |
| ADR / research 関連 | docs/adr / docs/research（既存に追加） |

tests は4箇所の役割を明確化（cli/lib/tests = detector・lib、cli/tests = コマンド、tests = トップ統合、.claude/hooks/tests = hook）するか、集約方針を1つ決める。

## まとめ

点検は機能（モード / 機構 / detector / template / skill / command）中心で行き届いたが、実装・成果物層（docs 472 / cli/lib 393 / 分散 tests 307）は大半が未点検だった。

再構成の核心は、新規フォルダを増やすことではなく、本セッションで helix-process/ に作った設計を、既に置き場が用意されている docs/（adr / research / runbook / rollback / postmortem / slo / design / architecture）へ接続することにある。ADR・research・運用ドキュメントは既存の慣行と置き場があるため、そこに合流させるのが筋。
