# Audit Followup 4: hooks / commands / agents source-of-truth 統合計画

最終更新: 2026-05-14

## 1. 目的

`docs/v2/A-audit/hooks-commands-subagents.md` で可視化された `hooks / commands / agents` の source-of-truth 多重化を、v2 運用で 1 箇所に統合する方針を詳細化する。

### 前提

- 参照入力: `docs/v2/A-audit/hooks-commands-subagents.md`
- 連携正本: `docs/commands/index.md`, `cli/ROLE_MAP.md`, `skills/SKILL_MAP.md`
- 本稿は実装方針を定める計画文書（実装自体は別 wave）

## 2. 対象資産

- **Hooks（現状 3 か所）**
  - `.claude/hooks/`
  - `cli/templates/hooks/`
  - `skills/agent-skills/hooks/`
- **Agents（現状 2 か所）**
  - `.claude/agents/`
  - `cli/roles/`
- **Commands（現状 2 か所）**
  - `.claude/commands/`
  - `docs/commands/`

## 3. 統合候補一覧（15 件以上）

| # | SOT-ID | カテゴリ | 現状 location | V2 後 SoT | 移行手順 | 影響範囲 | 承認要否 |
|---:|---|---|---|---|---|---|---|
| 1 | SOT-001 | hooks | `.claude/hooks/` + `cli/libexec/helix-session-start` | `cli/templates/hooks/`（正本）+ `.claude/hooks/`（シンボリックリンク） | `cli/templates/hooks/` 配下へ移設し、`.claude/hooks/` は `session-start` symlink | install 時の hook 配布、SessionStart 発火経路 | PM |
| 2 | SOT-001 | hooks | `.claude/hooks/helix-pre-bash` | `cli/templates/hooks/`（実体） + `.claude/settings.json` が参照する hook 入口 | `cli/templates/hooks/` を正本化し、`settings` を wrapper ではなく実体へ向ける | hook 失敗時の guard（Bash）制御 | PM |
| 3 | SOT-001 | hooks | `.claude/hooks/helix-pre-research` | `cli/templates/hooks/`（実体）+ wrapper を薄く残存 | `helix-pre-research` を実体と責務定義に揃え、wrapper 廃止 or 最小化 | research 制限、WebSearch/WebFetch 制御 | PM |
| 4 | SOT-001 | hooks | `.claude/hooks/pretooluse-opus-repo-block.sh` | `cli/templates/hooks/`（ガード条件）+ `.claude/hooks/` は配布 symlink | 条件ロジックを templates 側へ移し、配布時に symlink を作成 | Opus 側 repository 直接編集防止 | PM |
| 5 | SOT-001 | hooks | `.claude/hooks/post-tool-use.sh` | `cli/templates/hooks/`（実体）+ `helix-post-tool-use` 連携 | 配布時に `.claude/hooks/post-tool-use.sh` を生成し、`cli/libexec/` へ delegate | post-tool-use telemetry の取りこぼし防止 | PM |
| 6 | SOT-001 | hooks | `.claude/hooks/stop.sh` | `cli/templates/hooks/`（実体）+ `cli/helix-session-summary` 連携 | `stop.sh` を `cli/templates/hooks/` 正本で維持し、配布で上書き | stop 時の記録、監査コネクタ | 自動 |
| 7 | SOT-001 | hooks | `cli/helix-check-claudemd`, `cli/helix-session-start` | `cli/templates/hooks/`（deprecate wrapper）+ `cli/libexec/`（実体） | 旧 wrapper を非正本化し、新実体への呼び先コメントを明記 | 廃止時期を明確化した保守、移行時互換 | PM |
| 8 | SOT-001 | hooks | `skills/agent-skills/hooks/session-start.sh` | `cli/templates/hooks/session-start.sh`（正本候補）+ `.claude/hooks/` symlink | `skills/agent-skills/hooks` の旧所有を廃止し、実体を template 側へ寄せる | agent 起動時の共通 hook 条件 | PM |
| 9 | SOT-001 | hooks | `skills/agent-skills/hooks/*.sh`（sdd-cache*, simplify-ignore*) | `cli/templates/hooks/hooks.json` + scripts in `cli/templates/hooks/`（正本化） | 配布用途をテンプレートへ一本化し、`skills/agent-skills/hooks` を参照ラッパへ変更 | hook テンプレートの更新一元化、検知漏れ低減 | PM |
| 10 | SOT-001 | commands | `.claude/commands/build.md` | `docs/commands/`（正本）+ `helix commands generate`（導線） | コマンド定義を docs 側に集約し、`/build` 生成物を再作成 | slash command 再発行、discoverability | PM |
| 11 | SOT-001 | commands | `.claude/commands/code-simplify.md` | `docs/commands/`（正本）+ 生成 script | docs を更新後、`/code-simplify` 生成/配布を自動化 | slash discoverability | 自動 |
| 12 | SOT-001 | commands | `.claude/commands/sdd-plan.md` (`/plan`) | `docs/commands/`（正本）+ generate | 実行時の prompt を docs から再生成 | planning 導線 | PM |
| 13 | SOT-001 | commands | `.claude/commands/sdd-review.md` (`/review`) | `docs/commands/`（正本）+ 5軸レビュー指針反映 | `docs/commands/` 定義で最終更新し、slash 生成 | レビュー導線、観測ログ | PM |
| 14 | SOT-001 | commands | `.claude/commands/spec.md` | `docs/commands/`（正本）+ wrapper | 正本文書を source としてコマンド生成 | spec-driven ドキュメント導線 | PM |
| 15 | SOT-001 | commands | `.claude/commands/test.md` | `docs/commands/`（正本）+ generator | docs に定義した検証フローを source にし再配布 | test 起動導線 | 自動 |
| 16 | SOT-001 | commands | `.claude/commands/ship.md`（deprecate） | `docs/commands/`で `ship` 定義を明示しつつ Agent tool 非依存実装へ移行 | `/ship` の依存を分離し、`docs/commands/` へ注記 + generate with compatibility shim | agent tool 依存解除、ADR-015 整合 | PM |
| 17 | SOT-001 | agents | `.claude/agents/be-api.md` | `cli/roles/be-api.conf` + `.claude/agents/be-api.md` thin wrapper | wrapper を最小化し `role.conf` を正本化 | API 担当 agent の起点を1つ化 | PM |
| 18 | SOT-001 | agents | `.claude/agents/be-logic.md` | `cli/roles/be-logic.conf` + thin wrapper | wrappers を参照のみ化し、実体は roles/へ移動 | business logic 実装経路統一 | PM |
| 19 | SOT-001 | agents | `.claude/agents/code-reviewer.md` | `cli/roles/tl.conf`（既定化）+ wrapper | role とレビュー責務の重複を解消し thin wrapper のみ残す | レビュー導線、権限制御 | PM |
| 20 | SOT-001 | agents | `.claude/agents/db-schema.md` | `cli/roles/dba.conf` + thin wrapper | 実体化済みの role 参照へ差し替え | DB 変更担当統一 | 自動 |
| 21 | SOT-001 | agents | `.claude/agents/devops-deploy.md` | `cli/roles/devops.conf` + thin wrapper | 配布手順を role ベースへ寄せる | release / infra 起点統一 | PM |
| 22 | SOT-001 | agents | `.claude/agents/qa-test.md` | `cli/roles/qa.conf` + thin wrapper | QA 実行責務を role に寄せ、wrapper の drift を抑制 | テスト実行契約 | 自動 |
| 23 | SOT-001 | agents | `.claude/agents/security-audit.md` | `cli/roles/security.conf` + thin wrapper | security role のみで最終責務を定義 | security ガード全体 | PM |

