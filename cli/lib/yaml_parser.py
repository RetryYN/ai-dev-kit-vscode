#!/usr/bin/env python3
"""Lightweight YAML parser — PyYAML 不要。
責務: HELIX の phase/state YAML の読み書き（状態管理）を安全に行う。
helix CLI の phase.yaml 読み書き専用。完全な YAML パーサーではない。

Usage:
  python3 yaml_parser.py read <file> <dotpath>        # 値を読む
  python3 yaml_parser.py write <file> <dotpath> <val>  # 値を書く
  python3 yaml_parser.py dump <file>                   # JSON で出力

Examples:
  python3 yaml_parser.py read phase.yaml gates.G2.status
  python3 yaml_parser.py write phase.yaml gates.G2.status passed
  python3 yaml_parser.py write phase.yaml sprint.current_step .1a
"""

import sys
import os
import json
import re
import fcntl
from pathlib import Path


def parse_yaml(text):
    """簡易 YAML パーサー。ネスト対応（インデントベース）。"""
    result = {}
    stack = [(result, -1)]  # (current_dict, indent_level)

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if not stripped or stripped.startswith('#'):
            continue

        indent = len(line) - len(stripped)

        # スタックを巻き戻し
        while len(stack) > 1 and stack[-1][1] >= indent:
            stack.pop()

        current = stack[-1][0]

        # key: value パターン
        m = re.match(r'^(["\']?[\w.\-]+["\']?)\s*:\s*(.*)', stripped)
        if not m:
            if stripped.startswith('- '):
                continue
            raise ValueError(f"Unsupported YAML syntax at line {lineno}: {stripped}")

        key = m.group(1).strip("'\"")
        raw_val = m.group(2).strip()

        if not raw_val:
            # サブキーが来る → 新しい dict
            new_dict = {}
            if isinstance(current, dict):
                current[key] = new_dict
            stack.append((new_dict, indent))
        elif raw_val.startswith('{') and raw_val.endswith('}'):
            # インライン dict: { status: pending, date: 2026-03-30 }
            inner = raw_val[1:-1].strip()
            d = {}
            for pair in inner.split(','):
                pair = pair.strip()
                if ':' in pair:
                    k, v = pair.split(':', 1)
                    d[k.strip()] = _cast(v.strip())
            if isinstance(current, dict):
                current[key] = d
        else:
            if isinstance(current, dict):
                current[key] = _cast(raw_val)

    return result


def _cast(val):
    """文字列を適切な型にキャスト。"""
    if val in ('null', 'None', '~', ''):
        return None
    if val in ('true', 'True'):
        return True
    if val in ('false', 'False'):
        return False
    val = val.strip("'\"")
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass
    return val


def _split_dotpath(data, dotpath):
    """ドットパスを分割。`G1.5` のようにキー自体に `.` を含む場合、既存キーを優先する。"""
    parts = []
    remaining = dotpath
    current = data
    while remaining:
        # まず完全一致を試す（残り全体がキー）
        if isinstance(current, dict) and remaining in current:
            parts.append(remaining)
            return parts
        # 最長一致: ドット位置を逆順（最長プレフィックスから）試す
        found = False
        dot_positions = [i for i, c in enumerate(remaining) if c == '.']
        for pos in reversed(dot_positions):
            candidate = remaining[:pos]
            if isinstance(current, dict) and candidate in current:
                parts.append(candidate)
                current = current[candidate]
                remaining = remaining[pos + 1:]
                found = True
                break
        if not found:
            # ドットがないか、どのプレフィックスもマッチしない → 残り全体をキーとする
            parts.append(remaining)
            return parts
    return parts


