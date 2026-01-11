from grading_core.base import BaseGrader, GradingResult
import os
import re

class CentosServerConfigGrader(BaseGrader):
    ID = "centos_server_config_final_loose"
    NAME = "CentOS服务器配置与管理期末(宽松模式)"

    def grade(self, student_dir, student_info) -> GradingResult:
        # 初始化文件映射
        self.scan_files(student_dir)
        self.res = GradingResult()
        
        # --- 第一部分：基础环境配置 (30分) ---
        
        # 1.1 创建运维团队账户 (10分) - 检查 10.png
        # 宽松策略：支持 jpg, png, 以及常见的命名变体
        score_1_1 = 0
        path_10, _ = self.smart_find(
            '10.png', 
            alternatives=['10.jpg', 'user.png', 'account.png', 'ops_team.png', '截图1.png'], 
            ignore_subfixes=True
        )
        if path_10:
            score_1_1 = 10
        else:
            self.res.add_deduction("P1-未找到创建用户/组的截图(10.png)")
        self.res.add_sub_score("P1-用户与组创建", score_1_1)

        # 1.2 配置日志备份目录 (10分) - 检查 11.png
        score_1_2 = 0
        path_11, _ = self.smart_find(
            '11.png', 
            alternatives=['11.jpg', 'log.png', 'logs.png', 'dir.png', '截图2.png'], 
            ignore_subfixes=True
        )
        if path_11:
            score_1_2 = 10
        else:
            self.res.add_deduction("P1-未找到日志目录权限截图(11.png)")
        self.res.add_sub_score("P1-日志目录配置", score_1_2)

        # 1.3 简易巡检脚本 (10分) - 检查 check_server.sh 内容 + 12.png
        # 评分逻辑：脚本文件存在且内容正确给分；若脚本缺失但有执行截图，给同情分
        score_1_3 = 0
        script_path, _ = self.smart_find(
            'check_server.sh', 
            alternatives=['check.sh', 'server_check.sh', 'server.sh'], 
            ignore_subfixes=True
        )
        img_path_12, _ = self.smart_find(
            '12.png', 
            alternatives=['12.jpg', 'run.png', 'exec.png', '截图3.png'], 
            ignore_subfixes=True
        )
        
        if script_path:
            content = self.read_text_content(script_path)
            # 检查关键命令
            # df -hT (3分)
            pts_df = self.verify_command(
                content, self.res, 
                r'df\s+-[a-zA-Z]*h', # Strict: df -h...
                r'df',               # Loose: just df
                3, "P1脚本-磁盘检查"
            )
            # free -m (3分)
            pts_free = self.verify_command(
                content, self.res, 
                r'free\s+-[a-zA-Z]*m', 
                r'free', 
                3, "P1脚本-内存检查"
            )
            # echo (2分)
            pts_echo = self.verify_command(
                content, self.res, 
                r'echo', 
                None, 
                2, "P1脚本-Echo输出"
            )
            # 文件存在基础分 (2分)
            score_1_3 = 2 + pts_df + pts_free + pts_echo
        elif img_path_12:
            score_1_3 = 5
            self.res.add_deduction("P1-未找到check_server.sh脚本文件，但发现执行截图(12.png)，给予同情分5分")
        else:
            self.res.add_deduction("P1-未找到巡检脚本及执行截图")
            
        self.res.add_sub_score("P1-巡检脚本", score_1_3)


        # --- 第二部分：Staging Web服务部署 (70分) ---
        
        # 2.1 Web服务配置 (15分) - 检查 20.png
        # 包含 httpd 安装启动及 UserDir 配置
        score_2_1 = 0
        path_20, _ = self.smart_find(
            '20.png', 
            alternatives=['20.jpg', 'web.png', 'httpd.png', 'apache.png', '截图4.png'], 
            ignore_subfixes=True
        )
        if path_20:
            score_2_1 = 15
        else:
            self.res.add_deduction("P2-未找到Web服务配置截图(20.png)")
        self.res.add_sub_score("P2-Web服务配置", score_2_1)

        # 2.2 开发者测试页面 (15分) - 检查 21.png
        # 包含 UserDir 访问 (~dev_user)
        score_2_2 = 0
        path_21, _ = self.smart_find(
            '21.png', 
            alternatives=['21.jpg', 'browser.png', 'dev_page.png', 'index.png', '截图5.png'], 
            ignore_subfixes=True
        )
        if path_21:
            score_2_2 = 15
        else:
            self.res.add_deduction("P2-未找到开发者页面访问截图(21.png)")
        self.res.add_sub_score("P2-开发者页面", score_2_2)

        # 2.3 数据库部署 (25分) - 检查 22.png
        # 包含安装 MariaDB, 初始化, 创建库/用户/授权
        score_2_3 = 0
        path_22, _ = self.smart_find(
            '22.png', 
            alternatives=['22.jpg', 'db.png', 'mysql.png', 'mariadb.png', 'sql.png', '截图6.png'], 
            ignore_subfixes=True
        )
        if path_22:
            score_2_3 = 25
        else:
            self.res.add_deduction("P2-未找到数据库配置截图(22.png)")
        self.res.add_sub_score("P2-数据库部署", score_2_3)

        # 2.4 自动化备份脚本 (15分) - 检查 backup_staging.sh + 23.png
        score_2_4 = 0
        bk_script_path, _ = self.smart_find(
            'backup_staging.sh', 
            alternatives=['backup.sh', 'staging_backup.sh', 'db_backup.sh'], 
            ignore_subfixes=True
        )
        img_path_23, _ = self.smart_find(
            '23.png', 
            alternatives=['23.jpg', 'backup_exec.png', 'tar.png', '截图7.png'], 
            ignore_subfixes=True
        )

        if bk_script_path:
            content = self.read_text_content(bk_script_path)
            # mysqldump (6分)
            pts_sql = self.verify_command(
                content, self.res, 
                r'mysqldump', 
                r'mysql', # 若写错成mysql也给一半分
                6, "P2脚本-数据库备份"
            )
            # tar (6分)
            pts_tar = self.verify_command(
                content, self.res, 
                r'tar\s+.*-.*c', # 检查是否有 create 标志
                r'tar',          # 只要有 tar 命令
                6, "P2脚本-Web打包"
            )
            # echo (1分)
            pts_echo = self.verify_command(
                content, self.res, 
                r'echo', 
                None, 
                1, "P2脚本-Echo"
            )
            # 文件存在基础分 (2分)
            score_2_4 = 2 + pts_sql + pts_tar + pts_echo
        elif img_path_23:
            score_2_4 = 7
            self.res.add_deduction("P2-未找到backup_staging.sh脚本，但发现执行截图(23.png)，给予同情分7分")
        else:
            self.res.add_deduction("P2-未找到备份脚本及执行截图")

        self.res.add_sub_score("P2-备份脚本", score_2_4)

        # 汇总分数并进行边界控制
        self.res.total_score = sum([item['score'] for item in self.res.sub_scores])
        if self.res.total_score > 100:
            self.res.total_score = 100
        elif self.res.total_score < 0:
            self.res.total_score = 0
            
        return self.res