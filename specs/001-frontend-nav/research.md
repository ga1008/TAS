# Research: 前端导航架构重构

**Feature**: 前端导航架构重构
**Date**: 2025-01-21
**Phase**: 0 - Research & Analysis

## 1. SPA 路由机制研究

### Decision: 使用现有 SPA Router，无需修改

**Analysis**:
- 现有 `static/js/spa_router.js` 已实现完整的 SPA 导航功能
- 通过 `X-Requested-With: SPA` 头识别 SPA 请求
- 自动从响应 HTML 中提取 `#spa-content` 内容区
- 支持浏览器前进/后退、菜单高亮、脚本执行

**Rationale**:
- 现有实现已满足需求，无需重复造轮子
- 新路由 `/tasks` 自动被 SPA Router 支持
- 仅需在 Flask 添加对应路由，返回完整 HTML 响应即可

**Alternatives Considered**:
- 改用 Vue/React：过度设计，现有 Jinja2 模板已足够
- 使用 HTMX：增加新依赖，学习成本，现有方案已足够

## 2. 统计数据源分析

### Decision: 创建 StatsService 聚合统计数据

**Data Sources Identified**:
| 统计项 | 数据来源 | 现有方法 |
|--------|----------|----------|
| 班级总数 | `classes` 表 | `db.get_classes(user_id)` |
| 学生总数 | `students` 表 | 新增聚合查询 |
| 批改核心数量 | `grading_core/graders/` | `GraderFactory.get_all_strategies()` |
| 待处理任务数 | `ai_tasks` 表 | `db.get_ai_tasks()` 筛选 status='pending'/'processing' |
| 最近活动 | `classes`, `ai_tasks` | 按时间排序获取最新记录 |

**Rationale**:
- 统计数据涉及多个表和文件系统，需要专门服务封装
- 会话级缓存通过 Flask `session` 对象实现
- 统计查询在 100ms 内完成（符合假设）

**API Design**:
```
GET /api/stats/summary
Response: {
  "class_count": 5,
  "student_count": 120,
  "grader_count": 3,
  "pending_task_count": 2,
  "recent_classes": [...],
  "recent_graders": [...]
}
```

## 3. 组件化策略研究

### Decision: 使用 Jinja2 Include + 宏实现组件复用

**Analysis**:
- Jinja2 `{% include %}` 适用于静态组件复用
- Jinja2 `{% macro %}` 适用于带参数的动态组件
- 顶栏组件化：创建 `templates/components/topbar/` 目录
- 各页面顶栏：通过 `{% include 'components/topbar/dashboard_topbar.html' %}` 引入

**Rationale**:
- 与现有模板系统一致
- 无需引入前端框架
- 保持 SPA 导航体验（组件在服务端渲染）

**Component Structure**:
```
templates/components/
├── topbar/
│   ├── base_topbar.html      # 基础顶栏框架
│   ├── dashboard_topbar.html # 仪表盘顶栏
│   ├── tasks_topbar.html     # 批改任务顶栏
│   └── grading_topbar.html   # 批改详情顶栏（含面包屑）
└── stats/
    ├── stat_card.html        # 统计卡片组件
    ├── quick_action.html     # 快捷操作入口组件
    └── activity_item.html    # 活动条目组件
```

## 4. 侧边栏菜单重构策略

### Decision: 扁平化菜单结构，移除不必要的嵌套

**Current Structure** (base.html):
```
- 仪表盘 (首页)
- 教学管理 (折叠)
  - 课程与批改 (折叠)
    - 作业批改
    - 新建班级
  - 学生管理 (折叠)
    - 学生名单
    - 导入学生
- 资源与工具 (折叠)
  - AI 批改核心 (折叠)
  - 文档解析
  - 文档&导出
- 系统 (折叠)
  - 教务系统同步
  - 管理员后台
  - 退出登录
```

**New Structure** (按 spec.md):
```
- 概览
  - 仪表盘
- 批改管理
  - 批改任务
  - 新建班级
- AI 工具
  - 生成核心
  - 核心列表
- 资源管理
  - 学生名单
  - 文档库
  - 文件管理
- 系统
  - 教务系统同步
  - 管理员后台
  - 退出登录
```

**Rationale**:
- 菜单层级不超过 2 层
- 常用功能直接暴露，减少点击次数
- 分类标题清晰，符合用户心智模型

## 5. 顶栏上下文管理策略

### Decision: 创建 `context_topbar.js` 管理顶栏状态

**Implementation**:
- 在 `base.html` 中定义顶栏占位符 `{% block topbar %}{% endblock %}`
- 各页面模板覆盖 topbar block，引入对应顶栏组件
- JavaScript 检测当前路径，动态更新顶栏按钮状态

**Rationale**:
- 保持 SPA 导航体验（顶栏随内容一起更新）
- 服务端渲染顶栏，SEO 友好
- 客户端 JS 仅处理动态交互（通知轮询、搜索展开）

## 6. 面包屑导航策略

### Decision: 在顶栏组件中集成面包屑

**Implementation**:
- 深层级页面（批改详情、学生详情、核心详情）使用专用顶栏组件
- 面包屑格式：`仪表盘 > 批改任务 > [班级名称] > [学生姓名]`
- 面包屑数据通过 Flask `render_template` 传递

**Rationale**:
- 面包屑数据在服务端已知，无需额外 API 调用
- 静态渲染，无需客户端计算
- 符合渐进增强原则

## 7. 路由迁移策略

### Decision: 保持向后兼容，新增 `/tasks` 路由

**Migration Plan**:
1. 新增 `/tasks` 路由，返回班级列表内容
2. 修改 `/` 路由，返回仪表盘内容
3. 更新 `base.html` 侧边栏菜单链接
4. SPA Router 自动适配新路由（无需修改）

**Rationale**:
- 用户书签到 `/` 仍可访问（内容变为仪表盘）
- 新 `/tasks` 路由提供专门的班级列表入口
- 无需重定向，避免额外 HTTP 请求

## 8. 移动端响应式策略

### Decision: 使用现有 CSS，添加汉堡菜单按钮

**Implementation**:
- 利用现有 CSS 变量 `--sidebar-width`
- 添加媒体查询：`@media (max-width: 768px)`
- 汉堡菜单按钮在移动端显示
- 侧边栏默认隐藏，点击后以覆盖层形式显示

**Rationale**:
- 现有 base.html 已有响应式基础
- Tailwind CSS 提供完整的响应式工具类
- 渐进增强，不影响桌面端体验

---

## Summary

| Research Item | Decision | Impact |
|---------------|----------|--------|
| SPA 路由机制 | 使用现有 spa_router.js | 低 |
| 统计数据源 | 创建 StatsService | 中 |
| 组件化策略 | Jinja2 Include + 宏 | 中 |
| 侧边栏重构 | 扁平化菜单结构 | 低 |
| 顶栏上下文 | context_topbar.js + 服务端渲染 | 中 |
| 面包屑导航 | 顶栏组件集成 | 低 |
| 路由迁移 | 新增 /tasks，修改 / | 低 |
| 移动端响应式 | 媒体查询 + 汉堡菜单 | 中 |

所有研究项已完成，无 NEEDS CLARIFICATION 遗留。
