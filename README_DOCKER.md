# Moondream-2B VLM Server

Vision Language Model HTTP Server with HTTP Basic Authentication

## ✨ 特性

- 🌙 **Moondream-2B 模型** - 高性能视觉语言模型
- 🔐 **HTTP Basic 认证** - 安全的访问控制
- 🐳 **Docker 支持** - 容器化部署
- ☸️ **Kubernetes 就绪** - K8s 部署配置
- 📊 **性能监控** - 识别时间打印
- 🌐 **Web 界面** - 简单的图片上传界面
- ⚡ **GPU 加速** - CUDA 支持

## 🚀 快速开始

### 1. 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量（可选）
export VLM_AUTH_USERNAME=admin
export VLM_AUTH_PASSWORD=your_password

# 启动服务
python app.py
```

### 2. Docker 运行

```bash
docker run -d \
  --gpus all \
  -p 5000:5000 \
  -e VLM_AUTH_USERNAME=admin \
  -e VLM_AUTH_PASSWORD=your_password \
  -e HF_TOKEN=your_huggingface_token \
  registryaliyun.code27.co/app/vlm-server:latest
```

### 3. Kubernetes 部署

```bash
# 部署到 K8s
bash k8s/deploy.sh

# 或手动部署
kubectl apply -f k8s/deployment.yaml
```

## 📡 API 使用

### 认证

所有请求都需要 HTTP Basic Authentication:

```bash
curl -u username:password http://host:5000/api
```

### 接口

#### 健康检查
```bash
curl -u admin:password http://localhost:5000/health
```

#### 图片识别
```bash
curl -X POST \
  -u admin:password \
  -F "file=@photo.jpg" \
  -F "question=这是什么？" \
  http://localhost:5000/identify
```

#### Web 界面
浏览器打开: `http://localhost:5000`

## 🔧 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VLM_AUTH_USERNAME` | 认证用户名 | `admin` |
| `VLM_AUTH_PASSWORD` | 认证密码 | `admin` |
| `HF_TOKEN` | Hugging Face Token | - |

## 📦 构建镜像

```bash
# 构建并推送
bash build_and_push.sh

# 或手动构建
nerdctl build -t vlm-server:latest -f docker/Dockerfile .
nerdctl push vlm-server:latest
```

## 📁 项目结构

```
.
├── app.py                  # 主应用（含 HTTP Basic Auth）
├── requirements.txt         # Python 依赖
├── docker/
│   └── Dockerfile          # Docker 镜像构建文件
├── k8s/
│   ├── deployment.yaml     # Kubernetes 部署配置
│   └── deploy.sh           # 部署脚本
├── build_and_push.sh       # 构建和推送脚本
├── start.sh                # 启动脚本
└── DEPLOY.md               # 详细部署文档
```

## 🔍 测试

```bash
# 下载测试图片
wget -O test.jpg "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800"

# 测试识别
curl -u admin:password \
  -F "file=@test.jpg" \
  -F "question=描述这张图片" \
  http://localhost:5000/identify
```

## 📊 性能

- 识别速度: 0.2-0.5 秒/张
- GPU 显存: 4-6 GB
- 推荐 GPU: NVIDIA L20 或同等

## 📝 文档

- [DEPLOY.md](DEPLOY.md) - 详细部署指南
- [USAGE.md](USAGE.md) - 使用说明

## 📄 许可证

Copyright © 2025

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!
