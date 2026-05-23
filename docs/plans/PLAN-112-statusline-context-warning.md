---
plan_id: PLAN-112
title: statusLine warning 実装 (V5 Layer 2、context % 4 段階監視)
status: draft
is_reference: true   # V2 完全移行 (2026-05-24): 旧 V1 PLAN 参考扱い、製本にしない (commit ea846ea)
process_layer: L7   # ★必須: 本 PLAN は L7 実装スプリント工程 (commit eeb0530 retrofit)
parent_design: docs/plans/PLAN-099-autonomous-runtime-framework-5layer.md   # from dependencies.parent
kind: impl
drive: be
layer: L4
size: M
created_at: 2026-05-23
authors:
  - PM (Opus)
  - SE (Codex gpt-5.4)
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 4 段階閾値設計承認・debounce/hysteresis パラメータ境界判断"
  - role: pmo-sonnet
    slot_label: "PMO — ドキュメント整合確認・drift チェック・Sprint review"
  - role: tl-advisor
    slot_label: "TL adversarial check — debounce/hysteresis logic・Stop 役割分担・context % 取得方式 review"
  - role: se
    slot_label: "SE — helix-statusline 実装・settings.json 登録・debounce/hysteresis state 管理"
  - role: qa
    slot_label: "QA — fake transcript size fixture test 全ケース検証・hysteresis 境界確認"
generates:
  - artifact_type: cli_extension
    path: cli/helix-statusline
  - artifact_type: config
    path: .claude/settings.json
  - artifact_type: test
    path: cli/lib/tests/test_statusline.py
  - artifact_type: design_doc
    path: docs/plans/PLAN-112-statusline-context-warning.md
  - artifact_type: adr_snapshot
    path: docs/adr/ADR-039-statusline-context-warning-decision.md
dependencies:
  requires:
    - PLAN-099
  blocks: []
  parent: PLAN-099
related_adr:
  - ADR-032
  - ADR-039
acceptance_criteria:
  - "context % 4 段階 (>50% / 30-50% / ≤30% / ≤20%) が正しく遷移する"
  - "debounce: 5 秒以内の同一 threshold 更新が 1 回に集約される"
  - "hysteresis: 各 threshold に 5% gap が設定され、境界付近での振動が抑制される"
  - "Stop hook へ handover snapshot / telemetry 処理を移管し、statusLine は監視専用に留まる"
  - "pytest test 全 6 ケース PASS (T2-001〜T2-006、PLAN-099 §11.2 準拠)"
  - "hook timeout ≤ 5 秒 (T6-004 ケース)"
  - "context % が 55% 以上に回復するまで黄 (≤50%) 警告が維持される (hysteresis)"
  - "ADR-039 起票 (L2 大局判断 snapshot)"
  - "helix doctor pass/fail/warn カウント維持 (regression なし)"
---

# PLAN-112: statusLine warning 実装 (V5 Layer 2)

## L2 凍結 (ADR snapshot)

本 PLAN tree 内の L2 大局判断は **ADR-039** で凍結 (起票予定):

- statusLine hook 採用判断 (Claude Code 2.x 公式仕様、PLAN-099 §6 設計確定済)
- 4 段階閾値定義 (>50% / 30-50% / ≤30% / ≤20%) と各段階のアクション
- debounce 5 秒 + hysteresis 5% gap の設計値選定
- Stop hook との役割分担確定 (threshold 監視は statusLine 専用)
- context % 取得方式 (transcript_path ファイルサイズ / HELIX_CONTEXT_PCT env / 推定値フォールバック)

## 背景

**PLAN-099 (V5 自動走行 framework 5-layer)** の Layer 2 担当 PLAN。

PLAN-099 §6 で設計を確定済み:
- Layer 2 = `statusLine hook で context % 先回り監視 (>50% / 30-50% / ≤30% / ≤20% の 4 段階)`
- 実装スコープは PLAN-099 の P2b (別 session 本実装) に分類
- 本 PLAN はその実装 PLAN として独立起票

**課題 (PLAN-099 §1 より)**:
- context 枯渇が察知されず突然の auto-compact が発生し、state が消失する
- 解決: statusLine が context % をリアルタイム監視し、4 段階の段階的警告で先回りさせる

## WebSearch 履歴 (PLAN-087 ガード遵守)

