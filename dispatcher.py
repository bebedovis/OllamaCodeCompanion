#!/usr/bin/env python3

import json
import re
from typing import Any

import os 
from ollama import AsyncClient
from templates import (
    ORCHESTRATE_PROMPT,
    EXECUTOR_PROMPT_TEMPLATE,
    CREATE_SCRIPT_PROMPT_TEMPLATE,
    FIX_SCRIPT_PROMPT_TEMPLATE,
    DEBUG_ERROR_PROMPT_TEMPLATE,
)


class OllamaCodeCompanion:
    def __init__(self):
        self.orchestrator = os.getenv("ORCHESTRATOR_MODEL","llama3:latest")
        self.executor = os.getenv("EXECUTOR_MODEL","qwen3-coder:30b")
        self.history = [{}]

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
        self.history.append({"role": "user", "content": query})
        task = await self._orchestrate(query)
        task.setdefault("structured_prompt", query)
        task_type = task.get("task_type", "shell_command")
        lang = task.get("language", "bash")
        constraints = task.get("constraints", [])
        constraint_note = f"\nConstraints: {', '.join(constraints)}" if constraints else ""
        # Last 10 interactions
        history = self.history[-10:]
        history_str = "\n".join(h["role"] + ": "+h["content"] for h in history if h.get("content"))

        query = history_str + "\n\nUser query: " + query

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
                self.history.append({"role": "assistant", "content": result})
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
                self.history.append({"role": "assistant", "content": content})
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

        self.history.append({"role": "assistant", "content": result})

        return task_type, result
