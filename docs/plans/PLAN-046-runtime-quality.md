---
plan_id: PLAN-046
title: 'PLAN-046（runtime quality 5 件集約解消 - PLAN-045 retro carry 4 件 + W-5）'
status: completed
completed: 2026-05-10
created: 2026-05-10
author: Docs (Codex)
priority: medium
size: M
phases_affected: cli/helix-doctor, cli/roles, cli/lib (allowed_files), SKILL_MAP / ROLE_MAP
parent_plan: PLAN-045
gates: G1, G2, G3, G4
acceptance:
  - effort_consistency: true
  - allowed_files_estimator: true
  - role_count_drift_resolved: true
  - pmo_doctor_consistency: true
  - budget_ui_divergence_documented: true
  - tests_all_pass: true
  - branch_minimal_footprint: true
verification_commands:
  effort_consistency:
    command: "helix doctor 2>&1 | grep -c 'role .*conf vs CLAUDE.md'"
    expected: "0"
  effort_consistency_anomaly:
    command: "pytest cli/lib/tests/test_helix_doctor_effort.py::test_detects_mismatch -q"
    expected: "PASS"
  allowed_files_estimator:
    command: "helix codex --role pg --task 'test' --auto-allowed-files --dry-run 2>&1 | grep -c 'allowed_files'"
    expected: "1 以上"
  role_count_drift_resolved:
    command: "helix doctor 2>&1 | grep -c 'cli/roles count drift'"
    expected: "0"
  pmo_doctor_consistency:
    command: "python3 -m pytest cli/lib/tests/test_helix_doctor_pmo.py -q"
    expected: "全 PASS"
  budget_ui_divergence_documented:
    command: "helix budget status 2>&1 | grep -c 'Anthropic console UI\\|UI 値'"
    expected: "1 以上"
  budget_ui_divergence_memory_feedback:
    command: "ls ~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_budget_anthropic_ui_divergence.md | wc -l"
    expected: "1"
  tests_all_pass:
    command: "cli/helix test"
    expected: "exit 0 / 0 failed (件数は drift 許容、参考値: shell 614+, pytest 1032+, bats 414)"
  branch_minimal_footprint:
    command: "git branch --list 'improvements/plan-046*' | wc -l"
    expected: "0"
related: [PLAN-045, PLAN-044, PLAN-043, PLAN-042, PLAN-038, ADR-014, ADR-016]
---

## §1 目的

PLAN-045 完遂後に carry された runtime quality の 5 件を、本 PLAN で集約して閉じる。

本 PLAN は、単なる文言修正や局所的な doctor 調整ではなく、runtime quality を 5 方向から同時に改善することを狙う。

1. effort 整合性を監査し、ロールごとの thinking 分布と文書記載の乖離を検出可能にする。
2. allowed_files の自動推定を導入し、委譲 Codex の手動列挙依存を減らす。
3. role count drift を解消し、実 role 数と文書の記載を 17 件で揃える。
4. PMO doctor consistency を回復し、pre-existing failure で落ちていた test を 2 件とも PASS に戻す。
5. budget 表記を精緻化し、Anthropic UI 値と helix 表示の metric 差異を明記する。

本 PLAN の焦点は、HELIX の実運用における「文書と実測のズレ」を減らし、TL / SE / Docs の各ロールが同じ前提で判断できる状態を作ることである。

## §2 全体方針

### §2.1 設計原則

- W-0 は draft 起草専任とし、実装ファイルの変更は行わない。
- W-1 は effort 整合性の監査と doctor 拡張であり、role conf / CLAUDE.md / SKILL_MAP / ROLE_MAP の整合確認を中心に据える。auto-thinking は opt-in 維持で、default は role conf の `codex_thinking` を正とする。
- W-2 は allowed_files 自動推定の導入であり、手動列挙の置き換えではなく fallback 付きの補助機能として設計する。
- W-3 は role count drift の文書修正であり、SKILL_MAP と ROLE_MAP を 17 role へ合わせる。
- W-4 は PMO doctor consistency の修正であり、config / doctor / test の 3 点を同じ前提へ揃える。
- W-5 は budget 表記の精緻化であり、Anthropic UI と helix 表示の差異を note と memory で明記する。
- W-final は統合検証、retro、push を担う。
- 工程表外の変更が必要になった場合は、interrupted / blocked として戻す。

### §2.2 スコープ境界

#### W-0: draft + TL review + finalize

- 本ファイル `docs/plans/PLAN-046-runtime-quality.md` のみを新規作成する。
- carry 5 件の解消方針、Sprint 構成、acceptance、risk を固定する。

#### W-1: effort 整合性監査 + helix doctor 拡張

