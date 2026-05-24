---
plan_id: L7-route-engine-drift-type-retrofit-ext
name: L7-route-engine-drift-type-retrofit-ext
description: route_engine.py 拡張 — drift_type 7 種細分化 + Retrofit mode 追加 + suggest subcommand + recommended_command field
status: draft
process_layer: L7
kind: impl
drive: be
size: M
priority: P0
generates:
  - artifact_path: docs/v2/L7-design/L7-route-engine-drift-type-retrofit-ext-design.md
    artifact_type: design_doc
  - artifact_path: docs/v2/L7-test-design/L7-route-engine-drift-type-retrofit-ext-test-design.md
    artifact_type: design_doc
  - artifact_path: cli/lib/route_engine.py
    artifact_type: python_module
  - artifact_path: cli/helix-route
    artifact_type: cli_extension
  - artifact_path: cli/lib/tests/test_route_engine.py
    artifact_type: test
  - artifact_path: cli/tests/helix-route.bats
    artifact_type: test
dependencies:
  parent: L7-helix-workflows-parent-acceptedplan
  requires:
    - L7-helix-route-implplan
  blocks:
    - L7-cli-helix-refactor-implplan
  # L7-cli-helix-retrofit-implplan は self-contained 化済 (PLAN C R3 で hard dep 削除)、C8 carry で route integration E2E は次 wave で接続
parent_design: HELIX-workflows/helix-process/detection-routing.md
parent_design_addenda:
  - docs/adr/ADR-043-mode-enum-extension-retrofit-freeze-break-decision.md
pairs_test_design: []
agent_slots:
  - role: tl-advisor
    slot_label: "TL — R1 設計 adversarial check (drift_type 分岐表 / suggest subcommand 契約 / backward compat)"
  - role: se
    slot_label: "SE — route_engine.py 拡張 + suggest subcommand + test 実装"
  - role: pmo-sonnet
    slot_label: "PMO — 4 artifact 双方向 trace 確認・PLAN B/C との drift_type 統一確認"
created: 2026-05-24
revised: 2026-05-24-R2
owner: PM
is_reference: false
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **正本設計**: [HELIX-workflows/helix-process/detection-routing.md](../../../HELIX-workflows/helix-process/detection-routing.md)
> **前提 PLAN**: [L7-helix-route-implplan.md](./L7-helix-route-implplan.md) (実装済 `helix route eval / list-signals` の上に拡張)
> **後続 PLAN (本 PLAN が blocks)**: L7-cli-helix-refactor-implplan / L7-cli-helix-retrofit-implplan

### 背景と切り出し経緯

PLAN C (L7-cli-helix-retrofit-impl) の tl-advisor R1 で P0-1 指摘:

> route → retrofit 接続契約が現行実装と不整合。`route_engine.py` は Retrofit mode 未追加、drift signal の細分化 (drift_type) 未対応、suggest subcommand 未実装、recommended_command field 未実装。

