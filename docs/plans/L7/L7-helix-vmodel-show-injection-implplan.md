---
plan_id: L7-helix-vmodel-show-injection-implplan
title: "L7-helix-vmodel-show-injection-implplan: helix vmodel show injection sub-path 取得 CLI 拡張"
kind: impl
layer: L7
drive: be
status: draft
created: 2026-05-24
owner: PM
process_layer: L7
parent_process: HELIX-workflows/helix-process/L7-implementation.md
parent_design: docs/plans/L7/L7-vmodel-semantics-injection-setplan.md
pairs_test_design:
  - docs/plans/L7/L7-helix-vmodel-show-injection-implplan.md
is_reference: false
agent_slots:
  - role: pm-advisor
    slot_label: "PM — 大局判断・最終 finalize"
  - role: tl-advisor
    slot_label: "TL — 設計判断 adversarial check (案 A vs B 選択)"
  - role: se
    slot_label: "SE — vmodel_loader.py method 追加 + CLI 拡張 + test 実装"
  - role: pmo-sonnet
    slot_label: "PMO — 整合チェック・review"
generates:
  - artifact_path: cli/helix-vmodel
    artifact_type: cli_extension
  - artifact_path: cli/lib/vmodel_loader.py
    artifact_type: python_module
  - artifact_path: cli/lib/tests/test_vmodel_loader.py
    artifact_type: test
  - artifact_path: cli/tests/helix-vmodel.bats
    artifact_type: test
dependencies:
  parent: null
  requires:
    - L7-vmodel-semantics-injection-setplan
  blocks: []
related_docs:
  - cli/helix-vmodel
  - cli/lib/vmodel_loader.py
  - cli/config/vmodel-semantics.yaml
  - docs/plans/L7/L7-helix-recover-implplan.md
  - docs/plans/L7/L7-helix-route-implplan.md
  - docs/plans/L7/L7-workflow-skills-pkgplan.md
---

## §0 PLAN concept

> **工程**: L7 実装スプリント
> **parent_design**: [L7-vmodel-semantics-injection-setplan](L7-vmodel-semantics-injection-setplan.md)
> **本 PLAN の位置づけ**: `L7-vmodel-semantics-injection-setplan` の **残 carry 解消**。同 PLAN の tl-advisor 第 2 ラウンド minor 指摘「`helix vmodel show <drive> <layer>` に injection サブフィールドのみを返す sub-path 取得機能を追加すること」を独立した L7 PLAN として起票する。

### 解決する問題

現行 `helix vmodel show <drive> <layer>` は `design / test / pair` セクション全体を返す。`helix-route` / `helix-recover` / `workflow-skills` が injection セット (`mandatory_agents` / `recommended_skills` / `recommended_commands` 等) のみを機械参照しようとすると、全量 JSON をパースして injection キーを抽出する追加処理が必要になる。

### 解決策の選択肢

| 案 | 構文例 | 実装方針 |
|---|---|---|
| **案 A (推奨)** | `helix vmodel show be L4 --injection-only [--json]` | 既存引数 `<drive> <layer>` を維持しフラグ追加 |
| 案 B | `helix vmodel show be/L4/injection [--json]` | 引数を slash-path 1 個に変更 |

**案 A を推奨する理由**:
- 既存 `show <drive> <layer>` の引数パターンを破壊しない
- `--json` と組み合わせた既存ユーザーの習慣を維持できる
- `--injection-only` フラグは他サブコマンドへの拡張 (`--design-only` / `--test-only`) への一貫性を保つ
- 案 B は slash-path 1 引数への変更で既存シェルスクリプトの引数番号がずれるリスクがある

**tl-advisor R1 で案 A / B の確定を委ねる** (§1.1 Step 1)。

### 期待動作

