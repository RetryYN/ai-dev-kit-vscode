---
plan_id: PLAN-043
title: 'PLAN-043（PLAN-042 retro carry 9 件集約解消 - small bug fixes + legacy progressive + lock critical path 接続 + 機能追加）'
status: completed
created: 2026-05-10
finalized: 2026-05-10
completed: 2026-05-10
author: Opus (PM)
size: M
phases: L1→L2→L3→L4
gates: G1, G2, G3, G4
acceptance:
  - W-1: skill chain double-path bug 修正、--consent 運用 memory feedback、Codex sandbox bootstrap runbook 拡張
  - W-2: legacy PLAN frontmatter migration 5 件追加 (PLAN-007〜011 progressive)
  - W-3: lock 機構 critical path 接続 (handover.py を concurrent_lock module へ移行)、lockfile cleanup は split-lock 回避のため本 PLAN scope 外
  - W-4: helix plan import コマンド追加 + helix doctor 文書 drift 検知拡張 + accuracy_score 経路修復
  - W-6: PreToolUse hook で Opus の repo Edit/Write を mechanical block、5 ケース bats test PASS
related: [PLAN-042, PLAN-041, PLAN-040, PLAN-038, ADR-014, ADR-015, ADR-016]
---

## §1 目的

PLAN-042 retro および本セッションの carry / findings を 1 PLAN で集約解消する。

1. skill chain の path 解決、Codex consent 運用、sandbox bootstrap の runbook を整備し、small bug fixes を閉じる。
2. legacy PLAN markdown の frontmatter を progressive に後付けし、parser / lint の正規経路を増やす。
3. lock 機構を critical path に接続し、handover / lockfile の共通 primitive への移行を進める。
4. plan import / doctor / accuracy_score の 3 つの機能追加で、文書と実測の drift を減らす。

scope は大きいが、各 W は独立で並列衝突がない前提とする。

## §2 全体方針

### §2.1 設計原則

- W-1: 副作用ゼロの bug fix と memory / runbook 記録のみ。
- W-2: PLAN-040〜042 と同じ progressive migration パターンを継続し、`cli/lib/plan_frontmatter.py` 本体は編集しない。
- W-3: PLAN-042 W-4 で起票した `cli/lib/concurrent_lock.py` を実 critical path へ展開し、ad-hoc `flock` を共通 module へ統合する。
- W-4: 機能追加 3 件を並列実装する。
- W-5: 統合検証 + retro + push は Opus 担当とする。

### §2.2 スコープ境界

#### W-1: small bug fixes (3 件並列)

- §3.1.A: `cli/lib/skill_dispatcher.py` の `_safe_reference_path` で repo-relative path 検出と正規化を修正する。
- §3.1.B: `~/.claude/projects/.../memory/feedback_codex_consent_rules.md` を新規作成し、`MEMORY.md` を追記する。
- §3.1.C: `docs/runbook/codex-test-bootstrap.md` に `TMPDIR` 環境変数注入手順を追加する。

#### W-2: legacy PLAN frontmatter migration 5 件

- 対象 5 件に frontmatter 後付けを行う。
- body-preservation hash test を 5 件追加する。
- `cli/lib/plan_frontmatter.py` 本体は変更しない。

#### W-3: lock 機構 critical path 接続

- `cli/lib/handover.py` の ad-hoc `fcntl.flock` を `cli/lib/concurrent_lock.py` の file lock context manager へ移行する。
- release 時の lockfile unlink は **行わない** (split-lock 回避、§3.3 詳細参照)。
- `pytest cli/lib/tests/test_handover.py` に race condition test を追加する。
- `helix.db` SQLite write transaction / `.helix/phase.yaml` は本 PLAN scope 外とする。

#### W-4: medium features (3 件並列)

- §3.4.A: `helix plan import --from-frontmatter` サブコマンドを追加する。
- §3.4.B: `helix doctor` を拡張し、skills/ `.claude/agents/` `cli/roles/` の実測値を `SKILL_MAP.md` / `ROLE_MAP.md` と突合する。
- §3.4.C: `helix codex` の終了時 hook で TL レビュー output から `overall_scores` を抽出し、`accuracy_score` table へ INSERT する。

