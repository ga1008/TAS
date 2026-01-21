# Quickstart Guide: 前端导航架构重构

**Feature**: 前端导航架构重构
**Date**: 2025-01-21
**Phase**: 1 - Design

## Prerequisites

1. Python 3.8+ 已安装
2. 项目依赖已安装 (`pip install -r requirements.txt`)
3. 数据库已初始化

## Development Setup

### 1. 启动服务

```bash
# 启动 AI 助手服务 (端口 9011)
python ai_assistant.py

# 启动主应用 (端口 5010)
python app.py
```

### 2. 访问应用

打开浏览器访问 `http://127.0.0.1:5010`

## Implementation Checklist

### Phase 1: 后端路由调整

- [ ] 修改 `blueprints/main.py`
  - [ ] 新增 `/tasks` 路由，返回班级列表
  - [ ] 修改 `/` 路由，返回仪表盘数据

- [ ] 创建 `services/stats_service.py`
  - [ ] 实现 `get_dashboard_stats(user_id)` 方法
  - [ ] 实现 `get_recent_activities(user_id)` 方法
  - [ ] 添加会话缓存支持

- [ ] 添加统计 API 路由
  - [ ] `GET /api/stats/summary`
  - [ ] `POST /api/stats/refresh`

### Phase 2: 前端模板创建

- [ ] 创建 `templates/dashboard.html`
  - [ ] 统计卡片网格 (4 卡片)
  - [ ] 快捷操作入口 (3 卡片)
  - [ ] 最近活动列表
  - [ ] 空状态处理

- [ ] 创建 `templates/tasks.html`
  - [ ] 班级卡片网格
  - [ ] 空状态引导

- [ ] 创建顶栏组件
  - [ ] `templates/components/topbar/dashboard_topbar.html`
  - [ ] `templates/components/topbar/tasks_topbar.html`
  - [ ] `templates/components/topbar/grading_topbar.html` (含面包屑)

- [ ] 创建统计组件
  - [ ] `templates/components/stats/stat_card.html`
  - [ ] `templates/components/stats/quick_action.html`
  - [ ] `templates/components/stats/activity_item.html`

### Phase 3: 侧边栏重构

- [ ] 修改 `templates/base.html`
  - [ ] 重构侧边栏菜单结构 (按 spec.md)
  - [ ] 添加顶栏 block 占位符
  - [ ] 添加移动端汉堡菜单按钮

- [ ] 更新菜单高亮逻辑
  - [ ] 确保 SPA Router 正确识别新路由

### Phase 4: 面包屑导航

- [ ] 在批改详情页面模板添加面包屑
- [ ] 在学生详情页面模板添加面包屑
- [ ] 在核心详情页面模板添加面包屑

### Phase 5: 响应式适配

- [ ] 添加移动端媒体查询
- [ ] 实现汉堡菜单交互
- [ ] 测试移动端显示效果

## File Structure After Implementation

```
autoCorrecting/
├── blueprints/
│   └── main.py          # 修改：新增 /tasks 路由
├── services/
│   └── stats_service.py # 新增：统计服务
├── templates/
│   ├── base.html        # 修改：侧边栏、顶栏占位符
│   ├── dashboard.html   # 新增：仪表盘页面
│   ├── tasks.html       # 新增：批改任务列表
│   └── components/
│       ├── topbar/      # 新增：顶栏组件
│       └── stats/       # 新增：统计组件
└── static/
    └── js/
        └── context_topbar.js  # 新增：顶栏上下文管理
```

## Testing

### 手动测试清单

1. **仪表盘页面**
   - [ ] 访问 `/` 显示仪表盘
   - [ ] 统计卡片显示正确数字
   - [ ] 快捷操作跳转正确
   - [ ] 最近活动列表显示

2. **批改任务页面**
   - [ ] 访问 `/tasks` 显示班级列表
   - [ ] 点击班级进入详情
   - [ ] 空状态显示引导

3. **侧边栏导航**
   - [ ] 菜单结构按 spec 组织
   - [ ] 当前页面菜单高亮
   - [ ] 子菜单展开/收起正常

4. **顶栏**
   - [ ] 各页面显示对应顶栏
   - [ ] 操作按钮功能正常
   - [ ] 面包屑导航正确

5. **响应式**
   - [ ] 移动端侧边栏隐藏
   - [ ] 汉堡菜单点击展开
   - [ ] 菜单项点击后收起

## Rollback Plan

如果出现严重问题，执行以下回滚：

1. 恢复 `blueprints/main.py` (git checkout)
2. 删除新创建的模板文件
3. 恢复 `templates/base.html` (git checkout)
4. 重启服务

## Known Limitations

1. 统计数据缓存基于 Flask session，服务重启后缓存丢失
2. 移动端侧边栏动画可能需要微调
3. 面包屑导航目前仅在深层级页面显示

## Next Steps

完成本功能后，建议：

1. 收集用户反馈，优化仪表盘布局
2. 考虑添加更多统计维度（如批改进度图表）
3. 优化移动端交互体验