```bash
# 案 A: injection フィールドのみ JSON 出力
$ helix vmodel show be L4 --injection-only --json
{
  "drive": "be",
  "layer": "L4",
  "injection": {
    "owner_role": "TL",
    "mandatory_agents": ["pmo-project-explorer", "pmo-helix-explorer"],
    "recommended_agents": ["pmo-project-scout"],
    "recommended_skills": ["workflow/design-doc", "workflow/api-contract"],
    "recommended_commands": ["helix plan draft", "helix code find"],
    "orchestration_mode": "parallel"
  }
}

# 既存動作は破壊しない
$ helix vmodel show be L4 --json
{ "drive": "be", "layer": "L4", "design": {...}, "test": {...}, "pair": {...}, "injection": {...} }
```

---

## §1 工程表 (作業手順 + 進捗)

| Step | 作業内容 | 担当 | 進捗 |
|------|---------|------|------|
| 1.1 | 設計判断: 案 A vs B → tl-advisor R1 adversarial check | PM + tl-advisor | [ ] |
| 1.2 | `vmodel_loader.py` に `get_layer_injection(drive, layer)` method 追加 | SE | [ ] |
| 1.3 | `cli/helix-vmodel` show サブコマンド拡張 (`--injection-only` フラグ対応) | SE | [ ] |
| 1.4 | help 文字列更新 (usage / show サブコマンド説明) | SE | [ ] |
| 1.5 | unit test 追加 (test_vmodel_loader.py 5 件) | SE | [ ] |
| 1.6 | bats test 追加 (helix-vmodel.bats 3 ケース) | SE | [ ] |
| 1.7 | 機械チェック: `bash -n` / `py_compile` / `pytest` / bats / `helix commands check` | SE | [ ] |
| 1.8 | pmo-sonnet review + self-review | PMO + PM | [ ] |
| 1.9 | commit + carry note 記録 | PM | [ ] |
| 1.10 | Exit 条件確認 (DoD 全 PASS) | PM | [ ] |

---

## §2 実装計画

### §2.A 設計判断 (tl-advisor R1 委任)

tl-advisor に以下の比較表を提示して adversarial check を実施する。

#### 案 A vs B 詳細比較

| 観点 | 案 A (`--injection-only` フラグ) | 案 B (slash-path 引数) |
|------|----------------------------------|------------------------|
| 破壊的変更 | なし (既存 `show <drive> <layer>` 継続動作) | あり (引数数変化、既存スクリプトの `$3` が `--json` ではなく `be/L4/injection` を受け取る) |
| 拡張性 | `--design-only` / `--test-only` / `--pair-only` への一貫拡張可 | path 表現は UNIX-like で直感的、`be/L4/design` 等も自然 |
| パース実装 | `show_entry()` に `--injection-only` 検出を追加するだけ | 引数 1 個 parse → split("/") で drive/layer/section を分解 |
| shell 使いやすさ | `helix vmodel show be L4 --injection-only --json` | `helix vmodel show be/L4/injection --json` |
| 一貫性 | `show` で drive/layer を空白区切りにする既存ルール維持 | 他サブコマンドは空白区切りのため混在 |
| 推奨 | **推奨** (破壊変更なし + 拡張一貫性) | 候補 |

tl-advisor R1 の結果を §2.C 実装へ反映する。本 PLAN は **案 A 前提**で設計を進める (tl-advisor が B を選択した場合は §2.C を差し替える)。

### §2.B vmodel_loader.py method 設計

```python
def get_layer_injection(self, drive: str, layer: str) -> dict[str, Any]:
    """Return only the injection block for the requested drive and layer.

    契約: L7-helix-vmodel-show-injection-implplan §2.B
    """
    layer_data = self.get_layer(drive, layer)   # KeyError は呼び出し元に伝播
    injection = layer_data.get("injection")
    if injection is None:
        raise KeyError(f"injection not defined for drive={drive} layer={layer}")
    if not isinstance(injection, dict):
        raise ValueError(f"injection must be a mapping for drive={drive} layer={layer}")
    return deepcopy(injection)
```