#### W-5: 統合検証 + retro + push

- `cli/helix-test` の全 PASS を確認する。
- `pytest` 全 PASS を確認する。
- `bats` 全 PASS を確認する。
- `.helix/retros/PLAN-043.md` を起票する。
- W-1〜W-4 各 commit + push `<working>:main` fast-forward + branch cleanup を Opus が行う。

### §2.3 既知制約

- PLAN-020〜037 の `accuracy_score` backfill は audit log 不在で永久不能とする。W-4.C は将来 plan からの記録経路修復のみ扱う。
- legacy frontmatter 残 7 件は PLAN-044+ で progressive 継続する。
- `helix.db` / `.helix/phase.yaml` への lock module 接続は PLAN-044 carry とする。

### §2.4 参照関係

- [PLAN-042](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-042-filter-design-and-legacy-and-lock-poc.md) を直近の集約 PLAN として参照する。
- [PLAN-038](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-038-codex-prompt-and-plan-workflow-tightening.md) の W-1 P3 debt を参照する。
- [ADR-016](/home/tenni/ai-dev-kit-vscode/docs/adr/ADR-016-concurrent-lock-primitive.md) の concurrent lock primitive を W-3 で活用する。

## §3 解決対象

### §3.1 W-1: small bug fixes と memory feedback

起源は PLAN-042 retro carry のうち、実装面の小修正と運用記録で閉じられる 3 件である。

#### §3.1.A skill chain double-path bug 修正

- `_safe_reference_path` で repo-relative path を検出し、canonical path に正規化する。
- path 由来の二重解釈を避け、reference chain の分岐を 1 系列へ固定する。
- 既存の外部 path 解決を壊さず、safe path のみを正規化対象とする。

#### §3.1.B `--consent` 運用 memory feedback

- Codex consent の運用ルールを memory として記録する。
- consent の有無で bootstrap / fallback の分岐を変える際の注意点を明示する。
- 記録は feedback 形式に限定し、既存 memory の破壊は行わない。

#### §3.1.C Codex sandbox bootstrap runbook 拡張

- `TMPDIR` を明示注入する手順を runbook に追加する。
- sandbox bootstrap の再現性を上げ、`helix-test` 実行時の temp path 不整合を抑える。
- 実行例は最小限にし、環境依存の説明を短く保つ。

### §3.2 W-2: legacy PLAN frontmatter progressive migration (5 件)

対象は次の 5 件とする。

- `docs/plans/PLAN-007-*.md`
- `docs/plans/PLAN-008-*.md`
- `docs/plans/PLAN-009-*.md`
- `docs/plans/PLAN-010-*.md`
- `docs/plans/PLAN-011-*.md`

手順は PLAN-041 / PLAN-042 と同型とする。

1. 各 `.md` の body を読み込み、frontmatter 不在を確認する。
2. body から `plan_id` / `title` / `status` / `size` / `phases` / `gates` / `acceptance` / `related` を抽出する。
3. frontmatter block を冒頭に付加する。
4. body-preservation hash 検証として、frontmatter 除外部分の sha256 が一致することを確認する。

受入条件は次の通り。

- 5 ファイルすべてに frontmatter を付与する。
- `cli/lib/tests/test_plan_frontmatter.py` に body-preservation hash test を 5 ケース追加する。
- `cli/lib/plan_frontmatter.py` 本体は編集しない。

### §3.3 W-3: lock 機構 critical path 接続 (handover 接続のみ)

起源は PLAN-042 W-4 で起票した concurrent lock PoC である。本 PLAN ではそれを **既存 standalone PoC として承継**し、handover の ad-hoc flock を共通 module 経由に移行する。

#### 既存実装の現状 (PLAN-042 W-4 で起票済み)

