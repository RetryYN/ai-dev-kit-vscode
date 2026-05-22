---
plan_id: PLAN-155
title: helix doctor severity 4 level 分類 (info / advisory / warn / fail-close)
status: draft
kind: refactor
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - PMO (Sonnet)
agent_slots:
  - role: pmo-sonnet
    slot_label: "PMO — Sprint .1 既存 check 棚卸し + severity 再分類案ドラフト"
  - role: tl-advisor
    slot_label: "TL adversarial check — Sprint .2 4 level 設計の妥当性確認 + fail-close 境界検証"
  - role: se
    slot_label: "SE — Sprint .3 check 関数戻り値 schema 拡張 + 既存 80+ warn 再分類実装"
  - role: qa
    slot_label: "QA — Sprint .4 level 別 smoke test + PLAN-110 / PLAN-124 regression 確認"
generates:
  - artifact_type: python_module
    path: cli/lib/helix_doctor.py
  - artifact_type: adr_snapshot
    path: docs/adr/ADR-039-helix-doctor-severity-schema.md
  - artifact_type: design_doc
    path: docs/v2/L4-test-design/PLAN-155-unit-test-design.md
  - artifact_type: test
    path: cli/lib/tests/test_helix_doctor_severity.py
dependencies:
  requires:
    - PLAN-110
    - PLAN-124
  blocks: []
  parent: null
related_adr:
  - ADR-039-helix-doctor-severity-schema
related_docs:
  - cli/lib/helix_doctor.py
  - cli/helix-doctor
  - docs/plans/PLAN-110-helix-doctor-warn-reduction.md
  - docs/plans/PLAN-124-helix-doctor-json-output.md
  - docs/plans/PLAN-077-sprint-plan-standardization.md
acceptance_criteria:
  - "helix doctor の check 結果が info / advisory / warn / fail-close の 4 level を返せる"
  - "既存 pass/warn/fail の出力互換が維持される (--legacy-format オプションで切替可)"
  - "PLAN-089 / PLAN-119 で fail-close 化済の check が fail-close level に再分類されている"
  - "既存 80+ warn のうち 20 件以上が info / advisory に降格し visibility が向上する"
  - "python3 -m py_compile cli/lib/helix_doctor.py PASS"
  - "unit test (pytest) 全 PASS"
  - "ADR-039 が accepted 状態で存在する"
---

# PLAN-155: helix doctor severity 4 level 分類 (info / advisory / warn / fail-close)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-039** で凍結 (Sprint .2 で採用方針確定後に起票):

- 4 level schema 設計 (info / advisory / warn / fail-close) の採用根拠
- 既存 pass/warn/fail との互換戦略 (--legacy-format オプション方針)
- fail-close level の昇格基準 (PLAN-089 / PLAN-119 等の既存 fail-close 化基準との整合)
- info / advisory の降格基準 (visibility 向上のための閾値ポリシー)

## 背景

`helix doctor` は現在 pass / warn / fail の 3 level。運用上の問題として:

1. **warn 80+ による visibility 低下** (PLAN-110 が漸減対応中): warn が多すぎると
   新規問題の発見が遅れる。粒度を細かくして対応優先度を明示することが必要
2. **fail-close 化済 check の表現不足**: PLAN-089 (設計 doc Web 検索ガード) /
   PLAN-119 等で fail-close 化された check が warn または fail として表示されており、
   「即修正必要」という意図が伝わりにくい
3. **info 相当の pass が見えない**: pass は一行サマリのみで、細粒度の
   状態情報 (ADR 件数、Sprint 完了率等) を閲覧できない

4 level 導入により:

- `info`: 状態情報の表示、対応不要
- `advisory`: 認識推奨、近い将来対応望ましい (旧 warn の一部)
- `warn`: 対応必要、次 sprint 内対処 (旧 warn の一部)
- `fail-close`: ゲート block、即時修正必須 (旧 fail の一部 + fail-close 化済 check)

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は HELIX 独自 lint ツールの内部 schema 拡張であり、外部ライブラリ /
業界 standard への新規依存なし。WebSearch **skip**。

skip 理由: severity level 設計は既存 PLAN-089 / PLAN-110 / PLAN-119 の
設計意図の整合整理であり、外部 standard 参照は不要。

## 設計方針

