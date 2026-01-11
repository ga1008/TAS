这里是完整的解决方案。为了彻底解决 Gunicorn 超时问题并提供优雅的人机交互体验，我们需要做两件事：

1. **后端 (`app.py`)**：新增一个“单人批改”的 API 接口。
2. **前端 (`grading.html`)**：重写页面逻辑，使用 JavaScript 控制进度条，**逐个**调用 API，实现实时的流式批改效果。

---

### 第一步：修改后端 `app.py`

请将以下代码添加到 `app.py` 的末尾（或者放在路由定义的区域）。我们需要提取批改逻辑并暴露一个新的 API。

```python
# ==============================================================================
# 新增：单人批改 API (解决 Docker/Gunicorn 超时问题)
# ==============================================================================

def _grade_single_student_internal(class_id, student_id):
    """
    内部核心逻辑：只批改一个学生
    """
    # 1. 获取基本信息
    cls_info = db.get_class_by_id(class_id)
    if not cls_info:
        return False, "班级不存在", None

    # 务必使用 get_real_workspace_path (如果你在之前步骤已添加该函数)
    # 如果没有添加，请确保这里使用正确的路径逻辑
    if 'get_real_workspace_path' in globals():
        workspace_path = get_real_workspace_path(class_id)
    else:
        # 兼容旧逻辑
        workspace_path = cls_info['workspace_path']
    
    raw_dir = os.path.join(workspace_path, 'raw_zips')
    extract_base = os.path.join(workspace_path, 'extracted')

    # 2. 获取学生信息
    conn = db.get_connection()
    student = conn.execute("SELECT * FROM students WHERE class_id=? AND student_id=?", 
                           (class_id, student_id)).fetchone()
    if not student:
        return False, "找不到学生记录", None

    name = student['name']
    
    # 3. 查找对应的压缩包
    if not os.path.exists(raw_dir):
        return False, "未上传任何文件", None
        
    uploaded_files = os.listdir(raw_dir)
    matched_file = None
    # 文件名匹配逻辑：学号 或 姓名
    for f in uploaded_files:
        if str(student_id) in f or name in f:
            matched_file = f
            break
            
    if not matched_file:
        db.save_grade_error(student_id, class_id, "未找到提交文件", "")
        return False, "未找到提交文件 (No Submission)", None

    # 4. 准备解压目录
    student_extract_dir = os.path.join(extract_base, str(student_id))
    if os.path.exists(student_extract_dir):
        try:
            shutil.rmtree(student_extract_dir)
        except:
            pass # 忽略删除错误
    os.makedirs(student_extract_dir, exist_ok=True)
    
    archive_path = os.path.join(raw_dir, matched_file)
    
    try:
        # 5. 加载评分策略
        grader = GraderFactory.get_grader(cls_info['strategy'])
        if not grader:
            return False, f"策略 {cls_info['strategy']} 加载失败", matched_file

        # 6. 解压
        try:
            patoolib.extract_archive(archive_path, outdir=student_extract_dir, verbosity=-1)
        except Exception as e:
            # 针对 Linux 环境下缺少 rar 支持的特殊提示
            if "rar" in matched_file.lower() and "patool" in str(e):
                raise Exception("解压失败(服务器不支持RAR格式，请上传ZIP)")
            raise e
        
        # 7. === 核心：调用 AI 批改 ===
        # 这一步最耗时 (30s - 60s)
        result = grader.grade(student_extract_dir, {"sid": str(student_id), "name": name})
        
        # 8. 保存结果
        status = "PASS" if result.is_pass else "FAIL"
        db.save_grade(str(student_id), class_id, result.total_score, result.get_details_json(),
                      result.get_deduct_str(), status, matched_file)
                      
        return True, "批改完成", {
            "total_score": result.total_score,
            "status": status,
            "filename": matched_file,
            "deduct": result.get_deduct_str(),
            "details": result.sub_scores
        }
        
    except Exception as e:
        err_msg = f"系统异常: {str(e)}"
        print(f"[Grading Error] {student_id}: {e}")
        # traceback.print_exc()
        db.save_grade_error(str(student_id), class_id, err_msg, matched_file)
        return False, err_msg, matched_file


@app.route('/api/grade_student/<int:class_id>/<string:student_id>', methods=['POST'])
def api_grade_single_student(class_id, student_id):
    """前端逐个调用的接口"""
    try:
        success, msg, data = _grade_single_student_internal(class_id, student_id)
        if success:
            return jsonify({"status": "success", "msg": msg, "data": data})
        else:
            return jsonify({"status": "error", "msg": msg, "filename": data if isinstance(data, str) else ""})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

```

