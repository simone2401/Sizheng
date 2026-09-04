from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from app.shared.config import default_resource_dir


class ResourceRepository:
    def __init__(self, resource_dir: str | Path | None = None) -> None:
        self.resource_dir = Path(resource_dir) if resource_dir else default_resource_dir()
        self.loaded = False
        self.entities: dict[str, Any] = {}
        self.relations: dict[str, list[dict[str, str]]] = {}
        self.summary: dict[str, Any] = {}
        for name in ("textbook", "chapters", "sections", "knowledge_points", "chunks", "standards", "paragraphs", "tags", "l2_tags", "l1_tags"):
            setattr(self, name, {})

    def load(self) -> None:
        def read(name: str) -> Any:
            with (self.resource_dir / name).open(encoding="utf-8") as file:
                return json.load(file)
        self.entities, self.relations, self.summary = read("entities.json"), read("relations.json"), read("summary.json")
        self.textbook = self.entities["textbook"][0]
        self.chapters = {x["chapter_id"]: x for x in self.entities["chapters"]}
        self.sections = {x["section_id"]: x for x in self.entities["sections"]}
        self.knowledge_points = {x["knowledge_point_id"]: x for x in self.entities["knowledge_points"]}
        self.chunks = {x["chunk_id"]: x for x in self.entities["textbook_chunks"]}
        self.standards = {x["standard_item_id"]: x for x in self.entities["curriculum_standards"]}
        self.paragraphs = {x["paragraph_id"]: x for x in self.entities["ideology_paragraphs"]}
        tags = self.entities["ideology_tags"]
        self.tags = {x["l3_code"]: x for x in tags["level_3"]}
        self.l2_tags = {x["l2_code"]: x for x in tags["level_2"]}
        self.l1_tags = {x["l1_code"]: x for x in tags["level_1"]}
        self.loaded = True
