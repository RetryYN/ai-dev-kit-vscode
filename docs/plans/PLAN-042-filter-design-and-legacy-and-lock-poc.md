---
plan_id: PLAN-042
title: 'PLAN-042（filter design 原則 + legacy frontmatter progressive (3 件) + concurrent reader lock 機構 PoC）'
status: completed
created: 2026-05-10
finalized: 2026-05-10
completed: 2026-05-10
author: Opus (PM)
size: M
phases: L1→L2→L3→L4
gates: G1, G2, G3, G4
acceptance:
  - W-1: feedback_filter_design_principle.md 作成、MEMORY.md 追記、原則 5 axis 以上記述
  - W-23: PLAN-004/005/006 frontmatter 後付け、body-preservation hash test PASS、cli/lib/plan_frontmatter.py 本体未変更
  - W-4: ADR-016 起票、standalone lock primitive PoC 実装、race condition 回帰テスト 1 ケース PASS
related: [PLAN-041, PLAN-040, PLAN-038, ADR-014, ADR-015]
---

## §1 目的

PLAN-041 retro carry 3 件を本 PLAN で集約解消する。

1. filter design 原則を memory feedback として記録する。W-1 の副作用として、footer 内 literal marker が STDOUT_FILE に流入し、emit_summary_from_capture が誤抽出した経験を再発防止可能な形で残す。
2. legacy PLAN markdown の frontmatter を後付けする。PLAN-004 / PLAN-005 / PLAN-006 の 3 件に限定し、body-preservation を維持したまま progressive に進める。
3. concurrent reader の中間状態観測不可保証（lock 機構）を、ADR 設計 + standalone lock primitive PoC に scope 限定して着手する。PLAN-038 W-1 P3 debt の carry を止め、実 critical path 接続は PLAN-043 へ carry する。

W-4 は scope 限定とし、critical path 全面展開は本 PLAN で扱わない。

## §2 全体方針

### §2.1 設計原則

- W-1: feedback memory file 新規作成のみ。既存 memory の改変はしない。
- W-23: body 完全保持を最優先とし、frontmatter 追加以外を行わない。`cli/lib/plan_frontmatter.py` 本体は編集しない。
- W-4: ADR-016 起票 + standalone lock primitive PoC のみ。実 critical path 接続および本番環境影響を伴う全面展開は PLAN-043 へ carry する。
- W-5: 3 Sprint 統合検証 + retrospective + push。

### §2.2 スコープ境界

- W-1: `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_filter_design_principle.md`（新規）と `MEMORY.md` の 1 行追記のみ。
- W-23: `docs/plans/PLAN-004-pm-reward-design.md` / `docs/plans/PLAN-005-ops-automation-skills.md` / `docs/plans/PLAN-006-upstream-meta-phase.md` の 3 件に限定。
- W-4: `docs/adr/ADR-016-*.md`（新規）+ `cli/lib/concurrent_lock.py`（新規）+ `cli/lib/tests/test_concurrent_lock.py`（新規）のみ。SQLite schema/migration、本番影響、handover 契約変更には踏み込まない。

### §2.3 既知問題

- PLAN-002 duplicate ID 問題は本 PLAN の解決対象外とし、risks / notes にのみ記載する。

### §2.4 参照関係

- PLAN-041 を直近の carry 集約例として参照する。
- PLAN-038 W-1 P3 debt を lock 機構 carry の起源として参照する。
- ADR-014 / ADR-015 をロール定義と orchestration の正本として参照する。

## §3 解決対象

### §3.1 W-1: filter design 原則の memory feedback 化

起源は PLAN-041 W-1 の副作用である。footer 内 literal `---SUMMARY_START---` / `---SUMMARY_END---` を concrete output 例として見せたことで、mock-codex 経由の STDOUT_FILE に流入し、emit_summary_from_capture が footer 例示 block を本物と誤認した。結果として mock の本物 summary block が抽出されず test fail になった。Opus の直接 fix で placeholder に差し替えたが、再発防止原則が必要である。

記録する原則は少なくとも次の 5 axis とする。

1. filter / parser / interpreter が見る範囲（output domain）と無視すべき範囲（specification domain）を明確に分離する。
2. 仕様文書（PROMPT / footer / docs）で marker を例示する場合は placeholder で示し、実際の marker は説明文のみで指定する。
3. concrete example の誘惑に注意する。LLM は example が具体的だと真似しやすいが、その example 自体が parser 干渉する場合がある。
4. filter の input source（STDIN / STDOUT_FILE / argv / env）を設計時に列挙し、各 source への流入経路を確認する。
5. test 時に「mock-codex に prompt を渡す経路で argv の内容が STDOUT_FILE に echo される」ような境界漏れ経路を意識する。

