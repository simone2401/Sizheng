# JSON 文件字段说明

- 目录：`/Users/simone/Desktop/思政/json_output`
- 说明：本文档自动基于当前 JSON 文件内容生成，字段类型为“观测到的实际类型”。

## `PEP8U_PHYSICS/entities.json`

- 文件描述：按实体类型汇总的主数据文件（教材、章节、节、知识点、原文分块、思政段落、标签体系）。
- 根类型：`object`
- 顶层字段数：`8`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `textbook` | `array` | 顶层字段 |
| `chapters` | `array` | 顶层字段 |
| `sections` | `array` | 顶层字段 |
| `curriculum_standards` | `array` | 顶层字段 |
| `knowledge_points` | `array` | 顶层字段 |
| `textbook_chunks` | `array` | 顶层字段 |
| `ideology_paragraphs` | `array` | 顶层字段 |
| `ideology_tags` | `object` | 顶层字段 |

### `textbook[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `edition` | `string` | `textbook` 数组元素字段 |
| `school_level` | `string` | `textbook` 数组元素字段 |
| `subject` | `string` | `textbook` 数组元素字段 |
| `textbook_id` | `string` | `textbook` 数组元素字段 |
| `textbook_name` | `string` | `textbook` 数组元素字段 |
| `textbook_version` | `string` | `textbook` 数组元素字段 |

### `chapters[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chapter_id` | `string` | `chapters` 数组元素字段 |
| `chapter_title` | `string` | `chapters` 数组元素字段 |

### `sections[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chapter_id` | `string` | `sections` 数组元素字段 |
| `chapter_title` | `string` | `sections` 数组元素字段 |
| `section_id` | `string` | `sections` 数组元素字段 |
| `section_title` | `string` | `sections` 数组元素字段 |

### `curriculum_standards[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `code` | `string` | `curriculum_standards` 数组元素字段 |
| `item_content` | `string` | `curriculum_standards` 数组元素字段 |
| `item_title` | `string` | `curriculum_standards` 数组元素字段 |
| `printed_page` | `integer` | `curriculum_standards` 数组元素字段 |
| `section_category` | `string` | `curriculum_standards` 数组元素字段 |
| `section_id` | `string` | `curriculum_standards` 数组元素字段 |
| `standard_item_id` | `string` | `curriculum_standards` 数组元素字段 |

### `knowledge_points[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `cognitive_level` | `string` | `knowledge_points` 数组元素字段 |
| `knowledge_point_id` | `string` | `knowledge_points` 数组元素字段 |
| `printed_pages` | `string` | `knowledge_points` 数组元素字段 |
| `section_id` | `string` | `knowledge_points` 数组元素字段 |
| `summary` | `string` | `knowledge_points` 数组元素字段 |
| `title` | `string` | `knowledge_points` 数组元素字段 |

### `textbook_chunks[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chunk_id` | `string` | `textbook_chunks` 数组元素字段 |
| `page` | `integer` | `textbook_chunks` 数组元素字段 |
| `section_id` | `string` | `textbook_chunks` 数组元素字段 |
| `text` | `string` | `textbook_chunks` 数组元素字段 |

### `ideology_paragraphs[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `evidence_type` | `string` | `ideology_paragraphs` 数组元素字段 |
| `ideology_l3_codes` | `string` | `ideology_paragraphs` 数组元素字段 |
| `ideology_l3_labels` | `string` | `ideology_paragraphs` 数组元素字段 |
| `keyword` | `string` | `ideology_paragraphs` 数组元素字段 |
| `paragraph_id` | `string` | `ideology_paragraphs` 数组元素字段 |
| `section_id` | `string` | `ideology_paragraphs` 数组元素字段 |
| `source_page` | `integer` | `ideology_paragraphs` 数组元素字段 |
| `textbook_original_excerpt` | `string` | `ideology_paragraphs` 数组元素字段 |

### `ideology_tags` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `level_1` | `array` | `ideology_tags` 对象字段 |
| `level_2` | `array` | `ideology_tags` 对象字段 |
| `level_3` | `array` | `ideology_tags` 对象字段 |

