# blueprints/student.py
import traceback

from flask import Blueprint, render_template, request, jsonify, g

from extensions import db
from services.ai_service import AiService
from services.file_service import FileService
from utils.common import calculate_file_hash, create_text_asset

bp = Blueprint('student', __name__, url_prefix='/student')


# === 页面路由 (Page Routes) ===

@bp.route('/')
def list_page():
    """1. 学生名单列表页"""
    if not g.user: return render_template('auth/login.html')
    return render_template('student/list.html', user=g.user)


@bp.route('/import')
def import_page():
    """2. 导入向导页"""
    if not g.user: return render_template('auth/login.html')
    return render_template('student/import.html', user=g.user)


@bp.route('/detail/<int:list_id>')
def detail_page(list_id):
    """3. 班级详情管理页"""
    if not g.user: return render_template('auth/login.html')
    # 校验权限
    sl_record = db.get_connection().execute("SELECT * FROM student_lists WHERE id=?", (list_id,)).fetchone()
    if not sl_record:
        return "班级不存在", 404
    # 简单的权限校验
    # if int(sl_record['uploaded_by']) != int(g.user['id']) and not g.user.get('is_admin'):
    #     return "无权访问", 403

    return render_template('student/detail.html', list_id=list_id, user=g.user)


# === API 接口 (API Endpoints) ===

@bp.route('/api/list')
def api_list():
    """获取班级列表数据 (带权限控制)"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    search = request.args.get('search', '').strip()

    # 核心修复 1: 传入 fetch_all=True，获取数据库中所有班级，解决列表空白问题
    raw_lists = db.get_student_lists(fetch_all=True)

    result = []
    user_id = g.user['id']
    is_admin = g.user.get('is_admin', False)

    for item in raw_lists:
        # 模糊搜索过滤
        if search:
            search_lower = search.lower()
            if (search_lower not in (item.get('class_name') or '').lower() and
                    search_lower not in (item.get('college') or '').lower()):
                continue

        # 核心修复 2: 权限计算逻辑
        # 规则1: 管理员拥有所有权限
        # 规则2: 自己创建的拥有所有权限
        # 规则3: 别人的只能看，不能改/删
        is_owner = int(item.get('uploaded_by', 0)) == int(user_id)

        can_manage = is_admin or is_owner  # 是否有管理权(删改)

        result.append({
            "id": item['id'],
            "class_name": item['class_name'] or "未命名班级",
            "student_count": item['student_count'],
            "college": item['college'] or "",
            "created_at": item['created_at'],
            "uploader": item.get('uploader_name', '未知'),
            "is_owner": is_owner,  # 用于前端展示"我"的标记
            "can_manage": can_manage  # 用于前端控制按钮显示
        })

    return jsonify({"status": "success", "data": result})


@bp.route('/api/upload_parse', methods=['POST'])
def api_upload_parse():
    """处理上传/粘贴并解析为预览数据"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    f = request.files.get('file')
    content = request.form.get('content')  # 用于粘贴板

    file_id = None

    try:
        # 场景A: 文件上传
        if f:
            path, _ = FileService.handle_file_upload_or_reuse(f, None, g.user['id'])
            with open(path, 'rb') as f_stream:
                f_hash = calculate_file_hash(f_stream)
            record = db.get_file_by_hash(f_hash)
            file_id = record['id']

        # 场景B: 文本粘贴
        elif content:
            title = "Pasted_Student_List"
            file_id, _ = create_text_asset(content, title, g.user['id'])

        if not file_id:
            return jsonify({"msg": "未接收到有效数据"}), 400

        # 调用 AI 解析服务
        success, data, error_msg = AiService.parse_student_list_dedicated(file_id)

        if not success:
            return jsonify({"status": "error", "msg": error_msg})

        return jsonify({
            "status": "success",
            "file_id": file_id,
            "preview_data": data  # 包含 students 和 metadata
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "msg": str(e)}), 500


