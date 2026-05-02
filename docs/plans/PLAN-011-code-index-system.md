# PLAN-011: コード index 登録システム (v1.2)

## §1. 目的 / Why

HELIX 開発が拡大する中で、同様のロジック・関数・パーサ・モデルが重複実装される問題が顕在化している (例: skill_catalog の frontmatter parser を `code_catalog` 用に再実装するリスク、`helix.db` migration が複数 PLAN で類似 schema を作成する等)。

スキル catalog と同じ枠組みで、コード自体にメタデータを付与し、検索 / 重複検知 / 統計を可能にする。これにより:

- 実装前の流用候補発見 (`helix code find`)
- 重複実装の早期検出 (`helix code dup`)
- domain 別のコード分布把握 (`helix code stats`)
- 実装着手時の Codex/Sonnet への流用先指示 (context bundle として `helix code show` 出力を渡す)

PLAN-002 (HELIX 棚卸し基盤) で扱った「成果物の機械可読化」を、コード資産そのものへ拡張する位置付け。

## §2. スコープ

### §2.1 含む

- コードメタデータ規約 (`# @helix:index id=... domain=... summary=...` 形式)
- `cli/lib/code_catalog.py`: index 抽出 / JSONL 化 / DB 同期
- `helix.db` v14 migration: `code_index` table + index 追加
- `cli/helix-code` CLI: build / find / show / dup / stats / list
- **`cli/helix` dispatcher への `code)` ケース追加 + help 更新** (P2-a 解消)
- find は `cli/lib/skill_recommender.py` の枠組みを流用 (`gpt-5.4-mini`、recommender.conf 流用)
- dup は domain 内 summary similarity (token-based) で実装
- redaction: secret-like value (token-like long sequence) と複合パターン (`auth.?token` / `bearer.?token` / `api.?key` 等) を含む summary を拒否 (`tokenize` / `token-based` 等の技術用語は許容、§3.5 参照)
- pytest (`cli/lib/tests/test_code_catalog.py`) + bats (`cli/tests/test-helix-code.bats`)
- **PoC seed metadata 付与** (P1 解消): `cli/lib/skill_catalog.py` の主要関数 3-5 個 (例: `_parse_scalar`, `_strip_quotes`, `_parse_yaml`, `parse_skill_md`) に `@helix:index` を付与し、catalog 動作確認 (find / show / dup の self-host 受入条件で使用)
- ドキュメント: `skills/SKILL_MAP.md` 末尾に CLI 行追加 / `helix/HELIX_CORE.md` の「タスク受領」に流用候補確認手順を追加

### §2.2 含まない

- AST レベルの semantic 解析 (本 PLAN はコメント抽出のみ)
- 多言語対応の網羅 (本 PLAN は Python / bash のみ走査。TypeScript / Go は次 PLAN)
- **markdown (`.md`) / bats (`.bats`) の走査** (v1.2 で除外決定): heredoc 本文や code block 内の `# @helix:index` 例を構文判定で除外できないため、test fixture / docs 内の marker が偽 entry として登録されるリスクを回避
- 既存 CLI/lib への **網羅的** 遡及メタデータ付与 (PoC seed §2.1 を除く。網羅付与は別 PLAN-011.1 起票方針)
- IDE 統合 / VSCode extension 連携
- AI 自動メタデータ生成 (本 PLAN は手動付与前提、自動化は次 PLAN)

## §3. 採用方針

### §3.1 メタデータ規約

コメント形式 (Python):

```python
# @helix:index id=code-catalog.parse-frontmatter domain=cli/lib summary=YAML frontmatter を Python dict に展開する
def parse_frontmatter(text: str) -> dict[str, Any]:
    ...
```

bash の場合:

```bash
# @helix:index id=helix-code.build domain=cli summary=git tracked files を走査して code-catalog を再構築
build_catalog() {
    ...
}
```

フィールド:

| フィールド | 必須 | 内容 |
|---|---|---|
| `id` | 必須 | kebab-case dotted (例: `code-catalog.parse-frontmatter`)。プロジェクト内で一意 |
| `domain` | 必須 | コードの所在カテゴリ (例: `cli/lib`, `cli/scripts`, `skills/workflow`) |
| `summary` | 必須 | 1 行 (≤ 80 char、日本語可) |
| `since` | 任意 | commit hash 短縮 or version (例: `v1`, `0d093ff`) |
| `related` | 任意 | 関連 id をカンマ区切り (例: `skill-catalog.parse-frontmatter`) |

