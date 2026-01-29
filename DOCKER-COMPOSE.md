# Moondream Docker Compose 部署指南

## 快速开始

### 1. 准备环境文件

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件（可选）
# - HF_TOKEN: HuggingFace token（用于下载模型）
# - VLM_API_KEY: API密钥（留空则无需认证）
# - HF_CACHE_PATH: 本地缓存路径
```

### 2. 启动服务

```bash
# 启动服务
docker-compose -f docker-compose-demo.yaml up -d

# 查看日志
docker-compose -f docker-compose-demo.yaml logs -f

# 停止服务
docker-compose -f docker-compose-demo.yaml down
```

### 3. 验证服务

```bash
# 健康检查
curl http://localhost:5000/health

# 运行测试脚本
./test-docker-compose.sh
```

## API 使用示例

### v1/caption - 生成图片描述

```bash
curl -X POST http://localhost:5000/v1/caption \
  -H 'Content-Type: application/json' \
  -d '{
    "image_url": "data:image/jpeg;base64,<base64_data>",
    "length": "normal",
    "stream": false
  }'
```

**响应示例：**
```json
{
  "caption": "一只姜黄色的猫...",
  "finish_reason": "stop",
  "metrics": {
    "input_tokens": 735,
    "output_tokens": 102,
    "prefill_time_ms": 0,
    "decode_time_ms": 1139.12,
    "ttft_ms": 1139.12
  }
}
```

### v1/query - 询问图片相关问题

```bash
curl -X POST http://localhost:5000/v1/query \
  -H 'Content-Type: application/json' \
  -d '{
    "image_url": "data:image/jpeg;base64,<base64_data>",
    "question": "这是什么动物？"
  }'
```

**响应示例：**
```json
{
  "request_id": "query_2026-01-28-15:39:37-c36043",
  "answer": "这是一只姜黄色的猫..."
}
```

### Python 示例

```python
import base64
import requests

# 读取图片并转换为 base64
with open('image.jpg', 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

# 调用 v1/query API
response = requests.post(
    'http://localhost:5000/v1/query',
    json={
        'image_url': f'data:image/jpeg;base64,{image_base64}',
        'question': '描述这张图片'
    }
)

print(response.json())
# {'answer': '...', 'request_id': 'query_...'}
```

### JavaScript 示例

```javascript
// 读取图片文件并转换为 base64
const fileInput = document.getElementById('file');
const file = fileInput.files[0];

const reader = new FileReader();
reader.onload = async (e) => {
    const base64 = e.target.result.split(',')[1];
    
    // 调用 v1/caption API
    const response = await fetch('http://localhost:5000/v1/caption', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            image_url: `data:image/jpeg;base64,${base64}`,
            length: 'normal',
            stream: false
        })
    });
    
    const data = await response.json();
    console.log(data.caption);
};
reader.readAsDataURL(file);
```

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HF_TOKEN` | HuggingFace token，用于下载模型 | 空 |
| `VLM_API_KEY` | API密钥，启用X-Moondream-Auth认证 | 空（禁用认证）|
| `HF_CACHE_PATH` | HuggingFace缓存路径 | `./huggingface-cache` |
| `PYTHONUNBUFFERED` | Python输出不缓冲 | `1` |

### length 参数（caption）

| 值 | 描述 | 长度 |
|----|------|------|
| `short` | 简短描述 | ~30字 |
| `normal` | 标准描述 | ~80字 |
| `long` | 详细描述 | ~150字 |

### GPU 支持

默认使用 NVIDIA GPU。如需使用 CPU，修改 `docker-compose-demo.yaml`:

```yaml
# 删除或注释掉 GPU 部署配置
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

## 故障排查

### 模型下载慢

首次启动会下载模型（约3.6GB），可以使用本地缓存：

```bash
# 1. 预先下载模型到本地
mkdir -p ./huggingface-cache
cp -r ~/.cache/huggingface/* ./huggingface-cache/

# 2. 启动服务（会使用本地缓存）
docker-compose -f docker-compose-demo.yaml up -d
```

### GPU 不可用

检查 GPU 是否可用：

```bash
# 检查 nvidia-docker
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu nvidia-smi

# 检查容器 GPU
docker exec moondream-server nvidia-smi
```

### 查看日志

```bash
# 实时日志
docker-compose -f docker-compose-demo.yaml logs -f

# 最近100行
docker-compose -f docker-compose-demo.yaml logs --tail 100
```

## 性能优化

### 使用 NVMe 存储

将缓存挂载到高速存储：

```yaml
volumes:
  - /nvme/huggingface-cache:/root/.cache/huggingface
```

### 调整 GPU 内存

```yaml
deploy:
  resources:
    limits:
      memory: 16G
      reservations:
        memory: 8G
```

## 生产部署

### 使用 HTTPS

添加反向代理（Nginx）：

```nginx
location / {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 启用认证

设置 API 密钥：

```bash
# .env
VLM_API_KEY=your_secret_api_key_here
```

客户端请求时添加 header：

```bash
curl -X POST http://localhost:5000/v1/query \
  -H 'Content-Type: application/json' \
  -H 'X-Moondream-Auth: your_secret_api_key_here' \
  -d '{...}'
```

## 参考资源

- [官方 API 文档](https://api.moondream.ai)
- [Moondream GitHub](https://github.com/vikhyat/moondream)
- [Docker Compose 文档](https://docs.docker.com/compose/)
