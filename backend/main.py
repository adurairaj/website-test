import os
from typing import List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


app = FastAPI(title="FastAPI Chat Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")
    return OpenAI(api_key=api_key)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    if not payload.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    system_prompt = os.getenv(
        "SYSTEM_PROMPT",
        "You are a helpful assistant. Keep answers concise and practical.",
    )
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")

    input_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": message.role, "content": message.content} for message in payload.messages
    ]

    client = _get_client()
    try:
        response = client.responses.create(model=model, input=input_messages)
        reply = response.output_text
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM request failed: {exc}") from exc

    if not reply:
        raise HTTPException(status_code=500, detail="Model returned an empty response")

    return ChatResponse(reply=reply)
