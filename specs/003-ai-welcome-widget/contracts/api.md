# API Contracts: AI 欢迎语功能改进

**Date**: 2026-01-24
**Base Path**: `/api/welcome`

## 1. 获取欢迎语 (主动触发)

**Endpoint**: `POST /api/welcome/messages`

### Request

```json
{
  "page_context": "dashboard",
  "trigger_type": "timer",
  "action_details": ""
}
```

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|-----|
| page_context | string | 是 | 页面上下文: dashboard, tasks, ai_generator, student_list, export |
| trigger_type | string | 是 | 触发类型: timer (定时), action (操作后) |
| action_details | string | 否 | 操作详情 (仅 action 类型有效) |

### Response - Success

```json
{
  "status": "success",
  "data": {
    "id": 123,
    "user_id": 1,
    "page_context": "dashboard",
    "message_content": "早上好老铁！又是元气满满的摸鱼日 🐟 先把那3份作业批了？",
    "created_at": "2026-01-24T08:30:00",
    "expires_at": "2026-01-24T09:00:00",
    "storage_key": "ai_welcome_seen_dashboard_123",
    "is_new": true
  }
}
```

### Response - Rate Limited

```json
{
  "status": "silence",
  "message": "Rate limited. Try again in 45s"
}
```

### Response - Fallback

```json
{
  "status": "fallback",
  "data": {
    "message_content": "欢迎回来！今天也要加油哦 💪"
  }
}
```

---

## 2. 对话接口

**Endpoint**: `POST /api/welcome/chat`

### Request

```json
{
  "message": "怎么批改作业？",
  "page_context": "dashboard"
}
```

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|-----|
| message | string | 是 | 用户发送的消息 |
| page_context | string | 否 | 当前页面上下文 |

### Response - Success

```json
{
  "status": "success",
  "data": {
    "reply": "批改作业？简单！先去'AI工具→生成核心'上传试卷，然后创建班级导入学生，最后一键批改。要不要我带你走一遍？",
    "timestamp": "2026-01-24T08:31:00"
  }
}
```

### Response - Error

```json
{
  "status": "error",
  "message": "AI 暂时掉线了"
}
```

---

## 3. 获取回退消息

**Endpoint**: `GET /api/welcome/fallback`

### Response

```json
{
  "status": "success",
  "data": {
    "message": "欢迎回来！有什么可以帮你的吗？"
  }
}
```

---

## 4. 操作反馈接口 (新增)

**Endpoint**: `POST /api/welcome/operation-feedback`

### Request

```json
{
  "operation_type": "generate_grader",
  "operation_result": "success",
  "details": {
    "grader_name": "计算机网络期末考试",
    "grader_id": "grader_abc123"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|-----|
| operation_type | string | 是 | 操作类型: generate_grader, import_students, create_class, grading_complete, export_grades |
| operation_result | string | 是 | 操作结果: success, error |
| details | object | 否 | 操作详情 |

### Response

```json
{
  "status": "success",
  "data": {
    "message_content": "批改核心生成完毕！建议先泡杯咖啡再开工 ☕ 下一步：创建班级导入学生"
  }
}
```

---

## 错误码

| HTTP Status | status 字段 | 说明 |
|-------------|------------|-----|
| 200 | success | 成功 |
| 200 | silence | 被速率限制，静默处理 |
| 200 | fallback | AI 不可用，使用回退消息 |
| 400 | error | 请求参数错误 |
| 401 | error | 未登录 |
| 500 | error | 服务器内部错误 |

---

## 前端 JavaScript API

### AIWelcome 全局对象

```typescript
interface AIWelcome {
  // 初始化（页面加载时自动调用）
  init(): void;

  // 显示气泡消息
  showBubble(content: string, autoHide?: boolean): void;

  // 隐藏气泡消息
  hideBubble(): void;

  // 切换聊天窗口
  toggleChat(): void;

  // 发送聊天消息
  sendMessage(content: string): Promise<string>;

  // 触发操作反馈
  triggerAction(operationType: string, details?: object): void;

  // 设置当前页面上下文
  setPageContext(context: string): void;

  // 启动定时触发器
  startProactiveTimer(): void;

  // 停止定时触发器
  stopProactiveTimer(): void;
}

// 全局访问
declare const AIWelcome: AIWelcome;
```

### 使用示例

```javascript
// 操作成功后触发反馈
function onGraderGenerateSuccess(graderId, graderName) {
  AIWelcome.triggerAction('generate_grader', {
    grader_id: graderId,
    grader_name: graderName
  });
}

// 页面切换时更新上下文
function onPageNavigate(pageName) {
  AIWelcome.setPageContext(pageName);
}
```