def get_nested(data, dotpath):
    """ドットパスで値を取得。キーに `.` を含む場合も対応。"""
    keys = _split_dotpath(data, dotpath)
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def set_nested(data, dotpath, value):
    """ドットパスで値を設定。キーに `.` を含む場合も対応。新規キーはドット分割で作成。"""
    # set では既存キーの貪欲マッチ + 新規キーのドット分割を組み合わせる
    parts = []
    remaining = dotpath
    current = data
    while remaining:
        if isinstance(current, dict) and remaining in current:
            parts.append(remaining)
            break
        found = False
        dot_positions = [i for i, c in enumerate(remaining) if c == '.']
        for pos in dot_positions:
            candidate = remaining[:pos]
            if isinstance(current, dict) and candidate in current:
                parts.append(candidate)
                current = current[candidate]
                remaining = remaining[pos + 1:]
                found = True
                break
        if not found:
            # 既存キーにマッチしない → ドットで単純分割
            rest_parts = remaining.split('.')
            parts.extend(rest_parts)
            break

    current = data
    for key in parts[:-1]:
        if key not in current or not isinstance(current.get(key), dict):
            current[key] = {}
        current = current[key]
    current[parts[-1]] = _cast(str(value)) if not isinstance(value, dict) else value


def dump_yaml(data, indent=0):
    """dict を YAML 文字列に変換。"""
    lines = []
    prefix = '  ' * indent
    for key, val in data.items():
        if isinstance(val, dict):
            # インラインか展開か判断
            if all(not isinstance(v, dict) for v in val.values()) and len(val) <= 3:
                # インライン
                inner = ', '.join(
                    f'{k}: {_serialize(v)}' for k, v in val.items()
                )
                lines.append(f'{prefix}{key}: {{ {inner} }}')
            else:
                lines.append(f'{prefix}{key}:')
                lines.append(dump_yaml(val, indent + 1))
        else:
            lines.append(f'{prefix}{key}: {_serialize(val)}')
    return '\n'.join(lines)


def _serialize(val):
    if val is None:
        return 'null'
    if isinstance(val, bool):
        return 'true' if val else 'false'
    if isinstance(val, str):
        if ' ' in val or val.startswith('.') or val in ('null', 'true', 'false'):
            return f'"{val}"'
        return val
    return str(val)


def _build_output_with_header(text, data):
    """ヘッダーコメントを保持した YAML 出力を作る。"""
    header = []
    for line in text.splitlines():
        if line.startswith('#'):
            header.append(line)
        else:
            break
    header_text = '\n'.join(header)
    body = dump_yaml(data)
    if header_text:
        return header_text + '\n\n' + body + '\n'
    return body + '\n'


def write_yaml_safe(filepath, dotpath, value):
    """排他ロック + atomic rename で YAML を安全に更新する。"""
    lock_path = filepath + ".lock"
    with open(lock_path, 'w', encoding='utf-8') as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            text = Path(filepath).read_text(encoding='utf-8')
            data = parse_yaml(text)
            set_nested(data, dotpath, value)
            output = _build_output_with_header(text, data)
            tmp_path = f"{filepath}.tmp.{os.getpid()}"
            Path(tmp_path).write_text(output, encoding='utf-8')
            os.replace(tmp_path, filepath)
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
    try:
        os.unlink(lock_path)
    except OSError:
        pass


def main():
    if len(sys.argv) < 3:
        print("Usage: yaml_parser.py <read|write|dump> <file> [dotpath] [value]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    filepath = sys.argv[2]

    if cmd == 'dump':
        text = Path(filepath).read_text(encoding='utf-8')
        data = parse_yaml(text)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif cmd == 'read':
        if len(sys.argv) < 4:
            print("Usage: yaml_parser.py read <file> <dotpath>", file=sys.stderr)
            sys.exit(1)
        try:
            text = Path(filepath).read_text(encoding='utf-8')
            data = parse_yaml(text)
        except Exception as e:
            print(f"エラー: YAML 解析失敗 — {e}", file=sys.stderr)
            sys.exit(1)
        dotpath = sys.argv[3]
        val = get_nested(data, dotpath)
        if isinstance(val, dict):
            print(json.dumps(val, ensure_ascii=False))
        elif val is not None:
            print(val)
    elif cmd == 'write':
        if len(sys.argv) < 5:
            print("Usage: yaml_parser.py write <file> <dotpath> <value>", file=sys.stderr)
            sys.exit(1)
        dotpath = sys.argv[3]
        value = sys.argv[4]
        write_yaml_safe(filepath, dotpath, value)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
