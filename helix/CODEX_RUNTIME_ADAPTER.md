# Codex Runtime Adapter

この文書は Codex CLI 固有の実行差分を定義する。

Codex は独自 workflow ではない。Codex は `HELIX_CORE.md` と `HELIX_RUNTIME_RULES.md` に従い、この文書では Codex 固有の読み取り、編集、委譲、検証、報告の制約だけを扱う。

## 1. 位置づけ

- HELIX の概念は `helix/HELIX_CORE.md` を正とする。
- 共通実行規律は `helix/HELIX_RUNTIME_RULES.md` を正とする。
- この文書は Codex 固有の実行方法、sandbox、CLI shim、handover、出力制約だけを書く。
- Codex は HELIX の判断主体ではなく、HELIX の工程、PLAN、DB、gate に従う実行者である。

## 2. 実行前チェック

Codex は作業前に次を確認する。

- `helix/HELIX_CORE.md`
- `helix/HELIX_RUNTIME_RULES.md`
- `skills/SKILL_MAP.md`
- `HELIX-workflows/HELIX-process-L0-L14.md`
- HELIX DB / handover / PLAN から渡された注入セット
- `.helix/handover/CURRENT.md` / `.helix/task-plan.yaml` / 該当 PLAN の有無
- 変更対象ファイル

`skills/SKILL_MAP.md` は工程・ゲート・スキル一覧の索引として Core Read に含める。個別 `SKILL.md` 本文は常時一括読込しない。skill は DB の現在地、`vmodel-semantics`、`helix skill search` / recommender、または trigger に該当したものだけを必要分だけ注入する。

作業に入る前に、目的、現在の工程または workflow、Forward 接続先、合格基準・検証条件、作業正本、変更許可範囲を固定する。

実装を伴う場合は、コードを書く前に合格基準となるテストを置く。Discovery では、仮説、PoC、検証条件、採用 / 棄却基準を先に置く。

## 3. 編集規律

- 実装前に対象ファイルを読む。未読状態で修正しない。
- 既存の構造、命名、配置、テスト方式に合わせる。
- 手動編集は `apply_patch` を使う。
- 既存の未コミット変更はユーザーまたは他 agent の作業として扱い、勝手に戻さない。
- 計画、実装順、整理案を提示した後は、明示承認まで write 操作を行わない。
- 工程外の変更が必要になったら、勝手に実装せず `interrupted` / `blocked` として戻す。

文書を編集する場合は DDD の用語・境界を守る。`docs/v2/L0-helix-workflows/concept.md` §12 Glossary / §14 Bounded Context を参照し、Forward 正本 doc に他 context の固有語を未変換の定義語として持ち込まない。

## 4. Forward / Reverse / DB 収束

Codex は、成果物が Forward で正本化される接続先を常に確認する。

- 既存コード、既存実態、失敗事象から要件や設計へ戻す場合は Reverse を通す。
- HELIX 管理下の PLAN / handover / L 成果物が有効な場合は、その正本から Forward を継続する。
- workflow の成果は対応する PLAN として起票し、HELIX DB の V モデル DB へ収束する前提で扱う。
- trace / drift / detector の管理対象にならない成果を完了扱いしない。

## 5. `helix codex` Guard

Codex 実装委譲は原則 `helix codex` 経由にする。

- `--plan-only`: 計画・調査・整理系。write を許可しない。
- `--approved`: 明示承認済み実装として write 実行を許可する。
- `--consent auto`: 計画・整理・レビュー・調査系タスクを検出した場合、自動で plan-only guard をかける。
- `--plan-id` / `--task-id` / `--wbs-id` / `--acceptance` / `--reference-doc` / `--allowed-files`: 工程表文脈をプロンプトへ注入する。
- `HELIX_CODEX_REQUIRE_APPROVED=1`: write 実行に `--approved` を必須化する。
- `HELIX_CODEX_DESIGN_WEB_EVIDENCE=<path[:path...]>`: 設計 doc（`docs/adr/ADR-*.md`）変更時の WebSearch / WebFetch 証跡を post-validation に渡す。対象 doc 変更に証跡が無い場合は fail-close する。
- `cli/codex` shim: raw `codex exec` を捕捉し、`helix codex` へ誘導する。

raw `codex exec` が必要な場合だけ、`HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=<理由> codex exec ...` を使い、理由を evidence に残す。

## 6. Claude 呼び出し

Codex から Claude Code へ委譲する場合は、原則 `helix claude --dry-run` で prompt / task-file を生成する。

raw `claude` が必要な場合だけ、`HELIX_ALLOW_RAW_CLAUDE=1 HELIX_RAW_CLAUDE_REASON=<理由> claude ...` を使い、理由を evidence に残す。

## 7. Handover

`.helix/handover/CURRENT.json` が存在する場合は、handover protocol を優先する。

- stale なら作業を止めてユーザーへ戻す。
- stale でなければ owner を Codex に移し、Next Action に従う。
- Next Action にないファイルへの変更は事前確認する。
- D-API / D-DB / D-CONTRACT / schema / env / secret / 本番影響が必要なら escalate する。
- `helix handover clear` は実行しない。

## 8. Verification

完了前に変更種別に応じた検証を行う。

- Bash 変更: `bash -n`
- Python 変更: `python3 -m py_compile` または対象 pytest
- CLI routing / docs 変更: 対象 Bats または該当 lint
- 広い変更: 対象 pytest / Bats / `helix doctor` / `helix review`

実行できない検証は、理由と残リスクを final に明記する。

## 9. Final Report

必要に応じて以下を簡潔に返す。

```text
HELIX 適用結果
- scope:
- files_changed:
- verification:
- gates:
- evidence:
- risks:
```

テストを実行できなかった場合は、理由と残リスクを明記する。