#### `ideology_tags.level_1[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `l1_code` | `string` | `ideology_tags.level_1` 数组元素字段 |
| `l1_label` | `string` | `ideology_tags.level_1` 数组元素字段 |

#### `ideology_tags.level_2[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `l1_code` | `string` | `ideology_tags.level_2` 数组元素字段 |
| `l2_code` | `string` | `ideology_tags.level_2` 数组元素字段 |
| `l2_label` | `string` | `ideology_tags.level_2` 数组元素字段 |

#### `ideology_tags.level_3[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `l2_code` | `string` | `ideology_tags.level_3` 数组元素字段 |
| `l3_code` | `string` | `ideology_tags.level_3` 数组元素字段 |
| `l3_label` | `string` | `ideology_tags.level_3` 数组元素字段 |

## `PEP8U_PHYSICS/graph.json`

- 文件描述：统一图视图，聚合 entities + relations + summary。
- 根类型：`object`
- 顶层字段数：`3`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `entities` | `object` | 顶层字段 |
| `relations` | `object` | 顶层字段 |
| `summary` | `object` | 顶层字段 |

### `entities` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `textbook` | `array` | `entities` 对象字段 |
| `chapters` | `array` | `entities` 对象字段 |
| `sections` | `array` | `entities` 对象字段 |
| `curriculum_standards` | `array` | `entities` 对象字段 |
| `knowledge_points` | `array` | `entities` 对象字段 |
| `textbook_chunks` | `array` | `entities` 对象字段 |
| `ideology_paragraphs` | `array` | `entities` 对象字段 |
| `ideology_tags` | `object` | `entities` 对象字段 |

#### `entities.textbook[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `edition` | `string` | `entities.textbook` 数组元素字段 |
| `school_level` | `string` | `entities.textbook` 数组元素字段 |
| `subject` | `string` | `entities.textbook` 数组元素字段 |
| `textbook_id` | `string` | `entities.textbook` 数组元素字段 |
| `textbook_name` | `string` | `entities.textbook` 数组元素字段 |
| `textbook_version` | `string` | `entities.textbook` 数组元素字段 |

#### `entities.chapters[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chapter_id` | `string` | `entities.chapters` 数组元素字段 |
| `chapter_title` | `string` | `entities.chapters` 数组元素字段 |

#### `entities.sections[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chapter_id` | `string` | `entities.sections` 数组元素字段 |
| `chapter_title` | `string` | `entities.sections` 数组元素字段 |
| `section_id` | `string` | `entities.sections` 数组元素字段 |
| `section_title` | `string` | `entities.sections` 数组元素字段 |

#### `entities.curriculum_standards[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `code` | `string` | `entities.curriculum_standards` 数组元素字段 |
| `item_content` | `string` | `entities.curriculum_standards` 数组元素字段 |
| `item_title` | `string` | `entities.curriculum_standards` 数组元素字段 |
| `printed_page` | `integer` | `entities.curriculum_standards` 数组元素字段 |
| `section_category` | `string` | `entities.curriculum_standards` 数组元素字段 |
| `section_id` | `string` | `entities.curriculum_standards` 数组元素字段 |
| `standard_item_id` | `string` | `entities.curriculum_standards` 数组元素字段 |

#### `entities.knowledge_points[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `cognitive_level` | `string` | `entities.knowledge_points` 数组元素字段 |
| `knowledge_point_id` | `string` | `entities.knowledge_points` 数组元素字段 |
| `printed_pages` | `string` | `entities.knowledge_points` 数组元素字段 |
| `section_id` | `string` | `entities.knowledge_points` 数组元素字段 |
| `summary` | `string` | `entities.knowledge_points` 数组元素字段 |
| `title` | `string` | `entities.knowledge_points` 数组元素字段 |

#### `entities.textbook_chunks[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chunk_id` | `string` | `entities.textbook_chunks` 数组元素字段 |
| `page` | `integer` | `entities.textbook_chunks` 数组元素字段 |
| `section_id` | `string` | `entities.textbook_chunks` 数组元素字段 |
| `text` | `string` | `entities.textbook_chunks` 数组元素字段 |

