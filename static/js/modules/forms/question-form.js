/**
 * static/js/modules/forms/question-form.js
 * 处理题目的添加、编辑、校验、类型切换以及外部数据填充
 */

// 缓存 DOM 元素查询，避免重复查找
const DOM = {
    form: () => document.getElementById('questionForm'),
    typeRadios: () => document.querySelectorAll('input[name="type"]'),
    hiddenType: () => document.getElementById('questionType'), // 编辑模式下的隐藏域
    questionInput: () => document.getElementById('question'),
    optionsSection: () => document.getElementById('options-section'),
    answerSection: () => document.getElementById('answer-section'),
    optionInputs: () => document.querySelectorAll('.option-input'),
    feedback: () => document.getElementById('questionFeedback'),
    submitBtns: () => document.querySelectorAll('.submit-btn')
};

/**
 * 初始化题目表单逻辑
 */
export function initQuestionForm() {
    const form = DOM.form();
    if (!form) return;

    // 1. 绑定类型切换事件 (仅在新增页面有效)
    const radios = DOM.typeRadios();
    if (radios.length > 0) {
        radios.forEach(radio => {
            radio.addEventListener('change', updateFormUI);
        });
        // 初始化 UI
        updateFormUI();
    }

    // 2. 绑定重复校验逻辑
    const questionInput = DOM.questionInput();
    if (questionInput) {
        questionInput.addEventListener('blur', validateQuestion);
        // 输入时清除错误状态
        questionInput.addEventListener('input', () => {
            questionInput.classList.remove('is-invalid');
            const fb = DOM.feedback();
            if(fb) fb.style.display = 'none';
            DOM.submitBtns().forEach(btn => btn.disabled = false);
        });

        // 切换类型时也需要重新校验（因为同一题目内容在不同题型下可能允许存在）
        if (radios.length > 0) {
            radios.forEach(r => r.addEventListener('change', validateQuestion));
        }
    }

    // 3. 绑定表单提交拦截 (处理多选题数据合并)
    form.addEventListener('submit', handleFormSubmit);
}

/**
 * 供外部调用：填充表单数据 (例如由图片解析器调用)
 * @param {Object} data 解析后的题目数据
 */
export function fillQuestionFormData(data) {
    const form = DOM.form();
    if (!data || !form) return;

    // 1. 填充题干
    const qInput = DOM.questionInput();
    if (data.question || data.question_text) {
        qInput.value = (data.question || data.question_text).trim();
        // 触发校验
        qInput.dispatchEvent(new Event('blur'));
    }

    // 2. 切换题型
    const targetType = data.question_type || data.type;
    if (targetType) {
        const radio = form.querySelector(`input[name="type"][value="${targetType}"]`);
        if (radio) {
            radio.checked = true;
            // 触发 UI 更新
            updateFormUI();
        }
    }

    // 3. 填充选项 (如果是选择题)
    const inputs = DOM.optionInputs();
    if (inputs.length > 0) {
        const options = Array.isArray(data.options) ? data.options : (data.choices || []);
        inputs.forEach((input, index) => {
            // 处理可能存在的对象格式 { label: 'A', text: '...' } 或纯字符串
            const optVal = options[index];
            let text = '';
            if (optVal) {
                text = typeof optVal === 'string' ? optVal : (optVal.text || optVal.value || '');
            }
            input.value = text.trim();
        });
    }

    // 4. 填充答案
    fillAnswer(data);
}

// ================= 内部逻辑函数 =================

/**
 * 根据当前选中的题型更新表单 UI (显示/隐藏选项，渲染答案区)
 */
function updateFormUI() {
    const optionsSection = DOM.optionsSection();
    const answerSection = DOM.answerSection();
    const optionInputs = DOM.optionInputs();

    // 获取当前选中的类型
    const checkedRadio = document.querySelector('input[name="type"]:checked');
    if (!checkedRadio) return;

    const type = checkedRadio.value;

    if (type === 'judgment') {
        // 判断题：隐藏选项输入，答案区显示 正确/错误
        if (optionsSection) optionsSection.style.display = 'none';
        optionInputs.forEach(input => input.removeAttribute('required'));

        answerSection.innerHTML = `
            <label class="form-label">正确答案</label>
            <div>
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="answer" value="正确" required>
                    <label class="form-check-label">正确</label>
                </div>
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="radio" name="answer" value="错误">
                    <label class="form-check-label">错误</label>
                </div>
            </div>
        `;
    } else {
        // 选择题：显示选项输入
        if (optionsSection) optionsSection.style.display = 'block';
        optionInputs.forEach(input => input.setAttribute('required', ''));

        // 生成 A-D 选项 HTML
        const generateOptions = (inputType) => {
            return ['A', 'B', 'C', 'D'].map(letter => `
                <div class="col-md-3">
                    <div class="form-check">
                        <input class="form-check-input" type="${inputType}" name="answer" value="${letter}" ${inputType === 'checkbox' ? '' : 'required'}>
                        <label class="form-check-label">${letter}</label>
                    </div>
                </div>
            `).join('');
        };

        if (type === 'single_choice') {
            answerSection.innerHTML = `
                <label class="form-label">正确答案</label>
                <div class="row g-2">${generateOptions('radio')}</div>
            `;
        } else { // multiple_choice
            answerSection.innerHTML = `
                <label class="form-label">正确答案（可多选）</label>
                <div class="row g-2">${generateOptions('checkbox')}</div>
            `;
        }
    }
}

