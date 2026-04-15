# 設計書: LLM最適化スキルカタログ + 自動分類機 (JSONL Catalog)

> フェーズ: L2-L3 設計
> ステータス: Draft (PM 起案、TL レビュー待ち)
> 作成日: 2026-04-16
> 対象: `cli/lib/skill_catalog.py`, `cli/lib/skill_recommender.py`, `cli/helix-skill`
> 関連: `SKILL_MAP.md §自動推挙システム`

---

## 1. 概要・目的

### 1.1 現状の問題

| # | 問題 | 影響 |
|---|------|------|
| P1 | SKILL.md は人間向け自由形式。LLM が読むと token を食う | 推挙コスト増、マッチング精度低下 |
| P2 | catalog が `helix_layer`（phase）とパスカテゴリの2軸のみ。タスク粒度の絞り込みができない | 「API設計」「E2Eテスト追加」等の具体タスクで的外れな推挙が発生 |
| P3 | 新規スキル追加時、タグ・適用範囲を手動で書く必要がある | 保守コスト増、タグ品質のばらつき |

### 1.2 導入効果

- LLM 最適化 JSONL により推挙プロンプトの token を **30〜50% 削減**（見込み）
- 3軸（category × phase × task）絞込で推挙精度向上
- `helix skill classify` による自動タグ付けで新規スキル追加コスト低減

### 1.3 スコープ（Phase 1）

| 項目 | In | Out |
|------|-----|-----|
| JSONL スキーマ定義 | ✅ | — |
| `skill classify` コマンド | ✅ | — |
| 推挙 JSONL 優先読み込み | ✅ | — |
| JSONL の一括初期化 | ✅ | — |
| PostToolUse hook 自動分類 | — | Phase 2 |
| 精度 before/after 比較 | — | Phase 3 |

---

## 2. JSONL スキーマ仕様

### 2.1 配置

- **Path**: `.helix/cache/skill-catalog.jsonl`
- **形式**: 1スキル1行 JSON（改行区切り）
- **生成**: `helix skill catalog rebuild` で JSON と同時再生成
- **削除可能**: JSONL が欠けても既存 JSON から再生成される

### 2.2 フィールド定義

| フィールド | 型 | 必須 | 説明 |
|----------|-----|------|------|
| `id` | string | ✅ | `category/name` 形式（例: `common/security`） |
| `title` | string | ✅ | 日本語スキル名（30字以内） |
| `summary` | string | ✅ | 30字前後の要約（LLM マッチング用） |
| `phases` | string[] | ✅ | HELIX Phase ID 配列（`L1`〜`L8`, `R0`〜`R4`） |
| `tasks` | string[] | ✅ | Task OS の 63 タスク ID 配列（例: `design-api`） |
| `triggers` | string[] | ✅ | マッチングキーワード（名詞・動詞・略語） |
| `anti_triggers` | string[] |  | 除外キーワード（紛らわしいが違う用途） |
| `agent` | string | ✅ | 委譲先（**正規化済み短縮名固定**）: `tl/se/pg/qa/security/dba/devops/docs/research/legacy/perf/fe-design/fe-component/fe-style/fe-test/fe-a11y` |
| `similar` | string[] |  | 類似・関連スキル ID 配列 |
| `references` | object[] |  | 参考資料（JSONL 検索時に recommender が選定する候補）: `[{path, title, summary?}]` |
| `source_hash` | string | ✅ | 元 SKILL.md の SHA256（64 hex、承認引継ぎ判定用） |
| `classification` | object | ✅ | `{status, classified_at, classifier_model, confidence?}` |

`classification.status` の値と recommender での利用可否:
| status | 意味 | 通常検索で使用 |
|--------|------|--------------|
| `pending` | 自動分類済み、人間承認待ち | ❌（`review-pending` 専用） |
| `approved` | 人間承認済み | ✅ |
| `manual` | 人間が手書きで入力（分類器不使用） | ✅ |

**recommender は `approved` / `manual` のみを候補にする**。`pending` は検索結果へ流入させない（品質担保）。

### 2.2.1 agent 正規化と search prompt 契約

現行 `cli/templates/skill-search-prompt.md` は `recommended_agent` に `fe-design` 等の短縮名と `helix-codex --role security` 形式を混在で返す仕様。JSONL 導入に伴い以下に統一する:

