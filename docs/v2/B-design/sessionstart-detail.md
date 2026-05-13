# Phase 5 SessionStart Hook 詳細設計
Status: draft
Phase: V2 Phase 5 自動化
Scope: SessionStart hook による起動時 sync + dashboard quick view
Mode: 設計提示 / docs 作成のみ
Primary FR: FR-A02, FR-A07, FR-EM03, FR-EM04
Related NFR: NFR-12, NFR-14

## 概要
本書は V2 Phase 5 で導入する SessionStart hook の詳細設計を定義する。目的は次の 2 点である。

1. Claude Code セッション開始時に skill/code/plan/detector 関連 state を自動同期する。
2. 同時に 1 秒以内で読める開発全容の quick dashboard を fail-open で表示する。

中心判断は **foreground と background の分離** である。dashboard 表示は cache ベースで 1 秒以内に返し、重い sync は `helix sync --auto` に集約して非同期実行する。これにより FR-A02 の「起動時自動同期」と FR-EM04 の「1 秒以内 dashboard 表示」を競合させずに両立する。

## 選択肢
| 選択肢 | 内容 | メリット | デメリット | 推奨度 |
|---|---|---|---|---|
| A | SessionStart ですべて同期完了後に dashboard 表示 | 実装像が単純 | 1 秒要件を満たしにくい。hook timeout 5s にも弱い | 低 |
| B | dashboard を先に表示し、sync は別 process で background 実行 | UX が安定し、FR-EM04 に最も整合 | 非同期失敗時の観測設計が必要 | 高 |
| C | SessionStart では dashboard のみ、sync は scheduler 任せ | 最速表示 | FR-A02 の「起動時自動同期」に不足 | 中 |

## 推奨
**Option B** を採用する。

- FR-A02 は SessionStart 起点の自動同期を要求している。
- FR-EM04 は 1 秒以内 dashboard 表示を要求している。
- 既存 `.claude/settings.json` の SessionStart timeout は 5 秒であり、重い同期を foreground で抱える設計は余裕が薄い。
- 既存 `cli/libexec/helix-session-start` も「失敗しても session を止めない」思想で作られており、fail-open と整合する。

## ソース
- `docs/v2/L1-REQUIREMENTS.md`
- `docs/v2/A-audit/hooks-commands-subagents.md`
- `docs/v2/A-audit/audit-summary.md`
- `docs/v2/C-followup/followup-p1-aggregate.md`
- `.claude/settings.json`
- `cli/libexec/helix-session-start`
- `cli/lib/session_start_helpers.py`
- `cli/lib/merge_settings.py`
- `docs/design/D-HOOK-SPEC.md`
- `docs/commands/index.md`
- `docs/commands/ai-harness.md`

不確実性:

- 入力指定の `docs/v2/C-followup/auto-extraction-plan.md` は 2026-05-14 時点の workspace に存在しなかった。
- PostToolUse 中心の follow-up 根拠は、実在する `followup-p1-aggregate.md` と `audit-summary.md` で代替している。

## 1. 目的と責務
SessionStart hook の責務は、既存の HELIX context 注入に加えて次の 5 つへ拡張される。

1. skill catalog rebuild の増分同期
2. code build の増分同期
3. plan import の増分同期
4. detector_runs 履歴の最新確認
5. dashboard quick view の表示

本 hook は状態の正本更新そのものを担わず、**正本更新の起点** を担う。正本更新は `helix sync --auto` に集約し、SessionStart は orchestrator として振る舞う。

## 2. 要件対応
| 要件 | 本設計での実現 |
|---|---|
| FR-A02 | SessionStart で `helix sync --auto` を起動し、skill/code/plan の差分同期を実施 |
| FR-A07 | sync の実体を `helix sync` へ一本化 |
| FR-EM03 | quick dashboard を SessionStart で常時提示 |
| FR-EM04 | `helix detect dashboard --quick` を cache 読みで 1 秒以内返却 |
| NFR-12 | foreground は cache read と軽量メタ確認に限定 |
| NFR-14 | 重い処理は background 実行、全 sync 完了を 60 秒以内目標に分離 |

