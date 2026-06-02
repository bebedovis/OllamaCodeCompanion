#!/usr/bin/env python3

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from dispatcher import OllamaCodeCompanion

app = FastAPI(title="OllamaCodeCompanion")
_companion = OllamaCodeCompanion()


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    task_type: str
    result: str


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    task_type, result = await _companion.dispatch(req.prompt)
    return ChatResponse(task_type=task_type, result=result)

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