- JSONL の `agent` フィールドは常に**正規化済み短縮名**（裸ロール名 or `fe-*`）
- 改訂後の search prompt は `recommended_agent` として JSONL の `agent` 値をそのまま返す
- dispatcher 側の `helix-codex --role X` 形式の受付は後方互換として維持（将来非推奨判断）

### 2.2.2 references フィールドの位置づけ

現行 recommender は候補ごとに参考資料 path を返す仕様。JSONL でも同機能を提供する:

- 優先: JSONL entry 内の `references` を prompt に含める（token 効率）
- fallback: JSONL に `references` が空の場合、dispatcher 側で既存 JSON catalog から補完（互換維持）

### 2.3 具体例

```jsonl
{"id":"common/security","title":"セキュリティ","summary":"脆弱性対策・秘密情報スキャン・認証認可実装","phases":["L2","L4","L6"],"tasks":["design-security","implement-auth","verify-security-scan","review-security","fix-security"],"triggers":["認証","認可","脆弱性","OWASP","秘密情報","セキュリティ"],"anti_triggers":["UI","デザイン"],"agent":"security","similar":["workflow/compliance"],"source_hash":"a1b2c3...","classification":{"status":"approved","classified_at":"2026-04-16T03:00:00Z","classifier_model":"gpt-5.4-mini","confidence":0.92}}
{"id":"common/visual-design","title":"ビジュアル設計","summary":"ブランドDESIGN.md・IA・モーション・a11y・データViz","phases":["L2","L5"],"tasks":["design-ui","review-visual","review-usability"],"triggers":["デザイン","ブランド","色","タイポグラフィ","UI/UX","Visual"],"anti_triggers":["API","DB"],"agent":"fe-design","similar":["design-tools/web-system"],"source_hash":"d4e5f6...","classification":{"status":"approved","classified_at":"2026-04-16T03:00:00Z","classifier_model":"gpt-5.4-mini","confidence":0.95}}
{"id":"common/error-fix","title":"エラー修正","summary":"デバッグ手順・失敗パターン・危険コマンドガード","phases":["L4","L6"],"tasks":["fix-bug","verify-regression"],"triggers":["バグ","エラー","デバッグ","修正","トラブルシュート"],"anti_triggers":[],"agent":"se","similar":["common/testing"],"source_hash":"789abc...","classification":{"status":"pending","classified_at":"2026-04-16T03:00:00Z","classifier_model":"gpt-5.4-mini","confidence":0.81}}
```

### 2.4 バリデーション

生成時に以下を検証:

| 対象 | ルール |
|------|-------|
| `id` | `^[a-z][a-z0-9-]*\/[a-z][a-z0-9-]*$` 形式 |
| `agent` | 許可リスト内（§2.2.1） |
| `phases` | `L1`〜`L8` or `R0`〜`R4` の enum |
| `tasks` | `helix task catalog` の既存 ID と照合 |
| `summary` | 60 字以内（30 字目安、超過は警告） |
| `source_hash` | SHA256 64 hex（小文字） |
| `classification.status` | enum: `pending` / `approved` / `manual` |
| `classification.classified_at` | ISO8601 UTC（`Z` サフィックス） |
| `classification.confidence` | 0.0〜1.0（float、`manual` は省略可） |
| 配列要素 | 重複排除（`phases` / `tasks` / `triggers` / `anti_triggers` / `similar`） |
| unknown field | **拒否**（将来追加時は明示的にスキーマ更新） |

---

## 3. `helix skill classify` コマンド仕様

### 3.1 サブコマンド

| コマンド | 動作 |
|---------|------|
| `helix skill classify <skill-id>` | 単発分類（結果を pending で JSONL に書く） |
| `helix skill classify <skill-id> --approve` | 分類 + 即承認 |
| `helix skill classify <skill-id> --dry-run` | 分類結果を stdout に出して JSONL には書かない |
| `helix skill catalog rebuild --auto-classify` | 55スキル全件を再分類（既存 approved/manual は hash 一致なら維持） |
| `helix skill catalog rebuild --auto-classify --only-pending` | **現 pending + hash 不一致で invalidated になった entry のみ**再分類（hash 一致の approved/manual は完全スキップ） |
| `helix skill review-pending` | pending 一覧表示 |
| `helix skill approve <skill-id>` | 既存 pending を承認に昇格 |

