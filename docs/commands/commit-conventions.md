# commit message ルール

PLAN-096 Sprint .2 の commitlint 検証を通すための Conventional Commits ルールです。
`CLAUDE.md` のコミット規約（`prefix` の 6 種＋`scope` 1つのドメイン名＋本文）と整合しています。

## ルール

- prefix: `feat`, `fix`, `chore`, `docs`, `test`, `refactor` のみ
- `scope`: 1 つ以上のドメインを同時に列挙せず、主要ドメイン 1 つを指定
- body の 1 行は **100 文字以内**
- subject は短く要約、変更意図を明確化

## prefix + scope + body 例

```text
feat(plan): add PLAN-096 commitlint automation

Add commitlint config, workflow, and documentation for PR commit
message validation.
```

```text
docs(plan): update Conventional Commit conventions document

Add scope list and template for PLAN-096 compliance.
Refs: PLAN-096
```

```text
chore(ci): pin commitlint toolchain for PR checks

Add node setup and npx commitlint execution in commitlint workflow.
```

```text
test(workflow): add minimal self-validation steps

Run package/json checks and formatting validations locally.
Refs: PLAN-096
```

```text
refactor(legacy): migrate old commit helper script to lint-first flow

Simplify message checks and remove unused script branch logic.
```

## 主要 scope 一覧

- `plan`
- `workflow`
- `ci`
- `docs`
- `cli`
- `hook`
- `skill`
- `pipeline`
- `db`
- `adr`
- `config`

## 文法

- 推奨フォーマット
  - `<type>(<scope>): <subject>`
  - body は任意だが、影響範囲・根拠を 1-3 行で記載推奨
- `scope` は `plan`, `workflow`, `ci`, `docs`, `cli`, `hook`, `skill`, `pipeline`, `db`, `adr`, `config` など 1 つ
- 破壊的変更や大規模影響がある場合は PR description へ追加情報を記載
