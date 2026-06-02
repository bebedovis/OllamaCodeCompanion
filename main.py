#!/usr/bin/env python3

import asyncio
import os
import re
import sys

import httpx
from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text

from midnight_style import MidnightStyle
import subprocess

SERVER_URL = os.getenv("COMPANION_URL", "http://localhost:8000")
print(SERVER_URL)

try:
    from rich.syntax import PygmentsSyntaxTheme
    _THEME = PygmentsSyntaxTheme(MidnightStyle)
except ImportError:
    _THEME = "monokai"

CODE_BG = "#181818"
CODE_FENCE = re.compile(r"```(\w*)\n?(.*?)```", re.DOTALL)
_CMD_FENCE  = re.compile(r"```(?:\w*)\n?(.*?)```", re.DOTALL)
_CMD_INLINE = re.compile(r"`([^`]+)`")
_FILE_RE    = re.compile(r"(?<!\w)(\.{0,2}/[\w./-]+\.\w+|[\w/-]+\.\w{1,6})(?!\w)")
console = Console()


def inject_file_context(prompt: str) -> str:
    """Find file paths mentioned in the prompt and append their contents."""
    attachments = []
    for m in _FILE_RE.finditer(prompt):
        path = m.group(1)
        if os.path.isfile(path):
            try:
                content = open(path).read()
                attachments.append(f"### {path}\n```\n{content}\n```")
                console.print(Text(f"  attached: {path}", style="#878d96"))
            except OSError:
                pass
    if attachments:
        return prompt + "\n\n" + "\n\n".join(attachments)
    return prompt


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


async def dispatch(client: httpx.AsyncClient, prompt: str) -> tuple[str, str]:
    r = await client.post("/chat", json={"prompt": prompt}, timeout=300.0)
    r.raise_for_status()
    data = r.json()
    return data["task_type"], data["result"]


async def main() -> None:
    console.print(Text("OllamaCodeCompanion", style="#5579f0 bold"))
    console.print(Text(f"  server : {SERVER_URL}", style="#878d96"))
    console.print(Text("Ctrl+C or Ctrl+D to quit\n", style="#878d96"))

    loop = asyncio.get_event_loop()

    async with httpx.AsyncClient(base_url=SERVER_URL) as client:
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
            task_type, result = await dispatch(client, inject_file_context(prompt))
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
