---
doc_id: l8-helix-workflows-dependency-resolution-design
title: "HELIX-workflows V2 L8 依存関係解消設計"
status: draft
owner: TL
type: design_doc
created: 2026-05-27
process_layer: L8
task_type: L8
parent_plan: docs/plans/L8/L8-helix-workflows-依存関係解消plan.md
plan_reference: docs/plans/L8/L8-helix-workflows-依存関係解消plan.md
generates:
  - artifact_path: docs/v2/L8-test-design/helix-workflows-dependency-resolution-design.md
    artifact_type: design_doc
    is_reference: false
implementation_status: planned
updated: 2026-05-27
---

# HELIX-workflows V2 L8 依存関係解消設計（Dependency Resolution Design）

## §0 PLAN reference + scope 宣言

本設計は `docs/plans/L8/L8-helix-workflows-依存関係解消plan.md` による `PLAN-093` 系設計依存を受け、`HELIX-workflows` V2 の dependency graph 不整合を `L8` で検知・分類・解消するための design doc である。

対象は以下。

- 設計対象: `cli/`, `cli/lib/`, `.claude/hooks/`, `.claude/agents/`, `skills/`
- 不整合種別: 循環依存 / 一方向 rule 違反 / stale module / missing dependency / subagent guard 不整合
- 設計成果: `helix doctor check_dependency_direction` を新設し、`helix doctor --summary` と統合する仕様を固定

本 doc は `L5` モジュール分割設計 `docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md` の §12 を機械検証仕様に翻訳し、`docs/v2/L5-internal-design/helix-workflows-internal-processing-design.md` の内部処理方針と整合させる。

## §0.1 受け入れ条件（本 doc 依存）

- 本 doc の §1〜§10 が終了時点で相互に循環する依存の定義と出力形式を満たすこと。
- `helix doctor check_dependency_direction` が 5 sub-check（`check_circular`, `check_one_way`, `check_stale`, `check_missing`, `check_subagent_guard`）を有すること。
- `check_*` 関数名に該当命名（`run_check_*`）が CLI 実装時に一致すること。
- `git status --short docs/v2/L8-test-design/` で本新規 file が存在し、`wc -l` が 800 以上 1400 未満であること。

## §0.2 実行順（PLAN §3 実装順との整合）

1. まず §1〜§4 を実装設計し検知ロジックを固定。
2. 次に §5〜§6 で inventory 生成と除外規則を固定。
3. §7 で doctor check 追加仕様と出力規約を設計。
4. §8 で P0/P1/P2 ロードマップ化。
5. §9 で 4 artifact trace 監査を固定。
6. §10 で実装状態管理（implementation_status）を固定。

## §1 dependency graph 全体方針

### §1.1 解析対象（入出力境界）

**入力**

- `cli/**/*.py`（対象層1）
- `cli/lib/*.py`（対象層2）
- `cli/config/*.yaml`（設定参照）
- `.claude/hooks/*.sh`（対象層3）
- `.claude/agents/*.md`（対象層4）
- `skills/**/*.md`（対象層5）
- `docs/v2/**/*.md`, `docs/plans/**/*.md`, `docs/adr/**/*.md`（対象参照層6）
- `cli/helix-*`, `cli/helix`（Bash entrypoint）

**出力**

- `dependency_nodes`（各 artifact の一意キー）
- `dependency_edges`（source→target）
- `check_*_raw`（各 sub-check の生診断）
- `check_dependency_direction` の集約 payload

**疑似コード**

```pseudo
TARGETS = {
    "cli": "cli/**/*.py, cli/lib/*.py, cli/config/*.yaml, cli/helix-*",
    "hooks": ".claude/hooks/*.sh",
    "agents": ".claude/agents/*.md",
    "skills": "skills/**/*.md"
}

for layer, glob_expr in TARGETS:
    entries = expand(glob_expr)
    for e in entries:
        node = normalize_path(e)
        add_node(node)
        for dep in extract_dependencies(layer, e):
            dep_node = normalize(dep)
            add_edge(node, dep_node)

build_graph(nodes, edges)
```

**境界条件 / 例外処理**

- glob が空 → 空集合として扱い、fail しない。
- 文字列エンコーディング失敗 → `encoding_error` warning。
- `ignore_patterns` 外の一時ファイル（`*.tmp`, `*.swp`, `.pytest_cache`）はスキップ。
- 入力が巨大（10000 ファイル超）になった場合は `collect_window_ms` を分割し、バッチ処理。

**出力**

