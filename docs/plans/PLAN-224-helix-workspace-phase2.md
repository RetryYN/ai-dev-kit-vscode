---
plan_id: PLAN-224
title: helix workspace Phase 2 (merge convenience + Layer 3 parallel lock + AC-6 symlink decision)
status: draft
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-24
authors:
  - PM (Opus)
agent_slots:
  - role: tl-advisor
    slot_label: "TL adversarial check — Phase 2 設計の妥当性 + symlink 採用判定 (AC-6)"
  - role: se
    slot_label: "SE — Sprint .2 merge subcommand 実装 (git diff --binary preflight + patch apply)"
  - role: qa
    slot_label: "QA — Sprint .3 Layer 3 parallel lock 競合 E2E 検証 (D8 Layer 3)"
  - role: pmo-sonnet
    slot_label: "PMO — Sprint .4 AC-6 decision review + ADR-041 起票判断"
generates:
  - artifact_type: python_module
    path: cli/lib/workspace_manager.py
  - artifact_type: cli_extension
    path: cli/helix-workspace
  - artifact_type: test
    path: cli/lib/tests/test_workspace_merge.py
  - artifact_type: doc_update
    path: docs/adr/ADR-040-helix-workspace-isolation.md
dependencies:
  parent: PLAN-156
  requires:
    - PLAN-156
  blocks: []
related_adr:
  - ADR-040-helix-workspace-isolation
related_docs:
  - docs/plans/PLAN-156-helix-workspace-worktree-isolation.md
  - docs/adr/ADR-040-helix-workspace-isolation.md
  - cli/lib/workspace_manager.py
  - cli/lib/tests/test_workspace_manager.py
  - docs/v2/L4-test-design/PLAN-156-integration-test-design.md
acceptance_criteria:
  - "helix workspace merge --task PLAN-X が git diff --binary preflight + patch apply で workspace 変更を main に取り込める"
  - "merge 時 main dirty の場合 abort + 明確なエラーメッセージ"
  - "merge conflict 時 workspace 保持 + conflict file 提示"
  - "D8 Layer 3 E2E: 2 workspace 並列で create / exec が helix-db.lock 競合なく完了"
  - "AC-6 symlink immutable snapshot 限定採用 判定が決着 (採用 / 不採用 / 条件付き)"
  - "採用判定なら ADR-041-helix-workspace-symlink-snapshot 起票 (新規 L2 snapshot)"
  - "python3 -m py_compile cli/lib/workspace_manager.py PASS"
  - "pytest cli/lib/tests/test_workspace_merge.py 全 PASS"
  - "ADR-040 §AC-5/AC-6 履歴に Phase 2 完遂記録追記"
---

# PLAN-224: helix workspace Phase 2 (merge convenience + Layer 3 parallel lock + AC-6 symlink decision)

## L2 凍結 (ADR snapshot)

本 PLAN は **ADR-040** (PLAN-156 tree の L2 snapshot) の Phase 2 carry を完了させる実装 PLAN。新規 L2 大局判断は **AC-6 symlink 採用判定** のみ。判定結果次第で:

- 採用 (immutable snapshot 対象限定で symlink 戦略を補助採用) → **ADR-041-helix-workspace-symlink-snapshot** を新規 L2 snapshot として起票
- 不採用 (Phase 2 でも完全採用見送り) → ADR-040 §AC-6 を「Phase 2 でも見送り、Phase 3 以降検討」と更新するのみ

`merge` 戦略は ADR-040 D4 で既に「git diff --binary preflight + patch apply convenience」と方針確定済、本 PLAN は実装のみ (新規 ADR 不要)。

Layer 3 並列 lock 競合検証は ADR-040 D3 設計 (workspace 内空 init DB) が機能することの実機検証であり、新規 L2 判断ではない (PASS 期待、FAIL 時のみ追加 ADR 候補)。

## 背景

PLAN-156 全 Sprint (.1-.4) 完遂で MVP scope (`create / list / exec / preflight / drop / prune`) は production-ready 状態。Phase 2 carry として ADR-040 で明示分離した以下 3 トピックを本 PLAN で完遂する:

1. **`helix workspace merge` convenience** (ADR-040 D4 Phase 2): 標準 git flow は維持しつつ、HELIX 独自の `workspace branch → main` 取り込み convenience を提供。main dirty 時 abort + binary file / rename / submodule 等の corner case を git 標準で安全に処理。
2. **D8 E2E Layer 3 並列 lock 競合検証** (ADR-040 D8 Layer 3): 2 workspace 同時 create / exec で helix-db.lock 競合が発生しないことを E2E 確認。ADR-040 D3 設計 (workspace 内空 init DB) の機能保証。
3. **AC-6 symlink 戦略採用判定** (ADR-040 AC-6): immutable snapshot 対象 (例: `.helix/templates/`、`config/` の read-only 部分) のみ symlink 採用を検討。実装複雑度と再現性低下リスクを weigh して decision を下す。

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は AC-6 symlink 採用判定 (新規 L2 大局判断) を含むため、Sprint .1 で **WebSearch 3 query 必須**:

