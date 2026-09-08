## 目标
以新版 `model_api + resource_api + shared` 作为唯一正式实现，收敛鉴权、错误和流式协议；在完整回归测试后移除旧单体服务，避免继续维护两套已分叉的业务逻辑。

## 实施范围

1. **先固化新版运行契约**
   - 在 `app/shared/config.py` 为 `MODEL_BACKEND` 建立明确允许值（`mock`、`zhipu`）并在 `ModelSettings.from_env()` 中校验未知值，避免拼写错误静默走 Mock。
   - 保持共享鉴权 `app/shared/auth.py` 的 fail-closed 行为：除非明确设置对应 `*_AUTH_DISABLED`，未配置 API Key 或未携带 Bearer Token 都返回未授权。
   - 检查 `app/model_api/main.py` 的 readiness 实现，将未就绪状态改为 HTTP 503；资源 API 同步采用这一约定。

2. **统一模型完成状态和异常边界**
   - 在 `app/model_api/teaching_service.py` 增加单一的上游 `finish_reason` 归一化逻辑：协议成功完成统一输出 `stop`；任何非正常/未知状态转换为受控 `ServiceError`（或在协议需要保留时以明确、受模型验证支持的映射处理），不把供应商原始值直接传入 `TeachingResponse`。
   - 保证流式生成在上游未给出 `usage` 或 `finish_reason` 时，正常迭代结束后仍补发一个 `finishReason: "stop"` 的 SSE 结束事件；只发一次终止事件。
   - 扩展 `app/model_api/router.py` 的非流式和 SSE 异常边界，处理响应验证及非 `ServiceError` 的受控服务错误，确保客户端收到标准错误 JSON/SSE，而不是普通 500 或中断连接。
   - 同时移除 router 中未使用的 `json`、`PreparedTeachingRequest` 导入，以及 `sse.py` 中无调用的 `encode_stream`（如确认没有外部兼容要求）。

3. **规范资源服务不可用的行为**
   - 在 `app/resource_api/main.py` 将资源加载异常保存为明确的不可用状态，并让 `current_service()` 抛出共享的、可映射的资源不可用异常，而不是 `RuntimeError`。
   - 在 `app/resource_api/router.py` 或应用级异常处理处把该异常转换为协议化响应；资源加载失败时 `/health/ready` 返回 503 和 `ready: false`，成功时仍为 200。
   - 清理 `resource_api/router.py` 中未使用的 `Any` 导入。

4. **补足针对新架构的测试**
   - 重构 `tests/test_api.py` 的固定机器绝对路径，改为基于仓库路径或 pytest 临时目录构造资源 fixture，保证跨机器可运行。
   - 增加模型 API 与资源 API 的鉴权测试：缺失 key、错误 key、正确 key、显式禁用鉴权。
   - 增加 `MODEL_BACKEND` 非法值、zhipu 未配置 key、两类 readiness（200/503）的测试。
   - 增加资源加载失败时业务接口返回规范错误而非裸 500 的测试。
   - 覆盖非流式和流式的上游异常结束原因、缺失终止标记的补充 stop 事件，以及流式错误事件格式。
   - 保留现有教案和案例正向路径测试，确保本轮契约修复不改变已确认的业务内容边界。

5. **更新接口与运行文档**
   - 更新 `课程思政模型服务接口内部设计文档 V1.0.md`：明确当前统一响应不提供 `outputType`、`outputs`、`stage`，并以现有 `content`、`reasoning_content`、`finishReason`、`usage` 为准；将版本说明与当前协议对齐。
   - 同步检查 `teaching_model_service/README.md` 中的启动与鉴权说明，删除重复段落，并使其只描述新版双服务入口。
   - 文档中明确 readiness 的 200/503 语义、`MODEL_BACKEND` 可选值和 fail-closed 鉴权行为。

6. **删除旧单体实现并做引用验证**
   - 在以上新版测试全部通过后，删除不再使用的 `app/main.py`、`app/service.py`、`app/resources.py`、`app/models.py`。
   - 使用全仓引用搜索确认没有脚本、文档、测试或包导入仍依赖这些文件；必要时更新 README、启动命令和测试导入。
   - 不在此改造中处理 `.venv`、`__pycache__`、`.gitignore`、依赖锁定或 `dev.sh` 的 macOS 兼容性，避免把架构收敛与仓库卫生重构混为一次变更；这些将作为后续独立清理项。

## 验证
- 运行目标测试集和完整 `pytest`。
- 对应用 Python 模块做语法/导入检查。
- 通过 TestClient 验证双服务的健康状态、鉴权、资源不可用、非流式和 SSE 完成/错误契约。
- 最后执行全仓引用搜索和 `git diff` 审查，确认旧单体入口已无引用，新版是唯一运行路径。