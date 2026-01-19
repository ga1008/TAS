import re

from bs4 import BeautifulSoup


class JwxtParser:
    @staticmethod
    def parse_login_page(html_content):
        """
        从登录页解析必要的参数：CSRF Token, RSA Keys
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {}

        def find_hidden_value(keys):
            if isinstance(keys, str): keys = [keys]
            for key in keys:
                # 1. 尝试通过 ID 查找 (精确匹配)
                tag = soup.find('input', id=key)
                if tag and tag.get('value'): return tag['value']

                # 2. 尝试通过 Name 查找
                tag = soup.find('input', attrs={'name': key})
                if tag and tag.get('value'): return tag['value']
            return None

        # 查找 csrftoken
        data['csrftoken'] = find_hidden_value(['csrftoken', 'csrf_token'])

        # 查找 RSA 公钥参数
        # 【关键修改】去掉了 'M'和'E'，防止匹配到页面其他 id="m" 的无关元素
        data['modulus'] = find_hidden_value(['modulus'])
        data['exponent'] = find_hidden_value(['exponent'])

        return data

    @staticmethod
    def parse_user_info(html_content):
        """
        解析个人信息页 (index_cxYhxxIndex.html)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        info = {
            "name": "未知",
            "role": "",
            "college": "未知",
            "avatar_url": ""
        }

        # 1. 解析姓名和角色
        # 结构示例: <h4 class="media-heading">张三&nbsp;&nbsp;教师</h4>
        heading = soup.find('h4', class_='media-heading')
        if heading:
            # 获取文本并清理空白字符 (包括 &nbsp; \xa0)
            text = heading.get_text(strip=True)
            # 替换常见的空白符并分割
            parts = re.split(r'\s+|&nbsp;|\xa0', text)
            parts = [p for p in parts if p]  # 过滤空串

            if len(parts) > 0: info['name'] = parts[0]
            if len(parts) > 1: info['role'] = parts[1]

        # 2. 解析学院
        # 结构示例: <div class="media-body"> ... <p>数字科技学院</p> ... </div>
        media_body = soup.find('div', class_='media-body')
        if media_body:
            # 通常学院在第一个 p 标签中
            p_tags = media_body.find_all('p')
            for p in p_tags:
                txt = p.get_text(strip=True)
                # 简单判断：如果不是空且不是class="fs1"这种辅助标签
                if txt and not p.get('class'):
                    info['college'] = txt
                    break

        # 3. 解析头像
        img = soup.find('img', class_='media-object')
        if img:
            src = img.get('src', '')
            if src:
                # 补全相对路径
                if src.startswith('/'):
                    # 这里的域名需要和 Client 中保持一致，或者由 Client 处理
                    info['avatar_url'] = src
                else:
                    info['avatar_url'] = src

        return info