# TAS System Architecture Blueprint

## 1. 项目概述
TAS (Teaching Assistant System) 是一个基于 Python Flask 的高校教学辅助系统。核心功能包括自动化作业批改（Python/Shell脚本）、文档结构化解析（AI驱动）、教学资料导出（Word模板）以及班级学生管理。

## 2. 技术栈
* **后端框架**: Flask (Python 3.x)
* **数据库**: SQLite (原生 `sqlite3` 封装，支持多线程)
* **前端**: Bootstrap 5 + jQuery + Jinja2 模板
* **AI 集成**: Volcengine (火山引擎) / OpenAI 协议兼容接口
* **数据处理**: Pandas (Excel/CSV处理), PDF转换工具

## 3. 目录结构说明
```text
/
├── app.py                # 应用入口，App Factory，蓝图注册
├── config.py             # 配置文件 (路径、密钥)
├── database.py           # 数据库核心封装 (ORM-like 手写层)
├── extensions.py         # 全局扩展实例 (db 等)
├── blueprints/           # 路由蓝图 (Controller 层)
│   ├── admin.py          # 系统管理
│   ├── ai_generator.py   # AI 生成器 (生成批改脚本)
│   ├── auth.py           # 认证
│   ├── export.py         # 导出业务
│   ├── grading.py        # 批改业务主流程
│   ├── library.py        # 文档库
│   ├── main.py           # 首页与通用
│   ├── signatures.py     # 电子签名管理
│   └── student.py        # 学生名单管理
├── grading_core/         # 批改核心引擎 (Strategy Pattern)
│   ├── base.py           # BaseGrader 抽象基类
│   ├── factory.py        # GraderFactory 动态加载工厂
│   └── graders/          # 具体批改策略脚本 (动态生成/手动编写)
├── export_core/          # 导出核心引擎
│   ├── manager.py        # TemplateManager 模板管理器
│   └── templates/        # 具体导出模板类
├── services/             # 业务逻辑层 (Service Layer)
│   ├── ai_service.py     # AI 高级业务 (解析、生成代码)
│   ├── file_service.py   # 文件上传、哈希、复用逻辑
│   └── grading_service.py# 批改执行逻辑
├── ai_utils/             # AI 底层工具
│   ├── ai_helper.py      # LLM 调用封装 (流式/非流式)
│   └── volc_file_manager.py # 火山引擎文件上传管理
├── static/               # 静态资源 (JS/CSS/Fonts)
└── templates/            # Jinja2 HTML 模板
```

### 4. 核心设计模式
Factory Pattern: 用于 grading_core 和 export_core，实现策略的动态加载与热重载。

Service Layer: 业务逻辑从 View (Blueprints) 剥离到 services/ 目录。

Singleton/Global: db 实例在 extensions.py 中定义，全局单例。
