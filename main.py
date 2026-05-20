#!/usr/bin/env python3

import asyncio
import json
import re
import sys
from typing import AsyncIterator

import httpx
from rich.console import Console
from rich.live import Live
from rich.syntax import Syntax
from rich.text import Text

from midnight_style import MidnightStyle

try:
    from rich.syntax import PygmentsSyntaxTheme
    _THEME = PygmentsSyntaxTheme(MidnightStyle)
except ImportError:
    _THEME = "monokai"

OLLAMA_BASE = "http://localhost:11434"
CODE_BG = "#181818"
CODE_FENCE = re.compile(r"```(\w*)\n?(.*?)```", re.DOTALL)

console = Console()


async def fetch_models() -> list[str]:
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{OLLAMA_BASE}/api/tags", timeout=5.0)
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []


async def stream_chat(model: str, messages: list[dict]) -> AsyncIterator[str]:
    payload = {"model": model, "messages": messages, "stream": True}
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST", f"{OLLAMA_BASE}/api/chat", json=payload
        ) as resp:
            async for line in resp.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if content := data.get("message", {}).get("content", ""):
                        yield content
                    if data.get("done"):
                        return
                except json.JSONDecodeError:
                    continue


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
    models = await fetch_models()
    if not models:
        console.print(
            Text(
                "Cannot reach Ollama at localhost:11434 — is it running?",
                style="#fa4d56",
            )
        )
        sys.exit(1)

    model = models[0]
    console.print(Text("OllamaCodeCompanion", style="#5579f0 bold"))
    console.print(Text(f"Model: {model}", style="#878d96"))
    console.print(Text("Ctrl+C or Ctrl+D to quit\n", style="#878d96"))

    messages: list[dict] = []
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

        messages.append({"role": "user", "content": prompt})
        buf = ""

        try:
            with Live(
                Text("▌", style="#c8b670"),
                console=console,
                refresh_per_second=15,
                transient=True,
            ) as live:
                async for chunk in stream_chat(model, messages):
                    buf += chunk
                    tail = buf[-300:] if len(buf) > 300 else buf
                    live.update(Text(f"{tail}▌", style="#b5bdc5"))
        except httpx.ConnectError:
            console.print(Text("Error: Cannot connect to Ollama.", style="#fa4d56"))
            messages.pop()
            continue
        except Exception as exc:
            console.print(Text(f"Error: {exc}", style="#fa4d56"))
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": buf})
        console.print(Text("Ollama:", style="#c8b670 bold"))
        print_response(buf)
        console.print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
