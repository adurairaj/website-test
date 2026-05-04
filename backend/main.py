import json
import os
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langgraph.graph import END, StateGraph
from openai import OpenAI
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


class DBIntentRequest(BaseModel):
    query: str = Field(..., min_length=1)


class DDLExtraction(BaseModel):
    entity_name: str
    attribute_name: str
    attribute_type: str
    attribute_length: Optional[str] = None


class ValidationExtraction(BaseModel):
    entity_name: str
    attribute_names: List[str]
    condition: str


class DBIntentResponse(BaseModel):
    intent: Literal["DB_DDL", "DB_VALIDATION", "UNKNOWN"]
    ddl_details: Optional[DDLExtraction] = None
    validation_details: Optional[ValidationExtraction] = None


class DBIntentState(BaseModel):
    query: str
    intent: Literal["DB_DDL", "DB_VALIDATION", "UNKNOWN"] = "UNKNOWN"
    ddl_details: Optional[DDLExtraction] = None
    validation_details: Optional[ValidationExtraction] = None


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


def _call_json_agent(prompt: str) -> Dict[str, Any]:
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")
    response = client.responses.create(
        model=model,
        input=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="Model did not return valid JSON") from exc


def classify_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state["query"]
    prompt = (
        "Classify this user query into one of: DB_DDL, DB_VALIDATION, UNKNOWN. "
        "Return JSON with only key 'intent'.\n"
        f"Query: {query}"
    )
    result = _call_json_agent(prompt)
    intent = result.get("intent", "UNKNOWN")
    if intent not in {"DB_DDL", "DB_VALIDATION", "UNKNOWN"}:
        intent = "UNKNOWN"
    return {"intent": intent}


def extract_ddl(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state["query"]
    prompt = (
        "Extract DDL details from the query. Return JSON keys: "
        "entity_name, attribute_name, attribute_type, attribute_length. "
        "If unknown, use null for attribute_length and empty string for other missing fields.\n"
        f"Query: {query}"
    )
    result = _call_json_agent(prompt)
    details = DDLExtraction(
        entity_name=result.get("entity_name", ""),
        attribute_name=result.get("attribute_name", ""),
        attribute_type=result.get("attribute_type", ""),
        attribute_length=result.get("attribute_length"),
    )
    return {"ddl_details": details}


def extract_validation(state: Dict[str, Any]) -> Dict[str, Any]:
    query = state["query"]
    prompt = (
        "Extract validation details from the query. Return JSON keys: "
        "entity_name, attribute_names (array), condition. "
        "If unknown, use empty values.\n"
        f"Query: {query}"
    )
    result = _call_json_agent(prompt)
    details = ValidationExtraction(
        entity_name=result.get("entity_name", ""),
        attribute_names=result.get("attribute_names", []),
        condition=result.get("condition", ""),
    )
    return {"validation_details": details}


def route_after_classify(state: Dict[str, Any]) -> str:
    return state.get("intent", "UNKNOWN")


def passthrough(_: Dict[str, Any]) -> Dict[str, Any]:
    return {}


def build_db_intent_graph():
    graph = StateGraph(dict)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("extract_ddl", extract_ddl)
    graph.add_node("extract_validation", extract_validation)
    graph.add_node("done", passthrough)

    graph.set_entry_point("classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        route_after_classify,
        {
            "DB_DDL": "extract_ddl",
            "DB_VALIDATION": "extract_validation",
            "UNKNOWN": "done",
        },
    )
    graph.add_edge("extract_ddl", END)
    graph.add_edge("extract_validation", END)
    graph.add_edge("done", END)

    return graph.compile()


db_intent_graph = build_db_intent_graph()


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


@app.post("/api/db-intent", response_model=DBIntentResponse)
def db_intent(payload: DBIntentRequest) -> DBIntentResponse:
    try:
        result = db_intent_graph.invoke({"query": payload.query})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB intent workflow failed: {exc}") from exc

    return DBIntentResponse(
        intent=result.get("intent", "UNKNOWN"),
        ddl_details=result.get("ddl_details"),
        validation_details=result.get("validation_details"),
    )
