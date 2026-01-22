/**
 * static/js/modules/utils.js
 * 通用工具函数库
 */

/**
 * 防抖函数
 * @param {Function} func - 需要执行的函数
 * @param {number} wait - 等待时间(ms)
 */
export function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

/**
 * 显示全局提示消息 (Toast)
 * @param {string} message - 消息内容
 * @param {string} type - 类型: 'success' | 'error' | 'info' | 'warning'
 * @param {number} duration - 显示时长(ms), 默认 3000
 */
export function showMessage(message, type = 'success', duration = 3000) {
    // 移除已存在的 toast 避免堆叠过多
    const existingToasts = document.querySelectorAll('.custom-toast');
    existingToasts.forEach(el => el.remove());

    const div = document.createElement('div');
    div.className = `custom-toast toast-${type}`;
    div.textContent = message;

    // 注入样式 (如果 css 中未定义，这里提供兜底样式)
    Object.assign(div.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '12px 24px',
        borderRadius: '8px',
        color: '#fff',
        zIndex: '9999',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        opacity: '0',
        transform: 'translateY(-20px)',
        transition: 'all 0.3s cubic-bezier(0.68, -0.55, 0.27, 1.55)',
        backgroundColor: type === 'success' ? '#4caf50' :
                         type === 'error' ? '#f44336' :
                         type === 'warning' ? '#ff9800' : '#2196f3'
    });

    document.body.appendChild(div);

    // 动画进入
    requestAnimationFrame(() => {
        div.style.opacity = '1';
        div.style.transform = 'translateY(0)';
    });

    // 定时移除
    setTimeout(() => {
        div.style.opacity = '0';
        div.style.transform = 'translateY(-20px)';
        div.addEventListener('transitionend', () => div.remove());
    }, duration);
}