# Teaching Model Service

独立 FastAPI 服务，提供教材静态资源查询和教学模型接口。

## 启动

```bash
cd /Users/simone/Desktop/思政/teaching_model_service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
TEACHING_API_KEYS=dev-key ZHIPU_API_KEY=your-key ZHIPU_MODEL=glm-5.2 uvicorn app.main:app --reload --port 8000
```

默认读取 `../json_output/PEP8U_PHYSICS`，可用 `TEACHING_RESOURCE_DIR` 覆盖。
未配置 `ZHIPU_API_KEY` 时使用 Mock 客户端，仅用于本地测试。

## 接口

`GET /v1/teaching/resources` 查询教材、知识点、课标和思政资源。

`POST /v1/chat/teaching` 使用 `Authorization: Bearer <成研院 API Key>` 调用。`TEACHING_API_KEYS` 可配置逗号分隔的多个 Key；这些 Key 与内部调用智谱的 `ZHIPU_API_KEY` 完全不同。

备课请求的非流式响应不使用 `stage`、`outputType` 或 `outputs[]`：

```json
{
  "model": "glm-5.2",
  "reasoning_content": "已完成教材分析、教案对齐和思政标签匹配。",
  "content": "# 课程思政融入初中物理教学\n...",
  "finishReason": "stop",
  "usage": {"inputTokens": 1580, "outputTokens": 920, "totalTokens": 2500},
  "error": null
}
```

`content` 是 Markdown 教案正文，由调用方自行渲染；`reasoning_content` 是中文、可展示的生成依据摘要。案例导引只返回 `content`，`reasoning_content` 为空。

`stream` 默认为 `true`，未传该字段时返回 SSE；显式设置 `stream=false` 时返回非流式 JSON。每个 SSE `data` 事件分别增量携带 `content` 或 `reasoning_content`；结束事件携带 `finishReason` 和驼峰格式 `usage`。智谱的 `[DONE]` 不会透传。

## 测试

```bash
pytest -q
```
