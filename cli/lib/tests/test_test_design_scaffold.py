"""Tests for cli.lib.test_design_scaffold."""

from __future__ import annotations

from cli.lib.test_design_scaffold import (
    extract_api_endpoints,
    extract_openapi_endpoints,
    auto_detect_paired_design,
    extract_function_signatures,
    extract_paired_design_sections,
    generate_skeleton,
    score_paired_design,
    write_scaffold,
)


def test_generate_skeleton_includes_layer_and_pair() -> None:
    """DoD 検証: W9-C U-001 L4 design から L9 pair skeleton を生成する。"""
    skeleton = generate_skeleton(
        "L4",
        "docs/plans/L4/L4-sample-design-plan.md",
        title="Sample Design",
    )

    assert "target_layer: 'L9'" in skeleton
    assert "paired_design_layer: 'L4'" in skeleton
    assert "TEST-DESIGN-L9" in skeleton
    assert "V-model L4↔L9" in skeleton


def test_generate_skeleton_includes_template_sections() -> None:
    """DoD 検証: W9-C U-002 skeleton に §0-§3 を含む。"""
    skeleton = generate_skeleton(
        "L4",
        "docs/plans/L4/L4-sample-design-plan.md",
        title="Sample Design",
    )

    assert "## §0 対応設計" in skeleton
    assert "## §1 受入条件" in skeleton
    assert "## §2 テストケース" in skeleton
    assert "## §3 トレース" in skeleton


def test_write_scaffold_dry_run_no_write(tmp_path) -> None:
    """DoD 検証: W9-C U-003 dry_run=True ではファイルを書かない。"""
    result = write_scaffold(
        "L4",
        "docs/plans/L4/L4-sample-design-plan.md",
        project_root=tmp_path,
        dry_run=True,
    )

    assert result["status"] == "dry_run"
    assert result["reason"] == "dry run"
    assert not list(tmp_path.rglob("TEST-DESIGN-L9-*.md"))


def test_write_scaffold_apply_writes_file(tmp_path) -> None:
    """DoD 検証: W9-C U-004 dry_run=False では scaffold を書き込む。"""
    output_path = tmp_path / "docs" / "plans" / "L9" / "TEST-DESIGN-L9-custom.md"

    result = write_scaffold(
        "L4",
        "docs/plans/L4/L4-sample-design-plan.md",
        project_root=tmp_path,
        dry_run=False,
        output_path=output_path,
    )

    assert result["status"] == "applied"
    assert result["output_path"] == str(output_path)
    assert output_path.exists()
    assert "paired_design_doc: 'docs/plans/L4/L4-sample-design-plan.md'" in output_path.read_text(
        encoding="utf-8"
    )


def test_write_scaffold_skips_existing(tmp_path) -> None:
    """DoD 検証: W9-C U-005 既存 path には上書きせず skip する。"""
    output_path = tmp_path / "docs" / "plans" / "L9" / "TEST-DESIGN-L9-custom.md"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("existing\n", encoding="utf-8")

    result = write_scaffold(
        "L4",
        "docs/plans/L4/L4-sample-design-plan.md",
        project_root=tmp_path,
        dry_run=False,
        output_path=output_path,
    )

    assert result["status"] == "skipped"
    assert result["reason"] == "file exists"
    assert output_path.read_text(encoding="utf-8") == "existing\n"


def test_extract_paired_design_sections_finds_acceptance(tmp_path) -> None:
    """DoD 検証: W13 U-001 paired design doc から受入条件 section を抽出する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        """# Sample Design

## §1 受入条件

- acceptance text

## §3 補足

- note
""",
        encoding="utf-8",
    )

    sections = extract_paired_design_sections(paired_design)

    assert "acceptance text" in sections["acceptance"]
    assert sections["function_spec"] == ""


def test_generate_skeleton_with_extract_sections_includes_acceptance(tmp_path) -> None:
    """DoD 検証: W13 U-002 extract_sections=True で受入条件引用を注入する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        """# Sample Design

## §1 受入条件

- acceptance text
""",
        encoding="utf-8",
    )

    skeleton = generate_skeleton("L4", str(paired_design), extract_sections=True)

    assert "> - acceptance text" in skeleton


