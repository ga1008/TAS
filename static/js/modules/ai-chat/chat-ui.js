/**
 * static/js/modules/ai-chat/chat-ui.js
 * 负责 AI 聊天的界面渲染、交互事件和窗口管理
 */

// 假设 utils.js 中定义了 showMessage，如果未定义则使用 fallback
const toast = (msg, type) => {
    if (window.showMessage) window.showMessage(msg, type);
    else alert(msg);
};

export class ChatUI {
    constructor(chatCore) {
        this.core = chatCore;

        // UI 状态
        this.pendingFiles = [];
        this.resizeState = { isResizing: false };

        // DOM 缓存
        this.els = {
            modal: document.getElementById('ai-chat-modal'),
            container: document.querySelector('.ai-chat-container'),
            fab: document.getElementById('ai-chat-fab'),
            historyList: document.getElementById('ai-chat-history-list'),
            messagesBox: document.getElementById('ai-chat-messages-box'),
            textarea: document.getElementById('ai-chat-textarea'),
            sendBtn: document.getElementById('ai-chat-btn-send'),
            attachBtn: document.getElementById('ai-chat-btn-attach'),
            fileInput: document.getElementById('ai-chat-file-input'),
            previewsBox: document.getElementById('ai-chat-previews'),
            deepThinkBtn: document.getElementById('ai-deep-think-btn'),
            currentTitle: document.getElementById('ai-chat-current-title'),
            closeBtn: document.getElementById('ai-chat-btn-close'),
            fullscreenBtn: document.getElementById('ai-chat-btn-fullscreen'),
            newSessionBtn: document.getElementById('ai-chat-btn-new')
        };

        // 图标资源
        this.icons = {
            maximize: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg>`,
            minimize: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/></svg>`,
            copy: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`
        };
    }

    init() {
        if (!this.els.modal) return; // 页面可能没有 AI 组件
        this.bindEvents();
        this.bindResizeEvents();
    }

    // ================= 事件绑定 =================

    bindEvents() {
        // 窗口开关
        this.els.fab.addEventListener('click', () => this.open());
        this.els.closeBtn.addEventListener('click', () => this.close());
        this.els.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());

        // 会话管理
        this.els.newSessionBtn.addEventListener('click', () => this.handleNewSession());
        this.els.historyList.addEventListener('click', (e) => {
            const item = e.target.closest('.history-item');
            if (item && item.dataset.uuid && item.dataset.uuid !== this.core.currentSessionId) {
                this.loadSession(item.dataset.uuid);
            }
        });

        // 消息发送
        this.els.sendBtn.addEventListener('click', () => this.handleSend());
        this.els.textarea.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!this.els.sendBtn.disabled) this.handleSend();
            }
        });
        this.els.textarea.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateSendBtnState();
        });
        this.els.textarea.addEventListener('paste', (e) => this.handlePaste(e));

        // 附件与工具
        this.els.attachBtn.addEventListener('click', () => this.els.fileInput.click());
        this.els.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.els.deepThinkBtn.addEventListener('click', () => {
            const isActive = this.core.toggleDeepThink();
            this.els.deepThinkBtn.classList.toggle('active', isActive);
            toast(isActive ? '已开启深度思考' : '已关闭深度思考', 'success');
        });
    }

    // ================= 业务逻辑处理 =================

    async open() {
        this.els.modal.style.display = 'block';
        this.els.fab.style.display = 'none';

        // --- 新增: 移动端/小屏幕自适应布局 ---
        this.adaptResponsiveLayout();

        this.els.textarea.focus();


        if (!this.core.currentSessionId) {
            // 初次打开，加载列表并加载最新的一个会话
            await this.refreshHistoryList(true);
        } else {
            // 仅刷新列表
            this.refreshHistoryList(false);
        }
    }

    close() {
        this.els.modal.style.display = 'none';
        this.els.fab.style.display = 'block';
    }

    async handleNewSession() {
        try {
            await this.core.createSession();
            this.els.messagesBox.innerHTML = '';
            this.renderSystemMessage('已开始新对话。');
            await this.refreshHistoryList();
        } catch (e) {
            toast(e.message, 'error');
        }
    }

    async loadSession(uuid) {
        // UI 切换选中状态
        this.els.historyList.querySelectorAll('.history-item').forEach(el => {
            el.classList.toggle('active', el.dataset.uuid === uuid);
        });

        // 更新标题
        const titleEl = this.els.historyList.querySelector(`.history-item[data-uuid="${uuid}"] .title`);
        this.els.currentTitle.textContent = titleEl ? titleEl.textContent : 'AI 助手';

        this.els.messagesBox.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-primary" role="status"></div></div>';

        try {
            const messages = await this.core.loadSession(uuid);
            this.els.messagesBox.innerHTML = '';
            if (messages.length === 0) {
                this.renderSystemMessage('新对话，请提问。');
            } else {
                messages.forEach(msg => this.renderMessage(msg.role, msg.answer, msg.thinking));
            }
            this.scrollToBottom();
        } catch (e) {
            this.els.messagesBox.innerHTML = `<div class="text-danger p-3">加载失败: ${e.message}</div>`;
        }
    }

    async handleSend() {
        const text = this.els.textarea.value.trim();
        if (!text && this.pendingFiles.length === 0) return;
        if (this.core.isLoading) return;

        // 1. 渲染用户消息
        const userFiles = [...this.pendingFiles];
        this.renderMessage('user', text, null, userFiles);

        // 清理输入
        this.els.textarea.value = '';
        this.clearFiles();
        this.autoResizeTextarea();

        // 2. 创建助手消息占位
        const { bubble, updateContent } = this.createAssistantPlaceholder();

        try {
            // 3. 消费流式数据
            let fullAnswer = '';
            let fullThinking = '';

            // 使用 for await...of 循环处理 Generator
            for await (const chunk of this.core.sendMessageStream(text, userFiles)) {
                fullAnswer = chunk.answer;
                fullThinking = chunk.thinking;

                // 实时渲染
                this.renderAssistantContent(bubble, fullAnswer, fullThinking, true);
                this.scrollToBottom();
            }

            // 4. 完成后重新渲染（添加复制按钮等）
            this.renderAssistantContent(bubble, fullAnswer, fullThinking, false);

            // 刷新历史列表（因为标题可能更新了）
            this.refreshHistoryList();

        } catch (e) {
            console.error(e);
            bubble.innerHTML += `<div class="text-danger mt-2">请求出错: ${e.message}</div>`;
        }
    }

    // ================= 渲染辅助 =================

    // [新增] 自适应布局方法
    adaptResponsiveLayout() {
        const winW = window.innerWidth;
        const container = this.els.container;

        // 设定一个阈值，比如 450px (常见手机宽度)
        // 或者如果当前容器宽度默认是 400px，只要屏幕小于 420px 就应该调整
        if (winW < 450) {
            const newWidth = winW - 20; // 屏幕宽度减去左右各 10px 边距
            const newLeft = 10; // 左边距 10px

            // 强制覆盖样式
            container.style.width = `${newWidth}px`;
            container.style.height = '70vh'; // 移动端高度给百分比，避免键盘遮挡太严重

            // 重置定位：清除 right，使用 left 定位
            container.style.right = 'auto';
            container.style.left = `${newLeft}px`;
            container.style.bottom = '10px';
            container.style.top = 'auto';
        }
    }

    /**
     * 渲染单条消息 (用于历史记录加载或用户发送)
     */
    renderMessage(role, content, thinking = null, files = []) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `ai-chat-message ${role}`;

        const bubble = document.createElement('div');
        bubble.className = 'bubble';

        // [修复关键点]：必须先将 bubble 加入父容器，确保 bubble.parentNode 存在
        // 否则后续 renderAssistantContent 调用 addMarkdownCopyBtn 时会因找不到 parentNode 而报错
        msgDiv.appendChild(bubble);

        // 1. 图片
        files.forEach(file => {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.className = 'msg-image';
            bubble.appendChild(img);
        });

        // 2. 文本内容
        if (role === 'user') {
            const p = document.createElement('p');
            p.textContent = content;
            bubble.appendChild(p);
        } else {
            // 助手消息：包含思考过程渲染
            // 此时 bubble.parentNode (即 msgDiv) 已存在，可以安全操作
            this.renderAssistantContent(bubble, content, thinking, false);
        }

        this.els.messagesBox.appendChild(msgDiv);
        this.scrollToBottom();
    }

    /**
     * 渲染助手的复合内容 (思考 + 答案)
     * @param {HTMLElement} bubble
     * @param {string} answerText
     * @param {string} thinkingText
     * @param {boolean} isStreaming
     */
    renderAssistantContent(bubble, answerText, thinkingText, isStreaming) {
        let html = '';

        // A. 思考过程
        if (thinkingText) {
            // 获取当前的用户折叠状态（如果之前已经渲染过），防止流式更新时重置用户的操作
            // 逻辑：如果元素存在且是 block，说明用户展开了；否则默认认为折叠
            const existingContent = bubble.querySelector('.thinking-content');
            const wasVisible = existingContent && existingContent.style.display === 'block';

            // 默认折叠 (none)，除非用户之前手动展开了 (block)
            const displayStyle = wasVisible ? 'block' : 'none';
            // 0deg 代表展开(向下)，180deg 代表折叠(向上/向右)
            const arrowTransform = wasVisible ? 'rotate(0deg)' : 'rotate(180deg)';

            // 加载动画：只在流式传输中显示
            // 当 isStreaming 为 false (消息结束) 时，loadingIcon 变为空字符串，即自动消失
            const loadingIcon = isStreaming
                ? '<span class="thinking-spinner" title="正在思考..."></span>'
                : '';

            html += `
                <div class="thinking-container">
                    <div class="thinking-header" onclick="
                        const content = this.nextElementSibling;
                        const isHidden = content.style.display === 'none';
                        content.style.display = isHidden ? 'block' : 'none';
                        /* 修正箭头旋转逻辑：展开时转回 0deg，折叠时转到 180deg */
                        this.querySelector('svg').style.transform = isHidden ? 'rotate(0deg)' : 'rotate(180deg)';
                    ">
                        <button class="thinking-toggle">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="transform: ${arrowTransform}; transition: transform 0.2s;">
                                <path d="m6 9 6 6 6-6"/>
                            </svg>
                            <span>深度思考过程</span>
                        </button>
                        ${loadingIcon}
                    </div>
                    <div class="thinking-content" style="display: ${displayStyle}">
                        <div class="thinking-text">${thinkingText}</div>
                    </div>
                </div>`;
        }

        // B. 正文答案
        const parsedAnswer = typeof marked !== 'undefined' ? marked.parse(answerText) : `<p>${answerText}</p>`;
        html += `<div class="final-answer">${parsedAnswer}</div>`;

        // C. 光标 (打字机效果)
        if (isStreaming) {
            html += '<span class="streaming-cursor"></span>';
        }

        bubble.innerHTML = html;

        // D. 非流式状态下，添加工具栏（复制按钮）
        if (!isStreaming) {
            this.addCodeCopyButtons(bubble);
            this.addMarkdownCopyBtn(bubble, answerText);
        }
    }

    createAssistantPlaceholder() {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'ai-chat-message assistant';
        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.innerHTML = '<span class="streaming-cursor"></span>';
        msgDiv.appendChild(bubble);
        this.els.messagesBox.appendChild(msgDiv);
        return { bubble };
    }

    renderSystemMessage(text) {
        const div = document.createElement('div');
        div.className = 'ai-chat-message system';
        div.innerHTML = `<div class="bubble">${text}</div>`;
        this.els.messagesBox.appendChild(div);
    }

    async refreshHistoryList(shouldLoadFirst = false) {
        try {
            const sessions = await this.core.fetchSessions();
            this.els.historyList.innerHTML = '';

            if (sessions.length === 0) {
                this.els.historyList.innerHTML = `<div class="history-item-empty p-2 text-muted small">尚无历史对话</div>`;
                // 如果没有会话且需要加载，则自动创建
                if (shouldLoadFirst) await this.handleNewSession();
                return;
            }

            sessions.forEach(s => {
                const item = document.createElement('div');
                item.className = 'history-item';
                if (s.session_uuid === this.core.currentSessionId) item.classList.add('active');
                item.dataset.uuid = s.session_uuid;
                item.innerHTML = `
                    <span class="title">${s.title || '新对话'}</span>
                    <span class="subtitle">${s.updated_at || ''}</span>
                `;
                this.els.historyList.appendChild(item);
            });

            if (shouldLoadFirst && sessions.length > 0) {
                this.loadSession(sessions[0].session_uuid);
            }
        } catch (e) {
            this.els.historyList.innerHTML = `<li class="history-item-error">加载失败</li>`;
        }
    }

    // ================= 文件与输入处理 =================

    handlePaste(e) {
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        let hasImage = false;
        for (const item of items) {
            if (item.kind === 'file' && item.type.startsWith('image/')) {
                const file = item.getAsFile();
                if (this.pendingFiles.length < 5) {
                    this.pendingFiles.push(file);
                    hasImage = true;
                } else {
                    toast('最多上传5张图片', 'error');
                }
            }
        }
        if (hasImage) {
            e.preventDefault();
            this.renderPreviews();
            this.updateSendBtnState();
        }
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        const validFiles = files.filter(f => f.type.startsWith('image/'));

        if (this.pendingFiles.length + validFiles.length > 5) {
            toast('一次最多上传5张图片', 'error');
            return;
        }
        this.pendingFiles.push(...validFiles);
        this.renderPreviews();
        this.updateSendBtnState();
        this.els.fileInput.value = '';
    }

    renderPreviews() {
        this.els.previewsBox.innerHTML = '';
        this.pendingFiles.forEach((file, idx) => {
            const item = document.createElement('div');
            item.className = 'preview-item';
            item.innerHTML = `
                <img src="${URL.createObjectURL(file)}">
                <button class="remove-preview">&times;</button>
            `;
            item.querySelector('button').onclick = () => {
                this.pendingFiles.splice(idx, 1);
                this.renderPreviews();
                this.updateSendBtnState();
            };
            this.els.previewsBox.appendChild(item);
        });
    }

    clearFiles() {
        this.pendingFiles = [];
        this.renderPreviews();
    }

    autoResizeTextarea() {
        this.els.textarea.style.height = 'auto';
        this.els.textarea.style.height = (this.els.textarea.scrollHeight) + 'px';
    }

    updateSendBtnState() {
        const hasText = this.els.textarea.value.trim().length > 0;
        const hasFiles = this.pendingFiles.length > 0;
        this.els.sendBtn.disabled = (!hasText && !hasFiles) || this.core.isLoading;
    }

    scrollToBottom() {
        this.els.messagesBox.scrollTop = this.els.messagesBox.scrollHeight;
    }

    // ================= 窗口管理 (Resize & Fullscreen) =================

    toggleFullscreen() {
        const isFullscreen = this.els.container.classList.toggle('fullscreen');

        // 处理图标
        this.els.fullscreenBtn.innerHTML = isFullscreen ? this.icons.minimize : this.icons.maximize;
        this.els.fullscreenBtn.title = isFullscreen ? '退出全屏' : '全屏';

        // 处理布局
        const navbar = document.querySelector('.navbar.sticky-top');
        const navHeight = navbar ? navbar.getBoundingClientRect().height : 0;
        const historyPanel = document.getElementById('ai-chat-history-panel');

        if (isFullscreen) {
            if (historyPanel) historyPanel.style.display = 'flex';
            this.els.container.style.top = `${navHeight}px`;
            this.els.container.style.height = `calc(100% - ${navHeight}px)`;
            // 清除可能由 resize 导致的内联样式
            ['width', 'bottom', 'left', 'right'].forEach(p => this.els.container.style[p] = '');
        } else {
            if (historyPanel) historyPanel.style.display = ''; // 恢复 CSS 控制
            // 恢复默认大小
            this.els.container.style.width = '400px';
            this.els.container.style.height = '600px';
            this.els.container.style.top = '';
            this.els.container.style.bottom = '30px';
            this.els.container.style.right = '30px';
        }
    }

    bindResizeEvents() {
        const resizers = this.els.container.querySelectorAll('.resizer');
        resizers.forEach(r => {
            r.addEventListener('mousedown', (e) => {
                if (this.els.container.classList.contains('fullscreen')) return;
                e.preventDefault();
                this.resizeState = {
                    isResizing: true,
                    direction: this._getResizeDirection(r),
                    startX: e.clientX,
                    startY: e.clientY,
                    startRect: this.els.container.getBoundingClientRect()
                };

                // 临时设置定位方式以支持左/上方向的拖拽
                this.els.container.style.right = 'auto';
                this.els.container.style.bottom = 'auto';
                this.els.container.style.left = `${this.resizeState.startRect.left}px`;
                this.els.container.style.top = `${this.resizeState.startRect.top}px`;

                const moveHandler = this._handleMouseMove.bind(this);
                const upHandler = () => {
                    this.resizeState.isResizing = false;
                    document.removeEventListener('mousemove', moveHandler);
                    document.removeEventListener('mouseup', upHandler);
                };
                document.addEventListener('mousemove', moveHandler);
                document.addEventListener('mouseup', upHandler);
            });
        });
    }

    _getResizeDirection(el) {
        const cl = el.classList;
        if (cl.contains('resizer-top-left')) return 'tl';
        if (cl.contains('resizer-top-right')) return 'tr';
        if (cl.contains('resizer-bottom-left')) return 'bl';
        if (cl.contains('resizer-bottom-right')) return 'br';
        if (cl.contains('resizer-top')) return 't';
        if (cl.contains('resizer-bottom')) return 'b';
        if (cl.contains('resizer-left')) return 'l';
        return 'r';
    }

    _handleMouseMove(e) {
        if (!this.resizeState.isResizing) return;
        const s = this.resizeState;
        const dx = e.clientX - s.startX;
        const dy = e.clientY - s.startY;
        const rect = s.startRect;

        let newW = rect.width;
        let newH = rect.height;
        let newL = rect.left;
        let newT = rect.top;

        // 简化后的逻辑：根据方向增减宽高和位移
        if (s.direction.includes('r')) newW = rect.width + dx;
        if (s.direction.includes('l')) { newW = rect.width - dx; newL = rect.left + dx; }
        if (s.direction.includes('b')) newH = rect.height + dy;
        if (s.direction.includes('t')) { newH = rect.height - dy; newT = rect.top + dy; }

        // 限制最小值
        if (newW >= 350) {
            this.els.container.style.width = `${newW}px`;
            if (s.direction.includes('l')) this.els.container.style.left = `${newL}px`;
        }
        if (newH >= 400) {
            this.els.container.style.height = `${newH}px`;
            if (s.direction.includes('t')) this.els.container.style.top = `${newT}px`;
        }
    }

    // ================= 工具函数：复制 =================

    addCodeCopyButtons(bubble) {
        bubble.querySelectorAll('pre').forEach(pre => {
            if (pre.querySelector('.copy-code-btn')) return;
            const btn = document.createElement('button');
            btn.className = 'copy-code-btn';
            btn.textContent = '复制';
            btn.onclick = (e) => {
                e.stopPropagation();
                const code = pre.querySelector('code')?.textContent || pre.textContent;
                this._copyToClipboard(code, btn);
            };
            pre.appendChild(btn);
        });
    }

    addMarkdownCopyBtn(bubble, text) {
        if (bubble.parentNode.querySelector('.message-actions')) return;
        const actions = document.createElement('div');
        actions.className = 'message-actions';
        const btn = document.createElement('button');
        btn.className = 'copy-btn';
        btn.innerHTML = `${this.icons.copy} 复制 Markdown`;
        btn.onclick = () => this._copyToClipboard(text, btn, true);
        actions.appendChild(btn);
        bubble.parentNode.appendChild(actions);
    }

    _copyToClipboard(text, btnElement, isMarkdown = false) {
        navigator.clipboard.writeText(text).then(() => {
            const original = btnElement.innerHTML;
            btnElement.innerHTML = isMarkdown ? '已复制' : '已复制!';
            btnElement.classList.add('copied');
            setTimeout(() => {
                btnElement.innerHTML = original;
                btnElement.classList.remove('copied');
            }, 2000);
        }).catch(() => toast('复制失败', 'error'));
    }
}