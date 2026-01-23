# Implementation Plan: 全局 AI 助手重构

**Branch**: `002-global-ai-assistant` | **Date**: 2026-01-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-global-ai-assistant/spec.md`

## Summary

将现有的单向 AI 欢迎语系统重构为全功能浮窗式 AI 对话助手。用户可在系统任意页面通过右下角浮窗与 AI 进行多轮对话，AI 能感知页面上下文、用户信息和操作历史，主动提供问候和操作反馈。

## Technical Context

**Language/Version**: Python 3.9+ (Flask 2.x + FastAPI for AI microservice)
**Primary Dependencies**: Flask, FastAPI, Jinja2, httpx, openai, SQLite3
**Storage**: SQLite (`data/grading_system_v2.db`)
**Testing**: Manual testing (no existing test framework)
**Target Platform**: Web browser (modern Chrome/Firefox/Edge)
**Project Type**: Web (Flask templates + JavaScript frontend)
**Performance Goals**: AI 响应 <5s, 消息同步延迟 <2s
**Constraints**: 单服务器部署, 内存 <500MB, 支持 100+ 并发用户
**Scale/Scope**: ~20 页面, ~10 个触发点, 每用户保留 100 条消息

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with `.specify/memory/constitution.md`:

- [x] **模块化解耦**: 新增 `blueprints/ai_assistant.py` 独立蓝图，`services/ai_conversation_service.py` 独立服务
- [x] **微服务分离**: AI 对话通过 HTTP 调用 `ai_assistant.py` 微服务（端口 9011）
- [x] **前端设计一致性**: 浮窗组件遵循 `FRONTEND_GUIDE.md` 玻璃态设计
- [x] **批改器可扩展性**: 不涉及批改逻辑
- [x] **数据库迁移友好**: 新增表使用 `_migrate_table` 辅助函数
- [x] **AI 能力分层**: 对话使用 `standard` 能力，无需 vision/thinking
- [x] **AI 内容生成与缓存**: 对话消息存储数据库，主动问候支持缓存
- [x] **前端 AI 内容展示**: 消息流式显示效果，容器自适应大小
- [x] **AI 提示工程**: 系统提示包含完整上下文和示例
- [x] **个性化AI交互**: 包含用户名、时间、操作历史等个性化元素

---

## Phase 3: Current Implementation State Assessment (2026-01-23)

### 3.1 Backend Layer Analysis

| Component | File | Status | Completeness |
|-----------|------|--------|-------------|
| Database Schema | `database.py:1173-1246` | ✅ Done | 100% |
| API Blueprint | `blueprints/ai_assistant.py` | ✅ Done | 95% |
| Conversation Service | `services/ai_conversation_service.py` | ✅ Done | 100% |
| Content Generation | `services/ai_content_service.py:511-749` | ✅ Done | 100% |
| Prompts | `services/ai_prompts.py:234-412` | ✅ Done | 100% |
| Blueprint Registration | `app.py:36` | ⚠️ 需验证 | - |

**Database Tables Implemented**:
- `ai_conversations`: id, user_id, title, status, created_at, last_active_at
- `ai_messages`: id, conversation_id, role, content, trigger_type, metadata_json, created_at
- `ai_rate_limits`: user_id, last_proactive_trigger, updated_at

**API Endpoints Implemented** (`/api/assistant/`):
```python
# 对话管理
GET  /conversations/active           # 获取活跃对话 (自动创建)
POST /conversations                  # 创建新对话
POST /conversations/{id}/archive     # 归档对话
GET  /conversations/{id}/messages    # 获取消息历史 (分页)
POST /conversations/{id}/messages    # 发送消息 + AI 回复

# 触发器
POST /trigger/page-change           # 页面切换触发
POST /trigger/operation             # 操作完成触发

# 轮询
GET  /poll                          # 轮询新消息
```

### 3.2 Frontend Layer Analysis

| Component | File | Status | Completeness |
|-----------|------|--------|-------------|
| Widget HTML | `templates/components/ai_assistant_widget.html` | ✅ Done | 100% |
| Message Templates | `templates/components/ai_message_bubble.html` | ✅ Done | 100% |
| Core JavaScript | `static/js/ai-assistant.js` | ✅ Done | 95% |
| Base Template | `templates/base.html:841-844` | ✅ Done | 100% |

**Frontend Features Implemented**:
- 浮窗按钮 + 展开/收起动画
- 对话面板 (消息列表 + 输入框)
- 消息气泡渲染 (用户/助手/系统)
- 打字机效果 (typewriter)
- 加载动画 (3 dots bounce)
- 快捷提示按钮
- 字符计数 (>1800 显示)
- 未读消息徽章
- 新建对话按钮

**JavaScript 模块** (`ai-assistant.js`):
```javascript
// 状态管理
state = { conversationId, lastMessageId, isOpen, isLoading, ... }

