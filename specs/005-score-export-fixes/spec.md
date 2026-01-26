# Feature Specification: 成绩导出与考核登分表完善

**Feature Branch**: `005-score-export-fixes`
**Created**: 2026-01-26
**Status**: Draft
**Input**: User description: 修复成绩导出bug并新增考核登分表文档类型

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 导出成绩时仅保留大题分数 (Priority: P1)

教师在批改任务完成后点击"导出成绩到文档库"，系统应只导出各大题（如"第一大题"、"第二大题"）的分数，不包含小题分数（如1.1、1.2、2.1）。同时元数据应包含每个大题的满分值和试卷总分。

**Why this priority**: 核心数据质量问题，直接影响成绩文档的可用性和后续Excel导出的正确性。

**Independent Test**: 批改一个包含多道大题和小题的任务 → 导出到文档库 → 检查Markdown表格仅显示大题分数 → 检查元数据包含各大题满分和总分

**Acceptance Scenarios**:

1. **Given** 一个已完成批改的班级，评分细则包含"第一大题(30分)"下的1.1(10分)、1.2(20分)，**When** 教师点击导出到文档库，**Then** 成绩表格只显示"第一大题"列，分数为30分（小题分数之和），不显示1.1、1.2列
2. **Given** 已导出的成绩文档，**When** 查看文档元数据，**Then** 可看到 `question_scores: [{"name": "第一大题", "max_score": 30}, ...]` 和 `total_max_score: 100`
3. **Given** 评分细则元数据中有total_score字段，**When** 导出成绩，**Then** 自动提取该值作为试卷总分

---

### User Story 2 - 动态题目分值配置表单 (Priority: P1)

从文档库导出Excel时，"题目分值配置"不再是单个文本框，而是根据大题数量动态生成的表单字段，每个字段预填从成绩文档获取的分值。

**Why this priority**: 当前单一文本框容易输入错误，动态表单提升易用性和数据准确性。

**Independent Test**: 打开一个含3道大题的成绩文档 → 点击导出Excel → 看到3个独立的分值输入框，预填各大题满分

**Acceptance Scenarios**:

1. **Given** 成绩文档元数据含`question_scores: [{name:"一", max_score:20}, {name:"二", max_score:30}, {name:"三", max_score:50}]`，**When** 用户点击"导出为Excel"，**Then** 界面显示3个独立的表单字段："第一题(20分)"、"第二题(30分)"、"第三题(50分)"，默认值分别为20、30、50
2. **Given** 用户修改了某题分值，**When** 点击确认导出，**Then** Excel中使用修改后的分值

---

### User Story 3 - 新增"考核登分表"文档分类 (Priority: P1)

成绩导出到文档库时使用新的文档分类"score_sheet"（8. 考核登分表），在前端选项卡中排在"期末试卷"之前。

**Why this priority**: 区分成绩文档与其他教学资料，便于分类管理和筛选。

**Independent Test**: 导出一份成绩到文档库 → 在文档库选项卡中看到"8. 考核登分表" → 该文档出现在此分类下

**Acceptance Scenarios**:

1. **Given** 从批改任务导出成绩到文档库，**When** 导出完成，**Then** 文档的`doc_category`字段值为`score_sheet`
2. **Given** 打开文档库页面，**When** 查看选项卡，**Then** 看到顺序为：全部、教学大纲、考核计划、评分细则、**考核登分表**、期末试卷、其他
3. **Given** 点击"考核登分表"选项卡，**When** 有已导出的成绩文档，**Then** 仅显示成绩类文档

---

### User Story 4 - 考核登分表详情页面 (Priority: P2)

考核登分表类型文档有专属的详情页面，可查看和编辑学生分数、编辑元数据、一键导出Excel（图标为Excel图标）。

**Why this priority**: 提供完整的成绩管理能力，但不影响导出的核心流程。

**Independent Test**: 打开一个考核登分表文档 → 能看到学生成绩表格 → 能编辑某学生分数 → 能编辑元数据 → 能点击Excel图标导出

**Acceptance Scenarios**:

1. **Given** 打开考核登分表文档详情，**When** 查看页面，**Then** 显示学生成绩表格（学号、姓名、各大题分数、总分）
2. **Given** 有权限的用户在详情页，**When** 点击某学生的分数单元格，**Then** 可修改分数并保存
3. **Given** 有权限的用户在详情页，**When** 点击元数据编辑按钮，**Then** 可编辑课程名、教师、班级等元数据
4. **Given** 详情页顶部，**When** 查看导出按钮，**Then** 按钮图标为Excel图标(fa-file-excel)而非默认下载图标
5. **Given** 点击Excel导出按钮，**When** 弹出配置表单，**Then** 出现动态题目分值配置（参见US2）

---

### User Story 5 - 系统功能完整性保障 (Priority: P2)

