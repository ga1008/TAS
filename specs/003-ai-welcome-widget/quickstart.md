# Quickstart: AI 欢迎语功能改进

**Date**: 2026-01-24
**Feature**: 003-ai-welcome-widget

## 开发环境准备

### 1. 启动服务

```bash
# 终端 1: 启动主 Flask 应用
python app.py
# 监听: http://127.0.0.1:5010

# 终端 2: 启动 AI 助手微服务
python ai_assistant.py
# 监听: http://127.0.0.1:9011
```

### 2. 确认 AI 配置

登录管理员后台 (`/admin`) 确保已配置至少一个 `standard` 能力的 AI 模型。

---

## 关键文件位置

| 文件 | 用途 |
|-----|-----|
| `blueprints/ai_welcome.py` | 后端 API 路由 |
| `services/ai_content_service.py` | AI 内容生成与缓存 |
| `services/ai_prompts.py` | 提示词模板 |
| `templates/components/ai_assistant_widget.html` | 浮动窗口 UI |
| `static/js/ai-welcome.js` | 前端交互逻辑 |

---

## 快速测试

### 1. 测试定时触发

```javascript
// 在浏览器控制台执行
AIWelcome.startProactiveTimer();
// 等待 1-10 分钟，观察右下角气泡弹出

// 或手动触发（跳过定时器）
await fetch('/api/welcome/messages', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    page_context: 'dashboard',
    trigger_type: 'timer'
  })
}).then(r => r.json()).then(console.log);
```

### 2. 测试操作反馈

```javascript
// 模拟批改核心生成成功
AIWelcome.triggerAction('generate_grader', {
  grader_name: '测试核心',
  grader_id: 'test_123'
});
```

### 3. 测试聊天功能

```javascript
// 打开聊天窗口
AIWelcome.toggleChat();

// 发送消息
await AIWelcome.sendMessage('怎么批改作业？');
```

### 4. 测试动画效果

```javascript
// 显示气泡（3秒后自动消失）
AIWelcome.showBubble('测试气泡消息 🎉', true);

// 显示气泡（不自动消失）
AIWelcome.showBubble('这条消息不会自动消失', false);
```

---

## 开发调试技巧

### 1. 绕过速率限制

```python
# 在 ai_welcome.py 中临时修改
cooldown = 1  # 从 60 秒改为 1 秒
```

### 2. 查看 AI 原始响应

```python
# 在 ai_content_service.py 的 _call_ai_for_welcome 函数中添加
logger.debug(f"AI 原始响应: {content}")
```

### 3. 查看 sessionStorage

```javascript
// 浏览器控制台
JSON.parse(sessionStorage.getItem('ai_chat_history'))
```

### 4. 清理测试数据

```sql
-- SQLite 命令行
DELETE FROM ai_welcome_messages WHERE user_id = 1;
DELETE FROM ai_messages;
DELETE FROM ai_conversations;
DELETE FROM ai_rate_limits;
```

---

## 常见问题

### Q: 气泡不显示？

1. 检查用户是否已登录
2. 检查 AI 服务是否运行 (`curl http://127.0.0.1:9011/health`)
3. 检查浏览器控制台是否有报错
4. 检查速率限制是否生效

### Q: AI 返回内容不符合"老油条"风格？

检查 `services/ai_prompts.py` 中的 Few-Shot 示例是否正确配置。

### Q: 动画卡顿？

1. 确保使用 CSS transition 而非 JavaScript 动画
2. 检查是否有大量 DOM 操作
3. 使用 Chrome DevTools Performance 面板分析

### Q: sessionStorage 数据丢失？

这是预期行为 - 关闭浏览器后清空。如需持久化，需修改为 localStorage 或后端存储。

---

## 验收检查清单

- [ ] 定时触发：停留页面 1-10 分钟后弹出气泡
- [ ] 操作触发：生成批改核心后弹出反馈
- [ ] 手动对话：点击按钮展开窗口，可发送消息
- [ ] 动画效果：展开/收起/弹出动画 ≤300ms
- [ ] 速率限制：定时触发 60s 冷却，操作触发 10s 冷却
- [ ] 数据持久化：欢迎语保存到数据库
- [ ] 30天清理：旧记录自动清理
- [ ] 回退消息：AI 不可用时显示预设消息
- [ ] 思考动画：AI 响应期间显示三点跳动，无文字