### 3.2 I/O

**入力**:
- `<skill-id>`: `category/name` 形式（例: `common/security`）
- SKILL.md の content + frontmatter
- 既存 55 スキルの JSONL（類似スキル検出用）

**出力（stdout）**:
```
[skill_classify] common/security
  phases: [L2, L4, L6]
  tasks: [design-security, implement-auth, verify-security-scan, review-security, fix-security]
  triggers: [認証, 認可, 脆弱性, OWASP, 秘密情報]
  agent: security
  similar: [workflow/compliance] (類似度 0.73)
  confidence: 0.92
  status: pending (--approve で approved に昇格)
```

**終了コード**:
| code | 意味 |
|------|------|
| 0 | 成功 |
| 2 | skill 未検出 |
| 3 | SKILL.md parse 失敗 |
| 7 | Codex 呼び出し失敗（ネットワーク/認証） |
| 8 | 分類結果のバリデーション失敗 |

### 3.3 分類器

- モデル: `gpt-5.4-mini`（`cli/roles/recommender.conf` を流用 or 別途 `classifier.conf`）
- thinking: `low`（コスト最小化）
- プロンプト: `cli/templates/skill-classify-prompt.md`（新規）
- キャッシュ: `source_hash` が同じなら再分類スキップ

### 3.4 承認引継ぎロジック

```
rebuild 時:
  for each skill in SKILL.md:
    new_hash = sha256(SKILL.md)
    if JSONL に既存 entry:
      if existing.source_hash == new_hash:
        if existing.status in {"approved", "manual"}:
          既存を維持（再分類しない）
        else:  # pending
          --only-pending なら再分類、そうでなければ維持
      else:  # hash 不一致 (SKILL.md 更新)
        if existing.status == "manual":
          manual は人手で維持されてきた値なので、content 部分は再分類しつつ
          classification.status = "pending" に降格（人間再承認を要求）
        else:  # approved or pending
          新規分類 → pending に設定
    else:
      新規分類 → pending
```

**原則**:
- SKILL.md が変われば `approved` / `manual` は `pending` に降格（品質チェック強制）
- `manual` は hash 一致の間だけ「人間信頼」として維持される
- 状態を増やさず 3 状態に閉じる（`manual-stale` 等は導入しない）

---

## 4. 既存コンポーネントとの関係

### 4.1 影響マップ

| コンポーネント | 変更 | 説明 |
|--------------|------|------|
| `cli/lib/skill_catalog.py` | 拡張 | JSON 生成は維持、`build_jsonl_catalog()` 関数追加 |
| `cli/lib/skill_recommender.py` | 拡張 | JSONL 優先読み込み、phase 事前絞込、fallback は JSON |
| `cli/lib/skill_classifier.py` | **新規** | Codex 呼び出し、スキーマ検証、類似検出 |
| `cli/lib/skill_dispatcher.py` | 変更なし | agent フィールドは JSONL 側で事前解決済み |
| `cli/helix-skill` | 拡張 | `classify` / `review-pending` / `approve` サブコマンド追加 |
| `cli/templates/skill-search-prompt.md` | 改訂 | JSONL 前提に簡略化、phase 絞込後の入力形式を反映 |
| `cli/templates/skill-classify-prompt.md` | **新規** | 分類用プロンプト |

### 4.2 データフロー

```
SKILL.md (55件)
      │
      │ rebuild
      ▼
┌──────────────────┐        ┌──────────────────────────┐
│ skill-catalog.json│        │ skill-catalog.jsonl      │
│ (リッチ情報源)    │        │ (LLM 最適化派生)         │
│ list/show/use 用  │        │ search 用                │
└──────────────────┘        └──────────────────────────┘
      │                               │
      │                               │ phase 絞込
      ▼                               ▼
  list/show/use                  skill_recommender
                                      │
                                      │ gpt-5.4-mini
                                      ▼
                                   選定結果
```

### 4.3 後方互換性と fallback 条件

**JSON fallback の発火条件**:

| 条件 | 挙動 |
|------|------|
| JSONL ファイルが存在しない | JSON fallback（静かに） |
| JSONL parse failure（行構文不正） | 警告 stderr + JSON fallback |
| JSONL schema validation failure | 警告 stderr + JSON fallback |
| `approved` / `manual` が 0 件（全て pending） | JSON fallback（未承認のみでは本線にしない） |
| phase/task フィルタ適用後 JSONL 候補 0 件 | JSONL 正常扱い、「候補なし」を返す（fallback しない） |
| `--no-jsonl` オプション指定 | 強制的に JSON 使用 |

**既存挙動維持**:
- `skill-catalog.json` は削除・置換しない
- `helix skill list / show / use` の出力・引数は無変更
- `--no-jsonl` でいつでも従来挙動に戻せる

---

## 5. マイグレーション方針

### 5.1 ステップ

| Step | 内容 | 影響範囲 |
|------|------|---------|
| M1 | `build_jsonl_catalog()` 実装 + rebuild が JSON と JSONL 両方生成 | 非破壊（JSON は変わらず） |
| M2 | `skill_classifier.py` 実装 + classify コマンド追加 | 新機能のみ |
| M3 | 55 スキル一括 auto-classify 実行 → pending 状態 | JSONL 生成のみ |
| M4 | 人間レビュー（PM が review-pending → approve） | JSONL のみ更新 |
| M5 | recommender を JSONL 優先に切替（**前提: 対象 entry が `approved` or `manual`**） | M4 で承認済み entry のみ本線投入 |
| M6 | (Phase 3) 精度計測後、JSON を非推奨化判断 | 判断のみ |

### 5.2 ロールバック

- JSONL 削除で自動 fallback（JSON を使い続ける）
- recommender は `--no-jsonl` オプションで強制 JSON 使用可

---

## 6. 実装工程表

### 6.1 実装タスク分解（se/pg 委譲用）

| ID | タスク | ロール | サイズ | 依存 |
|----|-------|--------|-------|------|
| T1 | JSONL スキーマ定義 + バリデータ実装 | pg | S | — |
| T2 | `skill_catalog.build_jsonl_catalog()` 実装 | pg | M | T1 |
| T3 | `cli/templates/skill-classify-prompt.md` 作成 | docs/pg | S | T1 |
| T4 | `skill_classifier.py` 実装（Codex 呼び出し） | se | M | T1, T3 |
| T5 | `helix skill classify` サブコマンド実装 | pg | S | T4 |
| T6 | `helix skill review-pending / approve` 実装 | pg | S | T2 |
| T8 | `cli/templates/skill-search-prompt.md` 改訂（契約確定） | docs | S | T1 |
| T7 | `skill_recommender.py` を JSONL 優先に改修 | se | M | T2, T8 |
| T9 | 単体テスト（schema/catalog/classifier/recommender/fallback） | qa | M | T2-T7 |
| T10 | 統合テスト（55件一括分類 + search 精度計測、Codex は mock） | qa | M | T9 |
| T11 | 55件 auto-classify 実行 + PM 承認 | PM | M | T10 |

### 6.2 優先順と並列化

```
Phase A (直列):
  T1 → T2, T3, T8 並列 → T4 → T5, T6 並列

Phase B (Phase A 完了後):
  T7（T8 の prompt 契約が先行確定している前提）

Phase C (Phase A,B 完了後):
  T9 → T10 → T11
```

T8 は T7 の入力契約を決めるため T7 より先行 or 同時に進める（TL 指摘 P2）。

### 6.3 推定規模

- 総サイズ: **M**（4〜10 ファイル、200〜500 行）
- 見積もり工数: 2〜3日（PM 承認時間除く）

---

## 7. リスク・トレードオフ

| # | リスク | 影響 | 緩和策 |
|---|-------|------|-------|
| R1 | 自動分類の誤りが catalog 全体に伝播 | 中 | `status: pending` デフォルト、PM 承認必須 |
| R2 | Task OS タスク ID が変わると JSONL が不整合化 | 中 | バリデーションで catalog が無効な ID を拒否 |
| R3 | LLM 分類のコスト増（55件 × rebuild 回数） | 小 | `source_hash` による re-classify 抑制 |
| R4 | JSON と JSONL の二重管理で差分発生 | 中 | 毎回 rebuild で両方を同時再生成、単一ソース（SKILL.md） |
| R5 | 推挙精度が改善しない可能性 | 中 | Phase 3 で skill_usage での before/after 比較、劣化なら JSON に巻き戻し |
| R6 | gpt-5.4-mini の出力形式揺れ | 中 | 分類結果を strict JSON schema で validation、失敗時は再試行3回 |