- **`cli/lib/concurrent_lock.py` は既に存在** (PLAN-042 commit `147fead`、ADR-016 採択):
  - API: `acquire(name: str, timeout: float = 5.0) -> int (fd)`
  - API: `release(fd: int) -> None`
  - API: `@contextmanager file_lock(name: str, timeout: float = 5.0)`
  - 実装: `fcntl.flock(LOCK_EX | LOCK_NB)` + retry loop、`.helix/locks/<key>.lock` 配置、name validation 済み
  - 5 ケース test PASS 済み (basic / context_manager / race_condition / timeout / invalid_name)
- `cli/lib/handover.py` には ad-hoc な `fcntl.flock(LOCK_EX)` (lines 280/286) と `os.replace` (lines 493/500/531) が存在 (PLAN-042 W-4 では編集禁止 scope だった)。
- `handover` 以外の critical path (helix.db / phase.yaml) は本 PLAN scope 外 (PLAN-044+ で扱う)。

#### W-3 作業内容

- **PoC module の再実装は不要**。既存 `cli/lib/concurrent_lock.py` をそのまま使用する。
- `cli/lib/handover.py` の ad-hoc flock 使用箇所 (lines 280/286) を `concurrent_lock.file_lock(name)` context manager 経由に移行する。
- 既存 `os.replace` (lines 493/500/531) は atomic write として継続使用する (lock とは別 concern)。
- race condition 回帰テストを `cli/lib/tests/test_handover.py` に 2 ケース追加 (既存 31 ケース + 新規 2 ケース = 33)。

#### lockfile cleanup について (race リスク回避)

TL Round 1 P1 指摘により、**lockfile unlink は本 PLAN scope 外**とする。理由:

- `flock` lockfile を release 時に unlink すると、待機中プロセスと新規プロセスが別 inode を掴む **split-lock リスク**がある。
- lockfile は `.helix/locks/<key>.lock` に安定配置のまま維持し、cleanup が必要なら別タスクで安全条件 (e.g., orphan detection + atomic unlink-with-flock) を設計する。

PLAN-042 retro #9 stale lock cleanup automation はこの理由で **本 PLAN では undertake しない**。安全な cleanup 設計 (orphan detection + atomic unlink-with-flock 等) は PLAN-044+ で扱う (リスク評価が必要)。

#### 受入条件

- `cli/lib/handover.py` の ad-hoc flock が `cli/lib/concurrent_lock.file_lock(name)` 経由に移行している。
- 既存 handover test (test_handover.py 31 ケース) が PASS する。
- 新規 race condition test 2 ケース (handover.CURRENT.json 同時 write 競合) が PASS する。
- `cli/lib/concurrent_lock.py` 本体は変更しない (PLAN-042 で凍結済み)。
- `.helix/phase.yaml` / `helix.db` / lockfile cleanup は本 PLAN 外で PLAN-044+ carry。

### §3.4 W-4: medium features 3 件

#### §3.4.A `helix plan import --from-frontmatter`

- `docs/plans/PLAN-*.md` の frontmatter から `.helix/plans/PLAN-NNN.yaml` を再生成する。
- import は再現可能であることを重視し、本文からは派生しない項目を増やさない。
- 新規 `cli/helix-plan-cmds/import.sh` を追加し、test は **`cli/lib/tests/test_helix_plan_import.py`** (新規ファイル) に分離する (W-2 の test_plan_frontmatter.py とは独立)。

#### §3.4.B `helix doctor` の drift 検知

- `skills/` 数、`.claude/agents/` 数、`cli/roles/` 数を実測する。
- `SKILL_MAP.md` / `ROLE_MAP.md` の記述値と突合し、差異があれば warn を出す。
- warn は drift の可視化に限定し、自動修復は行わない。

#### §3.4.C `accuracy_score` 記録経路修復

- `helix codex` 終了時 hook (`cli/helix-codex` の post-processing) から TL レビュー output の `overall_scores` JSON 形式 (`{"dimension":..., "level":..., "comment":...}`) を抽出する。
- `accuracy_score` table への INSERT を行い、レビュー output の履歴を残す。
- 既存実装との重複防止 (責務分界):
  - `cli/lib/feedback_hook.py` (G2/G4 ゲート評価記録) とは別経路 (本 W-4.C は **TL レビュー output 経由のみ**、PM/PE 出力は対象外)
  - `cli/lib/review_output.py` (もしあれば) との INSERT 重複防止のため `reviewer='codex-tl'` + `evidence='source=helix-codex-post-hook'` で識別
  - 重複 INSERT 検出時は skip (UNIQUE 制約 or precheck)
