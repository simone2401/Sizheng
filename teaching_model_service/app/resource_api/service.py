from __future__ import annotations
from typing import Any
from app.shared.errors import ResourceNotFoundError
from app.shared.resource_contracts import ResourceQuery, ResourceResponse
from .repository import ResourceRepository


class ResourceService:
    def __init__(self, repository: ResourceRepository) -> None:
        self.repo = repository

    @staticmethod
    def _matches(value: str, query: str) -> bool:
        return value == query or query in value

    def query(self, query: ResourceQuery) -> ResourceResponse:
        tb = self.repo.textbook
        if any(tb[k] != v for k, v in {"school_level": query.school_level, "subject": query.subject, "textbook_version": query.textbook_version}.items()):
            raise ResourceNotFoundError("textbook not found")
        chapter = next((x for x in self.repo.chapters.values() if self._matches(x["chapter_id"], query.chapter) or self._matches(x["chapter_title"], query.chapter)), None)
        if chapter is None: raise ResourceNotFoundError("chapter not found")
        section = next((x for x in self.repo.sections.values() if x["chapter_id"] == chapter["chapter_id"] and (self._matches(x["section_id"], query.lesson) or self._matches(x["section_title"], query.lesson))), None)
        if section is None: raise ResourceNotFoundError("lesson not found")
        sid = section["section_id"]
        kps = [x for x in self.repo.knowledge_points.values() if x["section_id"] == sid]
        if query.knowledge_points:
            requested = set(query.knowledge_points)
            kps = [x for x in kps if x["knowledge_point_id"] in requested or x["title"] in requested]
            if len(kps) != len(requested): raise ResourceNotFoundError("knowledge point not found in lesson")
        paragraphs = [x for x in self.repo.paragraphs.values() if x["section_id"] == sid]
        return ResourceResponse(dataVersion=self.repo.summary.get("source_file", "unknown"), textbook=tb, chapter=chapter, section=section, knowledgePoints=kps, textbookChunks=[x for x in self.repo.chunks.values() if x["section_id"] == sid], curriculumStandards=[x for x in self.repo.standards.values() if x["section_id"] == sid], ideologyParagraphs=paragraphs, ideologyTags=self._tags_for(paragraphs))

    def _tags_for(self, paragraphs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        pids = {x["paragraph_id"] for x in paragraphs}
        l3_codes = sorted({e["l3_code"] for e in self.repo.relations["paragraph_tagged_with_l3"] if e["paragraph_id"] in pids})
        l3 = [self.repo.tags[c] for c in l3_codes if c in self.repo.tags]
        l2_codes = sorted({x["l2_code"] for x in l3})
        l2 = [self.repo.l2_tags[c] for c in l2_codes if c in self.repo.l2_tags]
        l1_codes = sorted({x["l1_code"] for x in l2})
        return {"level1": [self.repo.l1_tags[c] for c in l1_codes if c in self.repo.l1_tags], "level2": l2, "level3": l3}
