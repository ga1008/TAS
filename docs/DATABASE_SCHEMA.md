# Database Schema Blueprint

## 核心设计
* **数据库**: SQLite
* **访问方式**: `database.py` 中的 `Database` 类，不使用 SQLAlchemy ORM，直接使用 SQL。
* **连接管理**: 线程本地存储 (`threading.local`) 确保多线程安全。

## 数据表定义

### 1. 用户与权限
* **users**: 系统用户
    * `id` (PK), `username` (Unique), `password_hash`, `is_admin` (Bool), `has_seen_help` (Bool)

### 2. 批改系统 (Grading)
* **classes**: 班级
    * `id`, `name`, `course`, `workspace_path`, `strategy` (关联 grader_id), `created_by`
* **students**: 学生 (旧表，逐渐被 student_lists 取代，但仍用于批改绑定)
    * `id`, `student_id`, `name`, `gender`, `class_id`
* **grades**: 成绩记录
    * `student_id`, `class_id`, `total_score`, `score_details` (JSON: 分项得分), `deduct_details` (扣分原因), `status`, `filename`

### 3. AI 核心 (AI Core)
* **ai_providers**: AI 厂商配置
    * `id`, `name`, `provider_type` (volcengine/openai), `base_url`, `api_key`, `max_concurrent_requests`
* **ai_models**: AI 模型配置
    * `id`, `provider_id`, `model_name`, `capability` (standard/thinking/vision), `weight` (权重), `can_force_json`
* **ai_tasks**: 异步任务记录 (用于生成 Grader 代码)
    * `id`, `name`, `status` (pending/processing/success/failed/deleted), `grader_id`, `log_info`, `exam_path`, `standard_path`, `strictness`, `extra_desc`, `max_score`, `course_name`

### 4. 资产管理 (Assets)
* **file_assets**: 文件资产 (核心表，所有上传文件去重存储)
    * `id`, `file_hash` (SHA256, Unique), `original_name`, `file_size`, `physical_path`, `parsed_content` (AI解析后的文本), `meta_info` (JSON: 学年/学期/课程等), `doc_category`, `uploaded_by`
* **signatures**: 电子签名
    * `id`, `name`, `file_hash`, `file_path`

### 5. 导出系统 (Export)
* **export_templates**: 导出模板注册表
    * `template_id` (对应 Python 类 ID), `name`, `file_path`, `ui_schema` (JSON: 前端表单定义)

### 6. 学生管理 (Student Management - New)
* **student_lists**: 学生名单元数据
    * `file_asset_id`, `class_name`, `college`, `department`, `enrollment_year`, `education_type`
* **student_details**: 学生详细信息
    * `student_list_id`, `student_id`, `name`, `gender`, `email`, `phone`, `status`

