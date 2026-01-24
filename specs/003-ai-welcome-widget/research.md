# Research: AI 欢迎语功能改进

**Date**: 2026-01-24
**Feature**: 003-ai-welcome-widget

## 1. 前端动画实现方案

### Decision
使用 Tailwind CSS 内置 `transition` + `transform` + `opacity` 组合，配合 JavaScript 类名切换实现丝滑动画。

### Rationale
- 项目已使用 Tailwind CSS，无需引入额外动画库
- CSS transition 性能优于 JavaScript 动画
- 可复用 `base.html` 中已定义的 `keyframes`（fadeIn, slideUp 等）

### Alternatives Considered
- **Framer Motion**: 功能强大但需要 React，不适合 Jinja2 模板
- **Animate.css**: 需额外引入 CSS 文件，增加加载时间
- **GSAP**: 功能过于复杂，学习成本高

### Implementation Pattern
```css
/* 气泡弹出动画 */
.bubble-enter {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}
.bubble-active {
  transform: scale(1) translateY(0);
  opacity: 1;
  transition: all 300ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

---

## 2. 对话历史 sessionStorage 方案

### Decision
使用 `sessionStorage` 存储当前会话的聊天历史，key 格式为 `ai_chat_history`。

### Rationale
- 符合规格要求：当前会话保留，关闭浏览器后清空
- sessionStorage 自动按标签页隔离，多标签页互不影响
- 无需后端参与，降低复杂度

### Alternatives Considered
- **localStorage**: 永久保留，不符合规格要求
- **IndexedDB**: 过于复杂，数据量小时无优势
- **后端数据库**: 增加网络开销，规格明确不需要跨会话保留

### Data Structure
```javascript
// sessionStorage 存储格式
{
  "messages": [
    {"role": "assistant", "content": "嗨！有什么可以帮你的？", "timestamp": "2026-01-24T10:00:00"},
    {"role": "user", "content": "怎么批改作业？", "timestamp": "2026-01-24T10:00:05"}
  ],
  "lastUpdated": "2026-01-24T10:00:05"
}
```

---

## 3. 定时器触发机制

### Decision
使用 `setTimeout` 配合随机延迟（1-10分钟），页面切换时重置定时器。

### Rationale
- `setTimeout` 比 `setInterval` 更灵活，可在每次触发后重新计算随机时间
- 页面切换时重置避免累积触发
- 配合 `visibilitychange` 事件，用户离开页面时暂停

### Alternatives Considered
- **setInterval**: 固定间隔，无法实现随机触发
- **Web Workers**: 增加复杂度，无明显优势
- **requestAnimationFrame**: 不适合长时间定时任务

### Implementation Pattern
```javascript
let welcomeTimer = null;

function scheduleNextWelcome() {
  clearTimeout(welcomeTimer);
  // 1-10 分钟随机延迟
  const delay = (Math.random() * 9 + 1) * 60 * 1000;
  welcomeTimer = setTimeout(triggerProactiveWelcome, delay);
}

document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    clearTimeout(welcomeTimer);
  } else {
    scheduleNextWelcome();
  }
});
```

---

## 4. "互联网老油条"人设提示词

### Decision
使用详细的角色设定 + 8-10 个 Few-Shot 示例，强调冷幽默、网感、无厘头风格。

### Rationale
- Standard 模型需要明确示例才能稳定输出
- 中文互联网语境特殊，需大量本土化示例
- 40字限制需要在示例中体现

### Alternatives Considered
- **简单指令**: "请用幽默语气" - 输出不稳定
- **英文示例**: 翻译后网感丧失
- **长篇描述**: 消耗 token，效果不如示例

### Prompt Template Structure
```
[角色设定] 你是一个混迹贴吧、知乎多年的互联网老油条...
[输出要求] 40字以内，可用表情，给出下一步建议
[Few-Shot 示例 x 10]
[当前上下文] 用户名、时间、统计、最近操作
[触发原因] timer/action/chat
```

### Few-Shot 示例库
```
1. 早上好啊老铁！又是元气满满的摸鱼日 🐟 先把那3份作业批了？
2. 深夜还在肝？注意身体，批完这波就睡 💤
3. 哟，刚导入200个学生，这波韭菜够割一学期了 😏
4. 批改核心生成完毕！建议先泡杯咖啡再开工 ☕
5. 又创建新班级了？教书匠の日常，respect！
6. 下午茶时间到，批完这5份就去摸鱼吧 🍵
7. 周一综合症？我懂，先从简单的作业开始批 💪
8. 成绩导出成功！建议保存三份备份，以防教务处甩锅
9. 这批作业质量堪忧啊，要不要考虑降低标准？（开玩笑的）
10. 晚安！明天继续当社畜，作业不急，先睡 😴
```

---

## 5. 操作触发事件绑定

### Decision
在前端关键操作成功回调中调用 `AIWelcome.triggerAction(operationType, details)`。

### Rationale
- 前端已有操作成功回调（Toast 提示处），易于集成
- 避免后端复杂的事件系统
- 可精确控制触发时机

### 5 个核心操作触发点
| 操作类型 | 触发位置 | action_type 值 |
|---------|---------|---------------|
| 生成批改核心 | `ai_generator.html` 生成成功回调 | `generate_grader` |
| 导入学生名单 | 学生管理页导入成功回调 | `import_students` |
| 创建班级 | 班级创建成功回调 | `create_class` |
| 批改完成 | 批改进度 100% 回调 | `grading_complete` |
| 成绩导出 | 导出成功回调 | `export_grades` |

---

## 6. 30天数据清理方案

### Decision
在应用启动时和每天凌晨执行清理任务，使用 SQLite 日期函数。

### Rationale
- SQLite 支持 `datetime('now', '-30 days')` 语法
- 启动时清理确保立即生效
- 定时清理避免数据堆积

### Implementation
```python
def cleanup_old_welcome_messages():
    """清理超过30天的欢迎语记录"""
    conn = db.get_connection()
    conn.execute('''
        DELETE FROM ai_welcome_messages
        WHERE created_at < datetime('now', '-30 days')
    ''')
    conn.commit()
```

---

## Summary

| 研究项 | 决策 | 关键技术 |
|-------|-----|--------|
| 动画方案 | Tailwind CSS transition | cubic-bezier 弹性曲线 |
| 会话存储 | sessionStorage | JSON 序列化 |
| 定时触发 | setTimeout + 随机延迟 | visibilitychange 事件 |
| AI 人设 | Few-Shot 示例驱动 | 10+ 本土化示例 |
| 操作触发 | 前端回调绑定 | 5 个核心操作点 |
| 数据清理 | SQLite datetime 函数 | 启动时 + 每日定时 |
