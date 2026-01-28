FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# 设置标签
LABEL description="Moondream-2B Vision Language Model HTTP Server with Standard Moondream API (v1/caption, v1/query)"

# 设置环境变量避免交互式提示
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    wget \
    libvips-dev \
    gcc \
    g++ \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制 requirements 文件
COPY requirements.txt /app/

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# Install pyvips separately (has metadata issues, install with --no-deps)
RUN pip3 install --no-cache-dir --no-build-isolation pyvips==3.1.1 || \
    pip3 install --no-cache-dir pyvips

# 复制应用代码
COPY app.py /app/
COPY test_client.py /app/
COPY README.md /app/
COPY USAGE.md /app/

# 复制脚本文件
COPY scripts/ /scripts/

# 创建模型缓存目录
RUN mkdir -p /root/.cache/huggingface

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV VLM_AUTH_USERNAME=${VLM_AUTH_USERNAME:-admin}
ENV VLM_AUTH_PASSWORD=${VLM_AUTH_PASSWORD:-admin}
ENV VLM_API_KEY=${VLM_API_KEY:-}
ENV HF_TOKEN=${HF_TOKEN:-}

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:5000/health || exit 1

# 启动命令
CMD ["python3", "app.py"]
