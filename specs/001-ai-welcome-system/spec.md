# Feature Specification: AI Welcome Message System

**Feature Branch**: `001-ai-welcome-system`
**Created**: 2026-01-21
**Status**: Draft
**Input**: User description: "新建一个AI欢迎语系统，要求如下：1. 欢迎语系统使用AI助手生成用户相关的欢迎语，目的是为用户提供情绪价值和简单的操作指引。并且每个功能模块需要提供对应的欢迎语或指引语。前端显示位置：首页的第一个欢迎方框内（原来的"今天也是充满效率的一天，准备好处理新的批改任务了吗？"的地方）；其他页面的顶栏的合适位置。并且支持动态变动显示框大小。2. 欢迎语后端更新机制：使用数据库缓存，前端刷新页面时读取数据库相关的欢迎语并打印出来。当用户第一次进入系统时触发更新、以及执行写入操作时更新。3. 前端首次显示时模拟AI流式输出效果，如果已经显示过了就直接显示即可。前端样式、交互设计需要参考前端设计规范文档。4. 使用AI助手的stander模型。由于stander模型的聪明程度一般，所以需要明确的指引提示词，并且给足够丰富的用户信息和操作信息，结合当前时间信息等环境信息，让AI猜测下一步需要做什么，给出什么提示等。最好给出几种示例给AI助手。5. 改进过程注意对系统其他部分影响范围。编写代码过程注意不要漏掉其他功能。"

## Clarifications

### Session 2026-01-21

- Q: What is the cache expiration strategy for welcome messages? → A: Time-based expiration of 4 hours (balances freshness with cost)
- Q: What is the AI service timeout threshold before fallback? → A: 5 seconds (balances response time with user patience)
- Q: What validation rules apply to AI-generated content? → A: Basic validation (10-200 chars, valid Chinese text)
- Q: How should the system handle AI service rate limiting? → A: Serve stale cached message if available (graceful degradation)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dashboard Personalized Welcome (Priority: P1)

As a teacher logging into the system, I want to see a personalized, contextually-aware welcome message that provides emotional encouragement and suggests my next action, so that I feel supported and can quickly resume my work.

**Why this priority**: This is the core user-facing feature that delivers immediate value upon login. It sets the tone for the entire user experience and provides the primary emotional benefit.

**Independent Test**: Can be fully tested by logging into the system and observing the welcome message content and display behavior. Delivers value by providing personalized guidance without requiring any other features to be implemented.

**Acceptance Scenarios**:

1. **Given** a teacher logs into the system for the first time today, **When** the dashboard loads, **Then** a personalized welcome message appears with a streaming animation effect
2. **Given** a teacher has pending grading tasks, **When** the dashboard loads, **Then** the welcome message references the pending tasks and encourages completion
3. **Given** a teacher has just created a new class, **When** they return to the dashboard, **Then** the welcome message suggests importing student roster
4. **Given** it is morning, **When** the dashboard loads, **Then** the welcome message uses morning-appropriate greeting and encouragement
5. **Given** it is evening, **When** the dashboard loads, **Then** the welcome message acknowledges end-of-day context and suggests wrapping up tasks

---

### User Story 2 - Cross-Page Contextual Guidance (Priority: P2)

As a teacher navigating to different functional pages, I want to see contextual hints or guidance relevant to that page's functionality, so that I can understand what actions are available and receive relevant tips.

**Why this priority**: Extends the welcome system beyond the homepage to provide ongoing value throughout the user's session. Priority is lower because it builds upon the core P1 feature.

**Independent Test**: Can be tested by navigating to each functional page and verifying the displayed guidance message is relevant to that page's context.

**Acceptance Scenarios**:

1. **Given** a teacher navigates to the AI Generator page, **When** the page loads, **Then** a guidance message about generating grading scripts appears
2. **Given** a teacher navigates to the Student List page, **When** the page loads, **Then** a guidance message about importing or managing students appears
3. **Given** a teacher navigates to the Grading Tasks page, **When** the page loads, **Then** a guidance message about managing and processing grading tasks appears
4. **Given** a teacher navigates to the Export page, **When** the page loads, **Then** a guidance message about exporting grades appears

---

### User Story 3 - Cache Refresh on User Actions (Priority: P2)

As a teacher performing write operations in the system, I want the welcome/guidance messages to refresh afterward to reflect my new context, so that the suggestions remain relevant to my current state.

**Why this priority**: Ensures the AI content stays current without requiring users to wait for regeneration. Important for maintaining relevance, but secondary to the initial display.

**Independent Test**: Can be tested by performing write operations (creating class, uploading file, generating grader) and verifying the welcome message updates accordingly.

**Acceptance Scenarios**:

1. **Given** a teacher is viewing the dashboard, **When** they create a new class, **Then** the welcome message updates to suggest next steps for the new class
2. **Given** a teacher is viewing the dashboard, **When** they import students, **Then** the welcome message updates to acknowledge the import and suggest grading
3. **Given** a teacher is viewing the dashboard, **When** they generate a new grading script, **Then** the welcome message updates to suggest using the new script

---

### User Story 4 - Streaming Display Effect (Priority: P3)