本 PLAN は新 framework 採用判断 (statusLine hook + debounce/hysteresis 設計) を含むため、PLAN-087 ガード対象。PLAN-099 §3 で実施済の WebSearch 3 query を parent として継承し、以下の key evidence を引用する。

| Query | 出典 | 抽出した業界 standard |
|---|---|---|
| "Claude Code 2.x statusLine hook specification 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG v2.1.141) | `transcript_path` が SessionStart/hook で提供される仕様を確認。statusLine は hook event type として公式サポート。context 使用率の直接 API 提供は未確認のため、transcript_path ファイルサイズを proxy として使用する方針を採用 |
| "Claude Code context window percentage tracking usage monitoring 2026" | https://github.com/anthropics/claude-code/releases (CHANGELOG 2.1.143 / CLAUDE_CODE_STOP_HOOK_BLOCK_CAP) | context block cap 機能 (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`) の存在から、Claude Code が内部で context 使用量を追跡していることが確認できる。hook への % 公開は現在 beta、HELIX_CONTEXT_PCT env 経由の external injection を代替として使用 |
| "statusLine debounce hysteresis pattern terminal UI progressive warning 2026" | https://github.com/anthropics/claude-code/releases / Elasticsearch 公式 debounce docs / UI engineering best practice | debounce: 監視系 UI で 100ms-30s 範囲が一般的。threshold 監視では 30 秒 debounce が標準 (too fast = noise、too slow = delayed reaction)。hysteresis: Schmitt trigger パターン。threshold 上下 5% gap が thermal engineering / electronics で標準 (vibration-free zone) |

## 業界 standard 参照

- Claude Code CHANGELOG v2.1.141/2.1.143: https://github.com/anthropics/claude-code/releases
- HELIX PLAN-099 §6 (statusLine 設計、本 PLAN の実装根拠)
- Schmitt Trigger / Hysteresis Design Pattern: https://en.wikipedia.org/wiki/Schmitt_trigger (threshold ±gap で振動抑制、embedded systems 標準)
- Elasticsearch Debounce Pattern: https://www.elastic.co/guide/en/elasticsearch/reference (monitor 系での debounce 適用例)
- Terminal UI Progressive Warning Pattern (ncurses / terminal status line): PLAN-099 §6.2 設計から引用

## 設計方針 (TL v5 round 5 修正条件 遵守)

CLAUDE.md §TL v5 round 5 修正条件 を厳密遵守する。特に修正条件 **#4 (statusLine + Stop 役割分担)** が本 PLAN の核心:

> 「statusLine + Stop 役割分担: 両方必要。Stop は軽量化 (handover snapshot / telemetry / stale release のみ)、statusLine に debounce + hysteresis 必須 (警告連打防止)」

### 4 段階 threshold 定義 (PLAN-099 §6.1 準拠)

| 残量 | 状態 | 表示色 | アクション |
|---|---|---|---|
| > 50% | 正常 | 緑 (🟢) | なし |
| 30-50% | 警告 | 黄 (🟡) | `/compact 推奨` メッセージ表示 |
| ≤ 30% | 危険 | 橙 (🟠) | `state 永続化実行推奨` + handover update 促進 |
| ≤ 20% | 緊急 | 赤 (🔴) | `PreCompact block 条件チェック中` + PLAN-111 連携促進 |

### debounce 設計

```
HELIX_STATUSLINE_DEBOUNCE_SEC=30 (default)

動作:
- 同一 threshold level の警告は 30 秒以内に再発しない
- state: last_warned_at + last_warned_level を .helix/statusline-state.json に保存
- 30 秒経過後または threshold が変化した場合は警告を再発
```

### hysteresis 設計 (Schmitt Trigger pattern)

```
HELIX_STATUSLINE_HYSTERESIS_PCT=5 (default)

動作:
- 黄 (≤50%) 入り → 緑 (>55%) に戻るまで黄維持
- 橙 (≤30%) 入り → 黄 (>35%) に戻るまで橙維持
- 赤 (≤20%) 入り → 橙 (>25%) に戻るまで赤維持

実装: lower_threshold = threshold - hysteresis_gap
      state machine (GREEN / YELLOW / ORANGE / RED) で遷移管理
```

