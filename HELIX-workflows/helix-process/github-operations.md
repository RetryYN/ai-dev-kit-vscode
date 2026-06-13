# GitHub 運用の HELIX 最適化（GitHub Operations for HELIX）

> ソロ開発（個人 1 名）に最適な GitHub 運用を、**HELIX-native**（V-model / 駆動 workflow / gate と紐づく形）で設計する。一般論（GitHub Flow / SHA pin / dependabot）に加え、**HELIX 固有の運用最適**を定める（ユーザー指摘 2026-06-03「Forward から外れた時に Issue を立てた方が分かりやすい / HELIX 向け運用最適」）。
> tl-advisor 2026-06-03 Q3 判定: 条件付き推奨。Phase1 は gate 紐づけ明文化 + 軽微 YAML 修正まで。CI 大改修・release-please・publish は carry。

## 1. 既存設定の監査（this repo, 2026-06-03）
- **workflow 7 本**: `ci` / `commitlint` / `security`(zizmor, SHA pin + codeql sarif) + branch-mode 4 本(`feature`/`hotfix`/`poc`/`refactor`、各 lint+test+validate)。
- `dependabot.yml`(weekly SHA 更新, PLAN-222/ADR-036) / `CODEOWNERS` / `pull_request_template.md`。
- **gap（2026-06-03 GitHub 早期実装 batch で一部解消）**: `ISSUE_TEMPLATE/` 不在 → **駆動 7 kind template + config 実装済**（§2.1） / ADR-029 が `Proposed` のまま実装済 = 状態ねじれ → **Accepted へ reconcile 済**（Accepted scope / transitional baseline / known debt を分離、ADR-029 §Status） / concurrency 未設定 → **全 7 workflow に追加済**（§3）。**残 gap**: branch-mode 4 本が `pull_request: branches: main` を持ち PR で全部走る運用ノイズ(P1) = branch-pipeline 統合（別 ADR/PLAN carry、§5）。
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
- **concurrency**: `cancel-in-progress: true` を全 7 workflow に **実装済**（2026-06-03、group=`${{ github.workflow }}-${{ github.ref }}`、job 名＝Required checks 名は不変）。

## 3.5 gate-driven push（承認の gate 委譲、2026-06-03 — push policy SSoT）

push の毎回手動承認を撤廃する。承認を**消す**のでなく**機械 gate に委譲**する。本節が push 政策の SSoT（CLI 契約 = [D-CONTRACT §4.5](../../docs/v2/L3-detailed-design/D-CONTRACT/D-CONTRACT-draft.md)、利用導線 = [docs/commands/push.md](../../docs/commands/push.md)、`CLAUDE.md` はリンク + 要約）。

- **承認の置換**: `helix push --gate --execute --plan-id <PLAN>` が **7 gate 全 PASS → authorized push**（別途の人間承認は不要）。これは HELIX harness 経由の push のみに適用する。
- **7 gate**: `G-tests` / `G-catalog` / `G-secret` / `G-ff` / `G-attr`(Co-Authored-By) / `G-nondestructive` / **`G-review`**（新）。`G-review` は **`plan_scope` 別 lifecycle** で検査する（TL 判定 A, 2026-06-05）:
  - **action-scope**（`plan_scope=action` / 既定）: `status ∈ {completed, finalized}` **かつ** `tl_review == approve`。＝Action 完了 + TL 承認。
  - **process-scope**（`plan_scope=process`）: `tl_review == approve` のみ必須、**`status` 完了は不問**。理由 = Process は長命の親（全 Action の L7 完了で収束、plan-model）であり、incremental Action landing 中は必然的に未完了。`completed` を要求すると Process⊃Action の段階 landing と矛盾するため。**Process の `workflow_chain` / `contains_action_plans` / `forward_return` を変更した commit は再 TL review を要する**（古い approve で親行程変更が通る穴を塞ぐ。当面は手続き規律、機械強制は follow-up）。
  - **承認済み deferred 境界チケット例外**（`plan_scope=action` の特例、TL 判定 Option B, 2026-06-14）: `workflow=add-feature` の**未承認 L7+ 作業を deferred する境界チケット**は、設計境界として確定し commit/push する一方で、対象作業（L7 実装 / 実行 / DB write / CI 等）が未承認のため `status: draft` を**維持する**（`test_helix_l0_l14_flow_contract.py` が draft=未承認境界を機械 enforce する境界保護機構と整合させるため）。この種のチケットに限り `status ∈ {completed,finalized}` 要件を**免除**する。免除は次の**全条件成立時のみ**（`push_gate._is_approved_deferred_add_feature_boundary`）: `plan_scope=action` ∧ `workflow=add-feature` ∧ `status=draft` ∧ `tl_review=approve` ∧ `approval_boundary` 非空かつ "approv" 含む ∧ `approval_required_before_*` のいずれかが YAML boolean `true` ∧ `current_task_scope ∈ {feature_ticket_only, L4_L6_design_closed_feature_ticketed}` ∧ `unlock_conditions` 非空。**`tl_review=approve` は「draft 境界チケットの push 承認」を意味し、対象 L7 作業の実装承認ではない**（実装承認は `approval_required_before_*` で別途要求）。それ以外の draft action PLAN は従来通り fail（回帰保護維持）。**`layer` は guard 条件に含めない**（実在の境界チケットは defer 対象に応じ L5-L6 / L7 / L8-L14 と分散するため。「L7+ 作業の deferred」は対象作業の性質を指す説明であり、チケット自身の `layer` 値を L7 に制約する条件ではない。予測の狭さは上記 8 条件の AND で担保する）。
  - **単一 ahead PLAN push はその 1 件を検査**し、**複数 ahead PLAN push は `--plan-id` で代表 PLAN を明示したうえで ahead 全 PLAN を検査**する（各 PLAN に上記 scope 別ルールを適用）。`--plan-id` が ahead に含まれない場合、複数候補/0、handover 不一致は fail-close。