## 3. 現状との接続点
2026-05-14 時点の現状は以下である。

- SessionStart 登録は `.claude/settings.json` で `~/ai-dev-kit-vscode/cli/helix-session-start`
- 実体は `cli/libexec/helix-session-start`
- timeout は 5 秒
- statusMessage は `Loading HELIX framework...`
- 現行 hook は context 注入、session 記録、handover/skill hint 生成が中心
- `cli/lib/session_start_helpers.py` は `helix detect dashboard --format text` を 1 秒 timeout で読む既存パスを持つ
- V2 監査では `helix sync` 統合入口未実装が P1-059 として指摘済み

したがって本設計は既存 hook を置換するというより、**既存 SessionStart に sync と quick dashboard 契約を追加する設計** である。

## 4. 設計方針
### 4.1 Foreground / Background 分離
- foreground:
  - dashboard quick view 表示
  - 最低限の stale 判定
  - hook 応答返却
- background:
  - skill catalog rebuild
  - code build
  - plan import
  - detector cache invalidation
  - detector summary cache refresh

### 4.2 Fail-open
- sync 失敗では session を block しない
- dashboard 失敗でも session 継続
- timeout 超過時は skip して warning を残す
- ログは `.helix/logs/` または `helix.db` 側イベントへ送る設計前提

### 4.3 統一入口
SessionStart から個別 CLI を並べて叩かず、sync 系は `helix sync --auto` に寄せる。

- SessionStart / PostToolUse / Gate / scheduler で同じ同期責務を共有しやすい
- cache invalidation を一箇所で持てる
- 後続の `--skills`, `--code`, `--plans`, `--detectors`, `--force` 分解に発展しやすい

## 5. Hook 契約
### 5.1 配布用 shell
```bash
# .claude/hooks/sessionstart-sync.sh
helix sync --auto --quiet
helix detect dashboard --quick
```

上記は責務の論理表現であり、runtime では次を追加する。

- `helix sync --auto --quiet` は background で起動
- `helix detect dashboard --quick` は foreground で実行

### 5.2 実行順序
1. SessionStart fired
2. session metadata 初期化
3. `helix sync --auto` を background 起動
4. `helix detect dashboard --quick` を foreground 実行
5. session metadata 更新
6. hook 応答返却

補足:

- TASK_INPUT では「session-summary 記録」が現状 SessionStart hook にあるとされるが、現 repo の実体は Stop hook `helix-session-summary` である。
- SessionStart 側にあるのは `sessions` table INSERT と progress/context 生成であり、本設計ではこれを「session metadata 初期化」と解釈して統合する。

## 6. `helix sync --auto` 詳細設計
### 6.1 責務
`helix sync --auto` は SessionStart 用の統一 sync CLI として次を担当する。

1. skill catalog rebuild
2. code build
3. plan import
4. detector cache invalidation
5. quick dashboard 用 aggregate cache 更新トリガ

### 6.2 想定 subcommand
```bash
helix sync --auto --quiet
helix sync --skills
helix sync --code
helix sync --plans
helix sync --detectors
helix sync --force
```

### 6.3 `--auto` の意味
`--auto` は「差分があるものだけ順に処理する」モードとする。

- skill: `SKILL.md` / references の mtime と hash を比較
- code: git tracked file 差分、または前回 build manifest 差分で対象を限定
- plans: `docs/plans/` の新規 file 検出
- detectors: 変更影響を受ける cache の invalidation のみ実施

### 6.4 実行モデル
```text
helix sync --auto
  ├─ sync_skills_if_dirty()
  ├─ sync_code_if_dirty()
  ├─ sync_plans_if_dirty()
  ├─ invalidate_detector_cache()
  └─ refresh_dashboard_aggregate_if_needed()
```