**設計上の注意**:
- `get_layer()` への委譲で drive / layer 存在確認を再利用し、重複ロジックを避ける
- `injection` キー不在時は `KeyError` (caller が stderr 出力してexit 2 する)
- `deepcopy` で内部 dict の意図しない変更を防ぐ (get_layer と同じパターン)
- `INJECTION_REQUIRED_FIELDS` 定数 (`vmodel_loader.py:23`) が validate 時に使用済みのため、get_layer_injection では再検証しない (validate 済みの yaml を前提とする)

### §2.C cli/helix-vmodel show コマンド拡張 (案 A 前提)

`show_entry()` 関数の呼び出しと引数解析を以下のように拡張する:

```bash
show_entry() {
  local drive="$1"
  local layer="$2"
  local as_json="$3"
  local injection_only="$4"   # 追加

  python3 - "$LIB_DIR" "$drive" "$layer" "$as_json" "$injection_only" <<'PY'
import json
import sys
from pathlib import Path

lib_dir = Path(sys.argv[1])
drive = sys.argv[2]
layer = sys.argv[3]
as_json = sys.argv[4] == "true"
injection_only = sys.argv[5] == "true"  # 追加

sys.path.insert(0, str(lib_dir))
from vmodel_loader import load_default

try:
    vm = load_default()
    if injection_only:
        injection = vm.get_layer_injection(drive, layer)
        payload = {"drive": drive, "layer": layer, "injection": injection}
    else:
        payload = {"drive": drive, "layer": layer, **vm.get_layer(drive, layer)}
except KeyError as exc:
    print(f"エラー: {exc.args[0]}", file=sys.stderr)
    raise SystemExit(2)
except Exception as exc:
    print(f"エラー: {exc}", file=sys.stderr)
    raise SystemExit(2)

if as_json:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0)

# テキスト出力 (injection_only)
if injection_only:
    print(f"drive: {payload['drive']}")
    print(f"layer: {payload['layer']}")
    for key, value in payload["injection"].items():
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value)
        else:
            rendered = str(value)
        print(f"injection.{key}: {rendered}")
    raise SystemExit(0)

# 既存テキスト出力 (全セクション)
print(f"drive: {payload['drive']}")
print(f"layer: {payload['layer']}")
for section_name in ("design", "test", "pair"):
    ...  # 既存ロジック維持
PY
}
```

`main()` のオプション解析部分:

```bash
# show サブコマンドの引数解析 (追加分)
injection_only="false"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --injection-only) injection_only="true"; shift ;;
    --json)           as_json="true";        shift ;;
    *)                break ;;
  esac
done
```

### §2.D テスト設計 (pairs_test_design として本 PLAN が自己内包)

#### unit test 設計 (test_vmodel_loader.py 追加分)

| ID | テスト名 | 検証内容 |
|----|---------|---------|
| U-INJ-001 | `test_get_layer_injection_returns_subset` | `be` / `L4` で `get_layer_injection()` を呼ぶと `injection` dict のみが返り、`design` / `test` / `pair` キーを含まない |
| U-INJ-002 | `test_get_layer_injection_unknown_drive_raises` | 存在しない drive で `get_layer_injection()` を呼ぶと `KeyError` |
| U-INJ-003 | `test_get_layer_injection_unknown_layer_raises` | 存在しない layer で `get_layer_injection()` を呼ぶと `KeyError` |
| U-INJ-004 | `test_get_layer_injection_is_deep_copy` | 返り値を変更しても内部 data が汚染されない |
| U-INJ-005 | `test_get_layer_injection_has_required_fields` | `INJECTION_REQUIRED_FIELDS` の全キーが返り値に存在する |

#### bats test 設計 (helix-vmodel.bats 追加分)

| ID | テスト名 | 検証内容 |
|----|---------|---------|
| B-INJ-001 | `show --injection-only --json returns injection dict` | `helix vmodel show be L4 --injection-only --json` が JSON を stdout に出力し、exit 0。`.drive` / `.layer` / `.injection.owner_role` が jq で取得可能 |
| B-INJ-002 | `show --injection-only text output` | `--json` なしで injection.* キーがテキスト出力される |
| B-INJ-003 | `show without --injection-only still works` | 既存 `helix vmodel show be L4 --json` が破壊されていない (`design` / `test` / `pair` キーが存在する) |

