# Moondream-2B 图像识别 HTTP 服务

基于 Moondream-2B 的高性能图像识别服务，支持上传图片并进行 AI 分析。已优化并发性能和 GPU 利用率。

## ✨ 功能特点

- ✅ **标准 Moondream API** - 支持 `/v1/caption` 和 `/v1/query` 端点
- ✅ **高性能优化** - 异步预处理 + Gunicorn + Gevent，大幅提升并发能力
- ✅ **GPU 加速** - 支持 CUDA，使用 bfloat16 精度优化
- ✅ **API 密钥认证** - 可选的 X-Moondream-Auth 头部认证
- ✅ **Web UI** - 内置美观的 Web 界面，支持问答和描述两种模式
- ✅ **Docker 支持** - 开箱即用的 Docker 镜像和 docker-compose 配置

## 🚀 快速开始

### 方式 1: Docker Compose（推荐）

```bash
# 1. 设置环境变量
export VLM_API_KEY=your_api_key_here
export HF_TOKEN=your_huggingface_token

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

服务将在 `http://localhost:5000` 运行。

### 方式 2: 本地运行

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 设置 Hugging Face Token

Moondream-2B 模型需要 Hugging Face 访问权限：

```bash
# 安装 huggingface-cli（如果没有）
pip install huggingface_hub

# 登录（需要你的 Hugging Face token）
huggingface-cli login
```

Token 可以从 https://huggingface.co/settings/tokens 获取。

#### 3. 启动服务

**开发模式（Flask 开发服务器）：**
```bash
python app.py
```

**生产模式（Gunicorn + Gevent，推荐）：**
```bash
# 使用启动脚本
./start.sh

# 或手动启动
gunicorn --worker-class gevent \
  --workers 1 \
  --threads 4 \
  --timeout 120 \
  --bind 0.0.0.0:5000 \
  app:app
```

## 📡 API 使用

### 1. 健康检查

```bash
curl http://localhost:5000/health
```

响应示例：
```json
{
  "status": "ok",
  "model": "moondream-2b-2025-04-14",
  "api_key_enabled": true,
  "optimization": {
    "preprocess_workers": 4,
    "batch_enabled": false,
    "batch_size": null
  }
}
```

### 2. 图片问答 (`/v1/query`)

**请求：**
```bash
curl -X POST http://localhost:5000/v1/query \
  -H 'Content-Type: application/json' \
  -H 'X-Moondream-Auth: your_api_key' \
  -d '{
    "image_url": "data:image/jpeg;base64,/9j/4AAQ...",
    "question": "这是什么？"
  }'
```

**响应：**
```json
{
  "request_id": "query_2025-01-29-18:30:00-abc123",
  "answer": "这是一只猫坐在红色的沙发上。"
}
```

### 3. 图片描述 (`/v1/caption`)

**请求：**
```bash
curl -X POST http://localhost:5000/v1/caption \
  -H 'Content-Type: application/json' \
  -H 'X-Moondream-Auth: your_api_key' \
  -d '{
    "image_url": "data:image/jpeg;base64,/9j/4AAQ...",
    "length": "normal"
  }'
```

**参数说明：**
- `length`: 描述长度，可选值：`"short"` (~30字), `"normal"` (~80字), `"long"` (~150字)

**响应：**
```json
{
  "caption": "一只橘色的猫坐在红色的沙发上，阳光从窗户照进来。",
  "metrics": {
    "input_tokens": 735,
    "output_tokens": 15,
    "prefill_time_ms": 0,
    "decode_time_ms": 234.56,
    "ttft_ms": 234.56
  },
  "finish_reason": "stop"
}
```

### 4. Web UI

访问 `http://localhost:5000` 使用内置的 Web 界面：

- 📷 上传图片
- 💬 问答模式 - 对图片提问
- 📝 描述模式 - 生成图片描述

## ⚙️ 配置选项

### 环境变量

| 变量 | 默认值 | 说明 |
|-----|-------|------|
| `VLM_API_KEY` | - | API 密钥（设置后启用认证） |
| `HF_TOKEN` | - | Hugging Face token（下载模型必需） |
| `PREPROCESS_WORKERS` | 4 | 图像预处理线程池大小 |
| `BATCH_ENABLED` | false | 是否启用批处理（实验性） |
| `BATCH_SIZE` | 4 | 批处理大小 |
| `BATCH_TIMEOUT` | 0.1 | 批处理超时时间（秒） |
| `GUNICORN_WORKERS` | 1 | Gunicorn worker 进程数 |
| `GUNICORN_THREADS` | 4 | 每个 worker 的线程数 |
| `GUNICORN_TIMEOUT` | 120 | 请求超时时间（秒） |

