# Phase 4: 5 層介入機構（FR-GR05）詳細設計

Status: draft
Phase: V2 Phase 4（検出ガードレール）
Scope: guardrail-mechanism / PM/Orchestration/Command/Skill/Verify

関連:
- `docs/v2/L1-REQUIREMENTS.md` FR-GR05
- `docs/v2/A-audit/hooks-commands-subagents.md`
- `docs/v2/A-audit/security-audit.md`
- `docs/plans/PLAN-043-consolidated-carry-resolution.md`

本設計は、`helix` 運用における tool 実行前後の安全制御を、PM/Orchestration/Command/Skill/Verify の 5 層で定義し、
`record -> detect -> feedback -> stop` の閉ループを構築する。

## 目的

- destructive op・scope 違反・権限逸脱を早期検知
- 同一違反の反復を 2 回目で制御
- PM 承認ルートを明示化して人間介入を強化
- hook/skill/route/gate の結果を detector で統一して監査可能化

## 1. 介入 hook の発火順序

設計順序（agent の 1 tool call を 1 単位）

1. `UserPromptSubmit`（PM 層）
2. `PreToolUse`（Command 層）
3. tool 実行
4. `PostToolUse`（Verify 層）
5. `PostToolUse`（Skill 層）
6. `SessionEnd`（Orchestration 層）

### 1.1 1) UserPromptSubmit（PM）

- 役割: 大局判断・エスカレーション要否の前提判定
- 受理条件: 方針不明、destructive 直前、PM 承認未了
- 出力: continue / block / hint + escalation context

### 1.2 2) PreToolUse（Command）

- 役割: tool 実行直前 guard
- 受理条件: invalid args、破壊コマンド疑義、scope違反なし
- 失敗: exit code 2（block）

### 1.3 3) tool 実行

- tool 実行本体
- 成否にかかわらず PostToolUse の観測対象に収集

### 1.4 4) PostToolUse（Verify）

- 役割: detector 判定、feedback 注入、critical stop 判定
- 出力: continue / hint / block（必要時）

### 1.5 5) PostToolUse（Skill）

- 役割: skill 利用の低 hit / fail 率に応じて reroute
- 失敗時は即停止せず、代替候補を返す

### 1.6 6) SessionEnd（Orchestration）

- 役割: routing の最終集約、次回継続方針の保存
- `routing_decisions` と `handover` へ反映

## 2. 5 層の詳細実装

ここでは各層を独立実装し、かつ共通イベントで接続する。

### 2.1 PM 層

#### 2.1.1 script path

- `helix handover`（`handover escalate` / `handover status --json`）
- `helix handover update --owner codex`（継続時）

#### 2.1.2 event

- `UserPromptSubmit`
- `SessionEnd`（最終審査）

#### 2.1.3 入力

- env: `HELIX_PM_SCOPE`, `HELIX_REQUIRE_PM_APPROVAL`
- 追加情報: prompt reason、plan/task context、role

#### 2.1.4 出力

- `continue`: 方針問題なし
- `block`: escalation 必要
- `hint`: 「設計 freeze / PM 承認 / 再実行手順」

#### 2.1.5 fail-close 条件

- 大局判断要件（destructive 直前）未承認
- PMO 方針に反する依存
- 人手判断必須の矛盾

#### 2.1.6 例

```bash
helix handover escalate --reason "destructive op before PM approval" \
  --context "target=docs/v2/B-design, gate=G3"
```

---

### 2.2 Orchestration 層

#### 2.2.1 script path

- `routing_decisions` table
- `helix handover`
- `helix skill chain`
- `helix review`

#### 2.2.2 event

- `SessionEnd`
- `helix gate` 通過時の routing 再計算

#### 2.2.3 入力

- `routing_decisions`
- PM/Verify からの hint
- WBS/plan の `reference_docs`

#### 2.2.4 出力

- `continue`: 既存ルート継続
- `hint`: routing reroute 推奨
- `block`: route 崩壊時（稀）

#### 2.2.5 fail-close 条件

- 路線再解決不能
- routing table 更新失敗の繰り返し

#### 2.2.6 例

```sql
INSERT INTO routing_decisions(session_id, from_role, to_role, reason)
VALUES (:sid, 'pg', 'se', :reason);
```

---

### 2.3 Command 層

#### 2.3.1 script path

- `.claude/hooks/pretooluse-*.sh`
- `.claude/hooks/pretooluse-opus-repo-block.sh`
- `cli/libexec/helix-pre-bash`
- `cli/libexec/helix-pre-research`
- `cli/lib/llm_guard.py`