#### `entities.ideology_paragraphs[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `evidence_type` | `string` | `entities.ideology_paragraphs` 数组元素字段 |
| `ideology_l3_codes` | `string` | `entities.ideology_paragraphs` 数组元素字段 |
| `ideology_l3_labels` | `string` | `entities.ideology_paragraphs` 数组元素字段 |
| `keyword` | `string` | `entities.ideology_paragraphs` 数组元素字段 |
| `paragraph_id` | `string` | `entities.ideology_paragraphs` 数组元素字段 |
| `section_id` | `string` | `entities.ideology_paragraphs` 数组元素字段 |
| `source_page` | `integer` | `entities.ideology_paragraphs` 数组元素字段 |
| `textbook_original_excerpt` | `string` | `entities.ideology_paragraphs` 数组元素字段 |

### `relations` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chapter_has_section` | `array` | `relations` 对象字段 |
| `section_has_standard` | `array` | `relations` 对象字段 |
| `section_has_knowledge_point` | `array` | `relations` 对象字段 |
| `section_has_chunk` | `array` | `relations` 对象字段 |
| `section_has_ideology_paragraph` | `array` | `relations` 对象字段 |
| `tag_l1_has_l2` | `array` | `relations` 对象字段 |
| `tag_l2_has_l3` | `array` | `relations` 对象字段 |
| `paragraph_tagged_with_l3` | `array` | `relations` 对象字段 |

#### `relations.chapter_has_section[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chapter_id` | `string` | `relations.chapter_has_section` 数组元素字段 |
| `section_id` | `string` | `relations.chapter_has_section` 数组元素字段 |

#### `relations.section_has_standard[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `section_id` | `string` | `relations.section_has_standard` 数组元素字段 |
| `standard_item_id` | `string` | `relations.section_has_standard` 数组元素字段 |

#### `relations.section_has_knowledge_point[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `knowledge_point_id` | `string` | `relations.section_has_knowledge_point` 数组元素字段 |
| `section_id` | `string` | `relations.section_has_knowledge_point` 数组元素字段 |

#### `relations.section_has_chunk[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chunk_id` | `string` | `relations.section_has_chunk` 数组元素字段 |
| `section_id` | `string` | `relations.section_has_chunk` 数组元素字段 |

#### `relations.section_has_ideology_paragraph[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `paragraph_id` | `string` | `relations.section_has_ideology_paragraph` 数组元素字段 |
| `section_id` | `string` | `relations.section_has_ideology_paragraph` 数组元素字段 |

#### `relations.tag_l1_has_l2[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `l1_code` | `string` | `relations.tag_l1_has_l2` 数组元素字段 |
| `l2_code` | `string` | `relations.tag_l1_has_l2` 数组元素字段 |

#### `relations.tag_l2_has_l3[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `l2_code` | `string` | `relations.tag_l2_has_l3` 数组元素字段 |
| `l3_code` | `string` | `relations.tag_l2_has_l3` 数组元素字段 |

#### `relations.paragraph_tagged_with_l3[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `l3_code` | `string` | `relations.paragraph_tagged_with_l3` 数组元素字段 |
| `paragraph_id` | `string` | `relations.paragraph_tagged_with_l3` 数组元素字段 |

### `summary` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `source_file` | `string` | `summary` 对象字段 |
| `sheet_count` | `integer` | `summary` 对象字段 |
| `sheets` | `array` | `summary` 对象字段 |
| `sheet_row_counts` | `object` | `summary` 对象字段 |
| `entity_counts` | `object` | `summary` 对象字段 |
| `relation_counts` | `object` | `summary` 对象字段 |

## `PEP8U_PHYSICS/marble/clusters.json`

- 文件描述：结构化数据文件。
- 根类型：`object`
- 顶层字段数：`3`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `version` | `string` | 顶层字段 |
| `clusterCount` | `integer` | 顶层字段 |
| `clusters` | `array` | 顶层字段 |

### `clusters[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `ageRangeStart` | `integer` | `clusters` 数组元素字段 |
| `domain` | `string` | `clusters` 数组元素字段 |
| `subject` | `string` | `clusters` 数组元素字段 |
| `summary` | `string` | `clusters` 数组元素字段 |

