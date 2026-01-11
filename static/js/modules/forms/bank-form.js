/**
 * static/js/modules/forms/bank-form.js
 * 处理新建题库表单的校验与交互
 */

export function initBankForm() {
    const form = document.getElementById('createBankForm');
    if (!form) return;

    const els = {
        nameInput: document.getElementById('bankName'),
        feedback: document.getElementById('bankNameFeedback'),
        submitBtn: document.getElementById('createBankSubmitBtn')
    };

    if (!els.nameInput) return;

    // 状态重置函数
    const resetState = () => {
        els.nameInput.classList.remove('is-invalid');
        els.feedback.style.display = 'none';
        els.submitBtn.disabled = false;
    };

    // 1. 失去焦点时校验 (Blur)
    els.nameInput.addEventListener('blur', async function() {
        const name = this.value.trim();
        if (!name) {
            resetState();
            return;
        }

        try {
            // 禁用按钮防止校验期间提交
            els.submitBtn.disabled = true;

            const res = await fetch(`/check_bank_name?name=${encodeURIComponent(name)}`);
            const data = await res.json();

            if (data.exists) {
                els.nameInput.classList.add('is-invalid');
                els.feedback.textContent = '题库名称已存在';
                els.feedback.style.display = 'block';
                els.submitBtn.disabled = true; // 保持禁用
            } else {
                resetState(); // 校验通过
            }
        } catch (err) {
            console.error('题库名称校验失败:', err);
            // 接口出错时不应该阻塞用户提交，除非是严格校验
            els.submitBtn.disabled = false;
        }
    });

    // 2. 输入时清除错误 (Input) - 提升体验
    els.nameInput.addEventListener('input', function() {
        if (this.classList.contains('is-invalid')) {
            resetState();
        }
    });
}