As a teacher viewing AI-generated content for the first time, I want to see a streaming typewriter effect that simulates real-time generation, so that the content feels more engaging and "AI-powered".

**Why this priority**: This is a visual enhancement that improves user experience but doesn't affect functionality. Lower priority as it's purely aesthetic.

**Independent Test**: Can be tested by clearing browser history/storage and refreshing the page to observe the streaming animation on first view.

**Acceptance Scenarios**:

1. **Given** a teacher has not seen the current welcome message, **When** the page loads, **Then** the message displays with a character-by-character or word-by-word streaming animation
2. **Given** a teacher has already seen the welcome message, **When** they refresh the page, **Then** the message displays instantly without animation
3. **Given** the streaming animation is in progress, **When** the user navigates away, **Then** the animation state is preserved for when they return

---

### Edge Cases

- What happens when the AI service is unavailable or returns an error?
  - **Expected**: System displays a predefined fallback welcome message that varies by time of day
- What happens when the AI service request exceeds 5 seconds?
  - **Expected**: System cancels request and displays fallback message within 1 second
- What happens when the AI returns inappropriate or malformed content?
  - **Expected**: System validates content (length 10-200 chars, valid Chinese text) and falls back to default message if validation fails
- What happens when a user's browser doesn't support localStorage?
  - **Expected**: System treats each page load as "first view" and always shows streaming effect
- What happens when the welcome message is extremely long?
  - **Expected**: Container expands dynamically with smooth transition; no content is truncated
- What happens when multiple tabs are open simultaneously?
  - **Expected**: Each tab operates independently; localStorage updates are synchronized
- What happens when the database cache is empty (first system startup)?
  - **Expected**: System triggers AI generation on first request and caches the result
- What happens when a cached message expires (older than 4 hours)?
  - **Expected**: System triggers AI regeneration on next page load and updates cache with new message
- What happens when the AI service returns rate limit error (HTTP 429)?
  - **Expected**: System serves stale cached message if available, otherwise shows fallback message

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate personalized welcome messages using AI service
- **FR-002**: System MUST display welcome messages on the dashboard in the primary welcome panel area
- **FR-003**: System MUST display contextual guidance messages on other functional pages in the top bar area
- **FR-004**: System MUST cache AI-generated messages in persistent storage (database) with a 4-hour TTL
- **FR-005**: System MUST refresh cached messages after write operations (create class, upload file, generate grader, etc.)
- **FR-006**: System MUST display a streaming/typewriter animation effect on first-time viewing of AI-generated content
- **FR-007**: System MUST display content instantly (no animation) on subsequent views of the same content
- **FR-008**: System MUST provide fallback default messages when AI service is unavailable
- **FR-009**: System MUST dynamically adjust container size based on message content length
- **FR-010**: System MUST include contextual information (time, user stats, recent actions) in AI generation requests
- **FR-011**: System MUST provide few-shot examples (3-5) in AI prompts to guide output quality
- **FR-012**: System MUST track whether each user has seen specific messages to control animation behavior
- **FR-013**: System MUST support messages in Chinese language appropriate for educational context
- **FR-014**: System MUST validate AI-generated content (10-200 characters, valid Chinese text) before displaying

### Key Entities

- **Welcome Message**: Represents a single AI-generated greeting, containing:
  - User identifier (who the message is for)
  - Page context (dashboard, tasks, student list, etc.)
  - Message content (the actual text)
  - Generation timestamp
  - Viewed flag (whether user has seen this message)
  - Context snapshot (time, stats used for generation)

- **Message Context**: Represents the data sent to AI for generation, containing:
  - Current time and day of week
  - User statistics (class count, student count, pending tasks)
  - Recent user actions (last 3-5 operations)
  - Target page/module

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% of users report the welcome message as helpful or encouraging (measured via optional feedback)
- **SC-002**: Welcome messages display within 2 seconds of page load (including AI generation if needed)
- **SC-003**: Streaming animation completes within 3 seconds for typical message length (50 characters)
- **SC-004**: Cached messages display instantly (within 500ms) on page refresh
- **SC-005**: AI service fallback occurs within 1 second when primary service times out (5-second threshold) or returns error
- **SC-006**: Welcome messages vary in content across different times of day and user states
- **SC-007**: Container size transitions complete smoothly without visual jump (200-300ms duration)

## Assumptions

1. The system has an existing AI service (ai_assistant.py) that supports "standard" capability models
2. Users access the system through a modern web browser with JavaScript enabled
3. The system already tracks user statistics (classes, students, tasks) in the database
4. User sessions are managed and user identification is available
5. The AI "standard" model has sufficient capability for simple text generation when provided with structured prompts and examples
6. Users are primarily teachers working in Chinese language educational context
7. Peak concurrent users is under 100, so AI generation latency is acceptable

## Scope Exclusions

The following items are explicitly out of scope for this feature:
- Multi-language support (beyond Chinese)
- User preference customization for message style or frequency
- A/B testing of different message variants
- Analytics tracking of message engagement
- Voice output or audio features
- Message editing or regeneration by users
- Admin configuration of AI prompts