### 6.5 出力方針
- `--quiet`: SessionStart では stdout を汚さない
- warning / error は structured log へ送る
- foreground の user-facing 文言は dashboard 側に限定

## 7. Incremental Update 戦略
### 7.1 skill catalog
- 基本判定: `SKILL.md` mtime 比較
- 補助判定: references 配下の mtime または manifest hash
- 出力: skill catalog cache 更新

利点:

- skill 数は多いが、毎回の全量 scan を避けやすい

注意:

- mtime のみでは rename や clock skew に弱い
- 実装時は `path + size + mtime` 以上、可能なら hash manifest を持つ方が安全

### 7.2 code build
- 基本判定: git diff もしくは tracked file manifest 差分
- 対象: 変更 file のみ rebuild
- 出力: `.helix/cache/code-catalog.jsonl` と派生 cache 更新

利点:

- `helix code build` の既存資産を流用しやすい

注意:

- untracked file をどう扱うかは要実装判断
- SessionStart では tracked 中心、PostToolUse で untracked 追従の分担が妥当

### 7.3 plan import
- 判定: `docs/plans/` の file count 差分と path 差分
- 対象: 新規 `PLAN-*.md`
- 出力: plan registry / DB record 更新

注意:

- file count 差分だけでは rename や削除に弱い
- 実装では count ではなく「前回 seen path set」との差集合を使うべき

### 7.4 detector cache invalidation
- 変更種別ごとに invalidate 範囲を限定
- skill 変更: skill 系 detector summary 再計算
- code 変更: code / coverage / relation 系 summary 再計算
- plan 変更: plan / orchestration / contract 系 summary 再計算

## 8. `helix detect dashboard --quick` 詳細設計
### 8.1 目的
SessionStart 直後に「今どこまで進んでいるか」を 1 秒以内で返す。

### 8.2 quick モードの制約
- cache 読みのみ
- DB full scan 禁止
- detector のその場再実行禁止
- relation graph 再構築禁止
- fail-open

### 8.3 表示観点
1. V-model 整合度
2. detector 状態
3. cost
4. skill hit
5. gate / next action

### 8.4 layout mockup
```text
[HELIX] V2 dev-state
====================
Phase: L1 (95%) -> G1 待ち
V-model: be 85% / fe 72% / db 90% / fs 78%
Detector: 12/14 OK / 2 WARN
Cost (week): codex 62% / claude 38%
Skill hit: 78%

[Next] G1 通過判定、Phase 2 統合 review
```

### 8.5 取得元
| 表示項目 | 主な取得元 |
|---|---|
| Phase / Gate | `.helix/phase.yaml` または session summary cache |
| V-model score | 直近 aggregate cache |
| Detector summary | `detector_runs` 集計 cache |
| Cost | `cost_log` 週次 summary cache |
| Skill hit | `skill_usage` 集計 cache |
| Next action | handover / readiness / phase summary cache |

## 9. 性能要件と根拠
### 9.1 目標
- SessionStart dashboard 表示: 1 秒以内
- sync 全完了: 60 秒以内目標
- hook timeout: 現行設定 5 秒以内に foreground 応答

### 9.2 根拠
- `.claude/settings.json` の SessionStart timeout は 5 秒
- `cli/lib/session_start_helpers.py` では既に `helix detect dashboard --format text` を 1 秒 timeout で呼ぶ設計が存在する
- V2 監査では SessionStart quick dashboard に性能 headroom がある前提が示されている
- 重い sync を background へ逃がせば、foreground は cache read と整形だけに絞れる

### 9.3 予算配分の目安
| 区間 | 目標 |
|---|---:|
| hook process 起動 + lock | 50ms |
| phase/cache read | 150ms |
| dashboard quick 整形 | 300ms |
| 予備 | 500ms |

