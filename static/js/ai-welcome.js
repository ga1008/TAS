/**
 * static/js/ai-welcome.js
 * AI 欢迎语系统脚本 - 增强版
 * 负责加载、显示、管理 AI 生成的欢迎消息，并支持流式打字机效果
 */

(function() {
    'use strict';

    // localStorage 键前缀
    const STORAGE_PREFIX = 'ai_welcome_seen_';

    // 配置
    const CONFIG = {
        typewriterSpeed: 30,          // 打字机速度 (ms/字符) - 稍微调快一点更流畅
        maxTypewriterTime: 5000,      // 打字机最大执行时间 (ms)
        containerMinHeight: 60,       // 容器最小高度 (px)
        requestTimeout: 8000          // API 请求超时 (ms)
    };

    /**
     * 从当前 URL 路径检测页面上下文
     * @returns {string} 页面上下文
     */
    function detectPageContext() {
        const path = window.location.pathname;

        // 路径到上下文的映射
        const pathMap = {
            '/': 'dashboard',
            '/tasks': 'tasks',
            '/new_class': 'ai_generator',
            '/ai_generator': 'ai_generator',
            '/ai_core_list': 'ai_generator',
            '/export': 'export'
        };

        // 检查前缀匹配
        for (const [pattern, context] of Object.entries(pathMap)) {
            if (path === pattern || path.startsWith(pattern + '/')) {
                return context;
            }
        }

        // 学生相关页面
        if (path.startsWith('/student') || path.startsWith('/students')) {
            return 'student_list';
        }

        // 默认返回 dashboard
        return 'dashboard';
    }

    /**
     * 调整容器高度 (防抖动优化)
     * @param {HTMLElement} container - 容器元素
     * @param {HTMLElement} contentEl - 内容元素 (可选)
     */
    function adjustContainerHeight(container, contentEl) {
        if (!container) return;

        // 如果未提供 contentEl，尝试查找
        if (!contentEl) {
            contentEl = container.querySelector('#welcome-content, #compact-welcome-text');
        }
        if (!contentEl) return;

        // 使用 requestAnimationFrame 确保在渲染后计算
        requestAnimationFrame(() => {
            // 获取实际内容高度
            const contentHeight = contentEl.scrollHeight;
            // 计算目标高度（保持最小高度，防止收缩太小）
            // +20 是为了留出 padding 空间，避免文字贴边
            const newHeight = Math.max(CONFIG.containerMinHeight, contentHeight + 20);

            // 只有当高度确实需要变大，或者当前是初始状态时才调整
            // 避免打字机过程中的微小高度收缩导致抖动
            const currentHeight = container.clientHeight;
            if (newHeight > currentHeight || currentHeight <= CONFIG.containerMinHeight) {
                container.style.minHeight = newHeight + 'px';
            }
        });
    }

    /**
     * 打字机效果
     * @param {HTMLElement} element - 目标文本元素
     * @param {string} text - 要显示的文本
     * @param {HTMLElement} container - 外层容器（用于动态调整高度）
     * @param {Function} callback - 完成回调
     */
    function typewriter(element, text, container, callback) {
        let i = 0;
        const textLength = text.length;
        const startTime = Date.now();

        // 准备状态
        element.textContent = '';
        element.classList.add('typewriter-cursor');

        // 确保容器初始高度正确
        adjustContainerHeight(container, element);

        function type() {
            // 检查是否超时或元素已移除
            if (!document.body.contains(element)) return;

            if (Date.now() - startTime > CONFIG.maxTypewriterTime) {
                element.textContent = text;
                finishTypewriter();
                return;
            }

            if (i < textLength) {
                element.textContent += text.charAt(i);
                i++;

                // 每打几个字调整一次高度，确保多行文本时容器平滑展开
                if (i % 10 === 0 && container) {
                    adjustContainerHeight(container, element);
                }

                setTimeout(type, CONFIG.typewriterSpeed);
            } else {
                finishTypewriter();
            }
        }

        function finishTypewriter() {
            element.textContent = text; // 确保文字完整
            element.classList.remove('typewriter-cursor');
            if (container) adjustContainerHeight(container, element);
            if (typeof callback === 'function') {
                callback();
            }
        }

        type();
    }

    /**
     * 检查消息是否已被查看
     */
    function hasSeenMessage(storageKey) {
        try {
            return localStorage.getItem(STORAGE_PREFIX + storageKey) === 'true';
        } catch (e) {
            console.warn('localStorage 不可用:', e);
            return false;
        }
    }

    /**
     * 标记消息为已查看
     */
    function markMessageAsSeen(storageKey) {
        try {
            localStorage.setItem(STORAGE_PREFIX + storageKey, 'true');
        } catch (e) {
            console.warn('无法写入 localStorage:', e);
        }
    }

    /**
     * 显示欢迎语内容（标准模式 - 首页）
     */
    function displayWelcomeMessage(container, data, animate) {
        const loadingEl = container.querySelector('#welcome-loading');
        const contentEl = container.querySelector('#welcome-content');
        const errorEl = container.querySelector('#welcome-error');
        const textEl = container.querySelector('#welcome-text');

        // 状态切换
        if (loadingEl) loadingEl.classList.add('hidden');
        if (errorEl) errorEl.classList.add('hidden');

        if (contentEl) {
            contentEl.classList.remove('hidden');
            contentEl.classList.add('animate-in');
        }

        if (!textEl) return;

        const message = data.message_content || data.message || '';
        const storageKey = data.storage_key;

        // 强制刷新时（animate=true），或者首次查看时，使用打字机
        // 注意：如果 data.status 是 'cached' 且 hasSeenMessage 为 true，则不动画
        const shouldAnimate = animate &&
                              message.length > 0 &&
                              (!storageKey || !hasSeenMessage(storageKey));

        if (shouldAnimate) {
            typewriter(textEl, message, container, () => {
                if (storageKey) markMessageAsSeen(storageKey);
            });
        } else {
            textEl.textContent = message;
            // 确保没有残留的光标
            textEl.classList.remove('typewriter-cursor');
            adjustContainerHeight(container, textEl);
        }
    }

    /**
     * 显示欢迎语内容（紧凑模式 - 顶部栏）
     */
    function displayCompactWelcomeMessage(container, data) {
        const loadingEl = container.querySelector('#compact-welcome-loading');
        const textEl = container.querySelector('#compact-welcome-text');
        const refreshBtn = container.querySelector('#compact-welcome-refresh');

        if (loadingEl) loadingEl.classList.add('hidden');

        if (textEl) {
            const message = data.message_content || data.message || '';
            textEl.textContent = message;
            textEl.classList.remove('hidden');
        }

        if (refreshBtn) {
            refreshBtn.classList.remove('hidden');
        }
    }

    /**
     * 显示回退消息
     */
    function showFallbackMessage(container, message) {
        const fallbackText = message || '今天也是充满效率的一天，准备好处理新的批改任务了吗？';
        const data = {
            message_content: fallbackText,
            storage_key: null
        };

        if (container.id === 'compact-welcome-container') {
            displayCompactWelcomeMessage(container, data);
        } else {
            // 回退消息通常不需要打字机动画，直接显示
            displayWelcomeMessage(container, data, false);
        }
    }

    /**
     * 核心加载函数
     * @param {string} pageContext - 上下文
     * @param {string} mode - 'standard' | 'compact'
     * @param {boolean} forceRefresh - 是否强制刷新(忽略缓存)
     */
    function loadWelcomeMessage(pageContext, mode, forceRefresh = false) {
        return new Promise((resolve, reject) => {
            const containerId = mode === 'compact' ? 'compact-welcome-container' : 'ai-welcome-container';
            const container = document.getElementById(containerId);

            if (!container) {
                // 容器不存在是正常的（例如在不显示欢迎语的页面），静默失败
                return resolve();
            }

            if (!pageContext) {
                pageContext = container.dataset.pageContext || detectPageContext();
            }

            // 只有在强制刷新时才显示加载态，避免普通加载时的闪烁
            if (forceRefresh) {
                if (mode === 'compact') {
                     const loadingEl = container.querySelector('#compact-welcome-loading');
                     const textEl = container.querySelector('#compact-welcome-text');
                     if(loadingEl) loadingEl.classList.remove('hidden');
                     if(textEl) textEl.classList.add('hidden');
                } else {
                     const loadingEl = container.querySelector('#welcome-loading');
                     const contentEl = container.querySelector('#welcome-content');
                     if(loadingEl) loadingEl.classList.remove('hidden');
                     if(contentEl) contentEl.classList.add('hidden');
                }
            }

            // 构建 API URL
            // 如果是 forceRefresh，我们使用 POST 刷新端点，或者带参数的 GET
            // 这里根据后端设计，使用带参数的 GET 或 POST
            let url;
            let method = 'GET';

            if (forceRefresh) {
                url = `/api/welcome/messages/refresh?page_context=${encodeURIComponent(pageContext)}`;
                method = 'POST';
            } else {
                url = `/api/welcome/messages?page_context=${encodeURIComponent(pageContext)}`;
            }

            const timeoutId = setTimeout(() => {
                showFallbackMessage(container);
                // 不 reject，避免控制台报错，只是降级显示
            }, CONFIG.requestTimeout);

            fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => response.json())
            .then(data => {
                clearTimeout(timeoutId);

                if (['success', 'cached', 'generated', 'fallback'].includes(data.status)) {
                    if (mode === 'compact') {
                        displayCompactWelcomeMessage(container, data.data);
                    } else {
                        // 强制刷新时，永远启用动画
                        displayWelcomeMessage(container, data.data, forceRefresh || true);
                    }
                    resolve(data);
                } else {
                    showFallbackMessage(container);
                    // 业务层面的错误也算处理完成
                    resolve(data);
                }
            })
            .catch(error => {
                clearTimeout(timeoutId);
                console.error('[AI Welcome] Load failed:', error);
                showFallbackMessage(container);
                resolve(); // 降级处理
            });
        });
    }

    // --- 初始化逻辑 ---

    document.addEventListener('DOMContentLoaded', function() {
        // 1. 初始化标准容器
        const standardContainer = document.getElementById('ai-welcome-container');
        if (standardContainer) {
            loadWelcomeMessage(null, 'standard');
        }

        // 2. 初始化紧凑容器
        const compactContainer = document.getElementById('compact-welcome-container');
        if (compactContainer) {
            loadWelcomeMessage(null, 'compact');
        }
    });

    // --- 全局事件监听 ---

    // 监听 'tas:refresh_welcome' 事件
    // 其他模块（如文件上传成功、任务创建成功）可触发此事件来刷新欢迎语
    window.addEventListener('tas:refresh_welcome', function(event) {
        console.log('[AI Welcome] Received refresh event');

        // 刷新标准容器
        const standardContainer = document.getElementById('ai-welcome-container');
        if (standardContainer) {
            loadWelcomeMessage(null, 'standard', true); // true = force refresh
        }

        // 刷新紧凑容器
        const compactContainer = document.getElementById('compact-welcome-container');
        if (compactContainer) {
            loadWelcomeMessage(null, 'compact', true);
        }
    });

    // --- 导出全局对象 ---

    window.AIWelcome = {
        load: (ctx) => loadWelcomeMessage(ctx, 'standard'),
        refresh: (ctx) => loadWelcomeMessage(ctx, 'standard', true),
        loadCompact: (ctx) => loadWelcomeMessage(ctx, 'compact'),
        refreshCompact: (ctx) => loadWelcomeMessage(ctx, 'compact', true),
        triggerRefresh: () => window.dispatchEvent(new CustomEvent('tas:refresh_welcome')),
        detectContext: detectPageContext
    };

})();