---

## §3 成果物

| ファイル | 変更種別 | 規模 |
|---------|---------|------|
| `cli/helix-vmodel` | 修正 | +20〜30 行 (show_entry 引数追加 + injection_only フラグ解析 + テキスト出力分岐) |
| `cli/lib/vmodel_loader.py` | 修正 | +15〜20 行 (`get_layer_injection` method 追加) |
| `cli/lib/tests/test_vmodel_loader.py` | 修正 | +50〜80 行 (5 unit test 追加) |
| `cli/tests/helix-vmodel.bats` | 修正 | +30〜50 行 (3 bats ケース追加) |

**合計変更規模**: +115〜180 行 (小規模)

---

## §4 受入条件 / DoD

- [ ] `bash -n cli/helix-vmodel` が正常終了する
- [ ] `python3 -m py_compile cli/lib/vmodel_loader.py` が正常終了する
- [ ] `pytest cli/lib/tests/test_vmodel_loader.py -q --tb=short` が U-INJ-001〜005 を含み全 PASS
- [ ] `bats cli/tests/helix-vmodel.bats` が B-INJ-001〜003 を含み全 PASS
- [ ] `helix vmodel show be L4 --injection-only --json` が injection dict を JSON 出力する (exit 0)
- [ ] `helix vmodel show be L4 --json` が既存通り `design` / `test` / `pair` / `injection` を返す (破壊変更なし)
- [ ] `helix commands check` が PASS する
- [ ] `helix plan lint docs/plans/L7/L7-helix-vmodel-show-injection-implplan.md` が warnings 0

---

## §5 関連 PLAN / docs

| 関係 | PLAN / doc |
|------|-----------|
| parent (残 carry 元) | `L7-vmodel-semantics-injection-setplan` |
| injection 参照対象 | `L7-helix-recover-implplan` (recovery の injection 機械参照) |
| injection 参照対象 | `L7-helix-route-implplan` (route の injection 機械参照) |
| injection 参照対象 | `L7-workflow-skills-pkgplan` (layer-context-injection skill の 20 セル参照) |
| 正本設計 | `HELIX-workflows/helix-process/layer-context-injection.md` |
| loader 実装元 | `cli/lib/vmodel_loader.py` |
| 設定ファイル | `cli/config/vmodel-semantics.yaml` |

---

## §6 後続 PLAN 候補

| 候補 | 内容 |
|------|------|
| vmodel show 細粒度抽出 | `--mandatory-agents-only` / `--recommended-skills-only` 等の injection 内フィールド単位取得 |
| vmodel list --injection | 全 drive × layer の injection 一覧を JSON 配列で取得 |
| vmodel diff | drive 間 / layer 間の injection 比較出力 |
| helix-route / helix-recover 連携実装 | 本 PLAN 完遂後に `get_layer_injection()` を route / recover から呼び出す |

---

## §7 risks

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| tl-advisor が案 B を選択した場合 | §2.C の実装を slash-path parse に差し替える必要あり | §2.C の代替案 B 実装メモを draft 状態で保持する |
| injection キー不在の既存 yaml セルがある | B-INJ-001 が `KeyError: injection not defined` で fail する | parent PLAN `L7-vmodel-semantics-injection-setplan` で全 20 セルへの injection 追加が DoD となっているため、parent 完遂を Entry 条件とする |
| helix-vmodel.bats 依存の jq コマンド不在 | B-INJ-001 の JSON 検証が実行環境で fail する | `command -v jq` で skip 分岐を bats helper に追加する (既存パターンに倣う) |
| `show_entry()` の引数番号シフトによる既存 test 影響 | B-INJ-003 の既存動作確認で意図しない regression が出る可能性 | Step 1.7 の bats 全量実行 + pytest 全量実行で検証 |
