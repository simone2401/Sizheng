# Teaching Model Service

项目由两个可独立运行的 FastAPI 服务组成：资源 API 只读取教材 JSON，模型 API 通过 HTTP 调用资源 API，再调用 Mock 或智谱模型。

## 安装

```bash
cd /Users/simone/Desktop/思政/teaching_model_service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

复制 `.env.example` 为 `.env` 后按本地环境修改。教材数据默认位于项目上级的 `json_output/PEP8U_PHYSICS`，也可设置 `TEACHING_RESOURCE_DIR`。如果前端跨域调用，可配置 `CORS_ALLOW_ORIGINS`，多个来源用逗号分隔。

## 启动

终端一启动资源服务：

```bash
RESOURCE_API_KEYS=local-resource-key uvicorn app.resource_api.main:app --host 127.0.0.1 --port 8001
```

终端二启动模型服务：

```bash
MODEL_BACKEND=mock TEACHING_API_KEYS=local-model-key RESOURCE_SERVICE_API_KEY=local-resource-key uvicorn app.model_api.main:app --host 127.0.0.1 --port 8000
```

访问 `/docs`：

- `http://127.0.0.1:8001/docs`
- `http://127.0.0.1:8000/docs`

也可以使用项目脚本同时启动两个服务：

```bash
# 先在 .env 中配置环境变量，或在当前终端导出变量
./scripts/dev.sh
```

按 `Ctrl+C` 会只停止该脚本启动的两个进程，不会使用 `pkill` 误杀其他服务。


资源查询：

```bash
curl -G 'http://127.0.0.1:8001/v1/teaching/resources' \
  -H 'Authorization: Bearer local-resource-key' \
  --data-urlencode 'schoolLevel=8年级上' \
  --data-urlencode 'subject=物理' \
  --data-urlencode 'textbookVersion=人教版' \
  --data-urlencode 'chapter=第六章' \
  --data-urlencode 'lesson=第4节'
```

模型非流式：

```bash
curl -X POST 'http://127.0.0.1:8000/v1/chat/teaching' \
  -H 'Authorization: Bearer local-model-key' -H 'Content-Type: application/json' \
  -d '{"model":"glm-5.2","stream":false,"turnId":1,"messages":[{"role":"USER","content":[{"type":"TEXT","text":"请生成教案"}]}],"metadata":{"chatType":"lesson_plan_assist","schoolLevel":"8年级上","subject":"物理","textbookVersion":"人教版","chapter":"第六章","lesson":"第4节"}}'
```

省略 `stream` 即返回 SSE；显式 `stream=false` 返回 JSON。模型响应使用 `content`、`reasoning_content`、`l1_labels` 和 `finishReason`，token 使用量为 `inputTokens/outputTokens/totalTokens`。案例导引和备课助手通过 `metadata.chatType` 区分；不使用 `stage`、`outputType` 或 `outputs[]`。

配置说明：

- 生产和联调环境必须开启 Bearer API Key 鉴权，并分别配置 `RESOURCE_API_KEYS`、`TEACHING_API_KEYS`。
- 仅允许本地离线开发时使用 `MODEL_API_AUTH_DISABLED=true` 或 `RESOURCE_API_AUTH_DISABLED=true` 关闭对应服务鉴权，禁止在生产和联调环境关闭。
- 服务端以请求体中的 `stream` 字段决定返回 JSON 或 SSE；`Accept` 仅作为客户端推荐请求头，不作为强制校验项。
- 生产和联调环境必须开启 Bearer API Key 鉴权，并分别配置 `RESOURCE_API_KEYS`、`TEACHING_API_KEYS`。
- 仅允许本地离线开发时使用 `MODEL_API_AUTH_DISABLED=true` 或 `RESOURCE_API_AUTH_DISABLED=true` 关闭对应服务鉴权，禁止在生产和联调环境关闭。
- 服务端以请求体中的 `stream` 字段决定返回 JSON 或 SSE；`Accept` 仅作为客户端推荐请求头，不作为强制校验项。
- `model` 传入时作为本次请求的期望模型；未传入时使用 `ZHIPU_MODEL`，默认 `glm-5.2`。
- `reasoning_content` 可以是字符串或 `null`；案例导引场景按业务约定返回空字符串。
`MODEL_BACKEND=mock` 用于本地离线测试；真实智谱调用需显式设置 `MODEL_BACKEND=zhipu` 和 `ZHIPU_API_KEY`，默认模型为 `glm-5.2`。成研院调用 Key 与智谱 Key 分开保存，长期 Key 不应放在浏览器端。

## 测试

```bash
pytest -q
```