## `PEP8U_PHYSICS/marble/curriculum-standards.json`

- 文件描述：结构化数据文件。
- 根类型：`object`
- 顶层字段数：`4`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `note` | `string` | 顶层字段 |
| `codesOnlySources` | `array` | 顶层字段 |
| `curriculumCount` | `integer` | 顶层字段 |
| `curricula` | `array` | 顶层字段 |

### `curricula[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `country` | `string` | `curricula` 数组元素字段 |
| `license` | `string` | `curricula` 数组元素字段 |
| `name` | `string` | `curricula` 数组元素字段 |
| `slug` | `string` | `curricula` 数组元素字段 |
| `sourceUrl` | `null` | `curricula` 数组元素字段 |
| `textIncluded` | `boolean` | `curricula` 数组元素字段 |
| `topicCount` | `integer` | `curricula` 数组元素字段 |
| `topics` | `array` | `curricula` 数组元素字段 |
| `version` | `string` | `curricula` 数组元素字段 |

## `PEP8U_PHYSICS/marble/dependencies.json`

- 文件描述：结构化数据文件。
- 根类型：`object`
- 顶层字段数：`4`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `version` | `string` | 顶层字段 |
| `note` | `string` | 顶层字段 |
| `edgeCount` | `integer` | 顶层字段 |
| `dependencies` | `array` | 顶层字段 |

### `dependencies[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `prerequisiteId` | `string` | `dependencies` 数组元素字段 |
| `reason` | `string` | `dependencies` 数组元素字段 |
| `strength` | `string` | `dependencies` 数组元素字段 |
| `topicId` | `string` | `dependencies` 数组元素字段 |

## `PEP8U_PHYSICS/marble/manifest.json`

- 文件描述：结构化数据文件。
- 根类型：`object`
- 顶层字段数：`4`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `version` | `string` | 顶层字段 |
| `counts` | `object` | 顶层字段 |
| `subjects` | `object` | 顶层字段 |
| `files` | `object` | 顶层字段 |

### `counts` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `topics` | `integer` | `counts` 对象字段 |
| `dependencies` | `integer` | `counts` 对象字段 |
| `clusters` | `integer` | `counts` 对象字段 |
| `curricula` | `integer` | `counts` 对象字段 |

### `subjects` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `物理` | `integer` | `subjects` 对象字段 |

### `files` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `topics.json` | `object` | `files` 对象字段 |
| `dependencies.json` | `object` | `files` 对象字段 |
| `curriculum-standards.json` | `object` | `files` 对象字段 |
| `clusters.json` | `object` | `files` 对象字段 |

## `PEP8U_PHYSICS/marble/topics.json`

- 文件描述：结构化数据文件。
- 根类型：`object`
- 顶层字段数：`3`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `version` | `string` | 顶层字段 |
| `topicCount` | `integer` | 顶层字段 |
| `topics` | `array` | 顶层字段 |

### `topics[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `ageRangeEnd` | `null` | `topics` 数组元素字段 |
| `ageRangeStart` | `null` | `topics` 数组元素字段 |
| `assessmentPrompt` | `null` | `topics` 数组元素字段 |
| `centrality` | `null` | `topics` 数组元素字段 |
| `description` | `string` | `topics` 数组元素字段 |
| `domain` | `string` | `topics` 数组元素字段 |
| `evidence` | `array` | `topics` 数组元素字段 |
| `id` | `string` | `topics` 数组元素字段 |
| `name` | `string` | `topics` 数组元素字段 |
| `source` | `object` | `topics` 数组元素字段 |
| `standards` | `array` | `topics` 数组元素字段 |
| `subject` | `string` | `topics` 数组元素字段 |
| `type` | `string` | `topics` 数组元素字段 |

## `PEP8U_PHYSICS/raw_sheets/curriculum_standards.json`

- 文件描述：结构化数据文件。
- 根类型：`array`
- 记录数：`43`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `code` | `string` | 来自该文件记录项字段 |
| `item_content` | `string` | 来自该文件记录项字段 |
| `item_title` | `string` | 来自该文件记录项字段 |
| `printed_page` | `integer` | 来自该文件记录项字段 |
| `section_category` | `string` | 来自该文件记录项字段 |
| `section_id` | `string` | 来自该文件记录项字段 |
| `standard_item_id` | `string` | 来自该文件记录项字段 |

