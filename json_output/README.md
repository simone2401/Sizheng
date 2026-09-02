# Excel 转 JSON 结果说明

## 目录结构
- `json_output/PEP8U_PHYSICS/raw_sheets/*.json`：按 Excel 分表逐个导出的原始 JSON。
- `json_output/PEP8U_PHYSICS/entities.json`：实体集合（教材、章节、节、知识点等）。
- `json_output/PEP8U_PHYSICS/relations.json`：关系集合（章节-节、节-知识点、段落-标签等）。
- `json_output/PEP8U_PHYSICS/summary.json`：总览统计（分表数量、实体数量、关系数量）。
- `json_output/PEP8U_PHYSICS/graph.json`：实体+关系+统计的统一视图。
- `json_output/PEP8U_PHYSICS/marble/`：对齐 os-taxonomy 风格的图谱文件（`topics.json`、`dependencies.json`、`curriculum-standards.json`、`clusters.json`、`manifest.json`）。

## 重新转换
在项目根目录运行：

```bash
python3 excel_to_json.py
```

脚本会自动扫描当前目录下所有 `.xlsx/.xls` 并输出到 `json_output/<工作簿名>/`。