- 対象: `cli/helix-doctor`
- 対象: `cli/roles/*.conf`
- 対象: `CLAUDE.md`
- 対象: `skills/SKILL_MAP.md`
- 対象: `cli/ROLE_MAP.md`
- 追加内容: codex_thinking 値と文書記載の整合チェック、warn の可視化、必要なら effort 利用統計の拡張
- sub-task W-1.A: helix-doctor に role conf vs CLAUDE.md/SKILL_MAP/ROLE_MAP の整合 check を追加し、warn として表示する。
- sub-task W-1.B: `--auto-thinking` の default 化は見送る。opt-in 維持とし、default は role conf の `codex_thinking` を使う。`helix-codex --thinking` 明示を無効化しない互換性を維持する。
- 文書追加: `cli/ROLE_MAP.md` または関連 docs に「auto-thinking は opt-in、default は role conf」を 1 行明記する。

#### W-2: allowed_files 自動推定

- 対象: `cli/helix-codex`
- 対象: `cli/lib/allowed_files_estimator.py` (新規候補)
- 対象: recommender 連動部分
- 追加内容: `--auto-allowed-files` flag、task description からの file 推定、fallback / user prompt

#### W-3: role count drift 解消

- 対象: `skills/SKILL_MAP.md`
- 対象: `cli/ROLE_MAP.md`
- 追加内容: role 一覧を 14 から 17 へ更新し、新 role の説明を追記する

#### W-4: PMO doctor consistency 解消

- 対象: `cli/roles/pmo-sonnet.conf`
- 対象: `cli/roles/pmo-haiku.conf`
- 対象: `cli/config/models.yaml`
- 対象: `cli/helix-doctor`
- 対象: `cli/lib/tests/test_helix_doctor_pmo.py`
- 追加内容: config mismatch の解消、doctor check の確認、test 2 件 PASS

#### W-5: budget UI 差明記 + memory feedback

- 対象: `cli/lib/budget_cli.py`
- 対象: `~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_budget_anthropic_ui_divergence.md`
- 追加内容: Anthropics UI と helix 表示の差異 note、ccusage cost-based metric と Anthropic console UI の違い、memory feedback の起票

#### W-final: 統合検証 + retro + push

- `cli/helix test` と `python3 -m pytest cli/lib/tests/ -q` の確認を行う。
- `docs/plans/PLAN-046*.md` の status を必要に応じて更新する。
- `.helix/retros/PLAN-046.md` を起票する。
- branch を整理して minimal footprint を維持する。

### §2.3 既知制約

- W-1 と W-4 は `cli/helix-doctor` を共有するため、先に effort / PMO の責務境界を固定する。
- W-2 の allowed_files 推定は false positive を起こしうるため、精度不足時は必ず手動列挙へ fallback する。
- W-3 は文書整備であって実装変更ではないが、doctor の count drift warn を消す前提条件になる。
- W-5 は軽量であり、UI metric の注記と memory feedback の追記のみを含む。
- 本 PLAN は本番影響・認証・決済・PII・ライセンス・外部 API 変更を含まない前提で進める。

### §2.4 参照関係

- [PLAN-045](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-045-runtime-debt-resolution.md) を直近の carry 解消例として参照する。
- [PLAN-044](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-044-phase-integrity-audit.md) を doctor drift 監査の前例として参照する。
- [PLAN-043](/home/tenni/ai-dev-kit-vscode/docs/plans/PLAN-043-consolidated-carry-resolution.md) を carry 収束の前例として参照する。
- [ADR-014](/home/tenni/ai-dev-kit-vscode/docs/adr/ADR-014-roles-config-format.md) と [ADR-016](/home/tenni/ai-dev-kit-vscode/docs/adr/ADR-016-concurrent-lock-primitive.md) を role / config の正本として参照する。

## §3 解決対象

### §3.1 W-1: effort 整合性監査 + helix doctor 拡張

PLAN-045 の retro で残った 1 つ目の carry は、effort 分布と文書整合の未監査である。

現状は `pg.conf medium 化` で二極化の一部が解消したが、他 role の effort 分布と文書整合の監査が未完了である。ここでは、ロールごとの thinking 設定と記載差分を doctor で見える化する。

#### 方針

1. `cli/roles/*.conf` の `codex_thinking` 値を列挙する。
2. `CLAUDE.md` と `skills/SKILL_MAP.md`、`cli/ROLE_MAP.md` の記載と突合する。
3. 不一致があれば warn として doctor に出す。
4. 可能であれば effort 利用統計を `skill_usage table` に拡張するが、これはオプション扱いとする。

#### 受入条件

