# fe 駆動の詳細フロー

> 目的: fe / fullstack 駆動採用時の L2〜L4 における具体的ステップ、モック駆動の実施手順、TL による API 契約導出プロセス、モック由来 debt のライフサイクルを定義する。
>
> 適用範囲: `helix-size --drive fe` または `--drive fullstack`（自動判定含む）
>
> 正本: SKILL_MAP.md §駆動タイプ別 L2〜L5 / gate-policy.md G2/G3/G4/G6

---

## 1. フェーズ別ステップ

### L1 要件定義（fe 駆動の追加観点）

- ユースケース一覧 + 画面一覧（IA の前段）
- UX 期待値（ペルソナ・デバイス・a11y・i18n）
- 成功指標（CV・離脱率等、UX KPI を含む場合）

### L2 モック駆動設計（fe-design サブエージェント主導）

| Step | 担当 | 成果物 | 備考 |
|------|------|--------|------|
| 2.1 | fe-design | ブランド方針 + デザイントークン | visual-design §①information の具体化 |
| 2.2 | fe-design | 情報アーキテクチャ（IA） | `docs/fe/D-IA.md` |
| 2.3 | fe-design | **モック** `.helix/mock/<feature>/mock.html` | HTML + Tailwind CDN、Alpine.js 任意。`src/` から import 禁止 |
| 2.4 | fe-design | **状態・イベント定義** `state-events.md` | 画面状態・イベント・遷移図（mermaid）・BE契約導出メモ |
| 2.5 | PM+PO | UX 承認（モックを触って確認） | G2 の必須入力 |

**G2 通過時の自動処理**:
- `helix-gate` が `.helix/phase.yaml` の `sprint.drive` が `fe|fullstack` なら以下を debt-register に auto-enqueue:
  - `MOCK-DERIVED-CONTRACT`（TL レビュー対象、target_sprint=L6、owner=TL）
  - `MOCK-HARDCODE`（grep 対象、target_sprint=G4、owner=SE）
  - `MOCK-CODE-LEAK`（AST 対象、target_sprint=G4、owner=SE）

### L3 契約導出（TL = Codex 5.4 主導）

| Step | 担当 | 成果物 | 備考 |
|------|------|--------|------|
| 3.1 | TL | `state-events.md` 精読 | 画面状態と発生イベントから API 需要を抽出 |
| 3.2 | TL | API 契約導出 → `D-API` | 各イベント → エンドポイント / リクエスト / レスポンス |
| 3.3 | TL | データモデル設計 → `D-DB` | 状態の永続化要件から逆算 |
| 3.4 | TL | 状態管理設計 → `D-STATE` | クライアント状態 / サーバー状態の境界 |
| 3.5 | TL | ドメイン整合性レビュー | 画面都合で歪んでいないか確認（MOCK-DERIVED-CONTRACT の消化前準備） |
| 3.6 | TL + PM | テスト設計 + 工程表 → `D-TEST` + `D-PLAN` | マイクロスプリント割付 |

**G3 追加条件** (fe/fullstack):
- モック凍結済み
- `state-events.md` から API 契約導出完了（`D-API` 凍結）
- fullstack は D-CONTRACT 凍結も必須

### L4 実装（モックを本実装に昇格）

fe 駆動は BE/FE 並列 + L4.5 結合:

```
Phase A (並列):
  BE Sprint (.1a → .1b → .2 → .3 → .4 → .5): TL 契約ベース実装
  FE Sprint (.1a → .1b → .2 → .3 → .4 → .5): モック UI を本実装化
    └─ .1a: mock.html のコンポーネント分解・Props 設計
    └─ .1b: fe-component が本実装（Vue/React/Svelte 等）に移植
    └─ .2:  fe-style が Tailwind/CSS 統合
    └─ .3:  セキュリティチェック（モックハードコード除去 ⇒ MOCK-HARDCODE 消化着手）
    └─ .4:  fe-test が unit/integration 追加
    └─ .5:  API 結合（モックデータ ⇒ 実 API に置換）

Phase B: L4.5 結合テスト（Contract CI pass 必須）
```