- **raw push は guarded**: gate を経由しない raw `git push`（`--force` / `git push origin main` 含む）は `helix-pre-bash` guard で **deny**（fail-close、bypass = `HELIX_ALLOW_RAW_PUSH=1` + 理由を evidence）。`helix push --execute`（`--gate` 無し）も deny。**＝従来「push は承認必須」は実行者の遵守頼みで機械 guard が無かったが、本変更で fail-close 化し安全性は向上する**。
- **branch scope**: `dogfood` / `feature/*` / `hotfix/*` は gate-driven auto-push 可。**`main` は auto-push 不可**（§3 branch protection: PR required + force off 維持）。main 直 push は `--allow-main --reason <text>` + 人間判断を必須とし、doc/typo/hotfix 限定（§3 と整合）。`helix push` の default branch は current branch（main 暗黙 push を防ぐ）。
- **配布 carry**: 消費側へ効かせるには CLAUDE/AGENTS template・hook/settings 配布・setup/migrate 導線への反映が要る（本 repo 確定後、別 batch）。

## 4. CLAUDE.md への取り込み
- `CLAUDE.md` の「## GitHub 運用ルール」に **§Forward 逸脱 → Issue** と **§CI↔gate 紐づけ** を追記し、運用導線を本書へリンクする（重複させない）。

## 5. carry（tl-advisor: Phase 後段 / 別 PLAN）

**2026-06-03 完了（GitHub 早期実装 batch）**:
- **ADR-029 reconcile** → 完了: `Accepted` へ遷移、Accepted scope / transitional baseline / known debt を分離（ADR-029 §Status）。Required checks 名（job 名）は不変。
- **`ISSUE_TEMPLATE/`（駆動 kind 別）実体化** → 完了: 駆動 7 kind template + `config.yml`（blank issue 無効化、逸脱 = template 選択を強制）。各 template に 症状/逸脱起点/forward_return/受入条件 + plan_id/parent_process。機能追加系 3 種（add-feature/reverse/retrofit）は **機能一覧 registry 登録/同期を必須 acceptance** 化（[functional-registry §1.5 更新規律](../../docs/v2/L3-requirements/helix-workflows-functional-registry.md)）。
- **concurrency** → 完了（§3、全 7 workflow）。

**残 carry**:
- **branch-mode 4 本 → reusable workflow or `ci.yml` の conditional jobs へ統合**（PR 全本走り = 運用ノイズ解消）。Required checks 名の互換を壊す可能性があるため**別 ADR/PLAN**で扱う（ADR-029 known debt、GitHub Flow 正規化方針の確定を含む）。
- **Issue↔PLAN 自動連携**: `helix` から Issue 起票/close を駆動 closure（forward_return 到達）に紐づける自動化。
- **`check_functional_registry` gate 実装**（L4 carry）: 機能一覧 §1.5 更新規律の機械 enforcement（未登録資産 fail-close）。whole-coverage detector に統合する。
- release-please / PyPI publish: 今は不要（clone + setup.sh 配布、dist publish は park）。
- macOS/Windows matrix: shell 差分検出（可搬性 NFR）が要る時点で追加。
