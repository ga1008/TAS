/**
 * static/js/main.js
 * 前端入口文件：负责模块调度、全局工具注册与初始化
 */

// 1. 导入通用工具
import { showMessage, checkBootstrap } from './modules/utils.js';

// 2. 导入业务模块
import { initBankForm } from './modules/forms/bank-form.js';
import { initQuestionForm } from './modules/forms/question-form.js';
import { initFilterList } from './modules/lists/filter-list.js';
import { initImageParser } from './modules/ui/image-parser.js';
import { ChatCore } from './modules/ai-chat/chat-core.js';
import { ChatUI } from './modules/ai-chat/chat-ui.js';

// 注意：ai-welcome.js 是通过 script 标签直接引入的 IIFE，
// 它会自动挂载 window.AIWelcome，不需要在此处 import

document.addEventListener('DOMContentLoaded', () => {

    // --- 全局工具注册 ---

    // 1. 消息提示 (Toast)
    window.showMessage = showMessage;

    // 2. 触发 AI 欢迎语刷新
    // 供其他模块在操作成功后调用 (例如: 文件上传完成、创建班级完成)
    window.triggerWelcomeRefresh = function() {
        if (window.AIWelcome && typeof window.AIWelcome.triggerRefresh === 'function') {
            window.AIWelcome.triggerRefresh();
        } else {
            // 降级：如果 AIWelcome 未加载，手动触发事件
            window.dispatchEvent(new CustomEvent('tas:refresh_welcome'));
        }
    };

    // --- 基础库初始化 ---

    // 初始化 Bootstrap Tooltips (全局通用)
    if (checkBootstrap()) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // --- 业务模块路由 (根据页面 DOM ID 按需加载) ---

    // 1. 题库列表页 / 新建题库
    if (document.getElementById('createBankForm')) {
        initBankForm();
    }

    // 2. 题库详情页 (筛选与列表)
    if (document.getElementById('filterForm')) {
        initFilterList();
    }

    // 3. 添加/编辑题目页
    if (document.getElementById('questionForm')) {
        initQuestionForm();
        // 仅在添加题目页初始化图片解析器
        if (document.getElementById('imageParseModal')) {
            initImageParser();
        }
    }

    // --- AI 助手初始化 (侧边栏浮动助手) ---

    // aiChatContextId 由后端模板注入 (见 HTML block scripts)
    if (typeof window.aiChatContextId !== 'undefined') {
        try {
            console.log('Initializing AI Chat for Context:', window.aiChatContextId);
            const chatCore = new ChatCore(window.aiChatContextId);
            const chatUI = new ChatUI(chatCore);
            chatUI.init();
        } catch (err) {
            console.error('AI Chat initialization failed:', err);
            const fab = document.getElementById('ai-chat-fab');
            if (fab) fab.style.display = 'none';
        }
    } else {
        // 如果页面不需要 AI 浮窗 (未定义 contextId)，隐藏入口按钮
        const fab = document.getElementById('ai-chat-fab');
        if (fab) fab.style.display = 'none';
    }
});