所有改动不破坏现有功能：批改流程、其他文档类型的查看编辑、现有Excel导出、教务系统同步等。

**Why this priority**: 回归测试确保系统稳定性，但优先级低于新功能实现。

**Independent Test**: 完成所有改动后 → 执行批改流程 → 查看其他类型文档 → 确认功能正常

**Acceptance Scenarios**:

1. **Given** 现有试卷类型文档，**When** 打开查看和编辑，**Then** 功能与改动前一致
2. **Given** 现有批改任务，**When** 执行批改流程，**Then** 批改正常完成，成绩正确记录
3. **Given** 旧版导出的成绩文档（doc_category='other'），**When** 在文档库中筛选，**Then** 仍可在"其他"分类下找到

---

### Edge Cases

- 评分细则没有大题/小题层级区分时，所有题目都视为大题导出
- 元数据中缺少total_score时，通过计算各大题满分之和得出
- 旧成绩文档没有question_scores元数据时，Excel导出使用默认配置
- 学生分数部分为空时，表格显示"-"而非0

## Requirements *(mandatory)*

### Functional Requirements

**成绩导出逻辑改进**:
- **FR-001**: System MUST 在导出成绩到文档库时，仅保留大题级别的分数列（如"第一大题"、"任务一"等）
- **FR-002**: System MUST 将小题分数（如1.1、1.2、2.1）聚合到所属大题，不单独显示
- **FR-002a**: 大题识别规则：题目名称以中文数字（一、二、三等）或"第X"格式开头为大题；以阿拉伯数字开头（1、2、1.1等）为小题
- **FR-003**: System MUST 在元数据中写入`question_scores`数组，包含每个大题的名称和满分
- **FR-004**: System MUST 在元数据中写入`total_max_score`字段，表示试卷总分
- **FR-005**: System MUST 优先从评分细则或试卷的元数据中提取总分，次选计算大题满分之和

**文档分类**:
- **FR-006**: System MUST 支持新的文档分类`score_sheet`，中文名"考核登分表"
- **FR-007**: System MUST 将成绩导出的文档自动归类为`score_sheet`
- **FR-008**: 前端选项卡 MUST 按顺序显示：全部、教学大纲、考核计划、评分细则、考核登分表、期末试卷、其他

**Excel导出表单**:
- **FR-009**: Excel导出界面 MUST 根据大题数量动态生成独立的分值输入字段
- **FR-010**: 每个分值字段 MUST 预填从成绩文档元数据获取的满分值
- **FR-011**: 用户 MUST 能够修改预填的分值后再导出

**考核登分表详情页**:
- **FR-012**: Users MUST be able to 在详情页查看学生成绩表格
- **FR-013**: Users MUST be able to 编辑学生的各大题分数（权限控制：文档所有者或管理员）
- **FR-013a**: 编辑任一大题分数后，该学生的总分 MUST 自动重新计算为各大题分数之和
- **FR-014**: Users MUST be able to 编辑文档元数据
- **FR-015**: 导出按钮 MUST 显示Excel图标(fa-file-excel)

**向后兼容**:
- **FR-016**: System MUST 保持旧成绩文档（doc_category='other'）的可访问性，不进行自动迁移
- **FR-017**: System MUST 保持现有批改流程不受影响

### Key Entities

- **成绩文档(Score Document)**: 存储在file_assets表，doc_category='score_sheet'，parsed_content为Markdown格式成绩表，meta_info包含question_scores和total_max_score
- **大题分数(Question Score)**: 结构为`{name: string, max_score: number}`，存储在meta_info.question_scores数组中
- **学生成绩记录(Student Grade Record)**: 现有grades表记录，score_details字段存储各题分数JSON

## Clarifications

### Session 2026-01-26
- Q: 如何识别大题与小题？ → A: 层级前缀规则 - 题目名称以阿拉伯数字开头（如1、2、3）视为小题，以中文数字（一、二、三）或"第X"格式开头视为大题
- Q: 编辑分数后总分如何处理？ → A: 自动计算 - 编辑任一大题分数后，总分自动重新计算为各大题之和
- Q: 旧成绩文档是否需要迁移到新分类？ → A: 不迁移 - 旧文档保持doc_category='other'，仅新导出的成绩文档使用'score_sheet'分类

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 导出的成绩文档中，列数等于大题数量+固定列（学号、姓名、总分等），不包含小题列
- **SC-002**: 100%的新导出成绩文档包含question_scores和total_max_score元数据
- **SC-003**: 文档库选项卡正确显示"考核登分表"分类，排序位置在期末试卷之前
- **SC-004**: Excel导出表单字段数量与大题数量一致
- **SC-005**: 现有功能（批改、其他文档类型操作）回归测试通过率100%
- **SC-006**: 用户能在2次点击内从成绩文档导出Excel（打开详情→点击导出→配置→下载）
