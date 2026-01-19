import os
import re
from grading_core.base import BaseGrader, GradingResult


class ServerConfigGrader(BaseGrader):
    ID = "server_config_2025"
    NAME = "服务器配置与管理考试"

    COURSE = "服务器配置与管理"

    def grade(self, student_dir, student_info) -> GradingResult:
        self.res = GradingResult()
        self.student_name = student_info.get('name', '')
        self.student_id = student_info.get('sid', '')

        # --- 初始化扣分池 ---
        # 结构分单独计算，最多扣5分
        self.structure_penalty = 0

        # --- 1. 智能文件定位 ---
        # 扫描整个目录建立索引，解决层级过深或命名大小写问题
        self.file_map = self._scan_all_files(student_dir)

        # 检查是否按要求分了 test1 和 test2 文件夹 (结构分)
        # 即使没分文件夹，只要文件能找到，我们依然批改内容，只是扣结构分
        has_test1 = any('test1' in path for path in self.file_map.values())
        has_test2 = any('test2' in path for path in self.file_map.values())
        if not (has_test1 and has_test2):
            self.structure_penalty += 3
            self.res.add_deduction("文档结构:未按test1/test2分类存放(-3)")

        # ==========================
        # 第一部分：基础环境配置 (30分)
        # ==========================
        self._grade_task1()

        # ==========================
        # 第二部分：Staging环境部署 (70分)
        # ==========================
        self._grade_task2()

        # ==========================
        # 分数汇总
        # ==========================
        # 总扣分不能超过该项总分，且结构扣分最后统一结算
        total = self.res.task1_score + self.res.task2_score - self.structure_penalty
        self.res.total_score = max(0, total)  # 兜底不出现负分
        self.res.is_pass = self.res.total_score >= 60

        return self.res

    # --------------------------------------------------------------------------
    # 核心逻辑方法
    # --------------------------------------------------------------------------

    def _grade_task1(self):
        """批改 Task 1: 基础环境 (30分)"""
        score = 0

        # 1. 账户截图 (10分) - 10.png
        # 策略：只要找到文件给10分，如果命名大小写错误扣1分
        file_10, penalty = self._smart_find('10.png', ignore_subfixes=True)
        if file_10:
            score += 10
            if penalty > 0:
                self.res.add_deduction(f"10.png命名或位置不规范(-{penalty})")
                score -= penalty
        else:
            self.res.add_deduction("T1:缺少用户创建截图 10.png (-10)")

        # 2. 目录权限截图 (10分) - 11.png
        file_11, penalty = self._smart_find('11.png', ignore_subfixes=True)
        if file_11:
            score += 10
            if penalty > 0:
                self.res.add_deduction(f"11.png命名或位置不规范(-{penalty})")
                score -= penalty
        else:
            self.res.add_deduction("T1:缺少权限截图 11.png (-10)")

        # 3. 巡检脚本 (10分) - check_server.sh + 12.png
        # 策略：脚本代码分析(8分) + 执行截图(2分)
        script_file, s_penalty = self._smart_find('check_server.sh', ['check_server.txt'])  # 允许学生误存为txt

        script_score = 0
        if script_file:
            # 读取内容
            content = self._read_text_content(script_file)
            if not content:
                self.res.add_deduction("T1:check_server.sh 文件为空或无法读取(-8)")
            else:
                # === 双重验证逻辑 ===
                # 检查点1: df -hT (3分)
                # 严格: df -hT (忽略空格) | 宽容: 只要有 df
                s1 = self._verify_command(content,
                                          strict_regex=r'df\s+-[a-zA-Z]*h[a-zA-Z]*T',
                                          loose_regex=r'\bdf\b',
                                          full_pts=3, name="磁盘检查(df)")
                script_score += s1

                # 检查点2: free -m (3分)
                s2 = self._verify_command(content,
                                          strict_regex=r'free\s+-[a-zA-Z]*m',
                                          loose_regex=r'\bfree\b',
                                          full_pts=3, name="内存检查(free)")
                script_score += s2

                # 检查点3: echo输出 (2分)
                # 只要有 echo 即可，不强制要求打印姓名，因为那是为了截图用的
                s3 = self._verify_command(content,
                                          strict_regex=r'\becho\b',
                                          loose_regex=None,
                                          full_pts=2, name="信息输出(echo)")
                script_score += s3

                if s_penalty > 0:
                    self.res.add_deduction(f"脚本命名或位置不规范(-{s_penalty})")
                    script_score = max(0, script_score - s_penalty)
        else:
            self.res.add_deduction("T1:缺少脚本 check_server.sh (-8)")

        score += script_score

        # 截图 12.png (2分)
        file_12, _ = self._smart_find('12.png', ignore_subfixes=True)
        if file_12:
            score += 2
        else:
            self.res.add_deduction("T1:缺少执行截图 12.png (-2)")

        self.res.task1_score = max(0, score)

    def _grade_task2(self):
        """批改 Task 2: Staging部署 (70分)"""
        score = 0

        # 1. Web服务配置截图 (15分) - 20.png
        file_20, penalty = self._smart_find('20.png', ignore_subfixes=True)
        if file_20:
            score += 15
            if penalty: score -= penalty
        else:
            self.res.add_deduction("T2:缺少Web配置截图 20.png (-15)")

        # 2. 网页访问截图 (15分) - 21.png
        file_21, penalty = self._smart_find('21.png', ignore_subfixes=True)
        if file_21:
            score += 15
            if penalty: score -= penalty
        else:
            self.res.add_deduction("T2:缺少网页访问截图 21.png (-15)")

        # 3. 数据库授权截图 (25分) - 22.png
        # 这是一个高风险项，学生很容易忘。
        file_22, penalty = self._smart_find('22.png', ignore_subfixes=True)
        if file_22:
            score += 25
            if penalty: score -= penalty
        else:
            self.res.add_deduction("T2:缺少数据库授权截图 22.png (-25)")

        # 4. 备份脚本 (15分) - backup_staging.sh + 23.png
        # 策略：脚本内容(10分) + 截图(5分)
        script_file, s_penalty = self._smart_find('backup_staging.sh', ['backup.sh', 'backup_db.sh'])  # 宽容命名

        script_score = 0
        if script_file:
            content = self._read_text_content(script_file)
            if not content:
                self.res.add_deduction("T2:备份脚本为空(-10)")
            else:
                # 检查点1: mysqldump (5分)
                # 严格: mysqldump (通常需要 -u -p，但学生可能用 .my.cnf，所以只要有命令就算对)
                # 宽容: 拼写错误如 msqldump (给1分辛苦分)
                s1 = self._verify_command(content,
                                          strict_regex=r'\bmysqldump\b',
                                          loose_regex=r'sql.*dump',
                                          full_pts=5, name="数据库备份命令")
                script_score += s1

                # 检查点2: tar 打包 (5分)
                # 严格: tar -zcvf 或 tar -czvf 等组合
                # 宽容: 只有 tar
                s2 = self._verify_command(content,
                                          strict_regex=r'\btar\s+-[a-zA-Z]*c',  # 必须有 c (create) 参数
                                          loose_regex=r'\btar\b',
                                          full_pts=5, name="文件打包命令")
                script_score += s2

                if s_penalty > 0:
                    self.res.add_deduction(f"备份脚本命名不规范(-{s_penalty})")
                    script_score = max(0, script_score - s_penalty)
        else:
            self.res.add_deduction("T2:缺少备份脚本 backup_staging.sh (-10)")

        score += script_score

        # 截图 23.png (5分)
        file_23, _ = self._smart_find('23.png', ignore_subfixes=True)
        if file_23:
            score += 5
        else:
            self.res.add_deduction("T2:缺少备份结果截图 23.png (-5)")

        self.res.task2_score = max(0, score)

    # --------------------------------------------------------------------------
    # 智能辅助工具 (Smart Utils)
    # --------------------------------------------------------------------------

    def _scan_all_files(self, root_dir):
        """
        全盘扫描，建立 {文件名(小写): 绝对路径} 的映射
        用于解决大小写敏感和深层嵌套问题
        """
        file_map = {}
        for root, _, files in os.walk(root_dir):
            for f in files:
                # 统一转小写作为 Key，但 Value 存真实路径
                file_map[f.lower()] = os.path.join(root, f)
        return file_map

    def _smart_find(self, target_filename, alternatives=None, ignore_subfixes=False):
        """
        智能查找文件
        :param target_filename: 目标文件名 (如 10.png)
        :param alternatives: 允许的替代文件名列表 (如 ['10-1.png'])
        :param ignore_subfixes: 是否忽略后缀大小写检测
        :return: (file_path, penalty_score)
        """
        penalty = 0
        target_lower = target_filename.lower()

        # 1. 精确/忽略大小写匹配
        if target_lower in self.file_map:
            # 检查是否大小写完全一致 (Linux敏感)
            real_path = self.file_map[target_lower]
            real_name = os.path.basename(real_path)
            if not ignore_subfixes and real_name != target_filename:
                penalty = 1  # 大小写不对，扣1分警告
            return real_path, penalty

        # 2. 替代名匹配 (宽容模式)
        if alternatives:
            for alt in alternatives:
                if alt.lower() in self.file_map:
                    return self.file_map[alt.lower()], 1  # 用了别名，扣1分

        return None, 0

    def _read_text_content(self, file_path):
        """健壮的文本读取，处理编码问题"""
        encodings = ['utf-8', 'gbk', 'cp936', 'latin-1']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.read()
            except:
                continue
        return None

    def _verify_command(self, content, strict_regex, loose_regex, full_pts, name):
        """
        双重验证引擎
        :param strict_regex: 严格匹配正则 (满分)
        :param loose_regex: 宽容匹配正则 (50%分)
        :return: 得分
        """
        # 1. 严格匹配
        if re.search(strict_regex, content, re.IGNORECASE | re.MULTILINE):
            return full_pts

        # 2. 宽容匹配 (如果提供了)
        if loose_regex and re.search(loose_regex, content, re.IGNORECASE | re.MULTILINE):
            half_pts = max(1, full_pts // 2)
            self.res.add_deduction(f"{name}:命令不完整或参数有误(得{half_pts}分)")
            return half_pts

        # 3. 失败
        self.res.add_deduction(f"{name}:未检测到有效命令(-{full_pts})")
        return 0