- fail-open 方針 (score 抽出失敗で `helix codex` 自体を fail させない、warn のみ stderr 出力)
- audit log 不在の過去 plan を復元しない。

受入条件は次の通り。

- plan import が frontmatter ベースで再生成できる、test は test_helix_plan_import.py に分離。
- doctor が実測と文書差異を warn する。
- accuracy_score の新規記録が残る、reviewer='codex-tl' + source 識別で他経路との重複を防止。

### §3.5 W-5: 統合検証 + retrospective + push

### §3.6 W-6: orchestration enforcement (PreToolUse hook)

起源は本セッション (2026-05-10) で観測した複数の Opus 直接 Edit 違反である。policy は CLAUDE.md / memory feedback で明文化されているが、mechanical enforcement が存在しないため、PreToolUse hook で repo 直接編集を block する。

#### 既存実装の現状

- `.claude/hooks/` ディレクトリは存在し、PreToolUse / PostToolUse / SessionStart 等の hook 配備済みである。
- Opus の Edit / Write / MultiEdit 呼出を block する hook は未存在である。
- 現状の予防策は Opus 自身の self-discipline のみであり、本セッションで複数回スリップが確認されている。

#### 実装内容

1. 新規 hook script: `.claude/hooks/pretooluse-opus-repo-block.sh`
   - PreToolUse hook として Edit / Write / MultiEdit ツール呼出時に発火する。
   - `tool_input` から `file_path` を抽出する。
   - `file_path` が repo root (`$HELIX_ROOT`) 以下かをチェックする。
   - 以下に該当する場合は block する。
     - `file_path` が repo root 内
     - かつ memory dir (`~/.claude/projects/.../memory/`) 外
     - かつ exception path にマッチしない
   - block 時メッセージ: `PM (Opus) は repo file を直接 Edit/Write できません。helix codex --role <pg|se|docs> --task ... で委譲してください`

2. exception paths (許可される Opus 直接 Edit)
   - `docs/plans/PLAN-*.md` (PLAN draft TL review followup small fix、`HELIX_ALLOW_OPUS_PLAN_FIX=1` で許可、ただし 30 行超の編集は block)
   - `.helix/` (gitignored runtime state)
   - 一時的 escape hatch: `HELIX_ALLOW_OPUS_REPO_EDIT=1` + `HELIX_OPUS_EDIT_REASON='<reason>'` 必須

3. `settings.json` 登録: `.claude/settings.json` の `hooks.PreToolUse` セクションに登録し、既存 hook 群と並列に動作させる。

4. test: `cli/tests/test-pretooluse-opus-repo-block.bats` (新規)
   - `test_block_repo_python_edit`: `Edit cli/lib/budget.py` が block される。
   - `test_block_repo_docs_edit`: `Edit docs/architecture/x.md` が block される。
   - `test_allow_memory_dir`: `Edit ~/.claude/.../memory/x.md` が許可される。
   - `test_allow_plan_md_with_env`: `Edit docs/plans/PLAN-NNN-*.md` が `HELIX_ALLOW_OPUS_PLAN_FIX=1` で許可される。
   - `test_escape_hatch`: `HELIX_ALLOW_OPUS_REPO_EDIT=1` + reason 設定で許可される。

#### 受入条件

- `.claude/hooks/pretooluse-opus-repo-block.sh` が新規追加され、`bash -n` を通過する。
- `.claude/settings.json` に hook 登録され、JSON valid である。
- bats test 5 ケース PASS。
- 既存 hook (他の PreToolUse / PostToolUse 等) を破壊しない。
- `HELIX_SUPPRESS_HOOK=1` で hook を一時無効化できる。

役割境界は HELIX v2 ルールに準拠する。

