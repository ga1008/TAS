# API Contracts: 成绩导出选择弹窗

**Feature**: 004-score-export-modal
**Date**: 2026-01-26

## 1. 导出到文档库 API

### POST /api/export_to_library/{class_id}

**Description**: 将班级成绩导出为Markdown文档并存入文档库

**Authentication**: Required (session-based)

**Authorization**: 只有班级创建者可以导出

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| class_id | integer | Yes | 班级ID |

**Request Body**: None

**Response**:

#### 成功响应 (HTTP 200)

```json
{
  "status": "success",
  "msg": "成绩已导出到文档库",
  "data": {
    "asset_id": 123,
    "filename": "2025-2026学年度第一学期-Python程序设计-23级软件工程1班-机考分数.md"
  }
}
```

#### 失败响应 - 无成绩数据 (HTTP 200)

```json
{
  "status": "error",
  "msg": "暂无成绩数据可导出"
}
```

#### 失败响应 - 权限不足 (HTTP 403)

```json
{
  "status": "error",
  "msg": "无权限操作此班级"
}
```

#### 失败响应 - 班级不存在 (HTTP 404)

```json
{
  "status": "error",
  "msg": "班级不存在"
}
```

#### 失败响应 - 服务器错误 (HTTP 500)

```json
{
  "status": "error",
  "msg": "导出失败: <错误详情>"
}
```

**Example**:

```bash
curl -X POST http://localhost:5010/api/export_to_library/42 \
  -H "Cookie: session=xxx"
```

---

## 2. 直接导出 Excel (现有API，保持不变)

### GET /export/{class_id}

**Description**: 下载班级成绩Excel文件

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| class_id | integer | Yes | 班级ID |

**Response**: Excel文件下载 (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

**Note**: 此API保持现有实现不变，弹窗选择"Excel导出"时直接跳转到此URL。

---

## 3. 错误代码表

| Code | HTTP Status | Description |
|------|-------------|-------------|
| NO_GRADES | 200 | 班级没有已批改的学生成绩 |
| UNAUTHORIZED | 403 | 用户无权操作此班级 |
| NOT_FOUND | 404 | 班级不存在 |
| EXPORT_FAILED | 500 | 文档生成或保存失败 |

---

## 4. 前端调用示例

### JavaScript Fetch

```javascript
async function exportToLibrary(classId) {
    try {
        const response = await fetch(`/api/export_to_library/${classId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.status === 'success') {
            // 显示成功消息
            showMessage('success', data.msg);
            // 可选：显示文件名
            console.log('Generated:', data.data.filename);
        } else {
            // 显示错误消息
            showMessage('error', data.msg);
        }

        return data;
    } catch (error) {
        showMessage('error', '网络请求失败');
        throw error;
    }
}
```

### 导出到Excel (直接跳转)

```javascript
function exportToExcel(classId) {
    window.location.href = `/export/${classId}`;
}
```