@bp.route('/api/confirm_create', methods=['POST'])
def api_confirm_create():
    """确认创建班级"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401
    data = request.json or {}

    file_id = data.get('file_id')
    metadata = data.get('metadata', {})
    students = data.get('students', [])

    if not file_id or not metadata.get('class_name'):
        return jsonify({"msg": "缺少必要信息"}), 400

    try:
        # 1. 创建班级记录
        list_id = db.save_student_list(
            file_asset_id=file_id,
            class_name=metadata.get('class_name'),
            college=metadata.get('college', ''),
            department=metadata.get('department', ''),
            enrollment_year=metadata.get('enrollment_year', ''),
            education_type=metadata.get('education_type', '普本'),
            student_count=len(students),
            has_gender=metadata.get('has_gender', False),
            user_id=g.user['id']
        )

        # 2. 批量写入学生
        # 简单循环写入，生产环境可优化为 batch insert
        for s in students:
            db.add_student_detail(
                student_list_id=list_id,
                student_id=s.get('student_id'),
                name=s.get('name'),
                gender=s.get('gender', ''),
                phone=s.get('phone', ''),
                email=s.get('email', '')
            )

        return jsonify({"status": "success", "msg": "班级创建成功", "list_id": list_id})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500
    finally:
        # 刷新 AI 欢迎语缓存（在用户导入学生后）
        if g.user:
            try:
                from services.ai_content_service import invalidate_cache
                invalidate_cache(g.user['id'], 'student_list')
            except Exception as e:
                print(f"[AI Welcome] Cache refresh failed: {e}")


@bp.route('/api/detail/<int:list_id>')
def api_get_detail(list_id):
    """获取详情 (带权限控制)"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    sl_record = db.get_connection().execute("SELECT * FROM student_lists WHERE id=?", (list_id,)).fetchone()
    if not sl_record: return jsonify({"msg": "Not Found"}), 404

    # 计算权限
    is_admin = g.user.get('is_admin', False)
    is_owner = int(sl_record['uploaded_by']) == int(g.user['id'])
    info = dict(sl_record)
    info['uploader_name'] = db.get_user_by_id(sl_record['uploaded_by'])['username']
    can_manage = is_admin or is_owner

    # 规则3: 所有人都可以查看详情，所以这里不再拦截 403，而是返回 can_manage 标记

    students = db.get_student_details(list_id)

    return jsonify({
        "status": "success",
        "info": info,
        "students": students,
        "permissions": {
            "can_manage": can_manage
        }
    })


@bp.route('/api/student/<int:student_db_id>', methods=['PUT', 'DELETE'])
def api_student_crud(student_db_id):
    """学生数据的修改与删除 (严格权限验证)"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    # 1. 获取学生信息以找到所属班级
    conn = db.get_connection()
    student_rec = conn.execute("SELECT * FROM student_details WHERE id=?", (student_db_id,)).fetchone()
    if not student_rec: return jsonify({"msg": "记录不存在"}), 404

    list_id = student_rec['student_list_id']
    list_rec = conn.execute("SELECT * FROM student_lists WHERE id=?", (list_id,)).fetchone()
    if not list_rec: return jsonify({"msg": "关联班级异常"}), 404

    # 2. 权限验证
    is_admin = g.user.get('is_admin', False)
    is_owner = int(list_rec['uploaded_by']) == int(g.user['id'])

    # 如果不是管理员且不是班级创建者，则禁止修改
    if not (is_admin or is_owner):
        return jsonify({"status": "error", "msg": "您没有权限修改此班级的数据"}), 403

    if request.method == 'DELETE':
        try:
            db.delete_student_detail(student_db_id)
            # 更新人数计数
            new_count = len(db.get_student_details(list_id))
            conn.execute("UPDATE student_lists SET student_count=? WHERE id=?", (new_count, list_id))
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500

    if request.method == 'PUT':
        data = request.json
        try:
            # 完整性更新逻辑
            db.update_student_detail(
                detail_id=student_db_id,
                student_id=data.get('student_id', student_rec['student_id']),
                name=data.get('name', student_rec['name']),
                gender=data.get('gender', student_rec['gender']),
                email=data.get('email', student_rec['email']),
                phone=data.get('phone', student_rec['phone']),
                status=student_rec['status']  # 保持原状态
            )
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "msg": str(e)}), 500


@bp.route('/api/delete_class/<int:list_id>', methods=['POST'])
def api_delete_class(list_id):
    """删除班级 (严格权限验证)"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    list_rec = db.get_connection().execute("SELECT * FROM student_lists WHERE id=?", (list_id,)).fetchone()
    if not list_rec: return jsonify({"msg": "记录不存在"}), 404

    is_admin = g.user.get('is_admin', False)
    is_owner = int(list_rec['uploaded_by']) == int(g.user['id'])

    if not (is_admin or is_owner):
        return jsonify({"status": "error", "msg": "您没有权限删除此班级"}), 403

    try:
        db.delete_student_list(list_id)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500


@bp.route('/api/class/<int:list_id>', methods=['PUT'])
def api_update_class_info(list_id):
    """更新班级元数据 (班级名、学院、系部、年份)"""
    if not g.user: return jsonify({"msg": "Unauthorized"}), 401

    # 1. 获取班级信息并校验权限
    conn = db.get_connection()
    list_rec = conn.execute("SELECT * FROM student_lists WHERE id=?", (list_id,)).fetchone()
    if not list_rec: return jsonify({"msg": "班级不存在"}), 404

    is_admin = g.user.get('is_admin', False)
    is_owner = int(list_rec['uploaded_by']) == int(g.user['id'])

    if not (is_admin or is_owner):
        return jsonify({"status": "error", "msg": "无权修改此班级信息"}), 403

    # 2. 执行更新
    data = request.json
    try:
        sql = '''
              UPDATE student_lists
              SET class_name      = ?, \
                  college         = ?, \
                  department      = ?, \
                  enrollment_year = ?
              WHERE id = ? \
              '''
        conn.execute(sql, (
            data.get('class_name'),
            data.get('college'),
            data.get('department'),
            data.get('enrollment_year'),
            list_id
        ))
        conn.commit()
        return jsonify({"status": "success", "msg": "班级信息已更新"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500