## `PEP8U_PHYSICS/raw_sheets/ideology_paragraphs.json`

- 文件描述：结构化数据文件。
- 根类型：`array`
- 记录数：`63`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `evidence_type` | `string` | 来自该文件记录项字段 |
| `ideology_l3_codes` | `string` | 来自该文件记录项字段 |
| `ideology_l3_labels` | `string` | 来自该文件记录项字段 |
| `keyword` | `string` | 来自该文件记录项字段 |
| `paragraph_id` | `string` | 来自该文件记录项字段 |
| `section_id` | `string` | 来自该文件记录项字段 |
| `source_page` | `integer` | 来自该文件记录项字段 |
| `textbook_original_excerpt` | `string` | 来自该文件记录项字段 |

## `PEP8U_PHYSICS/raw_sheets/ideology_tag_taxonomy.json`

- 文件描述：结构化数据文件。
- 根类型：`array`
- 记录数：`93`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `l1_code` | `string` | 来自该文件记录项字段 |
| `l1_label` | `string` | 来自该文件记录项字段 |
| `l2_code` | `string` | 来自该文件记录项字段 |
| `l2_label` | `string` | 来自该文件记录项字段 |
| `l3_code` | `string` | 来自该文件记录项字段 |
| `l3_label` | `string` | 来自该文件记录项字段 |

## `PEP8U_PHYSICS/raw_sheets/knowledge_points.json`

- 文件描述：结构化数据文件。
- 根类型：`array`
- 记录数：`106`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `cognitive_level` | `string` | 来自该文件记录项字段 |
| `knowledge_point_id` | `string` | 来自该文件记录项字段 |
| `printed_pages` | `string` | 来自该文件记录项字段 |
| `section_id` | `string` | 来自该文件记录项字段 |
| `summary` | `string` | 来自该文件记录项字段 |
| `title` | `string` | 来自该文件记录项字段 |

## `PEP8U_PHYSICS/raw_sheets/meta.json`

- 文件描述：结构化数据文件。
- 根类型：`array`
- 记录数：`1`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `edition` | `string` | 来自该文件记录项字段 |
| `school_level` | `string` | 来自该文件记录项字段 |
| `subject` | `string` | 来自该文件记录项字段 |
| `textbook_id` | `string` | 来自该文件记录项字段 |
| `textbook_name` | `string` | 来自该文件记录项字段 |
| `textbook_version` | `string` | 来自该文件记录项字段 |

## `PEP8U_PHYSICS/raw_sheets/sections.json`

- 文件描述：结构化数据文件。
- 根类型：`array`
- 记录数：`28`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chapter_id` | `string` | 来自该文件记录项字段 |
| `chapter_title` | `string` | 来自该文件记录项字段 |
| `section_id` | `string` | 来自该文件记录项字段 |
| `section_title` | `string` | 来自该文件记录项字段 |

## `PEP8U_PHYSICS/raw_sheets/textbook_original_chunks.json`

- 文件描述：结构化数据文件。
- 根类型：`array`
- 记录数：`140`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chunk_id` | `string` | 来自该文件记录项字段 |
| `page` | `integer` | 来自该文件记录项字段 |
| `section_id` | `string` | 来自该文件记录项字段 |
| `text` | `string` | 来自该文件记录项字段 |

## `PEP8U_PHYSICS/relations.json`

