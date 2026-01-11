// 对应 dashboard.html 中的 logic
import { showMessage } from './modules/utils.js';

window.editProvider = function(data) {
    // ... 原有填充逻辑
    const modal = new bootstrap.Modal(document.getElementById('editProviderModal'));
    modal.show();
}

window.addModel = function(pId, pName) {
    // ... 原有逻辑
    const modal = new bootstrap.Modal(document.getElementById('modelModal'));
    modal.show();
}

// ... 其他 admin 函数