// API 调用
apiCall(), getActiveConversation(), createNewConversation()
loadMessages(), sendMessage(), pollNewMessages()
triggerPageChange()

// UI 交互
toggleWidget(), showLoading(), hideLoading()
appendMessage(), typewriterEffect()

// 公开 API
window.AIAssistant = {
    toggle: toggleWidget,
    triggerOperationFeedback: async (operationType, result, details) => {...}
}
```

### 3.3 Integration Points Analysis

| Integration | Status | Notes |
|-------------|--------|-------|
| Blueprint 注册 | ⚠️ 需验证 | `app.py` 中需确认注册 |
| AI 服务端点 | ⚠️ 需验证 | `Config.AI_ASSISTANT_CHAT_ENDPOINT` |
| SPA 导航检测 | ✅ Done | popstate + 链接点击拦截 |
| 多标签页同步 | ✅ Done | localStorage 事件 |
| 操作完成触发 | 🔄 Partial | 接口已定义，需集成到操作点 |

---

## Phase 4: Remaining Tasks (Priority Ordered)

### 4.1 Critical - Must Complete

#### Task C1: 验证 Blueprint 注册
**File**: `app.py`
**Issue**: 需确认 `ai_assistant_bp` 已正确注册
**Action**:
```python
# 在 app.py 中验证存在:
from blueprints.ai_assistant import ai_assistant_bp
app.register_blueprint(ai_assistant_bp, url_prefix='/api/assistant')
```

#### Task C2: 验证 AI 服务端点配置
**File**: `config.py`
**Issue**: 确认端点指向正确的 AI 微服务
**Action**:
```python
# 确认存在:
AI_ASSISTANT_CHAT_ENDPOINT = 'http://127.0.0.1:9011/chat'
# 或基于环境变量:
AI_ASSISTANT_BASE_URL = os.getenv('AI_ASSISTANT_BASE_URL', 'http://127.0.0.1:9011')
AI_ASSISTANT_CHAT_ENDPOINT = f"{AI_ASSISTANT_BASE_URL}/chat"
```

#### Task C3: 端到端基本流程测试
**测试步骤**:
1. 启动 AI 微服务 (`python ai_assistant.py`)
2. 启动主应用 (`python app.py`)
3. 登录系统
4. 点击右下角浮窗按钮
5. 发送消息 "你好"
6. 验证收到 AI 回复
7. 刷新页面，验证消息历史保留

### 4.2 Important - Should Complete

#### Task I1: 集成操作完成触发器
**触发点清单**:

| 操作 | 文件 | 触发位置 |
|------|------|----------|
| 生成批改核心 | `templates/ai_generator.html` | AJAX 成功回调 |
| 导入学生 | `templates/student_import.html` | 导入成功后 |
| 创建班级 | `templates/new_class.html` | 创建成功后 |
| 导出成绩 | `templates/export.html` | 导出完成后 |

**集成示例**:
```javascript
// 在操作成功的回调中添加:
if (response.ok && window.AIAssistant) {
    window.AIAssistant.triggerOperationFeedback(
        'generate_grader',  // 操作类型
        'success',          // 结果
        {                   // 详情
            grader_name: data.grader_name,
            question_count: data.question_count
        }
    );
}
```

#### Task I2: 修复 base.html 中的重复 AI 按钮
**Issue**: `base.html:806-835` 存在旧版 AI 聊天按钮 (`#ai-chat-fab`, `#ai-chat-modal`)，与新浮窗组件冲突
**Action**: 移除旧版代码或隐藏

#### Task I3: 添加错误处理 Toast 提示
**File**: `static/js/ai-assistant.js`
**Action**: 发送失败时调用 `window.showToast()`
```javascript
catch (e) {
    hideLoading();
    if (window.showToast) {
        window.showToast('消息发送失败，请稍后重试', 'error');
    }
    // 现有逻辑...
}
```

### 4.3 Nice to Have - Optional

#### Task O1: 提取 Widget CSS 到独立文件
**Current**: 样式内联在 `ai_assistant_widget.html`
**Target**: 移动到 `static/css/ai-assistant.css`

#### Task O2: Markdown 渲染支持
**Action**: AI 回复使用 `marked.min.js` 渲染
```javascript
if (withTypewriter && message.role === 'assistant') {
    // 完成打字机后渲染 Markdown
    const html = marked.parse(message.content);
    contentEl.innerHTML = html;
}
```

#### Task O3: 键盘快捷键
- `Ctrl/Cmd + /` 打开/关闭浮窗
- `Esc` 关闭浮窗

#### Task O4: 对话历史列表
**Action**: 添加历史对话列表面板，支持切换历史对话

---

