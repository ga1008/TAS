# JWXT Integration Blueprint (v2.0 Stable)

**版本**: 2.0 (2026-01-19)
**状态**: 已验证 (Production Ready)
**适用系统**: 正方教务管理系统 (ZFSoft v5/v6)

## 1. 核心架构：混合式转接器 (Hybrid Adapter)

本模块采用 **Database-Adapter Pattern**，将远程教务系统封装为本地可调用的数据服务。针对正方教务系统的反爬特性，我们实现了 **"HTML解析 + API补救"** 的混合登录策略。

### 1.1 目录结构

```text
services/
└── jwxt/
    ├── __init__.py
    ├── client.py       # [Core] 状态机与请求调度器
    ├── encryption.py   # [Crypto] RSA/Hex 加密算法库
    └── parser.py       # [ETL] HTML 清洗与数据提取器
blueprints/
└── jwxt.py             # [Controller] HTTP 接口暴露

```

## 2. 关键技术规范 (Must Follow)

在开发新功能时，必须严格遵守以下规范，否则会导致连接失败。

### 2.1 加密标准 (Encryption)

* **算法**: RSA (PKCS1_v1_5)
* **公钥格式**: **16进制字符串 (Hex String)**。
* *严禁* 将 Modulus/Exponent 当作 Base64 处理，这是旧版逻辑，新版会导致长度校验错误。


* **依赖库**: `pycryptodome` (用于 RSA), `binascii` (用于 Hex/Bytes 转换)。

### 2.2 公钥获取策略 (Dynamic Key Fetching)

正方系统公钥分发存在两种模式，Client 必须同时兼容：

1. **静态模式**: 公钥直接渲染在 `login_slogin.html` 的隐藏域中。
2. **动态模式**: 隐藏域为空或包含无效值（如 `E=0`），需请求 `/xtgl/login_getPublicKey.html` 获取。

* **实现原则**: 优先解析 HTML -> 校验合法性 (E!=0, M长度>20) -> 校验失败则 fallback 请求 API。

### 2.3 HTML 解析规则 (Parsing)

* **ID 选择器**: 严禁使用单字母 ID（如 `id="M"`, `id="E"`）查找元素，极易命中页面中的干扰项。必须使用全称 `modulus` / `exponent`。
* **容错**: 同时查找 `id` 和 `name` 属性。

## 3. 标准登录流程 (Login Flow)

所有受保护的操作（查询/提交）前，必须确保 `JwxtClient` 处于 `is_logged_in = True` 状态。

1. **Phase 0 (Init)**: GET `/xtgl/login_slogin.html`
* 获取 `csrftoken`。
* 尝试解析 `modulus`, `exponent`。


2. **Phase 0.5 (Key Rescue)**: **[关键步骤]**
* 如果 HTML 中公钥缺失或无效，GET `/xtgl/login_getPublicKey.html?time={ts}`。
* 更新 Client 内部的公钥参数。


3. **Phase 1 (Pre-flight)**: POST `/xtgl/login_logoutAccount.html`
* 清除服务端旧 Session，防止串号。


4. **Phase 2 (Auth)**: POST `/xtgl/login_slogin.html?time={ts}`
* Payload: `yhm`, `mm` (RSA-Hex-Base64 Encrypted), `csrftoken`。
* 验证: 检查响应 URL 是否包含 `index_initMenu` 或响应体包含 "登录成功"。



## 4. 功能扩展指南 (Extension Guide)

### 场景 A: 获取课表 (Schedule)

1. **抓包**: 登录教务系统，点击“课表查询”，记录 URL（通常是 `/kbcx/xskbcx_cxXsKb.html`）。
2. **解析 (`parser.py`)**:
```python
def parse_schedule(html):
    # 使用 BeautifulSoup 定位表格 #kbgrid
    # 遍历 tr/td，提取课程名、地点、时间
    return structured_data

```


3. **客户端 (`client.py`)**:
```python
def get_student_schedule(self, xnm, xqm):
    # xnm: 学年 (2024), xqm: 学期 (3/12/16)
    url = urljoin(self.BASE_URL, "/kbcx/xskbcx_cxXsKb.html")
    data = {"xnm": xnm, "xqm": xqm}
    resp = self.session.post(url, data=data) # 注意课表通常是 POST
    return JwxtParser.parse_schedule(resp.text)

```



### 场景 B: 获取成绩 (Grades)

* **注意**: 成绩查询通常需要特定的 `gnmkdm` (功能模块代码) 参数，该参数在点击菜单时由前端生成。
* **技巧**: 必须带上 Referer 头，且 `User-Agent` 必须保持一致。

## 5. 异常处理与调试

* **Crypto Error**: 通常是公钥无效。检查日志中 `M=` 和 `E=` 的打印值。
* **302 Redirect**: `requests.Session` 会自动处理，但在判断登录成功时，需检查 `resp.url` 是否发生了变化。
* **Session 失效**: 教务系统 Session 超时较快（约 15-30 分钟）。建议每次用户操作前先检查 Session 有效性，或者采用“每次操作都重新登录”的无状态策略（当前实现方案）。

---