#### 2.3.2 event

- `PreToolUse`（Write/Bash/WebSearch/WebFetch）

#### 2.3.3 入力

- command name、args、working dir
- 現在 role (`pg` / `se` / `docs` / `security`)
- `HELIX_DRY_RUN`、`HELIX_ALLOWED_FILES`

#### 2.3.4 出力

- `continue`: allow
- `block`: exit 2
- `hint`: 代替コマンド

#### 2.3.5 fail-close 条件

- invalid args
- destructive op（`rm -rf`, `git reset --hard`, `DROP TABLE`, `danger-full-access`）
- scope 逸脱、hook 無効化検知

#### 2.3.6 例

```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"
if echo "$INPUT" | rg -qE '(git reset --hard|DROP TABLE|rm -rf|danger-full-access)'; then
  echo "[guardrail][command] block: critical destructive pattern detected"
  echo "<hint>Use scoped command or escalate via pm-advisor</hint>"
  exit 2
fi
exit 0
```

---

### 2.4 Skill 層

#### 2.4.1 script path

- `cli/helix-skill`
- `cli/lib/skill_dispatcher.py`
- `cli/lib/recommender.py`

#### 2.4.2 event

- `PostToolUse` 後
- `skill_usage` update

#### 2.4.3 入力

- task 文
- skill hit rate / low-confidence
- cost budget 状態

#### 2.4.4 出力

- `continue`: 既存スキル維持
- `hint`: reroute 候補
- `block`: なし（Verify / Command に委譲）

#### 2.4.5 fail-close 条件

- `helix skill chain` 高確率失敗が連続
- 低ヒット率で重要タスクが停止ループ化しうる

#### 2.4.6 例

```python
def skill_guard(skill_state):
    if skill_state.hit_rate < 0.4:
        return {
            "action": "hint",
            "next": "agent-skills:documentation-and-adrs",
            "reason": "low hit-rate"
        }
    return {"action": "continue"}
```

---

### 2.5 Verify 層

#### 2.5.1 script path

- `cli/libexec/helix-post-tool-use`
- `cli/lib/helix_db.py`（`detector_runs`）
- `cli/lib/codex_post_validation.py`
- `.claude/hooks/post-tool-use.sh`
- `helix gate G<N>`
- `cli/lib/agent_policy_guard.py`

#### 2.5.2 event

- `PostToolUse`
- `SessionEnd` 集約時の再評価
- gate 実行時

#### 2.5.3 入力

- tool event payload
- axis candidate（01〜19）
- repeat count（同 violation 再現回数）

#### 2.5.4 出力

- `continue`: pass
- `hint`: `<hint>...</hint>` を stdout
- `block`: critical stop / gate fail

#### 2.5.5 fail-close 条件

- axis-01 / axis-02 / axis-07 / axis-08 など critical fail
- 同一 axis 2 回連続 fail
- security/hook-bypass の重大検知

#### 2.5.6 hint フォーマット

```xml
<hint>
axis=axis-07
severity=warn
summary=contract drift detected
repeat_count=1
suggestion=run: helix gate G4 --plan-id <PLAN-ID>
</hint>
```

#### 2.5.7 stop フォーマット

```xml
<stop>
axis=axis-02
severity=critical
reason=destructive command candidate
action=exit 2 + escalate
</stop>
```

## 3. feedback mechanism

### 3.1 経路

- Verify 層で `<hint>...</hint>` を出力
- 次 tool call で agent が `hint` を参照し、同一 axis 1 回目は調整
- 2 回目で `block` 判定

### 3.2 同違反 2 回目の動作

- 1 回目: `warn` + 推奨コマンド
- 2 回目: PM escalation route + verify stop の同時提示
- 3 回目: `routing_decisions` で強制 reroute

### 3.3 受信側（Claude/Codex）要件

1. hint がある場合は context に保持
2. `axis` を再実行時パラメータへ連携
3. `repeat_count` が 2 以上なら実行中止判定へ誘導

## 4. stop mechanism

### 4.1 Critical axis

- axis-01: dead code / 破壊的設計疑義
- axis-02: spaghetti 依存増悪
- axis-07: contract drift
- axis-16+: 追加 critical（security）

### 4.2 停止条件

- コマンド実行前（Command）：危険コマンド検知
- 実行後（Verify）：critical axis fail
- 同一違反再発で Verifier 再評価

### 4.3 停止時応答

- exit code 2
- エラーメッセージ: 何が違反か + 推奨操作 + PM 経路