def test_generate_skeleton_extract_sections_handles_missing_file() -> None:
    """DoD 検証: W13 U-003 missing file でも extract_sections=True で落ちない。"""
    skeleton = generate_skeleton(
        "L4",
        "docs/plans/L4/not-found.md",
        extract_sections=True,
    )

    assert "## §1 受入条件" in skeleton
    assert "TODO: pair design doc から DoD を引き写す" in skeleton


def test_auto_detect_paired_design_finds_first_match(tmp_path) -> None:
    """DoD 検証: W16 U-001 pair layer 配下の最初の PLAN を auto detect する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-foo-plan.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")
    (pair_dir / "L9-bar-plan.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path)

    assert detected == "docs/plans/L9/L9-bar-plan.md"


def test_auto_detect_paired_design_returns_none_when_no_pair(tmp_path) -> None:
    """DoD 検証: W16 U-002 pair なし layer は None を返す。"""
    assert auto_detect_paired_design("L0", project_root=tmp_path) is None


def test_auto_detect_paired_design_returns_none_when_no_match(tmp_path) -> None:
    """DoD 検証: W16 U-003 pair layer に match が無いとき None を返す。"""
    assert auto_detect_paired_design("L4", project_root=tmp_path) is None


def test_auto_detect_paired_design_prefers_draft_status(tmp_path) -> None:
    """DoD 検証: W20 U-001 prefer_status='draft' なら draft 候補を優先する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-a-completed-plan.md").write_text("---\nstatus: completed\n---\n", encoding="utf-8")
    (pair_dir / "L9-z-draft-plan.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path, prefer_status="draft")

    assert detected == "docs/plans/L9/L9-z-draft-plan.md"


def test_auto_detect_paired_design_fallback_to_first_when_no_preferred(tmp_path) -> None:
    """DoD 検証: W20 U-002 prefer_status 未該当時は sorted 最初へ fallback する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-a-completed-plan.md").write_text("---\nstatus: completed\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path, prefer_status="draft")

    assert detected == "docs/plans/L9/L9-a-completed-plan.md"


def test_auto_detect_paired_design_none_disables_preference(tmp_path) -> None:
    """DoD 検証: W20 U-003 prefer_status=None なら従来の sorted 最初を使う。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-a-completed-plan.md").write_text("---\nstatus: completed\n---\n", encoding="utf-8")
    (pair_dir / "L9-z-draft-plan.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path, prefer_status=None)

    assert detected == "docs/plans/L9/L9-a-completed-plan.md"


def test_auto_detect_paired_design_prefers_design_kind(tmp_path) -> None:
    """DoD 検証: W22 U-001 prefer_kind='design' なら design 候補を優先する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-poc-plan.md").write_text("---\nkind: poc\nstatus: draft\n---\n", encoding="utf-8")
    (pair_dir / "L9-design-plan.md").write_text("---\nkind: design\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path, prefer_kind="design")

    assert detected == "docs/plans/L9/L9-design-plan.md"


def test_auto_detect_paired_design_fallback_when_no_preferred_kind(tmp_path) -> None:
    """DoD 検証: W22 U-002 prefer_kind 未該当時は sorted 最初へ fallback する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-impl-plan.md").write_text("---\nkind: impl\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design("L4", project_root=tmp_path, prefer_kind="design")

    assert detected == "docs/plans/L9/L9-impl-plan.md"


def test_auto_detect_paired_design_prefer_status_and_kind_combined(tmp_path) -> None:
    """DoD 検証: W22 U-003 prefer_status と prefer_kind 両一致を最優先する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-old-design-completed-plan.md").write_text(
        "---\nkind: design\nstatus: completed\n---\n",
        encoding="utf-8",
    )
    (pair_dir / "L9-new-design-draft-plan.md").write_text(
        "---\nkind: design\nstatus: draft\n---\n",
        encoding="utf-8",
    )
    (pair_dir / "L9-impl-draft-plan.md").write_text("---\nkind: impl\nstatus: draft\n---\n", encoding="utf-8")

    detected = auto_detect_paired_design(
        "L4",
        project_root=tmp_path,
        prefer_status="draft",
        prefer_kind="design",
    )

    assert detected == "docs/plans/L9/L9-new-design-draft-plan.md"


def test_score_paired_design_status_match_only() -> None:
    """DoD 検証: W26 U-001 status 一致のみなら status weight を返す。"""
    score = score_paired_design(
        {"status": "draft", "kind": "impl"},
        prefer_status="draft",
        prefer_kind=None,
    )

    assert score == 2


def test_score_paired_design_both_match() -> None:
    """DoD 検証: W26 U-002 status と kind が両一致なら合計 score を返す。"""
    score = score_paired_design(
        {"status": "draft", "kind": "design"},
        prefer_status="draft",
        prefer_kind="design",
    )

    assert score == 3


def test_auto_detect_paired_design_weighted_selects_best(tmp_path) -> None:
    """DoD 検証: W26 U-003 weighted=True なら最高 score の候補を選ぶ。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-a-status-only-plan.md").write_text(
        "---\nstatus: draft\nkind: impl\n---\n",
        encoding="utf-8",
    )
    (pair_dir / "L9-b-both-match-plan.md").write_text(
        "---\nstatus: draft\nkind: design\n---\n",
        encoding="utf-8",
    )

    detected = auto_detect_paired_design(
        "L4",
        project_root=tmp_path,
        prefer_status="draft",
        prefer_kind="design",
        weighted=True,
    )

    assert detected == "docs/plans/L9/L9-b-both-match-plan.md"


def test_auto_detect_paired_design_custom_weight(tmp_path) -> None:
    """DoD 検証: W28 U-001 custom weight で kind 優先候補を選べる。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-status-match-plan.md").write_text(
        "---\nstatus: draft\nkind: impl\n---\n",
        encoding="utf-8",
    )
    (pair_dir / "L9-kind-match-plan.md").write_text(
        "---\nstatus: completed\nkind: design\n---\n",
        encoding="utf-8",
    )

    detected = auto_detect_paired_design(
        "L4",
        project_root=tmp_path,
        prefer_status="draft",
        prefer_kind="design",
        weighted=True,
        status_weight=1,
        kind_weight=3,
    )

    assert detected == "docs/plans/L9/L9-kind-match-plan.md"


def test_auto_detect_paired_design_default_weight_uses_status_priority(tmp_path) -> None:
    """DoD 検証: W28 U-002 default weight は status 優先を維持する。"""
    pair_dir = tmp_path / "docs" / "plans" / "L9"
    pair_dir.mkdir(parents=True)
    (pair_dir / "L9-status-match-plan.md").write_text(
        "---\nstatus: draft\nkind: impl\n---\n",
        encoding="utf-8",
    )
    (pair_dir / "L9-kind-match-plan.md").write_text(
        "---\nstatus: completed\nkind: design\n---\n",
        encoding="utf-8",
    )

    detected = auto_detect_paired_design(
        "L4",
        project_root=tmp_path,
        prefer_status="draft",
        prefer_kind="design",
        weighted=True,
    )

    assert detected == "docs/plans/L9/L9-status-match-plan.md"


def test_extract_function_signatures_finds_python_def(tmp_path) -> None:
    """DoD 検証: W21 U-001 paired design doc から Python def を抽出する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        """# Sample Design

def my_function(arg1, arg2):
    return arg1 + arg2
""",
        encoding="utf-8",
    )

    signatures = extract_function_signatures(paired_design)

    assert signatures[0]["name"] == "my_function"
    assert "def my_function(arg1, arg2):" in signatures[0]["signature"]
    assert "return arg1 + arg2" in signatures[0]["context"]