### 4 level schema

| level | 旧対応 | 説明 | 対応期限 |
|---|---|---|---|
| `info` | pass の一部 | 状態情報、問題なし | 対応不要 |
| `advisory` | warn の一部 | 認識推奨、許容範囲内 | 次 sprint 以内を目安 |
| `warn` | warn の一部 | 対応必要、品質劣化リスク | 当 sprint 内 |
| `fail-close` | fail + fail-close 化済 | ゲート block、即修正 | 即時 |

### 戻り値 schema 拡張 (Python)

```python
@dataclass
class CheckResult:
    check_id: str
    level: Literal["info", "advisory", "warn", "fail-close"]
    count: int
    reasons: list[str]
    # 旧互換フィールド (--legacy-format 時のみ参照)
    legacy_status: Literal["pass", "warn", "fail"]
```

level → legacy_status のマッピング:

- `info` → `pass`
- `advisory` → `warn`
- `warn` → `warn`
- `fail-close` → `fail`

### CLI 出力互換

```bash
helix doctor            # 4 level 出力 (デフォルト)
helix doctor --json     # PLAN-124 schema に level フィールド追加
helix doctor --legacy-format  # 旧 pass/warn/fail 互換出力
```

サマリ行への 4 level 件数追加:

```
passed: 24  info: 12  advisory: 15  warnings: 8  fail-close: 0  failed: 0
```

### 既存 check の再分類方針 (暫定、Sprint .1 で確定)

| 現状 | 再分類先 | 根拠 |
|---|---|---|
| check_adr_index (warn) | advisory | ADR index drift は近い将来対応で十分 |
| check_subagent_phase (warn) | advisory / warn | mandatory 種は warn、on-demand 種は advisory |
| check_sprint_completion (warn) | info | completed PLAN は対応不要 |
| check_plan_adr_snapshot (warn) | warn | L2 大局判断 + snapshot 不在は設計違反 |
| check_recovery_plan_freshness (warn) | advisory | 厳格 fail-close は不要 |
| fail-close 化済 check | fail-close | PLAN-089 / PLAN-119 等の明示 fail-close |

## 実装計画

### Sprint .1: 既存 check 棚卸し + severity 再分類ドラフト (PMO Sonnet 委譲)

実施内容:

1. `helix doctor --json` (PLAN-124 完了後) で全 check 一覧を取得
2. check 別に current level + 推奨 4 level + 根拠 PLAN を表で整理
3. fail-close 化済 check のリスト確定 (PLAN-089 / PLAN-119 等の git log 参照)
4. info 降格候補 (pass の一部) の洗い出し
5. 分類ドラフトを本 PLAN §Sprint .1 更新として追記

完了条件:

- 全 check の 4 level 再分類ドラフトが完成
- fail-close 対象 check が 1 件以上特定されている

### Sprint .2: 4 level 設計確定 + ADR-039 凍結 (Opus + tl-advisor)

実施内容:

1. Sprint .1 の分類ドラフトを Opus がレビューし推奨方針確定
2. tl-advisor 召喚:
   ```
   helix codex --role tl-advisor --task "helix doctor 4 level severity 設計の adversarial check。
   fail-close level の昇格基準が PLAN-089 設計意図と整合するか、
   info/advisory の降格基準が品質ゲートを弱めないかを確認してほしい。
   [分類ドラフト添付]"
   ```
3. tl-advisor 助言を踏まえて最終方針確定
4. ADR-039 起票 (4 level schema 採用根拠 + level 別対応方針を凍結)

完了条件:

- ADR-039 が accepted 状態
- 全 check の final 4 level が確定
- --legacy-format 互換戦略が ADR-039 に記録済

### Sprint .3: check 関数戻り値拡張 + 再分類実装 (Codex se 委譲)

実施内容:

1. `cli/lib/helix_doctor.py` の `CheckResult` dataclass に `level` フィールド追加
2. 各 check 関数の戻り値を Sprint .2 確定 4 level に対応
3. `cli/helix-doctor` (bash) の出力フォーマットを 4 level 対応に更新:
   - `--legacy-format` で旧 pass/warn/fail 出力を維持
4. PLAN-124 の `--json` schema に `level` フィールドを追加
5. サマリ行に `info` / `advisory` / `fail-close` の件数を追加

