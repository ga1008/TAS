# Quickstart: 全局 AI 助手开发指南

**Feature**: 002-global-ai-assistant
**Date**: 2026-01-23

## 环境准备

### 1. 安装依赖

```bash
# 项目已有依赖，无需额外安装
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 终端 1: 启动主应用
python app.py

# 终端 2: 启动 AI 助手微服务
python ai_assistant.py
```

### 3. 验证服务

```bash
# 检查主应用
curl http://localhost:5010/health

# 检查 AI 服务
curl http://localhost:9011/health
```

---

## 快速开始

### 1. 数据库迁移

新表会在 `database.py` 初始化时自动创建，无需手动执行迁移脚本。

```python
# database.py 中添加的表会在首次连接时自动创建
# ai_conversations, ai_messages, ai_rate_limits
```

### 2. 创建蓝图

```python
# blueprints/ai_assistant.py
from flask import Blueprint, jsonify, request, session

ai_assistant_bp = Blueprint('ai_assistant', __name__, url_prefix='/api/assistant')

@ai_assistant_bp.route('/conversations/active', methods=['GET'])
def get_active_conversation():
    user_id = session.get('user_id')
    # ... 实现逻辑
    return jsonify({'status': 'success', 'data': conversation})
```

### 3. 注册蓝图

```python
# app.py
from blueprints.ai_assistant import ai_assistant_bp

# 在 create_app() 中注册
app.register_blueprint(ai_assistant_bp)
```

### 4. 创建前端组件

```html
<!-- templates/components/ai_assistant_widget.html -->
<div id="ai-assistant-widget" class="fixed bottom-6 right-6 z-50">
    <!-- 浮窗按钮 -->
    <button id="ai-toggle-btn" class="w-14 h-14 rounded-full bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-lg shadow-indigo-300/50 hover:shadow-indigo-400/60 hover:-translate-y-0.5 transition-all duration-300 flex items-center justify-center">
        <i class="fas fa-robot text-xl"></i>
    </button>

    <!-- 对话框 -->
    <div id="ai-chat-panel" class="hidden absolute bottom-16 right-0 w-96 glass-panel rounded-2xl shadow-xl overflow-hidden">
        <!-- 头部 -->
        <div class="p-4 border-b border-white/20 flex items-center justify-between">
            <h3 class="font-bold text-slate-800">AI 助手</h3>
            <button id="ai-close-btn" class="text-slate-400 hover:text-slate-600">
                <i class="fas fa-times"></i>
            </button>
        </div>

        <!-- 消息列表 -->
        <div id="ai-messages" class="h-80 overflow-y-auto p-4 space-y-3">
            <!-- 消息气泡动态插入 -->
        </div>

        <!-- 输入区 -->
        <div class="p-4 border-t border-white/20">
            <div class="flex gap-2">
                <input type="text" id="ai-input"
                       class="flex-1 px-4 py-2.5 rounded-xl border-0 bg-white/50 focus:bg-white focus:ring-2 focus:ring-indigo-100 transition-all outline-none text-sm"
                       placeholder="输入消息...">
                <button id="ai-send-btn" class="px-4 py-2.5 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 transition-colors">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
    </div>
</div>
```

### 5. 集成到 base.html

```html
<!-- templates/base.html -->
{% if current_user and current_user.is_authenticated %}
    {% include 'components/ai_assistant_widget.html' %}
    <script src="{{ url_for('static', filename='js/ai-assistant.js') }}"></script>
{% endif %}
```

---

## 开发流程

### 后端开发顺序

1. **数据库层** (`database.py`)
   - 添加表创建 SQL
   - 添加索引

2. **服务层** (`services/ai_conversation_service.py`)
   - 实现 CRUD 操作
   - 实现消息限制逻辑
   - 实现速率限制检查

3. **蓝图层** (`blueprints/ai_assistant.py`)
   - 实现 API 端点
   - 参数验证
   - 错误处理

4. **提示词** (`services/ai_prompts.py`)
   - 添加对话场景提示词
   - 添加操作反馈提示词

### 前端开发顺序

1. **HTML 组件**
   - `ai_assistant_widget.html` - 浮窗主组件
   - `ai_message_bubble.html` - 消息气泡

2. **JavaScript 逻辑** (`static/js/ai-assistant.js`)
   - 浮窗展开/收起
   - 消息发送/接收
   - 页面切换触发
   - 操作完成触发
   - 多标签页同步

3. **样式调整**
   - 遵循 `FRONTEND_GUIDE.md`
   - 玻璃态效果
   - 动画过渡

---

## 测试场景

### 基础功能测试

```bash
# 1. 获取活跃会话
curl -X GET http://localhost:5010/api/assistant/conversations/active \
  -H "Cookie: session=xxx"

# 2. 发送消息
curl -X POST http://localhost:5010/api/assistant/conversations/1/messages \
  -H "Content-Type: application/json" \
  -H "Cookie: session=xxx" \
  -d '{"content": "你好", "page_context": "dashboard"}'

# 3. 触发页面切换
curl -X POST http://localhost:5010/api/assistant/trigger/page-change \
  -H "Content-Type: application/json" \
  -H "Cookie: session=xxx" \
  -d '{"page_context": "ai_generator"}'
```

### 边缘情况测试

1. **速率限制**: 连续触发页面切换，验证 1 分钟限制
2. **消息上限**: 发送 100+ 条消息，验证自动清理
3. **AI 不可用**: 停止 AI 服务，验证降级处理
4. **多标签页**: 在两个标签页打开，验证消息同步

---

## 关键文件清单

### 新建文件

```
bluepints/ai_assistant.py           # API 蓝图
services/ai_conversation_service.py # 对话服务
templates/components/ai_assistant_widget.html  # 浮窗组件
templates/components/ai_message_bubble.html    # 消息气泡
static/js/ai-assistant.js           # 前端逻辑
```

### 修改文件

```
database.py                 # 新增表
app.py                      # 注册蓝图
templates/base.html         # 注入浮窗
services/ai_prompts.py      # 新增提示词
services/ai_content_service.py  # 提取通用函数
```

---

## 常见问题

### Q: AI 服务连接失败？

检查 `config.py` 中 `AI_ASSISTANT_BASE_URL` 配置是否正确指向 AI 微服务。

```python
# config.py
AI_ASSISTANT_BASE_URL = os.getenv('AI_ASSISTANT_BASE_URL', 'http://127.0.0.1:9011')
```

### Q: 消息历史不显示？

检查数据库表是否已创建，重启应用会自动执行迁移。

```bash
# 检查表是否存在
sqlite3 data/grading_system_v2.db ".tables" | grep ai_
```

### Q: 浮窗不显示？

1. 确认用户已登录
2. 确认 `base.html` 已包含组件
3. 检查浏览器控制台错误

### Q: 速率限制不生效？

确保前端和后端都实现了限制逻辑，只依赖前端无法真正防止滥用。
