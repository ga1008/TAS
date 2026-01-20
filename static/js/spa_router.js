/**
 * SPA Router - 无刷新页面导航
 *
 * 实现 SPA 式的导航体验，点击菜单时只更新内容区域，
 * 侧边栏保持不变，避免整页刷新闪烁。
 */

(function() {
    'use strict';

    // 配置
    const CONFIG = {
        contentSelector: '#spa-content',           // 主内容区选择器
        titleSelector: '#page-title-display',      // 页面标题选择器
        navLinkSelector: '.sidebar-content .nav-link', // 导航链接选择器
        excludePatterns: [                         // 排除的 URL 模式（这些链接会正常跳转）
            '/logout',
            '/auth/logout',
            '/admin/logout',
            '/static/',
            '/api/',
            'javascript:',
            '#'
        ],
        loadingClass: 'spa-loading',               // 加载中的 CSS 类
        fadeInClass: 'spa-fade-in',                // 淡入动画类
        transitionDuration: 200                     // 过渡动画时长 (ms)
    };

    // 状态
    let isNavigating = false;
    let abortController = null;

    /**
     * 初始化 SPA 路由器
     */
    function init() {
        // 绑定链接点击事件
        bindLinkClicks();

        // 监听浏览器前进/后退
        window.addEventListener('popstate', handlePopState);

        // 初始化当前页面的菜单状态
        updateActiveMenu(window.location.pathname);

        // 添加必要的 CSS
        injectStyles();

        console.log('[SPA Router] Initialized');
    }

    /**
     * 注入必要的 CSS 样式
     */
    function injectStyles() {
        if (document.getElementById('spa-router-styles')) return;

        const style = document.createElement('style');
        style.id = 'spa-router-styles';
        style.textContent = `
            /* SPA 过渡动画 */
            .spa-loading {
                opacity: 0.5;
                pointer-events: none;
                transition: opacity ${CONFIG.transitionDuration}ms ease;
            }

            .spa-fade-in {
                animation: spaFadeIn ${CONFIG.transitionDuration}ms ease forwards;
            }

            @keyframes spaFadeIn {
                from { opacity: 0; transform: translateY(8px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* 加载指示器 */
            .spa-loading-indicator {
                position: fixed;
                top: var(--topbar-height, 64px);
                left: var(--sidebar-width, 260px);
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #4f46e5, #7c3aed, #4f46e5);
                background-size: 200% 100%;
                animation: spaLoadingBar 1s linear infinite;
                z-index: 9999;
                opacity: 0;
                transition: opacity 0.2s;
            }

            .spa-loading-indicator.active {
                opacity: 1;
            }

            @keyframes spaLoadingBar {
                0% { background-position: 200% 0; }
                100% { background-position: -200% 0; }
            }

            /* 菜单高亮过渡 */
            .nav-link {
                transition: all 0.2s ease, background-color 0.15s ease, color 0.15s ease;
            }
        `;
        document.head.appendChild(style);

        // 创建加载指示器
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'spa-loading-indicator';
        loadingIndicator.id = 'spa-loading-indicator';
        document.body.appendChild(loadingIndicator);
    }

    /**
     * 绑定链接点击事件
     */
    function bindLinkClicks() {
        // 使用事件委托，绑定到 document
        document.addEventListener('click', function(e) {
            // 查找最近的 <a> 元素
            const link = e.target.closest('a');
            if (!link) return;

            // 检查是否应该拦截
            if (!shouldIntercept(link)) return;

            // 阻止默认行为
            e.preventDefault();

            // 执行 SPA 导航
            navigateTo(link.href);
        });
    }

    /**
     * 判断链接是否应该被 SPA 拦截
     */
    function shouldIntercept(link) {
        const href = link.getAttribute('href');

        // 基本检查
        if (!href) return false;
        if (link.target === '_blank') return false;
        if (link.hasAttribute('download')) return false;
        if (link.hasAttribute('data-spa-ignore')) return false;

        // 检查是否是外部链接
        if (href.startsWith('http') && !href.startsWith(window.location.origin)) {
            return false;
        }

        // 检查排除模式
        for (const pattern of CONFIG.excludePatterns) {
            if (href.includes(pattern)) return false;
        }

        // 检查是否是 toggle-submenu（子菜单展开按钮）
        if (link.classList.contains('toggle-submenu')) return false;

        return true;
    }

    /**
     * 执行 SPA 导航
     */
    async function navigateTo(url, pushState = true) {
        // 防止重复导航
        if (isNavigating) {
            if (abortController) abortController.abort();
        }

        // 如果是当前页面，不导航
        if (url === window.location.href) return;

        isNavigating = true;
        abortController = new AbortController();

        const contentEl = document.querySelector(CONFIG.contentSelector);
        const loadingIndicator = document.getElementById('spa-loading-indicator');

        try {
            // 显示加载状态
            if (contentEl) contentEl.classList.add(CONFIG.loadingClass);
            if (loadingIndicator) loadingIndicator.classList.add('active');

            // 获取页面内容
            const response = await fetch(url, {
                signal: abortController.signal,
                headers: {
                    'X-Requested-With': 'SPA',
                    'Accept': 'text/html'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const html = await response.text();

            // 解析 HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // 提取新内容
            const newContent = doc.querySelector(CONFIG.contentSelector);
            const newTitle = doc.querySelector('title')?.textContent || '';
            const newHeaderTitle = doc.querySelector(CONFIG.titleSelector)?.textContent || '';

            if (!newContent) {
                // 如果找不到内容区域，回退到传统导航
                console.warn('[SPA Router] Content not found, falling back to full navigation');
                window.location.href = url;
                return;
            }

            // 更新内容
            if (contentEl) {
                // 淡出效果
                contentEl.classList.add(CONFIG.loadingClass);

                await sleep(CONFIG.transitionDuration / 2);

                // 替换内容
                contentEl.innerHTML = newContent.innerHTML;

                // 淡入效果
                contentEl.classList.remove(CONFIG.loadingClass);
                contentEl.classList.add(CONFIG.fadeInClass);

                // 移除动画类
                setTimeout(() => {
                    contentEl.classList.remove(CONFIG.fadeInClass);
                }, CONFIG.transitionDuration);
            }

            // 更新标题
            document.title = newTitle;
            const titleEl = document.querySelector(CONFIG.titleSelector);
            if (titleEl && newHeaderTitle) {
                titleEl.textContent = newHeaderTitle;
            } else if (titleEl && newTitle) {
                titleEl.textContent = newTitle.split('-')[0].trim();
            }

            // 更新浏览器历史
            if (pushState) {
                history.pushState({ url: url }, '', url);
            }

            // 更新菜单状态
            const urlPath = new URL(url, window.location.origin).pathname;
            updateActiveMenu(urlPath);

            // 执行新页面中的脚本
            executeScripts(contentEl);

            // 滚动到顶部
            const mainEl = document.querySelector('.app-main');
            if (mainEl) mainEl.scrollTop = 0;

            // 触发自定义事件
            window.dispatchEvent(new CustomEvent('spa:navigated', {
                detail: { url, title: newTitle }
            }));

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('[SPA Router] Navigation aborted');
                return;
            }

            console.error('[SPA Router] Navigation failed:', error);
            // 导航失败时回退到传统导航
            window.location.href = url;

        } finally {
            isNavigating = false;
            if (loadingIndicator) loadingIndicator.classList.remove('active');
            if (contentEl) contentEl.classList.remove(CONFIG.loadingClass);
        }
    }

    /**
     * 处理浏览器前进/后退
     */
    function handlePopState(e) {
        const url = e.state?.url || window.location.href;
        navigateTo(url, false);
    }

    /**
     * 更新菜单激活状态
     */
    function updateActiveMenu(currentPath) {
        // 移除所有激活状态
        document.querySelectorAll(CONFIG.navLinkSelector).forEach(link => {
            link.classList.remove('active');
        });

        // 收起所有子菜单（可选，如果希望保持展开状态可以注释掉）
        // document.querySelectorAll('.submenu').hide();
        // document.querySelectorAll('.toggle-submenu').removeClass('expanded');

        let matchedLink = null;
        let matchedLength = 0;

        // 查找最匹配的链接
        document.querySelectorAll(CONFIG.navLinkSelector).forEach(link => {
            const href = link.getAttribute('href');
            if (!href || href === '#') return;

            // 解析 href 以获取路径
            let linkPath;
            try {
                linkPath = new URL(href, window.location.origin).pathname;
            } catch {
                linkPath = href;
            }

            // 精确匹配或前缀匹配
            if (currentPath === linkPath ||
                (linkPath !== '/' && currentPath.startsWith(linkPath))) {
                // 选择最长匹配
                if (linkPath.length > matchedLength) {
                    matchedLength = linkPath.length;
                    matchedLink = link;
                }
            }
        });

        // 特殊处理首页
        if (!matchedLink && currentPath === '/') {
            matchedLink = document.querySelector('#menu-home');
        }

        // 激活匹配的链接
        if (matchedLink) {
            matchedLink.classList.add('active');

            // 如果在子菜单中，展开父菜单
            const submenu = matchedLink.closest('.submenu');
            if (submenu) {
                submenu.style.display = 'block';
                const parentToggle = submenu.previousElementSibling;
                if (parentToggle && parentToggle.classList.contains('toggle-submenu')) {
                    parentToggle.classList.add('expanded');
                    parentToggle.classList.add('active');
                }
            }
        }
    }

    /**
     * 执行内容区域中的脚本
     */
    function executeScripts(container) {
        if (!container) return;

        const scripts = container.querySelectorAll('script');
        const scriptPromises = [];

        scripts.forEach(oldScript => {
            // 创建新脚本元素
            const newScript = document.createElement('script');

            // 复制属性
            Array.from(oldScript.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });

            if (oldScript.src) {
                // 外部脚本：检查是否已加载
                const existingScript = document.querySelector(`script[src="${oldScript.src}"]`);

                // 特殊处理 Tailwind CDN - 已加载则跳过
                if (oldScript.src.includes('tailwindcss') && existingScript) {
                    oldScript.remove();
                    return;
                }

                // 其他已加载的外部脚本也跳过
                if (existingScript && !oldScript.hasAttribute('data-spa-reload')) {
                    oldScript.remove();
                    return;
                }

                // 加载新的外部脚本
                const loadPromise = new Promise((resolve, reject) => {
                    newScript.onload = resolve;
                    newScript.onerror = reject;
                });
                scriptPromises.push(loadPromise);
            } else {
                // 内联脚本：直接复制内容
                newScript.textContent = oldScript.textContent;
            }

            // 替换旧脚本
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });

        // 等待所有外部脚本加载完成后，触发 Tailwind 重新处理（如果存在）
        Promise.all(scriptPromises).then(() => {
            // 检查是否有 Tailwind 配置需要应用
            if (window.tailwind && typeof window.tailwind.config !== 'undefined') {
                // Tailwind JIT 会自动处理新内容
                console.log('[SPA Router] Tailwind config detected');
            }
        }).catch(err => {
            console.warn('[SPA Router] Script loading error:', err);
        });
    }

    /**
     * 辅助函数：延迟
     */
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * 公开 API
     */
    window.SPARouter = {
        init: init,
        navigateTo: navigateTo,
        updateActiveMenu: updateActiveMenu,

        // 配置方法
        setConfig: function(key, value) {
            if (CONFIG.hasOwnProperty(key)) {
                CONFIG[key] = value;
            }
        }
    };

    // DOM 加载完成后自动初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
