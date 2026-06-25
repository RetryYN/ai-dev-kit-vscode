from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    pass


class PlanKind(StrEnum):
    IMPL = "impl"
    DESIGN = "design"
    POC = "poc"
    REVERSE = "reverse"
    ADD_DESIGN = "add-design"
    ADD_IMPL = "add-impl"
    REFACTOR = "refactor"
    RETROFIT = "retrofit"
    RECOVERY = "recovery"
    TROUBLESHOOT = "troubleshoot"
    RESEARCH = "research"


class ArtifactType(StrEnum):
    CHARTER = "charter"
    DESIGN_DOC = "design_doc"
    MARKDOWN_DOC = "markdown_doc"
    ADR_SNAPSHOT = "adr_snapshot"
    PYTHON_MODULE = "python_module"
    TEST = "test"
    CLI_EXTENSION = "cli_extension"
    BASH_SCRIPT = "bash_script"
    TEMPLATE = "template"
    YAML_CONFIG = "yaml_config"
    CONFIG = "config"
    SCRIPT = "script"
    HOOK = "hook"
    SKILL = "skill"
    COMMAND_DOC = "command_doc"
    RUNBOOK = "runbook"
    GITHUB_WORKFLOW = "github_workflow"
    GITHUB_CONFIG = "github_config"
    WORKFLOW_CONFIG = "workflow_config"


class Layer(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    L6 = "L6"
    L7 = "L7"
    L8 = "L8"
    L9 = "L9"
    L10 = "L10"
    L11 = "L11"
    L12 = "L12"
    L13 = "L13"
    L14 = "L14"
    CROSS = "cross"


V_MODEL_PAIRS = (
    (Layer.L1.value, Layer.L14.value),
    (Layer.L2.value, Layer.L10.value),
    (Layer.L3.value, Layer.L12.value),
    (Layer.L4.value, Layer.L9.value),
    (Layer.L5.value, Layer.L8.value),
    (Layer.L6.value, Layer.L7.value),
)


VALID_SUB_DOCS = {
    Layer.L1.value: (
        "business-requirements",
        "functional-requirements",
        "non-functional-requirements",
        "glossary",
        "screen",
    ),
    Layer.L2.value: ("screen-list", "screen-flow", "ui-element", "wireframe"),
    Layer.L3.value: ("business-detail", "functional-registry", "nfr-grade", "screen-functional"),
    Layer.L4.value: (
        "architecture",
        "data",
        "function",
        "external-if",
        "ui-standard",
        "tokens",
        "security",
        "workflow",
        "test-strategy",
    ),
    Layer.L5.value: ("if-detail", "internal-processing", "data-contract", "schema", "ui-detail"),
    Layer.L6.value: ("schema-registry", "projection-writer", "detector-wiring", "screen-spec"),
}


class Drive(StrEnum):
    BE = "be"
    FE = "fe"
    FULLSTACK = "fullstack"
    DB = "db"
    AGENT = "agent"


class Status(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Role(StrEnum):
    PO = "po"
    TL = "tl"
    QA = "qa"
    AIM = "aim"
    UIUX = "uiux"
    SE = "se"
    DOCS = "docs"


class WorkflowPhase(StrEnum):
    S0 = "S0"
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"


class DecisionOutcome(StrEnum):
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    PIVOT = "pivot"


class ReverseType(StrEnum):
    CODE = "code"
    DESIGN = "design"
    UPGRADE = "upgrade"
    NORMALIZATION = "normalization"
    FULLBACK = "fullback"


class ForwardRouting(StrEnum):
    L1 = "L1"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    GAP_ONLY = "gap-only"


class PromotionStrategy(StrEnum):
    REUSE_AS_IS = "reuse-as-is"
    WITH_HARDENING = "with-hardening"
    REDESIGN = "redesign"
    DISCARD = "discard"


class OrchestrationMode(StrEnum):
    PM_LEAD = "pm_lead"
    CLAUDE_JUDGE = "claude_judge"
    CLAUDE_JUDGE_CODEX_IMPL = "claude_judge_codex_impl"
    CODEX_IMPL_QA_VERIFY = "codex_impl_qa_verify"
    CLAUDE_DESIGN_IMPL = "claude_design_impl"
