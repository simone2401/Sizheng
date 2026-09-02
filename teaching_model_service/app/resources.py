from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class ResourceNotFound(Exception):
    pass


class InvalidResourceQuery(Exception):
    pass


class JSONRepository:
    def __init__(self, resource_dir: str | Path | None = None) -> None:
        default_dir = Path(__file__).resolve().parents[2] / "json_output" / "PEP8U_PHYSICS"
        self.resource_dir = Path(resource_dir or os.getenv("TEACHING_RESOURCE_DIR", default_dir))
        with (self.resource_dir / "entities.json").open(encoding="utf-8") as file:
            self.entities: dict[str, Any] = json.load(file)
        with (self.resource_dir / "relations.json").open(encoding="utf-8") as file:
            self.relations: dict[str, list[dict[str, str]]] = json.load(file)
        with (self.resource_dir / "summary.json").open(encoding="utf-8") as file:
            self.summary: dict[str, Any] = json.load(file)
        self.textbook = self.entities["textbook"][0]
        self.chapters = {item["chapter_id"]: item for item in self.entities["chapters"]}
        self.sections = {item["section_id"]: item for item in self.entities["sections"]}
        self.knowledge_points = {item["knowledge_point_id"]: item for item in self.entities["knowledge_points"]}
        self.chunks = {item["chunk_id"]: item for item in self.entities["textbook_chunks"]}
        self.standards = {item["standard_item_id"]: item for item in self.entities["curriculum_standards"]}
        self.paragraphs = {item["paragraph_id"]: item for item in self.entities["ideology_paragraphs"]}
        tags = self.entities["ideology_tags"]
        self.tags = {item["l3_code"]: item for item in tags["level_3"]}
        self.l2_tags = {item["l2_code"]: item for item in tags["level_2"]}
        self.l1_tags = {item["l1_code"]: item for item in tags["level_1"]}


class ResourceQueryService:
    def __init__(self, repository: JSONRepository | None = None) -> None:
        self.repo = repository or JSONRepository()

    @staticmethod
    def _matches(value: str, query: str) -> bool:
        return value == query or query in value

    def query(
        self,
        school_level: str,
        subject: str,
        textbook_version: str,
        chapter: str,
        lesson: str,
        knowledge_points: list[str] | None = None,
    ) -> dict[str, Any]:
        textbook = self.repo.textbook
        if any(textbook[key] != value for key, value in {
            "school_level": school_level,
            "subject": subject,
            "textbook_version": textbook_version,
        }.items()):
            raise ResourceNotFound("textbook not found")
        chapter_item = next((item for item in self.repo.chapters.values() if self._matches(item["chapter_id"], chapter) or self._matches(item["chapter_title"], chapter)), None)
        if chapter_item is None:
            raise ResourceNotFound("chapter not found")
        section_item = next((item for item in self.repo.sections.values() if item["chapter_id"] == chapter_item["chapter_id"] and (self._matches(item["section_id"], lesson) or self._matches(item["section_title"], lesson))), None)
        if section_item is None:
            raise ResourceNotFound("lesson not found")
        section_id = section_item["section_id"]
        selected_kps = [item for item in self.repo.knowledge_points.values() if item["section_id"] == section_id]
        if knowledge_points:
            requested = set(knowledge_points)
            selected_kps = [item for item in selected_kps if item["knowledge_point_id"] in requested or item["title"] in requested]
            if len(selected_kps) != len(requested):
                raise ResourceNotFound("knowledge point not found in lesson")
        chunks = [item for item in self.repo.chunks.values() if item["section_id"] == section_id]
        standards = [item for item in self.repo.standards.values() if item["section_id"] == section_id]
        paragraphs = [item for item in self.repo.paragraphs.values() if item["section_id"] == section_id]
        ideology_tags = self._tags_for(paragraphs)
        return {
            "dataVersion": self.repo.summary.get("source_file", "unknown"),
            "textbook": textbook,
            "chapter": chapter_item,
            "section": section_item,
            "knowledgePoints": selected_kps,
            "textbookChunks": chunks,
            "curriculumStandards": standards,
            "ideologyParagraphs": paragraphs,
            "ideologyTags": ideology_tags,
        }

    def _tags_for(self, paragraphs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        paragraph_ids = {item["paragraph_id"] for item in paragraphs}
        codes = {edge["l3_code"] for edge in self.repo.relations["paragraph_tagged_with_l3"] if edge["paragraph_id"] in paragraph_ids}
        l3 = [self.repo.tags[code] for code in codes if code in self.repo.tags]
        l2_codes = {item["l2_code"] for item in l3}
        l1_codes = {item["l1_code"] for item in self.repo.l2_tags.values() if item["l2_code"] in l2_codes}
        return {
            "level1": [self.repo.l1_tags[code] for code in l1_codes],
            "level2": [self.repo.l2_tags[code] for code in l2_codes],
            "level3": l3,
        }
