---
plan_id: L7-merge-settings-hook-ordering-fixplan
title: "L7-merge-settings-hook-ordering-fixplan: merge_settings hook ordering / custom hook preserve fix"
kind: impl
layer: L7
drive: be
status: draft
revised: '2026-05-25'
process_layer: L7
parent_design: docs/v2/CONCEPT.md
pairs_test_design: []
dependencies:
  parent: null
  requires:
    - HELIX-workflows/HELIX-process-L0-L14.md
  blocks: []
agent_slots:
  - role: se
    slot_label: "SE — merge_settings.py root cause fix + TDD 5 case 実装"
  - role: qa
    slot_label: "QA — pytest / security hardening 回帰確認"
generates:
  - artifact_path: docs/plans/L7/L7-merge-settings-hook-ordering-fixplan.md
    artifact_type: design_doc
  - artifact_path: cli/lib/merge_settings.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_merge_settings.py
    artifact_type: test
  - artifact_path: cli/lib/tests/test_security_hardening.py
    artifact_type: test
---

## §0 PLAN concept

`cli/lib/merge_settings.py` が canonical HELIX hook を再配置する際、同一 entry 内の custom hook を HELIX hook と同一視して削除する不具合を root cause から修正する。対象は `_is_helix_hook` の厳密化だけで終えず、canonical hook 順序保証、custom hook 保持、remove 時の HELIX hook のみ除去、冪等性まで含めて `settings.json` 再生成バグを止血する。

## §1 背景

- 2026-05-22 に同系統の `feedback_merge_settings_helix_hook_judge_bug` が発生したが、`SessionStart` / `PostToolUse` の mixed entry 保持までは未修正だった。
- 2026-05-25 の W4 で `.claude/settings.json` が本 wave で hook 非変更にもかかわらず再生成され、`sessionstart-history-injection.sh` 消失、SessionStart 順序変動、`test_security_hardening` fail が再発した。
- tl-advisor 助言で「W6-A 単独直列先行、TDD 5 case 必須」と判定済みであり、本 PLAN はその実装正本とする。

## §2 scope

1. `cli/lib/merge_settings.py` の HELIX hook 判定を canonical command 完全一致へ限定する。
2. event / matcher ごとに canonical HELIX hook を順序固定で維持しつつ、同一 entry 内の custom hook を保持できる merge/remove ロジックへ修正する。
3. `cli/lib/tests/test_merge_settings.py` に TDD 5 case を追加し、mixed entry・順序・冪等性・remove の再発を固定する。
4. `cli/lib/tests/test_security_hardening.py` に SessionStart history/harness と PostToolUse [0] 維持の観点を追加する。

scope 外:
- `.claude/settings.json` 実ファイルの恒久更新
- `helix init` / `helix migrate` 経路全体の end-to-end 回帰
- hook 追加要件そのものの設計変更

## §3 工程表

| Sprint | 作業内容 | 受入条件 | 状態 |
|---|---|---|---|
| .1 | PLAN 起票 + `test_merge_settings.py` に TDD 5 case 追加 | 5 case が現行実装で少なくとも一部 fail し、再発条件を再現できる | pending |
| .2 | `test_security_hardening.py` に SessionStart / PostToolUse 維持観点を追加 | `.claude/settings.json` の実運用順序と custom hook 存在がテスト化される | pending |
| .3 | `merge_settings.py` 修正 + `pytest` / `py_compile` / `plan lint` / `git diff --stat .claude/settings.json` 検証 | 対象 pytest 全 PASS、`settings.json` 差分 0、冪等性確認 | pending |

## §11 carry

- `helix init` / `helix migrate` の auto regen 経路全体検証は本 PLAN scope 外とし、別 carry で end-to-end 確認する。
- SessionStart / PostToolUse に今後 custom hook が増える場合の matcher 正規化ルールは別 PLAN で明文化する。
