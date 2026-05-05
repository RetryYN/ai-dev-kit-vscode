import json
import py_compile
import sys
from pathlib import Path


LIB_DIR = Path(__file__).resolve().parents[1]
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import llm_guard


MODULE_PATH = LIB_DIR / "llm_guard.py"


def test_module_py_compile() -> None:
    py_compile.compile(str(MODULE_PATH), doraise=True)


def test_allows_helix_codex() -> None:
    assert llm_guard.inspect_command("helix codex --role se --task fix --approved").ok


def test_allows_helix_claude() -> None:
    assert llm_guard.inspect_command("helix claude --role se --task 'design it' --dry-run").ok


def test_blocks_direct_codex_exec() -> None:
    result = llm_guard.inspect_command("codex exec 'fix this'")

    assert result.ok is False
    assert "helix codex" in result.reason


def test_blocks_direct_claude_cli() -> None:
    result = llm_guard.inspect_command("claude --print 'fix this'")

    assert result.ok is False
    assert "helix claude" in result.reason


def test_blocks_codex_exec_with_global_options_and_alias() -> None:
    assert not llm_guard.inspect_command("codex -m gpt-5 exec unsafe").ok
    assert not llm_guard.inspect_command("codex --model=gpt-5 exec unsafe").ok
    assert not llm_guard.inspect_command("codex -c foo=bar exec unsafe").ok
    assert not llm_guard.inspect_command("codex --full-auto e unsafe").ok
    assert not llm_guard.inspect_command("codex -C /tmp exec unsafe").ok
    assert not llm_guard.inspect_command("codex --add-dir /tmp exec unsafe").ok
    assert not llm_guard.inspect_command("codex -a never exec unsafe").ok
    assert not llm_guard.inspect_command("codex --ask-for-approval never exec unsafe").ok


def test_blocks_codex_exec_split_by_shell_line_continuation() -> None:
    assert not llm_guard.inspect_command("codex \\\nexec unsafe").ok
    assert not llm_guard.inspect_command("codex \\\n--model gpt-5 exec unsafe").ok


def test_blocks_codex_exec_when_exec_is_quoted() -> None:
    assert not llm_guard.inspect_command('codex "exec" unsafe').ok
    assert not llm_guard.inspect_command("npx codex 'exec' unsafe").ok


def test_blocks_npx_codex_exec() -> None:
    assert not llm_guard.inspect_command("npx -y codex exec 'fix this'").ok
    assert not llm_guard.inspect_command("npx -y codex@latest exec unsafe").ok
    assert not llm_guard.inspect_command("npx -y codex -m gpt-5 e unsafe").ok


def test_blocks_npx_scoped_codex_package_exec() -> None:
    assert not llm_guard.inspect_command("npx -y @openai/codex@latest exec unsafe").ok
    assert not llm_guard.inspect_command("npx --package @openai/codex codex exec unsafe").ok
    assert not llm_guard.inspect_command("npx --node-options foo @openai/codex exec unsafe").ok