```text
[block] Critical axis-07 fail
Recommendation: helix gate G4 --plan-id <PLAN>
Escalation: helix handover escalate --reason "critical axis repeated"
```

### 4.4 再開

1. PM/TL 承認
2. 再実行前に gate 通過
3. `repeat_count` リセット確認

## 5. 優先順位（PM > Verify > Command > Skill > Orchestration）

### 5.1 優先ルール

- PM が介入した場合は最優先
- Verify の fail-close は Command と連動して最終停止
- Command は実行前安全化
- Skill は reroute だけで停止は原則行わない
- Orchestration は post-run 集約で最後

### 5.2 同時介入例

- 状況: destructive command + low trust recommendation + routing conflict

```text
PM: block (escalate)
Verify: block (critical)
Command: block (exit2)
Skill: hint only
Orchestration: record routing fallback
```

## 6. 暴走防止

### 6.1 false positive 抑制

- axis ごと threshold を個別設定
- `max_false_positive_rate` 0.05
- 学習ログを 7 日以上保留しなければ即時有効化しない

### 6.2 opt-out

- `disable_layer_pm`
- `disable_layer_orchestration`
- `disable_layer_command`
- `disable_layer_skill`
- `disable_layer_verify`
- `HELIX_DRY_RUN`

優先: `disable_*` > dry run。ただし PM 層は承認理由がある場合のみ上位無効化。

### 6.3 dry-run mode

- `HELIX_DRY_RUN=1`: block を hint 化（記録は残す）
- `HELIX_DRY_RUN=2`: block を warning 化（CI 向け）

### 6.4 組込み監視

- 同一 axis の fail 率、誤検知率、ヒント無視率を週次で監査
- 超過時に gating threshold を一時緩和

### 6.5 rollback 方針

- `axis` 追加：1 週間保留後に本番反映
- `disable_layer_*` は有効期限付き

## 7. 既存 hook との衝突整理

### 7.1 PLAN-043 既存 PreToolUse hook

- 既存 `.claude/hooks/pretooluse-opus-repo-block.sh` の失敗理由を Command 層へ接続
- 新規設計では command 層を上位 API 化し、既存 hook は下位実装として委譲

### 7.2 DocumentationAssistant hook

- 本 repo では実在確認は不十分だが、将来存在時に備えて
- `block` 権限は付与せず、verify hint 限定
- quality advisory のみ扱う

### 7.3 session-summary / stop hook

- 現行 Stop hook は会計目的が主。これを Orchestration と同時に重複実行しない
- order: verify/summaries -> orchestration finalize -> stop-summary

### 7.4 既存 hook の fail-open/close

- SessionStart: fail-open
- PreToolUse Command: fail-close
- PostToolUse Verify: fail-close（条件付き）
- Stop: fail-open

## 8. 実装インタフェース（最小セット）

### 8.1 PreToolUse script テンプレ

```bash
#!/usr/bin/env bash
set -euo pipefail

if [[ "${disable_layer_command:-false}" == "true" ]]; then
  exit 0
fi

INPUT="$(cat)"
if echo "$INPUT" | rg -qE '(git reset --hard|DROP TABLE|rm -rf)'; then
  echo "[command] blocked"
  echo "<hint>Use pm escalation before destructive op</hint>"
  exit 2
fi
exit 0
```

### 8.2 PostToolUse detector 注入テンプレ

```python

def run_verify(event):
    verdict = evaluate_axes(event)
    if verdict == "warn":
        print(format_hint(event.axis, verdict))
    elif verdict == "fail":
        print(format_hint(event.axis, verdict, block=True))
        if event.repeat_count >= 2:
            escalate(event)
            return False
    return True
```

### 8.3 routing override テンプレ

```sql
INSERT INTO routing_decisions(
    session_id, layer, from_state, to_state, reason, created_at
) VALUES (:sid, 'orchestration', :from_state, :to_state, :reason, CURRENT_TIMESTAMP);
```

### 8.4 skill reroute テンプレ

```bash
helix skill chain "..."
helix skill chain --refresh
```

## 9. 参照整合チェックと TODO

### 9.1 リンク先確認

- `docs/v2/L1-REQUIREMENTS.md` の FR-GR05 は本機構の起点
- 既存監査書で hook / security 課題を検知対象に再利用
- `PLAN-043` 既存 hook を command 層に吸収接続

### 9.2 TODO 残件

- axis 一覧（01〜19）を detector catalog と完全紐付け
- `helix gate` と `<hint>` の schema テスト追加
- `routing_decisions` と `handover` の重複更新防止
- false positive ログを 1 週間以上保存ししきい値更新

## 10. 受入想定