アウトプットは次の通り。

- `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_filter_design_principle.md` を新規作成する。
- frontmatter は YAML 表記で `name:` / `description:` / `type: feedback` / `originSessionId:` を含める。
- body には 5 axis + Why（PLAN-041 W-1 incident）+ How to apply（filter / parser 設計時 / Codex prompt footer 設計時）を含める。
- `MEMORY.md` へ「filter design 原則」インデックスを 1 行追記する。

### §3.2 W-23: legacy PLAN frontmatter progressive migration (3 件)

対象は次の 3 件とする。

- `docs/plans/PLAN-004-pm-reward-design.md`
- `docs/plans/PLAN-005-ops-automation-skills.md`
- `docs/plans/PLAN-006-upstream-meta-phase.md`

手順は PLAN-041 W-23 と同型とする。

1. 各 `.md` の body を読み込み、frontmatter 不在を確認する。
2. body から `plan_id` / `title` / `status` / `size` / `phases` / `gates` / `acceptance` / `related` を抽出する。
3. frontmatter block を冒頭に付加する。
4. body-preservation hash 検証として、frontmatter 除外部分の sha256 が一致することを確認する。

受入条件は次の通り。

- 3 ファイルすべてに frontmatter を付与する。
- `cli/lib/tests/test_plan_frontmatter.py` に body-preservation hash test を 3 ケース追加する。
- `cli/lib/plan_frontmatter.py` 本体は編集しない。

### §3.3 W-4: standalone lock primitive PoC（concurrent reader 中間状態観測不可保証の起点）

起源は PLAN-038 W-1 P3 debt であり、3 度 carry された候補である。本 PLAN では scope を絞った着手に格下げし、carry を止める。**実 critical path への接続は本 PLAN scope 外**とし、standalone な lock primitive PoC + ADR 起票に限定する。実 critical path 接続は PLAN-043 で行う。

#### 既存実装の現状（ADR-016 の前提）

- `cli/lib/handover.py` には既に ad-hoc な `fcntl.flock(LOCK_EX)` + `os.replace` での atomic write が存在する（lines 280 / 286 / 493 / 500 / 531）。
- `.helix/locks/` ディレクトリは未作成（`.helix/lock/` ではない、正式 path は `.helix/locks/<key>.lock`）。
- 共通 lock primitive module は未存在（`cli/lib/concurrent_lock.py` 等は未実装）。
- 結果として、handover 以外の critical path（`helix.db` SQLite write、`.helix/phase.yaml` 等）には locking が適用されていない。

#### フェーズ A: 設計（ADR-016 起票）

ADR-016 では次の必須項目を扱う。

- **既存 lock 実装の現状整理**: `cli/lib/handover.py` の ad-hoc flock 使用箇所、未保証点（race window、timeout 不足、retry なし）、移行しない範囲。
- **lock primitive 選定**: option A = `cli/lib/concurrent_lock.py` 共通 module 化（`fcntl.flock` ベース、`.helix/locks/<key>.lock` 統一）、option B = SQLite トランザクション活用、option C = 既存 ad-hoc 維持の 3 つを比較する。
- **推奨**: option A を採用し、handover.py の ad-hoc 実装は将来 PLAN で共通 module へ移行する。本 PLAN では handover.py は変更しない。
- **対象 critical path 優先度**（PLAN-043 以降の実装順）:
  1. `.helix/handover/CURRENT.json`（既に flock あり、共通 module へ統合）
  2. `helix.db` SQLite write transaction（skill_usage / handover state 等）
  3. `.helix/phase.yaml`（phase transition 時）
- **deadlock 回避**: lock acquire timeout default 5s、ordered acquisition は alphabetical lock name 順。

#### フェーズ B: standalone PoC 実装