**G4 追加条件** (fe/fullstack):
- `MOCK-HARDCODE` resolved（モック由来のハードコード値が本実装に残存していない）
- `MOCK-CODE-LEAK` resolved（`.helix/mock/` が `src/` から import されていない）

### L5 Visual Refinement（モック → 本実装の品質昇格）

- モック時の UX を本実装でも再現できているか
- デザイントークンの一貫性
- a11y（fe-a11y が監査）

### L6 統合検証

**G6 追加条件** (fe/fullstack):
- `MOCK-DERIVED-CONTRACT` resolved（TL が L6 で API 契約のドメイン整合性を再レビュー済み）

---

## 2. 責務分担

| ロール | 担当 | L2 | L3 | L4 | L5 | L6 |
|-------|------|----|----|----|----|-----|
| fe-design | サブエージェント | **モック + state-events** | — | .1a (Props 分解) | — | — |
| fe-component | サブエージェント | — | — | .1b (本実装移植) | — | — |
| fe-style | サブエージェント | — | — | .2 | リファイン | — |
| fe-a11y | サブエージェント | — | — | — | 監査 | 監査 |
| fe-test | サブエージェント | — | テスト設計 | .4 | — | — |
| TL (Codex 5.4) | 契約導出 + レビュー | G2 レビュー | **契約導出** | Sprint レビュー | — | MOCK-DERIVED-CONTRACT 消化 |
| SE (Codex 5.3) | BE 上級実装 | — | — | BE Sprint | — | — |
| PG (Codex 5.3 Spark) | BE 通常実装 | — | — | BE Sprint | — | — |
| Opus (PM) | 統合・判断 | UX 承認参加 | 工程表承認 | Sprint 監視 | Visual 判断 | RC 判定 |

---

## 3. モック由来 debt のライフサイクル

| ID | 登録タイミング | 消化タイミング | 消化条件 | 未消化時の挙動 |
|----|-------------|-------------|---------|-------------|
| MOCK-DERIVED-CONTRACT | G2 通過時 (auto) | L6 | TL がドメイン整合性レビュー完了 → `helix debt resolve --id MOCK-DERIVED-CONTRACT` | **G6 fail-close** |
| MOCK-HARDCODE | G2 通過時 (auto) | G4 | grep でハードコード値が残存していないことを確認 → resolve | **G4 fail-close** |
| MOCK-CODE-LEAK | G2 通過時 (auto) | G4 | `.helix/mock/` が `src/` から import されていないことを AST で確認 → resolve | **G4 fail-close** |

**be / db / agent 駆動**: 上記 debt は登録されない。fail-close も適用されない（advisory のまま）。

---

## 4. アンチパターン

| アンチパターン | 回避策 |
|-------------|-------|
| モック作成を飛ばして L3 に進む | fe-design が G2 で mock.html + state-events.md を必須化している |
| モックのコードを本実装にコピペ | L4.1b で fe-component が「分解 → 移植」する。.helix/mock/ は throw-away |
| state-events.md を書かずに API 契約を書く | TL が L3 で state-events.md 読めないと契約導出不可 |
| モック時のハードコード値（URL / トークン / テストデータ）が本番に残る | G4 で MOCK-HARDCODE が fail-close |
| `import from "../../.helix/mock/..."` | G4 で MOCK-CODE-LEAK が fail-close |
| 画面都合で API が歪み、ドメイン貧弱化 | L6 で TL が MOCK-DERIVED-CONTRACT を再レビュー |

---

## 5. 関連ドキュメント

- 駆動タイプ別 L2〜L5 テーブル: `skills/SKILL_MAP.md §駆動タイプ別 L2〜L5`
- ゲート通過条件: `skills/tools/ai-coding/references/gate-policy.md`
- fe-design スキル本体: `skills/project/fe-design/SKILL.md`
- モックテンプレート: `skills/project/fe-design/references/mock-template.md`
- visual-design: `skills/common/visual-design/SKILL.md`
- 実装設計案（history）: `.helix/design-proposals/fe-drive-and-drift-check-expansion.md`
