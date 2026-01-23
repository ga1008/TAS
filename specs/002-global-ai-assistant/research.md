# Research: 全局 AI 助手重构

**Feature**: 002-global-ai-assistant
**Date**: 2026-01-23

## 1. 多标签页同步机制

### Decision: localStorage 事件 + 定时轮询混合方案

### Rationale
- **localStorage 事件** (`storage` event): 当一个标签页写入 localStorage 时，其他标签页可以通过监听 `storage` 事件实时感知变化。延迟几乎为 0，无需服务器开销。
- **定时轮询**: 作为补充，每 3-5 秒轮询服务器获取最新消息 ID，处理 localStorage 事件丢失的边缘情况。

### Alternatives Considered
1. **WebSocket**: 实时性最好，但需要额外的服务器基础设施，增加复杂度。
2. **Server-Sent Events (SSE)**: 比 WebSocket 简单，但需要长连接支持，对现有 Flask 架构改动较大。
3. **纯轮询**: 实现简单但延迟高、服务器压力大。

### Implementation Notes
```javascript
// 标签页 A 发送消息后
localStorage.setItem('ai_assistant_last_message', JSON.stringify({
    timestamp: Date.now(),
    conversation_id: conversationId,
    message_id: newMessageId
}));

// 标签页 B 监听
window.addEventListener('storage', (e) => {
    if (e.key === 'ai_assistant_last_message') {
        const data = JSON.parse(e.newValue);
        if (data.conversation_id === currentConversationId) {
            fetchNewMessages(data.message_id);
        }
    }
});
```

---

## 2. 防抖策略

### Decision: 前端 1 分钟冷却 + 后端双重验证

### Rationale
根据 spec 要求，主动触发（页面切换、操作完成）需要 1 分钟间隔限制。防止快速页面切换造成 AI 打扰。

### Implementation

**前端防抖**:
```javascript
const PROACTIVE_COOLDOWN = 60 * 1000; // 1 分钟
let lastProactiveTrigger = 0;

function canTriggerProactive() {
    const now = Date.now();
    if (now - lastProactiveTrigger < PROACTIVE_COOLDOWN) {
        return false;
    }
    lastProactiveTrigger = now;
    return true;
}
```

**后端验证** (数据库记录):
```python
# ai_rate_limits 表
# user_id | last_proactive_trigger

def can_trigger_proactive(user_id: int) -> bool:
    row = db.get_rate_limit(user_id)
    if row and (now - row.last_proactive_trigger) < 60:
        return False
    db.update_rate_limit(user_id, now)
    return True
```

### Alternatives Considered
1. **纯前端**: 刷新页面会重置，无法真正限制。
2. **Redis**: 更适合高并发场景，但对当前 SQLite 架构过度工程。

---

## 3. 流式输出效果

### Decision: 复用现有 typewriter 实现，扩展至对话气泡

### Rationale
`ai-welcome.js` 已有成熟的 typewriter 实现，支持：
- 每字符 30ms 延迟
- 最大执行时间 5s 保护
- 容器高度自适应
- 光标动画效果

### Implementation Notes
需要将 typewriter 函数提取到通用模块，供 AI 助手复用：

```javascript
// static/js/ai-typewriter.js (新建通用模块)
export function typewriter(element, text, options = {}) {
    const config = {
        speed: options.speed || 30,
        maxTime: options.maxTime || 5000,
        onComplete: options.onComplete || (() => {})
    };
    // ... 现有逻辑
}
```

对于 AI 对话场景，后端返回完整消息（非 streaming），前端使用 typewriter 模拟流式效果。真正的 streaming 需要 SSE/WebSocket，复杂度过高。

---

## 4. 现有代码复用分析

### 可复用组件

| 组件 | 来源 | 复用方式 |
|------|------|----------|
| `MessageContext` dataclass | `ai_content_service.py` | 直接复用，扩展 conversation_id 字段 |
| `validate_message_content()` | `ai_content_service.py` | 直接复用 |
| `_call_ai_for_welcome()` | `ai_content_service.py` | 重构为通用 `call_ai()` |
| `get_user_stats()` | `ai_welcome.py` | 直接复用 |
| `get_recent_actions()` | `ai_welcome.py` | 直接复用 |
| `typewriter()` | `ai-welcome.js` | 提取到通用模块 |
| `detectPageContext()` | `ai-welcome.js` | 直接复用 |
| Tailwind 配置 | `base.html` | 自动继承 |
| 玻璃态样式 | `FRONTEND_GUIDE.md` | 遵循规范 |

