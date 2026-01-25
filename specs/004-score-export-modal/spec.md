# Feature Specification: 成绩导出选择弹窗

**Feature Branch**: `004-score-export-modal`
**Created**: 2026-01-26
**Status**: Draft
**Input**: User description: "在任务详情页点击导出成绩时弹出选择弹窗，可选择导出到文档库或直接导出Excel"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 弹窗选择导出方式 (Priority: P1)

教师完成批改后，点击"导出成绩"按钮，系统弹出选择弹窗，教师可以选择导出到文档库（Markdown格式）或直接下载Excel表格。

**Why this priority**: 这是核心交互变更，是整个功能的入口点。没有这个弹窗，用户无法选择导出方式。

**Independent Test**: 可以单独测试弹窗的打开/关闭、选项切换，验证两个按钮都能正确触发对应流程。

**Acceptance Scenarios**:

1. **Given** 教师在批改任务详情页, **When** 点击"导出成绩"按钮, **Then** 显示导出选择弹窗，包含两个选项卡："文档库"和"Excel表格"
2. **Given** 弹窗已打开, **When** 点击弹窗外部或关闭按钮, **Then** 弹窗平滑关闭
3. **Given** 弹窗已打开且有成绩数据, **When** 选择任一导出方式并点击确认, **Then** 对应导出流程开始执行

---

### User Story 2 - 导出到文档库 (Priority: P1)

教师选择"导出到文档库"选项后，系统自动收集课程元数据和学生成绩，生成Markdown格式的成绩文档，存入文档库。

**Why this priority**: 这是本功能的核心价值——实现批改系统与文档库的数据互通，减少教师重复录入工作。

**Independent Test**: 可以通过创建一个已批改班级，触发导出到文档库，验证文档库中出现新文档且内容正确。

**Acceptance Scenarios**:

1. **Given** 批改任务有至少一名学生已批改, **When** 选择"导出到文档库"并确认, **Then** 系统收集元数据（课程名、班级名、教师、学年学期等）生成Markdown文档
2. **Given** 导出成功, **When** 用户查看文档库, **Then** 可看到名为"{学年学期}-{课程}-{班级}-机考分数.md"的新文档，类型为"其他"
3. **Given** 生成的文档, **When** 查看内容, **Then** 包含元数据头部信息和学生成绩表格（学号、姓名、性别、各题分数、总分、状态）
4. **Given** 该班级已存在同名成绩文档, **When** 再次导出, **Then** 新文档自动添加时间戳后缀避免冲突

---

### User Story 3 - 直接导出Excel (Priority: P2)

教师选择"直接导出Excel"选项后，系统直接下载Excel表格，保持原有功能不变。

**Why this priority**: 这是对现有功能的保留，确保不破坏已有工作流。优先级略低是因为功能已存在，只需集成到新弹窗中。

**Independent Test**: 可以单独测试点击Excel导出按钮后，浏览器是否下载了正确格式的Excel文件。

**Acceptance Scenarios**:

1. **Given** 弹窗已打开, **When** 选择"直接导出Excel"并确认, **Then** 浏览器开始下载Excel文件
2. **Given** Excel文件下载完成, **When** 打开文件, **Then** 内容与之前的导出功能一致（学号、姓名、各题分数、总分、扣分详情）

---

### User Story 4 - Excel导出模板与文档库对接 (Priority: P2)

从文档库的成绩文档使用"机试考核登分表"模板导出Excel时，系统能自动识别并填充学生成绩数据。

**Why this priority**: 这是数据链路闭环的关键——确保导出到文档库的数据能够被Excel模板正确消费。

**Independent Test**: 可以先导出成绩到文档库，然后在文档库中选择该文档并使用"机试考核登分表"模板导出，验证Excel内容正确。

**Acceptance Scenarios**:

1. **Given** 文档库中存在成绩文档（包含source_class_id元数据）, **When** 选择"机试考核登分表"模板导出, **Then** 系统自动查询关联班级的学生成绩
2. **Given** 导出的Excel文件, **When** 查看内容, **Then** 学生信息和分数与原批改数据一致

---

### Edge Cases

- **无成绩数据时导出**: 如果班级没有任何已批改学生，导出到文档库时应提示"暂无成绩数据可导出"
- **元数据不完整**: 如果试卷缺少教师/课程编码元数据，应使用默认值（空字符串）或从当前日期推断学年学期
- **导出过程中网络中断**: 应显示错误提示，允许用户重试
- **弹窗打开时批改进行中**: 应禁用导出按钮或提示"请等待批改完成"

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统 MUST 在用户点击"导出成绩"按钮时显示导出选择弹窗
- **FR-002**: 弹窗 MUST 提供两个导出选项："导出到文档库"和"直接导出Excel"
- **FR-003**: 弹窗设计 MUST 遵循现有系统弹窗风格（参考教务系统登录弹窗的视觉样式）
- **FR-004**: 选择"导出到文档库"时，系统 MUST 收集以下元数据：
  - 课程名称（从班级记录获取）
  - 班级名称（从班级记录获取）
  - 教师（从生成批改核心时使用的试卷元数据追溯）
  - 课程编码（从试卷元数据追溯）
  - 学年学期（优先从试卷元数据获取，无则根据当前日期推断）
- **FR-005**: 生成的Markdown文档 MUST 包含学生成绩表格，列包括：序号、学号、姓名、性别、各大题分数、总分、状态
- **FR-006**: 生成的文档 MUST 存入file_assets表，doc_category设为"other"，并记录source_class_id
- **FR-007**: 文档命名格式 MUST 为"{学年学期}-{课程名}-{班级名}-机考分数.md"
- **FR-008**: 如果已存在同班级的成绩文档，系统 MUST 添加时间戳后缀避免命名冲突
- **FR-009**: 选择"直接导出Excel"时，系统 MUST 执行现有的Excel导出逻辑，保持功能不变
- **FR-010**: "机试考核登分表"Excel模板 MUST 能够通过source_class_id从成绩文档关联到原始班级数据

### Key Entities

- **导出选择弹窗**: 包含导出方式选项、确认/取消按钮、加载状态显示
- **成绩文档**: 存储于file_assets表的Markdown文档，包含元数据和学生成绩表格
- **元数据追溯链**: class.strategy → ai_tasks.grader_id → ai_tasks.exam_path → file_assets.meta_info

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 用户可在3秒内完成从点击导出按钮到选择导出方式的操作
- **SC-002**: 导出到文档库的成功率达到95%以上（在有成绩数据的前提下）
- **SC-003**: 生成的成绩文档包含100%的已批改学生数据
- **SC-004**: 从文档库导出Excel时，学生成绩数据匹配率达到100%
- **SC-005**: 弹窗交互体验满足用户期望（打开/关闭流畅，状态反馈及时）

## Assumptions

- 用户已完成批改任务（至少有一名学生已批改）才会使用导出功能
- 现有的ScoreDocumentService服务可以被复用于弹窗导出流程
- 前端弹窗使用与jwxt_login_modal.html相同的设计模式和动画效果
- 学年学期推断逻辑遵循中国高校学期制度（9-1月为第一学期，2-8月为第二学期）
