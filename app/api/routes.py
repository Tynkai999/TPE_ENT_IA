from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.agent import run_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class Source(BaseModel):
    source: Optional[str] = None
    page: Optional[int] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    answer, sources = run_agent(request.message)
    return ChatResponse(answer=answer, sources=sources)
