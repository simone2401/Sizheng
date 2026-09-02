from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContentItem(BaseModel):
    type: Literal["TEXT"]
    text: str = Field(min_length=1)


class ChatMessage(BaseModel):
    role: Literal["USER", "ASSISTANT"]
    content: list[ContentItem] = Field(min_length=1)


class TeachingMetadata(BaseModel):
    chat_type: Literal["case_guide_study", "lesson_plan_assist"] = Field(alias="chatType")
    school_level: str = Field(alias="schoolLevel", min_length=1)
    subject: str = Field(min_length=1)
    textbook_version: str = Field(alias="textbookVersion", min_length=1)
    chapter: str = Field(min_length=1)
    lesson: str = Field(min_length=1)
    knowledge_points: list[str] | None = Field(default=None, alias="knowledgePoints")
    original_lesson_plan: str | None = Field(default=None, alias="originalLessonPlan")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class TeachingChatRequest(BaseModel):
    model: str | None = None
    stream: bool = True
    request_id: str | None = Field(default=None, alias="requestId")
    conversation_id: str | None = Field(default=None, alias="conversationId")
    turn_id: int = Field(alias="turnId", ge=1)
    messages: list[ChatMessage] = Field(min_length=1)
    metadata: TeachingMetadata
    reasoning_content: str | None = Field(default=None, alias="reasoning_content")
    lesson_plan_markdown: str | None = Field(default=None, alias="lessonPlanMarkdown")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    @field_validator("messages")
    @classmethod
    def last_message_must_be_user(cls, value: list[ChatMessage]) -> list[ChatMessage]:
        if value[-1].role != "USER":
            raise ValueError("last message must have role USER")
        return value


class Usage(BaseModel):
    input_tokens: int = Field(alias="inputTokens", ge=0)
    output_tokens: int = Field(alias="outputTokens", ge=0)
    total_tokens: int = Field(alias="totalTokens", ge=0)

    model_config = ConfigDict(populate_by_name=True)


class ErrorInfo(BaseModel):
    code: str
    message: str
    retriable: bool


class TeachingResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    conversation_id: str = Field(alias="conversationId")
    turn_id: int = Field(alias="turnId")
    model: str | None
    l1_labels: list[str] = Field(default_factory=list, alias="l1_labels")
    reasoning_content: str = Field(default="", alias="reasoning_content")
    content: str = ""
    finish_reason: Literal["stop", "error"] | None = Field(default=None, alias="finishReason")
    usage: Usage | None = None
    error: ErrorInfo | None = None

    model_config = ConfigDict(populate_by_name=True)
