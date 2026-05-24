---
name: helix-discovery
description: 要件未確定・実現可能性不明の案件で仮説検証駆動で開発を進める。D0 (Backlog) → D1 (Sprint Plan) → D2 (PoC) → D3 (Verify) → D4 (Decide) を回し、confirmed 仮説を Forward HELIX L1 要件へ昇格する。PoC・新規事業・技術検証・リサーチ系タスクで使う。
helix_layer: [D0, D1, D2, D3, D4]
codex_role: tl
tier: 1
upstream: cli/helix-discovery
---

# HELIX Discovery

## Overview

通常の HELIX は L1 要件定義から始めるが、要件や成立条件がまだ固まっていない案件では、そのまま Forward に入ると仮定のまま設計と実装が進んでしまう。
このスキルは、D0-D4 の Discovery モードで仮説を backlog 化し、PoC と検証スクリプトで成立可否を判断してから、confirmed 仮説だけを Forward HELIX の L1 要件へ昇格する。

> 旧: `helix-scrum` (S0-S4)。backward compat alias は `L7-scrum-to-discovery-renameplan` を参照。
