# export_core/doc_config.py

class DocumentTypeConfig:
    # 定义支持的文档类型及其中文名
    TYPES = {
        "exam": "试卷",
        "standard": "评分细则",
        "syllabus": "教学大纲", # 扩展支持
        "plan": "授课计划"      # 扩展支持
    }

    # 定义提取规则 (System Prompt 的核心部分)
    # 这里特别强调了 cohort (适用班级/人群) 的提取
    EXTRACTION_SCHEMA = """
    请从文档中严格提取以下 JSON 字段：
    {
        "title": "文档标题",
        "doc_category": "文档类型(exam/standard/syllabus/plan)",
        "metadata": {
            "academic_year": "学年 (格式如 2025-2026)",
            "semester": "学期 (1 或 2)",
            "course_name": "课程名称",
            "cohort_tag": "适用班级或人群 (关键：如果是专升本、特定班级群，请明确提取，例如 '专升本', '2401-2402班', '全校通用')",
            "assessment_mode": "考核方式 (开卷/闭卷/大作业)",
            "duration": "考试时长(分钟)",
            "total_score": "总分",
            "author": "命题人"
        }
    }
    如果文中未明确提及某字段，请根据上下文推断，实在无法推断则留空。
    对于 'cohort_tag'，请仔细区分。如果标题是《...软工2406、2407班(专升本)期末试卷》，则 cohort_tag 应为 "专升本(2406-2408)"。
    """

    # 3. [新增] 针对不同文档类型的定制化 Prompt
    # 这里我们利用多态思想，根据类型下发不同的指令
    @staticmethod
    def get_prompt_by_type(doc_type):
        base_prompt = """
        任务：清洗文档并转换为标准 Markdown，同时提取元数据 JSON。
        """

        if doc_type == "syllabus":
            return base_prompt + """
            【针对“课程教学大纲”的特殊提取规则】
            请重点提取以下元数据（metadata）：
            1. **course_name**: 课程名称（通常在《》内或第一行）。
            2. **course_code**: 课程编号（数字字母组合）。
            3. **course_category**: 课程类别。**注意：** 文档中会出现如“通识必修□ 专业限选☑”的形式，请提取符号为 ☑、R、√ 或实心方框对应的文字。
            4. **hours_info**: 学时信息字典。需解析“总学时48（理论32+实践16）”，提取为 {"total": 48, "theory": 32, "practice": 16}。
            5. **credits**: 学分（数字）。
            6. **department**: 开课部门。
            7. **authors**: {"drafter": "制定人姓名", "reviewer": "审定人姓名"}。

            【正文 Markdown 结构要求】
            请严格按照以下章节整理正文，如果原文档没有对应标题，请根据内容归类：
            # 课程名称
            ## 一、课程简介
            ## 二、课程目标
            ## 三、教学安排
            ### (一) 课程知识图谱 (标注[知识图谱图片])
            ### (二) 教学内容及要求
            ## 四、课程考核
            ### (三) 期末综合考核方式
            ### (四) 期末综合成绩构成比例
            ### (五) 期末综合考核题型及命题要求
            ## 五、选用教材
            ## 六、主要参考资料
            """

        elif doc_type == "exam":
            return base_prompt + """
            【针对“试卷”的特殊规则】
            提取学年、学期、课程名、教师、系主任、学院领导等。保留所有题目、选项、分值。
            """

        elif doc_type == "standard":
            return base_prompt + """
            【针对“评分标准”的特殊规则】
            提取评分点、得分依据、扣分细则、教师、系主任等等。保留所有评分细则内容。
            """

        else:
            return base_prompt
