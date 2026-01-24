/**
 * static/js/ai-welcome.js
 * AI 欢迎语系统 - 增强版 (右下角悬浮交互)
 * 负责管理主动触发、操作响应、手动对话及 UI 动效
 */

(function() {
    'use strict';

    // === 配置常量 ===
    const CONFIG = {
        minInterval: 60 * 1000,      // 最短触发间隔: 1分钟
        maxInterval: 10 * 60 * 1000, // 最长触发间隔: 10分钟
        typewriterSpeed: 35,         // 打字速度 (ms)
        apiEndpoint: '/api/welcome/messages',
        chatEndpoint: '/api/welcome/chat',
        maxChatHistory: 50,          // sessionStorage 最多保存 50 条
        chatStorageKey: 'ai_chat_history'
    };

    // === 状态变量 ===
    let timerId = null;
    let isChatOpen = false;
    let isThinking = false;
    let typingTimer = null; // 用于打字机取消

    // === DOM 元素缓存 ===
    const els = {
        root: null,
        bubbleContainer: null,
        bubbleContent: null,
        bubbleClose: null,
        chatWindow: null,
        triggerBtn: null,
        chatInput: null,
        chatForm: null,
        chatMessages: null,
        thinkingOverlay: null,
        btnThinking: null,
        btnIcon: null
    };

    /**
     * 初始化 DOM 元素引用
     */
    function initElements() {
        els.root = document.getElementById('ai-widget-root');
        if (!els.root) return false;

        els.bubbleContainer = document.getElementById('ai-bubble-container');
        els.bubbleContent = document.getElementById('ai-bubble-content');
        els.bubbleClose = document.getElementById('ai-bubble-close');

        els.chatWindow = document.getElementById('ai-chat-window');
        els.triggerBtn = document.getElementById('ai-trigger-btn');
        els.btnIcon = els.triggerBtn ? els.triggerBtn.querySelector('.fa-robot') : null;
        els.btnThinking = document.getElementById('ai-btn-thinking');

        els.chatInput = document.getElementById('ai-chat-input');
        els.chatForm = document.getElementById('ai-chat-form');
        els.chatMessages = document.getElementById('ai-chat-messages');
        els.thinkingOverlay = document.getElementById('ai-thinking-overlay');

        return true;
    }

    // === sessionStorage 聊天历史管理 ===

    /**
     * 获取聊天历史
     */
    function getChatHistory() {
        try {
            const data = sessionStorage.getItem(CONFIG.chatStorageKey);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            console.warn('[AI Welcome] Failed to load chat history:', e);
            return [];
        }
    }

    /**
     * 保存聊天消息到历史
     */
    function saveChatMessage(role, text) {
        try {
            let history = getChatHistory();
            history.push({ role, text, time: Date.now() });

            // 保持最多 maxChatHistory 条
            if (history.length > CONFIG.maxChatHistory) {
                history = history.slice(-CONFIG.maxChatHistory);
            }

            sessionStorage.setItem(CONFIG.chatStorageKey, JSON.stringify(history));
        } catch (e) {
            console.warn('[AI Welcome] Failed to save chat message:', e);
        }
    }

    /**
     * 恢复聊天历史到 UI
     */
    function restoreChatHistory() {
        if (!els.chatMessages) return;

        const history = getChatHistory();
        if (history.length === 0) return;

        // 清空默认欢迎消息外的内容（保留第一个）
        while (els.chatMessages.children.length > 1) {
            els.chatMessages.removeChild(els.chatMessages.lastChild);
        }

        // 渲染历史消息
        history.forEach(msg => {
            appendMessageToDOM(msg.role, msg.text);
        });

        scrollToBottom();
    }

    /**
     * 清空聊天历史
     */
    function clearChatHistory() {
        try {
            sessionStorage.removeItem(CONFIG.chatStorageKey);
        } catch (e) {
            console.warn('[AI Welcome] Failed to clear chat history:', e);
        }
    }

    // === 核心功能：触发机制 ===

    /**
     * 启动随机定时器 (1-10分钟)
     */
    function startRandomTimer() {
        if (timerId) clearTimeout(timerId);

        const delay = Math.floor(Math.random() * (CONFIG.maxInterval - CONFIG.minInterval + 1)) + CONFIG.minInterval;
        // console.log(`[AI Welcome] Next auto-trigger scheduled in ${(delay/1000).toFixed(0)}s`);

        timerId = setTimeout(() => {
            // 只有当聊天窗口关闭且未在思考时，才尝试触发
            if (!isChatOpen && !isThinking) {
                triggerAI('timer');
            }
            startRandomTimer(); // 递归调用，保持循环
        }, delay);
    }

    /**
     * 检测当前页面上下文
     */
    function detectPageContext() {
        const path = window.location.pathname;
        if (path === '/' || path === '/dashboard') return 'dashboard';
        if (path.startsWith('/tasks')) return 'tasks';
        if (path.startsWith('/student')) return 'student_list';
        if (path.startsWith('/ai_generator')) return 'ai_generator';
        if (path.startsWith('/export')) return 'export';
        if (path.startsWith('/library')) return 'library';
        return 'dashboard';
    }

    /**
     * 触发 AI 获取消息
     * @param {string} type - 'timer' | 'action'
     * @param {string} details - 操作详情
     */
    async function triggerAI(type, details = null) {
        if (isThinking) return;
        setThinkingState(true);

        try {
            const context = detectPageContext();

            const response = await fetch(CONFIG.apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    page_context: context,
                    trigger_type: type,
                    action_details: details
                })
            });

            // 处理网络错误
            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            if (data.status === 'success') {
                showBubble(data.data.message_content);
            } else if (data.status === 'fallback') {
                showBubble(data.data.message_content); // 回退消息也显示
            } else if (data.status === 'silence') {
                console.log('[AI Welcome] Silent mode (Rate Limited)');
            }
        } catch (e) {
            console.error('[AI Welcome] Trigger failed:', e);
        } finally {
            setThinkingState(false);
        }
    }

    // === UI 交互逻辑 ===

    /**
     * 设置思考状态 (控制图标动画)
     */
    function setThinkingState(thinking) {
        isThinking = thinking;

        // 1. 悬浮按钮状态
        if (els.btnThinking && els.btnIcon) {
            if (thinking) {
                els.btnThinking.classList.remove('hidden');
                els.btnIcon.classList.add('opacity-0'); // 隐藏机器人图标
            } else {
                els.btnThinking.classList.add('hidden');
                els.btnIcon.classList.remove('opacity-0');
            }
        }

        // 2. 聊天窗口内状态
        if (els.thinkingOverlay) {
            thinking ? els.thinkingOverlay.classList.remove('hidden')
                     : els.thinkingOverlay.classList.add('hidden');
        }
    }

    /**
     * 显示气泡消息
     */
    function showBubble(text) {
        if (!els.bubbleContainer || isChatOpen) return;

        // 重置状态
        els.bubbleContainer.classList.remove('hidden');
        // 强制重绘以触发 transition
        void els.bubbleContainer.offsetWidth;

        els.bubbleContainer.classList.remove('scale-95', 'opacity-0', 'translate-y-2');
        els.bubbleContainer.classList.add('scale-100', 'opacity-100', 'translate-y-0');

        // 执行打字机
        typewriter(els.bubbleContent, text, () => {
            // 打字结束后，15秒自动消失 (除非用户 hover)
            const autoHideTimer = setTimeout(hideBubble, 15000);

            els.bubbleContainer.onmouseenter = () => clearTimeout(autoHideTimer);
            els.bubbleContainer.onmouseleave = () => setTimeout(hideBubble, 5000);
        });
    }

    /**
     * 隐藏气泡消息
     */
    function hideBubble() {
        if (!els.bubbleContainer) return;

        els.bubbleContainer.classList.remove('scale-100', 'opacity-100', 'translate-y-0');
        els.bubbleContainer.classList.add('scale-95', 'opacity-0', 'translate-y-2');

        setTimeout(() => {
            els.bubbleContainer.classList.add('hidden');
            if (els.bubbleContent) els.bubbleContent.textContent = ''; // 清空内容
        }, 300); // 等待 CSS transition 结束
    }

    /**
     * 切换聊天窗口显示/隐藏
     */
    function toggleChat() {
        isChatOpen = !isChatOpen;

        if (isChatOpen) {
            hideBubble(); // 打开聊天必然关闭气泡
            els.chatWindow.classList.remove('hidden');
            // 动画
            requestAnimationFrame(() => {
                els.chatWindow.classList.remove('scale-95', 'opacity-0', 'translate-y-4');
                els.chatWindow.classList.add('scale-100', 'opacity-100', 'translate-y-0');
            });
            setTimeout(() => els.chatInput && els.chatInput.focus(), 100);

            // 滚动到底部
            scrollToBottom();
        } else {
            els.chatWindow.classList.remove('scale-100', 'opacity-100', 'translate-y-0');
            els.chatWindow.classList.add('scale-95', 'opacity-0', 'translate-y-4');
            setTimeout(() => els.chatWindow.classList.add('hidden'), 300);
        }
    }

    /**
     * 消息列表滚动到底部
     */
    function scrollToBottom() {
        if (els.chatMessages) {
            els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
        }
    }

    /**
     * 打字机效果
     */
    function typewriter(el, text, callback) {
        if (!el) return;
        if (typingTimer) clearTimeout(typingTimer);

        el.textContent = '';
        let i = 0;

        function type() {
            if (i < text.length) {
                el.textContent += text.charAt(i);
                i++;
                typingTimer = setTimeout(type, CONFIG.typewriterSpeed);
                // 如果是在聊天框打字，保持滚动
                if (isChatOpen) scrollToBottom();
            } else {
                if (callback) callback();
            }
        }
        type();
    }

    /**
     * 发送手动消息
     */
    async function sendManualMessage(e) {
        if (e) e.preventDefault();

        const msg = els.chatInput.value.trim();
        if (!msg) return;

        // 1. UI: 显示用户消息
        appendMessage('user', msg);
        els.chatInput.value = '';

        // 2. 状态: 思考中
        setThinkingState(true);

        // 3. API 调用
        try {
            const context = detectPageContext();
            const response = await fetch(CONFIG.chatEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: msg,
                    page_context: context
                })
            });

            const data = await response.json();

            setThinkingState(false);

            if (data.status === 'success') {
                appendMessage('ai', data.data.reply);
            } else {
                appendMessage('ai', '哎呀，我大脑短路了，稍后再试吧。');
            }
        } catch (err) {
            setThinkingState(false);
            console.error(err);
            appendMessage('ai', '网络连接似乎断开了... (T_T)');
        }
    }

    /**
     * 添加消息到 DOM (内部函数，不保存到 sessionStorage)
     */
    function appendMessageToDOM(role, text) {
        if (!els.chatMessages) return;

        const isUser = role === 'user';
        const div = document.createElement('div');
        div.className = `flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`;

        // 样式类
        const bubbleClass = isUser
            ? 'bg-indigo-600 text-white rounded-tr-none'
            : 'bg-white border border-slate-100 text-slate-700 rounded-tl-none';

        div.innerHTML = `
            <div class="${bubbleClass} py-2 px-3 rounded-2xl shadow-sm text-sm max-w-[85%] break-words">
                ${text} </div>
        `;

        els.chatMessages.appendChild(div);
        scrollToBottom();
    }

    /**
     * 添加消息到聊天界面并保存到 sessionStorage
     */
    function appendMessage(role, text) {
        appendMessageToDOM(role, text);
        saveChatMessage(role, text);
    }

    // === 事件监听 ===

    function setupEventListeners() {
        // 1. 全局 Action 事件监听 (供其他模块调用)
        window.addEventListener('tas:action', (e) => {
            // console.log('[AI Welcome] Action received:', e.detail);
            // 动作触发不检查 isChatOpen，但如果正在聊天则不弹气泡
            if (!isChatOpen) {
                triggerAI('action', e.detail);
            }
        });

        // 2. 兼容旧版刷新事件
        window.addEventListener('tas:refresh_welcome', () => {
            triggerAI('action', '数据更新');
        });

        // 3. UI 事件
        if (els.triggerBtn) els.triggerBtn.addEventListener('click', toggleChat);
        if (els.bubbleClose) els.bubbleClose.addEventListener('click', (e) => {
            e.stopPropagation();
            hideBubble();
        });
        if (els.chatForm) els.chatForm.addEventListener('submit', sendManualMessage);
    }

    // === 初始化入口 ===

    document.addEventListener('DOMContentLoaded', () => {
        if (initElements()) {
            setupEventListeners();
            startRandomTimer();

            // 恢复聊天历史
            restoreChatHistory();

            // 初始检查：如果刚好有未读消息或通过 URL 参数触发，可以在此处理
            // 这里我们选择 2秒后尝试触发一次进入页面的欢迎（如果冷却允许）
            setTimeout(() => triggerAI('action', 'page_enter'), 2000);
        }
    });

    // 暴露全局对象
    window.AIWelcome = {
        hideBubble,
        toggleChat,
        trigger: (details) => triggerAI('action', details)
    };

})();