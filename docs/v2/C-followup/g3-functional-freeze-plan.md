# G3.functional_freeze 実装 Step 詳細（V2）

作成日: 2026-05-14  
対象: `docs/v2/L1-REQUIREMENTS.md §3.8 FR-VS03`, `docs/v2/v2-gate-overlay.md §2`, `cli/helix-gate`, `cli/lib/helix_db.py`, `cli/tests`  
作成者: Docs 実装タスク（実装）

## 0. 目的

`G3.functional_freeze` を、サブゲートとして helix CLI 実装と整合する形で実装するための具体手順を規定する。  
本計画は既存の `G3` を破壊せず、既存 `gate-policy.md` の正本を保持しつつ V2 追加仕様として運用する。

## 1. 要件参照

- `docs/v2/L1-REQUIREMENTS.md §3.8 FR-VS03`
  - `design_sprint_entries` ベースの `pair_status` 判定の導入
  - `pairing`（design/test design）を軸にした G2/G3 系の制約追加
- `docs/v2/v2-gate-overlay.md §2`
  - V2 追加規則（G3.functional_freeze）を `pair_status='paired'` として明文化
- `vmodel-semantics.yaml`（L1 判定連動）
  - `requires_functional_freeze` 参照

## 2. 実装目標（Definition of Done）

1. CLI `helix gate G3 --subgate functional_freeze --plan-id <PLAN>` が使用可能
2. 既存 `G3` は維持しつつ、サブゲートとして段階的 enforce が可能
3. L1 size 判定と drive 判定が連動し、L 案件で fail-close できること
4. 監査観点（設計観点・テスト設計観点）を含む pass/blocked/skip の挙動が明確
5. テスト（bats + pytest）を追加し、pass/false positive の再現まで可能
6. 関連ドキュメントに実装 step と運用ルールを反映

## 3. 関連データ構造

- `design_sprint_entries`（データソース）
  - 調査対象: `plan_id`, `drive`, `track`, `pair_status`, `sprint_type`
  - `pair_status` enum: `pending`, `paired`, `design_only`, `test_only`, `waived`, `failed`
- テスト設計側は `test_design_entries` 相当の実データを横断して確認
- L1 接続: `vmodel-semantics.yaml` の `requires_functional_freeze`（論理キー）

## 4. CLI 仕様（確定）

```bash
helix gate G3 --subgate functional_freeze --plan-id PLAN-NNN [--drive <drive>]
```

### 4.1 オプション仕様

- `--subgate`: `G3` のみ有効。`functional_freeze` 以外は warning + 既存処理またはエラーハンドリング
- `--plan-id` : 対象 plan
- `--drive` : 既存 drive 引数と整合（`fe`, `fullstack`, `db`, `be`）

### 4.2 結果仕様

- 通過
  - 条件を満たしたときに `passed` を返却
- 失敗
  - fail-close の対象条件を満たせなかったとき `failed`
- 警告
- skip
  - `size=S/M` + 該当運用ポリシー時は warning + passed（互換運用）

## 5. §1 enforce 条件の実装

## 5.1 TL 決定値（L1 + Drive）

| 条件 | 判定 |
|---|---|
| L1 + `size=L` + `drive in (fe,fullstack,db)` | hard-fail 条件 |
| L1 + `size=L` + `drive=be` | 観察対象（フェーズ拡張方針によりフェーズ4.4で適用可能性） |
| L1 + `size in (S,M)` | warning/skip 可 |
| 例外 (`size` 不明 / `drive` 不明) | 最小限 fail-close 推奨、または warning 再試行 |

### 5.2 実装ステップ

1. `vmodel-semantics.yaml` の `requires_functional_freeze` を評価して、当該 plan が対象かを判定
2. `cli/helix-gate` 内の size 判定と drive 判定を OR 条件にして fail-close 可否を決定
3. 例外値（`size`/`drive` 未設定）の場合は `skip` と `warning` の順を検討し、将来フェーズで fail-close へ昇格

## 6. §2 通過条件の実装