- `helix doctor` で role conf と文書の不整合が warn として検出できる。
- effort 分布の監査結果が、実装前に TL が確認可能な粒度で残る。
- 既存の doctor 挙動を壊さない。
- 正常系: pytest fixture で全 role conf 整合 → doctor warn 0 件。
- 異常系: pytest fixture で role conf に強制不整合（例: `pg.conf` の `codex_thinking` を一時的に `high` に変更）→ doctor warn 1 件以上検出。

### §3.2 W-2: allowed_files 自動推定

PLAN-045 の retro carry #4 を引き継ぎ、委譲 Codex の `allowed_files` 手動列挙依存を減らす。

現状は `helix codex` の委譲時に `--allowed-files` を手動列挙する必要があり、抜けると Codex blocked が発生する。ここでは task description から file 候補を推定し、低精度時のみ fallback する。

#### 方針

1. `helix codex` に `--auto-allowed-files` を追加する。
2. task description から関連 file を推定する。
3. recommender 連動で候補抽出を強化する。
4. 推定精度が低い場合は user 確認 prompt か手動列挙へ fallback する。

#### 受入条件

- `--auto-allowed-files` 有効時に task description から file 候補を推定できる。
- 推定が不十分な場合に fallback できる。
- blocked 回避に寄与することが test か dry-run で確認できる。
- `cli/lib/allowed_files_estimator.py` の unit test が 5 件以上ある。
- 推定信頼度低時は manual `--allowed-files` で override でき、推定結果は `--auto-allowed-files` の suggestion として提示される。
- 推定結果が `--allowed-files` 注入経路に渡り、`helix-codex` 実行で実際に enforced されることを確認できる。
- false positive（含めるべきでないファイル）の検出 test がある。
- false negative（含めるべきファイルの抜け）の検出 test がある。

### §3.3 W-3: role count drift 解消

PLAN-045 の retro で残った 3 つ目の carry は、role 数の drift である。

`helix doctor` では「実測 17 / 文書記述 14」の warn が出ており、`cli/roles` の実 role 数と `SKILL_MAP` / `ROLE_MAP` の記載がズレている。これを本 PLAN で 17 件へ揃える。

#### 方針

1. `skills/SKILL_MAP.md` の「ロール一覧 (14)」を「(17)」へ更新する。
2. `cli/ROLE_MAP.md` も同じく 17 件に合わせる。
3. 新 role 追加分の説明を追記し、実 role 一覧と一致させる。

#### 受入条件

- `helix doctor` で `cli/roles count drift` warn が消える。
- `grep` で 17 件の role 一覧を確認できる。
- SKILL_MAP と ROLE_MAP の記載数が一致する。

### §3.4 W-4: PMO doctor consistency 解消

PLAN-045 の retro で残った 4 つ目の carry は、PMO の consistency failure である。

`test_helix_doctor_pmo::test_pmo_sonnet_consistency_pass` と `test_helix_doctor_pmo::test_pmo_haiku_consistency_pass` は PLAN-044 baseline で pre-existing failure として残っていた。ここでは PMO config と `cli/config/models.yaml` の mismatch を解消し、doctor の PMO check を整える。

#### 方針

1. `cli/roles/pmo-sonnet.conf` と `cli/roles/pmo-haiku.conf` を確認する。
2. `cli/config/models.yaml` と照合し、model / thinking の mismatch を解消する。
3. doctor の PMO check ロジックを確認し、必要なら修正する。
4. `test_helix_doctor_pmo` の 2 件を PASS に戻す。

#### 受入条件

- `python3 -m pytest cli/lib/tests/test_helix_doctor_pmo.py -q` が PASS する。
- PMO consistency の warn が doctor で解消される。
- model config と role config の整合が保たれる。

### §3.5 W-5: budget UI 差明記 + memory feedback

PLAN-045 retro carry の budget 表記を、Anthropic UI 値と helix 表示の差異が分かる形へ精緻化する。

`helix budget status` は ccusage の cost-based metric を表示するが、Anthropic console UI の quota / usage 表示とは同一ではない。ここでは、ユーザーが見ている UI 値と helix の表示値が異なる前提を note で明記し、memory にも同内容を残す。

#### 方針

1. `cli/lib/budget_cli.py` の budget note に、Anthropic console UI の値と helix の表示 metric が一致しない旨を追加する。
2. memory feedback に `extra-usage` のような組み込みコマンドは存在しないこと、UI 値は Anthropic console で確認すること、ccusage cost-based 値は Anthropic 内部 quota engine とは別系統であることを残す。
3. 乖離量は 5 pt 以上で明記し、単なる注意書きではなく解釈差として固定する。

#### 受入条件