def test_extract_function_signatures_truncates_at_max_count(tmp_path) -> None:
    """DoD 検証: W21 U-002 max_count を超える関数定義は truncate する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        "\n".join(f"def func_{chr(97 + index)}():" for index in range(10)),
        encoding="utf-8",
    )

    signatures = extract_function_signatures(paired_design, max_count=3)

    assert len(signatures) == 3


def test_generate_skeleton_with_extract_functions_includes_tc_per_function(tmp_path) -> None:
    """DoD 検証: W21 U-003 extract_functions=True で関数別 TC を展開する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        """# Sample Design

def first_case():
    return 1

def second_case():
    return 2
""",
        encoding="utf-8",
    )

    skeleton = generate_skeleton("L4", str(paired_design), extract_functions=True)

    assert "### TC-001: `first_case`" in skeleton
    assert "### TC-002: `second_case`" in skeleton
    assert "> signature: `def first_case():`" in skeleton


def test_extract_api_endpoints_finds_inline(tmp_path) -> None:
    """DoD 検証: W23 U-001 inline 記法の endpoint を抽出する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        """# Sample Design

API list:
GET /api/users
""",
        encoding="utf-8",
    )

    endpoints = extract_api_endpoints(paired_design)

    assert endpoints == [{"method": "GET", "path": "/api/users", "context": "API list:\nGET /api/users"}]


def test_extract_api_endpoints_finds_table_row(tmp_path) -> None:
    """DoD 検証: W23 U-002 markdown table row の endpoint を抽出する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        """# Sample Design

| Method | Path |
| POST | /api/orders |
""",
        encoding="utf-8",
    )

    endpoints = extract_api_endpoints(paired_design)

    assert endpoints[0]["method"] == "POST"
    assert endpoints[0]["path"] == "/api/orders"
    assert "| POST | /api/orders |" in endpoints[0]["context"]


