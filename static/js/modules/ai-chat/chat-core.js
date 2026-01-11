/**
 * static/js/modules/ai-chat/chat-core.js
 * 负责 AI 聊天的核心业务逻辑、状态管理和 API 通信
 */

export class ChatCore {
    constructor(contextId) {
        this.contextId = contextId; // 对应原 classOfferingId / bank_id
        this.currentSessionId = null;
        this.isDeepThinking = false;
        this.isLoading = false;

        // 状态标记：用于解析流式响应
        this._streamBuffer = '';
    }

    /**
     * 获取会话列表
     */
    async fetchSessions() {
        try {
            const response = await fetch(`/api/ai/chat/sessions/${this.contextId}`);
            if (!response.ok) throw new Error('获取会话列表失败');
            const data = await response.json();
            return data.sessions || [];
        } catch (error) {
            console.error('ChatCore: fetchSessions error', error);
            throw error;
        }
    }

    /**
     * 加载特定会话的历史记录
     */
    async loadSession(uuid) {
        if (!uuid) return null;
        this.currentSessionId = uuid;

        try {
            const response = await fetch(`/api/ai/chat/history/${uuid}`);
            if (!response.ok) throw new Error('加载历史失败');
            const data = await response.json();

            // 统一格式化历史消息
            return (data.messages || []).map(msg => this._normalizeHistoryMessage(msg));
        } catch (error) {
            console.error('ChatCore: loadSession error', error);
            throw error;
        }
    }

    /**
     * 创建新会话
     */
    async createSession() {
        try {
            const response = await fetch(`/api/ai/chat/session/new/${this.contextId}`, { method: 'POST' });
            if (!response.ok) throw new Error('创建新会话失败');
            const data = await response.json();
            this.currentSessionId = data.session.session_uuid;
            return data.session;
        } catch (error) {
            console.error('ChatCore: createSession error', error);
            throw error;
        }
    }

    /**
     * 发送消息并处理流式响应 (Generator 函数)
     * @param {string} message - 文本消息
     * @param {Array} files - 文件对象数组
     */
    async *sendMessageStream(message, files = []) {
        if (!this.currentSessionId) throw new Error('未选择会话');
        this.isLoading = true;
        this._streamBuffer = ''; // 重置缓冲区

        try {
            // 1. 文件转 Base64
            const base64Urls = await Promise.all(files.map(f => this._fileToBase64(f)));

            // 2. 构建请求
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    session_uuid: this.currentSessionId,
                    class_offering_id: this.contextId,
                    deep_thinking: this.isDeepThinking,
                    base64_urls: base64Urls
                })
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(errText || `服务器错误: ${response.status}`);
            }

            // 3. 处理流
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                this._streamBuffer += chunk;

                // 解析当前的思考内容和最终回复
                const parsed = this._parseThinkingContent(this._streamBuffer);
                yield parsed; // 将解析结果 yield 给 UI 层
            }

        } catch (error) {
            throw error;
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * 切换深度思考模式
     */
    toggleDeepThink() {
        this.isDeepThinking = !this.isDeepThinking;
        return this.isDeepThinking;
    }

    // ================= 私有辅助方法 =================

    /**
     * 解析混合了 <thinking> 标签的文本 (核心算法优化版)
     */
    _parseThinkingContent(text) {
        const startTag = '<thinking>';
        const endTag = '</thinking>';

        const startIndex = text.indexOf(startTag);
        const endIndex = text.indexOf(endTag);

        let thinking = '';
        let answer = '';
        let isThinking = false;

        if (startIndex !== -1) {
            isThinking = true; // 只要有开始标签，就算在思考模式（或思考刚结束）

            if (endIndex !== -1) {
                // 思考已结束
                thinking = text.substring(startIndex + startTag.length, endIndex).trim();
                answer = text.substring(endIndex + endTag.length); // 这里不 trim，保留流式打字感
            } else {
                // 正在思考中...
                thinking = text.substring(startIndex + startTag.length); // 不 trim
                answer = '';
            }
        } else {
            // 普通模式
            answer = text;
        }

        return { thinking, answer, isThinking };
    }

    /**
     * 规范化历史消息数据结构 (适配 V3/V4/V5 格式)
     */
    _normalizeHistoryMessage(msg) {
        let content = msg.message;
        let thinking = '';
        let answer = '';

        // 处理对象格式 (V4)
        if (typeof content === 'object' && content !== null) {
            if (content.answer) {
                answer = content.answer;
                thinking = content.thinking || '';
            } else if (Array.isArray(content)) {
                // 多模态数组
                const textPart = content.find(p => p.type === 'text');
                content = textPart ? textPart.text : '';
            }
        }

        // 处理字符串格式 (可能包含 JSON 字符串或 XML 标签)
        if (typeof content === 'string') {
            try {
                const parsed = JSON.parse(content);
                if (parsed.answer) {
                    answer = parsed.answer;
                    thinking = parsed.thinking || '';
                } else {
                    // 纯文本尝试解析 XML 标签
                    const res = this._parseThinkingContent(content);
                    answer = res.answer;
                    thinking = res.thinking;
                }
            } catch (e) {
                // 普通文本
                const res = this._parseThinkingContent(content);
                answer = res.answer;
                thinking = res.thinking;
            }
        }

        return {
            role: msg.role,
            answer: answer || content || '',
            thinking: thinking,
            attachments: [] // 历史附件暂留空，待后端支持
        };
    }

    _fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    }
}