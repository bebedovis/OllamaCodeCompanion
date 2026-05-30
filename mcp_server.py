#!/usr/bin/env python3

import json
import re
from typing import Any

from ollama import AsyncClient
from templates import (
    ORCHESTRATE_PROMPT,
    EXECUTOR_PROMPT_TEMPLATE,
    CREATE_SCRIPT_PROMPT_TEMPLATE,
    FIX_SCRIPT_PROMPT_TEMPLATE,
    DEBUG_ERROR_PROMPT_TEMPLATE,
)


class MCPCli:
    def __init__(self):
        self.orchestrator = "llama3:latest"
        self.executor = "qwen3-coder:30b"

    async def _chat(self, model: str, messages: list[dict], timeout: float = 120.0) -> str:
        client = AsyncClient(timeout=timeout)
        r = await client.chat(model=model, messages=messages)
        return r.message.content

    async def _orchestrate(self, user_query: str) -> dict[str, Any]:
        raw = await self._chat(self.orchestrator, [
            {"role": "system", "content": ORCHESTRATE_PROMPT},
            {"role": "user",   "content": user_query},
        ])
        print(raw)
        try:
            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
            if m:
                cleaned = m.group(1)
            else:
                start = raw.index("{")
                end = raw.rindex("}") + 1
                cleaned = raw[start:end]
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            print(f"Orchestrator output is not valid JSON:\n{raw}\nDefaulting to shell_command task.")
            return {
                "task_type": "shell_command",
                "language": "bash",
                "structured_prompt": user_query,
                "constraints": [],
            }

    async def _execute(self, task: dict[str, Any]) -> str:
        lang = task.get("language", "bash")
        constraints = task.get("constraints", [])
        constraint_note = f"\nConstraints: {', '.join(constraints)}" if constraints else ""
        system = EXECUTOR_PROMPT_TEMPLATE.format(language=lang, constraints=constraint_note)
        return await self._chat(self.executor, [
            {"role": "system", "content": system},
            {"role": "user",   "content": task["structured_prompt"]},
        ])

    async def dispatch(self, query: str) -> tuple[str, str]:
        task = await self._orchestrate(query)
        task_type = task.get("task_type", "shell_command")
        lang = task.get("language", "bash")
        constraints = task.get("constraints", [])
        constraint_note = f"\nConstraints: {', '.join(constraints)}" if constraints else ""

        print(f"Executing {task_type}")
        match task_type:
            case "explain_output":
                result = await self._chat(self.orchestrator, [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful Linux/CLI expert. "
                            "Explain clearly and concisely. Point out anything unusual."
                        ),
                    },
                    {"role": "user", "content": query},
                ])
                return task_type, result

            case "create_file":
                file_path = task.get("file_path")
                system = (
                    f"You are an expert {lang} programmer.\n"
                    "Output ONLY the raw file content — no shell commands, no heredocs, no markdown fences.\n"
                    f"{constraint_note}"
                )
                content = await self._chat(self.executor, [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": CREATE_SCRIPT_PROMPT_TEMPLATE.format(
                            language=lang,
                            description=task.get("structured_prompt", query),
                        ),
                    },
                ])
                if file_path:
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(content)
                        return task_type, f"Written to {file_path}\n\n{content}"
                    except OSError as e:
                        return task_type, f"Error writing to {file_path}: {e}\n\n{content}"
                return task_type, content

            case "script_fix":
                task["structured_prompt"] = FIX_SCRIPT_PROMPT_TEMPLATE.format(
                    language=lang,
                    description=task.get("structured_prompt", query),
                )

            case "debug_error":
                task["structured_prompt"] = DEBUG_ERROR_PROMPT_TEMPLATE.format(
                    error=query,
                    context=task.get("structured_prompt", ""),
                )

        result = await self._execute(task)

        file_path = task.get("file_path")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(result)
                return "create_file", f"Written to {file_path}\n\n{result}"
            except OSError as e:
                return task_type, f"Error writing to {file_path}: {e}\n\n{result}"

        return task_type, result