def test_generate_skeleton_with_extract_endpoints_includes_tc_per_endpoint(tmp_path) -> None:
    """DoD 検証: W23 U-003 extract_endpoints=True で endpoint 別 TC を展開する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text(
        """# Sample Design

GET /api/users
POST /api/orders
""",
        encoding="utf-8",
    )

    skeleton = generate_skeleton("L4", str(paired_design), extract_endpoints=True)

    assert "### TC-API-001: `GET /api/users`" in skeleton
    assert "### TC-API-002: `POST /api/orders`" in skeleton
    assert "> endpoint: `GET /api/users`" in skeleton


def test_extract_openapi_endpoints_yaml(tmp_path) -> None:
    """DoD 検証: W24 U-001 OpenAPI YAML から endpoint を抽出する。"""
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        """openapi: 3.0.0
paths:
  /api/users:
    get:
      summary: List users
""",
        encoding="utf-8",
    )

    endpoints = extract_openapi_endpoints(spec_path)

    assert endpoints == [
        {
            "method": "GET",
            "path": "/api/users",
            "summary": "List users",
            "parameters": [],
            "responses": [],
            "request_body": "",
        }
    ]


def test_extract_openapi_endpoints_includes_parameters(tmp_path) -> None:
    """DoD 検証: W30 U-001 OpenAPI parameters の name 一覧を抽出する。"""
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        """openapi: 3.0.0
paths:
  /api/users/{id}:
    get:
      parameters:
        - name: id
          in: path
        - name: verbose
          in: query
""",
        encoding="utf-8",
    )

    endpoints = extract_openapi_endpoints(spec_path)

    assert [
        parameter["name"] if isinstance(parameter, dict) else parameter
        for parameter in endpoints[0]["parameters"]
    ] == ["id", "verbose"]


def test_extract_openapi_endpoints_parameter_includes_type(tmp_path) -> None:
    """DoD 検証: W31 U-001 OpenAPI parameter detail を type/required/example 付きで抽出する。"""
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        """openapi: 3.0.0
paths:
  /api/users:
    get:
      parameters:
        - name: x
          in: query
          required: true
          schema:
            type: string
          example: abc
