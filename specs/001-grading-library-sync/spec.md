# Feature Specification: 自动评分结果同步到文档库

**Feature Branch**: `001-grading-library-sync`
**Created**: 2026-01-26
**Status**: Draft
**Input**: User description: "自动评分任务完成后自动生成成绩文档到文档库，并与Excel导出功能对接"

## User Scenarios & Testing

### User Story 1 - 批改完成自动生成成绩文档 (Priority: P1)

教师使用批改核心对班级学生作品完成批量评分后，系统自动收集相关元数据（课程名称、班级名称、教师、课程编码、学年学期等），生成一份包含所有学生成绩的 Markdown 文档并存入文档库。

**Why this priority**: 这是功能的核心价值所在，实现评分结果与文档库的自动互通，减少手动整理工作。

**Independent Test**: 完成一次批量批改后，在文档库中能看到自动生成的成绩文档，包含完整的学生信息和分数。

**Acceptance Scenarios**:

1. **Given** 教师已完成班级批量批改（至少有1名学生成功评分），**When** 批改任务完成，**Then** 系统自动生成成绩文档到文档库，文档类型为"其他"，名称格式为"学年学期-课程-班级-机考分数.md"
2. **Given** 成绩文档已生成，**When** 教师在文档库查看该文档，**Then** 文档内容包含：元数据表头（课程、班级、教师、学年学期等）+ 学生成绩 Markdown 表格（学号、姓名、性别、各题分数、总分）
3. **Given** 批改核心关联的试卷文件有完整元数据，**When** 生成成绩文档，**Then** 文档元数据自动填充（课程名称、教师等从试卷元数据获取）

---

### User Story 2 - 成绩文档导出为机试考核登分表 (Priority: P2)

教师在文档库选择已生成的成绩文档，使用"机试考核登分表"模板导出 Excel 文件，系统自动识别文档中的成绩数据并正确填充到模板中。

**Why this priority**: 导出功能是成绩文档价值的延伸，让教师能直接获得规范的登分表格。

**Independent Test**: 从文档库选择成绩文档并选择"机试考核登分表"模板导出，得到包含完整学生成绩的 Excel 文件。

**Acceptance Scenarios**:

1. **Given** 文档库中有自动生成的成绩文档，**When** 教师进入导出页面选择该文档和"机试考核登分表"模板，**Then** 表单自动填充课程名称、班级等信息
2. **Given** 导出表单已配置，**When** 教师点击导出，**Then** 生成的 Excel 文件包含正确的学生学号、姓名、各题得分、总分
3. **Given** 成绩文档中各题分数与模板题目配置不完全匹配，**When** 导出时，**Then** 系统按顺序匹配题目分数，多余的题目显示空白

---

### User Story 3 - 元数据追溯与数据库优化 (Priority: P3)

系统在生成成绩文档时，能够从批改核心关联的原始试卷中追溯教师、课程编码等元数据，即使这些信息未在班级表中直接存储。

**Why this priority**: 元数据完整性是文档质量的保障，但可以通过渐进式优化实现。

**Independent Test**: 生成的成绩文档元数据字段完整填充，教师名称能从试卷元数据中正确获取。

**Acceptance Scenarios**:

1. **Given** 批改核心是通过 AI 生成的，关联了试卷文件，**When** 生成成绩文档，**Then** 教师名称从试卷的 meta_info.teacher 字段获取
2. **Given** 试卷元数据中包含 course_code，**When** 生成成绩文档，**Then** 课程编码正确填入文档元数据

---

### Edge Cases

- 批改过程部分失败时（部分学生成功，部分失败）：仍然生成成绩文档，失败的学生显示"批改失败"状态
- 批改核心没有关联试卷元数据时：文档元数据中教师、课程编码等字段留空，课程名称从班级表的 course 字段获取
- 同一班级多次批改时：每次批改生成新文档，不覆盖已有文档（使用时间戳后缀，如 `_20260126143052`）
- 班级没有学生或所有学生批改失败时：不生成成绩文档，仅在日志中记录
- 成绩文档已被手动编辑后再次导出：以文档当前内容为准进行导出

## Requirements

### Functional Requirements

- **FR-001**: 批量批改完成后（至少有1名学生成功评分），系统 MUST 自动生成成绩文档到文档库
- **FR-002**: 成绩文档类型 MUST 设置为 "other"（其他）
- **FR-003**: 成绩文档名称 MUST 遵循格式："[学年学期]-[课程名称]-[班级名称]-机考分数.md"
- **FR-004**: 成绩文档 MUST 包含 Markdown 格式的学生成绩表格，列包括：序号、学号、姓名、性别、各大题分数（动态列）、总分
- **FR-005**: 成绩文档元数据 MUST 包含：course_name、class_name、teacher、course_code、academic_year_semester
- **FR-006**: 系统 MUST 从批改核心关联的 ai_tasks 记录追溯到原始试卷的 file_assets 记录以获取 meta_info 中的教师和课程编码
- **FR-007**: "机试考核登分表" Excel 导出 MUST 支持从成绩文档的 parsed_content 解析学生成绩数据
- **FR-008**: 导出时如果文档 meta_info 包含 class_name，系统 SHOULD 优先从关联班级获取成绩数据，而非解析 Markdown 内容
- **FR-009**: 成绩文档生成失败时 MUST 记录错误日志，不影响批改流程的正常完成
- **FR-010**: 系统 MUST 保留现有批改功能的所有行为，成绩文档生成为附加功能

### Key Entities

- **成绩文档 (Score Document)**: 存储在 file_assets 表，doc_category='other'，parsed_content 为 Markdown 格式的成绩表格，meta_info 包含课程/班级/教师等元数据，新增 source_class_id 字段关联班级
- **批改任务 (AI Task)**: ai_tasks 表，关联 exam_path 指向试卷文件，course_name 存储课程名称
- **试卷元数据 (Exam Metadata)**: file_assets 表的 meta_info JSON 字段，包含 teacher、course_code 等信息
- **班级成绩 (Class Grades)**: grades 表，score_details 为 JSON 数组存储各题得分

## Success Criteria

### Measurable Outcomes

- **SC-001**: 完成批量批改后，5秒内在文档库可见自动生成的成绩文档
- **SC-002**: 成绩文档生成成功率达到99%（排除系统级故障）
- **SC-003**: 导出的 Excel 文件学生数据准确率100%（与数据库记录一致）
- **SC-004**: 教师无需手动整理成绩即可完成从批改到导出的完整流程

## Assumptions

1. 批改核心（grader）通过 ai_tasks 表与原始试卷文件关联，试卷文件存储在 file_assets 表中
2. 试卷文件的 meta_info 字段已由 AI 解析填充，包含 teacher、course_code 等字段
3. 学生性别信息存储在 students 表的 gender 字段（可能为空）
4. 学年学期信息可从试卷元数据的 academic_year_semester 字段获取；若缺失则根据当前日期推断（9月-次年1月为第一学期，2月-8月为第二学期）
5. 成绩文档生成为同步操作，在批改完成响应返回前完成

## Clarifications

### Session 2026-01-26

- Q: 同一班级多次批改时，文件命名冲突如何处理？ → A: 使用时间戳后缀（如 `_20260126143052`）
- Q: 试卷元数据缺少 academic_year_semester 时如何处理？ → A: 根据当前日期自动推断学年学期