PLAN C 本体は scope を「retrofit CLI state manager のみ」に限定して revision され、route_engine 拡張を本 PLAN (C') として切り出す。本 PLAN は **PLAN B (helix-refactor) および PLAN C (helix-retrofit) の前提依存 (blocks)** であり、両 PLAN が参照する drift_type 分岐表・suggest subcommand 契約を確立する。

### 解決する 5 課題 (tl-advisor R1 P0-1 + PLAN B P1-1)

| # | 現行の問題 | 本 PLAN の解決 |
|---|---|---|
| 1 | `Mode` が `Reverse\|Refactor\|Recovery\|Incident` のみ | `Retrofit` 追加 |
| 2 | `drift` signal が `Reverse/normalization` 固定 | drift_type 7 種で分岐先を変える |
| 3 | drift_type 数が PLAN 間で不統一 (6 種 vs 7 種) | 7 種で正式確定 |
| 4 | `suggest` subcommand 未実装 | `helix route suggest` 追加 |
| 5 | `recommended_command` field 未実装 | `RouteResult` に field 追加 |

### 本 PLAN の scope 外 (別 PLAN 担当)

- Refactor CLI 本体実装 → L7-cli-helix-refactor-implplan
- Retrofit CLI state manager 実装 → L7-cli-helix-retrofit-implplan
- cross-detection / dashboard schema adapter → 既存 `from_detect_output` 範囲維持

---

## §1 工程表

| Sprint | 内容 | 担当 | 受入条件 | 状態 |
|--------|------|------|----------|------|
| .0 | Entry 条件確認 + 既存資産 Read + 設計判断確定 | PM + TL | §2 全項目承認、drift_type 分岐表 PLAN B/C と照合一致 | pending |
| .1 | テスト設計 (test-design doc 起草) + failing tests 作成 (TDD) | SE | test-design doc 生成、pytest で全 failing 確認 | pending |
| .2 | route_engine.py 拡張実装 (Mode / drift_type / recommend / suggest) | SE | py_compile PASS、既存テスト全 PASS | pending |
| .3 | suggest subcommand 実装 (helix-route CLI 拡張) | SE | bats 新規テスト PASS、backward compat 確認 | pending |
| .4 | 全テスト通過確認 + 設計 doc 生成 | SE | pytest ALL PASS、bats ALL PASS | pending |
| .5 | セルフレビュー + pmo-sonnet review + DoD 確認 | SE + PMO | DoD 全項目 checked | pending |

**Entry 条件**:
- L7-helix-route-implplan の Sprint .1-.5 完遂済み (route_engine.py 実装済)
- PLAN B/C の drift_type 分岐表確認済み

**Exit 条件 (DoD)**:
- §5 DoD 全項目 checked
- py_compile PASS
- pytest (test_route_engine.py 拡張分) ALL PASS
- bats (helix-route.bats 拡張分) ALL PASS
- 既存テスト回帰なし
- drift_type 分岐表が PLAN B/C/C' で完全一致

---

## §2 設計判断

### §2.1 Mode enum 拡張

**現行**:
```python
Mode = Literal["Reverse", "Refactor", "Recovery", "Incident"]
Kind = Literal["reverse", "refactor", "recovery", "troubleshoot"]
```

**拡張後**:
```python
Mode = Literal["Reverse", "Refactor", "Recovery", "Incident", "Retrofit"]
Kind = Literal["reverse", "refactor", "recovery", "troubleshoot", "retrofit"]
```

**設計判断**: Retrofit は独立 mode として追加する。既存 4 mode の kind mapping には影響しない。

**backward compat**: `Mode` は Literal 型 (型ヒント用途)。実行時ロジックは SIGNAL_TO_MODE dict が source of truth であり、既存 signal の mode 値は変更しない。新 signal (`dependency_outdated` / `upgrade` / `config_drift`) のみ `Retrofit` を返す。

---

### §2.2 drift_type 7 種細分化 + 分岐表

#### drift_type 正式定義 (7 種、PLAN B/C/C' 統一)

| drift_type | 意味 | 分岐先 mode | kind | subtype |
|---|---|---|---|---|
| `schema` | DB/API スキーマ乖離 | Reverse | reverse | normalization |
| `contract` | API 契約・型定義乖離 | Reverse | reverse | normalization |
| `code_smell` | コード品質劣化・技術的負債 | Refactor | refactor | null |
| `structural` | 構造・アーキテクチャ乖離 | Refactor | refactor | null |
| `dependency_outdated` | 依存ライブラリ陳腐化 | Retrofit | retrofit | dependency |
| `upgrade` | バージョンアップ必要 | Retrofit | retrofit | upgrade |
| `config_drift` | 設定値・環境設定乖離 | Retrofit | retrofit | config |

#### drift signal の拡張マッピング

現行の `drift` signal は `Reverse/normalization` 固定。拡張後は `drift_type` で細分化:

```
drift (signal)
├─ drift_type=schema      → Reverse / normalization
├─ drift_type=contract    → Reverse / normalization
├─ drift_type=code_smell  → Refactor / null
├─ drift_type=structural  → Refactor / null
├─ drift_type=dependency_outdated → Retrofit / dependency
├─ drift_type=upgrade     → Retrofit / upgrade
└─ drift_type=config_drift → Retrofit / config
```

**drift_type 未指定時のデフォルト**: `schema` (既存 `Reverse/normalization` を維持、backward compat)

#### 新 signal 追加 (drift_type shortcut)

drift_type shortcut として以下 3 シグナルを新規追加する:

| signal | drift_type | mode | kind | subtype |
|---|---|---|---|---|
| `dependency_outdated` | dependency_outdated | Retrofit | retrofit | dependency |
| `upgrade` | upgrade | Retrofit | retrofit | upgrade |
| `config_drift` | config_drift | Retrofit | retrofit | config |

**設計判断**: shortcut signal は `drift` + `drift_type=X` の等価表現。detector が直接 shortcut signal を送ることができる (cross-detection output との互換性確保)。

---

### §2.3 suggest subcommand 設計

#### コマンド仕様

```
helix route suggest --signal <signal> [--drift-type <drift_type>]
                    [--uncertainty low|high] [--impact low|high]
                    [--env dev|prod]
```

**出力** (P1-5 反映、ADR-042 役割分離):
- デフォルト出力 (`--format command` 相当): `suggest_command` (人間向け 1 行文字列) を stdout 出力
- `--format json`: RouteResult 全体 (`suggest_command` + `recommended_command` JSON object additive) を JSON 出力 (ADR-042 §--format json additive)
- `recommended_command` は **必ず JSON object** (機械契約)、stdout に 1 行 string 出力は不可

#### route → mode 接続コマンド契約 (ADR-042 §Decision SoT)

> **ADR-042 §backward compat 固定表** が正本。本 PLAN は SoT 参照のみ行い、独自定義しない。

| mode | recommended_command (JSON object 形式) |
|---|---|
| Recovery (runaway/regression_dev) | `{"command": "helix recover plan", "args": {"signal_id": "{signal}", "reopen_point": "{reopen_point}", "auto_routed_from": "helix-route"}}` ★ ADR-042 Recovery 例外 |
| Incident (prod) | `{"command": "helix recover plan", "args": {"signal_id": "{signal}", "reopen_point": "{reopen_point}", "auto_routed_from": "helix-route"}}` ★ ADR-042 Recovery 例外 |
| Reverse | `{"command": "helix reverse normalization R0", "args": {}}` (`helix reverse <type> <stage>` 形式、ADR-042 固定) |
| Refactor | `{"command": "helix plan draft", "args": {"kind": "refactor"}}` |
| Retrofit | `{"command": "helix plan draft", "args": {"kind": "retrofit", "drift_type": "{drift_type}"}}` |

> **注意**: Reverse コマンド形式は `helix reverse <type> <stage>` (cli/helix-reverse の usage に準拠)。  
> `helix reverse R0 --type normalization` は誤り、ADR-042 §backward compat 固定表と不一致のため使用禁止。  
> Recovery は `helix recover plan --signal-id <signal>` を使用 (ADR-042 Recovery 例外、`helix plan draft` とは異なる)。

**既存 `suggest_command` field との関係**:
- `suggest_command` (既存): `helix route eval --format command` で出力される文字列。backward compat 維持 (string 形式)。
- `recommended_command` (新規): **JSON object 形式** (ADR-042 で string 廃止・JSON object 一本化確定)。`helix route suggest` 専用出力。
- `suggest_command` は deprecated 候補だが backward compat のため共存維持。機械処理には `recommended_command` (JSON object) を使用する。

#### suggest vs eval の使い分け

| コマンド | 用途 | 出力 |
|---|---|---|
| `helix route eval` | 全 RouteResult 情報 (JSON) または suggest_command 1 行 | JSON / 1 行コマンド |
| `helix route suggest` | `suggest_command` (人間向け 1 行 string) を stdout 出力、`--format json` で `recommended_command` JSON 含む RouteResult 全体 (ADR-042 役割分離: recommended_command は機械 JSON、suggest_command は人間表示) | 1 行 string (デフォルト) または JSON |

---

### §2.4 recommended_command field 設計

#### RouteResult 拡張

```python
@dataclass(frozen=True, slots=True)
class RouteResult:
    # 既存 fields (変更なし)
    signal: str
    mode: Mode
    kind: Kind
    subtype: str | None
    priority: Priority
    action: Action
    env: Env
    source_schema: str
    suggest_command: str             # 既存 (backward compat 維持、string 形式)
    recover_args: dict[str, str] | None
    plan_hint: str
    # 新規追加 fields
    drift_type: str | None           # drift signal 細分化。shortcut signal は自動付与、drift 以外の signal は None
    recommended_command: dict[str, Any]  # JSON object 形式 (ADR-042 string 廃止・JSON object 一本化)
```

> **ADR-042 §Decision**: `recommended_command` は JSON object 一本化 (string 形式は廃止)。  
> `suggest_command` (string) は backward compat のため共存維持するが、機械処理には `recommended_command` (dict) を使用。

**backward compat**:
- `to_dict()` は `asdict()` で自動追加される。既存呼び出し元が JSON を parse する場合、新 field は追加情報として無視される (破壊的変更なし)。
- `drift_type=None` はデフォルト値で、`drift` signal 以外の signal (shortcut signal 含む) には自動付与ロジックで値が設定される (P0-1 修正、下記 `_resolve_drift_type()` 参照)。
- `recommended_command` は dict 型。`suggest_command` (string) は既存値を維持。

#### drift_type の伝播経路

```
helix-detect 出力 (detect_run.json)
  └─ result.drift_type (optional field)
       └─ RouteEngine.from_detect_output()
            └─ RouteResult.drift_type
                 └─ recommended_command に --drift-type {drift_type} 付与 (Retrofit 時)
```

`from_detect_output()` 拡張: `result.drift_type` を読み取り、`evaluate()` に `drift_type` を渡す。

---

## §3 影響範囲 inventory

### §3.1 変更対象ファイル

| ファイル | 変更種別 | 変更内容 |
|---|---|---|
| `cli/lib/route_engine.py` | extend | Mode/Kind Literal 拡張、SIGNAL_TO_MODE 3 signal 追加、RouteResult 2 field 追加、evaluate() drift_type 引数追加、_build_suggest_command() Retrofit 分岐追加、from_detect_output() drift_type 抽出追加 |
| `cli/helix-route` | extend | `suggest` subcommand 追加 (argparse)、`list-signals` に drift_type 情報追加 |
| `cli/lib/tests/test_route_engine.py` | extend | Retrofit mode / drift_type / recommend / suggest 対応テスト追加 |
| `cli/tests/helix-route.bats` | extend | `suggest` subcommand bats テスト追加 |

### §3.2 新規生成ファイル

| ファイル | 内容 |
|---|---|
| `docs/v2/L7-design/L7-route-engine-drift-type-retrofit-ext-design.md` | 設計 doc (§2 設計判断の永続化) |
| `docs/v2/L7-test-design/L7-route-engine-drift-type-retrofit-ext-test-design.md` | テスト設計 doc (Sprint .1 で生成) |

### §3.3 既存呼び出し元 (backward compat 確認対象)

```bash
# 既存呼び出し元を確認
grep -rn "route_engine\|helix-route\|helix route" /home/tenni/ai-dev-kit-vscode/cli/ \
  --include="*.py" --include="*.bats" --include="*.bash" \
  | grep -v "__pycache__" | grep -v ".pyc" | head -30
```

確認済み呼び出し元:
- `cli/lib/tests/test_route_engine.py` — テストコード、本 PLAN で拡張
- `cli/lib/tests/test_detector_router.py` — detector_router 経由の間接参照。RouteResult dict 形式を確認必要
- `cli/tests/helix-route.bats` — CLI 統合テスト、本 PLAN で拡張
- `cli/helix-route` — CLI entrypoint、suggest subcommand 追加

### §3.4 変更しないファイル (scope 外)

- `cli/lib/detectors/registry.py` — detector 定義は変更しない
- `cli/helix-detect` — detect CLI は変更しない
- `cli/helix-recover` — recover CLI は変更しない (recover_args の consume 側)
- `HELIX-workflows/helix-process/detection-routing.md` — 親設計 doc は read-only

---

## §4 Sprint 詳細

### Sprint .0: Entry 条件確認 + 設計判断確定

**担当**: PM + TL-advisor

**作業**:
1. `cli/lib/route_engine.py` 全体 Read (完了: §2 の設計判断ベース)
2. `cli/lib/tests/test_route_engine.py` 冒頭 Read (テスト構造確認)
3. `cli/tests/helix-route.bats` 冒頭 Read (bats 構造確認)
4. PLAN B (L7-cli-helix-refactor-implplan) / PLAN C (L7-cli-helix-retrofit-implplan) の drift_type 分岐表と §2.2 分岐表を照合し完全一致を確認
5. tl-advisor R1 review → 承認後 Sprint .1 に進む

**受入条件**:
- §2 全設計判断が tl-advisor によって承認済み
- drift_type 7 種分岐表が PLAN B/C と一致確認済み
- 既存 `helix route eval` / `list-signals` backward compat 方針が明確

---

### Sprint .1: テスト設計 + Failing Tests (TDD Step 1)

**担当**: SE

**TDD 原則**: テストが全て failing になることを pytest で確認してから Sprint .2 に進む。

#### テスト設計 doc 起草

`docs/v2/L7-test-design/L7-route-engine-drift-type-retrofit-ext-test-design.md` を作成する。

内容:
- 対象設計: `docs/v2/L7-design/L7-route-engine-drift-type-retrofit-ext-design.md`
- テスト対象: `cli/lib/route_engine.py` (拡張分)
- テスト実装: `cli/lib/tests/test_route_engine.py` (拡張分) / `cli/tests/helix-route.bats` (拡張分)

#### 追加テストケース一覧

**Python unit tests (test_route_engine.py 追加分)**:

```
U-EXT-001: drift + drift_type=schema → mode=Reverse, kind=reverse, subtype=normalization
U-EXT-002: drift + drift_type=contract → mode=Reverse, kind=reverse, subtype=normalization
U-EXT-003: drift + drift_type=code_smell → mode=Refactor, kind=refactor, subtype=None
U-EXT-004: drift + drift_type=structural → mode=Refactor, kind=refactor, subtype=None
U-EXT-005: drift + drift_type=dependency_outdated → mode=Retrofit, kind=retrofit, subtype=dependency
U-EXT-006: drift + drift_type=upgrade → mode=Retrofit, kind=retrofit, subtype=upgrade
U-EXT-007: drift + drift_type=config_drift → mode=Retrofit, kind=retrofit, subtype=config
U-EXT-008: drift + drift_type 未指定 → mode=Reverse (backward compat)
U-EXT-009: signal=dependency_outdated (shortcut) → mode=Retrofit, kind=retrofit, drift_type="dependency_outdated" (自動付与 P0-1)
U-EXT-010: signal=upgrade (shortcut) → mode=Retrofit, kind=retrofit, drift_type="upgrade" (自動付与 P0-1)
U-EXT-011: signal=config_drift (shortcut) → mode=Retrofit, kind=retrofit, drift_type="config_drift" (自動付与 P0-1)
U-EXT-012: RouteResult.drift_type が drift signal で drift_type 値を持つ
U-EXT-013: RouteResult.drift_type が非 shortcut/非 drift signal で None を返す
U-EXT-014: RouteResult.recommended_command が Retrofit 時に JSON object で drift-type 含む
U-EXT-015: RouteResult.recommended_command が Reverse 時に command="helix reverse normalization R0" (P0-2)
U-EXT-016: RouteResult.recommended_command が Refactor 時に command="helix plan draft", args={"kind": "refactor"}
U-EXT-017: RouteResult.to_dict() に drift_type / recommended_command が含まれる
U-EXT-018: from_detect_output() が result.drift_type を読み取り RouteResult に伝播する
U-EXT-019: from_detect_output() が drift_type 未指定時にデフォルト (schema) を適用する
U-EXT-020: list_signals() に dependency_outdated / upgrade / config_drift が含まれる
U-EXT-021: list_signals() の drift エントリに drift_types[] field が追加されている
U-EXT-022: 既存テスト (test_drift_routes_to_reverse_normalization 等) が回帰しない (py_compile 含む)
U-EXT-023: shortcut signal=upgrade + recommended_command の exact match (command/args/safety 全項目、P1-5)
U-EXT-024: shortcut signal=upgrade + uncertainty=high, impact=high → recommended_command.safety.requires_preflight=True (P1-5 高リスク)
U-EXT-025: drift_type validate conflict — signal=upgrade + drift_type="config_drift" → RouteEngineError 発生 (P1-2)
U-EXT-026: Reverse recommended_command format — signal=drift, drift_type=schema → command="helix reverse normalization R0" (P0-2 exact match)
```

**追加テストコード例 (P1-5、Sprint .1 で実装)**:

```python
def test_shortcut_upgrade_recommended_command():
    result = RouteEngine().evaluate(signal="upgrade", uncertainty="low", impact="low")
    assert result.mode == "Retrofit"
    assert result.drift_type == "upgrade"              # P0-1: shortcut 自動付与
    assert result.recommended_command["command"] == "helix plan draft"
    assert result.recommended_command["args"]["kind"] == "retrofit"
    assert result.recommended_command["args"]["drift_type"] == "upgrade"

def test_shortcut_upgrade_high_risk_preflight():
    result = RouteEngine().evaluate(signal="upgrade", uncertainty="high", impact="high")
    assert result.recommended_command["safety"]["requires_preflight"] is True  # P1-5

def test_drift_type_validate_conflict():
    with pytest.raises(RouteEngineError, match="矛盾"):
        RouteEngine().evaluate(signal="upgrade", drift_type="config_drift")  # P1-2

def test_reverse_command_format():
    result = RouteEngine().evaluate(signal="drift", drift_type="schema")
    # P0-2: helix reverse <type> <stage> 形式
    assert result.recommended_command["command"] == "helix reverse normalization R0"
```

**bats integration tests (helix-route.bats 追加分)**:

```
B-EXT-001: helix route eval --signal drift → backward compat (mode=Reverse)
B-EXT-002: helix route eval --signal dependency_outdated → mode=Retrofit JSON 確認
B-EXT-003: helix route suggest --signal dependency_outdated → suggest_command 1 行 string 出力 (`--format json` で recommended_command JSON object 含む)
B-EXT-004: helix route suggest --signal drift --drift-type config_drift → Retrofit command
B-EXT-005: helix route suggest --signal drift --drift-type code_smell → Refactor command
B-EXT-006: helix route suggest --signal drift → backward compat (drift_type 未指定 = schema)
B-EXT-007: helix route list-signals --json に dependency_outdated / upgrade / config_drift 含む
B-EXT-008: helix route suggest --json で full RouteResult JSON 出力
```

#### Failing tests 作成手順

1. `test_route_engine.py` に U-EXT-001〜022 を追加 (実装前なので全て failing)
2. `helix-route.bats` に B-EXT-001〜008 を追加 (suggest subcommand 未実装なので failing)
3. `pytest cli/lib/tests/test_route_engine.py -v` でフォールバックテスト (U-EXT-022) のみ PASS、他は FAIL を確認
4. Failing 確認後に Sprint .2 に移行

**受入条件**:
- テスト設計 doc 生成済み
- 新規テスト U-EXT-001〜021 が全て failing
- 既存テスト U-EXT-022 (回帰確認群) は PASS を維持

---

### Sprint .2: route_engine.py 拡張実装

**担当**: SE

**TDD 原則**: テストを PASS させることだけを目的にする。テスト追加は Sprint .1 で完了済み。

#### 変更対象: cli/lib/route_engine.py

**Step 2-1: Mode / Kind Literal 拡張**

```python
# Before
Mode = Literal["Reverse", "Refactor", "Recovery", "Incident"]
Kind = Literal["reverse", "refactor", "recovery", "troubleshoot"]

# After
Mode = Literal["Reverse", "Refactor", "Recovery", "Incident", "Retrofit"]
Kind = Literal["reverse", "refactor", "recovery", "troubleshoot", "retrofit"]
DriftType = Literal[
    "schema", "contract", "code_smell", "structural",
    "dependency_outdated", "upgrade", "config_drift"
]
VALID_DRIFT_TYPES: tuple[str, ...] = (
    "schema", "contract", "code_smell", "structural",
    "dependency_outdated", "upgrade", "config_drift"
)
DEFAULT_DRIFT_TYPE = "schema"
```

**Step 2-2: SIGNAL_TO_MODE 拡張**

```python
SIGNAL_TO_MODE: dict[str, dict[str, str | None]] = {
    # 既存 (変更なし)
    "drift": {"mode": "Reverse", "kind": "reverse", "subtype": "normalization"},
    "debt_degradation": {"mode": "Refactor", "kind": "refactor", "subtype": None},
    "regression_prod": {"mode": "Incident", "kind": "recovery", "subtype": None},
    "regression_dev": {"mode": "Recovery", "kind": "recovery", "subtype": None},
    "runaway": {"mode": "Recovery", "kind": "recovery", "subtype": None},
    "incident": {"mode": "Incident", "kind": "_env_dependent", "subtype": None},
    "unknown_design": {"mode": "Reverse", "kind": "reverse", "subtype": "code"},
    # 新規追加 (Retrofit shortcut signals)
    "dependency_outdated": {"mode": "Retrofit", "kind": "retrofit", "subtype": "dependency"},
    "upgrade": {"mode": "Retrofit", "kind": "retrofit", "subtype": "upgrade"},
    "config_drift": {"mode": "Retrofit", "kind": "retrofit", "subtype": "config"},
}

# drift signal の drift_type 別マッピング (新規)
DRIFT_TYPE_OVERRIDE: dict[str, dict[str, str | None]] = {
    "schema":               {"mode": "Reverse",  "kind": "reverse",  "subtype": "normalization"},
    "contract":             {"mode": "Reverse",  "kind": "reverse",  "subtype": "normalization"},
    "code_smell":           {"mode": "Refactor", "kind": "refactor", "subtype": None},
    "structural":           {"mode": "Refactor", "kind": "refactor", "subtype": None},
    "dependency_outdated":  {"mode": "Retrofit", "kind": "retrofit", "subtype": "dependency"},
    "upgrade":              {"mode": "Retrofit", "kind": "retrofit", "subtype": "upgrade"},
    "config_drift":         {"mode": "Retrofit", "kind": "retrofit", "subtype": "config"},
}
```

**Step 2-3: RouteResult 拡張**

```python
@dataclass(frozen=True, slots=True)
class RouteResult:
    signal: str
    mode: Mode
    kind: Kind
    subtype: str | None
    priority: Priority
    action: Action
    env: Env
    source_schema: str
    suggest_command: str                   # 既存 (backward compat 維持、string 形式)
    recover_args: dict[str, str] | None
    plan_hint: str
    drift_type: str | None                 # 新規: shortcut signal は自動付与、drift signal は引数/DRIFT_TYPE_OVERRIDE から取得
    recommended_command: dict[str, Any]    # 新規: JSON object 形式 (ADR-042、string 形式廃止)
```

**Step 2-4: evaluate() 拡張**

```python
def evaluate(
    self,
    signal: str,
    uncertainty: Severity = "low",
    impact: Severity = "low",
    env: Env | None = None,
    reopen_point: str = "HEAD",
    drift_type: str | None = None,   # 新規引数
) -> RouteResult:
    signal_id = self._normalize_signal(signal)
    normalized_uncertainty = self._normalize_severity("uncertainty", uncertainty)
    normalized_impact = self._normalize_severity("impact", impact)
    normalized_env = self._resolve_env(signal_id, env)
    normalized_drift_type = self._resolve_drift_type(signal_id, drift_type)  # 新規
    route = self._resolve_route(signal_id, normalized_env, normalized_drift_type)  # 拡張
    priority, action = self.PRIORITY_ACTION[(normalized_uncertainty, normalized_impact)]
    suggest_command, recover_args = self._build_suggest_command(
        signal_id, route["kind"], normalized_env, reopen_point
    )
    recommended_command = self._build_recommended_command(  # 新規
        signal_id, route["mode"], route["kind"], normalized_drift_type,
        normalized_env, reopen_point
    )
    plan_hint = self._build_plan_hint(signal_id, route["mode"], priority, action)
    return RouteResult(
        signal=signal_id,
        mode=route["mode"],
        kind=route["kind"],
        subtype=route["subtype"],
        priority=priority,
        action=action,
        env=normalized_env,
        source_schema=SOURCE_SCHEMA,
        suggest_command=suggest_command,
        recover_args=recover_args,
        plan_hint=plan_hint,
        drift_type=normalized_drift_type,
        recommended_command=recommended_command,
    )
```

**Step 2-5: 新規プライベートメソッド**

```python
# shortcut signal → drift_type 自動付与マッピング (P0-1 修正)
# signal != "drift" でも shortcut signal (dependency_outdated / upgrade / config_drift) は drift_type を自動付与
SIGNAL_TO_DRIFT_TYPE: dict[str, str | None] = {
    "drift": None,                        # 単独 drift は drift_type を引数または DRIFT_TYPE_OVERRIDE から取得
    "dependency_outdated": "dependency_outdated",  # shortcut → drift_type 自動付与
    "upgrade": "upgrade",                          # shortcut → drift_type 自動付与
    "config_drift": "config_drift",                # shortcut → drift_type 自動付与
    "debt_degradation": None,             # Refactor 経由、drift_type 必須でない
    # 他 signal は drift_type=None (Reverse/Recovery 系)
}

def _resolve_drift_type(self, signal: str, drift_type_arg: str | None) -> str | None:
    """drift_type を解決する (P0-1 shortcut signal 対応版)。
    - shortcut signal (dependency_outdated/upgrade/config_drift): drift_type を自動付与
      → drift_type_arg が同値なら許可、矛盾する値なら RouteEngineError
    - drift signal: 引数または DRIFT_TYPE_OVERRIDE から取得、未指定は DEFAULT_DRIFT_TYPE
    - 他 signal: None を返す
    """
    auto = SIGNAL_TO_DRIFT_TYPE.get(signal)
    if auto is not None:
        # shortcut signal: drift_type が自動決定される
        self._validate_drift_type(signal, drift_type_arg)  # 矛盾チェック (P1-2)
        return auto
    if signal == "drift":
        if drift_type_arg is None:
            return DEFAULT_DRIFT_TYPE
        normalized = drift_type_arg.strip().lower()
        if normalized not in VALID_DRIFT_TYPES:
            raise RouteEngineError(f"unknown drift_type: {drift_type_arg}")
        return normalized
    # その他 signal (Reverse/Recovery/Incident 系): DRIFT_TYPE_OVERRIDE 上書きなし
    return DRIFT_TYPE_OVERRIDE.get(signal)  # 基本 None、特殊 override がある signal のみ非 None

def _validate_drift_type(self, signal: str, drift_type_arg: str | None) -> None:
    """shortcut signal に明示 drift_type 指定された場合、同値なら許可、矛盾は RouteEngineError (P1-2)。"""
    shortcut = SIGNAL_TO_DRIFT_TYPE.get(signal)
    if shortcut is not None and drift_type_arg is not None and shortcut != drift_type_arg:
        raise RouteEngineError(
            f"signal={signal} の drift_type は {shortcut} 固定、"
            f"明示指定 {drift_type_arg} と矛盾します"
        )
```

def _resolve_route(self, signal: str, env: Env, drift_type: str | None = None) -> dict[str, Any]:
    """signal + drift_type でルートを解決する。drift signal のみ drift_type で上書き。"""
    mapping = self.SIGNAL_TO_MODE[signal]
    mode = mapping["mode"]
    subtype = mapping["subtype"]
    kind = mapping["kind"]
    if signal == "incident":
        kind = "recovery" if env == "prod" else "troubleshoot"
    # drift signal + drift_type が指定された場合は DRIFT_TYPE_OVERRIDE で上書き
    if signal == "drift" and drift_type is not None:
        override = self.DRIFT_TYPE_OVERRIDE[drift_type]
        mode = override["mode"]
        kind = override["kind"]
        subtype = override["subtype"]
    return {"mode": mode, "kind": kind, "subtype": subtype}

def _build_recommended_command(
    self,
    signal: str,
    mode: str,
    kind: str,
    drift_type: str | None,
    env: Env,
    reopen_point: str,
) -> dict[str, Any]:
    """suggest subcommand が返す詳細 recommended_command を JSON object 形式で生成する。
    ADR-042 §Decision: string 廃止・JSON object 一本化。
    Recovery 例外: helix recover plan を使用 (helix plan draft とは異なる)。
    Reverse 形式: helix reverse <type> <stage> (cli/helix-reverse usage、ADR-042 固定表)。
    """
    # P1-4 反映: ADR-042 RecommendedCommandV1 schema 完全化 (schema_version + safety 3 field: auto_apply / requires_human_approval / requires_preflight)
    base_safety = {"auto_apply": False, "requires_human_approval": False, "requires_preflight": False}
    if signal in RECOVER_LINKED_SIGNALS or (signal == "incident" and env == "prod"):
        # ADR-042 Recovery 例外: helix recover plan
        return {
            "schema_version": "v1",
            "command": "helix recover plan",
            "args": {
                "signal_id": signal,
                "reopen_point": reopen_point,
                "auto_routed_from": "helix-route",
            },
            "safety": {**base_safety, "requires_human_approval": True},  # recovery は人間承認推奨
        }
    if mode == "Reverse":
        # P0-2 修正: helix reverse <type> <stage> 形式 (ADR-042 固定表と一致)
        # 誤: "helix reverse R0 --type normalization"
        # 正: "helix reverse normalization R0"
        reverse_type = "normalization"  # schema/contract → normalization
        return {
            "schema_version": "v1",
            "command": f"helix reverse {reverse_type} R0",
            "args": {},
            "safety": base_safety,
        }
    if mode == "Refactor":
        return {
            "schema_version": "v1",
            "command": "helix plan draft",
            "args": {"kind": "refactor"},
            "safety": base_safety,
        }
    if mode == "Retrofit":
        dt = drift_type or "dependency_outdated"
        high_risk = uncertainty == "high" or impact == "high"  # ADR-041 §upgrade 行
        # ADR-041 §config_drift 行: env/infra/prod 人間承認必須
        requires_approval = (dt == "config_drift")
        if high_risk and dt == "upgrade":
            # ADR-042 §RecommendedCommandV1 requires_preflight: Reverse upgrade R0 前段
            return {
                "schema_version": "v1",
                "command": "helix reverse upgrade R0",
                "args": {},
                "safety": {**base_safety, "requires_preflight": True},
            }
        return {
            "schema_version": "v1",
            "command": "helix plan draft",
            "args": {"kind": "retrofit", "drift_type": dt},
            "safety": {**base_safety, "requires_human_approval": requires_approval},
        }
    # fallback
    return {
        "schema_version": "v1",
        "command": "helix plan draft",
        "args": {"kind": kind},
        "safety": base_safety,
    }
```

**Step 2-6: from_detect_output() 拡張**

```python
def from_detect_output(self, detect_run_json: dict[str, Any] | list[dict[str, Any]]) -> list[RouteResult]:
    # ... 既存の schema 検証ロジック (変更なし) ...
    results: list[RouteResult] = []
    for item in items:
        # ... 既存の validation (変更なし) ...
        result = item.get("result")
        # drift_type を result から取得 (新規)
        raw_drift_type = result.get("drift_type") if isinstance(result, dict) else None
        results.append(
            self.evaluate(
                str(item["status"]),
                uncertainty=str(result.get("uncertainty", "low")),
                impact=str(result.get("impact", "low")),
                env=self._env_from_result(result),
                reopen_point=str(result.get("reopen_point", "HEAD")),
                drift_type=str(raw_drift_type) if raw_drift_type is not None else None,  # 新規
            )
        )
    return results
```

**Step 2-7: list_signals() 拡張**

```python
def list_signals(self) -> list[dict[str, Any]]:
    items = []
    for signal, values in self.SIGNAL_TO_MODE.items():
        entry: dict[str, Any] = {
            "signal": signal,
            "mode": values["mode"],
            "kind": self._display_kind(signal, "dev"),
            "subtype": values["subtype"],
            "deprecated": False,
        }
        # drift signal に drift_types[] を追加 (新規)
        if signal == "drift":
            entry["drift_types"] = list(VALID_DRIFT_TYPES)
        items.append(entry)
    # deprecated alias (変更なし)
    items.append({
        "signal": "degradation",
        "mode": "alias",
        "kind": "alias",
        "subtype": None,
        "deprecated": True,
        "replacement": self.DEPRECATED_ALIAS["degradation"],
    })
    return items
```

**受入条件**:
- py_compile PASS
- U-EXT-001〜021 が PASS に転換
- 既存テスト全件 PASS (回帰なし)

---

### Sprint .3: suggest subcommand 実装 (helix-route CLI 拡張)

**担当**: SE

#### 変更対象: cli/helix-route

`suggest` subcommand を argparse に追加する。

**argparse 拡張**:

```python
# _build_parser() 内
suggest_parser = sub.add_parser("suggest")
suggest_source = suggest_parser.add_mutually_exclusive_group(required=True)
suggest_source.add_argument("--signal")
suggest_source.add_argument("--from-json")
suggest_parser.add_argument("--drift-type")
suggest_parser.add_argument("--uncertainty", default="low")
suggest_parser.add_argument("--impact", default="low")
suggest_parser.add_argument("--env")
suggest_parser.add_argument("--reopen-point", default="HEAD")
suggest_parser.add_argument("--json", action="store_true", dest="output_json")
```

**suggest コマンドの実行ロジック**:

```python
if args.command == "suggest":
    if args.from_json:
        results = engine.from_detect_output(_load_json_input(args.from_json))
        if args.output_json:
            print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, sort_keys=True))
        else:
            for r in results:
                print(r.recommended_command)
        return 0
    result = engine.evaluate(
        args.signal,
        uncertainty=args.uncertainty,
        impact=args.impact,
        env=args.env,
        reopen_point=args.reopen_point,
        drift_type=args.drift_type,
    )
    if args.output_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))
    else:
        print(result.recommended_command)
    return 0
