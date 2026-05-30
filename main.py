#!/usr/bin/env python3

import asyncio
import re
import sys

from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text

from midnight_style import MidnightStyle
from mcp_server import MCPCli
import subprocess

try:
    from rich.syntax import PygmentsSyntaxTheme
    _THEME = PygmentsSyntaxTheme(MidnightStyle)
except ImportError:
    _THEME = "monokai"

CODE_BG = "#181818"
CODE_FENCE = re.compile(r"```(\w*)\n?(.*?)```", re.DOTALL)
# Matches a fenced block, then inline backticks, then falls back to raw text
_CMD_FENCE  = re.compile(r"```(?:\w*)\n?(.*?)```", re.DOTALL)
_CMD_INLINE = re.compile(r"`([^`]+)`")
console = Console()


def extract_command(text: str) -> str:
    """Strip prose and fences, returning only the bare shell command."""
    m = _CMD_FENCE.search(text)
    if m:
        return m.group(1).strip()
    m = _CMD_INLINE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()

TASK_COLORS = {
    "shell_command":  "#50b0e0",
    "script":         "#a8cc8c",
    "create_file":    "#a8cc8c",
    "script_fix":     "#e8a87c",
    "debug_error":    "#fa4d56",
    "explain_output": "#c8b670",
}


def print_response(text: str) -> None:
    last = 0
    for m in CODE_FENCE.finditer(text):
        before = text[last : m.start()].strip()
        if before:
            console.print(Text(before, style=MidnightStyle.default_color))
        lang = m.group(1).strip() or "text"
        code = m.group(2).rstrip()
        console.print(
            Syntax(code, lang, theme=_THEME, background_color=CODE_BG, padding=(0, 1))
        )
        last = m.end()
    tail = text[last:].strip()
    if tail:
        console.print(Text(tail, style=MidnightStyle.default_color))


async def main() -> None:
    server = MCPCli()

    console.print(Text("OllamaCodeCompanion", style="#5579f0 bold"))
    console.print(Text(f"  orchestrator : {server.orchestrator}", style="#878d96"))
    console.print(Text(f"  executor     : {server.executor}", style="#878d96"))
    console.print(Text("Ctrl+C or Ctrl+D to quit\n", style="#878d96"))

    loop = asyncio.get_event_loop()

    while True:
        try:
            console.print(Text("You: ", style="#50b0e0 bold"), end="")
            prompt = await loop.run_in_executor(None, sys.stdin.readline)
        except (KeyboardInterrupt, EOFError):
            break

        prompt = prompt.strip()
        if not prompt:
            continue

        console.print(Text("  thinking…", style="#878d96"), end="\r")
        try:
            task_type, result = await server.dispatch(prompt)
        except Exception as exc:
            console.print(Text(f"Error: {exc}", style="#fa4d56"))
            continue

        color = TASK_COLORS.get(task_type, "#878d96")
        console.print(Text(f"[{task_type}] Ollama:", style=f"{color} bold"))

        print_response(result)
        if task_type == "shell_command":
            cmd = extract_command(result)
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.stdout:
                console.print(Text(res.stdout.rstrip(), style=MidnightStyle.default_color))
            if res.stderr:
                console.print(Text(res.stderr.rstrip(), style="#fa4d56"))
        console.print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
