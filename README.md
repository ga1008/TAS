# 🎓 AI 自动化作业批改系统 (AI Grading System)

> **解放双手，让 AI 帮你改作业！**
> 专为计算机课程、编程作业、以及标准化文档作业设计的自动化评估系统。

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-green)](https://flask.palletsprojects.com/)
[![AI Powered](https://img.shields.io/badge/AI-DeepSeek%20%7C%20OpenAI%20%7C%20Volcengine-purple)](https://github.com/)

---

## 📖 这是一个什么项目？

你是否还在为批改几十份、上百份的学生代码作业而头秃？
- 手动解压压缩包？❌
- 逐个打开代码文件看逻辑？❌
- 手动运行代码看报错？❌
- 甚至还要手动填 Excel 成绩单？❌

**本系统一站式解决所有痛点：**
1. **自动解压**：直接上传全班作业压缩包（zip/rar），系统自动处理。
2. **AI 生成批改脚本**：你只需要上传“题目文档”和“评分标准”，AI 自动帮你写出批改程序！
3. **一键批改**：点击按钮，系统自动运行批改程序，判断学生作业对不对。
4. **自动登分**：批改完直接导出 Excel 成绩单，包含详细的扣分原因。

---

## 🚀 快速开始 (小白用户版)

### 1. 环境准备
确保你的电脑安装了 [Python 3.8 或以上版本](https://www.python.org/downloads/)。

### 2. 安装与启动
下载本项目代码后，在文件夹内打开终端（CMD），依次运行：

```bash
# 1. 安装依赖库
pip install -r requirements.txt

# 2. 启动 AI 助手服务 (不要关闭窗口)
python ai_assistant.py

# 3. 启动主程序 (新建一个终端窗口运行)
python app.py
```

当看到 `Running on http://127.0.0.1:5010` 时，打开浏览器访问该地址即可使用！

### 3. 第一次使用必读 (关键配置)
系统启动后，**必须先配置 AI 模型**，否则无法生成批改脚本。

1. **登录后台**：访问 `http://127.0.0.1:5010/admin/login`
   - 默认账号：`admin`
   - 默认密码：`admin123`
2. **添加 AI 服务商**：
   - 点击“新增服务商”。
   - **OpenAI 兼容协议** (推荐)：适用于 DeepSeek, ChatGPT, Moonshot, DashScope 等。
   - **Volcengine**：适用于字节跳动豆包模型。
3. **添加模型**：
   - 在刚添加的服务商下点击“添加模型”。
   - 填写模型 ID (如 `deepseek-chat`)。
   - **能力类型**选择 `Thinking` (用于生成代码) 或 `Standard` (用于普通对话)。

---

## 🕹️ 使用流程图解

1.  **生成核心 (AI Workshop)**
    *   进入“AI 核心生成工坊”。
    *   上传《期末考试卷.docx》和《评分标准.txt》。
    *   点击生成，AI 会写出一个专门批改这套试卷的 Python 脚本。

2.  **创建班级**
    *   进入“新建班级/任务”。
    *   上传学生名单 (Excel 包含学号、姓名)。
    *   选择刚才生成的“批改核心”。

3.  **上传与批改**
    *   进入班级，点击“上传作业包”。
    *   系统自动解压、匹配学号。
    *   点击“运行自动批改”，等待进度条跑完。

4.  **导出成绩**
    *   查看全班概览，支持手动修正分数。
    *   点击“导出 Excel”获取最终成绩单。

---

## 👨‍💻 开发者指南 (Deployment & Dev Guide)

如果你是开发者，或者想要部署到服务器，请参考以下信息。

### 1. 项目架构 (Dual-Service)
系统采用微服务架构，前后端分离（逻辑上）：

| 服务 | 文件 | 默认端口 | 职责 |
| :--- | :--- | :--- | :--- |
| **Main App** | `app.py` | `5010` | Flask Web 应用。处理 UI、文件管理、批改任务调度、Excel 导出。 |
| **AI Assistant** | `ai_assistant.py` | `9011` | FastAPI 微服务。封装各家 AI 厂商接口，提供统一的 Chat API。 |

### 2. 目录结构
```text
autoCorrecting/
├── app.py                 # 主 Web 服务入口
├── ai_assistant.py        # AI 微服务入口
├── config.py              # 核心配置文件 (端口, 数据库路径, 密钥)
├── docker-compose.yml     # Docker 编排文件
├── blueprints/            # Flask 路由模块 (Admin, Grading, Auth...)
├── grading_core/          # 批改逻辑核心
│   ├── base.py            # BaseGrader 基类 (所有批改脚本的父类)
│   ├── factory.py         # 动态加载器 (热重载)
│   └── graders/           # [生成] AI 生成的批改脚本存放处
├── services/              # 业务逻辑层 (FileService, AIService...)
└── data/                  # SQLite 数据库与运行时数据
```

### 3. Docker 部署 (推荐)
已提供 `docker-compose.yml`，一键拉起所有服务。

```bash
# 构建并后台运行
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```
*注意：默认挂载了当前目录到容器内，方便开发调试。生产环境建议修改 `volumes` 配置。*

### 4. 二次开发：自定义批改器
除了用 AI 生成，你也可以手写批改脚本。
1. 在 `grading_core/graders/` 下新建 `.py` 文件。
2. 继承 `grading_core.base.BaseGrader`。
3. 实现 `grade(self, student_dir, student_info)` 方法。

```python
from grading_core.base import BaseGrader, GradingResult

class MyCustomGrader(BaseGrader):
    ID = "custom_v1"
    NAME = "手工编写的批改器"

    def grade(self, student_dir, student_info):
        self.res = GradingResult()
        self.scan_files(student_dir) # 扫描学生目录建立索引

        # 查找文件
        path, penalty = self.smart_find("main.py")
        if path:
            self.res.add_sub_score("文件提交", 10)
        else:
            self.res.add_deduction("未找到 main.py")

        self.res.total_score = sum(item['score'] for item in self.res.sub_scores)
        return self.res
```

### 5. 环境变量 (Env Vars)
可以在 `.env` 或 `docker.env` 中配置：
- `ADMIN_PASSWORD`: 初始化管理员密码
- `FLASK_SECRET_KEY`: Session加密密钥
- `AI_ASSISTANT_ENDPOINT`: 主应用连接 AI 服务的地址
