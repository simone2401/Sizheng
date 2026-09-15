from __future__ import annotations
import re
from typing import Any
from app.shared.errors import ResourceNotFoundError
from app.shared.resource_contracts import ResourceQuery, ResourceResponse, StaticIdeologyItem, StaticIdeologyResponse
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
        if query.ideology_ids:
            selected_ids = set(query.ideology_ids)
            paragraphs = [x for x in paragraphs if x["paragraph_id"] in selected_ids]
        return ResourceResponse(dataVersion=self.repo.summary.get("source_file", "unknown"), textbook=tb, chapter=chapter, section=section, knowledgePoints=kps, textbookChunks=[x for x in self.repo.chunks.values() if x["section_id"] == sid], curriculumStandards=[x for x in self.repo.standards.values() if x["section_id"] == sid], ideologyParagraphs=paragraphs, ideologyTags=self._tags_for(paragraphs))

    def query_static(self, query: ResourceQuery) -> StaticIdeologyResponse:
        base = self.query(ResourceQuery(
            schoolLevel=query.school_level,
            subject=query.subject,
            textbookVersion=query.textbook_version,
            chapter=query.chapter,
            lesson=query.lesson,
            knowledgePoints=query.knowledge_points,
        ))
        results: list[StaticIdeologyItem] = []
        for paragraph in base.ideology_paragraphs:
            codes = self._paragraph_l3_codes(paragraph)
            l1_labels = sorted(dict.fromkeys(
                label for label in (self._l1_label_by_l3(code) for code in codes) if label
            ))
            if not l1_labels:
                continue
            results.append(StaticIdeologyItem(
                ideologyID=paragraph.get("paragraph_id", ""),
                sourcePage=paragraph.get("source_page", 0),
                ideologyKeyword=paragraph.get("keyword", ""),
                l1_label="、".join(l1_labels),
            ))
        return StaticIdeologyResponse(items=results)

    def _paragraph_l3_codes(self, paragraph: dict[str, Any]) -> list[str]:
        raw_codes = paragraph.get("ideology_l3_codes")
        if isinstance(raw_codes, str):
            return [x.strip() for x in re.split(r"[;,，；]\s*", raw_codes) if x.strip()]
        if isinstance(raw_codes, list):
            return [str(x).strip() for x in raw_codes if str(x).strip()]
        return [
            edge["l3_code"]
            for edge in self.repo.relations.get("paragraph_tagged_with_l3", [])
            if edge.get("paragraph_id") == paragraph.get("paragraph_id") and edge.get("l3_code")
        ]

    def _l1_label_by_l3(self, l3_code: str) -> str | None:
        l3 = self.repo.tags.get(l3_code)
        if not l3:
            return None
        l2 = self.repo.l2_tags.get(l3.get("l2_code"))
        if not l2:
            return None
        l1 = self.repo.l1_tags.get(l2.get("l1_code"))
        if not l1:
            return None
        return l1.get("l1_label")

    def _tags_for(self, paragraphs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        pids = {x["paragraph_id"] for x in paragraphs}
        l3_codes = sorted({e["l3_code"] for e in self.repo.relations["paragraph_tagged_with_l3"] if e["paragraph_id"] in pids})
        l3 = [self.repo.tags[c] for c in l3_codes if c in self.repo.tags]
        l2_codes = sorted({x["l2_code"] for x in l3})
        l2 = [self.repo.l2_tags[c] for c in l2_codes if c in self.repo.l2_tags]
        l1_codes = sorted({x["l1_code"] for x in l2})
        return {"level1": [self.repo.l1_tags[c] for c in l1_codes if c in self.repo.l1_tags], "level2": l2, "level3": l3}