実施予定 (Sprint .1 entry 時に Opus 直接):

1. `git worktree symlink immutable snapshot pattern 2026` — symlink を immutable snapshot 対象に限定する pattern の妥当性確認
2. `filesystem symlink readonly mount immutable 2026 best practices` — immutable filesystem 設計の業界 standard
3. `parallel test isolation sqlite WAL lock contention 2026` — Layer 3 検証時の SQLite WAL mode 振る舞い (PLAN-156 Sprint .1 で実施済の query を補完)

検索結果は ADR-041 起票時 §Context に転記 (採用判定なら)、または ADR-040 §AC-6 履歴に転記 (不採用判定なら)。

## 実装計画

### Sprint .1: 設計確定 + tl-advisor adversarial check

**担当**: Opus + tl-advisor

**作業**:

1. WebSearch 3 query 実施 + 結果を本 PLAN §WebSearch 履歴 に記録
2. merge 戦略の細部仕様確定:
   - `git diff --binary <workspace_branch> <main_ref> > /tmp/<task>-merge.patch` (binary file 対応)
   - main workspace で `git apply --check` で preflight、success なら `git apply` で適用
   - main dirty なら abort (`git status --porcelain` が non-empty)
   - 失敗時 conflict patch を `~/.helix/workspace-trash/<task>/<ts>/merge-conflict.patch` に保存
3. Layer 3 並列検証の test 設計:
   - 2 workspace を同時 create → 各 workspace 内で同時 exec → helix-db.lock 競合が出ないこと
   - 検証は subprocess.Popen + `time` で同時起動、両 exit 0 確認
4. AC-6 symlink decision の判定基準明確化:
   - 採用: `.helix/templates/` 等の immutable な read-only 部分のみ symlink、それ以外は materialized copy 維持
   - 不採用: 全 immutable 部分も materialized copy (符号化 cost は数 KB で許容)
5. **tl-advisor 召喚** (helix codex --role tl-advisor):
   - merge 仕様の corner case 抜け
   - Layer 3 検証手法の妥当性
   - AC-6 採用判定基準の整合性

**完了条件**:

- ✓ WebSearch 3 query 完了
- ✓ tl-advisor adversarial check 受領 (changes_required 時は本 PLAN 修正)
- ✓ 各 Sprint の細部仕様確定

### Sprint .2: merge subcommand 実装

**担当**: Codex SE

**作業**:

1. `WorkspaceManager.merge(task_id, *, target_ref="main", abort_on_dirty=True)`:
   - main repo の `git status --porcelain` 確認 (dirty なら abort)
   - workspace branch HEAD と main の `git diff --binary` 生成
   - `git apply --check` で preflight
   - PASS なら main workspace に apply、registry status を `merged` に遷移
   - FAIL なら conflict patch を trash に保存、WorkspaceMergeConflictError raise
2. `helix workspace merge --task PLAN-X [--target-ref main] [--no-abort-on-dirty]` の workspace_cli.py 分岐実装
3. `cli/helix-workspace` help text に `merge` 追記
4. 新 exception class `WorkspaceMergeConflictError` (WorkspaceManager) + main dirty error class

**完了条件**:

- ✓ python3 -m py_compile cli/lib/workspace_manager.py PASS
- ✓ bash -n cli/helix-workspace PASS
- ✓ helix workspace merge --help 動作

### Sprint .3: D8 Layer 3 並列 lock 競合 E2E 検証

**担当**: Codex QA + Opus 直接

**作業**:

1. `cli/lib/tests/test_workspace_merge.py` 新規:
   - merge subcommand 単体テスト 8 case (上記 acceptance_criteria 基準)
   - main dirty で abort
   - patch apply success / conflict 両方 verify
2. `cli/lib/tests/test_workspace_parallel.py` 新規 (Layer 3 検証):
   - 2 workspace 同時 create (subprocess.Popen × 2、両 join 待ち)
   - 各 workspace 内で同時 exec (Codex 委譲不要、軽量 bash command で十分)
   - 両者 exit 0 + lock 競合 0 確認
3. Layer 3 E2E 実機:
   - `./cli/helix workspace create --task PLAN-224-LAYER3-A & ./cli/helix workspace create --task PLAN-224-LAYER3-B & wait`
   - 並列 exec で互いに干渉しないことを実機確認
   - PASS なら ADR-040 §AC-5/D8 履歴に Layer 3 PASS 記録
   - FAIL なら lock 設計改善 (workspace 別 lock_dir に分離する設計案を新規 ADR-XXX 起票)

