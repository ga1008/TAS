/**
 * static/js/modules/ui/image-parser.js
 * 处理图片上传、预览、API 调用及结果填充
 * 使用 Tailwind CSS 自定义弹窗替代 Bootstrap Modal
 */

import { fillQuestionFormData } from '../forms/question-form.js';

export function initImageParser() {
    const els = {
        modal: document.getElementById('imageParseModal'),
        openBtn: document.getElementById('openImageParseModal'),
        uploadInput: document.getElementById('imageUploadInput'),
        dropZone: document.getElementById('imageDropZone'),
        previewList: document.getElementById('imagePreviewList'),
        status: document.getElementById('imageParseStatus'),
        parseBtn: document.getElementById('parseImagesBtn')
    };

    // 校验必要元素是否存在
    if (!Object.values(els).every(el => el)) return;

    let pendingFiles = []; // 当前待解析的文件列表

    // ================== 自定义弹窗控制 ==================

    function showModal() {
        els.modal.classList.remove('hidden');
        els.modal.classList.add('flex');
        document.body.style.overflow = 'hidden';
        // 触发动画
        setTimeout(() => {
            const panel = els.modal.querySelector('.modal-panel');
            if (panel) {
                panel.classList.remove('scale-95', 'opacity-0');
                panel.classList.add('scale-100', 'opacity-100');
            }
        }, 10);
    }

    function hideModal() {
        const panel = els.modal.querySelector('.modal-panel');
        if (panel) {
            panel.classList.remove('scale-100', 'opacity-100');
            panel.classList.add('scale-95', 'opacity-0');
        }
        setTimeout(() => {
            els.modal.classList.add('hidden');
            els.modal.classList.remove('flex');
            document.body.style.overflow = '';
            reset();
        }, 200);
    }

    // ================== 事件绑定 ==================

    els.openBtn.addEventListener('click', () => {
        reset();
        showModal();
    });

    // 点击遮罩关闭
    els.modal.addEventListener('click', (e) => {
        if (e.target === els.modal || e.target.classList.contains('modal-backdrop')) {
            hideModal();
        }
    });

    // 关闭按钮
    const closeBtn = els.modal.querySelector('.modal-close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', hideModal);
    }

    // ESC 键关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !els.modal.classList.contains('hidden')) {
            hideModal();
        }
    });

    // 点击上传区
    els.dropZone.addEventListener('click', () => els.uploadInput.click());

    // 文件选择
    els.uploadInput.addEventListener('change', (e) => addFiles(e.target.files));

    // 拖拽支持
    els.dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        els.dropZone.classList.add('dragover');
    });
    els.dropZone.addEventListener('dragleave', () => els.dropZone.classList.remove('dragover'));
    els.dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        els.dropZone.classList.remove('dragover');
        addFiles(e.dataTransfer.files);
    });

    // 粘贴支持 (监听全局粘贴，但仅在弹窗显示时生效)
    document.addEventListener('paste', (e) => {
        if (els.modal.classList.contains('hidden')) return;
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        const files = [];
        for (let item of items) {
            if (item.kind === 'file' && item.type.startsWith('image/')) {
                files.push(item.getAsFile());
            }
        }
        if (files.length > 0) {
            e.preventDefault();
            addFiles(files);
        }
    });

    // 删除图片
    els.previewList.addEventListener('click', (e) => {
        const btn = e.target.closest('.image-preview-remove');
        if (btn) {
            const idx = parseInt(btn.dataset.index);
            pendingFiles.splice(idx, 1);
            renderPreviews();
        }
    });

    // 执行解析
    els.parseBtn.addEventListener('click', handleParse);


    // ================== 逻辑函数 ==================

    function reset() {
        pendingFiles = [];
        els.uploadInput.value = '';
        renderPreviews();
        updateStatus('', 'muted');
        setLoading(false);
    }

    function addFiles(fileList) {
        if (!fileList || fileList.length === 0) return;
        const validFiles = Array.from(fileList).filter(f => f.type.startsWith('image/'));

        if (validFiles.length === 0) {
            updateStatus('请选择有效的图片文件', 'error');
            return;
        }

        pendingFiles.push(...validFiles);
        renderPreviews();
        updateStatus('', 'muted');
    }

    function renderPreviews() {
        els.previewList.innerHTML = '';
        if (pendingFiles.length === 0) {
            els.previewList.innerHTML = '<li class="p-3 text-slate-400 text-center text-sm">尚未添加图片</li>';
            return;
        }

        pendingFiles.forEach((file, index) => {
            const li = document.createElement('li');
            li.className = 'flex justify-between items-center p-3 border-b border-slate-100 last:border-0';
            const size = (file.size / 1024).toFixed(1);

            li.innerHTML = `
                <span class="truncate text-sm text-slate-700" style="max-width: 80%;">${file.name} <small class="text-slate-400">(${size} KB)</small></span>
                <button type="button" class="image-preview-remove text-rose-500 hover:text-rose-700 p-1 transition-colors" data-index="${index}" title="删除">
                    <i class="fas fa-times"></i>
                </button>
            `;
            els.previewList.appendChild(li);
        });
    }

    function updateStatus(msg, type = 'muted') {
        els.status.textContent = msg;
        els.status.className = 'text-sm mt-3';
        if (type === 'error') els.status.classList.add('text-rose-500');
        else if (type === 'success') els.status.classList.add('text-emerald-500');
        else els.status.classList.add('text-slate-400');
    }

    function setLoading(isLoading) {
        els.parseBtn.disabled = isLoading;
        const spinner = els.parseBtn.querySelector('.spinner-icon');
        const text = els.parseBtn.querySelector('.parse-btn-text');
        if (spinner) spinner.classList.toggle('hidden', !isLoading);
        if (text) text.textContent = isLoading ? '解析中，大约需要5分钟...' : '解析';
        if (isLoading) {
            els.parseBtn.classList.add('opacity-75', 'cursor-not-allowed');
        } else {
            els.parseBtn.classList.remove('opacity-75', 'cursor-not-allowed');
        }
    }

    async function handleParse() {
        if (pendingFiles.length === 0) {
            updateStatus('请先添加图片', 'error');
            return;
        }

        setLoading(true);
        updateStatus('正在智能识别题目内容...', 'muted');

        try {
            // 1. 转 Base64
            const base64List = await Promise.all(pendingFiles.map(fileToDataURL));

            // 2. API 调用
            const response = await fetch('/ai/parse-question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ images: base64List })
            });

            const result = await response.json();

            if (!response.ok || result.status !== 'success') {
                throw new Error(result.message || '解析服务响应异常');
            }

            // 3. 填充表单 (调用外部模块)
            fillQuestionFormData(result.data);

            // 4. 成功反馈
            updateStatus('解析成功！数据已填入表单', 'success');
            setTimeout(() => hideModal(), 1500);

        } catch (err) {
            console.error('Parse error:', err);
            updateStatus(`解析失败: ${err.message}`, 'error');
        } finally {
            setLoading(false);
        }
    }

    function fileToDataURL(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(new Error('读取文件失败'));
            reader.readAsDataURL(file);
        });
    }
}