- 問題無: `pass +0`
- 警告: 解析不能 edge の warning
- 失敗: 正規化不可 path、同時に参照数>10^5 でしきい値超過

### §1.2 graph 表現（Python AST / bash source / yaml ref）

**入力**

- Python: `Import`, `ImportFrom`, `Call`, `ClassDef`（`bases`）
- Bash: `source`, `bash`/`sh` 呼び出し、`python3` 実行、`.helix/` 実行系参照
- YAML/Markdown: `---` frontmatter key, `refs`, `related_docs`, `reference_docs`
- リンク: 正規表現 `\w+://`, `docs/..`, `cli/..`, `.claude/...`

**疑似コード**

```pseudo
function parse_python(path):
    tree = ast.parse(read_text(path))
    edges = []
    for node in walk(tree):
        if type(node) is Import:
            edges += ["import" edge for each alias]
        if type(node) is ImportFrom:
            edges += ["from_import" edge]
        if type(node) is Call:
            edges += ["call" edge for callee]
        if type(node) is ClassDef and node.bases:
            edges += ["inherit" edge for base]
    return edges

function parse_bash(path):
    for line in read_lines(path):
        if match line with /^\s*(source|\.)\s+([^\s#]+):
            edges += source edge
        if match line with /helix\s+([a-z-]+)/:
            edges += hook_exec edge
        if match line with /python3\s+.*?\.(py)/:
            edges += python_edge
        if match line with /\$(.*)/:
            edges += command_substitution edge

function parse_yaml_or_md(path):
    fm = parse_frontmatter(path)
    for k in fm["refs","reference_docs","related_docs","frontmatter"]; if exists:
        edges += metadata edge
    for tokens matching /(\.md|\.yaml|\.yml|\.sh|\.py|.json)/:
        edges += inline edge

```

**境界条件 / 例外処理**

- `ast.parse` 失敗: `SyntaxError` として warning。
- Bash の heredoc / here-string は簡易 tokenizer 不可。`complex_command` として記録。
- Markdown リンクは相対/絶対混在。`path.normalize` で正規化を試み、不能なら `reference_unresolved` warning。

**出力**

- `edge_type` は `import/call/inherit/source/ref/path/metadata/sql` のいずれか。
- edge に `source_line` と `raw_meta` を付与し、トレースを再現可能にする。

### §1.3 出力 format（Mermaid / JSON / textual report）

**入力**

- `dependency_nodes`, `dependency_edges`

**疑似コード**

```pseudo
function render_text_report(graph, findings):
    print_header()
    print_summary(pass, warn, fail)
    print_sections(findings)

function render_json_summary(graph, checks):
    return {
      "version":"L8-1.0",
      "generated_at": now(),
      "graph": {
        "node_count": |nodes|,
        "edge_count": |edges|,
        "layers": {...}
      },
      "checks": checks,
      "policy": {...}
    }

function render_mermaid(graph, checks):
    print("```mermaid")
    print("flowchart TD")
    for n in nodes if n in violations: highlight(n, "red")
    for (u,v,meta) in edges if keep(u,v): print(u, "-->|",meta,"|", v)
    print("```")
```

**境界条件 / 例外処理**

- JSON は 256KB を超える場合、`top_k` で圧縮（`top_n_longest_paths` など）。
- Mermaid は edge 1000 超で折り返しページ化。

**出力**

- テキスト: CI 向けログ
- JSON: machine readability（`--json`/`--summary`）
- Mermaid: 人間理解用図（`--viz` 拡張で有効化）

**出力の最終仕様**

- text summary 行末は必ず `結果: <pass> pass, <warn> warn, <fail> fail` 相当情報を含む。
- section list は `[セクション名]` 形式で 1 行目から 1 回以上。

## §2 循環依存検出

### §2.1 algorithm（DFS / Tarjan SCC）

**入力**

- directed graph G = (V, E)
- `max_depth`, `max_cycle_len`, `ignore_edge_types`（既定: `sql`, `call` の一部を除外可）
- `entry_filter`: `cli/lib` のみ or 全層

**疑似コード（Tarjan）**

```pseudo
index = 0
stack = []
indices = {}
low = {}
onstack = {}
components = []

function strongconnect(v):
    indices[v] = index
    low[v] = index
    index += 1
    push(stack, v); onstack[v] = true

    for w in neighbors(v):
        if w not in indices:
            strongconnect(w)
            low[v] = min(low[v], low[w])
        elif onstack[w]:
            low[v] = min(low[v], indices[w])

    if low[v] == indices[v]:
        comp = set()
        repeat:
            w = pop(stack)
            onstack[w] = false
            comp.add(w)
        until w == v
        components.append(comp)