---

### 第二步：完整的前端代码 `templates/grading.html`

这份代码替换了原有的文件。
**主要改进点：**

1. **流式批改 UI**：增加了一个悬浮的“批改控制台”，显示进度条、成功数、失败数、耗时预估。
2. **实时反馈**：每批改完一个学生，表格对应行会立即更新分数和状态，**无需刷新页面**。
3. **自动滚动**：页面会自动滚动到当前正在批改的学生行。
4. **防误触**：批改过程中自动禁用按钮，支持中途停止。
5. **美观**：使用了 Tailwind CSS 制作了平滑的动画和清晰的状态标识。

```html
<!DOCTYPE html>
<html>
<head>
    <title>AI 智能批改控制台 - {{ cls['name'] }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        /* 自定义样式补充 */
        .deduct-item { display: inline-block; background: #fee2e2; color: #b91c1c; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; margin-right: 4px; margin-bottom: 2px; border: 1px solid #fecaca; }
        .score-tag { display: inline-flex; align-items: center; background: #eff6ff; border: 1px solid #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; margin-right: 6px; margin-bottom: 4px; }
        .score-tag span.val { font-weight: bold; margin-left: 4px; color: #2563eb; }

        /* 进度条动画 */
        .progress-bar-transition { transition: width 0.5s ease-in-out; }
        
        /* 表格行高亮动画 */
        @keyframes highlightRow {
            0% { background-color: #e0e7ff; }
            100% { background-color: transparent; }
        }
        .row-active { background-color: #e0e7ff !important; border-left: 4px solid #4f46e5; }
        .row-updated { animation: highlightRow 2s ease-out; }
    </style>
</head>
<body class="bg-gray-50 min-h-screen font-sans pb-20">

    <nav class="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="/" class="text-gray-500 hover:text-gray-700 mr-4 transition"><i class="fas fa-arrow-left"></i> 返回</a>
                    <h1 class="text-xl font-bold text-gray-800">{{ cls['course'] }} <span class="text-gray-300 mx-2">|</span> {{ cls['name'] }}</h1>
                    <span class="ml-4 px-2 py-1 bg-indigo-50 text-indigo-600 text-xs rounded border border-indigo-100 font-mono">
                        <i class="fas fa-code-branch"></i> {{ cls['strategy'] }}
                    </span>
                </div>
                <div class="flex items-center space-x-3">
                    <button onclick="deleteData()" class="text-gray-400 hover:text-red-500 hover:bg-red-50 px-3 py-2 rounded transition text-sm">
                        <i class="fas fa-trash-alt mr-1"></i> 删除任务
                    </button>
                    <button onclick="clearData()" class="text-gray-400 hover:text-red-500 hover:bg-red-50 px-3 py-2 rounded transition text-sm">
                        <i class="fas fa-broom mr-1"></i> 清空成绩
                    </button>
                    <a href="/export/{{ cls['id'] }}" class="bg-green-600 text-white px-4 py-2 rounded shadow hover:bg-green-700 transition flex items-center text-sm">
                        <i class="fas fa-file-excel mr-2"></i> 导出成绩单
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="md:col-span-2 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <h3 class="text-lg font-bold mb-3 text-gray-700 flex items-center">
                    <span class="bg-blue-100 text-blue-600 w-8 h-8 rounded-full flex items-center justify-center mr-2 text-sm font-bold">1</span>
                    上传作业包
                </h3>
                <div id="dropzone" class="border-2 border-dashed border-blue-200 rounded-xl p-8 text-center bg-blue-50 hover:bg-blue-100 transition cursor-pointer relative group">
                    <input type="file" id="fileInput" multiple class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" onchange="handleFiles(this.files)">
                    <i class="fas fa-cloud-upload-alt text-4xl text-blue-400 group-hover:text-blue-600 transition mb-3"></i>
                    <p class="text-gray-700 font-medium">点击或拖拽全班压缩包到此处</p>
                    <p class="text-xs text-gray-400 mt-1">支持 .zip, .rar (文件名需包含学号或姓名)</p>
                </div>
                <div id="uploadStatus" class="mt-3 text-sm hidden flex items-center p-2 bg-gray-50 rounded">
                    </div>
            </div>

            <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex flex-col justify-center relative overflow-hidden">
                <div class="absolute top-0 right-0 p-4 opacity-10">
                    <i class="fas fa-robot text-9xl text-indigo-500"></i>
                </div>
                
                <h3 class="text-lg font-bold mb-3 text-gray-700 flex items-center z-10">
                    <span class="bg-indigo-100 text-indigo-600 w-8 h-8 rounded-full flex items-center justify-center mr-2 text-sm font-bold">2</span>
                    智能批改
                </h3>
                
                <div class="z-10">
                    <p class="text-gray-500 text-xs mb-4">
                        <i class="fas fa-info-circle mr-1"></i> AI 将逐个分析学生作业。处理每个学生约需 30-60 秒 (视图片数量而定)。
                    </p>
                    
                    <button onclick="startBatchGrading()" id="btnStart" class="w-full bg-indigo-600 text-white py-3 rounded-lg font-bold shadow-lg hover:bg-indigo-700 transition transform active:scale-95 flex items-center justify-center">
                        <i class="fas fa-magic mr-2"></i> 开始 AI 批改
                    </button>

                    <button onclick="stopBatchGrading()" id="btnStop" class="hidden w-full bg-red-500 text-white py-3 rounded-lg font-bold shadow hover:bg-red-600 transition flex items-center justify-center">
                        <i class="fas fa-stop-circle mr-2"></i> 停止批改
                    </button>
                </div>
            </div>
        </div>

        <div id="progressPanel" class="hidden bg-white rounded-xl shadow-lg border border-indigo-100 p-6 mb-8 sticky top-20 z-30 animate-fade-in-down">
            <div class="flex justify-between items-center mb-2">
                <h4 class="font-bold text-gray-700"><i class="fas fa-sync fa-spin text-indigo-500 mr-2"></i> 正在批改中...</h4>
                <span class="text-xs font-mono text-gray-500" id="progressText">0 / 0</span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-4 mb-4 overflow-hidden">
                <div id="progressBar" class="bg-indigo-600 h-4 rounded-full progress-bar-transition" style="width: 0%"></div>
            </div>
            <div class="grid grid-cols-4 gap-4 text-center text-xs">
                <div class="bg-gray-50 p-2 rounded">
                    <span class="block text-gray-400">已处理</span>
                    <span class="font-bold text-lg text-gray-700" id="statProcessed">0</span>
                </div>
                <div class="bg-green-50 p-2 rounded">
                    <span class="block text-green-400">成功/得分</span>
                    <span class="font-bold text-lg text-green-600" id="statSuccess">0</span>
                </div>
                <div class="bg-red-50 p-2 rounded">
                    <span class="block text-red-400">异常/未交</span>
                    <span class="font-bold text-lg text-red-600" id="statError">0</span>
                </div>
                <div class="bg-blue-50 p-2 rounded">
                    <span class="block text-blue-400">当前正在处理</span>
                    <span class="font-bold truncate text-blue-600 px-1" id="statCurrent">...</span>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200" id="gradesTable">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-24">学号</th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-24">姓名</th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">得分明细 (AI 识别项)</th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider w-24">总分</th>
                            <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">自动分析报告 / 状态</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200 text-sm">
                        {% for s in students %}
                        <tr id="row-{{ s['student_id'] }}" data-student-id="{{ s['student_id'] }}" data-name="{{ s['name'] }}"
                            class="hover:bg-gray-50 transition group {{ 'bg-red-50' if s['status'] == 'MISSING' else ('bg-yellow-50' if s['status'] == 'ERROR' else '') }}">

                            <td class="px-6 py-4 font-mono text-gray-600">{{ s['student_id'] }}</td>

                            <td class="px-6 py-4 font-bold text-gray-800">
                                <a href="/grading/{{ cls['id'] }}/student/{{ s['student_id'] }}" target="_blank"
                                   class="text-blue-600 hover:text-blue-800 hover:underline flex items-center">
                                    {{ s['name'] }}
                                    <i class="fas fa-external-link-alt text-xs ml-2 opacity-0 group-hover:opacity-100 transition"></i>
                                </a>
                            </td>

                            <td class="px-6 py-4 text-gray-700 col-details">
                                {% if s['score_details'] %}
                                    <div class="flex flex-wrap">
                                        {% set details = s['score_details'] | from_json %}
                                        {% for item in details %}
                                            <div class="score-tag" title="{{ item.name }}">
                                                {{ item.name }}: <span class="val">{{ item.score }}</span>
                                            </div>
                                        {% else %}
                                            <span class="text-gray-400 text-xs">-</span>
                                        {% endfor %}
                                    </div>
                                {% else %}
                                    <span class="text-gray-400">-</span>
                                {% endif %}
                            </td>

                            <td class="px-6 py-4 col-score">
                                {% if s['total_score'] is not none %}
                                    <span class="px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full {{ 'bg-green-100 text-green-800' if s['total_score'] >= 60 else 'bg-red-100 text-red-800' }}">
                                        {{ s['total_score'] }}
                                    </span>
                                {% else %}
                                    <span class="text-gray-400">-</span>
                                {% endif %}
                            </td>

                            <td class="px-6 py-4 col-status">
                                {% if s['status'] == 'MISSING' %}
                                    <span class="text-red-500 font-bold text-xs"><i class="fas fa-exclamation-circle"></i> 未提交/无法匹配</span>
                                {% elif s['status'] == 'ERROR' %}
                                    <span class="text-orange-600 font-bold text-xs"><i class="fas fa-bug"></i> {{ s['deduct_details'] }}</span>
                                {% elif s['status'] == 'PASS' or s['status'] == 'FAIL' %}
                                    {% if s['deduct_details'] %}
                                        <div class="flex flex-wrap max-w-lg">
                                        {% for detail in s['deduct_details'].split(';') %}
                                            {% if detail.strip() %}
                                                <span class="deduct-item">{{ detail }}</span>
                                            {% endif %}
                                        {% endfor %}
                                        </div>
                                    {% else %}
                                        <span class="text-green-600 font-bold text-xs"><i class="fas fa-check-circle"></i> 完美通过</span>
                                    {% endif %}
                                {% endif %}

                                <div class="file-info text-xs text-gray-400 mt-1 truncate max-w-xs flex items-center">
                                    {% if s['filename'] %}
                                        <i class="fas fa-file-archive mr-1"></i> {{ s['filename'] }}
                                    {% endif %}
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const CLASS_ID = {{ cls['id'] }};
        let isProcessing = false;
        let stopFlag = false;

        // === 文件上传逻辑 ===
        function handleFiles(files) {
            if (files.length === 0) return;
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            const statusDiv = document.getElementById('uploadStatus');
            statusDiv.classList.remove('hidden');
            statusDiv.innerHTML = '<i class="fas fa-spinner fa-spin mr-2 text-blue-500"></i> 正在上传并建立索引...';

            fetch(`/upload_zips/${CLASS_ID}`, { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                statusDiv.innerHTML = '<span class="text-green-600 font-bold"><i class="fas fa-check"></i> 上传完成! 页面即将刷新...</span>';
                setTimeout(() => location.reload(), 1500);
            })
            .catch(err => {
                alert('上传失败: ' + err);
                statusDiv.classList.add('hidden');
            });
        }

        // === 批量批改逻辑 (解决 Gunicorn 超时问题的关键) ===
        
        async function startBatchGrading() {
            if (!confirm('【耗时预警】AI 需要仔细阅读每位同学的代码和截图。\n\n• 每个学生约耗时 30-60 秒\n• 请勿关闭此页面\n\n确定要开始吗？')) return;

            // 1. UI 初始化
            isProcessing = true;
            stopFlag = false;
            document.getElementById('btnStart').classList.add('hidden');
            document.getElementById('btnStop').classList.remove('hidden');
            document.getElementById('progressPanel').classList.remove('hidden');

            const rows = document.querySelectorAll('tr[data-student-id]');
            const total = rows.length;
            let processed = 0;
            let successCount = 0;
            let errorCount = 0;

            updateProgress(0, total);

            // 2. 遍历所有学生
            for (let i = 0; i < total; i++) {
                if (stopFlag) break;

                const row = rows[i];
                const studentId = row.dataset.studentId;
                const studentName = row.dataset.name;
                
                // 忽略已经有分数的行 (如果想强制重跑，可以去掉这个判断，或者加个 checkbox 控制)
                // const hasScore = row.querySelector('.col-score').innerText.trim() !== '-';
                // if (hasScore && !confirmRetry) continue;

                // 2.1 高亮当前行并滚动
                updateCurrentStatus(studentName, processed, total, successCount, errorCount);
                row.scrollIntoView({ behavior: "smooth", block: "center" });
                row.classList.add('row-active');
                
                // 设置行状态为 Loading
                const statusCell = row.querySelector('.col-status');
                const originalStatus = statusCell.innerHTML;
                statusCell.innerHTML = '<span class="text-indigo-600 font-bold"><i class="fas fa-spinner fa-spin"></i> AI 正在深度思考...</span>';

                try {
                    // 2.2 调用后端 API (逐个批改)
                    const response = await fetch(`/api/grade_student/${CLASS_ID}/${studentId}`, {
                        method: 'POST'
                    });
                    const resData = await response.json();

                    // 2.3 更新该行 UI
                    if (resData.status === 'success') {
                        successCount++;
                        renderSuccessRow(row, resData.data);
                    } else {
                        // 业务逻辑错误 (如未提交)
                        errorCount++;
                        renderErrorRow(row, resData.msg, resData.filename);
                    }
                } catch (err) {
                    // 网络错误
                    console.error(err);
                    errorCount++;
                    statusCell.innerHTML = `<span class="text-red-500 font-bold"><i class="fas fa-network-wired"></i> 网络超时/错误</span>`;
                }

                // 2.4 完成后处理
                row.classList.remove('row-active');
                row.classList.add('row-updated');
                processed++;
                updateProgress(processed, total);
            }

            // 3. 结束状态
            finishGrading(processed, total);
        }

        function stopBatchGrading() {
            if (confirm('确定要停止批改吗？已生成的成绩会保留。')) {
                stopFlag = true;
            }
        }

        // === 辅助渲染函数 ===

        function updateProgress(processed, total) {
            const pct = Math.round((processed / total) * 100);
            document.getElementById('progressBar').style.width = `${pct}%`;
            document.getElementById('progressText').innerText = `${processed} / ${total}`;
            document.getElementById('statProcessed').innerText = processed;
        }

        function updateCurrentStatus(name, processed, total, s, e) {
            document.getElementById('statCurrent').innerText = name;
            document.getElementById('statSuccess').innerText = s;
            document.getElementById('statError').innerText = e;
        }

        function renderSuccessRow(row, data) {
            // 更新总分
            const scoreClass = data.total_score >= 60 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
            row.querySelector('.col-score').innerHTML = `
                <span class="px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full ${scoreClass}">
                    ${data.total_score}
                </span>`;
            
            // 更新明细
            let detailsHtml = '';
            if (data.details && data.details.length > 0) {
                detailsHtml = '<div class="flex flex-wrap">';
                data.details.forEach(item => {
                    detailsHtml += `
                        <div class="score-tag" title="${item.name}">
                            ${item.name}: <span class="val">${item.score}</span>
                        </div>`;
                });
                detailsHtml += '</div>';
            } else {
                detailsHtml = '<span class="text-gray-400 text-xs">-</span>';
            }
            row.querySelector('.col-details').innerHTML = detailsHtml;

            // 更新状态
            let statusHtml = '';
            if (data.deduct) {
                statusHtml += '<div class="flex flex-wrap max-w-lg">';
                data.deduct.split(';').forEach(d => {
                    if (d.trim()) statusHtml += `<span class="deduct-item">${d}</span>`;
                });
                statusHtml += '</div>';
            } else {
                statusHtml = '<span class="text-green-600 font-bold text-xs"><i class="fas fa-check-circle"></i> 完美通过</span>';
            }
            // 文件名
            if (data.filename) {
                statusHtml += `<div class="text-xs text-gray-400 mt-1"><i class="fas fa-file-archive mr-1"></i> ${data.filename}</div>`;
            }
            row.querySelector('.col-status').innerHTML = statusHtml;
            
            // 移除之前的颜色类，添加正常背景
            row.className = row.className.replace(/bg-\w+-50/g, ''); 
        }

        function renderErrorRow(row, msg, filename) {
            row.querySelector('.col-status').innerHTML = `
                <span class="text-orange-600 font-bold text-xs"><i class="fas fa-exclamation-triangle"></i> ${msg}</span>
                ${filename ? `<div class="text-xs text-gray-400 mt-1">${filename}</div>` : ''}
            `;
            row.classList.add('bg-yellow-50');
        }

        function finishGrading(processed, total) {
            isProcessing = false;
            document.getElementById('btnStart').classList.remove('hidden');
            document.getElementById('btnStop').classList.add('hidden');
            
            const msg = stopFlag ? '批改已手动停止。' : '所有学生批改完成！';
            alert(msg + `\n共处理: ${processed}/${total}`);
            
            // 可选：完成后刷新页面以确保数据一致性，或者保留当前视图
            // location.reload(); 
        }

        // === 其他功能 ===
        function clearData() {
            if(confirm('警告：确定要清空所有成绩和已上传的文件吗？此操作无法撤销。')) {
                fetch(`/clear_data/${CLASS_ID}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => location.reload());
            }
        }

        function deleteData() {
            if(confirm('警告：确定要删除本次批改所有相关数据吗？此操作无法撤销。')) {
                fetch(`/delete_class/${CLASS_ID}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => window.location.href = '/');
            }
        }
    </script>
</body>
</html>

```