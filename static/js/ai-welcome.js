/**
 * AI 欢迎语系统脚本
 * 负责加载、显示和管理 AI 生成的欢迎消息
 */

(function() {
    'use strict';

    // localStorage 键前缀
    const STORAGE_PREFIX = 'ai_welcome_seen_';

    // 配置
    const CONFIG = {
        typewriterSpeed: 50,          // 打字机速度 (ms/字符)
        maxTypewriterTime: 3000,      // 打字机最大执行时间 (ms)
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
            '/export': 'export'
        };

        // 检查前缀匹配
        for (const [pattern, context] of Object.entries(pathMap)) {
            if (path === pattern || path.startsWith(pattern + '/')) {
                return context;
            }
        }

        // 学生相关页面
        if (path.startsWith('/student')) {
            return 'student_list';
        }

        // 默认返回 dashboard
        return 'dashboard';
    }

    /**
     * 打字机效果
     * @param {HTMLElement} element - 目标元素
     * @param {string} text - 要显示的文本
     * @param {Function} callback - 完成回调
     */
    function typewriter(element, text, callback) {
        let i = 0;
        const textLength = text.length;
        const startTime = Date.now();

        // 清空元素
        element.textContent = '';
        element.classList.add('typewriter-cursor');

        function type() {
            // 检查是否超时
            if (Date.now() - startTime > CONFIG.maxTypewriterTime) {
                element.textContent = text;
                finishTypewriter();
                return;
            }

            if (i < textLength) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, CONFIG.typewriterSpeed);
            } else {
                finishTypewriter();
            }
        }

        function finishTypewriter() {
            element.classList.remove('typewriter-cursor');
            if (typeof callback === 'function') {
                callback();
            }
        }

        type();
    }

    /**
     * 检查消息是否已被查看
     * @param {string} storageKey - localStorage 键
     * @returns {boolean} 是否已查看
     */
    function hasSeenMessage(storageKey) {
        try {
            return localStorage.getItem(STORAGE_PREFIX + storageKey) === 'true';
        } catch (e) {
            // localStorage 不可用时，返回 false（始终显示动画）
            console.warn('localStorage 不可用:', e);
            return false;
        }
    }

    /**
     * 标记消息为已查看
     * @param {string} storageKey - localStorage 键
     */
    function markMessageAsSeen(storageKey) {
        try {
            localStorage.setItem(STORAGE_PREFIX + storageKey, 'true');
        } catch (e) {
            console.warn('无法写入 localStorage:', e);
        }
    }

    /**
     * 调整容器高度
     * @param {HTMLElement} container - 容器元素
     */
    function adjustContainerHeight(container) {
        if (!container) return;

        const contentEl = container.querySelector('#welcome-content');
        if (!contentEl) return;

        // 等待内容渲染后调整高度
        requestAnimationFrame(() => {
            const contentHeight = contentEl.scrollHeight;
            const newHeight = Math.max(CONFIG.containerMinHeight, contentHeight + 20);
            container.style.minHeight = newHeight + 'px';
        });
    }

    /**
     * 显示欢迎语内容（标准模式）
     * @param {HTMLElement} container - 容器元素
     * @param {Object} data - 响应数据
     * @param {boolean} animate - 是否使用动画
     */
    function displayWelcomeMessage(container, data, animate) {
        const loadingEl = container.querySelector('#welcome-loading');
        const contentEl = container.querySelector('#welcome-content');
        const errorEl = container.querySelector('#welcome-error');
        const textEl = container.querySelector('#welcome-text');

        // 隐藏加载和错误状态
        if (loadingEl) loadingEl.classList.add('hidden');
        if (errorEl) errorEl.classList.add('hidden');

        // 显示内容容器
        if (contentEl) {
            contentEl.classList.remove('hidden');
            contentEl.classList.add('animate-in');
        }

        if (!textEl) return;

        const message = data.message_content || data.message || '';
        const storageKey = data.storage_key;

        if (animate && storageKey && !hasSeenMessage(storageKey)) {
            // 首次查看，使用打字机效果
            typewriter(textEl, message, () => {
                markMessageAsSeen(storageKey);
                adjustContainerHeight(container);
            });
        } else {
            // 已查看或无 storageKey，直接显示
            textEl.textContent = message;
            adjustContainerHeight(container);
        }
    }

    /**
     * 显示欢迎语内容（紧凑模式 - 用于顶部栏）
     * @param {HTMLElement} container - 容器元素
     * @param {Object} data - 响应数据
     */
    function displayCompactWelcomeMessage(container, data) {
        const loadingEl = container.querySelector('#compact-welcome-loading');
        const textEl = container.querySelector('#compact-welcome-text');
        const refreshBtn = container.querySelector('#compact-welcome-refresh');

        // 隐藏加载状态
        if (loadingEl) loadingEl.classList.add('hidden');

        // 显示内容
        if (textEl) {
            const message = data.message_content || data.message || '';
            textEl.textContent = message;
            textEl.classList.remove('hidden');
        }

        // 显示刷新按钮
        if (refreshBtn) {
            refreshBtn.classList.remove('hidden');
        }
    }

    /**
     * 显示错误状态
     * @param {HTMLElement} container - 容器元素
     */
    function showErrorState(container) {
        const loadingEl = container.querySelector('#welcome-loading');
        const errorEl = container.querySelector('#welcome-error');
        const contentEl = container.querySelector('#welcome-content');

        if (loadingEl) loadingEl.classList.add('hidden');
        if (contentEl) contentEl.classList.add('hidden');
        if (errorEl) errorEl.classList.remove('hidden');

        // 调整高度
        container.style.minHeight = CONFIG.containerMinHeight + 'px';
    }

    /**
     * 显示回退消息
     * @param {HTMLElement} container - 容器元素
     * @param {string} message - 回退消息
     */
    function showFallbackMessage(container, message) {
        const data = {
            message_content: message || '今天也是充满效率的一天，准备好处理新的批改任务了吗？',
            storage_key: null  // 回退消息不追踪查看状态
        };

        // 检测是否为紧凑模式
        if (container.id === 'compact-welcome-container') {
            displayCompactWelcomeMessage(container, data);
        } else {
            displayWelcomeMessage(container, data, false);
        }
    }

    /**
     * 加载欢迎语
     * @param {string} pageContext - 页面上下文
     * @param {string} mode - 显示模式 ('standard' 或 'compact')
     * @returns {Promise} 加载 Promise
     */
    function loadWelcomeMessage(pageContext, mode) {
        return new Promise((resolve, reject) => {
            // 根据 mode 选择容器
            const containerId = mode === 'compact' ? 'compact-welcome-container' : 'ai-welcome-container';
            const container = document.getElementById(containerId);

            if (!container) {
                reject(new Error('欢迎语容器不存在'));
                return;
            }

            // 从容器 data 属性获取 page_context（如果未指定）
            if (!pageContext) {
                pageContext = container.dataset.pageContext || detectPageContext();
            }

            const url = `/api/welcome/messages?page_context=${encodeURIComponent(pageContext)}`;

            // 设置超时
            const timeoutId = setTimeout(() => {
                showFallbackMessage(container);
                reject(new Error('请求超时'));
            }, CONFIG.requestTimeout);

            fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                clearTimeout(timeoutId);

                if (data.status === 'success' || data.status === 'cached' || data.status === 'generated' || data.status === 'fallback') {
                    if (mode === 'compact') {
                        displayCompactWelcomeMessage(container, data.data);
                    } else {
                        displayWelcomeMessage(container, data.data, true);
                    }
                    resolve(data);
                } else {
                    showFallbackMessage(container);
                    reject(new Error(data.message || '加载失败'));
                }
            })
            .catch(error => {
                clearTimeout(timeoutId);
                console.error('加载欢迎语失败:', error);
                showFallbackMessage(container);
                reject(error);
            });
        });
    }

    /**
     * 刷新欢迎语（强制重新生成）
     * @param {string} pageContext - 页面上下文
     * @param {string} mode - 显示模式 ('standard' 或 'compact')
     * @returns {Promise} 刷新 Promise
     */
    function refreshWelcomeMessage(pageContext, mode) {
        return new Promise((resolve, reject) => {
            const containerId = mode === 'compact' ? 'compact-welcome-container' : 'ai-welcome-container';
            const container = document.getElementById(containerId);
            if (!container) {
                reject(new Error('欢迎语容器不存在'));
                return;
            }

            if (!pageContext) {
                pageContext = container.dataset.pageContext || detectPageContext();
            }

            // 显示加载状态
            if (mode === 'compact') {
                const loadingEl = container.querySelector('#compact-welcome-loading');
                const textEl = container.querySelector('#compact-welcome-text');
                const refreshBtn = container.querySelector('#compact-welcome-refresh');

                if (loadingEl) loadingEl.classList.remove('hidden');
                if (textEl) textEl.classList.add('hidden');
                if (refreshBtn) refreshBtn.classList.add('hidden');
            } else {
                const loadingEl = container.querySelector('#welcome-loading');
                const contentEl = container.querySelector('#welcome-content');
                const errorEl = container.querySelector('#welcome-error');

                if (loadingEl) loadingEl.classList.remove('hidden');
                if (contentEl) contentEl.classList.add('hidden');
                if (errorEl) errorEl.classList.add('hidden');
            }

            const url = `/api/welcome/messages/refresh?page_context=${encodeURIComponent(pageContext)}`;

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (mode === 'compact') {
                        displayCompactWelcomeMessage(container, data.data);
                    } else {
                        displayWelcomeMessage(container, data.data, true);
                    }
                    resolve(data);
                } else {
                    showFallbackMessage(container);
                    reject(new Error(data.message || '刷新失败'));
                }
            })
            .catch(error => {
                console.error('刷新欢迎语失败:', error);
                showFallbackMessage(container);
                reject(error);
            });
        });
    }

    // 页面加载时自动初始化
    document.addEventListener('DOMContentLoaded', function() {
        // 初始化标准容器（dashboard）
        const standardContainer = document.getElementById('ai-welcome-container');
        if (standardContainer) {
            const pageContext = standardContainer.dataset.pageContext || detectPageContext();
            loadWelcomeMessage(pageContext, 'standard').catch(() => {
                // 错误已在 loadWelcomeMessage 中处理
            });
        }

        // 初始化紧凑容器（topbar）
        const compactContainer = document.getElementById('compact-welcome-container');
        if (compactContainer) {
            const pageContext = compactContainer.dataset.pageContext || detectPageContext();
            loadWelcomeMessage(pageContext, 'compact').catch(() => {
                // 错误已在 loadWelcomeMessage 中处理
            });
        }
    });

    // 导出函数到全局（供其他脚本调用）
    window.AIWelcome = {
        load: loadWelcomeMessage,
        refresh: refreshWelcomeMessage,
        loadCompact: function(pageContext) { return loadWelcomeMessage(pageContext, 'compact'); },
        refreshCompact: function(pageContext) { return refreshWelcomeMessage(pageContext, 'compact'); },
        showFallback: showFallbackMessage,
        typewriter: typewriter,
        detectContext: detectPageContext
    };

})();