hysteresis 採用理由: context % が threshold 付近で振動すると、debounce なしでは警告が高頻度で on/off を繰り返しユーザーが警告を無視するリスクがある (TL v5 修正条件 #4「ノイズ化、重要警告無視リスク」対応)。

### context % 取得方式

Claude Code の hook に context % を直接提供する公式 API が確認できない場合、以下の優先順位で取得:

```
Priority 1: HELIX_CONTEXT_PCT 環境変数 (外部から注入、最優先)
Priority 2: transcript_path ファイルサイズ / 推定最大サイズ (4 MB = PLAN-101 MAX_SCAN_BYTES)
Priority 3: hook stdin の context フィールド (Claude Code が将来提供する可能性)
Priority 4: デフォルト値 = 100% (監視不能 = 警告なし = fail-open)
```

Priority 2 の推定式:
```bash
TRANSCRIPT_BYTES=$(stat -c %s "$TRANSCRIPT_PATH" 2>/dev/null || echo 0)
MAX_BYTES=$((4 * 1024 * 1024))  # 4 MB (PLAN-101 MAX_SCAN_BYTES)
CONTEXT_PCT=$(( TRANSCRIPT_BYTES * 100 / MAX_BYTES ))
```

**注意**: この推定値は proxy であり、実際の token 使用率と異なる場合がある。将来 Claude Code が context % を hook に提供した場合、Priority 1 経由で直接取得に切り替える (HELIX_CONTEXT_PCT env injection)。

### Stop hook との役割分担 (PLAN-099 §6.3 準拠)

| 処理 | 担当 hook | 根拠 |
|---|---|---|
| context % 監視 + 段階的警告 | statusLine (本 PLAN) | threshold 監視はリアルタイム性重視 |
| debounce + hysteresis | statusLine (本 PLAN) | 警告頻度制御 |
| handover snapshot | Stop hook (既存) | session 終了時の重い処理 |
| session telemetry | Stop hook (既存) | 非同期で良い |
| stale lock release | Stop hook (既存) | session 終了時実行 |
| PreCompact block 判定 | PreCompact hook (PLAN-111) | Layer 3 担当 |

statusLine は **監視専用**。実際の永続化処理は Stop / PreCompact に委譲し、threshold 超過の通知のみを担う。

## 実装計画

### Sprint .1: context % 取得 + 4 段階 state machine 実装 (Codex se 委譲)

**対象ファイル**: `cli/helix-statusline` (新規 bash script)

実装内容:
- `detect_context_pct()` 関数 (4 priority fallback chain)
- 4 段階 state machine (GREEN / YELLOW / ORANGE / RED)
- hysteresis 計算 (`effective_threshold = threshold - HELIX_STATUSLINE_HYSTERESIS_PCT`)
- state 保存 / 読み込み (`.helix/statusline-state.json`)
- 警告メッセージ生成 (各段階のアクション案内を含む)

mandatory in sprint:
- `bash -n cli/helix-statusline` PASS

### Sprint .2: debounce 実装 + settings.json 登録 (Codex se 委譲)

**対象ファイル**: `cli/helix-statusline` (Sprint .1 の拡張), `.claude/settings.json` (Edit)

実装内容:
- debounce ロジック追加 (last_warned_at + last_warned_level を state.json で管理)
- debounce 秒数 = `HELIX_STATUSLINE_DEBOUNCE_SEC` (default 30)
- settings.json: statusLine hook 登録 (event type: PostToolUse などのタイミングで発火)
- 既存 hooks への追加 (append のみ)

mandatory in sprint:
- `python3 -c "import json; json.load(open('.claude/settings.json'))"` PASS (JSON syntax)
- 既存 hook 回帰 (他 hook が影響を受けない)

### Sprint .3: pytest fixture test 実装 + DoD 確認 (Codex qa 委譲)

**対象ファイル**: `cli/lib/tests/test_statusline.py` (新規)

テストケース (PLAN-099 §11.2 T2-001〜T2-006 + T6-004 完全準拠):

| ケース | 内容 |
|---|---|
| T2-001 | context 51% → state=GREEN、警告メッセージなし |
| T2-002 | context 49% → state=YELLOW、黄警告メッセージあり |
| T2-003 | context 49% → 31% 推移 → debounce 30s 内は同一 YELLOW 再警告なし |
| T2-004 | context 49% → 51% → 46% → hysteresis gap で YELLOW 維持 (55% に達していないため) |
| T2-005 | context 29% → state=ORANGE、橙警告メッセージあり |
| T2-006 | context 19% → state=RED、赤警告 + PreCompact 連携案内あり |
| T6-004 | helix-statusline 実行時間 ≤ 5 秒 |

fake fixture 方針:
- `HELIX_CONTEXT_PCT` 環境変数を直接制御 (Priority 1 経由でテスト)
- `HELIX_HOME` を `tmp_path` に向け、状態ファイルを分離
- `HELIX_STATUSLINE_DEBOUNCE_SEC=2` でテスト内 debounce を短縮 (30秒待ち不要)
- `HELIX_STATUSLINE_HYSTERESIS_PCT=5` 固定

mandatory in sprint:
- `python3 -m py_compile cli/lib/tests/test_statusline.py` PASS
- `python3 -m pytest cli/lib/tests/test_statusline.py -v` 全 7 ケース PASS
- セルフレビュー (Codex qa 内)
- pmo-sonnet review (Sprint Exit 時)

## DoD (Definition of Done)

- [ ] `bash -n cli/helix-statusline` PASS
- [ ] 4 段階 state machine が正しく遷移 (T2-001〜T2-006 PASS)
- [ ] debounce: 30 秒以内の同一 threshold 再警告が抑制される (T2-003 PASS)
- [ ] hysteresis: threshold 付近の振動が抑制される (T2-004 PASS)
- [ ] pytest test 全 7 ケース PASS (T2-001〜T2-006 + T6-004)
- [ ] settings.json hook 登録 PASS (JSON syntax valid)
- [ ] 既存 hook 回帰なし
- [ ] hook timeout ≤ 5 秒 (T6-004 PASS)
- [ ] Stop hook との役割分担が明確 (statusLine は監視専用、永続化処理なし)
- [ ] ADR-039 起票 (本 PLAN tree の L2 snapshot)
- [ ] helix doctor pass/fail/warn カウント regression なし

## V-model 4 artifact trace

| artifact | 対象 |
|---|---|
| ① 設計 (本 PLAN) | §設計方針 / §実装計画 |
| ③ テスト設計 | 本 PLAN §実装計画 Sprint .3 ケース一覧 (T2-001〜T2-006 + T6-004) |
| ② 実装コード | cli/helix-statusline (Sprint .1-.2 で実装) |
| ④ テストコード | cli/lib/tests/test_statusline.py (Sprint .3 で実装) |

双方向 trace:
- 本 PLAN → テスト: Sprint .3 ケース一覧に T2/T6 番号明記
- テストコード → 設計: pytest test に `# PLAN-112 T2-001` コメントで対応付け (Sprint .3 実装時)
- テスト設計 → テストコード: class 名 / 関数名で T2-NNN 対応 (Sprint .3 実装時)

## carry / 学び (起票時記録)

- **context % の取得精度**: transcript_path ファイルサイズは proxy であり token 使用率と完全一致しない。将来 Claude Code 公式で context % hook 提供が実現した場合、HELIX_CONTEXT_PCT Priority 1 経由に即切替え可能な設計にしておく
- **debounce 秒数の調整**: 30 秒は経験値。実際の運用で「警告が多すぎる」場合は 60 秒、「遅すぎる」場合は 15 秒に調整できるよう env で外部化
- **hysteresis gap 5% の根拠**: Schmitt Trigger パターンの標準値を採用。context % の推定精度が低い場合、gap を 10% に拡大する選択肢あり
- **PLAN-111 (Layer 3) との連携**: 赤 (≤20%) 到達時に PLAN-111 の PreCompact block 条件チェックを促す。直接呼び出しではなく、systemMessage でユーザーへ案内するにとどめる (Layer 間の疎結合維持)
- **settings.json の hook event type**: statusLine の発火タイミングは PostToolUse が適切か SessionStart が適切かは Sprint .2 で確認。過剰発火を避けるため、発火頻度の調整が必要な場合は debounce が機能する

## 関連 reference

- PLAN-099 §6 (Layer 2 設計、本 PLAN の実装根拠)
- PLAN-099 §11.2 (テストケース T2-001〜T2-006 + T6-004)
- PLAN-111 (Layer 3 PreCompact hook、≤20% 時の連携先)
- ADR-032 (PLAN-099 の L2 snapshot)
- ADR-039 (本 PLAN の L2 snapshot、起票予定)
- [[feedback_dont_stop_with_carry_remaining]] (context 枯渇による中断課題の背景)
- [[feedback_design_doc_web_search_required]] (PLAN-087 ガード遵守)
- CLAUDE.md §TL v5 round 5 修正条件 (設計方針の根拠)