走査対象 (v1.2): `git ls-files` で取得した tracked files のうち `*.py`, `*.sh` (本 PLAN scope)。
- Python: `tokenize.COMMENT` トークンのみ抽出 (文字列リテラル / docstring 内の marker を除外)
- bash: `lstrip().startswith("#")` で純コメント行のみ抽出
- `.md` / `.bats` は heredoc / code block 内の例を構文判定で除外できないため対象外 (v1.2 で除外決定、§2.2 参照)
- 直近 1 行下の Python `def` / `class` / bash function に紐付く想定

### §3.2 catalog format

二層構造 (P2-b 解消):

- **JSONL = 正本** (authoritative source): `.helix/cache/code-catalog.jsonl` (gitignore 対象)
- **DB = 派生キャッシュ** (derived cache): `helix.db` v14 `code_index` table

`helix code build` のフロー:

1. 全 git tracked files を走査 → JSONL を **完全再生成** (旧内容 truncate + 新内容書き込み、atomic write)
2. JSONL から DB へ反映: `DELETE FROM code_index` → JSONL 全 entry を upsert (一括 prune + rebuild)
3. JSONL 書き込み失敗時は DB を変更しない (古い JSONL と DB のペアを維持)
4. DB 反映失敗時は JSONL を 1 つ前の世代に rollback (`.helix/cache/code-catalog.jsonl.prev` を保持)

これにより、削除 / rename / redaction skip された entry は build ごとに自動 prune され、stale data が残らない。`find / show / stats` は常に DB を参照する (高速化のため)。

| カラム | 型 | indexed | 用途 |
|---|---|---|---|
| `id` | TEXT PRIMARY KEY | yes | unique constraint + lookup |
| `domain` | TEXT | yes | フィルタ / stats 集計 |
| `summary` | TEXT | yes | find / dup 入力 |
| `path` | TEXT | yes | show 表示 |
| `line_no` | INTEGER | — | show 表示 |
| `since` | TEXT | — | 詳細表示 |
| `related` | TEXT | — | 詳細表示 |
| `source_hash` | TEXT | — | catalog rebuild 必要判定 |
| `updated_at` | DATETIME | — | 最終更新 |

JSONL 形式 (1 行 1 entry):

```json
{"id":"code-catalog.parse-frontmatter","domain":"cli/lib","summary":"...","path":"cli/lib/code_catalog.py","line_no":42,"since":"v1","related":[],"source_hash":"abc123","updated_at":"2026-05-02T23:55:00+09:00"}
```

### §3.3 CLI 設計

```
helix code build              # 全 tracked files 走査 → JSONL + DB 同期 (replace + prune)
helix code find <query> [-n 5]  # gpt-5.4-mini マッチング
helix code show <id>          # 詳細 (path:line_no, full metadata)
helix code dup [--threshold 0.85] [--domain <name>]  # similarity 検出
helix code stats [--by domain|since]  # 集計
helix code list [--domain <name>] [--json]  # 一覧
helix code --help             # サブコマンド一覧 (cli/helix dispatcher 経由)
```

**`cli/helix` dispatcher 統合** (P2-a 解消): `cli/helix` の case 文に `code) exec "$SCRIPT_DIR/helix-code" "$@" ;;` を追加し、help 出力にも `code  コードインデックス検索/重複検出/統計` を含める。bats テストでは `helix code --help` 経由で起動を確認する。

#### find の振る舞い

- `cli/templates/skill-search-prompt.md` 相当のプロンプトテンプレートを `cli/templates/code-search-prompt.md` として新設
- 推挙結果は `.helix/cache/recommendations/code/<sha256>.json` に 1 時間キャッシュ
- 出力: id / domain / summary / path:line_no / score / 推挙理由

#### dup の振る舞い

- 同 domain 内で summary を tokenize (空白 + 記号区切り)
- Jaccard 係数 ≥ threshold (default 0.85) を duplicate 候補として返却
- LLM は使わない (token-based のみ。LLM 拡張は次 PLAN)

### §3.4 既存資源の流用

