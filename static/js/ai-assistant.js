/**
 * AI 助手前端逻辑
 * Feature: 002-global-ai-assistant
 *
 * 功能:
 * - 浮窗展开/收起
 * - 消息发送/接收
 * - 打字机效果
 * - 页面切换触发
 * - 多标签页同步
 */

(function() {
    'use strict';

    // ==================== 配置 ====================
    const CONFIG = {
        API_BASE: '/api/assistant',
        POLL_INTERVAL: 5000,          // 轮询间隔 (ms)
        RATE_LIMIT_COOLDOWN: 60000,   // 速率限制冷却 (ms)
        TYPEWRITER_SPEED: 30,         // 打字机速度 (ms/字符)
        MAX_MESSAGE_LENGTH: 2000,
        HISTORY_LIMIT: 20,            // 单次加载历史消息数
        STORAGE_KEY_PREFIX: 'ai_assistant_'
    };

    // ==================== 状态 ====================
    const state = {
        conversationId: null,
        lastMessageId: 0,
        isOpen: false,
        isLoading: false,
        lastPageChangeTrigger: 0,
        currentPageContext: null,
        pollTimer: null,
        messages: []
    };

    // ==================== DOM 元素 ====================
    let elements = {};

    function initElements() {
        elements = {
            widget: document.getElementById('ai-assistant-widget'),
            toggleBtn: document.getElementById('ai-toggle-btn'),
            chatPanel: document.getElementById('ai-chat-panel'),
            closeBtn: document.getElementById('ai-close-btn'),
            newChatBtn: document.getElementById('ai-new-chat-btn'),
            messagesContainer: document.getElementById('ai-messages'),
            input: document.getElementById('ai-input'),
            sendBtn: document.getElementById('ai-send-btn'),
            charCount: document.getElementById('ai-char-count'),
            unreadBadge: document.getElementById('ai-unread-badge'),
            welcomePlaceholder: document.getElementById('ai-welcome-placeholder'),
            loadMore: document.getElementById('ai-load-more'),
            statusText: document.getElementById('ai-status-text'),
            quickPrompts: document.querySelectorAll('.quick-prompt')
        };
    }

    // ==================== 工具函数 ====================

    function formatTime(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    function detectPageContext() {
        const path = window.location.pathname;
        if (path === '/' || path === '/dashboard') return 'dashboard';
        if (path.includes('/tasks') || path.includes('/grader')) return 'tasks';
        if (path.includes('/student')) return 'student_list';
        if (path.includes('/ai_generator')) return 'ai_generator';
        if (path.includes('/export')) return 'export';
        if (path.includes('/library')) return 'library';
        if (path.includes('/admin')) return 'admin';
        return 'dashboard';
    }

    function scrollToBottom() {
        if (elements.messagesContainer) {
            elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
        }
    }

    // ==================== API 调用 ====================

    async function apiCall(endpoint, options = {}) {
        const url = CONFIG.API_BASE + endpoint;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        };
        const response = await fetch(url, { ...defaultOptions, ...options });
        const data = await response.json();
        if (!response.ok && data.status === 'error') {
            throw new Error(data.error?.message || '请求失败');
        }
        return data;
    }

    async function getActiveConversation() {
        const data = await apiCall('/conversations/active');
        if (data.status === 'success') {
            state.conversationId = data.data.id;
            return data.data;
        }
        return null;
    }

    async function createNewConversation() {
        const data = await apiCall('/conversations', {
            method: 'POST',
            body: JSON.stringify({ title: '新对话' })
        });
        if (data.status === 'success') {
            state.conversationId = data.data.id;
            state.messages = [];
            state.lastMessageId = 0;
            return data.data;
        }
        return null;
    }

    async function loadMessages(limit = CONFIG.HISTORY_LIMIT, offset = 0) {
        if (!state.conversationId) return [];
        const data = await apiCall(`/conversations/${state.conversationId}/messages?limit=${limit}&offset=${offset}&order=desc`);
        if (data.status === 'success') {
            return data.data.messages.reverse(); // 反转为时间正序
        }
        return [];
    }

    async function sendMessage(content) {
        if (!state.conversationId || !content.trim()) return null;

        const data = await apiCall(`/conversations/${state.conversationId}/messages`, {
            method: 'POST',
            body: JSON.stringify({
                content: content.trim(),
                page_context: state.currentPageContext
            })
        });

        if (data.status === 'success') {
            return data.data;
        }
        return null;
    }

    async function triggerPageChange(pageContext) {
        // 前端速率限制检查
        const now = Date.now();
        if (now - state.lastPageChangeTrigger < CONFIG.RATE_LIMIT_COOLDOWN) {
            console.log('[AI Assistant] 页面切换触发被前端速率限制');
            return null;
        }

        try {
            const data = await apiCall('/trigger/page-change', {
                method: 'POST',
                body: JSON.stringify({
                    page_context: pageContext,
                    page_url: window.location.pathname
                })
            });

            if (data.status === 'success' && data.data.triggered) {
                state.lastPageChangeTrigger = now;
                return data.data.message;
            }
        } catch (e) {
            console.error('[AI Assistant] 页面切换触发失败:', e);
        }
        return null;
    }

    async function pollNewMessages() {
        if (!state.conversationId || !state.isOpen) return;

        try {
            const data = await apiCall(`/poll?conversation_id=${state.conversationId}&last_message_id=${state.lastMessageId}`);
            if (data.status === 'success' && data.data.has_new) {
                for (const msg of data.data.messages) {
                    appendMessage(msg, true);
                }
            }
        } catch (e) {
            console.error('[AI Assistant] 轮询失败:', e);
        }
    }

    // ==================== 消息渲染 ====================

    function createMessageElement(message, withTypewriter = false) {
        const div = document.createElement('div');
        div.className = `ai-message ${message.role}-message ai-message-enter flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`;
        div.setAttribute('data-message-id', message.id);

        const time = formatTime(message.created_at);

        if (message.role === 'user') {
            div.innerHTML = `
                <div class="max-w-[80%] bg-gradient-to-r from-indigo-500 to-blue-500 text-white px-4 py-2.5 rounded-2xl rounded-br-md shadow-md">
                    <p class="text-sm leading-relaxed whitespace-pre-wrap">${escapeHtml(message.content)}</p>
                    <span class="text-xs opacity-70 mt-1 block text-right">${time}</span>
                </div>
            `;
        } else if (message.role === 'assistant') {
            div.innerHTML = `
                <div class="flex gap-2 max-w-[85%]">
                    <div class="flex-shrink-0 w-7 h-7 rounded-full bg-gradient-to-r from-indigo-100 to-blue-100 flex items-center justify-center">
                        <i class="fas fa-robot text-indigo-500 text-xs"></i>
                    </div>
                    <div class="bg-white/90 backdrop-blur-sm px-4 py-2.5 rounded-2xl rounded-bl-md shadow-sm border border-slate-100">
                        <p class="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap message-content">${withTypewriter ? '' : escapeHtml(message.content)}</p>
                        <span class="text-xs text-slate-400 mt-1 block">${time}</span>
                    </div>
                </div>
            `;
        } else {
            // system message
            div.className = 'ai-message system-message ai-message-enter flex justify-center';
            div.innerHTML = `
                <div class="text-xs text-slate-400 bg-slate-100/50 px-3 py-1 rounded-full">
                    ${escapeHtml(message.content)}
                </div>
            `;
        }

        return div;
    }

    function createLoadingElement() {
        const div = document.createElement('div');
        div.className = 'ai-message loading-message flex justify-start';
        div.id = 'ai-loading-indicator';
        div.innerHTML = `
            <div class="flex gap-2">
                <div class="flex-shrink-0 w-7 h-7 rounded-full bg-gradient-to-r from-indigo-100 to-blue-100 flex items-center justify-center">
                    <i class="fas fa-robot text-indigo-500 text-xs"></i>
                </div>
                <div class="ai-loading bg-white/90 backdrop-blur-sm rounded-2xl rounded-bl-md shadow-sm border border-slate-100">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                </div>
            </div>
        `;
        return div;
    }

    function appendMessage(message, withTypewriter = false) {
        // 隐藏欢迎占位符
        if (elements.welcomePlaceholder) {
            elements.welcomePlaceholder.style.display = 'none';
        }

        // 检查是否已存在该消息
        const existing = elements.messagesContainer.querySelector(`[data-message-id="${message.id}"]`);
        if (existing) return;

        const msgElement = createMessageElement(message, withTypewriter);
        elements.messagesContainer.appendChild(msgElement);

        // 更新最后消息 ID
        if (message.id > state.lastMessageId) {
            state.lastMessageId = message.id;
        }

        // 打字机效果
        if (withTypewriter && message.role === 'assistant') {
            const contentEl = msgElement.querySelector('.message-content');
            if (contentEl) {
                typewriterEffect(contentEl, message.content);
            }
        }

        scrollToBottom();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ==================== 打字机效果 ====================

    function typewriterEffect(element, text, speed = CONFIG.TYPEWRITER_SPEED) {
        let index = 0;
        element.innerHTML = '';

        // 添加光标
        const cursor = document.createElement('span');
        cursor.className = 'typing-cursor';
        element.appendChild(cursor);

        function type() {
            if (index < text.length) {
                // 在光标前插入字符
                const char = document.createTextNode(text[index]);
                element.insertBefore(char, cursor);
                index++;
                setTimeout(type, speed);
            } else {
                // 完成后移除光标
                cursor.remove();
            }
        }

        type();
        scrollToBottom();
    }

    // ==================== UI 交互 ====================

    function toggleWidget() {
        state.isOpen = !state.isOpen;

        if (state.isOpen) {
            elements.chatPanel.classList.add('show');
            elements.input.focus();
            hideUnreadBadge();

            // 开始轮询
            startPolling();

            // 加载历史消息
            if (state.messages.length === 0) {
                loadInitialMessages();
            }
        } else {
            elements.chatPanel.classList.remove('show');
            stopPolling();
        }
    }

    function showUnreadBadge(count = 1) {
        if (elements.unreadBadge && !state.isOpen) {
            elements.unreadBadge.textContent = count;
            elements.unreadBadge.classList.remove('hidden');
        }
    }

    function hideUnreadBadge() {
        if (elements.unreadBadge) {
            elements.unreadBadge.classList.add('hidden');
        }
    }

    function showLoading() {
        state.isLoading = true;
        elements.sendBtn.disabled = true;
        elements.statusText.textContent = '思考中...';

        // 添加加载动画
        const loading = createLoadingElement();
        elements.messagesContainer.appendChild(loading);
        scrollToBottom();
    }

    function hideLoading() {
        state.isLoading = false;
        updateSendButtonState();
        elements.statusText.textContent = '在线';

        // 移除加载动画
        const loading = document.getElementById('ai-loading-indicator');
        if (loading) loading.remove();
    }

    function updateSendButtonState() {
        const hasContent = elements.input.value.trim().length > 0;
        elements.sendBtn.disabled = !hasContent || state.isLoading;
    }

    function updateCharCount() {
        const length = elements.input.value.length;
        if (length > 1800) {
            elements.charCount.textContent = `${length}/${CONFIG.MAX_MESSAGE_LENGTH}`;
            elements.charCount.classList.remove('hidden');
            if (length > CONFIG.MAX_MESSAGE_LENGTH) {
                elements.charCount.classList.add('text-red-500');
            } else {
                elements.charCount.classList.remove('text-red-500');
            }
        } else {
            elements.charCount.classList.add('hidden');
        }
    }

    // ==================== 核心操作 ====================

    async function loadInitialMessages() {
        try {
            // 获取或创建活跃对话
            await getActiveConversation();
            if (!state.conversationId) return;

            // 加载历史消息
            const messages = await loadMessages();
            if (messages.length > 0) {
                messages.forEach(msg => appendMessage(msg, false));
            }
        } catch (e) {
            console.error('[AI Assistant] 加载初始消息失败:', e);
        }
    }

    async function handleSendMessage() {
        const content = elements.input.value.trim();
        if (!content || state.isLoading) return;

        // 清空输入
        elements.input.value = '';
        updateSendButtonState();
        updateCharCount();

        // 显示用户消息 (临时)
        const tempUserMsg = {
            id: Date.now(),
            role: 'user',
            content: content,
            created_at: new Date().toISOString()
        };
        appendMessage(tempUserMsg, false);

        // 显示加载状态
        showLoading();

        try {
            const result = await sendMessage(content);
            hideLoading();

            if (result) {
                // 更新用户消息 ID
                const tempEl = elements.messagesContainer.querySelector(`[data-message-id="${tempUserMsg.id}"]`);
                if (tempEl && result.user_message) {
                    tempEl.setAttribute('data-message-id', result.user_message.id);
                    state.lastMessageId = Math.max(state.lastMessageId, result.user_message.id);
                }

                // 显示 AI 回复 (带打字机效果)
                if (result.assistant_message) {
                    appendMessage(result.assistant_message, true);
                }
            }
        } catch (e) {
            hideLoading();
            console.error('[AI Assistant] 发送消息失败:', e);
            // 显示错误消息
            appendMessage({
                id: Date.now(),
                role: 'assistant',
                content: '抱歉，消息发送失败。请稍后再试。',
                created_at: new Date().toISOString()
            }, false);
        }
    }

    async function handleNewChat() {
        if (state.isLoading) return;

        try {
            await createNewConversation();
            // 清空消息显示
            elements.messagesContainer.innerHTML = '';
            if (elements.welcomePlaceholder) {
                elements.welcomePlaceholder.style.display = 'block';
                elements.messagesContainer.appendChild(elements.welcomePlaceholder);
            }
        } catch (e) {
            console.error('[AI Assistant] 创建新对话失败:', e);
        }
    }

    // ==================== 轮询 ====================

    function startPolling() {
        if (state.pollTimer) return;
        state.pollTimer = setInterval(pollNewMessages, CONFIG.POLL_INTERVAL);
    }

    function stopPolling() {
        if (state.pollTimer) {
            clearInterval(state.pollTimer);
            state.pollTimer = null;
        }
    }

    // ==================== 页面切换检测 ====================

    function handlePageChange() {
        const newContext = detectPageContext();

        // 如果是管理页面，禁用自动问候
        if (newContext === 'admin') {
            return;
        }

        if (newContext !== state.currentPageContext) {
            state.currentPageContext = newContext;

            // 触发页面切换问候
            triggerPageChange(newContext).then(message => {
                if (message) {
                    // 自动展开并显示消息
                    if (!state.isOpen) {
                        toggleWidget();
                    }
                    appendMessage(message, true);
                    showUnreadBadge();
                }
            });
        }
    }

    // ==================== 多标签页同步 ====================

    function setupMultiTabSync() {
        // localStorage 事件监听
        window.addEventListener('storage', (e) => {
            if (e.key === CONFIG.STORAGE_KEY_PREFIX + 'new_message') {
                // 其他标签页发送了新消息，触发轮询
                pollNewMessages();
            }
        });
    }

    function notifyOtherTabs() {
        // 通知其他标签页有新消息
        localStorage.setItem(
            CONFIG.STORAGE_KEY_PREFIX + 'new_message',
            Date.now().toString()
        );
    }

    // ==================== 事件绑定 ====================

    function bindEvents() {
        // 展开/收起
        elements.toggleBtn?.addEventListener('click', toggleWidget);
        elements.closeBtn?.addEventListener('click', toggleWidget);

        // 发送消息
        elements.sendBtn?.addEventListener('click', handleSendMessage);
        elements.input?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });

        // 输入监听
        elements.input?.addEventListener('input', () => {
            updateSendButtonState();
            updateCharCount();
        });

        // 输入框焦点动画
        elements.input?.addEventListener('focus', () => {
            elements.input.parentElement.classList.add('ring-2', 'ring-indigo-200');
        });
        elements.input?.addEventListener('blur', () => {
            elements.input.parentElement.classList.remove('ring-2', 'ring-indigo-200');
        });

        // 新建对话
        elements.newChatBtn?.addEventListener('click', handleNewChat);

        // 快捷提示点击
        elements.quickPrompts?.forEach(btn => {
            btn.addEventListener('click', () => {
                const prompt = btn.getAttribute('data-prompt');
                if (prompt) {
                    elements.input.value = prompt;
                    updateSendButtonState();
                    elements.input.focus();
                }
            });
        });

        // 页面切换检测
        window.addEventListener('popstate', handlePageChange);

        // 拦截链接点击
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link && link.href && link.origin === window.location.origin) {
                // 延迟检测页面变化
                setTimeout(handlePageChange, 100);
            }
        });
    }

    // ==================== 初始化 ====================

    function init() {
        // 检查是否存在 widget
        if (!document.getElementById('ai-assistant-widget')) {
            console.log('[AI Assistant] Widget 未找到，跳过初始化');
            return;
        }

        initElements();
        bindEvents();
        setupMultiTabSync();

        // 初始化页面上下文
        state.currentPageContext = detectPageContext();

        console.log('[AI Assistant] 初始化完成');
    }

    // 等待 DOM 加载完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // 暴露公共 API (用于操作触发)
    window.AIAssistant = {
        toggle: toggleWidget,
        triggerOperationFeedback: async function(operationType, result, details) {
            try {
                const data = await apiCall('/trigger/operation', {
                    method: 'POST',
                    body: JSON.stringify({
                        operation_type: operationType,
                        operation_result: result,
                        operation_details: details || {}
                    })
                });

                if (data.status === 'success' && data.data.triggered) {
                    // 自动展开并显示反馈
                    if (!state.isOpen) {
                        toggleWidget();
                    }
                    appendMessage(data.data.message, true);
                    notifyOtherTabs();
                }
            } catch (e) {
                console.error('[AI Assistant] 操作触发失败:', e);
            }
        }
    };
})();