def test_blocks_package_runner_codex_exec() -> None:
    assert not llm_guard.inspect_command("pnpm dlx @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("pnpm dlx codex@latest exec unsafe").ok
    assert not llm_guard.inspect_command("pnpm dlx -q @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("pnpm dlx --package @openai/codex codex exec unsafe").ok
    assert not llm_guard.inspect_command("pnpm --silent dlx @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("pnpm --dir /tmp dlx @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("pnpm -C /tmp dlx @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("pnpm exec codex exec unsafe").ok
    assert not llm_guard.inspect_command("pnpm exec -- codex exec unsafe").ok
    assert not llm_guard.inspect_command("yarn dlx @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("yarn dlx --silent @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("yarn --silent dlx @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("yarn --cwd /tmp dlx @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("yarn exec codex exec unsafe").ok
    assert not llm_guard.inspect_command("yarn exec -- codex exec unsafe").ok
    assert not llm_guard.inspect_command("bunx @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("bunx --bun @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("bunx codex@latest exec unsafe").ok
    assert not llm_guard.inspect_command("uvx codex exec unsafe").ok
    assert not llm_guard.inspect_command("uvx @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("npm exec -- codex exec unsafe").ok
    assert not llm_guard.inspect_command("npm exec --package @openai/codex -- codex exec unsafe").ok
    assert not llm_guard.inspect_command("npm x @openai/codex exec unsafe").ok
    assert not llm_guard.inspect_command("corepack pnpm dlx @openai/codex exec unsafe").ok


def test_blocks_npx_call_script_codex_exec() -> None:
    assert not llm_guard.inspect_command("npx -p @openai/codex -c 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("npx -p @openai/codex -c codex exec unsafe").ok
    assert not llm_guard.inspect_command("npx --package @openai/codex --call 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("FOO=1 npx -p @openai/codex -c 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("npx -p @openai/codex -c 'codex exec unsafe && echo ok'").ok
    assert not llm_guard.inspect_command("FOO=1 npx -p @openai/codex -c 'codex exec unsafe && echo ok'").ok
    assert not llm_guard.inspect_command("env FOO=1 npx -p @openai/codex -c 'codex exec unsafe && echo ok'").ok


def test_blocks_env_and_command_wrapped_codex_exec() -> None:
    assert not llm_guard.inspect_command("env -u FOO codex exec unsafe").ok
    assert not llm_guard.inspect_command("env -S 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("env -S codex exec unsafe").ok
    assert not llm_guard.inspect_command("FOO=1 env -S 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("timeout 10s env codex exec unsafe").ok
    assert not llm_guard.inspect_command("command codex exec unsafe").ok
    assert not llm_guard.inspect_command("nice codex exec unsafe").ok
    assert not llm_guard.inspect_command("nohup codex exec unsafe").ok
    assert not llm_guard.inspect_command("nohup -- codex exec unsafe").ok
    assert not llm_guard.inspect_command("exec codex exec unsafe").ok
    assert not llm_guard.inspect_command("exec -a codex-alias codex exec unsafe").ok
    assert not llm_guard.inspect_command("sudo -u root codex exec unsafe").ok
    assert not llm_guard.inspect_command("sudo --user root codex exec unsafe").ok
    assert not llm_guard.inspect_command("time -o log codex exec unsafe").ok
    assert not llm_guard.inspect_command("/usr/bin/time -f '%E' codex exec unsafe").ok


def test_blocks_env_and_command_wrapped_claude_cli() -> None:
    assert not llm_guard.inspect_command("env -u FOO claude --print unsafe").ok
    assert not llm_guard.inspect_command("env -S 'claude --print unsafe'").ok
    assert not llm_guard.inspect_command("timeout 10s env claude --print unsafe").ok
    assert not llm_guard.inspect_command("command claude --print unsafe").ok
    assert not llm_guard.inspect_command("nice claude --print unsafe").ok
    assert not llm_guard.inspect_command("nohup claude --print unsafe").ok
    assert not llm_guard.inspect_command("exec claude --print unsafe").ok
    assert not llm_guard.inspect_command("sudo -u root claude --print unsafe").ok
    assert not llm_guard.inspect_command("time -o log claude --print unsafe").ok


def test_blocks_common_wrappers_around_raw_llm_binaries() -> None:
    assert not llm_guard.inspect_command("stdbuf -oL /usr/local/bin/codex exec unsafe").ok
    assert not llm_guard.inspect_command("flock /tmp/lock /usr/local/bin/codex exec unsafe").ok
    assert not llm_guard.inspect_command("ionice -c2 /usr/local/bin/codex exec unsafe").ok
    assert not llm_guard.inspect_command("chrt -i 0 /usr/local/bin/codex exec unsafe").ok
    assert not llm_guard.inspect_command("unbuffer /usr/local/bin/codex exec unsafe").ok
    assert not llm_guard.inspect_command("rlwrap /usr/local/bin/codex exec unsafe").ok
    assert not llm_guard.inspect_command("xvfb-run /usr/local/bin/codex exec unsafe").ok
    assert not llm_guard.inspect_command("stdbuf -oL /usr/local/bin/claude --print unsafe").ok
    assert not llm_guard.inspect_command("flock /tmp/lock /usr/local/bin/claude --print unsafe").ok
    assert not llm_guard.inspect_command("flock /tmp/lock -c 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("flock --command 'claude --print unsafe' /tmp/lock").ok


def test_blocks_package_runner_claude_cli() -> None:
    assert not llm_guard.inspect_command("pnpm dlx @anthropic-ai/claude-code --print unsafe").ok
    assert not llm_guard.inspect_command("pnpm --dir /tmp dlx @anthropic-ai/claude-code --print unsafe").ok
    assert not llm_guard.inspect_command("pnpm -C /tmp dlx @anthropic-ai/claude-code --print unsafe").ok
    assert not llm_guard.inspect_command("yarn dlx @anthropic-ai/claude-code --print unsafe").ok
    assert not llm_guard.inspect_command("yarn --cwd /tmp dlx @anthropic-ai/claude-code --print unsafe").ok


def test_blocks_dynamic_codex_path_invocation() -> None:
    assert not llm_guard.inspect_command("$(which codex) exec unsafe").ok
    assert not llm_guard.inspect_command("$(which codex) --model gpt-5 exec unsafe").ok
    assert not llm_guard.inspect_command("$(command -v codex) --full-auto e unsafe").ok
    assert not llm_guard.inspect_command('"$(type -P codex)" -C /tmp exec unsafe').ok
    assert not llm_guard.inspect_command("`which codex` exec unsafe").ok
    assert not llm_guard.inspect_command("`command -v codex` --model gpt-5 exec unsafe").ok
    assert not llm_guard.inspect_command('"`type -P codex`" -C /tmp exec unsafe').ok
    assert not llm_guard.inspect_command("C=$(which codex); $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=`which codex`; $C exec unsafe").ok
    assert not llm_guard.inspect_command("CODEX_BIN=`command -v codex`; ${CODEX_BIN} exec unsafe").ok
    assert not llm_guard.inspect_command("C=$(printf codex); $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=$(echo codex); $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=`printf codex`; $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=codex; $C --model gpt-5 exec unsafe").ok
    assert not llm_guard.inspect_command("C=codex; $C e unsafe").ok
    assert not llm_guard.inspect_command("C=co; C=${C}dex; $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=c; C+=odex; $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=c; C=$C'odex'; $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=codex; ${C:-foo} exec unsafe").ok
    assert not llm_guard.inspect_command("C=codex; ${C-default} exec unsafe").ok
    assert not llm_guard.inspect_command("CODEX_BIN=$(command -v codex); ${CODEX_BIN} exec unsafe").ok
    assert not llm_guard.inspect_command('C="codex"; $C exec unsafe').ok
    assert not llm_guard.inspect_command("C='codex'; $C exec unsafe").ok
    assert not llm_guard.inspect_command('C="$(command -v codex)"; $C exec unsafe').ok


def test_blocks_dynamic_claude_path_invocation() -> None:
    assert not llm_guard.inspect_command("$(which claude) --print unsafe").ok
    assert not llm_guard.inspect_command("$(command -v claude) --print unsafe").ok
    assert not llm_guard.inspect_command('"$(type -P claude)" --print unsafe').ok
    assert not llm_guard.inspect_command("`which claude` --print unsafe").ok
    assert not llm_guard.inspect_command("C=$(which claude); $C --print unsafe").ok
    assert not llm_guard.inspect_command("CLAUDE_BIN=`command -v claude`; ${CLAUDE_BIN} --print unsafe").ok
    assert not llm_guard.inspect_command("C=$(printf claude); $C --print unsafe").ok
    assert not llm_guard.inspect_command("C=claude; $C --print unsafe").ok
    assert not llm_guard.inspect_command("C=cl; C=${C}aude; $C --print unsafe").ok
    assert not llm_guard.inspect_command("C=cl; C+=aude; $C --print unsafe").ok
    assert not llm_guard.inspect_command('C="claude"; $C --print unsafe').ok


def test_blocks_array_expanded_raw_llm_invocations() -> None:
    assert not llm_guard.inspect_command('C=(codex exec unsafe); "${C[@]}"').ok
    assert not llm_guard.inspect_command("C=(/usr/local/bin/codex exec unsafe); ${C[@]}").ok
    assert not llm_guard.inspect_command("C=($(command -v codex) exec unsafe); ${C[@]}").ok
    assert not llm_guard.inspect_command("C=(codex); ${C[@]} exec unsafe").ok
    assert not llm_guard.inspect_command("C=(claude --print unsafe); ${C[@]}").ok
    assert not llm_guard.inspect_command('C=(/usr/local/bin/claude --print unsafe); "${C[@]}"').ok
    assert not llm_guard.inspect_command("C=($(command -v claude) --print unsafe); ${C[@]}").ok
    assert not llm_guard.inspect_command("C=(claude); ${C[0]} --print unsafe").ok


def test_blocks_variable_expanded_runner_commands() -> None:
    assert not llm_guard.inspect_command("C='codex exec unsafe'; bash -lc \"$C\"").ok
    assert not llm_guard.inspect_command("C='codex exec unsafe'; sh -c \"$C\"").ok
    assert not llm_guard.inspect_command("C='codex exec unsafe'; eval $C").ok
    assert not llm_guard.inspect_command("C='claude --print unsafe'; bash -lc \"$C\"").ok
    assert not llm_guard.inspect_command("C='claude --print unsafe'; eval $C").ok
    assert not llm_guard.inspect_command("C=('codex exec unsafe'); eval \"${C[0]}\"").ok
    assert not llm_guard.inspect_command("C=('claude --print unsafe'); bash -lc \"${C[0]}\"").ok


def test_blocks_expandable_codex_command_words() -> None:
    assert not llm_guard.inspect_command("EMPTY=; codex$EMPTY exec unsafe").ok
    assert not llm_guard.inspect_command("cod${EMPTY}ex exec unsafe").ok
    assert not llm_guard.inspect_command("codex${CODEX_SUFFIX} --model gpt-5 exec unsafe").ok
    assert not llm_guard.inspect_command("$(printf codex) exec unsafe").ok
    assert not llm_guard.inspect_command("$(printf co)dex exec unsafe").ok
    assert not llm_guard.inspect_command("co$(printf dex) exec unsafe").ok
    assert not llm_guard.inspect_command("cod$(printf e)x exec unsafe").ok
    assert not llm_guard.inspect_command("$(printf '%s' codex) --full-auto e unsafe").ok
    assert not llm_guard.inspect_command("`printf codex` exec unsafe").ok
    assert not llm_guard.inspect_command("C=co$(printf dex); $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=co; D=dex; $C$D exec unsafe").ok
    assert not llm_guard.inspect_command("C=/usr/local/bin/co; D=dex; $C$D exec unsafe").ok
    assert not llm_guard.inspect_command("C=co D=dex $C$D exec unsafe").ok
    assert not llm_guard.inspect_command("printf -v C %s codex; $C exec unsafe").ok
    assert not llm_guard.inspect_command("${CODEX_BIN} exec unsafe").ok


def test_blocks_expandable_codex_subcommands() -> None:
    assert not llm_guard.inspect_command("F=exec; codex $F unsafe").ok
    assert not llm_guard.inspect_command("F=ex; G=ec; codex $F$G unsafe").ok
    assert not llm_guard.inspect_command("codex ${F:-exec} unsafe").ok
    assert not llm_guard.inspect_command("codex $(printf exec) unsafe").ok
    assert not llm_guard.inspect_command("F=exec; npx @openai/codex $F unsafe").ok
    assert not llm_guard.inspect_command("F=e; npx @openai/codex $F unsafe").ok


def test_blocks_expandable_claude_command_words() -> None:
    assert not llm_guard.inspect_command("EMPTY=; claude$EMPTY --print unsafe").ok
    assert not llm_guard.inspect_command("clau${EMPTY}de --print unsafe").ok
    assert not llm_guard.inspect_command("claude${CLAUDE_SUFFIX} --print unsafe").ok
    assert not llm_guard.inspect_command("$(printf claude) --print unsafe").ok
    assert not llm_guard.inspect_command("$(printf clau)de --print unsafe").ok
    assert not llm_guard.inspect_command("clau$(printf de) --print unsafe").ok
    assert not llm_guard.inspect_command("C=clau; D=de; $C$D --print unsafe").ok
    assert not llm_guard.inspect_command("${CLAUDE_BIN} --print unsafe").ok


def test_blocks_codex_vars_inside_shell_wrappers() -> None:
    assert not llm_guard.inspect_command("export C=codex; bash -lc '$C exec unsafe'").ok
    assert not llm_guard.inspect_command("C=codex bash -lc '$C exec unsafe'").ok
    assert not llm_guard.inspect_command("C=co D=dex bash -lc '$C$D exec unsafe'").ok
    assert not llm_guard.inspect_command("export C=co D=dex; bash -lc '$C$D exec unsafe'").ok
    assert not llm_guard.inspect_command("C=codex; eval '$C exec unsafe'").ok
    assert not llm_guard.inspect_command("C=codex; env $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=codex; timeout 10 $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=codex; sudo $C exec unsafe").ok
    command = "export CODEX_BIN=$(which codex); bash -lc '$CODEX_BIN exec unsafe'"

    assert not llm_guard.inspect_command(command).ok


def test_blocks_claude_vars_inside_shell_wrappers() -> None:
    assert not llm_guard.inspect_command("export C=claude; bash -lc '$C --print unsafe'").ok
    assert not llm_guard.inspect_command("C=claude bash -lc '$C --print unsafe'").ok
    assert not llm_guard.inspect_command("C=clau D=de bash -lc '$C$D --print unsafe'").ok
    assert not llm_guard.inspect_command("export C=clau D=de; bash -lc '$C$D --print unsafe'").ok
    assert not llm_guard.inspect_command("C=claude; eval '$C --print unsafe'").ok
    assert not llm_guard.inspect_command("C=claude; env $C --print unsafe").ok
    assert not llm_guard.inspect_command("C=claude; sudo $C --print unsafe").ok
    command = "export CLAUDE_BIN=$(which claude); bash -lc '$CLAUDE_BIN --print unsafe'"

    assert not llm_guard.inspect_command(command).ok


def test_blocks_exec_style_shell_helpers() -> None:
    assert not llm_guard.inspect_command("xargs -I{} codex exec {}").ok
    assert not llm_guard.inspect_command("find . -name '*.py' -exec codex exec {} \\;").ok
    assert not llm_guard.inspect_command("find . -exec env codex exec unsafe \\;").ok
    assert not llm_guard.inspect_command("find . -exec command codex exec unsafe \\;").ok
    assert not llm_guard.inspect_command("find . -ok codex exec unsafe \\;").ok
    assert not llm_guard.inspect_command("find . -okdir claude --print unsafe \\;").ok
    assert not llm_guard.inspect_command("parallel -j 2 codex exec unsafe ::: input").ok
    assert not llm_guard.inspect_command("parallel --jobs 2 claude --print unsafe ::: input").ok
    assert not llm_guard.inspect_command("xargs -I{} claude --print {}").ok
    assert not llm_guard.inspect_command("find . -name '*.py' -exec claude --print {} \\;").ok
    assert not llm_guard.inspect_command("find . -exec env claude --print unsafe \\;").ok


def test_blocks_shell_control_wrapped_codex_exec() -> None:
    assert not llm_guard.inspect_command("(codex exec unsafe)").ok
    assert not llm_guard.inspect_command("{ codex exec unsafe; }").ok
    assert not llm_guard.inspect_command("if codex exec unsafe; then echo ok; fi").ok
    assert not llm_guard.inspect_command("if true; then codex exec unsafe; fi").ok
    assert not llm_guard.inspect_command("while codex exec unsafe; do echo ok; done").ok
    assert not llm_guard.inspect_command("while true; do codex exec unsafe; done").ok
    assert not llm_guard.inspect_command("until codex exec unsafe; do echo ok; done").ok
    assert not llm_guard.inspect_command("for item in x; do codex exec unsafe; done").ok
    assert not llm_guard.inspect_command("case x in x) codex exec unsafe;; esac").ok
    assert not llm_guard.inspect_command("coproc codex exec unsafe").ok
    assert not llm_guard.inspect_command("coproc RAW { codex exec unsafe; }").ok


def test_allows_direct_codex_with_inline_evidence() -> None:
    command = "HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=plugin-gap codex exec 'inspect'"

    assert llm_guard.inspect_command(command).ok


def test_allows_quoted_raw_codex_reason_with_inline_evidence() -> None:
    command = 'HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON="manual exception" codex exec unsafe'

    assert llm_guard.inspect_command(command).ok


def test_allows_shell_wrapped_codex_with_outer_inline_evidence() -> None:
    command = "HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=manual bash -lc 'codex exec unsafe'"

    assert llm_guard.inspect_command(command).ok


def test_outer_evidence_covers_only_one_nested_raw_codex_segment() -> None:
    command = "HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=manual bash -lc 'codex exec one; codex exec two'"

    assert not llm_guard.inspect_command(command).ok
    npx_command = "HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=manual npx -p @openai/codex -c 'codex exec one; codex exec two'"

    assert not llm_guard.inspect_command(npx_command).ok
    substitution_command = (
        'HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=manual bash -c "$(echo codex exec one; echo codex exec two)"'
    )

    assert not llm_guard.inspect_command(substitution_command).ok


def test_allows_shell_wrapped_codex_with_inner_inline_evidence() -> None:
    command = "bash -lc 'HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=manual codex exec unsafe'"

    assert llm_guard.inspect_command(command).ok


def test_allows_direct_claude_with_inline_evidence() -> None:
    command = "HELIX_ALLOW_RAW_CLAUDE=1 HELIX_RAW_CLAUDE_REASON=plugin-gap claude --print 'inspect'"

    assert llm_guard.inspect_command(command).ok


def test_allows_shell_wrapped_claude_with_outer_inline_evidence() -> None:
    command = "HELIX_ALLOW_RAW_CLAUDE=1 HELIX_RAW_CLAUDE_REASON=manual bash -lc 'claude --print unsafe'"

    assert llm_guard.inspect_command(command).ok


def test_outer_evidence_covers_only_one_nested_raw_claude_segment() -> None:
    command = "HELIX_ALLOW_RAW_CLAUDE=1 HELIX_RAW_CLAUDE_REASON=manual bash -lc 'claude --print one; claude --print two'"

    assert not llm_guard.inspect_command(command).ok


def test_allows_shell_wrapped_claude_with_inner_inline_evidence() -> None:
    command = "bash -lc 'HELIX_ALLOW_RAW_CLAUDE=1 HELIX_RAW_CLAUDE_REASON=manual claude --print unsafe'"

    assert llm_guard.inspect_command(command).ok


def test_does_not_block_searching_for_codex_exec_text() -> None:
    assert llm_guard.inspect_command("rg -n 'codex exec' docs cli").ok


def test_does_not_block_shell_wrapped_searching_for_codex_exec_text() -> None:
    assert llm_guard.inspect_command('bash -lc \'rg -n "codex exec" docs cli\'').ok


def test_does_not_block_safe_heredoc_examples() -> None:
    command = "cat >note <<'EOF'\ncodex exec unsafe\nEOF"

    assert llm_guard.inspect_command(command).ok


def test_blocks_command_substitution_in_unquoted_heredoc() -> None:
    command = "cat >note <<EOF\n$(codex exec unsafe)\nEOF"

    assert not llm_guard.inspect_command(command).ok


def test_blocks_shell_wrapped_codex_exec() -> None:
    assert not llm_guard.inspect_command('bash -lc "codex exec unsafe"').ok
    assert not llm_guard.inspect_command('dash -c "codex exec unsafe"').ok
    assert not llm_guard.inspect_command('zsh -c "codex exec unsafe"').ok
    assert not llm_guard.inspect_command('fish -c "codex exec unsafe"').ok


def test_blocks_shell_wrapped_claude_cli() -> None:
    assert not llm_guard.inspect_command('bash -lc "claude --print unsafe"').ok
    assert not llm_guard.inspect_command('dash -c "claude --print unsafe"').ok
    assert not llm_guard.inspect_command('zsh -c "claude --print unsafe"').ok
    assert not llm_guard.inspect_command('fish -c "claude --print unsafe"').ok


def test_blocks_eval_wrapped_codex_exec() -> None:
    assert not llm_guard.inspect_command("eval 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("eval 'codex exec unsafe; codex exec other'").ok
    assert not llm_guard.inspect_command("FOO=1 eval 'codex exec unsafe && echo ok'").ok
    assert not llm_guard.inspect_command('bash -lc "eval \'codex exec unsafe\'"').ok
    assert not llm_guard.inspect_command("builtin eval 'codex exec unsafe'").ok


def test_blocks_literal_stdout_rendered_as_executed_command() -> None:
    assert not llm_guard.inspect_command('bash -c "$(printf \'codex exec unsafe\')"').ok
    assert not llm_guard.inspect_command('bash -c "$(echo codex exec unsafe)"').ok
    assert not llm_guard.inspect_command("sh -c `echo 'codex exec unsafe'`").ok
    assert not llm_guard.inspect_command("eval $(echo codex exec unsafe)").ok
    assert not llm_guard.inspect_command("env -S $(echo codex exec unsafe)").ok
    assert not llm_guard.inspect_command("timeout 10 $(echo codex) exec unsafe").ok
    assert not llm_guard.inspect_command("sudo $(echo codex) exec unsafe").ok


def test_allows_literal_stdout_rendered_as_non_executing_text() -> None:
    assert llm_guard.inspect_command("echo $(echo codex exec unsafe)").ok
    assert llm_guard.inspect_command('bash -c "$(printf \'echo codex exec unsafe\')"').ok


def test_blocks_ansi_c_quoted_shell_bodies() -> None:
    assert not llm_guard.inspect_command("bash -lc $'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("eval $'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("$'codex' exec unsafe").ok
    assert not llm_guard.inspect_command("bash -lc $'codex\\040exec unsafe'").ok
    assert not llm_guard.inspect_command("co$'d'ex exec unsafe").ok
    assert not llm_guard.inspect_command("co$'\\x64'ex exec unsafe").ok
    assert not llm_guard.inspect_command("codex$'' exec unsafe").ok
    assert not llm_guard.inspect_command("npx co$'d'ex exec unsafe").ok
    assert not llm_guard.inspect_command("npx @openai/co$'d'ex exec unsafe").ok
    assert not llm_guard.inspect_command("npx @openai/codex$'' exec unsafe").ok
    assert not llm_guard.inspect_command("clau$'d'e --print unsafe").ok
    assert not llm_guard.inspect_command("claude$'' --print unsafe").ok
    assert not llm_guard.inspect_command("npx clau$'d'e --print unsafe").ok


def test_blocks_shell_heredoc_codex_exec() -> None:
    command = "bash <<'EOF'\ncodex exec unsafe\nEOF"

    assert not llm_guard.inspect_command(command).ok


def test_blocks_heredoc_piped_to_shell() -> None:
    command = "cat <<'EOF' | bash\ncodex exec unsafe\nEOF"

    assert not llm_guard.inspect_command(command).ok


def test_blocks_literal_raw_codex_piped_to_shell_stdin() -> None:
    assert not llm_guard.inspect_command("printf 'codex exec unsafe\\n' | bash").ok
    assert not llm_guard.inspect_command("printf '%s\\n' 'codex exec unsafe' | sh").ok
    assert not llm_guard.inspect_command("echo codex exec unsafe | bash").ok
    assert not llm_guard.inspect_command("bash -c 'echo codex exec unsafe | bash'").ok
    assert not llm_guard.inspect_command("printf 'codex %s unsafe\\n' exec | bash").ok
    assert not llm_guard.inspect_command("printf 'codex exec unsafe\\n' | cat | bash").ok
    assert not llm_guard.inspect_command("printf 'codex exec unsafe\\n' | tee /tmp/raw | bash").ok
    assert not llm_guard.inspect_command("printf 'codex exec unsafe\\n' | sed 's/x/x/' | sh").ok
    assert not llm_guard.inspect_command("echo codex exec unsafe |& bash").ok
    assert not llm_guard.inspect_command("printf 'codex exec unsafe\\n' |& bash").ok
    assert not llm_guard.inspect_command("printf 'coDEX exec unsafe\\n' | sed 's/DEX/dex/' | bash").ok
    assert not llm_guard.inspect_command("printf '%s ' codex exec unsafe | bash").ok
    assert not llm_guard.inspect_command("cat <<< 'codex exec unsafe' | bash").ok
    assert not llm_guard.inspect_command("cat <<< 'claude --print unsafe' | sh").ok
    assert not llm_guard.inspect_command("cat <<<$'codex exec unsafe' | bash").ok


def test_blocks_literal_raw_codex_piped_to_script_and_executed() -> None:
    assert not llm_guard.inspect_command("printf 'codex exec unsafe\\n' | tee /tmp/run >/dev/null; bash /tmp/run").ok
    assert not llm_guard.inspect_command("printf 'codex exec unsafe\\n' | cat > /tmp/run; bash /tmp/run").ok


def test_blocks_heredoc_written_to_script_and_executed() -> None:
    command = "cat >/tmp/run <<'EOF'\ncodex exec unsafe\nEOF\nbash /tmp/run"

    assert not llm_guard.inspect_command(command).ok
    assert not llm_guard.inspect_command("echo 'codex exec unsafe' > /tmp/run\nbash /tmp/run").ok
    assert not llm_guard.inspect_command("printf '%s ' codex exec unsafe > /tmp/run\nbash /tmp/run").ok
    assert not llm_guard.inspect_command("dd of=/tmp/run <<'EOF'\ncodex exec unsafe\nEOF\nbash /tmp/run").ok


def test_blocks_heredoc_written_to_directly_executed_script() -> None:
    command = "cat >/tmp/run <<'EOF'\ncodex exec unsafe\nEOF\nchmod +x /tmp/run\n/tmp/run"

    assert not llm_guard.inspect_command(command).ok


def test_blocks_heredoc_written_to_script_with_equivalent_relative_paths() -> None:
    assert not llm_guard.inspect_command("cat >run.sh <<'EOF'\ncodex exec unsafe\nEOF\nbash ./run.sh").ok
    assert not llm_guard.inspect_command("cat >./run.sh <<'EOF'\ncodex exec unsafe\nEOF\nbash run.sh").ok
    command = "cat >run.sh <<'EOF'\ncodex exec unsafe\nEOF\nchmod +x run.sh\n./run.sh"

    assert not llm_guard.inspect_command(command).ok


def test_blocks_heredoc_written_to_sourced_script() -> None:
    command = "cat >/tmp/run <<'EOF'\ncodex exec unsafe\nEOF\nsource /tmp/run"

    assert not llm_guard.inspect_command(command).ok


def test_blocks_heredoc_written_to_shell_input_redirection() -> None:
    command = "cat >/tmp/run <<'EOF'\ncodex exec unsafe\nEOF\nbash < /tmp/run"
    compact = "cat >/tmp/run <<'EOF'\ncodex exec unsafe\nEOF\nbash</tmp/run"

    assert not llm_guard.inspect_command(command).ok
    assert not llm_guard.inspect_command(compact).ok


def test_blocks_shell_wrapped_codex_exec_with_preceding_options() -> None:
    assert not llm_guard.inspect_command('bash -euo pipefail -c "codex exec unsafe"').ok
    assert not llm_guard.inspect_command('bash -c -- "codex exec unsafe"').ok
    assert not llm_guard.inspect_command("env --split-string=codex exec unsafe").ok


def test_blocks_timeout_wrapped_codex_exec_with_option_arguments() -> None:
    assert not llm_guard.inspect_command("timeout -k 5s 10s codex exec unsafe").ok
    assert not llm_guard.inspect_command("timeout --kill-after=5s 10s codex exec unsafe").ok


def test_blocks_raw_codex_inside_command_substitution() -> None:
    assert not llm_guard.inspect_command("OUT=$(codex exec unsafe)").ok
    assert not llm_guard.inspect_command("echo $(codex exec unsafe)").ok
    assert not llm_guard.inspect_command('echo "$(codex exec unsafe)"').ok
    assert not llm_guard.inspect_command("OUT=`codex exec unsafe`").ok


def test_blocks_raw_codex_inside_process_substitution() -> None:
    assert not llm_guard.inspect_command("cat <(codex exec unsafe)").ok
    assert not llm_guard.inspect_command("diff <(echo ok) <(codex exec unsafe)").ok
    assert not llm_guard.inspect_command("cat <(echo codex exec unsafe) | bash").ok
    assert not llm_guard.inspect_command("bash <(echo codex exec unsafe)").ok
    assert not llm_guard.inspect_command("bash < <(printf 'codex exec unsafe\\n')").ok
    assert not llm_guard.inspect_command("bash <<< 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("bash <<<$'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("bash<<<$'codex\\040exec unsafe'").ok
    assert not llm_guard.inspect_command("bash <<< codex\\ exec\\ unsafe").ok
    assert not llm_guard.inspect_command("source <(echo codex exec unsafe)").ok
    assert not llm_guard.inspect_command(". <(echo codex exec unsafe)").ok


def test_blocks_raw_codex_after_sed_transformed_stdin_to_shell() -> None:
    assert not llm_guard.inspect_command("printf 'coXex exec unsafe\\n' | sed 's/X/d/' | bash").ok
    assert not llm_guard.inspect_command("echo 'coXex exec unsafe' | sed 's/X/d/' | bash").ok
    assert not llm_guard.inspect_command("printf 'codex exXc unsafe\\n' | sed 's/X/e/' | bash").ok


def test_blocks_raw_codex_inside_here_string_command_substitution() -> None:
    assert not llm_guard.inspect_command("bash <<< $(printf 'codex exec unsafe')").ok
    assert not llm_guard.inspect_command("bash<<<$(printf 'codex\\040exec\\040unsafe')").ok
    assert not llm_guard.inspect_command("sh <<< `echo codex exec unsafe`").ok


def test_blocks_raw_codex_after_helix_codex_in_compound_command() -> None:
    assert not llm_guard.inspect_command("helix codex --role se --task ok --approved; codex exec unsafe").ok


def test_blocks_raw_codex_inside_shell_function_body() -> None:
    assert not llm_guard.inspect_command("f(){ codex exec unsafe; }; f").ok
    assert not llm_guard.inspect_command("function f { codex exec unsafe; }; f").ok
    assert not llm_guard.inspect_command("f() { codex exec unsafe; } && f").ok


def test_blocks_raw_codex_through_alias() -> None:
    assert not llm_guard.inspect_command("alias c=codex; c exec unsafe").ok
    assert not llm_guard.inspect_command("alias c='codex'; c --model gpt-5 exec unsafe").ok
    assert not llm_guard.inspect_command(
        "bash -lc \"shopt -s expand_aliases; alias c='codex --model gpt-5'; c exec unsafe\""
    ).ok
    assert not llm_guard.inspect_command("zsh -c \"alias c='codex --model gpt-5'; c exec unsafe\"").ok


def test_blocks_raw_codex_through_passthrough_function() -> None:
    assert not llm_guard.inspect_command('bash -lc \'c(){ codex "$@"; }; c exec unsafe\'').ok
    assert not llm_guard.inspect_command(
        'bash -lc \'function c { codex --model gpt "$@"; }; c exec unsafe\''
    ).ok
    assert not llm_guard.inspect_command('bash -lc \'f(){ "$@"; }; f codex exec unsafe\'').ok
    assert not llm_guard.inspect_command('bash -lc \'f(){ command "$@"; }; f codex exec unsafe\'').ok
    assert not llm_guard.inspect_command('bash -lc \'g(){ eval "$@"; }; g codex exec unsafe\'').ok


def test_blocks_raw_codex_through_xargs_placeholder() -> None:
    assert not llm_guard.inspect_command("printf %s codex | xargs -I{} {} exec unsafe").ok
    assert not llm_guard.inspect_command("echo codex | xargs --replace=CMD CMD exec unsafe").ok


def test_blocks_raw_codex_inside_language_eval_strings() -> None:
    assert not llm_guard.inspect_command("python3 -c \"import os; os.system('codex exec unsafe')\"").ok
    assert not llm_guard.inspect_command("python3 -c \"import os; os.system('codex e unsafe')\"").ok
    assert not llm_guard.inspect_command("python3 -c 'import os; os.system(\"co\"+\"dex exec unsafe\")'").ok
    assert not llm_guard.inspect_command("python3 -c 'import os; os.system(\"codex \"+\"exec unsafe\")'").ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess; subprocess.run(['codex','exec','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess; subprocess.run(['codex','e','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c 'import subprocess; subprocess.run([\"co\"+\"dex\",\"exec\",\"unsafe\"])'"
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c 'import subprocess; subprocess.run([\"co\" \"dex\",\"exec\",\"unsafe\"])'"
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c 'import subprocess; subprocess.run([\"codex\",\"ex\"+\"ec\",\"unsafe\"])'"
    ).ok
    assert not llm_guard.inspect_command("python3 -c 'import os; os.system(\"co\" \"dex exec unsafe\")'").ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess as s; s.run(['codex','exec','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"from subprocess import run; run(['codex','exec','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"from subprocess import run as r; r(['codex','exec','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import os; os.execvp('codex',['codex','exec','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import os; os.execlp('codex','codex','e','unsafe')\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c 'import os; os.spawnvp(os.P_WAIT, \"codex\", [\"codex\",\"exec\",\"unsafe\"])'"
    ).ok
    assert not llm_guard.inspect_command("node -e \"require('child_process').execSync('codex exec unsafe')\"").ok
    assert not llm_guard.inspect_command("node -e 'require(\"child_process\").execSync(\"co\"+\"dex exec unsafe\")'").ok
    assert not llm_guard.inspect_command("node -e \"require('child_process').execSync('codex e unsafe')\"").ok
    assert not llm_guard.inspect_command("perl -e \"system('codex exec unsafe')\"").ok
    assert not llm_guard.inspect_command("perl -e 'exec \"codex\", \"exec\", \"unsafe\"'").ok
    assert not llm_guard.inspect_command("php -r 'exec(\"codex exec unsafe\");'").ok
    assert not llm_guard.inspect_command("perl -e 'system(qq{codex exec unsafe})'").ok
    assert not llm_guard.inspect_command("ruby -e 'exec(\"codex\",\"exec\",\"unsafe\")'").ok
    assert not llm_guard.inspect_command("ruby -e 'system(%q{codex exec unsafe})'").ok


def test_allows_printed_raw_codex_examples_inside_eval_strings() -> None:
    assert llm_guard.inspect_command("python3 -c \"print('codex exec unsafe')\"").ok
    assert llm_guard.inspect_command("python3 -c \"import subprocess; print(['codex','exec','unsafe'])\"").ok
    assert llm_guard.inspect_command(
        "python3 -c \"import subprocess; run=['codex','exec','unsafe']; print(run)\""
    ).ok
    assert llm_guard.inspect_command("node -e \"console.log('codex exec unsafe')\"").ok
    assert llm_guard.inspect_command(
        "node -e \"const child_process = 'not used'; console.log('codex exec unsafe')\""
    ).ok
    assert llm_guard.inspect_command("ruby -e 'puts \"codex exec unsafe\"'").ok
    assert llm_guard.inspect_command("perl -e 'print \"codex exec unsafe\"'").ok
    assert llm_guard.inspect_command("php -r 'echo \"codex exec unsafe\";'").ok


def test_blocks_raw_claude_inside_language_eval_strings() -> None:
    assert not llm_guard.inspect_command("python3 -c \"import os; os.system('claude --print unsafe')\"").ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess; subprocess.run(['claude','--print','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"from subprocess import run as r; r(['claude','--print','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command("node -e \"require('child_process').execSync('claude --print unsafe')\"").ok
    assert not llm_guard.inspect_command("ruby -e 'system(\"claude --print unsafe\")'").ok


def test_blocks_obfuscated_process_calls_inside_language_eval_strings() -> None:
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess; getattr(subprocess,'run')(['codex','exec','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess; getattr(subprocess,'run')(['claude','--print','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess as s; getattr(s,'run')(['codex','exec','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess as s; getattr(s,'run')(['claude','--print','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command("python3 -c \"__import__('os').system('codex exec unsafe')\"").ok
    assert not llm_guard.inspect_command("python3 -c \"__import__('os').system('claude --print unsafe')\"").ok
    assert not llm_guard.inspect_command("python3 -c \"import os as o; getattr(o,'system')('codex exec unsafe')\"").ok
    assert not llm_guard.inspect_command("python3 -c \"import os as o; getattr(o,'system')('claude --print unsafe')\"").ok
    assert not llm_guard.inspect_command(
        "python3 -c \"from os import execvp as ex; ex('codex',['codex','exec','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"__import__('subprocess').run(['codex','exec','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"__import__('subprocess').run(['claude','--print','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import os; getattr(os,'system')('npx @openai/codex exec unsafe')\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import os; getattr(os,'system')('npx @anthropic-ai/claude-code --print unsafe')\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"getattr(__import__('subprocess'),'run')(['npx','@openai/codex','exec','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"getattr(__import__('subprocess'),'run')(['npx','@anthropic-ai/claude-code','--print','unsafe'])\""
    ).ok
    assert not llm_guard.inspect_command(
        "node -e \"require('child_process')['execSync']('codex exec unsafe')\""
    ).ok
    assert not llm_guard.inspect_command(
        "node -e \"require('child_process')['execSync']('claude --print unsafe')\""
    ).ok
    assert not llm_guard.inspect_command(
        "node -e \"require('node:child_process')['spawnSync']('claude',['--print','unsafe'])\""
    ).ok


def test_blocks_raw_codex_inside_interpreter_heredoc() -> None:
    command = "python3 - <<'PY'\nimport os\nos.system('codex exec unsafe')\nPY"
    piped = "cat <<'PY' | python3\nimport os\nos.system('codex exec unsafe')\nPY"
    subprocess_list = 'python3 - <<\'PY\'\nimport subprocess\nsubprocess.run(["codex", "exec", "unsafe"])\nPY'
    script_file = "cat >/tmp/run.py <<'PY'\nimport os\nos.system('codex exec unsafe')\nPY\npython3 /tmp/run.py"
    node_script_file = (
        "cat >/tmp/run.js <<'JS'\n"
        "require('child_process').execSync('codex exec unsafe')\n"
        "JS\nnode /tmp/run.js"
    )

    assert not llm_guard.inspect_command(command).ok
    assert not llm_guard.inspect_command(piped).ok
    assert not llm_guard.inspect_command(subprocess_list).ok
    assert not llm_guard.inspect_command(script_file).ok
    assert not llm_guard.inspect_command(node_script_file).ok


def test_blocks_eval_code_written_script_then_executed() -> None:
    command = "python3 -c \"open('/tmp/run','w').write('codex exec unsafe')\"; bash /tmp/run"
    node_command = (
        "node -e \"require('fs').writeFileSync('/tmp/run.sh','codex exec unsafe')\"; "
        "bash /tmp/run.sh"
    )
    claude_command = "python3 -c \"open('/tmp/run','w').write('claude --print unsafe')\"; bash /tmp/run"
    claude_node_command = (
        "node -e \"require('fs').writeFileSync('/tmp/run.sh','claude --print unsafe')\"; "
        "bash /tmp/run.sh"
    )

    assert not llm_guard.inspect_command(command).ok
    assert not llm_guard.inspect_command(node_command).ok
    assert not llm_guard.inspect_command(claude_command).ok
    assert not llm_guard.inspect_command(claude_node_command).ok


def test_blocks_script_watch_and_dd_generated_shell_execution() -> None:
    assert not llm_guard.inspect_command("script -q /dev/null -c 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("script -q /dev/null -c 'claude --print unsafe'").ok
    assert not llm_guard.inspect_command("script -e -c 'claude --print unsafe' /dev/null").ok
    assert not llm_guard.inspect_command("script --return -c 'codex exec unsafe' /dev/null").ok
    assert not llm_guard.inspect_command("script -f -c 'claude --print unsafe' /dev/null").ok
    assert not llm_guard.inspect_command("script --flush -c 'codex exec unsafe' /dev/null").ok
    assert not llm_guard.inspect_command("watch 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("watch -n 1 'claude --print unsafe'").ok
    assert not llm_guard.inspect_command("watch -d 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("watch --differences 'claude --print unsafe'").ok
    assert not llm_guard.inspect_command("watch -w 'codex exec unsafe'").ok
    assert not llm_guard.inspect_command("watch -r 'claude --print unsafe'").ok
    assert not llm_guard.inspect_command("printf 'codex exec unsafe\\n' | dd of=/tmp/run; bash /tmp/run").ok
    assert not llm_guard.inspect_command("printf 'claude --print unsafe\\n' | dd of=/tmp/run; bash /tmp/run").ok


def test_blocks_npx_call_equals_and_parallel_raw_codex() -> None:
    assert not llm_guard.inspect_command("npx --package @openai/codex --call=codex exec unsafe").ok
    assert not llm_guard.inspect_command("parallel codex exec ::: unsafe").ok


def test_blocks_package_runner_raw_codex_through_variable_command() -> None:
    assert not llm_guard.inspect_command("C=codex; npx -p @openai/codex $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=codex; npm exec $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=codex; pnpm dlx $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=codex; yarn dlx $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=codex; bunx $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=@openai/codex; npx $C exec unsafe").ok
    assert not llm_guard.inspect_command("C=codex@latest; npx $C exec unsafe").ok


def test_blocks_package_runner_raw_codex_through_alias_and_function() -> None:
    assert not llm_guard.inspect_command("alias c='npx -p @openai/codex codex'; c exec unsafe").ok
    assert not llm_guard.inspect_command("f(){ npx -p @openai/codex codex \"$@\"; }; f exec unsafe").ok


def test_blocks_shell_c_raw_codex_argv_passthrough() -> None:
    assert not llm_guard.inspect_command("bash -c 'codex \"$@\"' sh exec unsafe").ok
    assert not llm_guard.inspect_command("bash -c 'codex $*' sh exec unsafe").ok
    assert not llm_guard.inspect_command("bash -c 'C=codex; $C \"$@\"' sh exec unsafe").ok
    assert not llm_guard.inspect_command("sh -c 'exec codex \"$@\"' sh exec unsafe").ok


def test_blocks_python_eval_raw_codex_argv_passthrough() -> None:
    command = "python3 -c \"import subprocess,sys; subprocess.run(['codex']+sys.argv[1:])\" exec unsafe"

    assert not llm_guard.inspect_command(command).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess,sys; subprocess.run(sys.argv[1:])\" codex exec unsafe"
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess,sys; subprocess.run(sys.argv[1:])\" npx @openai/codex exec unsafe"
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import os,sys; os.execvp(sys.argv[1], sys.argv[1:])\" codex exec unsafe"
    ).ok


def test_blocks_python_eval_raw_claude_argv_passthrough() -> None:
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess,sys; subprocess.run(sys.argv[1:])\" claude --print unsafe"
    ).ok
    assert not llm_guard.inspect_command(
        "python3 -c \"import subprocess,sys; subprocess.run(sys.argv[1:])\" npx @anthropic-ai/claude-code --print unsafe"
    ).ok


def test_evidence_must_be_on_raw_codex_segment() -> None:
    command = "echo HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=x; codex exec unsafe"

    assert not llm_guard.inspect_command(command).ok


def test_outer_evidence_does_not_cover_argument_command_substitution() -> None:
    assert not llm_guard.inspect_command("HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=x echo $(codex exec unsafe)").ok
    assert not llm_guard.inspect_command(
        "HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=x echo $(npx @openai/codex exec unsafe)"
    ).ok


def test_outer_evidence_does_not_cover_later_compound_raw_codex() -> None:
    command = "HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=x bash -lc 'codex exec unsafe'; codex exec unsafe"

    assert not llm_guard.inspect_command(command).ok


def test_evidence_must_be_leading_assignment() -> None:
    assert not llm_guard.inspect_command("codex exec unsafe HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=x").ok
    assert not llm_guard.inspect_command("codex exec unsafe --arg HELIX_ALLOW_RAW_CODEX=1 HELIX_RAW_CODEX_REASON=x").ok


def test_evidence_must_not_come_from_inherited_environment(monkeypatch) -> None:
    monkeypatch.setenv("HELIX_ALLOW_RAW_CODEX", "1")
    monkeypatch.setenv("HELIX_RAW_CODEX_REASON", "stale")

    assert not llm_guard.inspect_command("codex exec unsafe").ok


def test_pretool_payload_deny_shape() -> None:
    payload = llm_guard.deny_payload("blocked")

    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert json.dumps(payload, ensure_ascii=False)