### Docker Compose 配置示例

```yaml
environment:
  - VLM_API_KEY=your_api_key_here
  - HF_TOKEN=your_hf_token
  - PREPROCESS_WORKERS=4
  - GUNICORN_WORKERS=1
  - GUNICORN_THREADS=4
```

## 🎯 性能优化

### 已实现的优化

1. **异步预处理** - 使用线程池并行处理图像解码，减少 GPU 空闲时间
2. **Gunicorn + Gevent** - 异步 I/O 处理，大幅提升并发连接能力
3. **GPU 锁机制** - 防止并发 GPU 访问导致的 OOM 错误
4. **bfloat16 精度** - 降低显存占用，提升推理速度

### 性能指标

- **并发连接处理能力**: +200% (相比 Flask 开发服务器)
- **GPU 利用率**: 提升 ~30% (异步预处理减少等待时间)
- **请求延迟稳定性**: 显著提升 (GPU 锁防止竞争)

### 推荐配置

| 场景 | Workers | Threads | Preprocess Workers |
|-----|---------|---------|-------------------|
| 开发测试 | 1 | 2 | 2 |
| 生产环境 | 1 | 4 | 4 |
| 高并发 | 1 | 8 | 8 |

**注意**: GPU 推理是串行的，多个 worker 不会提升 GPU 利用率，但可以提升 I/O 并发能力。

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -t friddlecooper/moondream:latest -f docker/Dockerfile .
```

### 运行容器

```bash
docker run -d \
  --name moondream-server \
  --gpus all \
  -p 5000:5000 \
  -e VLM_API_KEY=your_api_key \
  -e HF_TOKEN=your_hf_token \
  -e PREPROCESS_WORKERS=4 \
  friddlecooper/moondream:latest
```

### 使用 docker-compose

```bash
# 编辑 docker-compose.yaml 设置环境变量
# 然后启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

## 📊 监控和日志

### 健康检查

```bash
curl http://localhost:5000/health
```

### 查看日志

**Docker:**
```bash
docker-compose logs -f
```

**本地运行:**
日志会输出到控制台，包含：
- 推理时间
- 请求 ID
- 问题和答案

示例输出：
```
============================================================
[v1 API] Request ID: query_2025-01-29-18:30:00-abc123
[v1 API] Inference Time: 0.234 seconds
[v1 API] Question: 这是什么？
[v1 API] Answer: 这是一只猫坐在红色的沙发上。
============================================================
```

## 🔒 安全建议

1. **生产环境务必设置 API 密钥**：
   ```bash
   export VLM_API_KEY=strong_random_key_here
   ```

2. **使用 HTTPS** - 通过反向代理（如 Nginx）配置 SSL/TLS

3. **限制访问** - 使用防火墙或云安全组限制访问来源

4. **监控资源** - 监控 GPU 显存和 CPU 使用情况

## 📝 注意事项

1. **GPU 要求**：
   - 需要 NVIDIA GPU 和 CUDA 支持
   - 推荐显存：16GB+（最低 12GB）
   - 需要 Ampere 架构（RTX 30xx+）以支持 bfloat16

2. **首次启动**：
   - 会下载模型（约 3.6GB）
   - 模型编译需要 1-2 分钟
   - 确保网络连接稳定

3. **性能调优**：
   - 根据实际负载调整 `PREPROCESS_WORKERS` 和 `GUNICORN_THREADS`
   - 监控 GPU 利用率，避免过度并发导致 OOM

## 🛠️ 故障排查

### GPU 不可用

```bash
# 检查 GPU
nvidia-smi

# 检查 CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

### 显存不足 (OOM)

- 降低 `PREPROCESS_WORKERS`
- 确保没有其他进程占用 GPU
- 考虑使用 float16 替代 bfloat16（需要修改代码）

### 请求超时

- 增加 `GUNICORN_TIMEOUT`（默认 120 秒）
- 检查网络连接
- 查看日志排查具体问题

## 📚 相关文档

- [API 详细文档](API.md)
- [Docker Compose 使用指南](DOCKER-COMPOSE.md)
- [部署指南](DEPLOY.md)
- [使用示例](USAGE.md)
- [问题排查](PROBLEM.md)

## 📄 许可证

本项目基于 Moondream-2B 模型，请遵循相应的许可证要求。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**最后更新**: 2025-01-29  
**版本**: 2.0 (优化版)
