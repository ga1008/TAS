/* static/js/script.js */

document.addEventListener('DOMContentLoaded', function() {

    // 1. 处理 "添加题目" 页面的动态表单
    const typeRadios = document.querySelectorAll('input[type="radio"][name="type"]');
    if (typeRadios.length > 0) {
        initAddQuestionForm(typeRadios);
    }

    // 2. 处理 "编辑题目" 和 "添加题目" 的表单
    const questionForm = document.getElementById('questionForm');
    if (questionForm) {
        // (合并) 多选题提交逻辑
        initMultiChoiceSubmit(questionForm);
        // (新增) 题目重复校验
        initQuestionCheck(questionForm);
    }

    // 3. (新增) 处理 "新建题库" 的重复校验
    const createBankForm = document.getElementById('createBankForm');
    if (createBankForm) {
        initBankNameCheck(createBankForm);
    }

    // 4. 题库筛选
    const filterForm = document.getElementById('filterForm');
    if (filterForm) {
        // (Request 1: 新增) 处理筛选持久化
        const fabAddButton = document.querySelector('.fab-add-question'); //
        const fabHref = fabAddButton ? fabAddButton.getAttribute('href') : null;
        // 从 FAB 按钮的 href 中提取 bank_id
        const fabBankIdMatch = fabHref ? fabHref.match(/bank_id=(\d+)/) : null;

        if (fabBankIdMatch && fabBankIdMatch[1]) {
            const bankId = fabBankIdMatch[1];
            // 使用 bank_id 确保 storage 键的唯一性
            const storageKey = `bank_${bankId}_filters`;
            // 在 initAutoFilter 之前调用持久化逻辑
            handleFilterPersistence(storageKey, filterForm);
        }

        // 筛选自动提交
        initAutoFilter(filterForm);
    }

    // 5. 图片解析弹窗
    if (document.getElementById('openImageParseModal')) {
        initImageParseModal();
    }

    // 6. (新增) 初始化 Bootstrap Tooltips (Request 3)
    // (用于 FAB 按钮的 hover 提示)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // -------------------------------------------------
    // 函数定义
    // -------------------------------------------------

    /**
     * (新增) 校验题库名称
     */
    function initBankNameCheck(form) {
        const nameInput = form.querySelector('#bankName');
        const feedback = form.querySelector('#bankNameFeedback');
        const submitBtn = form.querySelector('#createBankSubmitBtn');

        nameInput.addEventListener('blur', function() {
            const name = nameInput.value.trim();
            if (name === '') {
                nameInput.classList.remove('is-invalid');
                feedback.style.display = 'none'; // 隐藏反馈
                submitBtn.disabled = false;
                return;
            }

            fetch(`/check_bank_name?name=${encodeURIComponent(name)}`)
                .then(res => res.json())
                .then(data => {
                    if (data.exists) {
                        nameInput.classList.add('is-invalid');
                        feedback.textContent = '题库名称已存在';
                        feedback.style.display = 'block'; // 显示反馈
                        submitBtn.disabled = true;
                    } else {
                        nameInput.classList.remove('is-invalid');
                        feedback.style.display = 'none'; // 隐藏反馈
                        submitBtn.disabled = false;
                    }
                })
                .catch(err => console.error('Check failed', err));
        });
    }

    /**
     * (新增) 校验题目名称
     */
    function initQuestionCheck(form) {
        const questionInput = form.querySelector('#question');
        const feedback = form.querySelector('#questionFeedback');
        const submitBtns = form.querySelectorAll('.submit-btn');
        const bankId = form.dataset.bankId;
        const questionId = form.dataset.questionId; // (可能)

        const typeRadios = form.querySelectorAll('input[name="type"]');
        const hiddenType = form.querySelector('#questionType');

        async function validate() {
            const questionText = questionInput.value.trim();

            // 获取题型
            let questionType;
            if (hiddenType) {
                questionType = hiddenType.value; // 编辑页
            } else if (typeRadios.length > 0) {
                questionType = form.querySelector('input[name="type"]:checked').value; // 新增页
            }

            if (questionText === '' || !questionType || !bankId) {
                questionInput.classList.remove('is-invalid');
                feedback.style.display = 'none';
                submitBtns.forEach(btn => btn.disabled = false);
                return;
            }

            let url = `/check_question_text?bank_id=${bankId}&type=${questionType}&question_text=${encodeURIComponent(questionText)}`;

            if (questionId) {
                url += `&current_question_id=${questionId}`;
            }

            try {
                const res = await fetch(url);
                const data = await res.json();

                if (data.exists) {
                    questionInput.classList.add('is-invalid');
                    feedback.textContent = '该题库下已存在相同题型和题干的题目';
                    feedback.style.display = 'block';
                    submitBtns.forEach(btn => btn.disabled = true);
                } else {
                    questionInput.classList.remove('is-invalid');
                    feedback.style.display = 'none';
                    submitBtns.forEach(btn => btn.disabled = false);
                }
            } catch (err) {
                console.error('Check failed', err);
            }
        }

        // 焦点离开时校验
        questionInput.addEventListener('blur', validate);

        // (仅新增页) 切换类型时也要校验
        typeRadios.forEach(radio => radio.addEventListener('change', validate));
    }


    /**
     * (原 add_question.html 逻辑)
     * 初始化 "添加题目" 页面的表单逻辑
     */
    function initAddQuestionForm(radios) {
        const optionsSection = document.getElementById('options-section');
        const answerSection = document.getElementById('answer-section');
        const optionInputs = document.querySelectorAll('.option-input');

        function updateForm() {
            const selectedType = document.querySelector('input[name="type"]:checked').value;

            if (selectedType === 'judgment') {
                // 隐藏选项
                optionsSection.style.display = 'none';
                optionInputs.forEach(input => input.removeAttribute('required'));

                // 更新答案
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
                // 显示选项
                optionsSection.style.display = 'block';
                optionInputs.forEach(input => input.setAttribute('required', ''));

                if (selectedType === 'single_choice') {
                    // 单选题答案
                    answerSection.innerHTML = `
                        <label class="form-label">正确答案</label>
                        <div class="row g-2">
                            ${['A', 'B', 'C', 'D'].map(letter => `
                            <div class="col-md-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="radio" name="answer" value="${letter}" required>
                                    <label class="form-check-label">${letter}</label>
                                </div>
                            </div>
                            `).join('')}
                        </div>
                    `;
                } else {
                    // 多选题答案
                    answerSection.innerHTML = `
                        <label class="form-label">正确答案（可多选）</label>
                        <div class="row g-2">
                            ${['A', 'B', 'C', 'D'].map(letter => `
                            <div class="col-md-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="answer" value="${letter}">
                                    <label class="form-check-label">${letter}</label>
                                </div>
                            </div>
                            `).join('')}
                        </div>
                    `;
                }
            }
        }

        radios.forEach(radio => radio.addEventListener('change', updateForm));

        // 立即初始化表单
        updateForm();
    }

    /**
     * (Request 1: 新增)
     * 处理题库筛选持久化
     * @param {string} storageKey - sessionStorage 的键
     * @param {HTMLElement} form - 筛选表单
     */
    function handleFilterPersistence(storageKey, form) {
        const currentSearch = window.location.search;
        const storedSearch = sessionStorage.getItem(storageKey);

        // 1. 监听重置按钮
        //
        const resetBtn = form.querySelector('a[href*="bank_detail"]');
        if (resetBtn) {
            resetBtn.addEventListener('click', function() {
                // 用户点击重置，清除 storage
                sessionStorage.removeItem(storageKey);
                // 正常导航
            });
        }

        // 2. 检查当前 URL
        const params = new URLSearchParams(currentSearch);
        // 检查是否存在任何一个筛选参数
        const hasFilters = ['type', 'date_start', 'date_end', 'sort_by', 'per_page', 'search'].some(key => params.has(key));

        if (hasFilters) {
            // 3. 如果当前 URL 有筛选，保存它 (排除 page)
            params.delete('page');
            const filtersToStore = '?' + params.toString();

            if (filtersToStore !== '?') {
                sessionStorage.setItem(storageKey, filtersToStore);
            } else {
                // 如果所有筛选器都被移除了 (比如只剩 'page'), 视同重置
                sessionStorage.removeItem(storageKey);
            }

        } else if (storedSearch && storedSearch !== '?') {
            // 4. 如果当前 URL *没有* 筛选, 但 storage *有*, 则重定向
            // (排除一种情况: currentSearch 是空的, 且 storage 也是 '?' (空的), 避免无限循环)
            window.location.href = window.location.pathname + storedSearch;
        }
    }


    /**
     * 列表筛选选项自动提交
     */
    function initAutoFilter(form) {
        const checkboxInputs = form.querySelectorAll('input[type="checkbox"]');
        const selectInputs = form.querySelectorAll('select');
        const datetimeInputs = form.querySelectorAll('input[type="datetime-local"]');
        const pageInput = form.querySelector('input[name="page"]');
        const startInput = form.querySelector('input[name="date_start"]');
        const endInput = form.querySelector('input[name="date_end"]');

        function submitWithResetPage() {
            if (pageInput) {
                pageInput.value = '1';
            }
            form.submit();
        }

        checkboxInputs.forEach(input => {
            input.addEventListener('change', submitWithResetPage);
        });

        selectInputs.forEach(input => {
            input.addEventListener('change', submitWithResetPage);
        });

        datetimeInputs.forEach(input => {
            input.addEventListener('change', (event) => {
                if (!startInput || !endInput) {
                    submitWithResetPage();
                    return;
                }

                const startHasValue = startInput.value.trim() !== '';
                const endHasValue = endInput.value.trim() !== '';

                if (event.target === startInput && startHasValue && !endHasValue) {
                    // 等待结束时间，允许连续点选
                    return;
                }

                submitWithResetPage();
            });
        });
    }

    /**
     * (原 edit_question.html 和 add_question.html 逻辑)
     * 初始化 "添加" 和 "编辑" 页面中多选题的提交逻辑
     */
    function initMultiChoiceSubmit(form) {

        form.addEventListener('submit', function(e) {

            // 确定题目类型
            let questionType;
            const typeInput = document.querySelector('input[name="type"]:checked'); // add_question 页面
            const typeHidden = document.getElementById('questionType'); // edit_question 页面

            if (typeInput) {
                questionType = typeInput.value;
            } else if (typeHidden) {
                questionType = typeHidden.value;
            }

            if (questionType === 'multiple_choice') {
                const checkboxes = form.querySelectorAll('input[name="answer"]:checked');
                if (checkboxes.length === 0) {
                    e.preventDefault();
                    alert('请至少选择一个正确答案');
                    return;
                }

                // 将多选答案合并为 A,B,C 格式
                const answers = Array.from(checkboxes).map(cb => cb.value).join(',');

                // 清理旧的答案输入，防止重复提交
                // (重要) 必须清理 *所有* name="answer" 的输入
                const oldAnswers = form.querySelectorAll('input[name="answer"]');
                oldAnswers.forEach(inp => {
                    // 移除 input，否则它们仍会作为表单数据提交（即使是 disabled）
                    // 最安全的方式是直接移除
                    if (inp.type === 'checkbox') {
                         inp.closest('.col-md-3').remove(); // 移除 DOM 避免提交
                    }
                });

                // 添加一个隐藏的 input 来提交合并后的答案
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'answer';
                hiddenInput.value = answers;
                form.appendChild(hiddenInput);
            }
        });
    }

    /**
     * 初始化题目图片解析弹窗
     */
    function initImageParseModal() {
        const modalEl = document.getElementById('imageParseModal');
        const openBtn = document.getElementById('openImageParseModal');
        const uploadInput = document.getElementById('imageUploadInput');
        const dropZone = document.getElementById('imageDropZone');
        const previewList = document.getElementById('imagePreviewList');
        const statusEl = document.getElementById('imageParseStatus');
        const parseBtn = document.getElementById('parseImagesBtn');

        if (!modalEl || !openBtn || !uploadInput || !dropZone || !previewList || !statusEl || !parseBtn) {
            return;
        }

        if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
            console.warn('Bootstrap 未加载，无法启用图片解析弹窗。');
            return;
        }

        const modalInstance = new bootstrap.Modal(modalEl);
        let imageFiles = [];

        function resetModal() {
            imageFiles = [];
            uploadInput.value = '';
            updatePreview();
            updateStatus('', 'muted');
        }

        function updateStatus(message, state) {
            statusEl.textContent = message;
            statusEl.className = 'small mt-3';
            if (!message) {
                return;
            }
            if (state === 'error') {
                statusEl.classList.add('text-danger');
            } else if (state === 'success') {
                statusEl.classList.add('text-success');
            } else if (state === 'muted') {
                statusEl.classList.add('text-muted');
            }
        }

        function updatePreview() {
            previewList.innerHTML = '';
            if (!imageFiles.length) {
                const empty = document.createElement('li');
                empty.className = 'list-group-item text-muted text-center';
                empty.textContent = '尚未添加图片';
                previewList.appendChild(empty);
                return;
            }

            imageFiles.forEach((file, index) => {
                const li = document.createElement('li');
                li.className = 'list-group-item d-flex justify-content-between align-items-center';

                const titleSpan = document.createElement('span');
                const sizeKB = Math.max(file.size / 1024, 1).toFixed(1);
                titleSpan.textContent = `${file.name} (${sizeKB} KB)`;

                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'image-preview-remove';
                removeBtn.dataset.index = String(index);
                removeBtn.setAttribute('aria-label', '删除图片');
                removeBtn.innerHTML = '<i class="fas fa-times"></i>';

                li.appendChild(titleSpan);
                li.appendChild(removeBtn);
                previewList.appendChild(li);
            });
        }

        function addFiles(files) {
            if (!files || !files.length) {
                return;
            }

            const validImages = Array.from(files).filter(file => file && file.type && file.type.startsWith('image/'));
            if (!validImages.length) {
                updateStatus('请选择图片文件进行解析。', 'error');
                return;
            }

            validImages.forEach(file => imageFiles.push(file));
            updatePreview();
            updateStatus('', 'muted');
        }

        function setParsingState(isParsing) {
            parseBtn.disabled = isParsing;
            const spinner = parseBtn.querySelector('.spinner-border');
            const textSpan = parseBtn.querySelector('.parse-btn-text');
            if (spinner) {
                spinner.classList.toggle('d-none', !isParsing);
            }
            if (textSpan) {
                textSpan.textContent = isParsing ? '解析中...' : '解析';
            }
        }

        function fileToDataURL(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.onerror = () => reject(new Error('读取图片失败'));
                reader.readAsDataURL(file);
            });
        }

        function normalizeOptionValue(option, index) {
            if (!option) {
                return '';
            }
            if (typeof option === 'string') {
                return option.trim();
            }
            const text = option.text || option.label || option.value || option.option || `选项 ${String.fromCharCode(65 + index)}`;
            return text ? text.toString().trim() : '';
        }

        function applyParsedResult(parsed) {
            if (!parsed || !questionForm) {
                return;
            }

            const questionInput = questionForm.querySelector('#question');
            if (questionInput) {
                let updated = false;
                if (parsed.question) {
                    questionInput.value = parsed.question.trim();
                    updated = true;
                } else if (parsed.question_text) {
                    questionInput.value = parsed.question_text.trim();
                    updated = true;
                }
                if (updated) {
                    questionInput.dispatchEvent(new Event('blur'));
                }
            }

            const targetType = parsed.question_type || parsed.type;
            if (targetType) {
                const radio = questionForm.querySelector(`input[name="type"][value="${targetType}"]`);
                if (radio) {
                    radio.checked = true;
                    radio.dispatchEvent(new Event('change'));
                }
            }

            const optionInputs = questionForm.querySelectorAll('.option-input');
            if (optionInputs.length) {
                const options = Array.isArray(parsed.options) ? parsed.options : Array.isArray(parsed.choices) ? parsed.choices : [];
                optionInputs.forEach((input, index) => {
                    const value = normalizeOptionValue(options[index], index);
                    input.value = value || '';
                });
            }

            const answers = Array.isArray(parsed.correct_answers) ? parsed.correct_answers
                : Array.isArray(parsed.answers) ? parsed.answers
                    : parsed.correct_answer ? [parsed.correct_answer] : [];
            if (answers.length) {
                const normalizedAnswers = answers.map(value => value == null ? '' : value.toString().trim());
                const type = (targetType || questionForm.querySelector('input[name="type"]:checked')?.value || '').toString();
                if (type === 'multiple_choice') {
                    const checkboxAnswers = normalizedAnswers.map(value => value.toString().toUpperCase());
                    const checkboxes = questionForm.querySelectorAll('input[name="answer"][type="checkbox"]');
                    checkboxes.forEach(cb => {
                        cb.checked = checkboxAnswers.includes(cb.value);
                    });
                } else if (type === 'judgment') {
                    const normalized = normalizedAnswers[0] || '';
                    const radios = questionForm.querySelectorAll('input[name="answer"][type="radio"]');
                    radios.forEach(radio => {
                        radio.checked = radio.value === normalized;
                    });
                } else {
                    const firstAnswer = normalizedAnswers[0] || '';
                    const normalized = firstAnswer.toUpperCase();
                    const radios = questionForm.querySelectorAll('input[name="answer"][type="radio"]');
                    radios.forEach(radio => {
                        radio.checked = radio.value === normalized;
                    });
                }
            }
        }

        openBtn.addEventListener('click', () => {
            resetModal();
            modalInstance.show();
        });

        dropZone.addEventListener('click', () => uploadInput.click());

        dropZone.addEventListener('dragover', event => {
            event.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', event => {
            event.preventDefault();
            dropZone.classList.remove('dragover');
            addFiles(event.dataTransfer ? event.dataTransfer.files : []);
        });

        uploadInput.addEventListener('change', event => {
            addFiles(event.target.files);
            uploadInput.value = '';
        });

        previewList.addEventListener('click', event => {
            if (event.target.closest('.image-preview-remove')) {
                const btn = event.target.closest('.image-preview-remove');
                const index = parseInt(btn.dataset.index, 10);
                if (!Number.isNaN(index)) {
                    imageFiles.splice(index, 1);
                    updatePreview();
                }
            }
        });

        document.addEventListener('paste', event => {
            if (!modalEl.classList.contains('show')) {
                return;
            }
            const clipboardItems = event.clipboardData ? event.clipboardData.items : [];
            const files = [];
            for (const item of clipboardItems) {
                if (item.kind === 'file') {
                    const file = item.getAsFile();
                    if (file && file.type && file.type.startsWith('image/')) {
                        files.push(file);
                    }
                }
            }
            if (files.length) {
                event.preventDefault();
                addFiles(files);
            }
        });

        parseBtn.addEventListener('click', async () => {
            if (!imageFiles.length) {
                updateStatus('请先添加至少一张图片。', 'error');
                return;
            }

            setParsingState(true);
            updateStatus('正在解析图片，请稍候...', 'muted');

            try {
                const base64List = await Promise.all(imageFiles.map(file => fileToDataURL(file)));
                const response = await fetch('/ai/parse-question', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ images: base64List })
                });

                const result = await response.json();
                if (!response.ok || result.status !== 'success') {
                    const message = result.message || '解析失败，请稍后重试。';
                    throw new Error(message);
                }

                applyParsedResult(result.data);
                updateStatus('解析成功，题目信息已填入表单，请确认后保存。', 'success');

                // --- (Request 2: 新增代码) ---
                // 延迟 1.5 秒自动关闭弹窗，以便用户阅读提示
                setTimeout(() => {
                    modalInstance.hide();
                }, 1500);
                // --- (新增代码结束) ---

            } catch (err) {
                console.error('图片解析失败', err);
                updateStatus(err.message || '解析失败，请稍后重试。', 'error');
            } finally {
                setParsingState(false);
            }
        });

        modalEl.addEventListener('hidden.bs.modal', () => {
            resetModal();
        });

        // 初始化预览
        resetModal();
    }
});