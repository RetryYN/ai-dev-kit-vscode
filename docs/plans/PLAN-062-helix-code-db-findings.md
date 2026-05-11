---
plan_id: PLAN-062
title: "PLAN-062（helix code DB 実用化で発見した 3 件 fix）"
status: completed
created: 2026-05-11
completed: 2026-05-12
author: "PM (Opus)"
priority: medium
size: S
phases_affected: "cli/lib/* / helix code DB / G4 coverage gate"
parent_plan: null
acceptance:
  post_validation_bug_fix:
    verification_commands: { command: "helix code find 'test' -n 3", expected: "exit 0、IsADirectoryError なし" }
  core5_coverage_headroom:
    verification_commands: { command: "helix code stats --uncovered --scope core5 --bucket coverage_eligible --fail-under 80", expected: "coverage ≥ 82% (G4 gate +2pt 以上の余裕)" }
    index_promotion_criteria: "private helper が次の 3 条件をすべて満たす場合のみ @helix:index 付与: (1) cli/lib/* または cli/helix-* から外部呼び出し caller >= 1、(2) docstring 有り、(3) public 相当の責務 (parse/build/validate/dispatch 系)。metric gaming 防止のため対象一覧と理由を retro §X に列挙する。"
  dup_main_suppression:
    verification_commands: { command: "helix code dup --threshold 0.85", expected: "main() entrypoint 6 件は除外マーク済 / 真重複のみ表示" }
    exclusion_spec: "default 除外条件は (name == 'main') AND (type == 'function') AND (parent_module endswith '__main__' or has 'if __name__' guard) の 3 軸 AND。--include-entrypoints flag で従来動作復元。name のみ判定 / body_hash 判定は採用しない (G3 で凍結)。"
finalized: 2026-05-11
---

# PLAN-062: helix code DB 実用化で発見した 3 件 fix

## §1 背景

PLAN-061 完遂後、ユーザー指示で `helix code` 系 DB を実用検証。
LLM 検索・重複検知・coverage gate は機能しているが、運用上の歪み 3 件を実発見:

1. **codex_post_validation.py:271 IsADirectoryError** — `helix code find` 経由の recommender 呼び出しで post-validation hook が落ちる (機能阻害なしだが stderr 汚染)
2. **core5 coverage 80.4% (45/56)** — G4 gate (80%) +0.4pt しか余裕なし。public symbol 1 件追加で gate fail のリスク
3. **main() 重複 6 ペア score=1.000** — code-recommender / helix-db / skill-catalog / skill-dispatcher の CLI entrypoint。false positive だが threshold 0.85 で常時 6 行ノイズ

## §2 解消対象

### Sprint W-1: codex_post_validation.py の path guard 追加
- 対象: `cli/lib/codex_post_validation.py` `read_snapshot()` または `main()` の args validation
- 修正: `args.before` / `args.after` / `args.untracked_after` が directory または存在しない場合は早期 return (or empty set)
- 動機: helix-codex が recommender role でスナップショット引数を渡さない経路がある → 落とさず skip

### Sprint W-2: core5 coverage headroom 確保
- 対象 (allowed_files): `cli/lib/code_catalog.py` / `cli/lib/helix_db.py` / `cli/lib/skill_catalog.py` / `cli/lib/skill_dispatcher.py` の **4 ファイルのみ** (code_recommender.py は W-3 が触るため除外)
- 修正: 既存 private helper のうち、acceptance.core5_coverage_headroom.index_promotion_criteria の 3 条件を満たす 2-3 件に `@helix:index` 付与で eligible 化 → coverage 80.4% → 82-85% へ
- 動機: G4 gate fail リスク回避、PLAN-013 taxonomy 運用の余裕作り

### Sprint W-3: main() entrypoint を dup 検知から除外
- 対象 (allowed_files): `cli/lib/code_recommender.py` (find_duplicates) + `cli/helix-code` (dup 出力 wrapper、必要時のみ)
- 修正: acceptance.dup_main_suppression.exclusion_spec で凍結した 3 軸 AND 条件で default 除外、`--include-entrypoints` で従来動作復元
- 動機: dup 検知のノイズ削減 → 真重複が見えるようにする

## §3 Sprint 構成

| Sprint | 内容 | 委譲先 |
|---|---|---|
| W-0 | draft + TL Round 1 + finalize (size=S) | PM |
| W-1 | post_validation.py path guard 実装 | Codex PE |
| W-2 | core5 coverage headroom (@helix:index 追加) | Codex PE |
| W-3 | main() dup 除外フィルタ実装 | Codex PE |
| W-final | 統合検証 + retro + push | Opus |

W-1 / W-2 / W-3 は **編集ファイル衝突なし** で並列投入可能 (W-1=codex_post_validation.py / W-2=code_catalog+helix_db+skill_catalog+skill_dispatcher / W-3=code_recommender+helix-code wrapper)。allowed_files は §2 で固定済。

## §4 Out of Scope

- vulture 60% 残 100 件のさらなる精査 (PLAN-061 W-3 tests-only carry と別 PLAN)
- skill 解像度 W-3 低使用度 ext=0 件見直し (PLAN-059 carry)
- helix code DB の bucket 拡張 (PLAN-013 v2 として独立)

## §5 リスク

- W-2 で `@helix:index` 付与基準を緩めすぎると private_helper bucket の意味が薄れる → acceptance.core5_coverage_headroom.index_promotion_criteria で 3 条件 AND 凍結済
- W-3 で main() 除外を強くしすぎると、実害ある main 重複 (例: 同じロジックを 2 ファイルにコピペした entry) を見逃す → acceptance.dup_main_suppression.exclusion_spec で 3 軸 AND 凍結済 (parent_module / __name__ guard 必須)
- W-1 は scope 極小、影響範囲限定
