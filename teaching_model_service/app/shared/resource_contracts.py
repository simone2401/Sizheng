from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ResourceQuery(BaseModel):
    school_level: str = Field(alias="schoolLevel", min_length=1)
    subject: str = Field(min_length=1)
    textbook_version: str = Field(alias="textbookVersion", min_length=1)
    chapter: str = Field(min_length=1)
    lesson: str = Field(min_length=1)
    knowledge_points: list[str] | None = Field(default=None, alias="knowledgePoints")
    ideology_ids: list[str] | None = Field(default=None, alias="ideologyIDs")
    model_config = ConfigDict(populate_by_name=True)


class ResourceResponse(BaseModel):
    data_version: str = Field(alias="dataVersion")
    textbook: dict[str, Any]
    chapter: dict[str, Any]
    section: dict[str, Any]
    knowledge_points: list[dict[str, Any]] = Field(alias="knowledgePoints")
    textbook_chunks: list[dict[str, Any]] = Field(alias="textbookChunks")
    curriculum_standards: list[dict[str, Any]] = Field(alias="curriculumStandards")
    ideology_paragraphs: list[dict[str, Any]] = Field(alias="ideologyParagraphs")
    ideology_tags: dict[str, list[dict[str, Any]]] = Field(alias="ideologyTags")
    model_config = ConfigDict(populate_by_name=True)


class StaticIdeologyItem(BaseModel):
    ideology_id: str = Field(alias="ideologyID")
    source_page: int = Field(alias="sourcePage")
    ideology_keyword: str = Field(alias="ideologyKeyword")
    l1_label: str = Field(alias="l1_label")
    model_config = ConfigDict(populate_by_name=True)


class StaticIdeologyResponse(BaseModel):
    items: list[StaticIdeologyItem]
    model_config = ConfigDict(populate_by_name=True)
