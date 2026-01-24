import os
import re
import json
from grading_core.base import BaseGrader, GradingResult

class LinuxFinalExamGrader(BaseGrader):
    ID = "linux_final_2026_std"
    NAME = "Linux期末考核(标准模式)"

    def grade(self, student_dir, student_info) -> GradingResult:
        self.res = GradingResult()
        self.scan_files(student_dir)

        # =========================================================
        # 第一部分：基础环境配置 (共30分)
        # =========================================================
        
        # 1.1 运维团队账户截图 (10分)
        # 要求：10.png (展示uid, gid ops_team)
        s1_1 = 0
        path_10, pen_10 = self.smart_find("10.png")
        if path_10:
            s1_1 = 10 - pen_10
        else:
            self.res.add_deduction("缺失基础环境配置截图 10.png")
        self.res.add_sub_score("Task 1.1: 用户组配置截图", s1_1)

        # 1.2 日志备份目录截图 (10分)
        # 要求：11.png (展示 /data/app_logs/fzxy 权限770)
        s1_2 = 0
        path_11, pen_11 = self.smart_find("11.png")
        if path_11:
            s1_2 = 10 - pen_11
        else:
            self.res.add_deduction("缺失日志目录配置截图 11.png")
        self.res.add_sub_score("Task 1.2: 目录权限截图", s1_2)

        # 1.3 简易巡检脚本 (10分)
        # 要求：check_server.sh (df -hT, free -m) + 12.png
        s1_3 = 0
        # A. 检查脚本内容 (6分)
        script_path, script_pen = self.smart_find("check_server.sh", alternatives=["check.sh"])
        if script_path:
            content = self.read_text_content(script_path)
            # 扣除命名不规范分
            s1_3 -= script_pen 
            
            # 检查 df -hT
            s1_3 += self.verify_command(
                content, self.res, 
                strict_regex=r"df\s+-[a-zA-Z]*h[a-zA-Z]*", # 匹配包含h参数的df
                loose_regex=r"df", 
                full_pts=2, 
                name="巡检脚本-磁盘查看"
            )
            # 检查 free -m
            s1_3 += self.verify_command(
                content, self.res, 
                strict_regex=r"free\s+-m", 
                loose_regex=r"free", 
                full_pts=2, 
                name="巡检脚本-内存查看"
            )
            # 检查 echo 输出
            if re.search(r"echo.*Server Check", content, re.IGNORECASE):
                s1_3 += 2
            else:
                self.res.add_deduction("巡检脚本缺少指定 echo 标题")
        else:
            self.res.add_deduction("缺失巡检脚本 check_server.sh")

        # B. 检查执行截图 (4分)
        path_12, pen_12 = self.smart_find("12.png")
        if path_12:
            s1_3 += (4 - pen_12)
        else:
            self.res.add_deduction("缺失脚本执行截图 12.png")
        
        self.res.add_sub_score("Task 1.3: 巡检脚本与执行", max(0, s1_3))


        # =========================================================
        # 第二部分：Staging Web服务部署 (30分)
        # =========================================================

        # 2.1 配置Web服务截图 (15分)
        # 要求：20.png (httpd安装启动，UserDir开启)
        s2_1 = 0
        path_20, pen_20 = self.smart_find("20.png")
        if path_20:
            s2_1 = 15 - pen_20
        else:
            self.res.add_deduction("缺失Web服务配置截图 20.png")
        self.res.add_sub_score("Task 2.1: Web服务配置截图", s2_1)

        # 2.2 开发者页面测试截图 (15分)
        # 要求：21.png (浏览器访问 /~dev_xxx)
        s2_2 = 0
        path_21, pen_21 = self.smart_find("21.png")
        if path_21:
            s2_2 = 15 - pen_21
        else:
            self.res.add_deduction("缺失Web页面访问截图 21.png")
        self.res.add_sub_score("Task 2.2: Web页面访问截图", s2_2)


        # =========================================================
        # 第三部分：Staging 数据库部署 (25分)
        # =========================================================

        # 2.3 数据库配置与授权 (25分)
        # 要求：22.png (创建库，创建用户，授权)
        s2_3 = 0
        path_22, pen_22 = self.smart_find("22.png")
        if path_22:
            s2_3 = 25 - pen_22
        else:
            self.res.add_deduction("缺失数据库配置截图 22.png")
        self.res.add_sub_score("Task 2.3: 数据库配置截图", s2_3)


        # =========================================================
        # 第四部分：自动化备份脚本 (15分)
        # =========================================================
        
        # 2.4 备份脚本 (15分)
        # 要求：backup_staging.sh (mysqldump, tar) + 23.png
        s2_4 = 0
        
        # A. 检查脚本内容 (10分)
        bk_script_path, bk_pen = self.smart_find("backup_staging.sh", alternatives=["backup.sh"])
        if bk_script_path:
            content = self.read_text_content(bk_script_path)
            s2_4 -= bk_pen # 扣除命名分

            # 检查 mysqldump (4分)
            s2_4 += self.verify_command(
                content, self.res,
                strict_regex=r"mysqldump.*fzxy_staging", 
                loose_regex=r"mysqldump",
                full_pts=4,
                name="备份脚本-DB备份"
            )

            # 检查 tar 压缩 (4分)
            # 严格匹配：tar 后面跟 c (create) 和 z (gzip)，且处理 public_html
            s2_4 += self.verify_command(
                content, self.res,
                strict_regex=r"tar\s+-[a-zA-Z]*c[a-zA-Z]*z.*public_html",
                loose_regex=r"tar",
                full_pts=4,
                name="备份脚本-Web打包"
            )

            # 检查 echo start/finish (2分)
            if re.search(r"echo", content):
                s2_4 += 2
            else:
                self.res.add_deduction("备份脚本缺少 echo 提示信息")
        else:
            self.res.add_deduction("缺失备份脚本 backup_staging.sh")

        # B. 检查执行截图 (5分)
        path_23, pen_23 = self.smart_find("23.png")
        if path_23:
            s2_4 += (5 - pen_23)
        else:
            self.res.add_deduction("缺失备份脚本执行截图 23.png")

        self.res.add_sub_score("Task 2.4: 备份脚本与执行", max(0, s2_4))

        # =========================================================
        # 汇总
        # =========================================================
        self.res.total_score = s1_1 + s1_2 + s1_3 + s2_1 + s2_2 + s2_3 + s2_4
        # 满分 100， 60分及格
        self.res.is_pass = self.res.total_score >= 60
        
        return self.res