- 文件描述：实体之间的关系边集合，可用于图谱构建。
- 根类型：`object`
- 顶层字段数：`8`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chapter_has_section` | `array` | 顶层字段 |
| `section_has_standard` | `array` | 顶层字段 |
| `section_has_knowledge_point` | `array` | 顶层字段 |
| `section_has_chunk` | `array` | 顶层字段 |
| `section_has_ideology_paragraph` | `array` | 顶层字段 |
| `tag_l1_has_l2` | `array` | 顶层字段 |
| `tag_l2_has_l3` | `array` | 顶层字段 |
| `paragraph_tagged_with_l3` | `array` | 顶层字段 |

### `chapter_has_section[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chapter_id` | `string` | `chapter_has_section` 数组元素字段 |
| `section_id` | `string` | `chapter_has_section` 数组元素字段 |

### `section_has_standard[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `section_id` | `string` | `section_has_standard` 数组元素字段 |
| `standard_item_id` | `string` | `section_has_standard` 数组元素字段 |

### `section_has_knowledge_point[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `knowledge_point_id` | `string` | `section_has_knowledge_point` 数组元素字段 |
| `section_id` | `string` | `section_has_knowledge_point` 数组元素字段 |

### `section_has_chunk[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chunk_id` | `string` | `section_has_chunk` 数组元素字段 |
| `section_id` | `string` | `section_has_chunk` 数组元素字段 |

### `section_has_ideology_paragraph[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `paragraph_id` | `string` | `section_has_ideology_paragraph` 数组元素字段 |
| `section_id` | `string` | `section_has_ideology_paragraph` 数组元素字段 |

### `tag_l1_has_l2[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `l1_code` | `string` | `tag_l1_has_l2` 数组元素字段 |
| `l2_code` | `string` | `tag_l1_has_l2` 数组元素字段 |

### `tag_l2_has_l3[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `l2_code` | `string` | `tag_l2_has_l3` 数组元素字段 |
| `l3_code` | `string` | `tag_l2_has_l3` 数组元素字段 |

### `paragraph_tagged_with_l3[]` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `l3_code` | `string` | `paragraph_tagged_with_l3` 数组元素字段 |
| `paragraph_id` | `string` | `paragraph_tagged_with_l3` 数组元素字段 |

## `PEP8U_PHYSICS/summary.json`

- 文件描述：数据总览统计（分表、实体计数、关系计数）。
- 根类型：`object`
- 顶层字段数：`6`

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `source_file` | `string` | 顶层字段 |
| `sheet_count` | `integer` | 顶层字段 |
| `sheets` | `array` | 顶层字段 |
| `sheet_row_counts` | `object` | 顶层字段 |
| `entity_counts` | `object` | 顶层字段 |
| `relation_counts` | `object` | 顶层字段 |

### `sheet_row_counts` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `meta` | `integer` | `sheet_row_counts` 对象字段 |
| `sections` | `integer` | `sheet_row_counts` 对象字段 |
| `curriculum_standards` | `integer` | `sheet_row_counts` 对象字段 |
| `knowledge_points` | `integer` | `sheet_row_counts` 对象字段 |
| `textbook_original_chunks` | `integer` | `sheet_row_counts` 对象字段 |
| `ideology_paragraphs` | `integer` | `sheet_row_counts` 对象字段 |
| `ideology_tag_taxonomy` | `integer` | `sheet_row_counts` 对象字段 |

### `entity_counts` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `textbook` | `integer` | `entity_counts` 对象字段 |
| `chapters` | `integer` | `entity_counts` 对象字段 |
| `sections` | `integer` | `entity_counts` 对象字段 |
| `curriculum_standards` | `integer` | `entity_counts` 对象字段 |
| `knowledge_points` | `integer` | `entity_counts` 对象字段 |
| `textbook_chunks` | `integer` | `entity_counts` 对象字段 |
| `ideology_paragraphs` | `integer` | `entity_counts` 对象字段 |
| `ideology_tags` | `object` | `entity_counts` 对象字段 |

### `relation_counts` 子字段

| 字段 | 字段类型 | 字段说明 |
|---|---|---|
| `chapter_has_section` | `integer` | `relation_counts` 对象字段 |
| `section_has_standard` | `integer` | `relation_counts` 对象字段 |
| `section_has_knowledge_point` | `integer` | `relation_counts` 对象字段 |
| `section_has_chunk` | `integer` | `relation_counts` 对象字段 |
| `section_has_ideology_paragraph` | `integer` | `relation_counts` 对象字段 |
| `tag_l1_has_l2` | `integer` | `relation_counts` 对象字段 |
| `tag_l2_has_l3` | `integer` | `relation_counts` 对象字段 |
| `paragraph_tagged_with_l3` | `integer` | `relation_counts` 对象字段 |