上記は設計目安であり、まだ実測値ではない。実装時は dogfood で p50/p95 を採取し、必要なら quick cache の粒度をさらに粗くする。

## 10. 既存 SessionStart hook との統合
### 10.1 既存機能
- setup 完了判定
- git 状態表示
- `sessions` table への session_id 記録
- handover 情報表示
- skill 推挙ヒント
- progress block 表示

### 10.2 統合原則
- 既存 context 注入は維持
- quick dashboard は progress block の先頭か直下に統合
- sync は context payload 生成の blocking path に載せない

### 10.3 望ましい順序
```text
SessionStart
  -> setup / lock / session_id
  -> background sync spawn
  -> quick dashboard build
  -> context + dashboard emit
  -> return
```

## 11. Failure Handling
### 11.1 失敗ポリシー
| 失敗箇所 | 動作 |
|---|---|
| sync 起動失敗 | warning のみ。session 継続 |
| sync 部分失敗 | 成功分のみ反映。失敗内容は log 化 |
| dashboard cache 読み失敗 | 空表示または最小表示で継続 |
| detector summary cache 破損 | detector 行を `unknown` 扱いで継続 |
| lock 競合 | 既存実行があれば skip |
| 5s 超過 | quick 表示を諦めて context のみ返却 |

### 11.2 fail-open と fail-close の境界
- SessionStart は fail-open
- Gate / pre-commit / detector run は fail-close 可
- したがって SessionStart では「警告を見せるが作業は止めない」が原則

### 11.3 表示例
```text
[HELIX] quick dashboard unavailable
reason: detector summary cache missing
status: session continued
```

## 12. Opt-out
### 12.1 project config
`.helix/config.yaml`

```yaml
disable_sessionstart_sync: true
```

### 12.2 env
```bash
HELIX_NO_SESSION_SYNC=1
```

優先順位:

1. env
2. project config
3. default enabled

想定用途:

- 大規模 repo で dogfood 比較をしたい場合
- CI 的な一時セッションで hook overhead を切りたい場合
- sync バグ切り分け

## 13. Dogfood 検証
Phase J で最低限確認する。

1. HELIX 自身の session で SessionStart が毎回発火する
2. quick dashboard が現実の phase / detector / cost に概ね一致する
3. p95 で 1 秒以内を達成する
4. sync 失敗時も session が継続する
5. opt-out が効く

## 14. 影響範囲
| パス | 影響 |
|---|---|
| `.claude/settings.json` | SessionStart hook の command / timeout / statusMessage 調整候補 |
| `cli/helix-sync` | 新規 CLI 追加 |
| `cli/templates/hooks/sessionstart-sync.sh` | 配布用 hook script 新規 |
| `cli/libexec/helix-session-start` | background sync spawn と quick dashboard 統合 |
| `cli/lib/session_start_helpers.py` | quick dashboard block 生成の再編 |
| `cli/lib/merge_settings.py` | hook 配線変更時の同期 |

## 15. open questions
1. `plan import` の差分判定を file count で止めるか、path manifest まで持つか
2. quick dashboard cache の正本を file cache に置くか、SQLite aggregate に置くか
3. `detector_runs` 最新確認を quick dashboard 表示項目へ含めるだけで十分か、sync 側で stale 警告も出すか
4. `helix detect dashboard --quick` の output format を text 専用にするか、JSON も持つか

推奨:

- 1 は path manifest
- 2 は SQLite + 軽量 cache file の二段
- 3 は warning 行を追加
- 4 は text と JSON の両対応

## 16. 結論
SessionStart hook は V2 で「context 注入」から「軽量可視化 + 非同期同期の起点」へ役割を拡張する。実装の鍵は、`helix sync --auto` に同期責務を集約し、`helix detect dashboard --quick` を cache 読み専用にして foreground を 1 秒以内へ閉じ込めることである。この設計により、FR-A02 と FR-EM04 を競合させずに両立できる。
