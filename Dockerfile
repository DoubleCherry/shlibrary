# 构建阶段
FROM python:3.10-slim as builder

# 设置工作目录
WORKDIR /app

# 安装poetry
RUN pip install poetry

# 复制项目文件
COPY pyproject.toml ./
COPY src ./src
COPY README.md ./

# 配置poetry不创建虚拟环境
RUN poetry config virtualenvs.create false

# 生成lock文件并安装依赖
RUN poetry lock && poetry install --only main --no-interaction --no-ansi

# 运行阶段
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# 从构建阶段复制安装好的依赖和项目文件
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /app/src ./src

# 创建非root用户
RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# 创建日志目录
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "apitest.main", "serve"] 