- `helix budget status` 出力に「Anthropic console UI 値とは異なる metric」の note が表示される。
- memory feedback に `ccusage` と Anthropic UI の差分が 5 pt 以上で記載される。
- budget 関連の既存テストを壊さない。
- `budget_ui_divergence_documented` は 2 段で検証し、`budget_ui_divergence_in_output` と `budget_ui_divergence_memory_feedback` の両方を満たす。

## §4 Sprint 構成

W-0 で本 draft を起票し、TL review を 1-2 round で実施する。

推奨順序は以下とする。

1. W-2 ∥ W-3 ∥ W-5 を第 1 波として並列で進める。
2. W-1 の doctor 拡張で effort 整合性を可視化する。
3. W-4 で PMO consistency を回復する。
4. W-final で統合検証、retro、push を完了する。

この順序により、文書上の role 数と config の正本を先に揃え、その後の doctor / allowed_files / PMO 修正が drift なく追従できる。

## §4.1 依存表

| W | depends_on | reason | allowed_files |
|---|------------|--------|---------------|
| W-1 | (none) | doctor 拡張独立 | `cli/helix-doctor`, `cli/lib/tests/test_helix_doctor_effort.py`, `cli/ROLE_MAP.md`, `skills/SKILL_MAP.md` |
| W-2 | (none) | helix-codex 単独 | `cli/helix-codex`, `cli/lib/allowed_files_estimator.py` |
| W-3 | (none) | docs 単独 | `skills/SKILL_MAP.md`, `cli/ROLE_MAP.md` |
| W-4 | W-1 | doctor 修正 (W-1 拡張後) | `cli/helix-doctor`, `cli/roles/pmo-sonnet.conf`, `cli/roles/pmo-haiku.conf`, `cli/config/models.yaml`, `cli/lib/tests/test_helix_doctor_pmo.py` |
| W-5 | (none) | budget_cli 単独 | `cli/lib/budget_cli.py` + memory file |
| W-final | W-1〜W-5 | 統合検証 + push | `docs/plans/PLAN-046*.md`, `.helix/retros/PLAN-046.md` |

## §5 ゲート

- G1: carry 5 件の解消対象と受入条件が draft で網羅されている。
- G2: effort / allowed_files / role count / PMO のスコープ境界が明確である。
- G3: 対象ファイル、検証コマンド、fallback 方針が特定されている。
- G4: W-final で全 test PASS、retro 起票、branch 最小化が確認される。

## §6 検証戦略

- W-1: `helix doctor` の role conf vs 文書 warn を確認する。
- W-2: `helix codex --role pg --task 'test' --auto-allowed-files --dry-run 2>&1 | grep -c 'allowed_files'` で allowed_files 候補が出ることを確認する。
- W-2: `pytest cli/lib/tests/test_allowed_files_estimator.py -q` で 5 件以上 PASS することを確認する。
- W-3: `helix doctor` の `cli/roles count drift` warn が 0 になることを確認する。
- W-4: `python3 -m pytest cli/lib/tests/test_helix_doctor_pmo.py -q` で 2 件 PASS を確認する。
- W-5: `helix budget status 2>&1 | grep -c 'Anthropic console UI\\|UI 値'` で UI 差 note が出ることを確認する。
- W-5: `ls ~/.claude/projects/-home-tenni-ai-dev-kit-vscode/memory/feedback_budget_anthropic_ui_divergence.md | wc -l` で memory feedback の存在を確認する。
- W-final: `cli/helix test` の総合結果と branch footprint を確認する。
- W-final: `helix plan import --from-frontmatter で PLAN-046 を registry 登録 (commit 不要、yaml 出力のみ)` を確認する。

## §7 リスク

- W-1 の doctor 拡張は既存 warn 出力の期待値を変える可能性があるため、既存 test の文字列参照を確認する。
- W-2 の allowed_files 推定は誤推定のリスクがあるため、fallback を必須にする。
- W-4 の PMO inconsistency は config だけでなく doctor ロジック側の mismatch である可能性があるため、初手で root cause を切り分ける。
- W-1 と W-4 が doctor を共有するため、修正順序を誤ると回帰が起きやすい。
- W-5 は軽量で、budget note の明記と memory feedback の追記のみなので、機能リスクは低い。
- `auto-thinking` の default 化は採用せず、role conf 既定値を維持するため互換性リスクは低い。

## §8 成果物

- `docs/plans/PLAN-046-runtime-quality.md`

## §9 完了条件

1. PLAN-045 から carry された runtime quality 5 件がすべて解消される。
2. `helix doctor` の role / PMO warn が収束する。
3. `allowed_files` 自動推定の入口が draft として固定される。
4. `SKILL_MAP.md` と `ROLE_MAP.md` の role count drift が解消される。
5. `cli/lib/tests/test_helix_doctor_pmo.py` の 2 件が PASS する。
6. budget UI 差異の note と memory feedback が固定される。