- Codex SE / docs は変更ファイルとテスト結果の報告までに限定する。`git add` / `git commit` / `git push` は禁止する。
- Opus / PM は各 W の成果物を検証後に commit + push を行う。

W-5 の作業内容:

- `cli/helix-test` の全 PASS を確認する。
- `pytest cli/lib/tests/` の全 PASS を確認する。
- `bats cli/tests` の全 PASS を確認する。
- `.helix/retros/PLAN-043.md` を起票する。

W-6 は以下を満たす。

- Opus の repo Edit / Write / MultiEdit を mechanical block する。
- 5 ケース bats test を追加し、全 PASS を確認する。
- 既存 hook chain と干渉しない。

## §4 Sprint 構成

W-0（本 draft）→ TL Round 1 → 修正 → TL Round 2 → 修正 → Opus finalize commit → W-1 / W-2 / W-3 / W-4 並列実装 → W-5 統合検証 + retro + push。

## §5 ゲート

- G1: §3.1〜§3.6 各 W の受入条件が draft で網羅されている。
- G2: TL 2 ラウンドで approve、設計凍結。
- G3: 各 W の対象ファイルと test ケースが特定されている。
- G4: W-5 統合検証で 0 failed、retrospective 起票。

## §6 検証戦略

- W-1.A: skill chain double-path bug 修正 + **regression test 追加** (repo-relative path で `_safe_reference_path` が二重連結しないこと、test_skill_dispatcher.py に 1 ケース)
- W-1.B: memory file `feedback_codex_consent_rules.md` 存在 + frontmatter valid 確認
- W-1.C: docs/runbook/codex-test-bootstrap.md に TMPDIR 注入手順追記の差分確認
- W-2: `pytest test_plan_frontmatter.py` PASS（body-preservation hash 5 ケース）
- W-3: `pytest test_handover.py` PASS (既存 31 + 新規 race condition 2 ケース)、`test_concurrent_lock.py` 5 ケース PASS 維持
- W-4: plan import / doctor / accuracy_score の smoke test PASS、test_helix_plan_import.py 独立確認
- W-5: 統合 PASS + retro + push。
- W-6: PreToolUse hook の mechanical block と 5 ケース bats PASS。

## §7 risks

- W-3 の lock 統合が想定より複雑化する場合は、`cli/lib/handover.py` の移行を縮小し、共通 primitive と race 回帰の安定化を優先する。
- legacy frontmatter migration で plan_id 衝突または致命的問題が発生した場合は、W-2 を `blocked` とし、該当 1 件を explicit に PLAN-044 へ carry する。
- W-4 の `accuracy_score` 経路が `helix codex` post-hook 改修で本体動作に副作用を起こす場合は、fail-open に倒し記録機能を skip 可能にする。過去 backfill は audit 不在で永久不能。
- W-6 hook が誤検出で正当な Opus 直接 Edit を過剰 block するリスクは、exception path の網羅と escape hatch (`HELIX_ALLOW_*`) で緩和する。
- W-6 hook が他の PreToolUse hook (既存 secrets scan 等) と干渉するリスクは、exit code 2 で permission denied とし、他 hook は別 chain で動作させる。
- **PLAN-002 duplicate ID 問題** (`PLAN-002-helix-fullauto-foundation.md` migrated 済 vs `PLAN-002-helix-inventory-foundation.md` legacy): 本 PLAN scope 外。PLAN-044+ で plan_id 衝突解決込みで扱う (PLAN-042 §7 から継続 carry)。

## §8 carry rule

- W-3 critical path 接続で `.helix/handover/CURRENT.json` 以外の対象に lock 必要性が広がる場合は、対象を一覧化して PLAN-044 へ carry する。
- legacy migration 残 7 件は PLAN-044+ で progressive 継続する。
- `helix.db` / `.helix/phase.yaml` への共通 module 適用は PLAN-044 carry とする。
- W-6 で block 検出された Opus 直接 Edit 試行は audit log に記録 (`.helix/audit/opus-block-events.log`) し、後続 PLAN で振り返る。
- `docs/plans/PLAN-012-*.md` 以降の追加 frontmatter は本 PLAN で扱わない。