```

**help テキスト更新**:

```python
def _print_route_help() -> None:
    print(
        "Usage: helix route <eval|suggest|list-signals|help> [args...]\n\n"
        "Commands:\n"
        "  eval          signal または detect JSON から route を評価 (full RouteResult)\n"
        "  suggest       suggest_command を 1 行 string で出力 (人間向け)、--format json で recommended_command JSON object 含む\n"
        "  list-signals  登録済 signal と alias を表示 (drift の drift_types[] 含む)\n"
        "  help          この usage を表示\n"
    )
```

**受入条件**:
- B-EXT-001〜008 が全て PASS
- `helix route eval` / `list-signals` の既存 bats テスト PASS (backward compat)
- `helix route suggest --signal drift` で backward compat (drift_type 未指定 = schema = Reverse)

---

### Sprint .4: 全テスト通過確認 + 設計 doc 生成

**担当**: SE

**作業**:

1. 全 pytest 実行:
   ```bash
   python3 -m pytest cli/lib/tests/test_route_engine.py -v --tb=short
   ```
   期待: 全件 PASS (既存 + U-EXT-001〜022)

2. 全 bats 実行:
   ```bash
   bats cli/tests/helix-route.bats
   ```
   期待: 全件 PASS (既存 + B-EXT-001〜008)

3. 回帰確認 (route 関連テスト全体):
   ```bash
   python3 -m pytest cli/lib/tests/test_detector_router.py -v --tb=short
   ```

4. py_compile 確認:
   ```bash
   python3 -m py_compile cli/lib/route_engine.py
   ```

5. 設計 doc 生成:
   `docs/v2/L7-design/L7-route-engine-drift-type-retrofit-ext-design.md` を起草する。
   内容: §2 設計判断の永続化 (接続契約・drift_type 7 種・suggest subcommand 仕様)

**受入条件**:
- pytest / bats 全件 PASS
- py_compile PASS
- 設計 doc 生成済み

---

### Sprint .5: セルフレビュー + pmo-sonnet review + DoD 確認

**担当**: SE + PMO

**セルフレビューチェックリスト**:

- [ ] drift_type 7 種分岐表が PLAN B (L7-cli-helix-refactor-implplan) と完全一致
- [ ] drift_type 7 種分岐表が PLAN C (L7-cli-helix-retrofit-implplan) と完全一致
- [ ] `helix route eval --signal drift` backward compat (Reverse/normalization)
- [ ] `helix route eval --format command` backward compat (出力形式変更なし)
- [ ] `from_detect_output()` backward compat (drift_type なし JSON でエラーなし)
- [ ] `RouteResult.to_dict()` に drift_type / recommended_command が含まれる
- [ ] suggest subcommand の Retrofit 出力に `--drift-type` が含まれる
- [ ] suggest subcommand の Reverse 出力: `helix reverse normalization R0` (P0-2、`helix reverse <type> <stage>` 形式)
- [ ] suggest subcommand の Refactor 出力: `helix plan draft --kind refactor`
- [ ] Recovery/Incident (prod) signal: recommended_command = helix recover plan (既存と同一)

**pmo-sonnet review 観点**:
- 4 artifact 双方向 trace: ① 設計 doc ↔ ③ テスト設計 doc ↔ ④ テストコード
- PLAN B/C の blocks 依存が frontmatter に正確に記述されているか
- §7 V3 接続契約の completeness

**受入条件**:
- セルフレビューチェックリスト全項目 checked
- pmo-sonnet review passed

---

## §5 DoD + 受入条件

### 必須 (Sprint Exit 前に全項目確認)

- [ ] py_compile PASS: `python3 -m py_compile cli/lib/route_engine.py`
- [ ] pytest ALL PASS: `python3 -m pytest cli/lib/tests/test_route_engine.py -v`
- [ ] bats ALL PASS: `bats cli/tests/helix-route.bats`
- [ ] 回帰なし: `python3 -m pytest cli/lib/tests/test_detector_router.py -v`
- [ ] drift_type 7 種分岐表が §2.2 テーブルと完全一致
- [ ] `Mode` Literal に `Retrofit` 追加済み
- [ ] `RouteResult` に `drift_type` / `recommended_command` field 追加済み
- [ ] `helix route suggest` が installed で動作する
- [ ] backward compat: 既存 `helix route eval --signal drift` が Reverse/normalization を返す
- [ ] backward compat: `RouteResult.suggest_command` が既存と同じ値
- [ ] テスト設計 doc 生成済み (`docs/v2/L7-test-design/`)
- [ ] 設計 doc 生成済み (`docs/v2/L7-design/`)
- [ ] PLAN B/C が本 PLAN の drift_type 分岐表を参照する旨を frontmatter に記載済み

### on-demand

- [ ] helix doctor check PASS (regression なし)
- [ ] security audit: RouteEngineError による入力 validation 確認

---

## §6 risk + mitigation

### R1: 既存 helix-route 互換破壊

**リスク**: `RouteResult` に field を追加することで、JSON を parse する既存コードが予期しない field で壊れる可能性。

**影響**: high (detect_router / 外部呼び出し元)

**mitigation**:
- `to_dict()` は `asdict()` で自動対応、追加 field は無視可能
- `suggest_command` の値は変更しない (既存コマンド文字列を保持)
- Sprint .4 で `test_detector_router.py` を回帰実行して確認

---

### R2: drift_type 誤判定 / PLAN B/C との不整合

**リスク**: PLAN B (refactor) / C (retrofit) が異なる drift_type 分岐表を参照した場合、3 PLAN 間で動作が矛盾する。

**影響**: high (Refactor/Retrofit の mode 選択が誤る)

**mitigation**:
- §2.2 分岐表を「本 PLAN を単一 source of truth」として確立し、PLAN B/C は本 PLAN を参照する形に統一
- Sprint .0 の Entry で PLAN B/C の分岐表と §2.2 を照合、差異があれば本 PLAN を訂正
- Sprint .5 セルフレビューでも再確認

---

### R3: Mode enum 移行 (Literal 型)

**リスク**: `Retrofit` を Literal に追加することで、型チェックツール (mypy) が既存コードの `Mode` 型ヒント使用箇所でエラーを出す可能性。

**影響**: low (現行は型ヒントのみ、runtime には影響しない)

**mitigation**:
- Literal の追加は backward compat (既存値は全て保持)
- mypy が実行されていれば Sprint .4 で確認

---

### R4: suggest subcommand の recommended_command JSON object 変更

**リスク**: ADR-042 で `recommended_command` は **後続 CLI に渡す機械契約 (JSON object)** と確定。schema_version v1 から v2 等への将来変更時に、消費側 (PLAN B/C/D の各 CLI) が strict parser で fail-close できる必要がある。

**影響**: medium

**mitigation** (ADR-042 §役割分離契約に整合、R5 P1-R5-2 で役割逆転を訂正):
- `recommended_command` は **機械処理用 JSON object** (§2.4、ADR-042 §Decision)。後続 CLI (`helix plan draft` / `helix recover plan` / `helix reverse`) はこの JSON を strict に parse する
- `schema_version` field を strict parser で検証し、unknown version で fail-close
- 人間向け表示 (cli_hint) には **`suggest_command` (string、backward compat 凍結値)** を使用する (ADR-042 §`suggest_command` backward compat 固定表参照)
- 将来 schema 変更時は ADR-042 §Decision に additive 拡張 (`safety` 追加 field 等) を記録し、`schema_version` を bump する

---

### R5: backward compat — drift signal の drift_type デフォルト

**リスク**: `drift` + drift_type 未指定時に `schema` をデフォルトにすることで、既存テストが `Reverse/normalization` を期待している場合に問題なし。しかし `schema` → `Reverse/normalization` のマッピングが将来変わった場合に不整合が生じる。

**影響**: low

**mitigation**:
- `schema` と `contract` は両方 `Reverse/normalization` にマッピングされているため、`schema` をデフォルトにすることは既存動作と完全一致
- U-EXT-008 / B-EXT-006 で backward compat テストを明示的に追加

---

## §7 V3 接続契約 (route → 各 mode CLI への signal_id / drift_type / recommended_command 完全契約)

### §7.1 契約 schema (helix route → 後続 CLI)

本 PLAN の拡張後、`helix route eval` / `helix route suggest` は以下の JSON schema で後続 CLI に情報を渡す:

```json
{
  "signal": "<signal_id>",
  "mode": "<Reverse|Refactor|Recovery|Incident|Retrofit>",
  "kind": "<reverse|refactor|recovery|troubleshoot|retrofit>",
  "subtype": "<normalization|code|dependency|upgrade|config|null>",
  "drift_type": "<7 種の drift_type | null>",
  "priority": "<P0|P1|P2|P3>",
  "action": "<suggest_only|immediate_plan_draft|discovery_first|emergency_routing>",
  "env": "<dev|prod>",
  "source_schema": "helix_detect_run_json_v1",
  "suggest_command": "<backward compat コマンド文字列 (string、機械処理非推奨)>",
  "recover_args": {"signal_id": "...", "reopen_point": "...", "auto_routed_from": "helix-route"},
  "plan_hint": "<signal> routed to <mode> (<priority>, <action>)",
  "recommended_command": {
    "schema_version": "v1",
    "command": "<CLI コマンド>",
    "args": {"<arg_name>": "<value>"},
    "safety": {
      "auto_apply": false,
      "requires_human_approval": false,
      "requires_preflight": false
    }
  },
  "source_schema": "helix_detect_run_json_v1"
}
```

### §7.2 mode 別 recommended_command テンプレート (ADR-042 SoT 参照)

> **正本**: ADR-042 §Decision + §backward compat 固定表。本 PLAN は SoT 参照のみ行う。

| mode | command | args | 後続 CLI | 備考 |
|---|---|---|---|---|
| Reverse | `helix reverse normalization R0` | `{}` | helix-reverse | `helix reverse <type> <stage>` 形式 (P0-2 修正、`--type` 形式は禁止) |
| Refactor | `helix plan draft` | `{"kind": "refactor"}` | helix plan | |
| Retrofit | `helix plan draft` | `{"kind": "retrofit", "drift_type": "{drift_type}"}` | helix plan | |
| Recovery | `helix recover plan` | `{"signal_id": "{signal}", "reopen_point": "{reopen_point}", "auto_routed_from": "helix-route"}` | helix-recover | ★ ADR-042 Recovery 例外 (helix plan draft ではない) |
| Incident (prod) | `helix recover plan` | `{"signal_id": "{signal}", "reopen_point": "{reopen_point}", "auto_routed_from": "helix-route"}` | helix-recover | ★ ADR-042 Recovery 例外 |

### §7.3 PLAN B (refactor) 接続契約

PLAN B (L7-cli-helix-refactor-implplan) が参照する route 出力:
- `mode=Refactor` かつ `kind=refactor`
- `drift_type` = `code_smell` または `structural`
- `recommended_command` = `helix plan draft --kind refactor`

PLAN B は `helix route eval --signal debt_degradation` または `helix route eval --signal drift --drift-type code_smell` の出力を入力として受け取ることができる。

### §7.4 PLAN C (retrofit) 接続契約

PLAN C (L7-cli-helix-retrofit-implplan) が参照する route 出力:
- `mode=Retrofit` かつ `kind=retrofit`
- `drift_type` = `dependency_outdated` / `upgrade` / `config_drift`
- `subtype` = `dependency` / `upgrade` / `config`
- `recommended_command` = `helix plan draft --kind retrofit --drift-type {drift_type}`

PLAN C の state manager が `drift_type` を受け取り、retrofit 種別 (dependency/upgrade/config) 別の処理分岐に使用する。

### §7.5 backward compat 保証

| 契約点 | 保証内容 |
|---|---|
| `helix route eval --signal drift` | mode=Reverse, kind=reverse, subtype=normalization (変更なし) |
| `helix route eval --format command` | `helix plan draft --kind reverse` (変更なし) |
| `RouteResult.suggest_command` | 既存値を維持 (string 形式、backward compat) |
| `RouteResult.recommended_command` | JSON object 形式 (ADR-042)。Reverse は `helix reverse normalization R0` |
| `from_detect_output()` | drift_type field なし JSON でエラーなし (default 適用) |
| shortcut signal drift_type | `dependency_outdated`/`upgrade`/`config_drift` は drift_type を自動付与 (P0-1) |

---

## §8 関連 doc

| doc | 関係 |
|---|---|
| [detection-routing.md](../../../HELIX-workflows/helix-process/detection-routing.md) | 親設計 doc (本 PLAN の設計の正本) |
| [cross-cutting-mechanisms.md](../../../HELIX-workflows/helix-process/cross-cutting-mechanisms.md) | drift detection の横断メカニズム |
| [refactor-workflow.md](../../../HELIX-workflows/helix-process/refactor-workflow.md) | PLAN B 参照 workflow |
| [retrofit-workflow.md](../../../HELIX-workflows/helix-process/retrofit-workflow.md) | PLAN C 参照 workflow |
| [recovery-workflow.md](../../../HELIX-workflows/helix-process/recovery-workflow.md) | Recovery/Incident 時の後続 workflow |
| [L7-helix-route-implplan.md](./L7-helix-route-implplan.md) | 既存 helix-route 実装 PLAN (本 PLAN の前提依存) |
| [L7-cli-helix-refactor-implplan.md](./L7-cli-helix-refactor-implplan.md) | blocks 依存先 (drift_type 分岐の利用側) |
| [L7-cli-helix-retrofit-implplan.md](./L7-cli-helix-retrofit-implplan.md) | blocks 依存先 (Retrofit mode + suggest の利用側) |
| `docs/adr/ADR-041-drift-type-7-categories-routing-decision.md` | drift_type 7 種分類 SoT (本 PLAN は参照) |
| `docs/adr/ADR-042-recommended-command-machine-vs-display-decision.md` | recommended_command 機械契約 + Recovery 例外 SoT (本 PLAN は参照) |
| `docs/adr/ADR-043-mode-enum-extension-retrofit-freeze-break-decision.md` | Mode enum 拡張 + parent_design_addenda field (frontmatter で適用済) |
| `cli/lib/route_engine.py` | 本 PLAN の実装対象 |
| `cli/lib/tests/test_route_engine.py` | テストコード (本 PLAN で拡張) |
| `cli/tests/helix-route.bats` | CLI 統合テスト (本 PLAN で拡張) |

---

## §9 carry / 残課題

### §9.1 本 PLAN 完遂後の carry

| carry | 担当 PLAN | 優先度 |
|---|---|---|
| helix-refactor CLI 実装 (drift_type 分岐受け取り側) | L7-cli-helix-refactor-implplan | P1 |
| helix-retrofit CLI state manager 実装 | L7-cli-helix-retrofit-implplan | P1 |
| from_detect_output() adapter 拡張 (cross-detection schema v2) | 別 PLAN | P3 |

### §9.2 本 PLAN で意図的に対応しない事項

| 項目 | 理由 |
|---|---|
| `helix reverse R0 --type` の実装 | helix-reverse CLI は既存、`--type normalization` 引数は別 scope |
| `helix plan draft --kind retrofit` の実装 | L7-cli-helix-retrofit-implplan scope |
| `helix plan draft --kind refactor` の実装 | L7-cli-helix-refactor-implplan scope |
| cross-detection dashboard schema adapter | 既存 `from_detect_output()` の schema エラー範囲維持 |
| drift_type の helix-detect 出力への追加 | helix-detect / detector 側は別 PLAN |

### §9.3 tl-advisor R1 反映済み指摘 (R2 revision 完了)

本 PLAN は tl-advisor R1 (decision: needs_revision, P0×3 + P1×5) を受けて R2 revision を実施済み。

| 指摘 | 対応状況 |
|---|---|
| P0-1: shortcut signal の drift_type が None になる | **解消**: `SIGNAL_TO_DRIFT_TYPE` dict + `_resolve_drift_type()` を shortcut 自動付与版に改訂 (§4 Step 2-5) |
| P0-2: Reverse の recommended_command が CLI 契約不一致 | **解消**: `helix reverse normalization R0` (`helix reverse <type> <stage>`) 形式に統一 (§2.3/§4/§7.2/§7.5) |
| P0-3: PLAN B/C/C' の route 接続コマンド契約未確定 | **解消**: ADR-042 §Decision SoT 参照に置換、Recovery 例外明示 (§2.3/§7.1/§7.2) |
| P1-1: recommended_command 二重契約矛盾 | **解消**: JSON object 一本化 (ADR-042 準拠)、string 形式記述全削除 (§2.4/§4 Step 2-3/Step 2-5) |
| P1-2: shortcut signal + --drift-type 明示時の validate | **解消**: `_validate_drift_type()` 追加 (§4 Step 2-5)、U-EXT-025 テスト追加 |
| P1-3: Mode enum 拡張前に L2 ADR snapshot | **解消**: ADR-043 起票完遂済、frontmatter `parent_design_addenda` に登録済み |
| P1-4: frontmatter 依存 ID 揺れ | **確認**: 本 PLAN 内部は `plan_id: L7-route-engine-drift-type-retrofit-ext` で統一済み (ファイル名 suffix `plan` は別途、関連 PLAN の参照揺れは各 PLAN で個別対処) |
| P1-5: テスト不足 (shortcut exact match / validate / reverse format) | **解消**: U-EXT-023〜026 + テストコード例追加 (§4 Sprint .1) |

---

## §10 L2 凍結 (ADR snapshot) — 起票完遂済

> **本 PLAN は ADR SoT を参照するのみ。ADR 起票は完遂済み。**

| L2 大局判断 | ADR | status |
|---|---|---|
| drift_type 7 種を PLAN B/C/C' の単一 SoT として route_engine.py に集約する | ADR-041 | Accepted with conditions (2026-05-25) |
| `recommended_command` を JSON object 一本化 (string 廃止)、`suggest_command` と共存で backward compat | ADR-042 | Accepted with conditions (2026-05-25) |
| Mode enum 拡張 (`Retrofit` 追加) + `parent_design_addenda` field 導入 | ADR-043 (R2 代替案 A 採用) | Accepted with conditions (2026-05-25) |

本 PLAN の frontmatter `parent_design_addenda` に ADR-043 を登録済み。実装時は各 ADR の §Decision を正本として参照し、本 PLAN で独自定義を行わない (PLAN ⊃ ADR レイヤー併存原則)。

**R5 反映 (2026-05-25)**: tl-advisor R5 (rollout JSONL bypass、bbvocrtey) で P0 なし、残 P1 2 件 (P1-R5-1 safety field 数 / P1-R5-2 R4 役割逆転) を本 PLAN 内で修正済 ([§5.7](#§5-7) base_safety コメント訂正、[§6 R4](#r4-suggest-subcommand) 役割記述修正)。ADR-041/042/043 を `Accepted with conditions` (frontmatter accepted_date: 2026-05-25) に推進。Conditions: (1) PLAN C' P1-R5 2 件修正反映済 (本 PLAN) (2) `helix plan draft` machine args 拡張 (`L7-helix-plan-draft-machine-args-ext`、ADR-042) (3) `plan_validator.py` `parent_design_addenda` 機械検査拡張 (`L7-plan-validator-parent-design-addenda-ext`、ADR-043) は後続 PLAN 依存。SE 委譲 final 判定 (R5 結果): A1 可 / A2 可 (A1 完遂後) / B 条件付き可 / C 条件付き可 (C1 superseded 完了済) / C' 本 PLAN R5 反映後に再判定 / D 条件付き可。

---

*作成: 2026-05-24 | PMO Sonnet | L7 実装 PLAN (route_engine.py 拡張)*
*R2 revision: 2026-05-24 | PMO Sonnet | tl-advisor R1 needs_revision (P0×3 + P1×5) 反映、ADR-041/042/043 SoT 接続*