""",
        encoding="utf-8",
    )

    endpoints = extract_openapi_endpoints(spec_path)

    assert endpoints[0]["parameters"] == [
        {
            "name": "x",
            "in": "query",
            "type": "string",
            "required": True,
            "example": "abc",
        }
    ]


def test_extract_openapi_endpoints_parameter_handles_missing_schema(tmp_path) -> None:
    """DoD 検証: W31 U-002 parameter schema/detail 不在時は default 値を返す。"""
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        """openapi: 3.0.0
paths:
  /api/users:
    get:
      parameters:
        - name: verbose
          in: query
""",
        encoding="utf-8",
    )

    endpoints = extract_openapi_endpoints(spec_path)

    assert endpoints[0]["parameters"] == [
        {
            "name": "verbose",
            "in": "query",
            "type": "unknown",
            "required": False,
            "example": "",
        }
    ]


def test_extract_openapi_endpoints_includes_responses(tmp_path) -> None:
    """DoD 検証: W30 U-002 OpenAPI responses の status code 一覧を抽出する。"""
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        """openapi: 3.0.0
paths:
  /api/users/{id}:
    get:
      responses:
        '200': {}
        '400': {}
""",
        encoding="utf-8",
    )

    endpoints = extract_openapi_endpoints(spec_path)

    assert endpoints[0]["responses"] == ["200", "400"]


def test_extract_openapi_endpoints_handles_missing_detail(tmp_path) -> None:
    """DoD 検証: W30 U-003 details 不在時は空 collection と空文字を返す。"""
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        """openapi: 3.0.0
paths:
  /api/users:
    get:
      summary: List users
""",
        encoding="utf-8",
    )

    endpoints = extract_openapi_endpoints(spec_path)

    assert endpoints[0]["parameters"] == []
    assert endpoints[0]["responses"] == []
    assert endpoints[0]["request_body"] == ""


def test_extract_openapi_endpoints_handles_missing_file(tmp_path) -> None:
    """DoD 検証: W24 U-002 OpenAPI spec 不在時は空 list を返す。"""
    missing_path = tmp_path / "missing-openapi.yaml"

    assert extract_openapi_endpoints(missing_path) == []


def test_generate_skeleton_with_openapi_spec_includes_endpoint_tc(tmp_path) -> None:
    """DoD 検証: W24 U-003 openapi_spec_path 指定で endpoint 別 TC を展開する。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text("# Sample Design\n", encoding="utf-8")
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text(
        """openapi: 3.0.0
paths:
  /api/users/{id}:
    get:
      summary: Get user
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        description: User payload
      responses:
        '200': {}
        '404': {}
""",
        encoding="utf-8",
    )

    skeleton = generate_skeleton("L4", str(paired_design), openapi_spec_path=spec_path)

    assert "### TC-OPENAPI-001: `GET /api/users/{id}`" in skeleton
    assert "> endpoint: `GET /api/users/{id}`" in skeleton
    assert "> summary: Get user" in skeleton
    assert "> parameters: id (string, required)" in skeleton
    assert "> responses: 200, 404" in skeleton
    assert "> request_body: User payload" in skeleton


def test_generate_skeleton_with_openapi_spec_parameter_backward_compat(monkeypatch, tmp_path) -> None:
    """DoD 検証: W31 U-003 skeleton は legacy str parameter entry も表示できる。"""
    paired_design = tmp_path / "paired-design.md"
    paired_design.write_text("# Sample Design\n", encoding="utf-8")
    spec_path = tmp_path / "openapi.yaml"
    spec_path.write_text("openapi: 3.0.0\npaths: {}\n", encoding="utf-8")

    monkeypatch.setattr(
        "cli.lib.test_design_scaffold.extract_openapi_endpoints",
        lambda *_args, **_kwargs: [
            {
                "method": "GET",
                "path": "/api/users/{id}",
                "summary": "Get user",
                "parameters": [
                    "id",
                    {
                        "name": "verbose",
                        "in": "query",
                        "type": "boolean",
                        "required": False,
                        "example": "",
                    },
                ],
                "responses": ["200"],
                "request_body": "",
            }
        ],
    )

    skeleton = generate_skeleton("L4", str(paired_design), openapi_spec_path=spec_path)

    assert "> parameters: id, verbose (boolean, optional)" in skeleton