/**
 * 校验题目是否重复
 */
async function validateQuestion() {
    const form = DOM.form();
    const qInput = DOM.questionInput();
    const feedback = DOM.feedback();

    if (!form || !qInput) return;

    const text = qInput.value.trim();
    const bankId = form.dataset.bankId;
    const questionId = form.dataset.questionId; // 编辑模式才有

    // 获取题型
    let type = '';
    const hiddenType = DOM.hiddenType();
    const checkedRadio = document.querySelector('input[name="type"]:checked');

    if (hiddenType) type = hiddenType.value;
    else if (checkedRadio) type = checkedRadio.value;

    if (!text || !type || !bankId) return;

    let url = `/check_question_text?bank_id=${bankId}&type=${type}&question_text=${encodeURIComponent(text)}`;
    if (questionId) url += `&current_question_id=${questionId}`;

    try {
        const res = await fetch(url);
        const data = await res.json();

        if (data.exists) {
            qInput.classList.add('is-invalid');
            if (feedback) {
                feedback.textContent = '该题库下已存在相同题型和题干的题目';
                feedback.style.display = 'block';
            }
            DOM.submitBtns().forEach(btn => btn.disabled = true);
        } else {
            qInput.classList.remove('is-invalid');
            if (feedback) feedback.style.display = 'none';
            DOM.submitBtns().forEach(btn => btn.disabled = false);
        }
    } catch (err) {
        console.error('Check failed', err);
    }
}

/**
 * 处理表单提交
 */
function handleFormSubmit(e) {
    const form = e.target;

    // 确定题目类型
    let type = '';
    const hiddenType = DOM.hiddenType();
    const checkedRadio = form.querySelector('input[name="type"]:checked');

    if (hiddenType) type = hiddenType.value; // 编辑页优先使用 hidden
    else if (checkedRadio) type = checkedRadio.value;

    // 仅处理多选题逻辑
    if (type === 'multiple_choice') {
        const checkboxes = form.querySelectorAll('input[name="answer"]:checked');
        if (checkboxes.length === 0) {
            e.preventDefault();
            // 使用原生 alert 或者 toast
            alert('请至少选择一个正确答案');
            return;
        }

        // 合并答案为 "A,B" 格式
        const answers = Array.from(checkboxes).map(cb => cb.value).join(',');

        // 移除原有的 checkbox name 属性，防止它们被提交
        // 注意：这里我们移除 name 属性而不是移除 DOM，这样如果提交失败（例如后端验证失败），
        // 页面刷新后用户还能看到原来的选项（虽然 submit 通常会导致刷新，但为了稳健性）
        const allCheckboxes = form.querySelectorAll('input[name="answer"]');
        allCheckboxes.forEach(cb => cb.removeAttribute('name'));

        // 添加隐藏域提交合并后的值
        let hiddenInput = form.querySelector('input[name="answer"][type="hidden"]');
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'answer';
            form.appendChild(hiddenInput);
        }
        hiddenInput.value = answers;
    }
}

/**
 * 辅助函数：填充答案
 */
function fillAnswer(data) {
    const form = DOM.form();

    // 获取答案数组
    let answers = [];
    if (Array.isArray(data.correct_answers)) answers = data.correct_answers;
    else if (Array.isArray(data.answers)) answers = data.answers;
    else if (data.correct_answer) answers = [data.correct_answer];

    if (answers.length === 0) return;

    // 规范化答案 (转字符串、去空格、大写)
    const normalizedAnswers = answers.map(val => String(val).trim().toUpperCase());

    // 获取当前题目类型
    const typeRadio = form.querySelector('input[name="type"]:checked');
    // 这种情况下可能是编辑页(hidden)或新增页(radio)，但填充通常发生在新增页
    // 如果是编辑页，DOM.hiddenType() 存在
    const type = (typeRadio ? typeRadio.value : (DOM.hiddenType()?.value || ''));

    if (type === 'multiple_choice') {
        const checkboxes = form.querySelectorAll('input[name="answer"][type="checkbox"]');
        checkboxes.forEach(cb => {
            if (normalizedAnswers.includes(cb.value)) {
                cb.checked = true;
            }
        });
    } else {
        // 单选或判断
        // 判断题解析出来可能是 "正确"/"错误" 或 true/false 或 A/B
        // 这里做一个简单的映射尝试
        let targetVal = normalizedAnswers[0];
        if (type === 'judgment') {
            if (['TRUE', 'YES', 'T', 'A', '对'].includes(targetVal)) targetVal = '正确';
            else if (['FALSE', 'NO', 'F', 'B', '错'].includes(targetVal)) targetVal = '错误';
        }

        const radios = form.querySelectorAll('input[name="answer"][type="radio"]');
        radios.forEach(radio => {
            if (radio.value === targetVal) {
                radio.checked = true;
            }
        });
    }
}