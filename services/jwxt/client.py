import time
import requests
from urllib.parse import urljoin
from services.jwxt.encryption import EncryptionHelper
from services.jwxt.parser import JwxtParser


class JwxtClient:
    BASE_URL = "https://jwxt.gxufl.com"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive"
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.is_logged_in = False
        self.username = None

    def login(self, username, password):
        self.username = username

        try:
            # Phase 0: 访问登录页
            login_page_url = urljoin(self.BASE_URL, "/xtgl/login_slogin.html")
            resp_0 = self.session.get(login_page_url)

            if resp_0.status_code != 200:
                return False, f"无法访问登录页 (Status: {resp_0.status_code})"

            # 解析页面参数
            meta_data = JwxtParser.parse_login_page(resp_0.text)

            # ---【新增：公钥合法性强校验】---
            # 如果解析到的值看起来是假的（例如 E=0 或 M太短），强制置空，以便触发下方 API 获取
            if meta_data['exponent'] and meta_data['exponent'] in ['0', '1']:
                print(f"[JWXT] 检测到无效指数 E={meta_data['exponent']}，丢弃。")
                meta_data['exponent'] = None

            if meta_data['modulus'] and len(meta_data['modulus']) < 20:
                print(f"[JWXT] 检测到无效模数长度 {len(meta_data['modulus'])}，丢弃。")
                meta_data['modulus'] = None
            # -------------------------------

            # 检查公钥来源 (如果 HTML 里没找到，或者被上面的校验置空了，就会进这里)
            if not meta_data['modulus'] or not meta_data['exponent']:
                print("[JWXT] 需要通过API获取公钥...")
                try:
                    key_url = urljoin(self.BASE_URL, "/xtgl/login_getPublicKey.html")
                    key_resp = self.session.get(key_url, params={'time': int(time.time() * 1000)})
                    if key_resp.status_code == 200:
                        key_data = key_resp.json()
                        meta_data['modulus'] = key_data.get('modulus')
                        meta_data['exponent'] = key_data.get('exponent')
                        print(f"[JWXT] API获取公钥成功")  # 减少日志长度，避免刷屏
                except Exception as e:
                    print(f"[JWXT] API获取公钥失败: {e}")

            # 再次检查
            if not meta_data['modulus'] or not meta_data['exponent']:
                return False, "获取RSA公钥失败 (HTML和API均未返回有效Key)"

            # 加密
            print(f"[JWXT] 开始加密密码...")
            enc_pwd = EncryptionHelper.encrypt_password(password, meta_data['modulus'], meta_data['exponent'])

            if not enc_pwd:
                return False, "密码加密失败 (请查看后端日志)"

            # Phase 1 & 2 (保持不变)
            logout_url = urljoin(self.BASE_URL, "/xtgl/login_logoutAccount.html")
            self.session.post(logout_url, data={})

            timestamp = int(time.time() * 1000)
            post_url = f"{login_page_url}?time={timestamp}"

            payload = {
                "csrftoken": meta_data['csrftoken'],
                "language": "zh_CN",
                "ydType": "ls",
                "yhm": username,
                "mm": enc_pwd
            }

            resp_2 = self.session.post(post_url, data=payload)

            # 结果判定 (增加 debug 打印)
            if "index_initMenu.html" in resp_2.url or "登录成功" in resp_2.text or "退出" in resp_2.text:
                self.is_logged_in = True
                return True, "登录成功"

            if "用户名或密码不正确" in resp_2.text:
                return False, "用户名或密码不正确"

            # 打印部分响应内容帮助调试
            print(f"[JWXT Login Fail] URL: {resp_2.url}")
            print(f"[JWXT Login Fail] Text snippet: {resp_2.text[:200]}")

            return False, "登录失败，未知原因"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"系统异常: {str(e)}"

    def get_teacher_info(self):
        """
        获取教师个人信息 (姓名、学院)
        对应提供的请求: /xtgl/index_cxYhxxIndex.html
        """
        if not self.is_logged_in:
            return None, "未登录"

        target_url = urljoin(self.BASE_URL, "/xtgl/index_cxYhxxIndex.html")
        params = {
            "xt": "jw",
            "localeKey": "zh_CN",
            "_": int(time.time() * 1000),
            "gnmkdm": "index"
        }

        try:
            resp = self.session.get(target_url, params=params)
            if resp.status_code == 200:
                info = JwxtParser.parse_user_info(resp.text)
                return info, None
            return None, f"请求失败: {resp.status_code}"
        except Exception as e:
            return None, str(e)
