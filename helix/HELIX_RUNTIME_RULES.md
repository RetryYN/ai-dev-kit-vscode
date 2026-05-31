# HELIX Runtime Rules

この文書は Claude Code / Codex CLI / HELIX CLI / subagent が共通で従う実行規律を定義する。

`HELIX_CORE.md` は HELIX の概念と機能単位の役割、`HELIX_RUNTIME_RULES.md` は実行時にその概念を守らせるための規律である。Claude と Codex の差分は各 runtime adapter に置く。

## 1. 実行前に固定するもの

作業に入る前に、次を固定する。

- 目的
- 現在の工程または workflow
- Forward で戻す接続先
- 合格基準・検証条件
- 作業正本
- 変更を許可された範囲

実装を伴う場合は TDD（テストファースト）を適用し、コードを書く前に合格基準となるテストを先に置く。Discovery では、仮説、PoC、検証条件、採用 / 棄却基準を先に置く。

## 2. 作業正本

実装・文書更新に入る前に、次の順で作業正本を確認する。

1. `.helix/handover/CURRENT.md` の Next Action
2. `.helix/task-plan.yaml`
3. `docs/plans/L*/` の該当 PLAN
4. 該当 workflow doc
5. 該当 L 成果物

上位の作業正本と矛盾する自己判断をしてはならない。

PLAN / handover / allowed_files がある場合は、それを作業正本にする。工程外の変更が必要になったら、勝手に進めず interrupted / blocked として戻す。

## 3. Forward / Reverse

すべての成果は Forward V モデルで正本化する。

Forward は要求・設計から実装・検証へ降ろすトップダウンの正本処理である。Reverse は既存コード・既存実態・失敗事象から要件・設計・契約を復元し、Forward へ戻すボトムアップの復元処理である。

既存コード、既存実態、失敗事象から要件や設計へ戻す場合は Reverse を通す。HELIX 管理下の PLAN / handover / L 成果物が有効な場合は、Reverse に入り直さず、その正本から Forward を継続する。

## 4. Workflow

Forward 以外の workflow は、正本化前の事象を受け止める枝葉循環として扱う。

| workflow | 実行時の扱い |
|---|---|
| Reverse | 既存コード・既存実態・失敗事象を復元し、Forward へ戻す |
| Discovery | 仮説、PoC、検証条件、採用 / 棄却基準を先に置き、confirmed を Forward へ昇格する |
| Scrum | 反復で要件をすり合わせ、完成機能を Forward へ接続する |
| Add-feature | 既存正本に差分機能を追補し、要求・設計・テスト・実装へ反映する |
| Refactor | 振る舞い不変を保護し、構造改善を Forward の該当工程へ戻す |
| Retrofit | 既存成果物を現行正本構造へ合わせ直す |
| Incident | 障害を止血し、恒久対策と postmortem を Forward / DB へ戻す |
| Recovery | AI 暴走、工程逸脱、認識ズレを収束し、再開点を Forward / DB へ戻す |
| Research | 調査結果を ADR / PLAN / Forward へ接続する |

どの workflow で進んでも、Forward 接続先と HELIX DB への収束先を持たないまま完了してはならない。

## 5. ドキュメント設計

ドキュメントは DDD の考え方で進める。

- 文書の配置、参照方向、常時注入 / 詳細注入の判断は `HELIX-workflows/helix-process/document-topology.md` を正とする。
- ユビキタス言語は `docs/v2/L0-helix-workflows/concept.md` §12 Glossary を SSoT とする。
- Bounded Context は同 doc §14 Bounded Context を正とする。
- 他 context の固有用語を Forward 正本 doc に未変換のまま定義語として持ち込まない。
- 境界を越える場合は anti-corruption layer として Glossary 経由で意味を写像する。
- 各 L のドキュメントは、上位の用語・境界・要求へ接続する。

## 6. HELIX DB 収束

HELIX DB は、V モデル DB（正本）と workflow 補助 state を持つ。

workflow の成果は、対応する PLAN として起票し、closure event で補助 state を V モデル DB に統合する。個別領域の作業で終わらせず、Forward の成果物と同じ整合管理に収束させる。

実行時は次を確認する。

- PLAN / docs / code / test / coverage の対応があるか。
- contract / command / skill の変更が登録対象になるか。
- trace / drift / detector の管理対象になるか。
- DB 検出が必要な異常を見つけた場合、Reverse / Recovery / Incident / Refactor などへ routing できるか。

## 7. Plan Consent

AI がユーザーに計画、実装順、整理案、リセット方針を提示した場合、明示承認があるまで write 操作を行わない。

明示承認の例:

- `OK`
- `進めて`
- `実装して`
- `それで`
- `やって`
- `apply`
- `proceed`

読み取り専用の調査、検索、状態確認、テスト実行は承認前でも実行してよい。

## 8. Harness

Claude / Codex / team / subagent は HELIX harness 経由で扱う。

- Codex 実行: `helix codex`
- Claude prompt 生成: `helix claude --dry-run`
- 複数 role: `helix team`
- 差分レビュー: `helix review`
- 引継ぎ: `helix handover`
- ルーティング: `helix route`
- V モデル確認: `helix vmodel`

raw LLM CLI を使う場合は、理由と代替不能性を evidence に残す。

## 9. Review / Verification

完了前に、変更種別に応じた検証を行う。

- Bash 変更: `bash -n`
- Python 変更: `python3 -m py_compile` または対象 pytest
- CLI routing / docs 変更: 対象 Bats または該当 lint
- 広い変更: 対象 pytest / Bats / `helix doctor` / `helix review`

実行できない検証は、理由と残リスクを final に明記する。

## 10. Escalation

以下は自己判断で確定しない。

- 本番影響
- 認証 / 認可
- 決済
- PII
- secret / credential / env
- license
- schema migration
- destructive data operation
- 外部 API / infrastructure 変更
- handover / PLAN / allowed_files と矛盾する変更

該当する場合は作業を止め、人間に確認する。

## 11. Evidence

final report には、必要に応じて以下を簡潔に含める。

```text
scope:
files_changed:
commands_used:
verification:
gates:
risks:
```

## 12. Tool Adapter

共通原則をツール固有の制約へ落とす文書:

- `helix/CODEX_RUNTIME_ADAPTER.md`
- `helix/CLAUDE_RUNTIME_ADAPTER.md`

Adapter は HELIX の概念を再定義しない。実行方法、hook、sandbox、CLI shim、出力制約などの差分だけを書く。
