#!/usr/bin/env python3
"""review_report.py

6段階コードレビューの指摘を集計し、Approve判断付きのMarkdownレポートを生成する。

入力(JSON): レビュー指摘のリスト。各指摘は以下の形式。
    {
      "stage": 4,                      # 1-6 (Format/Lint/Style/Logic/Design/Architecture)
      "file": "src/api/users.py",      # 対象ファイル(任意)
      "line": 42,                       # 行番号(任意)
      "severity": "blocking",          # blocking | recommended | optional | hint | warning
      "message": "空配列のとき処理をスキップする仕様だが、処理してしまう",
      "spec_checked": true             # 仕様書と照合済みか(Stage4で使用, 任意)
    }

「AIが指摘しなかった箇所(逆説ルールの対象)」を表現したい場合は、
severity="warning" かつ stage=4 で message に未確認領域を記載する。

使い方:
    python review_report.py findings.json
    python review_report.py findings.json --spec-available
    cat findings.json | python review_report.py -
    python review_report.py findings.json -o report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from typing import Any

STAGE_NAMES: dict[int, str] = {
    1: "Format",
    2: "Lint",
    3: "Style",
    4: "Logic",
    5: "Design",
    6: "Architecture",
}

# 各段階のAI比率(目安。定量基準ではない)
STAGE_AI_RATIO: dict[int, str] = {
    1: "100%",
    2: "100%",
    3: "90%",
    4: "60%",
    5: "30%",
    6: "0%",
}

SEVERITY_ORDER: dict[str, int] = {
    "blocking": 0,
    "warning": 1,
    "recommended": 2,
    "hint": 3,
    "optional": 4,
}

SEVERITY_LABEL: dict[str, str] = {
    "blocking": "ブロッキング",
    "warning": "要確認",
    "recommended": "採用推奨",
    "hint": "ヒント",
    "optional": "任意",
}


@dataclass
class Finding:
    stage: int
    message: str
    file: str | None = None
    line: int | None = None
    severity: str = "recommended"
    spec_checked: bool = False

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Finding":
        stage = int(raw.get("stage", 0))
        if stage not in STAGE_NAMES:
            raise ValueError(f"stage は 1-6 で指定してください: {stage!r}")
        severity = str(raw.get("severity", "recommended")).lower()
        if severity not in SEVERITY_ORDER:
            raise ValueError(f"未知の severity: {severity!r}")
        return cls(
            stage=stage,
            message=str(raw.get("message", "")).strip(),
            file=raw.get("file"),
            line=raw.get("line"),
            severity=severity,
            spec_checked=bool(raw.get("spec_checked", False)),
        )

    def location(self) -> str:
        if self.file and self.line:
            return f"{self.file}:{self.line}"
        if self.file:
            return self.file
        return "-"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    spec_available: bool = False

    def by_stage(self, stage: int) -> list[Finding]:
        items = [f for f in self.findings if f.stage == stage]
        return sorted(items, key=lambda f: SEVERITY_ORDER[f.severity])

    def count(self, severity: str) -> int:
        return sum(1 for f in self.findings if f.severity == severity)

    def approve_recommendation(self) -> str:
        """Approve判断を返す。

        - blocking が1件でもあれば「保留」
        - Stage4で仕様未照合の指摘 or 仕様書がない場合は「条件付き」
        - それ以外は「Approve可」
        """
        if self.count("blocking") > 0:
            return "保留（ブロッキング指摘を解消してから再判断）"

        logic_unverified = any(
            f.stage == 4 and not f.spec_checked for f in self.findings
        )
        if not self.spec_available:
            return "条件付き（仕様書未確認。Logic層の仕様由来エッジケースは未検証）"
        if logic_unverified:
            return "条件付き（Logic層に仕様未照合の指摘あり。仕様書と照合してから）"
        return "Approve可"


def render(report: Report) -> str:
    lines: list[str] = []
    lines.append("## 6段階コードレビュー結果")
    lines.append("")

    # --- サマリ ---
    lines.append("### サマリ")
    lines.append("")
    lines.append(f"- ブロッキング指摘: {report.count('blocking')}件")
    lines.append(f"- 要確認: {report.count('warning')}件")
    lines.append(
        f"- 採用推奨: {report.count('recommended')}件 / "
        f"ヒント: {report.count('hint')}件 / 任意: {report.count('optional')}件"
    )
    spec_text = "あり" if report.spec_available else "なし（仕様由来エッジケース未検証）"
    lines.append(f"- 仕様書: {spec_text}")
    lines.append("")

    # --- 段階別 ---
    for stage in range(1, 7):
        items = report.by_stage(stage)
        if not items:
            continue
        name = STAGE_NAMES[stage]
        ratio = STAGE_AI_RATIO[stage]
        suffix = " ★最重要" if stage == 4 else ""
        lines.append(f"### Stage {stage}: {name}（AI比率 目安 {ratio}）{suffix}")
        lines.append("")
        for f in items:
            label = SEVERITY_LABEL[f.severity]
            loc = f.location()
            spec_mark = ""
            if stage == 4 and f.severity != "warning":
                spec_mark = " [仕様照合済]" if f.spec_checked else " [仕様未照合]"
            lines.append(f"- **[{label}]** `{loc}`{spec_mark} — {f.message}")
        lines.append("")

    # --- 逆説ルールの注意喚起 ---
    logic_warnings = [
        f for f in report.findings if f.stage == 4 and f.severity == "warning"
    ]
    if logic_warnings:
        lines.append("### ⚠️ 逆説ルール: AI指摘が薄い/ゼロの領域（人間が念入りに見る）")
        lines.append("")
        lines.append(
            "AIのコメントが少ない箇所こそ、仕様書を開いて確認する価値がある。"
            "以下は重点確認対象。"
        )
        lines.append("")
        for f in logic_warnings:
            lines.append(f"- `{f.location()}` — {f.message}")
        lines.append("")

    # --- Approve判断 ---
    lines.append("### Approve判断")
    lines.append("")
    checklist = [
        "Stage 1-2 自動ゲート通過",
        "Stage 3 Style 指摘に対応 or 却下理由を記録",
        "Stage 4 Logic を仕様書と照合（AI指摘ゼロ箇所を含む）",
        "Stage 5 Design の責務分割に合意",
        "Stage 6 Architecture が事前ADRと整合",
    ]
    for item in checklist:
        lines.append(f"- [ ] {item}")
    lines.append("")
    lines.append(f"**推奨: {report.approve_recommendation()}**")
    lines.append("")

    return "\n".join(lines)


def load_input(path: str) -> list[dict[str, Any]]:
    if path == "-":
        data = json.load(sys.stdin)
    else:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    if isinstance(data, dict) and "findings" in data:
        return data["findings"]
    if isinstance(data, list):
        return data
    raise ValueError("入力は指摘のリスト、または {\"findings\": [...]} 形式で渡してください")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="6段階コードレビューの指摘を集計しMarkdownレポートを生成する"
    )
    parser.add_argument("input", help="指摘のJSONファイルパス（'-' で標準入力）")
    parser.add_argument(
        "--spec-available",
        action="store_true",
        help="仕様書と照合できる状態であることを示す（Approve判断に影響）",
    )
    parser.add_argument(
        "-o", "--output", help="出力先Markdownファイル（省略時は標準出力）"
    )
    args = parser.parse_args(argv)

    try:
        raw_findings = load_input(args.input)
        findings = [Finding.from_dict(r) for r in raw_findings]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    report = Report(findings=findings, spec_available=args.spec_available)
    markdown = render(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        print(f"レポートを書き出しました: {args.output}", file=sys.stderr)
    else:
        print(markdown)

    # ブロッキング指摘がある場合は非ゼロで終了（CIゲート用）
    return 2 if report.count("blocking") > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
