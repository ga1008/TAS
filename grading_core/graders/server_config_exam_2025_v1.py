import os
import re
import json
import abc
from grading_core.base import BaseGrader, GradingResult

class ServerConfigExamGrader(BaseGrader):
    ID = "server_config_exam_2025_v1"
    NAME = "服务器配置与管理期末(宽松模式)"

    COURSE = "服务器配置与管理"
    
    def grade(self, student_dir, student_info) -> GradingResult:
        """主评分函数"""
        # 初始化结果对象
        self.res = GradingResult()
        
        # 扫描学生目录中的所有文件
        self.scan_files(student_dir)
        
        # 第一部分：基础环境配置 (30分)
        self._grade_part1(student_dir)
        
        # 第二部分：Staging Web服务部署 (70分)
        self._grade_part2(student_dir)
        
        # 计算总分
        total = sum(sub["score"] for sub in self.res.sub_scores)
        self.res.total_score = min(total, 100)  # 确保不超过100分
        self.res.is_pass = self.res.total_score >= 60
        
        return self.res
    
    def _grade_part1(self, student_dir):
        """评分第一部分：基础环境配置 (30分)"""
        task_score = 0
        
        # 检查test1目录是否存在
        test1_path = os.path.join(student_dir, "test1")
        if not os.path.exists(test1_path):
            self.res.add_sub_score("Part1_目录结构", 0)
            self.res.add_deduction("test1目录不存在")
            return
        
        # Task 1.1: 创建运维团队账户 (10分)
        task1_score = 10
        file1_path, penalty1 = self.smart_find(
            "10.png", 
            alternatives=["10_1.png", "10-1.png", "1_10.png", "task1.png", "用户创建.png"],
            ignore_subfixes=True
        )
        if file1_path:
            content = self.read_text_content(file1_path)
            # 宽松检查：只要文件存在就基本给分
            if content:
                task1_score -= penalty1
                if penalty1:
                    self.res.add_deduction("Task1.1文件名不规范")
            else:
                task1_score -= 2  # 文件为空或无法读取
                self.res.add_deduction("Task1.1截图文件无法读取")
        else:
            task1_score = 0
            self.res.add_deduction("Task1.1截图缺失")
        
        task_score += task1_score
        
        # Task 1.2: 配置日志备份目录 (10分)
        task2_score = 10
        file2_path, penalty2 = self.smart_find(
            "11.png",
            alternatives=["11_1.png", "11-1.png", "1_11.png", "task2.png", "日志目录.png"],
            ignore_subfixes=True
        )
        if file2_path:
            content = self.read_text_content(file2_path)
            # 宽松检查
            if content:
                # 检查是否有目录相关的关键词
                if re.search(r'(data|app_logs|fzxy)', content, re.IGNORECASE):
                    task2_score -= penalty2
                else:
                    task2_score -= penalty2 + 2
                    self.res.add_deduction("Task1.2截图内容不相关")
                if penalty2:
                    self.res.add_deduction("Task1.2文件名不规范")
            else:
                task2_score = 5  # 文件无法读取但存在，给一半分
                self.res.add_deduction("Task1.2截图文件无法读取")
        else:
            task2_score = 0
            self.res.add_deduction("Task1.2截图缺失")
        
        task_score += task2_score
        
        # Task 1.3: 编写简易巡检脚本 (10分)
        task3_score = 10
        file3_path, penalty3 = self.smart_find(
            "12.png",
            alternatives=["12_1.png", "12-1.png", "1_12.png", "task3.png", "脚本执行.png"],
            ignore_subfixes=True
        )
        
        # 检查脚本文件
        script_path, script_penalty = self.smart_find(
            "check_server.sh",
            alternatives=["checkserver.sh", "check.sh", "server_check.sh", "巡检脚本.sh"],
            ignore_subfixes=True
        )
        
        if file3_path and script_path:
            # 检查脚本内容
            script_content = self.read_text_content(script_path)
            if script_content:
                # 宽松检查脚本内容关键词
                script_points = 0
                # 检查echo输出
                if re.search(r'echo.*server.*check', script_content, re.IGNORECASE):
                    script_points += 2
                # 检查df命令
                if re.search(r'df.*-hT', script_content, re.IGNORECASE) or re.search(r'df.*-h', script_content, re.IGNORECASE):
                    script_points += 3
                # 检查free命令
                if re.search(r'free.*-m', script_content, re.IGNORECASE) or re.search(r'free', script_content, re.IGNORECASE):
                    script_points += 3
                # 检查可执行权限设置
                if re.search(r'chmod.*x', script_content, re.IGNORECASE) or re.search(r'#!.*bash', script_content):
                    script_points += 2
                
                task3_score = min(script_points, 10)
                if task3_score < 10:
                    self.res.add_deduction(f"Task1.3脚本内容不完整，得{task3_score}分")
            else:
                task3_score = 5  # 脚本文件存在但无法读取
                self.res.add_deduction("Task1.3脚本文件无法读取")
            
            task3_score -= penalty3 + script_penalty
        else:
            # 部分文件存在的情况
            if file3_path or script_path:
                task3_score = 5  # 有一个文件存在就给部分分
                self.res.add_deduction("Task1.3文件不完整，得5分")
            else:
                task3_score = 0
                self.res.add_deduction("Task1.3文件全部缺失")
        
        task_score += task3_score
        
        self.res.add_sub_score("Part1_基础环境配置", min(task_score, 30))
    
    def _grade_part2(self, student_dir):
        """评分第二部分：Staging Web服务部署 (70分)"""
        task_score = 0
        
        # 检查test2目录是否存在
        test2_path = os.path.join(student_dir, "test2")
        if not os.path.exists(test2_path):
            self.res.add_sub_score("Part2_目录结构", 0)
            self.res.add_deduction("test2目录不存在")
            return
        
        # Task 2.1.1: 配置Web服务 (15分)
        task1_1_score = 15
        file20_path, penalty20 = self.smart_find(
            "20.png",
            alternatives=["20_1.png", "20-1.png", "2_20.png", "web配置.png", "httpd.png"],
            ignore_subfixes=True
        )
        
        if file20_path:
            content = self.read_text_content(file20_path)
            # 宽松检查：只要文件存在就基本给分
            if content:
                # 检查是否有httpd相关的关键词
                if re.search(r'(httpd|apache|web|服务)', content, re.IGNORECASE):
                    task1_1_score -= penalty20
                else:
                    task1_1_score = 10  # 存在但内容不相关，给部分分
                    self.res.add_deduction("Task2.1.1截图内容不相关")
                if penalty20:
                    self.res.add_deduction("Task2.1.1文件名不规范")
            else:
                task1_1_score = 10  # 文件无法读取但存在，给大部分分
                self.res.add_deduction("Task2.1.1截图文件无法读取")
        else:
            task1_1_score = 0
            self.res.add_deduction("Task2.1.1截图缺失")
        
        task_score += task1_1_score
        
        # Task 2.1.2: 创建开发者测试页面 (15分)
        task1_2_score = 15
        file21_path, penalty21 = self.smart_find(
            "21.png",
            alternatives=["21_1.png", "21-1.png", "2_21.png", "浏览器访问.png", "测试页面.png"],
            ignore_subfixes=True
        )
        
        if file21_path:
            content = self.read_text_content(file21_path)
            if content:
                # 宽松检查：可能是二进制图片文件，不检查具体内容
                task1_2_score -= penalty21
                if penalty21:
                    self.res.add_deduction("Task2.1.2文件名不规范")
            else:
                task1_2_score = 12  # 文件无法读取但存在，给大部分分
                self.res.add_deduction("Task2.1.2截图文件无法读取")
        else:
            task1_2_score = 0
            self.res.add_deduction("Task2.1.2截图缺失")
        
        task_score += task1_2_score
        
        # Task 2.2: 部署Staging数据库 (25分)
        task2_score = 25
        file22_path, penalty22 = self.smart_find(
            "22.png",
            alternatives=["22_1.png", "22-1.png", "2_22.png", "数据库.png", "mariadb.png", "mysql.png"],
            ignore_subfixes=True
        )
        
        if file22_path:
            content = self.read_text_content(file22_path)
            if content:
                # 宽松检查数据库相关关键词
                points = 0
                # 检查mariadb相关
                if re.search(r'(mariadb|mysql)', content, re.IGNORECASE):
                    points += 5
                # 检查create database或show databases
                if re.search(r'(create.*database|show.*databases)', content, re.IGNORECASE):
                    points += 10
                # 检查create user或grant
                if re.search(r'(create.*user|grant.*)', content, re.IGNORECASE):
                    points += 10
                
                if points < 25:
                    task2_score = points
                    self.res.add_deduction(f"Task2.2数据库操作不完整，得{points}分")
                else:
                    task2_score -= penalty22
                
                if penalty22:
                    self.res.add_deduction("Task2.2文件名不规范")
            else:
                task2_score = 15  # 文件无法读取但存在，给大部分分
                self.res.add_deduction("Task2.2截图文件无法读取")
        else:
            task2_score = 0
            self.res.add_deduction("Task2.2截图缺失")
        
        task_score += task2_score
        
        # Task 2.3: 编写Staging环境自动化备份脚本 (15分)
        task3_score = 15
        file23_path, penalty23 = self.smart_find(
            "23.png",
            alternatives=["23_1.png", "23-1.png", "2_23.png", "备份执行.png", "backup.png"],
            ignore_subfixes=True
        )
        
        # 检查备份脚本
        backup_script_path, backup_penalty = self.smart_find(
            "backup_staging.sh",
            alternatives=["backup.sh", "staging_backup.sh", "备份脚本.sh", "backup_script.sh"],
            ignore_subfixes=True
        )
        
        if file23_path and backup_script_path:
            # 检查脚本内容
            script_content = self.read_text_content(backup_script_path)
            if script_content:
                # 宽松检查脚本内容关键词
                script_points = 0
                # 检查echo输出
                if re.search(r'echo.*backup.*start', script_content, re.IGNORECASE):
                    script_points += 2
                # 检查mysqldump命令
                if re.search(r'mysqldump', script_content, re.IGNORECASE) or re.search(r'mysql.*dump', script_content, re.IGNORECASE):
                    script_points += 5
                # 检查tar命令
                if re.search(r'tar.*-czf', script_content, re.IGNORECASE) or re.search(r'tar.*-zcf', script_content, re.IGNORECASE) or re.search(r'tar.*gz', script_content, re.IGNORECASE):
                    script_points += 5
                # 检查echo完成输出
                if re.search(r'echo.*finished', script_content, re.IGNORECASE) or re.search(r'echo.*done', script_content, re.IGNORECASE):
                    script_points += 3
                
                task3_score = min(script_points, 15)
                if task3_score < 15:
                    self.res.add_deduction(f"Task2.3脚本内容不完整，得{task3_score}分")
            else:
                task3_score = 10  # 脚本文件存在但无法读取
                self.res.add_deduction("Task2.3脚本文件无法读取")
            
            task3_score -= penalty23 + backup_penalty
        else:
            # 部分文件存在的情况
            if file23_path or backup_script_path:
                task3_score = 10  # 有一个文件存在就给大部分分
                self.res.add_deduction("Task2.3文件不完整，得10分")
            else:
                task3_score = 0
                self.res.add_deduction("Task2.3文件全部缺失")
        
        task_score += task3_score
        
        self.res.add_sub_score("Part2_Web服务部署", min(task_score, 70))