---

## 8. PoC 提案

### 8.1 推奨: **5スキル先行 PoC**

#### 対象スキル（多様性確保）
| ID | 理由 |
|----|------|
| `common/security` | phase 跨ぎ（L2, L4, L6）・agent=security の代表 |
| `common/visual-design` | agent=fe-design、フロント領域の代表 |
| `common/error-fix` | 頻度高い、L4 実装系 |
| `workflow/design-doc` | L2 専用、文書系 |
| `tools/ai-coding` | 横断スキル、triggers 広範 |

#### 検証項目
- [ ] JSONL スキーマが実スキルで破綻しないか
- [ ] 分類器が適切な agent/phases/tasks を返すか
- [ ] recommender が JSONL 使用時に従来同等以上の推挙を返すか（3〜5 タスクで比較）
- [ ] `source_hash` 引継ぎが正しく動作するか

#### 進め方
1. T1-T4 実装（pg/se 委譲）
2. 5件手動分類 → JSONL 手書き（分類器検証の baseline）
3. 分類器で 5件自動分類 → 手書きとの差分を PM レビュー
4. recommender 改修 → 3 クエリで baseline と比較
5. 問題なければ 55 件全件 auto-classify に進む

### 8.2 代替: いきなり 55 件一括（推奨しない）

- メリット: 早い
- デメリット: 分類誤りが一気に入り、切り分けに時間かかる
- 判断: **却下**

---

## 9. オープンクエスチョン（TL レビュー済・回答反映）

| Q# | 質問 | TL 回答 |
|----|------|--------|
| Q1 | 分類器は recommender.conf 流用 or 専用 classifier.conf か | **専用 `cli/roles/classifier.conf` を切る**。recommender は候補選定、classifier は構造化抽出でプロンプト・再試行・制約が異なる。モデルは同じ `gpt-5.4-mini` / thinking=low |
| Q2 | JSONL 側でも HELIX_HOME 解決が必要か | **必要**。`HELIX_SKILLS_ROOT → HELIX_HOME/skills → repo/default` の順で解決を揃える。共通 helper 化も検討 |
| Q3 | 類似検出の閾値は PoC で決めて良いか | **良い**。初期値 0.70、PoC で 0.65/0.70/0.75 を比較。hard fail にせず補助情報として扱う |
| Q4 | テスト粒度は | **unit + Codex mock integration まで必要**。unit: schema validation / JSONL read-write / hash invalidation / agent normalization / fallback。integration: 分類成功 / 不正 JSON / validation fail / retry / exit code 7,8 を mock で |
| Q5 | JSONL の行順は | **alphabetical by `id`**。diff 安定・レビュー容易・再現性保持 |

---

## 10. 成果物

- [x] 設計書（本ファイル）
- [ ] `skill-catalog-jsonl-sample.jsonl`（PoC 5件、T1 完了時に追加）
- [ ] `skill-classify-prompt.md`（T3）

---

**承認欄**
- PM: 起案（2026-04-16）
- TL: ✅ レビュー済（2026-04-16、conditional → P1/P2/P3 反映済で pass 相当）
- PO: 不要（CLI 内部変更）

**TL 指摘の反映トレーサビリティ**:
| 指摘 | 反映先 |
|------|-------|
| P1: pending/approved/manual 利用条件 | §2.2, §5 (M5 前提) |
| P1: agent 正規化 + prompt 契約 | §2.2.1 |
| P1: references フィールド | §2.2, §2.2.2 |
| P2: manual 引継ぎロジック | §3.4 |
| P2: --only-pending 定義 | §3.1 |
| P2: fallback 条件細分化 | §4.3 |
| P2: T7/T8 依存順 | §6.1, §6.2 |
| P3: バリデーション | §2.4 |
| P3: typo (scheme→schema) | §6.1 T9 |

※ P3 日付指摘: 現在日は 2026-04-16（memory 確認済み）のため維持。