## Phase 5: Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Browser (Frontend)                          │
├─────────────────────────────────────────────────────────────────────┤
│  ai_assistant_widget.html                                           │
│  ├── 浮窗按钮 (#ai-toggle-btn)                                      │
│  ├── 对话面板 (#ai-chat-panel)                                      │
│  │   ├── 消息列表 (#ai-messages)                                    │
│  │   └── 输入区域 (#ai-input, #ai-send-btn)                         │
│  └── 未读徽章 (#ai-unread-badge)                                    │
│                                                                     │
│  ai-assistant.js                                                    │
│  ├── toggleWidget()           展开/收起                             │
│  ├── handleSendMessage()      发送消息                              │
│  ├── pollNewMessages()        轮询同步                              │
│  ├── handlePageChange()       页面切换检测                          │
│  └── triggerOperationFeedback() 操作触发 (公开 API)                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ fetch('/api/assistant/...')
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Flask App (app.py:5010)                        │
├─────────────────────────────────────────────────────────────────────┤
│  blueprints/ai_assistant.py                                         │
│  ├── /conversations/active      GET  获取/创建活跃对话              │
│  ├── /conversations             POST 创建新对话                     │
│  ├── /conversations/{id}/messages                                   │
│  │   ├── GET  获取消息历史                                          │
│  │   └── POST 发送消息 + 获取 AI 回复                               │
│  ├── /trigger/page-change       POST 页面切换触发                   │
│  ├── /trigger/operation         POST 操作完成触发                   │
│  └── /poll                      GET  轮询新消息                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌───────────────────────────────┐   ┌─────────────────────────────────┐
│   services/                   │   │   AI Microservice               │
│   ai_conversation_service.py  │   │   (ai_assistant.py:9011)        │
├───────────────────────────────┤   ├─────────────────────────────────┤
│ create_conversation()         │   │ POST /chat                      │
│ get_active_conversation()     │   │ ├── 调用 AI 厂商 API            │
│ add_message()                 │   │ │   (OpenAI / 火山引擎)         │
│ get_messages()                │   │ └── 返回 AI 回复                │
│ check_rate_limit()            │   └─────────────────────────────────┘
│ update_rate_limit()           │
└───────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────┐
│   SQLite Database             │
│   data/grading_system_v2.db   │
├───────────────────────────────┤
│ ai_conversations              │
│ ai_messages                   │
│ ai_rate_limits                │
└───────────────────────────────┘
```

---

## Phase 6: Testing Checklist

### 6.1 Manual Testing

**基本流程**:
- [ ] 登录后浮窗按钮可见
- [ ] 点击按钮展开对话面板
- [ ] 发送消息后显示用户气泡
- [ ] 显示加载动画
- [ ] 收到 AI 回复并显示打字机效果
- [ ] 点击关闭按钮收起面板
- [ ] 再次点击展开，消息历史保留

**新建对话**:
- [ ] 点击新建按钮
- [ ] 历史消息清空
- [ ] 显示欢迎占位符

**页面切换**:
- [ ] 切换到不同页面
- [ ] (首次) 收到页面问候消息
- [ ] (60秒内再次切换) 不触发新消息

**错误处理**:
- [ ] AI 服务不可用时显示错误提示
- [ ] 网络断开时显示错误提示

### 6.2 API Testing (curl/httpie)

```bash
# 获取活跃对话
curl http://localhost:5010/api/assistant/conversations/active \
  -H "Cookie: session=<your_session>"

# 发送消息
curl -X POST http://localhost:5010/api/assistant/conversations/1/messages \
  -H "Content-Type: application/json" \
  -H "Cookie: session=<your_session>" \
  -d '{"content": "你好", "page_context": "dashboard"}'
```

---

## Phase 7: Deployment Notes

### 7.1 Dependencies
无新增依赖，使用现有 `httpx`, `flask` 等。

### 7.2 Database
表已在 `database.py` 定义，首次运行自动创建。无需手动迁移。

### 7.3 Configuration Checklist
- [ ] `AI_ASSISTANT_BASE_URL` 指向 AI 微服务
- [ ] `AI_ASSISTANT_CHAT_ENDPOINT` 可达
- [ ] AI 微服务 (`ai_assistant.py`) 已启动

---

## Appendix: File Reference

| File | Lines | Description |
|------|-------|-------------|
| `database.py` | 1173-1246 | AI 对话相关表定义 |
| `blueprints/ai_assistant.py` | 全文 | API 路由端点 |
| `services/ai_conversation_service.py` | 全文 | 对话 CRUD 服务 |
| `services/ai_content_service.py` | 511-749 | AI 对话内容生成 |
| `services/ai_prompts.py` | 234-412 | 对话系统提示词 |
| `templates/components/ai_assistant_widget.html` | 全文 | 浮窗 HTML + CSS |
| `templates/components/ai_message_bubble.html` | 全文 | 消息模板 |
| `static/js/ai-assistant.js` | 全文 | 前端交互逻辑 |
| `templates/base.html` | 841-844 | 组件集成 |