- pass 条件（論理 AND）
  - `design_sprint_entries.pair_status = 'paired'`
  - functional レイヤー design + unit test_design が共に存在
  - 垂直レビュー (`vertical_review`) と水平レビュー (`horizontal_review`) の両方が `passed`
- 実装ポイント
  - `review_axes` 集約関数を新設し、既存 `pair-check` と互換で再利用
  - `contract_entries` と `test_design_entries` の存在を同一 `plan_id` で照合

## 7. Step 1: `cli/helix-gate` サブゲート追加

### 7.1 引数 parse

- Bash entry に `--subgate` を追加
- `--subgate functional_freeze` を検知
- 既定値は空文字列（現行 G3 動作に影響なし）

### 7.2 handler 実装

- `G3` ハンドラ内で分岐
- `subgate=functional_freeze` の場合は `evaluate_subgate_functional_freeze`（または等価ロジック）を呼ぶ
- 想定呼出し:
  - `helix gate G3 --subgate functional_freeze --plan-id PLAN-XXX`
  - `helix gate G3 --subgate functional_freeze --plan-id PLAN-XXX --json`

### 7.3 既存 G3 との非破壊共存

- `--subgate` 未指定時は従来 G3 判定のみ
- `--subgate` 指定時でも `G3` 基本チェックは必要に応じて分岐実行
- `--json` 結果形式は既存スキーマを維持し、subgate 失敗情報を追加

## 8. Step 2: `helix_db.py` へ `pair_status` 取得関数追加

### 8.1 追加関数

```bash
query_functional_pair_status(plan_id, drive)
```

### 8.2 期待ロジック

1. `design_sprint_entries` を `plan_id` で絞る
2. `track` が `functional` に近い値を持つ行と、`test_design` が `unit` に近い行を抽出
3. `pair_status` を `paired` の有無で集約し、ない場合はエラー理由を返却
4. 追加観点: `sprint_type`/`pair_status` の不一致

### 8.3 既存関数との整合

- `query_design_review_pair` 既存関数の呼び出しパターンを踏襲（引数名/戻り値を揃える）
- 返却値は `pair_status`, `has_design`, `has_unit`, `errors` を保持

## 9. Step 3: enforce 判定を L1 と連動

### 9.1 vmodel-semantics 参照

- `requires_functional_freeze=true` の plan に対してのみ、`subgate` が評価対象
- それ以外は warning-only / skip（将来 policy 切替時に fail-close へ昇格）

### 9.2 失敗時の分岐

- size/drive 条件が未充足なら `warning` か `failed` を選択
- フェーズ移行に合わせて `failed` 優先化（Phase 4.4）

## 10. Step 4: テスト実装

### 10.1 bats

- `cli/tests/test-helix-gate.bats` を追加更新
  - G3 functional_freeze: 通過パターン
    - size=L + fe/fullstack/db + `pair_status=paired` → passed
    - size=L + fe/fullstack/db + `pair_status!=paired` → failed
  - スキップ/警告パターン
    - size=S/M + 任意 drive → warning + passed
  - 不整合パターン
    - `--subgate` 未指定（既存 G3）
    - `--subgate unknown`（エラー or warning）
    - `plan_id` 不在（plan未登録）

### 10.2 pytest

- `cli/tests/test_helix_db.py` または対象 pytest に追加
  - `query_functional_pair_status` の単体ケース
  - 正常: `paired` 判定 true
  - 異常: 行不在、値欠損、複数行不一致、`track/test_type` 混在
  - サイズ/drive 分岐に依存しない core 判定と連携確認

## 11. Step 5: ドキュメント更新

### 11.1 `docs/v2/v2-gate-overlay.md`

- `G3` / `G3.functional_freeze` の節に以下を追記
  - 実装 command
  - `pair_status='paired'` の明文化
  - Phase 4.x 段階的 enforce ロードマップ
  - `size + drive + vmodel-semantics` の判定式

### 11.2 `skills/tools/ai-coding/references/gate-policy.md`

- `G3` 付録として subgate 記載を追加
- `functional/unit` のペア凍結を G3 サブゲートとして補足
- CLI 例: `helix gate G3 --subgate functional_freeze ...`
- 既存 G3（public gate）の条件は変更しない

