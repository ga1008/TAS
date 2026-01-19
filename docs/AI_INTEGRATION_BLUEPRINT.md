# AI Integration Blueprint

## 1. AI 服务分层
1.  **Blueprints (`ai_generator.py`)**: 处理 HTTP 请求，启动后台线程。
2.  **Service Layer (`services/ai_service.py`)**: 封装复杂业务逻辑（如智能解析、代码生成工作流）。
3.  **Utils Layer (`ai_utils/ai_helper.py`)**: 处理底层的 API 调用、并发控制和协议适配。

## 2. 关键功能

### 智能解析 (Smart Parse)
* **入口**: `AiService.smart_parse_content(file_id)`
* **策略**:
    1.  **Vision Mode (V3)**: 使用火山引擎 Responses API 上传文件（PDF/Doc/Image），直接视觉解析。
    2.  **Text Mode (V2)**: 提取文件纯文本，发送给 LLM 进行结构化。
    3.  **Fallback**: 仅提取纯文本。
* **结果**: 解析结果存入 `file_assets.parsed_content`，元数据存入 `file_assets.meta_info`。

### AI 代码生成 (Grader Generation)
* **流程**: 用户上传试卷/标准 -> 存入 `ai_tasks` -> 后台线程 `AiService.generate_grader_worker` -> 组装 Prompt (Base + Strict/Loose + Input) -> 调用 AI -> 提取 Python 代码 -> 保存到 `graders/` -> 触发 `GraderFactory` 热重载。

### 并发控制
* 使用 `ai_utils/ai_concurrency_manager.py` 控制每个 Provider 的并发数，防止 API Rate Limit。

## 3. 协议适配
* **Volcengine**: 支持多模态文件上传 (`ai_utils/volc_file_manager.py`) 和流式对话。
* **OpenAI**: 支持标准 Chat Completion 接口。