/**
 * static/js/modules/lists/filter-list.js
 * 处理列表页面的筛选、排序自动提交及状态持久化
 */

export function initFilterList() {
    const form = document.getElementById('filterForm');
    if (!form) return;

    // 1. 持久化处理 (进入页面时检查是否需要恢复筛选，或保存当前筛选)
    handlePersistence(form);

    // 2. 绑定自动提交事件
    bindAutoSubmit(form);
}

/**
 * 处理筛选状态的持久化 (SessionStorage)
 */
function handlePersistence(form) {
    // 尝试获取 bank_id 以生成唯一的 storage key
    // 优先从 URL 获取，其次尝试从页面元素获取
    let bankId = null;
    const pathMatch = window.location.pathname.match(/bank\/(\d+)/);
    if (pathMatch) {
        bankId = pathMatch[1];
    } else {
        // 回退：尝试从 FAB 按钮获取 (原逻辑兼容)
        const fab = document.querySelector('.fab-add-question');
        const fabHref = fab ? fab.getAttribute('href') : '';
        const fabMatch = fabHref.match(/bank_id=(\d+)/);
        if (fabMatch) bankId = fabMatch[1];
    }

    if (!bankId) return;

    const storageKey = `bank_${bankId}_filters`;
    const currentSearch = window.location.search;
    const params = new URLSearchParams(currentSearch);

    // 检查是否有筛选参数 (排除 page)
    const filterKeys = ['type', 'date_start', 'date_end', 'sort_by', 'per_page', 'search'];
    const hasActiveFilters = filterKeys.some(key => params.has(key));

    // A. 绑定重置按钮逻辑
    const resetBtn = form.querySelector('a[href*="bank_detail"]');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            sessionStorage.removeItem(storageKey);
        });
    }

    // B. 状态保存与恢复逻辑
    if (hasActiveFilters) {
        // 如果当前 URL 有筛选参数，保存到 Storage
        // (移除 page 参数，因为筛选变动通常意味着回到第一页，但单纯保存状态时不需要 page)
        params.delete('page');
        const searchStr = params.toString();
        if (searchStr) {
            sessionStorage.setItem(storageKey, '?' + searchStr);
        } else {
            sessionStorage.removeItem(storageKey);
        }
    } else {
        // 如果当前 URL 没有筛选参数 (即干净的 /bank/1)，但 Storage 有存货，则恢复
        const storedSearch = sessionStorage.getItem(storageKey);
        if (storedSearch && storedSearch !== '?' && storedSearch !== currentSearch) {
            window.location.href = window.location.pathname + storedSearch;
        }
    }
}

/**
 * 绑定表单元素的 Change 事件以自动提交
 */
function bindAutoSubmit(form) {
    const inputs = form.querySelectorAll('input[type="checkbox"], select');
    const dateInputs = form.querySelectorAll('input[type="datetime-local"]');
    const startInput = form.querySelector('#dateStart');
    const endInput = form.querySelector('#dateEnd');

    // 辅助：提交前重置页码
    const submit = () => {
        const pageInput = form.querySelector('input[name="page"]');
        if (pageInput) pageInput.value = 1;
        form.submit();
    };

    // 常规输入：直接提交
    inputs.forEach(input => {
        input.addEventListener('change', submit);
    });

    // 日期输入：智能判断
    dateInputs.forEach(input => {
        input.addEventListener('change', (e) => {
            // 如果只选了开始没选结束（或反之），且另一个框是空的，暂时不提交，等待用户填完
            if (startInput && endInput) {
                const sVal = startInput.value;
                const eVal = endInput.value;

                // 如果当前操作的是开始时间，且没有结束时间 -> 等待
                if (e.target === startInput && sVal && !eVal) return;
                // 如果当前操作的是结束时间，且没有开始时间 -> 等待
                // (虽然逻辑上不太可能，但为了体验)
            }
            submit();
        });
    });
}