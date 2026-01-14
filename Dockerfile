# 使用一个精简的 Python 基础镜像
FROM auto_correcting:v3

# 设置工作目录
WORKDIR /auto_app

# 复制并安装依赖（只复制 requirements.txt）
COPY requirements.txt .

# 安装依赖（这些不经常变化）
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5010
EXPOSE 9011