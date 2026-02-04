
import os
import json
import asyncio
import re
from grading_core.base import BaseGrader, GradingResult
from database import Database
from ai_utils.volc_file_manager import VolcFileManager
from ai_utils.ai_helper import call_ai_platform_chat

db = Database()

class DirectGrader_direct_9fa38898(BaseGrader):
    ID = "direct_9fa38898"
    NAME = "动态web程序设计实验-网工2502班（专升本）"
    COURSE = "None"

    # === 固化的核心知识库 ===
    EXAM_CONTENT = """
# 广西外国语学院课程考核试卷-动态web程序设计实验
## 2025 — 2026学年度第一学期
期末考试（√） 补考（ ） 重新学习考试（ ）

| 课程名称 | 动态web程序设计实验 |
| --- | --- |
| 学历层次 | 本科（√）/ 专科（ ） |
| 考核类型 | 考查(√) / 考试( ) |
| 专业年级班级 | 网工2502班（专升本） |
| 考试时间 | （90）分钟 |
| 试卷类型 | 开卷（√）/ 闭卷（ ） |
| 命题教师 | 张海林 |
| 系（教研室）主任 | 朱远坤 |
| 二级学院（部）主管教学领导 |  |

| 题号 | 一 | 二 | 总分 | 核分人 |
| --- | --- | --- | --- | --- |
| 满分 | 30 | 70 | 100 |  |
| 实得分 |  |  |  |  |

---

## 一、第19届南宁国际马拉松不久前在广西首府南宁市成功举办，许多来自全国乃至世界各地的选手参加赛事并完成了各自的挑战。请你以此为背景，并根据下面题目的要求，开发一个选手信息系统来记录各个选手的信息。以下是第一部分：数据库构建与JDBC环境搭建（共30分）。

1. 数据库设计。登录MySQL数据库，创建一个名为db_nanning_run_[你的学号]的数据库。在库中创建选手表t_runner，字段要求如下：  
   (1) id (int, 主键, 自增)  
   (2) name (varchar, 选手姓名)  
   (3) bib_number (varchar, 号码布编号，如：A12345)  
   (4) gory (varchar, 参赛组别，如：全程马拉松、半程马拉松、10公里跑)  

2. 数据插入要求：插入至少2条测试数据，其中第一条数据的姓名必须是你的真实姓名，组别任意。

3. 截图要求1(命名为10.png)： 在Navicat或命令行执行SQL查询：
   ```sql
   USE db_nanning_run_[你的学号];
   SELECT * FROM t_runner;
   ```
   截图必须包含：完整的SQL语句、查询结果（能看到你的名字）、以及窗口标题或输出信息中体现的数据库名。

4. Java 工程与 JDBC 连接。在 Eclipse 中新建 Dynamic Web Project，项目命名为web_run_[你的姓名拼音]。

5. 导入必要的Jar包（MySQL驱动等）到WEB-INF/lib并配置Build Path。

6. 在com.[姓名拼音].util包下编写DBUtil.java工具类。

7. 编写main方法测试连接，连接成功后，使用System.out.println输出以下格式内容：
   ```
   ==============================================
   数据库连接成功！
   当前时间：[系统当前时间]
   操作员：[你的班级]-[你的姓名]-[你的学号]
   ==============================================
   ```

8. 截图要求2(命名11.png)： 运行main方法，截图Eclipse的Console控制台窗口。截图必须包含：上述完整的输出信息（包含你的班级、姓名、学号）。

---

## 二、请在第一大题的基础上，根据下面的指示，完成数据库构建与JDBC环境搭建（共70分）。

1. 过滤器(Filter)开发。为了防止中文乱码，请在com.[姓名拼音].filter包下创建一个名为EncodingFilter的过滤器。过滤器需要包含下面的功能：  
   (1) 设置为拦截所有请求(/*)。  
   (2) 在doFilter方法中设置请求和响应的编码为utf-8。  
   (3) 在过滤器中增加一行打印语句：System.out.println(\"请求已被 [你的姓名] 的过滤器拦截处理\");  

2. 截图要求3(命名20.png)： 截图Eclipse的代码编辑器界面，展示EncodingFilter.java的代码。 截图必须包含：左侧的项目结构树（能看清包名com.[你的姓名拼音]...）以及代码中包含你名字的打印语句。  

3. 选手列表展示功能(Servlet + JSP + Layui)  
   后端开发：  
   (1) 创建RunnerListServlet，拦截路径/list。    
   (2) 调用JDBC查询t_runner表的所有数据，封装成List集合。    
   (3) 将List集合存入Request域：request.setAttribute(\"runners\", list);  
   (4) 使用RequestDispatcher转发跳转到index.jsp页面。  

   前端页面开发(index.jsp)：  
   (1) 引入Layui的CSS文件（美化表格）。  
   (2) 在页面顶部使用h2标签显示大标题：“2025南宁马拉松选手名单 - [你的学号]-[你的姓名]”(注意：标题必须包含个人信息)  
   (3) 使用JSTL标签库(<c:forEach>)遍历后端传递的runners数据。  
   (4) 使用HTML 的 table 标签显示数据，并添加Layui的样式类class=\"layui-table\"，使其具有美观的表格样式。  
   (5) 表格列需包含：ID、姓名、号码布、参赛组别。  

4. 截图要求4(命名21.png)： 启动Tomcat，在浏览器访问/list，截图完整的浏览器窗口。截图必须包含：  
   (1) 浏览器地址栏（URL）。  
   (2) 页面大标题（包含你的学号和姓名）。  
   (3) 表格中显示出的数据库数据（包含你的名字）。  
   (4) (可选)Eclipse控制台输出了过滤器的拦截日志。  

5. 结果提交要求：  
   (1) 在电脑桌面创建一个文件夹，命名为“班级-学号-姓名”（例如：网工2502-2025001-张三）。  
   (2) 将上述4张截图(10.png,11.png,20.png,21.png)放入该文件夹。  
   (3) 将Eclipse中的项目文件夹(web_run_[姓名拼音])复制放入该文件夹。  
   (4) 将该文件夹压缩为.zip格式，提交至教师机。  

    """

    GRADING_STANDARD = """
# 《动态web程序设计实验》评分标准

## 一、数据库构建与JDBC环境搭建（共30分）
### 1. 数据库设计（8分）
- 成功创建命名为`db_nanning_run_[学号]`的数据库得3分；数据库名称错误扣1分，未创建数据库得0分。
- 正确创建`t_runner`表且所有字段（`id`为主键自增、`name`、`bib_number`、`gory`字段类型符合要求）得5分；字段遗漏或类型错误，每个错误扣1分，扣完为止；未创建表得0分。

### 2. 数据插入（5分）
- 插入至少2条测试数据，且第一条数据包含本人真实姓名得5分；少插入1条数据扣2分，第一条数据非本人真实姓名扣2分；未插入任何数据得0分。

### 3. 截图要求1（5分）
- 截图（命名为`10.png`）包含完整SQL语句、查询结果（可见本人名字）、数据库名得5分；缺少其中1项扣1分，截图命名错误扣1分；无截图得0分。

### 4. Java工程创建（3分）
- 正确创建`Dynamic Web Project`，项目命名为`web_run_[姓名拼音]`得3分；项目名称错误扣1分，未创建项目得0分。

### 5. Jar包导入与配置（3分）
- 正确将MySQL驱动等Jar包导入`WEB-INF/lib`并配置`Build Path`得3分；Jar包未放入指定目录扣1分，未配置`Build Path`扣1分；未导入Jar包得0分。

### 6. DBUtil.java工具类编写（6分）
- 正确创建`com.[姓名拼音].util`包及`DBUtil.java`类得2分；包名或类名错误扣1分，未创建得0分。
- 工具类实现数据库连接逻辑，且`main`方法能测试连接成功得4分；连接逻辑错误扣2-3分，未编写`main`方法扣2分；连接完全失败得0分。

### 7. 输出信息与截图要求2（5分）
- 控制台输出符合指定格式（包含系统当前时间、`[班级]-[姓名]-[学号]`）得3分；输出格式存在1项错误扣1分，扣完为止。
- 截图（命名为`11.png`）包含完整输出信息（可见班级、姓名、学号）得2分；截图信息不全扣1分，截图命名错误扣1分；无截图得0分。

---

## 二、过滤器与选手列表展示功能（共70分）
### 1. 过滤器(Filter)开发（15分）
- 正确创建`com.[姓名拼音].filter`包及`EncodingFilter`类得3分；包名或类名错误扣1分，未创建得0分。
- 过滤器设置为拦截所有请求(`/*`)得3分；拦截路径错误扣2分。
- 在`doFilter`方法中正确设置请求和响应编码为`utf-8`得4分；编码设置错误扣2-3分。
- 代码中包含指定打印语句（含本人姓名：`System.out.println(\"请求已被 [你的姓名] 的过滤器拦截处理\");`）得3分；打印语句未包含本人姓名扣2分，未添加打印语句扣3分。
- 在`web.xml`中正确配置过滤器得2分；配置错误扣1分，未配置得0分。

### 2. 截图要求3（8分）
- 截图（命名为`20.png`）包含左侧项目结构树（可清晰查看包名`com.[姓名拼音]...`）、代码中含本人姓名的打印语句得8分；缺少其中1项扣2分，截图命名错误扣1分；无截图得0分。

### 3. 选手列表展示功能（Servlet + JSP + Layui）（42分）
#### 后端RunnerListServlet开发（15分）
- 正确创建`RunnerListServlet`，拦截路径为`/list`得4分；Servlet类名错误扣1分，拦截路径错误扣2分，未创建得0分。
- 正确调用JDBC查询`t_runner`表所有数据并封装为`List`集合得6分；查询逻辑错误扣3-5分，未封装为`List`扣3分。
- 将`List`集合存入Request域并转发到`index.jsp`得5分；未存入域对象扣3分，转发路径错误扣2分。

#### 前端index.jsp开发（20分）
- 正确引入Layui的CSS文件得3分；未引入扣3分，引入路径错误扣1分。
- 页面顶部`h2`标签标题为`2025南宁马拉松选手名单 - [学号]-[姓名]`得4分；标题格式错误扣2分，未包含个人信息扣3分。
- 使用JSTL标签库遍历`runners`数据得8分；未使用JSTL遍历扣6分，遍历逻辑错误扣3-5分。
- 使用带`layui-table`样式的`table`标签展示指定列（ID、姓名、号码布、参赛组别）得5分；列遗漏每个扣1分，未添加`layui-table`样式扣2分。

#### 功能运行验证（7分）
- 启动Tomcat访问`/list`能正确展示选手列表得5分；页面无法访问扣3-5分，数据展示不全扣2-3分。
- Eclipse控制台输出过滤器拦截日志得2分；未输出但过滤器功能正常，可酌情给1分；过滤器功能完全失效得0分。

### 4. 结果提交要求（5分）
- 在桌面创建命名为`班级-学号-姓名`的文件夹，包含所有截图和Eclipse项目文件夹得5分；文件夹命名错误扣1分，截图或项目遗漏1项扣1分；未按要求整理得0分。
- 文件夹压缩为`.zip`格式提交，未压缩仅扣1分，不影响其他得分点。

---

## 例外情况说明
1. 若学生因环境故障（如MySQL、Eclipse配置异常）导致部分功能未完成，能提供故障截图或有效说明的，可酌情给对应得分点10%-30%的基础分。
2. 截图内容基本完整但存在小瑕疵（如窗口标题部分遮挡），最多扣1分，不扣全分。
3. 文件名称、位置存在非核心错误（如截图命名为`10.jpg`而非`10.png`），仅扣1分，不影响其他得分项。
4. 核心功能完成（如数据库连接成功、选手列表正常展示），仅细节（如输出格式略有差异）不符合要求，最多扣2分。
    """

    EXTRA_INSTRUCTION = """
给分原则是尽可能给分。

试卷中要求学生截图，所以优先处理和识别图片，从截图的结果反推学生的完成情况并给分或扣分。

如果截图已经满足评分要求则不再分析其他文件。

如果没有截图，分析代码文件时只关注HTML、jsp、java等代码文件，其他多余文件过滤掉
    """

    @property
    def system_prompt(self):
        return f'''
你是一名极其严格且专业的阅卷专家。你的任务是根据【试卷内容】和【评分细则】，对学生提交的作业进行评分。

【试卷内容】:
{self.EXAM_CONTENT}

【评分细则】:
{self.GRADING_STANDARD}

【额外指令】:
{self.EXTRA_INSTRUCTION}

【输出要求】:
1. 必须以合法的 JSON 格式输出，根对象包含:
   - "total_score" (数字): 总得分
   - "details" (数组): 每个得分项，包含 "name" (项目名) 和 "score" (得分)
   - "comment" (字符串): 简短的评语和扣分原因
2. 不要输出 Markdown 代码块标记，直接输出 JSON 字符串。
'''

    def grade(self, student_dir, student_info, *args, **kwargs) -> GradingResult:
        self.res = GradingResult()

        valid_media_files = [] 
        text_content_buffer = ""

        MAX_MEDIA_FILES = 15
        media_count = 0
        MAX_FILE_SIZE = 512 * 1024 * 1024  # 512 MB
        MAX_TEXT_LENGTH = 15000  # 文本总长度限制

        # 1. 扫描文件
        for root, _, files in os.walk(student_dir):
            for f in files:
                if f.startswith('.'): continue
                full_path = os.path.join(root, f)
                ext = os.path.splitext(f)[1].lower()

                # 大小检查
                try:
                    file_size = os.path.getsize(full_path)
                    if file_size > MAX_FILE_SIZE:
                        self.res.add_deduction(f"跳过文件 {f} (超过512MB)")
                        continue
                except: continue

                # A. 文本类 (直接读取内容)
                if ext in ['.py', '.java', '.txt', '.md', '.c', '.cpp', '.html', '.css', '.js', '.json', '.sql']:
                    try:
                        content = self.read_text_content(full_path)
                        if content:
                            if len(content) > 5000:
                                content = content[:5000] + "\n[...内容过长已截断]"

                            if len(text_content_buffer) < MAX_TEXT_LENGTH:
                                text_content_buffer += f"\n=== 文件: {f} ===\n{content}\n"
                    except Exception as e:
                        print(f"[Grader] 读取文本失败: {e}")

                # B. 媒体类 (图片/视频/PDF)
                elif ext in ['.jpg', '.png', '.jpeg', '.webp', '.bmp', '.mp4', '.avi', '.mov', '.pdf']:
                    if media_count < MAX_MEDIA_FILES:
                        valid_media_files.append(full_path)
                        media_count += 1
                    else:
                        self.res.add_deduction(f"媒体文件过多，跳过: {f}")

        # 2. 准备调用 AI
        try:
            ai_config = db.get_best_ai_config("vision") or db.get_best_ai_config("standard")
            if not ai_config:
                self.res.add_deduction("系统未配置 AI 模型")
                return self.res

            content_list = []

            # (1) 添加文本内容
            if text_content_buffer:
                content_list.append({
                    "type": "input_text", 
                    "text": f"【学生代码/文本作业集合】:\n{text_content_buffer}"
                })

            # (2) 上传并添加媒体文件
            if valid_media_files and ai_config.get('api_key'):
                uploader = VolcFileManager(api_key=ai_config['api_key'], base_url=ai_config.get('base_url'))

                for vf in valid_media_files:
                    try:
                        ext = os.path.splitext(vf)[1].lower()
                        fid = uploader.upload_file(vf)

                        if fid:
                            # 关键修复：根据文件类型指定 input type
                            if ext in ['.jpg', '.png', '.jpeg', '.webp', '.bmp']:
                                content_list.append({
                                    "type": "input_image",
                                    "file_id": fid
                                })
                            elif ext in ['.mp4', '.avi', '.mov']:
                                content_list.append({
                                    "type": "input_video",
                                    "file_id": fid
                                })
                            elif ext == '.pdf':
                                content_list.append({
                                    "type": "input_file",
                                    "file_id": fid
                                })

                            print(f"[Grader] 文件已上传: {os.path.basename(vf)} -> {fid} (Type: {ext})")
                        else:
                            self.res.add_deduction(f"文件上传失败: {os.path.basename(vf)}")
                    except Exception as e:
                        print(f"[Grader] 上传异常: {e}")

            if not content_list:
                self.res.add_deduction("未找到有效作业文件")
                return self.res

            # 3. 调用 AI
            response_json_str = asyncio.run(call_ai_platform_chat(
                system_prompt=self.system_prompt,
                messages=[{"role": "user", "content": content_list}],
                platform_config=ai_config
            ))

            # 4. 解析结果
            match = re.search(r'\{.*\}', response_json_str, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                self.res.total_score = float(data.get('total_score', 0))
                for d in data.get('details', []):
                    self.res.add_sub_score(str(d.get('name', '评分项')), float(d.get('score', 0)))
                if data.get('comment'):
                    self.res.add_deduction(str(data['comment']))
            else:
                self.res.total_score = 0
                self.res.add_deduction("AI 返回格式无法解析")

        except Exception as e:
            self.res.total_score = 0
            self.res.add_deduction(f"批改服务异常: {str(e)}")
            import traceback
            traceback.print_exc()

        self.res.is_pass = self.res.total_score >= 60
        return self.res