- `cli/lib/concurrent_lock.py` を新規作成し、`acquire(name, timeout)`、`release(name)`、context manager を実装する。
- 実装方針は `fcntl.flock(LOCK_EX | LOCK_NB)` + retry loop with timeout とする。
- lock 配置 path は `.helix/locks/<key>.lock` で統一する（必要に応じて初回呼出で mkdir）。
- `cli/lib/tests/test_concurrent_lock.py` を新規作成し、race condition 回帰テスト 1 ケースを置く（2 process 同時 acquire で片方が timeout、または ordered serialization）。
- **既存 `cli/lib/handover.py` は変更しない**（PLAN-043 で共通 module 移行を扱う）。

受入条件は次の通り。

- ADR-016 が起票される（既存実装現状整理 / option A 採用根拠 / critical path 優先度 / deadlock 回避方針 を含む）。
- `cli/lib/concurrent_lock.py` が `acquire` / `release` / context manager を備えて動作する。
- `cli/lib/tests/test_concurrent_lock.py` の race condition test 1 ケースが PASS する。
- `cli/lib/handover.py` への接続は本 PLAN 外、PLAN-043 へ carry する。

### §3.4 W-5: 統合検証 + retrospective + push

役割境界（HELIX v2 ルール準拠）:

- **Codex SE / docs（W-1 / W-23 / W-4 委譲先）**: 変更ファイルとテスト結果の報告までに限定する。`git add` / `git commit` / `git push` は禁止。
- **Opus / PM（本 W-5 担当）**: 各 W の成果物を検証後に commit + push を行う。

W-5 の作業内容:

- `cli/helix-test` の全 PASS を確認する。
- `pytest cli/lib/tests/` の全 PASS を確認する。
- `bats cli/tests` の全 PASS を確認する。
- `.helix/retros/PLAN-042.md` を起票する。
- W-1 / W-23 / W-4 / W-5 各 commit を Opus が作成し、push origin/improvements/helix-overhaul を行う。

## §4 Sprint 構成

W-0（本 draft）→ TL Round 1 → 修正 → TL Round 2 → 修正 → Opus finalize commit → W-1 / W-23 / W-4 並列実装 → W-5 統合検証 + retro + push。

## §5 ゲート

- G1: §3.1〜§3.3 各 W の受入条件が draft で網羅されている。
- G2: TL 2 ラウンドで approve、設計凍結。
- G3: 各 W の対象ファイルと test ケースが特定されている。
- G4: W-5 統合検証で 0 failed、retrospective 起票。

## §6 検証戦略

- W-1: memory file 存在 + frontmatter valid + 5 axis 記述確認。
- W-23: `pytest test_plan_frontmatter.py` PASS（body-preservation hash 3 ケース）。
- W-4: `pytest test_concurrent_lock.py` PASS（race condition 1 ケース）+ ADR-016 存在確認。
- W-5: 統合 PASS + retro + push。

## §7 risks

- W-4 standalone lock PoC が想定より複雑化する場合は、PoC を実装無しに縮小し、ADR-016 のみで PLAN-042 を完了させ、PoC 実装は PLAN-043 へ carry する。
- PLAN-002 duplicate ID 問題（`PLAN-002-helix-fullauto-foundation.md` migrated 済 vs `PLAN-002-helix-inventory-foundation.md` legacy）は本 PLAN scope 外とし、PLAN-043 の §risks へ carry する。
- legacy frontmatter migration で plan_id 衝突またはその他の致命的問題が発生した場合は、W-23 を `blocked` とし、該当 1 件を explicit に PLAN-043 へ carry する（残り 2 件のみで受入条件達成扱いにはしない）。

## §8 carry rule

- W-4 PoC が PLAN-042 内で完了しない場合は、ADR-016 のみ起票し PoC は PLAN-043 へ carry する。
- legacy migration 残 11 件（W-23 で PLAN-004/005/006 を解消した後の残）+ PLAN-002 duplicate ID 別枠 1 件 = 計 12 件を PLAN-043〜046 で 3-5 件ずつ progressive 継続する。
  - 残 11 件: PLAN-007 / PLAN-008 / PLAN-009 / PLAN-010 / PLAN-011 / PLAN-012 / PLAN-013 / PLAN-014 / PLAN-015 / PLAN-016 / PLAN-028
  - 別枠 1 件: PLAN-002-helix-inventory-foundation.md（duplicate ID 解決込みで PLAN-043 以降）
- W-4 critical path 接続（`.helix/handover/CURRENT.json` / `helix.db` / `.helix/phase.yaml` への共通 module 適用）は PLAN-043 で扱う。
- filter design feedback memory が不十分な場合は、PLAN-043 で memory feedback 強化 Sprint を追加する。

