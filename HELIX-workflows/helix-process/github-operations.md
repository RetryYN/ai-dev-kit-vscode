# GitHub 運用の HELIX 最適化（GitHub Operations for HELIX）

> ソロ開発（個人 1 名）に最適な GitHub 運用を、**HELIX-native**（V-model / 駆動 workflow / gate と紐づく形）で設計する。一般論（GitHub Flow / SHA pin / dependabot）に加え、**HELIX 固有の運用最適**を定める（ユーザー指摘 2026-06-03「Forward から外れた時に Issue を立てた方が分かりやすい / HELIX 向け運用最適」）。
> tl-advisor 2026-06-03 Q3 判定: 条件付き推奨。Phase1 は gate 紐づけ明文化 + 軽微 YAML 修正まで。CI 大改修・release-please・publish は carry。

## 1. 既存設定の監査（this repo, 2026-06-03）
- **workflow 7 本**: `ci` / `commitlint` / `security`(zizmor, SHA pin + codeql sarif) + branch-mode 4 本(`feature`/`hotfix`/`poc`/`refactor`、各 lint+test+validate)。
- `dependabot.yml`(weekly SHA 更新, PLAN-222/ADR-036) / `CODEOWNERS` / `pull_request_template.md`。
- **gap**: `ISSUE_TEMPLATE/` 不在（駆動↔Issue 未実装）/ **ADR-029(github-actions-branch-pipeline) が `Proposed` のまま workflow は実装済 = 状態ねじれ**（要 reconcile）/ branch-mode 4 本が `pull_request: branches: main` を持ち PR で全部走る運用ノイズ(P1)。
- 一般論ベストプラクティス（GitHub Flow / 最小権限 GITHUB_TOKEN / SHA pin + dependabot / Linux 単独 / public repo = Actions 無料）は既存設定とほぼ整合。

## 2. HELIX-native 運用最適（中核）

### 2.1 Forward 逸脱 → GitHub Issue（駆動 workflow の可視化）
**Forward V モデルから外れた瞬間（= 駆動 workflow が発火: Incident / Reverse / Discovery / Recovery / Refactor / Add-feature / Retrofit）に GitHub Issue を立てる。** これにより逸脱が GitHub 上で可視化され、`forward_return` で閉じるまで追跡できる。

```
Forward 逸脱検出（drift / 障害 / 探索 / 既存実態 / AI 暴走）
  → GitHub Issue 起票（駆動 kind 別 template）
  → 駆動 Process(親) ⊃ Action(子) で収束（PLAN と紐づけ）
  → forward_return 到達 → Issue close（Forward 復帰の証跡）
```

- **Issue ↔ PLAN 対応**: Issue は駆動 Process PLAN（`forward_return` 必須、plan-model）に対応。Issue body に `plan_id` / `forward_return` / `parent_process` を記載。
- **close 条件**: 駆動の closure event（Forward 該当 L へ収束）= Issue close。「戻し先を持たない駆動は完了できない」（Core §3）を Issue lifecycle で担保。
- **label**: 駆動 kind（`incident`/`reverse`/`discovery`/`recovery`/`refactor`/`add-feature`/`retrofit`）+ 戻し先 layer（`L1`..`L14`）+ 優先度。
- **ISSUE_TEMPLATE**: 駆動 kind ごとに template（症状/逸脱起点/forward_return/受入条件）。Forward 正常進行は Issue 不要（PLAN で足りる）、**逸脱のみ Issue 化**で「Issue = 逸脱の surface」を明確にする。

### 2.2 CI ↔ V-model gate 紐づけ
| CI | V-model | 紐づけ |
|---|---|---|
| `ci.yml` Required status checks ALL PASS | **G7 実装凍結** | 実装完了 gate の機械判定証跡 |
| test-pytest + test-bats | L8 結合 | Python helper / CLI 統合 |
| security.yml(zizmor/pip-audit) + smoke | L9 総合 | セキュリティ③ / 総合検証 |
| release + GitHub Release（carry） | L12 受入 | tag = 配布物固定証跡 |
| dependabot weekly + security weekly | L13 運用 | 依存・脆弱性の継続監視 |

- gate の機械判定は `gate_verdict = static_subchecks AND ai_review`（[[verification-strategy]] §10）。CI Required checks は static 側の証跡。

## 3. solo 最適ルール（一般論、既存と整合）
- **branch**: GitHub Flow（main + 短命 feature branch + PR）。Git Flow 不採用。
- **main 直 push**: admin bypass 許可 + doc/typo/hotfix 限定 + コミットに理由必記（HELIX 既存ルール CLAUDE.md と整合）。
- **branch protection**: Required status checks(Loose) + PR required + admin bypass ON + Force push OFF。
- **GITHUB_TOKEN**: top-level `contents: read`、job 単位で最小追加（write は release job のみ）。
- **SHA pin + dependabot**: 維持（immutable ref + 継続更新）。
- **concurrency**: `cancel-in-progress: true`（Phase1 軽微修正で追加候補）。

## 4. CLAUDE.md への取り込み
- `CLAUDE.md` の「## GitHub 運用ルール」に **§Forward 逸脱 → Issue** と **§CI↔gate 紐づけ** を追記し、運用導線を本書へリンクする（重複させない）。

## 5. carry（tl-advisor: Phase 後段 / 別 PLAN）
- **ADR-029 reconcile**: `Proposed` → `Accepted` か実装方針かを確定（実装済との状態ねじれ解消）。Required checks 名を壊さない段階移行。
- branch-mode 4 本 → reusable workflow or `ci.yml` の conditional jobs へ統合（PR 全本走り = 運用ノイズ解消）。
- `ISSUE_TEMPLATE/`（駆動 kind 別）実体化 + Issue↔PLAN 自動連携（`helix` から Issue 起票/close を駆動 closure に紐づける）。
- release-please / PyPI publish: 今は不要（clone + setup.sh 配布、dist publish は park）。
- macOS/Windows matrix: shell 差分検出（可搬性 NFR）が要る時点で追加。
