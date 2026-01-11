/**
 * static/js/modules/api.js
 * 统一 API 请求封装
 */

import { showMessage } from './utils.js';

class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultHeaders = {
            'Content-Type': 'application/json',
            // 如果有 CSRF token 可以在这里统一添加
            // 'X-CSRFToken': getCsrfToken()
        };

        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, config);

            // 处理 HTTP 错误状态
            if (!response.ok) {
                // 尝试解析错误信息
                let errorMsg = `请求失败: ${response.status}`;
                try {
                    const errorData = await response.json();
                    if (errorData.detail || errorData.message) {
                        errorMsg = errorData.detail || errorData.message;
                    }
                } catch (e) {
                    // 响应不是 JSON，使用默认文本
                }
                throw new Error(errorMsg);
            }

            // 如果是 204 No Content
            if (response.status === 204) {
                return null;
            }

            return await response.json();

        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            // 只有在非静默模式下才弹窗
            if (!options.silent) {
                showMessage(error.message || '网络请求发生错误', 'error');
            }
            throw error;
        }
    }

    get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

// 导出单例
export const api = new ApiClient();