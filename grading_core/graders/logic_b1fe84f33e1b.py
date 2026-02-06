from grading_core.base import BaseGrader, GradingResult
import re
import os

class ExamGrader(BaseGrader):
    ID = "logic_b1fe84f33e1b"
    NAME = "2026春-服务器配置与管理-机试批改核心"
    COURSE = "服务器配置与管理"

    def grade(self, student_dir, student_info) -> GradingResult:
        self.res = GradingResult()
        self.scan_files(student_dir)  # 扫描所有文件

        # ------------------------------
        # 第一题：基础环境配置 (总分30分)
        # ------------------------------
        task1_total = 0

        # 1.1 创建运维团队账户 (10分)
        score_1_1 = 0
        img_path, penalty = self.smart_find(
            "10.png",
            alternatives=['10.PNG', '10.jpg', '10.jpeg', '用户创建截图.png', 'task1_1.png'],
            ignore_subfixes=True
        )
        if img_path:
            score_1_1 = 10 - penalty  # 文件名不规范扣1分，宽松模式尽量给分
        else:
            self.res.add_deduction("未找到10.png或等效的运维账户创建截图，扣除10分")
        self.res.add_sub_score("1.1 创建运维团队账户", score_1_1)
        task1_total += score_1_1

        # 1.2 配置日志备份目录 (10分)
        score_1_2 = 0
        img_path, penalty = self.smart_find(
            "11.png",
            alternatives=['11.PNG', '11.jpg', '11.jpeg', '日志目录配置截图.png', 'task1_2.png'],
            ignore_subfixes=True
        )
        if img_path:
            score_1_2 = 10 - penalty
        else:
            self.res.add_deduction("未找到11.png或等效的日志目录配置截图，扣除10分")
        self.res.add_sub_score("1.2 配置日志备份目录", score_1_2)
        task1_total += score_1_2

        # 1.3 编写简易巡检脚本 (10分)
        score_1_3 = 0
        script_path, penalty = self.smart_find(
            "check_server.sh",
            alternatives=['checkserver.sh', '巡检脚本.sh', 'task1_3.sh'],
            ignore_subfixes=True
        )
        if script_path:
            content = self.read_text_content(script_path)
            # 宽松匹配关键命令：服务器检查标题、磁盘命令、内存命令
            strict_regex = r'echo.*Server Check by.*\s+df -hT\s+.*free -m'
            loose_regex = r'(echo.*Server Check|df -hT|free -m)'
            score_1_3 = self.verify_command(
                content, self.res, strict_regex, loose_regex,
                10 - penalty, "1.3 巡检脚本内容检查"
            )
        else:
            self.res.add_deduction("未找到check_server.sh或等效的巡检脚本，扣除10分")
            # 宽松模式：若有执行截图则给部分分数
            img_path, _ = self.smart_find(
                "12.png", alternatives=['12.PNG', '12.jpg', '脚本执行截图.png'], ignore_subfixes=True
            )
            if img_path:
                score_1_3 = 3
                self.res.add_deduction("未找到巡检脚本但找到执行截图，宽松给分3分")
        self.res.add_sub_score("1.3 编写简易巡检脚本", score_1_3)
        task1_total += score_1_3

        self.res.add_sub_score("第一题：基础环境配置", task1_total)

        # ------------------------------
        # 第二题：Staging环境部署 (总分70分)
        # ------------------------------
        task2_total = 0

        # 2.1 部署Staging Web服务 (30分)
        score_2_1 = 0
        # 2.1.1 Web服务配置截图 (15分)
        img20_path, penalty20 = self.smart_find(
            "20.png",
            alternatives=['20.PNG', '20.jpg', '20.jpeg', 'Web配置截图.png', 'task2_1_1.png'],
            ignore_subfixes=True
        )
        # 2.1.2 浏览器访问截图 (15分)
        img21_path, penalty21 = self.smart_find(
            "21.png",
            alternatives=['21.PNG', '21.jpg', '21.jpeg', 'Web访问截图.png', 'task2_1_2.png'],
            ignore_subfixes=True
        )
        if img20_path and img21_path:
            score_2_1 = 30 - (penalty20 + penalty21)
        elif img20_path or img21_path:
            score_2_1 = 15  # 宽松模式：找到任意一张截图给一半分
            self.res.add_deduction("Web服务部署仅找到1张截图，宽松给分15分")
        else:
            self.res.add_deduction("未找到20.png/21.png或等效的Web服务截图，扣除30分")
        self.res.add_sub_score("2.1 部署Staging Web服务", score_2_1)
        task2_total += score_2_1

        # 2.2 部署Staging数据库 (25分)
        score_2_2 = 0
        img_path, penalty = self.smart_find(
            "22.png",
            alternatives=['22.PNG', '22.jpg', '22.jpeg', '数据库操作截图.png', 'task2_2.png'],
            ignore_subfixes=True
        )
        if img_path:
            score_2_2 = 25 - penalty
        else:
            self.res.add_deduction("未找到22.png或等效的数据库部署截图，扣除25分")
        self.res.add_sub_score("2.2 部署Staging数据库", score_2_2)
        task2_total += score_2_2

        # 2.3 编写自动化备份脚本 (15分)
        score_2_3 = 0
        script_path, penalty = self.smart_find(
            "backup_staging.sh",
            alternatives=['backup.sh', '备份脚本.sh', 'task2_3.sh'],
            ignore_subfixes=True
        )
        if script_path:
            content = self.read_text_content(script_path)
            # 宽松匹配关键命令：备份开始提示、数据库备份、Web目录打包、备份完成提示
            strict_regex = r'echo.*start backup.*\s+mysqldump.*fzxy_staging_.*\s+tar.*public_html\s+.*echo.*backup finished'
            loose_regex = r'(echo.*start backup|mysqldump|tar.*public_html|echo.*backup finished)'
            score_2_3 = self.verify_command(
                content, self.res, strict_regex, loose_regex,
                15 - penalty, "2.3 备份脚本内容检查"
            )
        else:
            self.res.add_deduction("未找到backup_staging.sh或等效的备份脚本，扣除15分")
            # 宽松模式：若有执行截图则给部分分数
            img_path, _ = self.smart_find(
                "23.png", alternatives=['23.PNG', '23.jpg', '备份执行截图.png'], ignore_subfixes=True
            )
            if img_path:
                score_2_3 = 4
                self.res.add_deduction("未找到备份脚本但找到执行截图，宽松给分4分")
        self.res.add_sub_score("2.3 编写自动化备份脚本", score_2_3)
        task2_total += score_2_3

        self.res.add_sub_score("第二题：Staging环境部署", task2_total)

        # ------------------------------
        # 总分计算与及格判定
        # ------------------------------
        self.res.total_score = task1_total + task2_total
        self.res.is_pass = self.res.total_score >= 60

        return self.res