完了条件:

- `python3 -m py_compile cli/lib/helix_doctor.py` PASS
- `helix doctor --legacy-format` で旧互換出力が維持される
- fail-close 対象 check が fail-close level で出力される

### Sprint .4: unit test + regression 確認 (Codex qa 委譲)

実施内容:

1. `docs/v2/L4-test-design/PLAN-155-unit-test-design.md` 新規作成 (V-model artifact ③)
2. `cli/lib/tests/test_helix_doctor_severity.py` 新規作成 (V-model artifact ④) 8 case:
   - 4 level が info / advisory / warn / fail-close のいずれかであること
   - `--legacy-format` で旧 pass/warn/fail が出力されること
   - fail-close check が legacy_status=fail にマップされること
   - info check が legacy_status=pass にマップされること
   - PLAN-124 `--json` schema に level フィールドが含まれること
   - サマリ件数と checks 配列の level 件数が整合すること
   - PLAN-110 warn 件数が Sprint .1 時点以下であること (regression 確認)
   - PLAN-124 `helix doctor --json` が valid JSON を返すこと (regression)
3. `pytest cli/lib/tests/test_helix_doctor_severity.py -v` 全 PASS
4. `helix doctor --legacy-format` の pass/warn/fail 件数が Sprint .3 前と同一であること確認

完了条件:

- unit test 8 case 全 PASS
- regression なし

## mandatory in sprint (Sprint Exit 前必須)

- [ ] `python3 -m py_compile cli/lib/helix_doctor.py` PASS
- [ ] `pytest cli/lib/tests/test_helix_doctor_severity.py -v` 全 PASS
- [ ] `helix doctor --legacy-format` の warn 件数が Sprint .3 前と同一 (regression なし)
- [ ] セルフレビュー (Opus)
- [ ] pmo-sonnet review (Sprint .4 完了時)
- [ ] ADR-039 accepted 状態で存在 (Sprint .2 完了時)
- [ ] V-model artifact ③ test design doc 起票済 (PLAN-155-unit-test-design.md)
- [ ] commit message に `PLAN-155 sprint .X` 明示

## DoD (Definition of Done)

- [ ] check 戻り値 schema に level フィールドが追加されている
- [ ] 既存 check が 4 level に再分類されている
- [ ] `helix doctor --legacy-format` で旧互換出力が維持されている
- [ ] fail-close 化済 check が fail-close level で出力される
- [ ] `python3 -m py_compile` PASS
- [ ] unit test 8 case 全 PASS
- [ ] ADR-039 snapshot 起票済 (accepted)
- [ ] V-model artifact ③ test design doc (PLAN-155-unit-test-design.md) 存在
- [ ] PLAN-110 warn 漸減効果が本 PLAN の info/advisory 降格と合算で確認可能

## carry / 学び (起票時記録)

- **PLAN-124 依存**: Sprint .1 で `helix doctor --json` を利用するため、
  PLAN-124 が完了していることが前提。PLAN-124 未完了の場合は
  Sprint .1 を text parse で代替し、後から --json 対応に切り替える
- **--legacy-format の永続化方針**: 旧 3 level への後退防止として、
  --legacy-format は非推奨フラグとして警告付きで提供し、
  2 sprint 後の削除を ADR-039 に明記することを検討する
- **fail-close level と gate policy の連動**: fail-close level check が
  gate policy (G2/G4 ゲート) で自動 block されるよう、
  PLAN-151 (gate fail-close 卒業 framework) との整合を Sprint .2 で確認する

## 関連 reference

- [[feedback_adr_before_plan_violation]] (ADR snapshot 要否、本 PLAN は Sprint .2 後起票)
- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード、本 PLAN は skip 適用)
- ADR-039 (本 PLAN tree の L2 snapshot、Sprint .2 で起票)
- PLAN-089 (gate fail-close 化、fail-close level 昇格対象の根拠 PLAN)
- PLAN-110 (helix doctor warn 漸減、本 PLAN の info/advisory 降格と相乗効果)
- PLAN-124 (--json output、Sprint .1 依存 + Sprint .3 で level フィールド追加)
- PLAN-151 (gate fail-close 卒業 framework、fail-close level 連動候補)
- cli/lib/helix_doctor.py (check 実装の正本)