**完了条件**:

- ✓ test_workspace_merge.py 8 case PASS
- ✓ test_workspace_parallel.py 2 case PASS (並列 create + 並列 exec)
- ✓ 実機 Layer 3 E2E PASS or FAIL 時の追加 ADR 起票

### Sprint .4: AC-6 symlink decision + ADR 更新

**担当**: pmo-sonnet + Opus

**作業**:

1. Sprint .1 で確定した判定基準と実測 (filtered copy cost、再現性影響、symlink readonly 担保性) を比較
2. 判定:
   - **採用** → ADR-041-helix-workspace-symlink-snapshot 起票 (Accepted with conditions、本 PLAN Sprint .4 完了で Accepted)
   - **不採用** → ADR-040 §AC-6 を「Phase 2 でも見送り (理由: filtered copy で数 KB 範囲、symlink readonly 担保が OS 依存で再現性低下)」と更新
3. ADR-040 §AC-5/D8 履歴に Layer 3 結果 (PASS / FAIL) 反映
4. ADR-040 Status History に Phase 2 完遂記録追記 (本 commit 紐付け)

**完了条件**:

- ✓ AC-6 decision 確定 + 該当 ADR 更新
- ✓ ADR-040 §AC-5/D8 履歴に Layer 3 結果反映

### Sprint .5: 統合 test + DoD 確認 + commit

**担当**: Opus

**作業**:

1. 全 unit test 回帰確認 (workspace 関連 + helix_db 既存)
2. helix doctor 21 pass / 0 fail 維持確認
3. docs/commands/index.md に `merge` subcommand 追記
4. 全 commit を整理 (1 Sprint = 1 commit 推奨、3-4 commit 想定)
5. handover update + memory feedback 永続化

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/workspace_manager.py` PASS
- [ ] `bash -n cli/helix-workspace` PASS
- [ ] `pytest cli/lib/tests/test_workspace_merge.py cli/lib/tests/test_workspace_parallel.py -v` 全 PASS
- [ ] WebSearch 3 query 完了 + 記録済 (PLAN-087 ガード遵守)
- [ ] tl-advisor adversarial check 受領 (Sprint .1)
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .4 AC-6 decision 時)
- [ ] commit message に `PLAN-224 sprint .X` 明示

## DoD (Definition of Done)

- [ ] `helix workspace merge --task PLAN-X` が動作 (main dirty abort + binary file 対応 + conflict 時 trash 退避)
- [ ] D8 Layer 3 並列 lock 競合 E2E PASS (2 workspace 同時 create / exec で競合 0)
- [ ] AC-6 symlink decision 確定 (採用 / 不採用)
- [ ] ADR-040 §AC-5/D8/AC-6 履歴に Phase 2 完遂記録反映
- [ ] (採用判定時のみ) ADR-041 起票 (Accepted)
- [ ] python3 -m py_compile + bash -n PASS
- [ ] unit test 10+ case 全 PASS
- [ ] docs/commands/index.md に merge subcommand 追記済

## carry / 学び (起票時記録)

- **新規 L2 大局判断は AC-6 のみ**: merge / Layer 3 は ADR-040 で既に方針確定済、本 PLAN は実装層。AC-6 採用判定のみ新規 ADR-041 起票候補
- **tl-advisor 召喚は Sprint .1 で必須**: ADR-040 で実証済の pattern (PLAN-156 Sprint .1)。Phase 2 でも同じく adversarial check 通す
- **Layer 3 FAIL 時の fallback**: workspace 別 lock_dir 分離設計を新規 ADR で起票。FAIL を pre-empt して設計案を Sprint .1 で merge 仕様と同時に考えておく
- **AC-6 判定の判断軸**: filtered copy cost (実測 KB-MB 範囲) vs symlink 再現性低下リスク。後者が前者を上回るなら不採用が妥当

## 関連 reference

- [[PLAN-156]] (parent PLAN、Phase 1 完遂、本 PLAN の前提)
- [[feedback_codex_workspace_exec_d8_sentinel_pattern]] (D8 E2E 検証 pattern、Layer 3 で再利用)
- [[feedback_adr_before_plan_violation]] (本 PLAN tree の L2 大局判断 = AC-6、採用判定なら ADR-041 起票が PLAN ⊃ ADR レイヤー併存)
- [[feedback_design_doc_web_search_test_design_scope]] (PLAN-087 ガード遵守、Sprint .1 で 3 query 必須)
- ADR-040 (本 PLAN の親 ADR、Phase 2 carry を完遂)
- PLAN-163 (前 session 連続起票で作成、本 PLAN-156 で吸収完遂、superseded)
