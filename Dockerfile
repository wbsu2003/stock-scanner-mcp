# 使用官方 Python 运行时作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 并安装依赖
COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

# 复制整个项目到工作目录
COPY . .

# 暴露 FastAPI 服务运行的端口
EXPOSE 8000

# 定义容器启动时运行的命令
# 使用 Gunicorn 配合 Uvicorn Workers 是生产环境推荐的部署方式
# CMD ["gunicorn", "main:app", "--workers", "4", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker"]
# 如果没有安装 gunicorn，或者只是用于开发测试，可以使用 uvicorn 直接启动
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
