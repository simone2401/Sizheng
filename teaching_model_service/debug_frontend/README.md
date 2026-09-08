# Debug Frontend（独立联调页面）

这是一个**独立的临时前端**，用于联调 `POST /v1/chat/teaching`。

- 不依赖现有后端代码结构。
- 可随时整体删除目录 `debug_frontend/`。
- 支持流式请求长等待（默认 10 分钟，可调到 60 分钟）。

## 启动

在项目根目录执行：

```bash
cd /Users/simone/Desktop/Sizheng/teaching_model_service
python3 -m http.server 5173
```

浏览器打开：

- http://127.0.0.1:5173/debug_frontend/index.html

## 页面功能

- 输入模型 API 地址（默认 `http://127.0.0.1:8000`）
- 输入 Bearer API Key
- 选择模型（含自定义）
- 选择业务类型：
  - `lesson_plan_assist`
  - `case_guide_study`
- 配置教材元信息与教师输入
- 流式/非流式请求切换
- `reasoning_content` 与 `content` 分栏实时展示
- 手动中止请求

## 注意事项（CORS）

如果页面请求被浏览器拦截，请确认模型 API 的 `CORS_ALLOW_ORIGINS` 包含：

- `http://127.0.0.1:5173`
- 或 `http://localhost:5173`

例如：

```bash
CORS_ALLOW_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```
