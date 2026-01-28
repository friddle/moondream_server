# Moondream-2B VLM Server Docker 部署指南

## 📦 镜像信息

- **镜像名称**: `registryaliyun.code27.co/app/vlm-server`
- **标签策略**:
  - `latest` - 最新版本
  - `YYYYMMDDHHMM` - 时间戳版本 (例如: `202601271437`)

## 🔐 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `VLM_AUTH_USERNAME` | HTTP Basic Auth 用户名 | `admin` |
| `VLM_AUTH_PASSWORD` | HTTP Basic Auth 密码 | `admin` |
| `HF_TOKEN` | Hugging Face 访问令牌 | - |

## 🏗️ 构建镜像

### 方式 1: 使用构建脚本（推荐）

```bash
cd /root/project/vlm
bash build_and_push.sh
```

### 方式 2: 手动构建

```bash
cd /root/project/vlm

# 构建镜像
nerdctl build -t registryaliyun.code27.co/app/vlm-server:latest \
              -t registryaliyun.code27.co/app/vlm-server:$(date +%Y%m%d%H%M) \
              -f docker/Dockerfile .

# 推送镜像
nerdctl push registryaliyun.code27.co/app/vlm-server:latest
nerdctl push registryaliyun.code27.co/app/vlm-server:$(date +%Y%m%d%H%M)
```

### 方式 3: 使用 Docker (如果有权限)

```bash
# 构建镜像
sudo docker build -t registryaliyun.code27.co/app/vlm-server:latest \
                  -t registryaliyun.code27.co/app/vlm-server:$(date +%Y%m%d%H%M) \
                  -f docker/Dockerfile .

# 推送镜像
sudo docker push registryaliyun.code27.co/app/vlm-server:latest
sudo docker push registryaliyun.code27.co/app/vlm-server:$(date +%Y%m%d%H%M)
```

## 🚀 运行容器

### Docker 运行

```bash
docker run -d \
  --name vlm-server \
  --gpus all \
  -p 5000:5000 \
  -e VLM_AUTH_USERNAME=admin \
  -e VLM_AUTH_PASSWORD=your_secure_password \
  -e HF_TOKEN=hf_your_huggingface_token \
  registryaliyun.code27.co/app/vlm-server:latest
```

### Kubernetes 部署

创建 `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vlm-server
  namespace: llm
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vlm-server
  template:
    metadata:
      labels:
        app: vlm-server
    spec:
      containers:
      - name: vlm-server
        image: registryaliyun.code27.co/app/vlm-server:latest
        ports:
        - containerPort: 5000
          name: http
        env:
        - name: VLM_AUTH_USERNAME
          valueFrom:
            secretKeyRef:
              name: vlm-auth
              key: username
        - name: VLM_AUTH_PASSWORD
          valueFrom:
            secretKeyRef:
              name: vlm-auth
              key: password
        - name: HF_TOKEN
          valueFrom:
            secretKeyRef:
              name: huggingface
              key: token
        resources:
          requests:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: "1"
          limits:
            memory: "16Gi"
            cpu: "8"
            nvidia.com/gpu: "1"
---
apiVersion: v1
kind: Service
metadata:
  name: vlm-service
  namespace: llm
spec:
  selector:
    app: vlm-server
  ports:
  - port: 5000
    targetPort: 5000
    name: http
  type: ClusterIP
---
apiVersion: v1
kind: Secret
metadata:
  name: vlm-auth
  namespace: llm
type: Opaque
stringData:
  username: admin
  password: your_secure_password
---
apiVersion: v1
kind: Secret
metadata:
  name: huggingface
  namespace: llm
type: Opaque
stringData:
  token: hf_your_huggingface_token
```

部署到 Kubernetes:

```bash
kubectl apply -f k8s/deployment.yaml
```

## 📡 API 使用

### 认证

所有 API 请求都需要 HTTP Basic Authentication:

```bash
# 使用 curl
curl -u username:password http://host:5000/health

# 使用 wget
wget --user=username --password=password http://host:5000/health
```

### 接口示例

#### 1. 健康检查

```bash
curl -u admin:password http://localhost:5000/health
```

响应:
```json
{
  "status": "ok",
  "model": "moondream-2b-2025-04-14"
}
```

#### 2. 图片识别

```bash
curl -X POST \
  -u admin:password \
  -F "file=@photo.jpg" \
  -F "question=这是什么？" \
  http://localhost:5000/identify
```

响应:
```json
{
  "question": "这是什么？",
  "answer": "这是一只猫咪...",
  "inference_time": "0.234s"
}
```

#### 3. Web 界面

浏览器访问: `http://localhost:5000`

会弹出 HTTP Basic Auth 认证对话框，输入用户名密码即可。

## 🔍 日志查看

```bash
# Docker
docker logs -f vlm-server

# Kubernetes
kubectl logs -f deployment/vlm-server -n llm
```

## 📊 性能指标

- 模型加载时间: 约 2-3 分钟（首次）
- 识别速度: 约 0.2-0.5 秒/张
- GPU 显存占用: 约 4-6 GB
- 推荐 GPU: NVIDIA L20 或同等性能

## 🛠️ 故障排查

### 问题 1: 镜像构建失败

确保 nerdctl 或 docker 已正确安装并有权限:

```bash
# 检查 nerdctl
nerdctl version

# 检查 docker
docker version
```

### 问题 2: 容器启动失败

检查日志:

```bash
docker logs vlm-server
```

常见原因:
- GPU 不可用
- HF_TOKEN 未设置或无效
- 显存不足

### 问题 3: 认证失败

确认环境变量已正确设置:

```bash
docker exec vlm-server env | grep VLM_AUTH
```

## 📝 更新日志

### v1.0 (2025-01-27)
- ✅ 初始版本
- ✅ HTTP Basic Authentication
- ✅ 环境变量配置
- ✅ Docker 镜像构建
- ✅ 识别时间打印
- ✅ Web 上传界面