## 4. 実装観点（共通）

### hooks 実装戦略

- `cli/templates/hooks/` を配布元（source-of-truth）とし、`cli/templates/hooks` 変更時に `.claude/hooks` へ再配布
- `.claude/hooks/` には symlink（または最小 wrapper）を原則採用
- `skills/agent-skills/hooks/*` は hook asset の実体ではなく、参照ヘルパーまたは移行記録位置へ変更

### agents 実装戦略

- `cli/roles/*.conf` を source-of-truth とし、`.claude/agents/*.md` は薄い wrapper とする
- wrapper には「委譲先」「許容する呼び出し元」「更新時期」を明記
- role 変更時は wrapper の stale チェックを月次レビューで確認

### commands 実装戦略

- `docs/commands/*.md` を source-of-truth とする
- slash command は `docs/commands` から生成し、`.claude/commands` へ配布
- `docs/commands/index.md` を index 真正として `commands` の discoverability を担保

## 5. 段階別実行（Phase）

### Phase 1: SoT 固定

- `cli/templates/hooks/` と `cli/roles/`、`docs/commands/` の対象資産を最優先で確定
- wrapper/duplicate の所在を監査ログ化

### Phase 2: 物理移行と再配布

- symlink 作成（hooks, agents）
- command generate + 再配布
- 既存参照を新パスへ更新

### Phase 3: 廃止/監査安定化

- `deprecate` 明示対象の整理（`ship`, wrapper) 解除
- discoverability と `hook`発火の smoke test を追加
- 今後の drift 防止のため、更新時に `docs/v2/C-followup/*` へ追記

## 6. リスクと承認フロー

- **migration risk**: 中〜高
  - hook 置換時のセッション開始/停止/事前ガードの不具合で運用停止が起こる可能性
  - `/ship` 系の再設計が agent tool 方針と未整合のまま進むと、導線混在が再発
  - `code-reviewer/qa/security` の責務を role 側へ寄せる際の権限差異

### 承認要否目安

- PM 承認: コマンド再生成や `/ship` 方針変更、hook wrapper 廃止
- 自動: hook 配布の再現実装、既存 wrappers のコメント更新のみ

## 7. 末尾サマリ

- 統合件数: **23**
- migration risk: **中〜高**（Phase 2 での回帰テスト必須）
- Phase 紐付け: **Phase 1 / Phase 2 / Phase 3** の順