| 流用元 | 流用先 | 範囲 |
|---|---|---|
| `cli/lib/skill_catalog.py` | `cli/lib/code_catalog.py` | frontmatter parser ヘルパー (`_parse_scalar`, `_strip_quotes`) を共通モジュール化、または import |
| `cli/lib/skill_recommender.py` | `cli/lib/code_recommender.py` | gpt-5.4-mini 呼び出し / キャッシュ機構 (recommender.conf 流用) |
| `cli/lib/skill_dispatcher.py` | (流用検討) | dispatcher 流用は本 PLAN scope 外 (find は dispatcher を持たない) |
| `cli/helix-skill` | `cli/helix-code` | bash サブコマンド分岐パターン |
| `cli/lib/helix_db.py` | (拡張) | v14 migration 追加 |

共通化対象 (`cli/lib/_yaml_parser.py` 相当の純関数群) は本 PLAN で抽出するかは TL レビュー時に判断 (重複コード防止 vs 抽出コスト)。

### §3.5 redaction (P3 解消)

コードコメントは公開可能だが、以下の場合は登録を拒否する。**安全な技術用語 (`tokenize`, `token-based`, `passwordless` 等) は誤検出しないよう、複合パターンと secret-like value を分離する**:

#### danger pattern (複合パターン、case-insensitive)

| パターン | 検出例 | 非検出例 (許容) |
|---|---|---|
| `(auth\|api\|access\|bearer\|refresh)[-_. ]?(token\|key\|secret)` | `auth_token`, `api-key`, `bearer.token` | `tokenize`, `token-based parser` |
| `password\b` (語境界) | `password verify` | `passwordless`, `passwords-table-doc` |
| `credential(s)?\b` | `credentials store` | `credentialing` (語境界外) |
| `client[-_ ]?secret` | `client_secret` | `secrets-management` (パターン不一致) |

#### secret-like value detection

- summary 内の連続 32 文字以上の `[a-zA-Z0-9+/=_-]` シーケンス → token-like value とみなして拒否
- ただしバージョン文字列 (`v1.0.0` 形式) / commit hash 短縮 (`[0-9a-f]{7,12}` の単独語) は除外

#### 検出時の挙動

- `helix code build`: 警告 + skip (catalog に登録しない)
- 警告ログ: `.helix/cache/code-catalog-rejected.log` に追記 (path:line_no + 該当パターン名 + reason)
- pytest テストで `tokenize` / `passwordless` / `credentialing` 等の安全語が **許容される** ケースを必須化

ファイル本体は走査するが catalog には path + 行番号のみ保存する (本文・後続コードは保存しない)。

### §3.6 メタデータ未付与時の扱い

- 本 PLAN ではメタデータ未付与のコードは catalog 対象外 (空 catalog で start)
- 段階的付与の促進策: `helix code stats --uncovered` で未付与ファイル数を表示 (将来拡張、本 PLAN 段階では `--uncovered` フラグの skeleton のみ)
- 既存 CLI/lib への付与作業は **PLAN-011.1** で別途起票方針 (本 PLAN の派生)

## §4. リスク / 回避

| リスク | 影響度 | 回避策 |
|---|---|---|
| メタデータ未付与のコードが大半 → catalog がほぼ空 | 高 | PoC として規約と仕組み確立を優先。付与は段階 (PLAN-011.1) |
| find の検索精度が低い | 中 | summary 表現の lint (≥ 5 word) を将来追加。現段階は LLM が緩く吸収 |
| catalog 肥大化 | 低 | JSONL は gitignore、DB はローカルキャッシュ。CI では使わない |
| メタデータ規約の自由度が高すぎ揺れる | 中 | id の kebab-case dotted を必須化。lint は次 PLAN |
| skill_catalog との二重メンテ | 中 | frontmatter parser を共通化候補に挙げる (TL レビュー時判断) |
| LLM コスト | 低 | キャッシュ 1 時間 + gpt-5.4-mini で抑制 (skill search と同等) |

## §5. 受入条件