### 需要新建的组件

| 组件 | 位置 | 职责 |
|------|------|------|
| `AIConversation` model | `ai_conversation_service.py` | 会话管理 |
| `AIMessage` model | `ai_conversation_service.py` | 消息管理 |
| `ai_assistant.py` blueprint | `blueprints/` | API 端点 |
| `ai_assistant_widget.html` | `templates/components/` | 浮窗 UI |
| `ai-assistant.js` | `static/js/` | 浮窗逻辑 |

### 重构建议

1. **提取通用 AI 调用逻辑**:
   - 将 `_call_ai_for_welcome()` 重构为 `call_ai(system_prompt, messages, user_message)`
   - 支持多轮对话历史传递

2. **提取上下文构建逻辑**:
   - `get_user_stats()` 和 `get_recent_actions()` 移至 `services/` 层
   - 供 ai_welcome 和 ai_assistant 共同使用

3. **前端模块化**:
   - 创建 `ai-common.js` 存放 typewriter、localStorage 工具
   - `ai-welcome.js` 和 `ai-assistant.js` 都引用该模块

---

## 5. 系统提示词设计

### Decision: 结构化 JSON 上下文 + 少样本示例

### System Prompt Template
```
你是一个智能教学助手，帮助教师高效完成作业批改和学生管理工作。

## 你的角色
- 友好、专业、有温度
- 主动提供帮助和建议
- 理解教师的工作压力

## 当前上下文
- 用户: {username}
- 当前时间: {current_time} ({weekday})
- 当前页面: {page_context_display}
- 系统状态:
  - 班级数: {class_count}
  - 学生数: {student_count}
  - 待处理任务: {pending_task_count}
  - 批改核心数: {grader_count}
- 最近操作: {recent_actions_str}

## 响应要求
1. 消息长度: 150-300 字
2. 语气: 自然友好，避免机械
3. 内容: 结合上下文给出有针对性的建议
4. 格式: 纯文本，不使用 Markdown

## 示例对话
用户: 我该怎么开始批改？
助手: 张老师好！我看到您已经创建了"计算机基础 2401 班"，并上传了 45 名学生名单。现在可以开始批改流程了：首先在"AI 生成"页面创建批改核心，上传试卷和评分标准后，系统会自动生成批改脚本。有任何问题随时问我！
```

---

## 6. 数据库表设计预研

### 消息保留策略
根据 spec FR-012a，每个会话最多保留 100 条消息。

实现方案：
```python
def add_message(conversation_id, role, content, trigger_type):
    # 1. 插入新消息
    msg_id = db.insert_message(...)

    # 2. 检查并清理超出的消息
    db.execute('''
        DELETE FROM ai_messages
        WHERE conversation_id = ?
        AND id NOT IN (
            SELECT id FROM ai_messages
            WHERE conversation_id = ?
            ORDER BY created_at DESC
            LIMIT 100
        )
    ''', (conversation_id, conversation_id))

    return msg_id
```

---

## 7. 边缘情况处理

### 管理员页面行为
- 显示浮窗按钮但默认收起
- 不触发自动问候
- 仅响应用户主动点击

实现：`base.html` 中通过 Jinja2 变量控制：
```html
{% if not is_admin_page %}
    <script>AIAssistant.enableAutoGreeting();</script>
{% endif %}
```

### AI 服务不可用
- 显示友好提示："AI 助手暂时不可用，请稍后再试"
- 不阻塞用户操作
- 保留输入框允许用户输入（但发送时提示不可用）

### 网络延迟
- 请求超时：8 秒
- 显示加载动画
- 超时后显示重试按钮

---

## Summary

所有 NEEDS CLARIFICATION 已解决：

1. ✅ 多标签页同步: localStorage 事件 + 轮询
2. ✅ 防抖策略: 前端 + 后端双重验证
3. ✅ 流式输出: 复用 typewriter
4. ✅ 代码复用: 识别出 8 个可复用组件
5. ✅ 系统提示词: 结构化设计
6. ✅ 消息保留: LIMIT 100 策略
7. ✅ 边缘情况: 全部覆盖
