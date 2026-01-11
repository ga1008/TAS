/**
 * static/js/modules/ui/window-resize.js
 * 通用窗口拖拽调整大小逻辑
 */

export class WindowResizer {
    /**
     * @param {HTMLElement} container - 需要调整大小的容器元素
     * @param {Object} options - 配置项
     * @param {number} options.minW - 最小宽度
     * @param {number} options.minH - 最小高度
     * @param {Function} options.onStart - 开始拖拽回调
     * @param {Function} options.onEnd - 结束拖拽回调
     */
    constructor(container, options = {}) {
        this.container = container;

        const screenBasedMinW = Math.min(350, window.innerWidth - 20);

        this.options = Object.assign({
            minW: screenBasedMinW,
            minH: 400,
            onStart: () => {},
            onEnd: () => {}
        }, options);

        this.state = {
            isResizing: false,
            direction: '',
            startX: 0,
            startY: 0,
            startRect: null
        };

        this._bindHandlers();
        this.init();
    }

    _bindHandlers() {
        this.handleMouseDown = this._onMouseDown.bind(this);
        this.handleMouseMove = this._onMouseMove.bind(this);
        this.handleMouseUp = this._onMouseUp.bind(this);
    }

    init() {
        // 查找容器内所有的 resizer 元素
        const resizers = this.container.querySelectorAll('.resizer');
        resizers.forEach(r => {
            r.addEventListener('mousedown', this.handleMouseDown);
        });
    }

    _getDirection(el) {
        const cl = el.classList;
        if (cl.contains('resizer-top-left')) return 'tl';
        if (cl.contains('resizer-top-right')) return 'tr';
        if (cl.contains('resizer-bottom-left')) return 'bl';
        if (cl.contains('resizer-bottom-right')) return 'br';
        if (cl.contains('resizer-top')) return 't';
        if (cl.contains('resizer-bottom')) return 'b';
        if (cl.contains('resizer-left')) return 'l';
        if (cl.contains('resizer-right')) return 'r';
        return '';
    }

    _onMouseDown(e) {
        // 如果全屏，禁用调整
        if (this.container.classList.contains('fullscreen')) return;

        e.preventDefault();
        e.stopPropagation(); // 防止事件冒泡

        const direction = this._getDirection(e.target);
        if (!direction) return;

        this.state = {
            isResizing: true,
            direction: direction,
            startX: e.clientX,
            startY: e.clientY,
            startRect: this.container.getBoundingClientRect()
        };

        // 预处理：将 right/bottom 定位转换为 left/top 定位，防止拖拽左/上边时窗口抖动
        // (假设 CSS 使用 fixed 或 absolute 定位)
        const rect = this.state.startRect;
        this.container.style.left = `${rect.left}px`;
        this.container.style.top = `${rect.top}px`;
        this.container.style.right = 'auto';
        this.container.style.bottom = 'auto';
        this.container.style.width = `${rect.width}px`;
        this.container.style.height = `${rect.height}px`;

        document.addEventListener('mousemove', this.handleMouseMove);
        document.addEventListener('mouseup', this.handleMouseUp);

        if (this.options.onStart) this.options.onStart();
    }

    _onMouseMove(e) {
        if (!this.state.isResizing) return;

        const { startX, startY, startRect, direction } = this.state;
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;

        let newW = startRect.width;
        let newH = startRect.height;
        let newX = startRect.left;
        let newY = startRect.top;

        // 宽度计算
        if (direction.includes('r')) {
            newW = startRect.width + dx;
        } else if (direction.includes('l')) {
            newW = startRect.width - dx;
            newX = startRect.left + dx;
        }

        // 高度计算
        if (direction.includes('b')) {
            newH = startRect.height + dy;
        } else if (direction.includes('t')) {
            newH = startRect.height - dy;
            newY = startRect.top + dy;
        }

        // 限制最小值
        if (newW < this.options.minW) {
            // 如果宽带达到最小，且是向左拖拽，需要修正 X 轴位置 (锁死在最小值的位置)
            if (direction.includes('l')) newX = startRect.left + (startRect.width - this.options.minW);
            newW = this.options.minW;
        }
        if (newH < this.options.minH) {
            if (direction.includes('t')) newY = startRect.top + (startRect.height - this.options.minH);
            newH = this.options.minH;
        }

        // 应用样式
        this.container.style.width = `${newW}px`;
        this.container.style.height = `${newH}px`;
        // 只有涉及左/上变动时才更新 left/top
        if (direction.includes('l')) this.container.style.left = `${newX}px`;
        if (direction.includes('t')) this.container.style.top = `${newY}px`;
    }

    _onMouseUp() {
        if (!this.state.isResizing) return;

        this.state.isResizing = false;
        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('mouseup', this.handleMouseUp);

        if (this.options.onEnd) this.options.onEnd();
    }
}