## 12. §3 既存 G3 との関係（運用上の注意）

- `G3` pass は `detailed+integration` ペアリングを重視
- `G3.functional_freeze` pass は `functional+unit` ペアリングを重視
- 両方 pass が必要になって初めて `G4` へ進行可能
- 1 方のみ pass の状態では `blocked` もしくは `warning` を返し、次アクションを明示

## 13. §4 段階的 enforce ロードマップ（運用計画）

### Phase 4.1

- 目的: false positive の最小化
- 振る舞い: warning only
- 期待効果: 既存計画へのノイズ低減、問題事例の収集

### Phase 4.2

- 目的: FE 優先導入
- 振る舞い: `drive=fe` かつ `size=L` のときのみ fail-close
- 期待効果: 実装直近リスクを圧縮しつつ、影響を限定

### Phase 4.3

- 目的: fullstack / db へ拡張
- 振る舞い: `drive in (fe,fullstack,db)` × `size=L` で fail-close
- 期待効果: ドメイン横断のペアリング未完了を低減

### Phase 4.4

- 目的: 全ドライブ統一運用
- 振る舞い: 定義済み条件を全 drive に適用
- 期待効果: 全体ゲート品質の一貫性

## 14. §5 Reverse / Scrum 接続

- Reverse: R4 後の forward 接続時、必要最小 gap についてのみ subgate 判定
- Scrum: confirmed 後の sprint 開始時評価。confirmed 以前は warning のみ運用で可
- evidence が未整備なら `interrupted` より前に warning で再収集要件を提示

## 15. 実装タスク分解（Step 実行順）

1. `cli/lib/helix_db.py`: `query_functional_pair_status` 追加
2. `cli/helix-gate`: `--subgate` parse + dispatch
3. `cli/helix-gate`: `review_axes` 連動分岐追加
4. `cli/tests`: bats 追加
5. `cli/tests`: pytest 追加
6. `docs/v2/v2-gate-overlay.md`: 仕様反映
7. `skills/tools/ai-coding/references/gate-policy.md`: 正本準拠参照
8. Link チェックと TODO 整合レビュー

## 16. リスクと対処

- `design_sprint_entries` の実データ整合
  - 対処: 欠損時は warning/failed の明示理由を返却
- `size=S/M` の運用逸脱
  - 対処: Phase 4 ごとに policy 設定を切り替え、skip条件を明示
- CLI オプション競合
  - 対処: parse 例外は既存エラー形式に統一
- テストデータの drift
  - 対処: v2 fixture は schema を固定し、`pair_status` の観測値を明記

## 17. 変更対象ドキュメント

- 新規作成: `docs/v2/C-followup/g3-functional-freeze-plan.md`（本書）
- 更新対象:
  - `docs/v2/v2-gate-overlay.md`
  - `skills/tools/ai-coding/references/gate-policy.md`

## 18. リンク整合チェック（実施観点）

1. `L1-REQUIREMENTS` ↔ `v2-gate-overlay`
   - 根拠リンク: `§3.8 FR-VS03`
2. `v2-gate-overlay` ↔ `gate-policy`
   - V1 正本と V2 追加の上下関係が明記されているか
3. CLI docs ↔ テスト参照
   - 実装コマンドがテスト名と一致しているか
4. `vmodel-semantics` 参照
   - `requires_functional_freeze` が実装手順に反映されているか

## 19. TODO（未解決）

- TODO-1: `helix gate G3 --subgate functional_freeze` の実体実装（CLI）
- TODO-2: `origin_mode` / `evidence_status` を fail-close 条件に組み込むかを Phase 5 で再定義
- TODO-3: pair 判定における `waived` の運用上限値（期限、理由必須項目）を policy へ統合

## 20. 承認ゲート（実装完了条件）

- CLI ドライバの挙動が仕様どおりで、失敗時ログに原因分類（size/drive/pair/missing）が出る
- テスト追加が両方の枠組み（bats/pytest）で収束
- overlay / policy ドキュメントの差分が互いに参照し合い、相互矛盾がない
- TODO の未消化が残る場合は次フェーズのチケット化