for v in V:
    if v not in indices:
        strongconnect(v)

for c in components:
    if len(c) >= 2 or has_self_loop(c[0]):
        emit_scc_cycle(c)
```

**DFS 付属検知（最短ループ）**

```pseudo
function detect_short_cycles(v, target, path):
    if len(path) > max_cycle_len: return
    if v == target and len(path) > 1:
        emit_cycle(path)
        return
    for next in neighbors(v):
        if next in path and next != v: continue
        if next in path or next == target:
            detect_short_cycles(next, target, path+[next])
```

**境界条件 / 例外処理**

- self-loop (`A -> A`) は必ず cycle として報告。
- `ignore_edge_types` に `call` を含めると、実行時呼び出し起因の loop を降格し、`caution` として扱う。
- 1,000 ノード超過時は Tarjan を分割実行。

**出力**

- `pass`: SCC size 1 のみ、self-loop 無し。
- `warn`: 1 サイクル検知あり（fail-close で止めるかは P0 判定ルール次第）。
- `fail`: graph reconstruction 不能など致命エラー。

### §2.2 既知 cycle inventory（起票時点）

**入力**

- 本 doc 作成時点の `cli/lib` 一次走査（Python import ベース + AST call edge を含む暫定）
- `python3 cli/lib/code_edges.py` の再利用可能情報
- `rg -n "import .*cli\.lib|from .* import .*" cli/lib/*.py`

**疑似コード**

```pseudo
cycles = []
for each scc in tarjan(graph):
    if len(scc) > 1:
        cycles.append(canonicalize(scc))

for edge in edges:
    if edge.type in {call, inherit, import} and edge.from == edge.to:
        cycles.append([edge.from, edge.to])

sort(cycles, key=len)
limit = 200
emit(cycles[:limit])
```

**実検知結果（本設計時点）**

- `edges` を簡易抽出した暫定結果: SCC 数 0。
- `import/call` 由来で暫定的な確定 cycle は未検出。
- ただし `code_edges.py` の `call` 収集は汎用名（`run_...`, `plan_parser` など）を含むため、誤検知・過小検知余地あり。
- したがって本 doc 起票時点の表現は「暫定 inventory」として扱い、T0 で再走査を義務化。

**出力**

- `check_circular` では暫定 inventory を `inventory_stage=t0` として報告。
- 再実行時の変更比較時に `delta_cycles` を追跡。

### §2.3 解消戦略（依存反転 / 共通 module 抽出）

**入力**

- 検知された cycle candidate list
- `policy`（TDD: まず壊れにくさ、次に可読性）

**疑似コード**

```pseudo
for cycle in cycle_list:
    for each edge in cycle:
        if edge can_be_inverted:
            propose("invert", edge)
        else if edge connects modules with共通目的:
            propose("extract_common", edge)
        else:
            propose("split", edge)
    score = minimize([break_count, touch_count, risk, test_effort])
    rank proposals
```

**境界条件 / 例外処理**

- 壊れやすい API を巻き戻さず互換関数を残す場合は fail-close ではなく warning。
- `cli/lib` の共通 module 抽出時は `__init__` 公開 API 変更時の import 互換を保持。
- cycle 解消が 2 つ以上必要な場合は P0 で再検討。

**出力**

- 各 cycle に `remediation_ticket`, `risk`, `estimated_effort` を付与。
- `check_circular` で `warn` なら P0 list に入れて fail-close。
- 修復対象が `skills` 由来のドキュメント参照なら warn のみ。

## §3 一方向 rule 違反検出

### §3.1 階層定義（cli/ < cli/lib/ < cli/config/）

**入力**

- ノード種別（layer）
  - `cli/*`
  - `cli/lib/*`
  - `cli/config/*`
  - `hooks`, `agents`, `skills`
- 例外定義（hook → cli）

**疑似コード**

```pseudo
function layer(node):
    if node matches "cli/lib/*": return 20
    if node matches "cli/config/*": return 30
    if node matches "cli/*" or node matches "cli/helix*": return 10
    if node matches ".claude/hooks/*": return 5
    return 100

for edge in edges:
    if is_edge(edge.from, edge.to):
        l_from = layer(edge.from)
        l_to = layer(edge.to)
        if l_from > l_to:
            if not is_allowed_reverse(edge):
                record_violation(edge)
```

**境界条件 / 例外処理**

- `l_from == l_to` は許容。
- `hooks -> cli` は allowlist により許可。
- 非解決参照（`to` が外部ライブラリ）も許可。

**出力**

- path 方向逆転を `one_way_violation` として一覧化。
- `check_one_way` は逆方向が 0 なら pass。

### §3.2 `.claude/hooks/` → `cli/lib/` via helix CLI call（直接 import 禁止）

**入力**

- hook files の `source`, `python3`, `helix`, `jq`, `rg` 呼び出し行
- `python` 実行での import path 指定（文字列）

**疑似コード**

```pseudo
ALLOWED = {"hooks_to_cli": true, "hooks_to_lib_via_helix": true}

for h in hooks:
    for edge in extract_bash_edges(h):
        if edge.kind == "source":
            continue
        if edge.target matches "cli/lib/*" and edge.origin == "call":
            if edge.command == "helix":
                allow
            else:
                violation("direct_import_or_call", edge)
```

**境界条件 / 例外処理**

- `sh -c "...` のコマンド文字列は safe parse 失敗するため `shell_parse_degraded` warning。
- `path` が相対で `../cli/lib` を参照する場合は正規化。

**出力**

- hook からの `cli/lib` へのアクセスは、`helix cli` 以外をすべて violation。
- 一部許容する場合は例外 YAML で `exception_reason` を残す。

### §3.3 違反 inventory

**入力**

- `check_one_way` 実行時に検知した violation list

**疑似コード**

```pseudo
violations = []
for v in scan_results:
    record = {
      "from": v.from,
      "to": v.to,
      "reason": v.reason,
      "evidence_line": v.lineno,
      "edge_type": v.kind
    }
    violations.append(record)

sort(violations, key=(severity, from, to))
```

**暫定 inventory（起票時）**

- `cli/lib -> cli` の違反: 一次走査で該当 0 件（暫定）。
- `hooks -> cli/lib` の direct import: 検知不可だが、既知の警告パターンは `pretool` 系と `session` 系 hook の一部の呼び出し。
- `missing parse`（bash 複合コマンド）で warning あり。

**出力**

- `check_one_way` は `warn` で violations 一覧を返却。
- `fail-close` 条件は「critical violation 件数>0」のみ。

## §4 stale module 検出

### §4.1 import 元 0 件の module

**入力**

- `nodes = cli/lib/*.py`
- `dependency_edges`（import/call/inherit）

**疑似コード**

```pseudo
indegree = defaultdict(int)
for e in edges:
    if e.to in nodes and is_internal(e.to):
        indegree[e.to] += 1

stale = [n for n in nodes if indegree[n] == 0]
for n in stale:
    if n in allowlist:
        stale.pop(n)
```

**境界条件 / 例外処理**

- `__init__`/`main`/`cli` 起点のみ別扱い（`entry_only`）。
- import ではなく entrypoint call でのみ参照される module は暫定 stale から除外し、要レビュー。
- `--legacy` のみ対象外。

**出力**

- `check_stale` は `stale_count` と `stale_candidates` を返す。
- 0 件 -> pass。
- 1 件以上 -> warn。

### §4.2 削除 candidate vs 廃止候補（DEPRECATED marker）

**入力**

- stale list と `TODO`/`DEPRECATED` マーカー
- file name pattern `deprecated_*.py`、frontmatter `deprecated: true`

**疑似コード**

```pseudo
for m in stale:
    fm = read_frontmatter(m)
    text = read_text(m)
    has_marker = "DEPRECATED" in text or fm.get("deprecated") is True
    if has_marker:
        classify(m, "deletion_candidate")
    else:
        classify(m, "investigation_needed")
```

**境界条件 / 例外処理**

- 廃止 candidate は `stale > 30 days` にも満たす場合のみ強制化。
- `unit test / lint` が参照している場合は除外。

**出力**

- `stale_modules.deprecated` / `stale_modules.investigation` の 2 区分。
- 廃止確定は P1 に carry。

### §4.3 ⚠️ subagent 禁止 7 種の扱い

**入力**

- `.claude/agents/*.md`
- `pretooluse-agent-guard.sh` 許可/禁止リスト
- `L5` §7.3 「禁止 7 種」の設計方針

**疑似コード**

```pseudo
FORBIDDEN = {be-api, be-logic, db-schema, qa-test, security-audit, code-reviewer, devops-deploy}
for subagent in agents:
    if name in FORBIDDEN:
        if target_context in {implementation, review}:
            require_gate_or_replacement(subagent)
```

**境界条件 / 例外処理**

- 7 種を `model` override で起動する運用は原則禁止。
- PMO/PM 用の `pmo-*` 系に再起動を誘導。

**出力**

- stale list の中に禁止7種の実装痕跡（frontmatter/model mismatch）があれば warn。
- 実装依存を直接持つ module は P0 評価へ昇格。

## §5 missing dependency 検出

### §5.1 PLAN.generates で宣言された artifact が実 file 不在

**入力**

- PLAN registry: `plan_generates(plan_id, artifact_path, artifact_type)`
- ファイル実体: リポジトリの実ファイル
- 参照ベース: plan frontmatter と `docs/plans/*`

**疑似コード**

```pseudo
for row in plan_generates:
    path = resolve_repo(row.artifact_path)
    if not exists(path):
        emit_missing(row.plan_id, row.artifact_path, reason="missing_artifact")
    else if path is dir and row.artifact_type == "artifact_file":
        emit_missing(row.plan_id, row.artifact_path, reason="unexpected_dir")
```

**境界条件 / 例外処理**

- `.yaml` と `.yml` を同一 artifact と見なすルールはない。
- `plan_generates` の row が壊れている場合は warning。
- reference plan (`is_reference`) は check から除外。

**出力**

- `check_missing` は `missing artifact` リストを返す。
- 件数 0: pass。

### §5.2 helix doctor check_plan_drift との整合

**入力**

- `cli/lib/doctor_plan_checks.py` の `run_check_plan_drift`
- `doc/frontmatter` の `is_reference`

**疑似コード**

```pseudo
check_plan_drift_rows = run_check_plan_drift()
check_missing_rows = check_missing()
assert keys in check_plan_drift_rows intersect check_missing_rows
for row in check_missing_rows:
    if row.plan_id in check_plan_drift_rows and row.status == "warning":
         row.source = "cross_check"
```

**境界条件 / 例外処理**

- `check_plan_drift` が table 欠如で warning を返した場合は `check_missing` 実行を強制しない。

**出力**

- `check_missing` と `check_plan_drift` の差分を `diff_map` で保持。
- 併存で同一 artifact が `missing` の場合 `warning` カウントを加算。

## §6 subagent ↔ Agent tool guard hook 整合

### §6.1 `.claude/agents/<X>.md` frontmatter `model` vs guard allow list

**入力**

- `subagent_type`（tool_input）
- `.claude/agents/${subagent_type}.md`
- guard script の `ALLOW_LIST`

**疑似コード**

```pseudo
ALLOW_LIST = {
  "pmo-sonnet","pmo-haiku","pmo-helix-explorer","pmo-helix-scout",
  "pmo-project-explorer","pmo-project-scout","pmo-tech-docs",
  "pmo-tech-fork","pmo-tech-news","pdm-tech-innovation",
  "pdm-marketing-innovation","pdm-innovation-manager"
}

for call in agent_calls:
    if call.subagent_type not in ALLOW_LIST: violation("type_not_allowed")
    fm_model = parse_model(f".claude/agents/{call.subagent_type}.md")
    fm_family = normalize_family(fm_model)
    req_family = normalize_family(call.model)
    if call.model is not empty and req_family != fm_family: violation("model_override")
```

**境界条件 / 例外処理**

- frontmatter ファイルが存在しない、または model 未定義は fail-close。
- `model` が `haiku/sonnet/opus` 以外は fail-close。
- `effort` 欠損は warn（既存 hook 仕様）。

**出力**

- `check_subagent_guard` で `forbidden_type`, `missing_definition`, `model_mismatch` を明示。

### §6.2 違反検出（Sonnet/Opus override block）

**入力**

- `subagent_type`, `model`
- frontmatter model family

**疑似コード**

```pseudo
if call.model and normalize_family(call.model) != normalize_family(frontmatter_model):
    emit("model_override_block")
if call.subagent_type in FORBIDDEN_7:
    emit("forbidden_subagent_type")
if call.subagent_type == "":
    emit("missing_type")
```

**境界条件 / 例外処理**

- `HELIX_ALLOW_RAW_AGENT=1` が付与された場合は一時的に警告で通過し、evidence を保存必須。

**出力**

- `check_subagent_guard` は `warn_count` と `block_count` を別管理。
- ブロック件数>0なら fail-close。

## §7 helix doctor check_dependency_direction 新設

### §7.1 sub-check 構成

**入力**

- `graph_report`（セクション 1 で構築）
- 運用フラグ: `--target`, `--strict`, `--skip`, `--json`, `--summary`

**疑似コード**

```pseudo
SUBCHECKS = [
    "check_circular",
    "check_one_way",
    "check_stale",
    "check_missing",
    "check_subagent_guard",
]

results = []
for name in SUBCHECKS:
    status, payload = run_subcheck(name)
    results.append({"name": name, "status": status, "payload": payload})
```

**境界条件 / 例外処理**

- 1 sub-check の fail は全体 fail-close。
- warn は総合 warn に加算。
- 例外が発生した sub-check は `error` 状態を返し、fail-close。

**出力**

- `check_dependency_direction` は section 単位で `status(pass|warn|fail)` を返す。
- text 出力は `△`, `✓`, `✗` で始まる。

### §7.2 exit code（0 pass / 1 warn / 2 fail-close）

**入力**

- `warn_count`, `fail_count`。
- `strict_fail_close`。

**疑似コード**

```pseudo
if fail_count > 0: exit 2
if warn_count > 0: exit 1
return 0
```

**例外ルール**

- `summary` 解析不能でも doctor text 解析で `fail=1`。
- `--json` 変換不可能時は fail で終了。

**出力**

- exit 0: passのみ
- exit 1: warningあり
- exit 2: fail-closeあり（`--strict` かどうかにかかわらず停止）

### §7.3 fail-close vs advisory 判定基準

**入力**

- 違反 severity map:
  - `critical` -> fail-close
  - `high` -> fail-close
  - `medium` -> warn
  - `low` -> warn

**疑似コード**

```pseudo
CRITICAL = {
  "check_one_way": "critical",
  "check_subagent_guard": "critical",
  "check_circular": "high",
  "check_missing": "medium",
  "check_stale": "low",
}

def classify(row):
    return CRITICAL.get(row.check_name, "low")

total_fail = count(sev in {critical,high} and row.action=="block")
total_warn = count(sev in {medium,low} and row.action=="warn")
```

**境界条件 / 例外処理**

- P0 issue は同一 run 内で fail-close 優先。
- advisory mode (`--advisory-only`) の場合は critical も warning ダウンレンジ可。

**出力**

- `check_dependency_direction` は fail-close の分類レベルを JSON に含める。

### §7.4 helix doctor --summary 統合

**入力**

- `helix-doctor` の既存 `check_plan_advisory` 互換形式
- `doctor_summary.py` の parser

**疑似コード**

```pseudo
function integrate_doctor_output(stdout_text):
    payload = doctor_summary.parse_doctor_output(stdout_text)
    dep = run_check_dependency_direction(payload_raw=True)
    payload.sections.append({
       "name": "dependency_direction",
       "status": dep.overall_status,
       "count": dep.problem_count,
    })
    print(json.dumps(payload))
```

**境界条件 / 例外処理**

- 既存 section パースに互換：`[セクション]` + `✓/△/✗` を必須。
- `--summary` 時は text parse を再利用。

**出力**

- `helix doctor --summary` では `dependency_direction` section が追加される。
- pass/warn/fail の累積は既存 `結果:` 行に加算される。

## §7.5 新規 helper 命名規約（既存 doctor パターン準拠）

**入力**

- 現行 doctor 命名規約: `run_check_<snake>`

**疑似コード**

```pseudo
file = cli/lib/doctor_dependency_direction.py
for sub in [circular,one_way,stale,missing,subagent_guard]:
    export "run_check_" + sub_name
```

**出力**

- 追加ファイル名: `doctor_dependency_direction.py`
- 呼び出し名: `run_check_dependency_direction`
- 既存 `check_plan_*` と同一 pattern。

## §8 不整合解消ロードマップ

### §8.1 P0（即修正）: 循環依存 / 一方向 rule 違反

**入力**

- `check_circular` の cycle list
- `check_one_way` の critical 違反

**疑似コード**

```pseudo
if check_circular.fail_count > 0: queue_high("C0")
if check_one_way.fail_count > 0: queue_high("C1")
while queues:
    run_fix(ticket)
    rerun_checks()
    assert fail_count decreases
```

**境界条件 / 例外処理**

- P0 は 1 ループごとに再検証。
- CI ブロック前にローカル再現を要求。

**出力**

- P0 完了時に `implementation_status` を `implemented` に更新。

### §8.2 P1（carry）: stale module の削除

**入力**

- stale candidate list と DEPRECATED 判定

**疑似コード**

```pseudo
for m in stale_investigation:
    if m.marker == "DEPRECATED": propose_delete(m)
    elif last_modified_days(m) > 90: propose_archive(m)
```

**出力**

- `implemented` できなかった場合は `carry` へ移行。

### §8.3 P2（任意）: subagent 禁止 7 種の整理

**入力**

- `.claude/agents` frontmatter と実呼び出し実績

**疑似コード**

```pseudo
for a in forbidden_types:
    if observed_calls(a) > 0:
        require_alternative_routing(a)
```

**出力**

- P2 は品質改善に該当、MVP では fail-close 対象外。

## §9 4 artifact 双方向 trace

### §9.1 参照ルール

**入力**

- PLAN, L5 internal design, ADR, L8 design

**疑似コード**

```pseudo
TRACE = [
  ("PLAN", "L5_internal_design", "L4_architecture", "ADR"),
  ("ADR", "PLAN", "L5_internal_design", "hooks/agents/skills"),
]
for (a,b,c,d) in TRACE:
  assert has_reference(a,b)
  assert has_reference(b,c)
  assert has_reference(c,d)
```

**出力**

- 欠落は `trace_incomplete` として warn。

### §9.2 設計トレース・検出仕様（機械化）

**入力**

- frontmatter `pairs_design`, `pairs_test_design`, `reference_docs`

**疑似コード**

```pseudo
for doc in docs:
    if doc.type == "design":
      require(doc.pairs_design in ["docs/v2/L9-test-design/...", ...])
    if doc.reference_docs is empty:
      warning("trace_gap")
```

**出力**

- 4 artifact trace は PASS 基準を持つ。欠落すると `check_vmodel_pair_freeze` 相当の gating 対象。

### §9.3 依存不整合と trace の関係

**入力**

- §2,§3,§4,§5,§6 の各結果
- `helix doctor --summary`

**疑似コード**

```pseudo
for section in dependency_sections:
    link_to_trace(section)
    if section.status == fail:
       mark_trace_block(section)
```

**出力**

- 追跡可能性を持つため、違反一件ごとに `artifact_triplet` を保持。

## §10 implementation_status 表

### §10.1 対象別実装計画

**入力**

- 設計フェーズの節別完了時点

| 対象 | planned | partial | implemented |
|---|---:|---:|---:|
| L8 dependency graph core | 1 | 0 | 0 |
| check_circular | 1 | 0 | 0 |
| check_one_way | 1 | 0 | 0 |
| check_stale | 1 | 0 | 0 |
| check_missing | 1 | 0 | 0 |
| check_subagent_guard | 1 | 0 | 0 |
| doctor check wiring | 1 | 0 | 0 |
| --summary schema | 1 | 0 | 0 |
| inventory snapshots | 1 | 0 | 0 |
| P0 remediation list | 1 | 0 | 0 |
| P1/P2 carry | 1 | 0 | 0 |

### §10.2 status 推移ルール

**入力**

- 各節のレビュー結果

**疑似コード**

```pseudo
if section.passes_review and no_warn:
    status = "implemented"
elif section.passes_review and has_warn:
    status = "partial"
else:
    status = "planned"
```

**境界条件 / 例外**

- P0 fail が残る場合は該当節が実装完了扱い不可。

**出力**

- `implementation_status` が `planned`/`partial`/`implemented` のいずれかで固定。

## §10.3 監査観点での証跡

**入力**

- `helix doctor --summary`
- `check_dependency_direction` 実行ログ

**疑似コード**

```pseudo
for item in audit_queue:
    write_audit(item)
    update_trace(item.section, item.status)
```

**出力**

- section ごとの audit を `.helix/audit` と `implementation_status` で相互参照。

## §10.4 差分比較（本 doc と L5 準拠）

**入力**

- `docs/v2/L5-internal-design/helix-workflows-module-decomposition-design.md` の §12
- `docs/plans/L8/L8-helix-workflows-依存関係解消plan.md` の §2.1

**疑似コード**

```pseudo
assert l8_doc.includes("check_circular")
assert l8_doc.includes("check_one_way")
assert l8_doc.includes("check_stale")
assert l8_doc.includes("check_missing")
assert l8_doc.includes("check_subagent_guard")
```

**出力**

- 乖離なし。

## §11 運用ガイド（実行・再現手順）

### §11.1 再現手順（最小）

**入力**

- チェック対象リポジトリ

**疑似コード**

```bash
# 依存関係抽出
rg -n "check_[a-z_]+" cli/lib/doctor_*.py | head -30

# 実行
helix doctor
helix doctor --summary
helix doctor check_dependency_direction
helix doctor check_dependency_direction --json > /tmp/dependency-check.json
```

**出力**

- 実行結果が `exit` code で即時判定可能。

### §11.2 運用フラグ一覧

- `--json`: parse 前提
- `--summary`: section 集約前提
- `--target cli`: CLI 層限定
- `--fail-on-cycle`: fail-close を厳格にする
- `--advisory-only`: warn 降格

### §11.3 ルール更新手順

**入力**

- 追加禁止/許可

**疑似コード**

```pseudo
if policy changed:
    bump doctype_version
    add_test_vector(
       name="policy_diff_YYYYMMDD",
       before=old_rule,
       after=new_rule
    )
```

**出力**

- policy change と実装変更を同時に追跡。

## §12 追加検証観点（quality gate）

### §12.1 テスト/監査観点

**入力**

- `check_dependency_direction` の 5 sub-check
- 既存 `doctor_plan_checks` との差分

**疑似コード**

```pseudo
for check in ["check_circular","check_one_way","check_stale","check_missing","check_subagent_guard"]:
   run_unit_test(check)
   run_property_test(check)
   assert parseable_exit_code(check)
```

**出力**

- 品質ゲート: 問題 0 件。

### §12.2 性能観点

**入力**

- ファイル数、edge 数
- メモリ上限

**疑似コード**

```pseudo
start = now()
run_dependency_build()
elapsed = now()-start
assert elapsed_ms < 30000
assert memory_usage < 1024MB
```

**出力**

- 既定: 30 秒以内に `pass`。

### §12.3 リスク観点

- false positive の上限: 1% 未満
- true positive の回収率: 90% 以上（MVP）
- 欠損依存の見落とし: 30日間で監査レビュー

### §12.4 監査エスカレーション（失敗時）

**入力**

- exit code 2
- warning が 100 件超

**疑似コード**

```pseudo
if exit_code == 2:
    create_hotfix_blocker_issue()
elif warn_count > 100:
    create_tech_debt_issue()
```

**出力**

- `blocked` な場合は helix handover の `stale` 解除手順に連携。

## §13 附録A: 代表的な疑似入力/出力

### §13.1 check_one_way 入出力例

**入力**

- `edge: cli/lib/a.py -> cli/b.py`

**出力（warn）**

```json
{
  "check": "check_one_way",
  "status": "warn",
  "severity": "critical",
  "items": [
    {"from":"cli/lib/task_dispatcher.py","to":"cli/helix" ,"kind":"layer_violation"}
  ]
}
```

### §13.2 check_circular 入力（cycle found）

```json
{
  "check": "check_circular",
  "status": "warn",
  "severity": "high",
  "cycle": ["cli/lib/x.py","cli/lib/y.py","cli/lib/z.py","cli/lib/x.py"]
}
```

### §13.3 check_missing 入力

```json
{
  "check": "check_missing",
  "status": "warn",
  "severity": "low",
  "missing": [{"plan_id":"PLAN-093","artifact":"docs/v2/L8-test-design/none.md"}]
}
```

### §13.4 check_subagent_guard 入力

```json
{
  "check": "check_subagent_guard",
  "status": "fail",
  "items": [
    {"subagent_type":"be-api","model":"claude-opus-4-7","error":"forbidden_type"}
  ]
}
```

## §14 附録B: コマンドリファレンス

### §14.1 利用コマンド

- `helix doctor`
- `helix doctor --summary`
- `helix doctor check_dependency_direction`
- `helix doctor check_dependency_direction --target cli`
- `helix doctor check_dependency_direction --json`
- `helix doctor check_dependency_direction --strict`
- `helix doctor check_dependency_direction --advisory-only`

### §14.2 生成ログ（想定）

**入力**

- 上記コマンドの text 出力

**出力**

- `pass`, `warn`, `fail` が 1 行 summary に集計。

## §15 結論

本設計は、`HELIX-workflows` V2 L8 で必要となる dependency 不整合検知の原則を、機械判定可能な 5 sub-check 仕様として固定した。`check_dependency_direction` は既存 doctor 命名規約（`run_check_*`）と `helix doctor --summary` を前提にし、L5/ADR/L8 設計の一貫性を保つ。

最終的な採用目標:
- 循環依存 / 一方向違反: P0 で即修正。
- stale / missing: carry として透明化。
- subagent guard 整合: 既存 hook と完全整合。
- 結果は exit code 0/1/2 で明確化。
