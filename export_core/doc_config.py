# export_core/doc_config.py

class DocumentTypeConfig:
    # 定义支持的文档类型及其中文名
    TYPES = {
        "exam": "试卷",
        "standard": "评分细则",
        "syllabus": "教学大纲",
        "plan": "考核计划",
        "student_list": "学生名单",
        "score_sheet": "考核登分表"
    }

    # ==================== 字段配置 Schema ====================
    # 每种文档类型的元数据字段定义，用于前端动态生成表单
    # type: text | select | number | nested
    # required: 是否必填
    # options: 下拉选项 (仅 select 类型)
    # fields: 嵌套字段 (仅 nested 类型)

    FIELD_SCHEMAS = {
        "exam": {
            "label": "试卷元数据",
            "fields": [
                {"key": "academic_year", "label": "学年", "type": "text", "placeholder": "如: 2025-2026"},
                {"key": "semester", "label": "学期", "type": "select", "options": ["第一学期", "第二学期", "第三学期"]},
                {"key": "academic_year_semester", "label": "学年学期(完整)", "type": "hidden"},
                {"key": "exam_type", "label": "考试类型", "type": "select", "options": ["期末考试", "补考", "重新学习考试"]},
                {"key": "course_name", "label": "课程名称", "type": "text", "required": True},
                {"key": "education_level", "label": "学历层次", "type": "select", "options": ["本科", "专科", "高职"]},
                {"key": "assessment_type", "label": "考核类型", "type": "select", "options": ["考试", "考查"]},
                {"key": "class_info", "label": "专业年级班级", "type": "text", "placeholder": "如: 软工2406、2407班"},
                {"key": "duration", "label": "考试时长(分钟)", "type": "number", "placeholder": "如: 120"},
                {"key": "exam_mode", "label": "试卷类型", "type": "select", "options": ["开卷", "闭卷"]},
                {"key": "teacher", "label": "命题教师", "type": "text"},
                {"key": "dept_head", "label": "系(教研室)主任", "type": "text"},
                {"key": "college_dean", "label": "二级学院主管领导", "type": "text"},
                {"key": "total_score", "label": "试卷总分", "type": "number", "placeholder": "如: 100"}
            ]
        },
        "syllabus": {
            "label": "教学大纲元数据",
            "fields": [
                {"key": "course_name", "label": "课程名称", "type": "text", "required": True},
                {"key": "course_code", "label": "课程编号", "type": "text", "placeholder": "如: E020185B3"},
                {"key": "course_category", "label": "课程类别", "type": "select", "options": ["通识必修", "专业核心", "专业限选", "专业任选", "通识选修"]},
                {"key": "hours_info", "label": "学时信息", "type": "nested", "fields": [
                    {"key": "total", "label": "总学时", "type": "number"},
                    {"key": "theory", "label": "理论学时", "type": "number"},
                    {"key": "practice", "label": "实践学时", "type": "number"}
                ]},
                {"key": "credits", "label": "学分", "type": "number", "placeholder": "如: 3.0"},
                {"key": "department", "label": "开课部门", "type": "text"},
                {"key": "authors", "label": "编写人员", "type": "nested", "fields": [
                    {"key": "drafter", "label": "制定人", "type": "text"},
                    {"key": "reviewer", "label": "审定人", "type": "text"}
                ]}
            ]
        },
        "plan": {
            "label": "考核计划元数据",
            "fields": [
                {"key": "academic_year", "label": "学年", "type": "text", "placeholder": "如: 2025-2026"},
                {"key": "semester", "label": "学期", "type": "select", "options": ["第一学期", "第二学期", "第三学期"]},
                {"key": "academic_year_semester", "label": "学年学期(完整)", "type": "hidden"},
                {"key": "assessment_note", "label": "考核提示语", "type": "select", "options": ["非笔试考核", "笔试考核"]},
                {"key": "course_name", "label": "课程名称", "type": "text", "required": True},
                {"key": "class_info", "label": "专业年级班级", "type": "text"},
                {"key": "assessment_type", "label": "考核类型", "type": "select", "options": ["考试", "考查"]},
                {"key": "teacher", "label": "命题教师", "type": "text"},
                {"key": "dept_head", "label": "系(教研室)主任", "type": "text"},
                {"key": "date", "label": "命题日期", "type": "text", "placeholder": "如: 2025年10月13日"}
            ]
        },
        "standard": {
            "label": "评分细则元数据",
            "fields": [
                {"key": "academic_year", "label": "学年", "type": "text", "placeholder": "如: 2025-2026"},
                {"key": "semester", "label": "学期", "type": "select", "options": ["第一学期", "第二学期", "第三学期"]},
                {"key": "academic_year_semester", "label": "学年学期(完整)", "type": "hidden"},
                {"key": "assessment_note", "label": "考核提示语", "type": "text", "placeholder": "如: 非笔试考核"},
                {"key": "course_name", "label": "课程名称", "type": "text", "required": True},
                {"key": "class_info", "label": "专业年级班级", "type": "text"},
                {"key": "assessment_form", "label": "考核形式", "type": "text", "placeholder": "如: 大作业、项目实战"},
                {"key": "date", "label": "命题日期", "type": "text"},
                {"key": "teacher", "label": "命题教师", "type": "text"},
                {"key": "dept_head", "label": "系(教研室)主任", "type": "text"}
            ]
        },
        "student_list": {
            "label": "学生名单元数据",
            "fields": [
                {"key": "class_name", "label": "班级名称", "type": "text", "required": True, "placeholder": "如: 软工2401班"},
                {"key": "college", "label": "学院", "type": "text", "placeholder": "如: 数字科技学院"},
                {"key": "enrollment_year", "label": "入学年份", "type": "text", "placeholder": "如: 2024"},
                {"key": "education_type", "label": "培养类型", "type": "select", "options": ["普本", "专升本", "专科"]}
            ]
        },
        "score_sheet": {
            "label": "考核登分表元数据",
            "fields": [
                {"key": "academic_year_semester", "label": "学年学期", "type": "text", "placeholder": "如: 2025-2026学年度第一学期"},
                {"key": "course_name", "label": "课程名称", "type": "text", "required": True},
                {"key": "course_code", "label": "课程编号", "type": "text", "placeholder": "如: E020001B4"},
                {"key": "class_name", "label": "班级名称", "type": "text"},
                {"key": "teacher", "label": "任课教师", "type": "text"},
                {"key": "student_count", "label": "学生人数", "type": "number"},
                {"key": "graded_count", "label": "已批改人数", "type": "number"},
                {"key": "average_score", "label": "平均分", "type": "number"},
                {"key": "pass_rate", "label": "及格率", "type": "number"}
            ]
        }
    }

    @classmethod
    def get_field_schema(cls, doc_type):
        """获取指定文档类型的字段配置 Schema"""
        return cls.FIELD_SCHEMAS.get(doc_type, {"label": "通用元数据", "fields": []})

    @staticmethod
    def get_prompt_by_type(doc_type):
        """
        根据文档类型返回特定的 System Prompt 和 Extraction Schema。
        核心原则：
        1. 不改写内容，不遗漏内容。
        2. 严格提取元数据 (metadata) 到 JSON。
        3. 勾选框识别 (√, ☑, R, 实心方框) 逻辑。
        4. 正文 (content) 转为标准 Markdown。
        """

        # 通用指令头
        base_instruction = """
        你是一名高校教学资料结构化专家。请读取用户提供的文档内容（文本或图像识别结果），将其整理为标准的 Markdown 格式，并提取关键元数据（Metadata）。

        【全局输出要求】
        1. **必须仅返回一个标准的 JSON 对象**。
        2. JSON 根对象包含两个字段："metadata" (对象) 和 "content" (字符串)。
        3. "content" 字段存放整理好的 Markdown 正文。请保留所有原有文本，**不要进行摘要或改写**，仅做格式规范化（如标题层级、表格格式）。
        4. 如果文档中存在勾选框（如 □, ☑, √, R, (√) 等），请识别被选中的项，并在 Metadata 中仅存储被选中的内容。
        5. 如果某个字段在文档中未找到，请在 JSON 中留空字符串，不要编造。
        """

        # ==================== 1. 试卷 (Exam) ====================
        if doc_type == "exam":
            return base_instruction + """
            【文档类型：试卷】
            请严格按照以下结构提取 Metadata 和整理 Content：

            一、Metadata 提取规则 (JSON字段):
            {
                "academic_year_semester": "年份时间段 (例: '2025-2026学年度第一学期')",
                "exam_type": "考试类型 (识别勾选: 期末考试/补考/重新学习考试)",
                "course_name": "课程名称",
                "education_level": "学历层次 (识别勾选: 本科/专科/高职)",
                "assessment_type": "考核类型 (识别勾选: 考试/考查)",
                "class_info": "专业年级班级 (例: '软工2406、2407、2408班(专升本)')",
                "duration": "考试时间 (分钟，仅提取数字)",
                "exam_mode": "试卷类型 (识别勾选: 开卷/闭卷)",
                "teacher": "命题教师姓名",
                "dept_head": "系(教研室)主任姓名",
                "college_dean": "二级学院(部)主管教学领导姓名",
                "total_score": "试卷总分"
            }
            *注意：识别勾选时，请寻找括号内的 √, ☑ 或类似标记。例如 '开卷(√)' 应提取为 '开卷'。*

            二、Content (Markdown) 整理规则:
            1. 保留大标题结构，例如 '# 一、单项选择题 (共10小题，每题2分，共20分)'。
            2. 题目需清晰编号，例如 '**1.** 题目内容...'。
            3. 选项（如有）请规范换行，例如 'A. xxx  B. xxx'。
            4. 包含所有题型：单选、多选、判断、填空、程序分析、简答、综合应用等。
            5. **严禁遗漏**任何一道小题或分值说明。
            """

        # ==================== 2. 教学大纲 (Syllabus) ====================
        elif doc_type == "syllabus":
            return base_instruction + """
            【文档类型：教学大纲】
            请严格按照以下结构提取 Metadata 和整理 Content：

            一、Metadata 提取规则 (JSON字段):
            {
                "course_name": "课程名称 (例: '服务器配置与管理')",
                "course_code": "课程编号 (例: 'E020185B3')",
                "course_category": "课程类别 (识别勾选: 通识必修/专业核心/专业限选等)",
                "hours_info": {
                    "total": "总学时 (数字)",
                    "theory": "理论学时 (数字)",
                    "practice": "实践学时 (数字)"
                },
                "credits": "学分 (数字，保留一位小数，如 3.0 或 0.5)",
                "department": "开课部门 (例: '数字科技学院')",
                "authors": {
                    "drafter": "制定人姓名",
                    "reviewer": "审定人姓名"
                }
            }
            *注意：学时学分通常表现为 '总学时48（理论32+实践16）'，请拆分提取。*

            二、Content (Markdown) 整理规则:
            请按章节整理正文，包含以下部分（如果没有对应标题，请根据内容归位）：
            1. **课程简介**：保留完整文字。
            2. **课程目标**：保留列表。
            3. **教学安排**：
               - **课程知识图谱**：如果原文是图片或描述了知识结构，请尝试用 ```mermaid graph TD ... ``` 代码块生成一个简单的知识结构图。
               - **教学内容及要求**：保留详细的章节、内容、重难点描述。
            4. **课程考核**：
               - 包含 '支撑课程目标的课程考核设计表'。
               - 包含 '考核内容对课程目标支撑矩阵'。
               - 包含 '期末综合考核方式'、'成绩构成比例'。
            5. **教材与参考资料**：列出书名、作者、出版社。
            """

        # ==================== 3. 考核计划表 (Plan) ====================
        elif doc_type == "plan":
            return base_instruction + """
            【文档类型：考核计划表】
            注意：这是一份三列多行的表格文档。

            一、Metadata 提取规则 (JSON字段):
            {
                "academic_year_semester": "年份学期 (例: '2025-2026学年度第一学期')",
                "assessment_note": "考核提示语 (例: '非笔试考核' 或 '笔试考核')",
                "course_name": "课程名称",
                "class_info": "专业年级班级",
                "assessment_type": "考核类型 (识别勾选: 考试/考查)",
                "teacher": "命题教师",
                "dept_head": "系(教研室)主任",
                "date": "命题日期 (例: '2025年10月13日')"
            }

            二、Content (Markdown) 整理规则:
            1. 文档核心是一个表格，包含三列：**[考核形式] | [考核技能/内容] | [分值]**。
            2. 请输出一个标准的 Markdown 表格。
            3. **行对应关系至关重要**：每一行的形式、内容、分值必须一一对应，不能错位。
            4. 内容列可能包含长段文字，请完整保留，可以使用 `<br>` 换行。
            """

        # ==================== 4. 评分细则 (Standard) ====================
        elif doc_type == "standard":
            return base_instruction + """
            【文档类型：评分细则】
            通常用于非笔试考核或大作业的评分标准。

            一、Metadata 提取规则 (JSON字段):
            {
                "academic_year_semester": "年份学期",
                "assessment_note": "考核提示语 (例: '非笔试考核')",
                "course_name": "课程名称",
                "class_info": "专业年级班级",
                "assessment_form": "考核形式 (例: '大作业' 或 '项目实战')",
                "date": "命题日期",
                "teacher": "命题教师",
                "dept_head": "系(教研室)主任"
            }

            二、Content (Markdown) 整理规则:
            1. 评分细则正文通常包含：一级指标、二级指标、分值、评分标准（得分点/失分点）。
            2. 请整理为清晰的 Markdown 表格或多级列表。
            3. 重点提取：**分值** 和 **具体的评分描述**（例如 '功能实现得5分，未实现扣2分'）。
            4. 如有特殊要求（如提交格式、截止时间），请单独列出。
            """

        # ==================== 5. 学生名单 (Student List) ====================
        elif doc_type == "student_list":
            return base_instruction + """
            【文档类型：学生名单】
            这是一份学生名单表格，需要准确提取每个学生的信息。请特别注意保持学号的准确性，不要随意更改或补全。

            一、Metadata 提取规则 (JSON字段):
            {
                "class_name": "班级名称 (从表格标题或内容中提取，如: '软工2401班')",
                "college": "学院名称 (如: '数字科技学院')",
                "enrollment_year": "入学年份 (四位数字，如: '2024')",
                "education_type": "培养类型 (识别或推断: '普本' / '专升本' / '专科')"
            }

            **元数据提取注意事项**：
            - 班级名称通常在表格标题中，格式如 "XXX学院2024级XXX班学生名单" 或 "软工2401班"
            - 学院名称通常在表格标题中
            - 入入年份可以从班级名称推断（如 "2401班" -> 2024年入学）
            - 培养类型：如果班级名称包含 "专升本" 标记为专升本，否则默认为普本

            二、Content (Markdown) 整理规则:
            1. 将名单整理为标准的 Markdown 表格。
            2. 表格必须包含以下列（按顺序）：
               - **学号** (student_id): 必须保持原样，不要修改或补全
               - **姓名** (name): 学生姓名
               - **性别** (gender): 可选列，如果没有则省略此列
            3. **核心原则**：
               - **学号准确性**：学号必须完全保持原样，不要补零、不要格式化、不要修正可能的"错误"
               - **姓名准确性**：姓名保持原样，不要添加空格或标点
               - **对应关系**：确保每个学生的学号、姓名、性别（如有）一一对应，不能错位
            4. 表格格式示例：
               | 学号 | 姓名 | 性别 |
               | --- | --- | --- |
               | 202401001 | 张三 | 男 |
               | 202401002 | 李四 | 女 |
            5. 如果原始表格包含其他列（如专业、备注等），请忽略，只保留上述必要列。
            """

        else:
            return base_instruction