- [ ] `helix code build` で `cli/lib/code_catalog.py` 自身および §2.1 PoC seed (`cli/lib/skill_catalog.py` 主要関数 3-5 個) の `@helix:index` を抽出できる (self-host 確認)
- [ ] `helix code find "frontmatter parser"` で `cli/lib/skill_catalog.py` の seed entry および `cli/lib/code_catalog.py` の関連関数が候補に出る
- [ ] `helix code show <id>` で path + line_no + summary + domain を表示
- [ ] `helix code dup --threshold 0.85` が同 summary を持つ entry を検出
- [ ] `helix code stats --by domain` が domain 別件数を表示
- [ ] `helix code list --domain cli/lib` が cli/lib 配下の entry を一覧
- [ ] **`helix code --help` が `cli/helix` dispatcher 経由で起動する** (P2-a 解消)
- [ ] redaction 動作確認: `auth_token` / `client_secret` / 32 文字 token-like value を含む summary が登録拒否され rejected.log に記録される
- [ ] **redaction 安全語確認** (P3 解消): `tokenize` / `token-based` / `passwordless` / `credentialing` を含む summary は登録される
- [ ] **stale entry prune 確認** (P2-b 解消): seed metadata を一旦削除してから `helix code build` を再実行すると、該当 entry が DB から消える
- [ ] helix-test 全 PASS (shell + pytest 新規 + bats 新規)
- [ ] SKILL_MAP.md に `helix code` 行追加、HELIX_CORE.md「タスク受領」に流用候補確認手順追加

## §6. 関連 PLAN

- **PLAN-002 (HELIX 棚卸し基盤)**: 棚卸し対象の機械可読化に直接寄与。本 PLAN で「コード資産」へ拡張
- **PLAN-005 (運用自動化スキル群)**: 将来 `cli/helix-scheduler` から月次 `helix code stats` 実行可能
- **PLAN-008 (Reverse 多系統)**: R0/R1 Evidence Acquisition で本 catalog を入力 source に追加検討
- **PLAN-010 (検証エージェント)**: `helix verify-agent harvest` の tool source に code catalog を追加検討

## §7. 工程表 (L4)

| Sprint | 内容 | 担当 | 想定時間 |
|---|---|---|---|
| .1a | `cli/lib/code_catalog.py` + メタデータ parser + helix.db v14 migration | Codex SE | 2-3h |
| .1b | `cli/helix-code` CLI + build/list/show 実装 | Codex SE | 2h |
| .2 | find (LLM 推挙 + cache) + dup (Jaccard) + stats 実装 | Codex SE | 2-3h |
| .3 | redaction + rejected.log 実装 | Codex PG | 1h |
| .4 | pytest + bats テスト追加 | Codex QA | 1-2h |
| .5 | SKILL_MAP.md / HELIX_CORE.md / README 追記 | Codex docs | 1h |
| .6 | TL 5 軸レビュー + 修正 | Codex TL + Opus | 1h |

合計: **8-12h** (1-2 セッション、Codex thinking medium 想定)

## §8. 改訂履歴

- v1.2 (2026-05-03): TL review (Sprint .6 1 回目 / 2 回目) findings 解消
  - P0 critical (1 回目): scanner を syntax-aware 化 (Python `tokenize.COMMENT` / bash 純コメント行)、`code_catalog.py` 自身に @helix:index seed 5 件付与
  - P0 critical (2 回目): bats heredoc 内の `# @helix:index` 例も誤抽出していたため、§2.2 / §3.1 で **`.md` と `.bats` を走査対象から除外** に確定
  - P1 high: `rebuild_catalog` で id 重複検出時 `ValueError` で fail-close
  - P2 medium: find cache key に catalog fingerprint (mtime_ns:size) を組み込み、build 後の stale 推挙を回避
  - P2 medium: bats self-host E2E 5 件追加 (self-host build / dup default threshold / stale prune / md+string 除外 / duplicate id fail-close)
- v1.1 (2026-05-02): TL review v1 needs-attention findings (P1×1 / P2×2 / P3×1) 全解消
  - P1: §2.1 に PoC seed metadata 付与 (skill_catalog.py 主要関数 3-5 個) を明記、§5 受入条件で seed と本実装両方を要求
  - P2-a: §2.1 / §3.3 / §5 に `cli/helix` dispatcher の `code)` 追加 + help 更新を明記
  - P2-b: §3.2 で JSONL を正本、DB を派生キャッシュと定義し、build フロー (replace + prune + rollback) を固定。§5 に stale entry prune 確認を追加
  - P3: §3.5 で redaction を danger pattern (複合) と secret-like value detection に分離、`tokenize` / `passwordless` 等の安全語を許容。§5 に安全語確認を追加
- v1 (2026-05-02): 初版起票
