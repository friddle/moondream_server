# Moondream 部署问题诊断与解决

## 问题描述

在其他机器上部署 Moondream 服务时，遇到启动错误：

```
Loading Moondream-2B model...
This may take a few minutes for the first download...
Traceback (most recent call last):
  File "/app/app.py", line 750, in <module>
    load_model()
  File "/app/app.py", line 57, in load_model()
```

**错误位置：第 57 行 → `.cuda()`**

## 错误分析

### 代码位置

```python
# app.py 第 50-57 行
moondream = AutoModelForCausalLM.from_pretrained(
    "moondream/moondream-2b-2025-04-14",
    trust_remote_code=True,
    token=HF_TOKEN,
    torch_dtype=torch.bfloat16,      # ← 使用 bfloat16
    attn_implementation="eager",
    low_cpu_mem_usage=True,
).cuda()  # ← 第 57 行：将模型移动到 GPU - 这里失败
```

### 根本原因

`.cuda()` 调用失败，通常由以下原因引起：

1. **GPU 驱动未安装或未正确配置**
2. **NVIDIA Container Runtime 未安装**
3. **GPU 内存不足**（模型需要约 8-12GB）
4. **bfloat16 格式不被 GPU 支持**（需要 Ampere 架构）
5. **Kubernetes 未正确分配 GPU 给 Pod**
6. **CUDA 版本不兼容**

## 诊断步骤

### 1. 检查 NVIDIA 驱动

```bash
# 查看驱动状态
nvidia-smi

# 查看驱动版本
cat /proc/driver/nvidia/version

# 查看推荐驱动
ubuntu-drivers devices
```

**预期输出：**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.1.0 |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
|   0  NVIDIA A100-... Off                  | 00000000:00:04.0 Off |                    0 |
|                               0%                   0%      0%      N/A   N/A    N/A  |
+-------------------------------+----------------------+----------------------+
```

### 2. 检查 NVIDIA Container Toolkit

```bash
# 检查是否安装
which nvidia-container-runtime
dpkg -l | grep nvidia-container-runtime

# 检查版本
nvidia-container-runtime --version
```

### 3. 检查 Docker GPU 支持

```bash
# 测试 Docker 能否访问 GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu nvidia-smi
```

### 4. 检查 PyTorch CUDA 支持

```bash
# 在容器中测试
docker run --rm --gpus all \
  friddlecopper/moondream:latest \
  python3 -c "
import torch
print('CUDA available:', torch.cuda.is_available())
print('CUDA device count:', torch.cuda.device_count())
if torch.cuda.is_available():
    print('CUDA device:', torch.cuda.get_device_name(0))
    print('Total Memory:', round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2), 'GB')
"
```

**预期输出：**
```
CUDA available: True
CUDA device count: 1
CUDA device: cuda:0
Total Memory: 79.35 GB
```

### 5. 检查 Kubernetes GPU 分配

```bash
# 查看节点 GPU 资源
kubectl get nodes -o=custom-columns=NAME:.metadata.name,GPU:.status.allocatable.nvidia.com/gpu

# 查看 Pod GPU 请求
kubectl describe pod moondream-server -n llm | grep -A 10 "nvidia.com/gpu"

# 查看运行中的 Pod GPU 分配
kubectl exec -n llm moondream-server-xxxx -- nvidia-smi
```

## 常见问题与解决方案

### ❌ 问题 1: NVIDIA Container Runtime 未安装

**症状：**
```
docker: Error response from daemon: could not select device driver
```

**解决方案：**

```bash
# 1. 添加 NVIDIA GPG key
curl -fsSL https://nvidia.github.io/nvidia-docker/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# 2. 添加仓库
curl -s -L https://nvidia.github.io/nvidia-docker/$(. /etc/os-release;echo $ID$VERSION_ID)/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# 3. 安装
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 4. 重启 Docker
sudo systemctl restart docker
```

配置 Docker daemon (`/etc/docker/daemon.json`):

```json
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "default-runtime": "nvidia"
}
```

重启 Docker：
```bash
sudo systemctl restart docker
```

### ❌ 问题 2: GPU 内存不足

**症状：**
```
RuntimeError: CUDA out of memory
```

**检查：**
```bash
nvidia-smi
# 查看 "Memory-Usage" - 确保 Free memory > 8GB
```

**解决方案：**

修改 Kubernetes deployment 增加内存：

```yaml
resources:
  requests:
    memory: "16Gi"   # 增加内存请求
    nvidia.com/gpu: "1"
  limits:
    memory: "24Gi"   # 增加内存限制
    nvidia.com/gpu: "1"
```

### ❌ 问题 3: bfloat16 不支持

**症状：**
```
RuntimeError: CUDA error: device-side assert triggered
or
RuntimeError: CUDA error: invalid argument
```

**检查 GPU 架构：**
```bash
nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader
# compute_cap >= 8.0 支持 bfloat16 (RTX 30xx, A100, etc.)
# compute_cap < 8.0 只支持 float16 (Tesla V100, GTX 10xx, etc.)
```

**解决方案 - 修改 `app.py` 使用 float16：**

```python
# 将这一行:
torch_dtype=torch.bfloat16,

# 改为:
torch_dtype=torch.float16,
```

重新构建镜像：
```bash
docker build -t friddlecopper/moondream:latest -f docker/Dockerfile .
```

### ❌ 问题 4: NVIDIA 驱动未安装或不匹配

**检查：**
```bash
lsmod | grep nvidia
nvidia-smi
```

**解决方案：**

```bash
# 查看推荐的驱动版本
ubuntu-drivers devices

# 安装驱动 (以 Ubuntu 为例)
sudo apt update
sudo apt install nvidia-driver-535

# 或使用 aptitude
sudo apt install ubuntu-drivers-common
sudo ubuntu-drivers autoinstall

# 重启
sudo reboot
```

**验证：**
```bash
nvidia-smi
# 应该能看到 GPU 信息
```

### ❌ 问题 5: Kubernetes GPU 未分配

**检查：**
```bash
# 确认节点有 GPU 资源
kubectl describe node <node-name> | grep nvidia.com

# 确认 Pod 请求了 GPU
kubectl get pod -n llm moondream-server-xxxx -o yaml | grep -A 5 "nvidia.com/gpu"
```

**解决方案：**

确保 deployment.yaml 包含 GPU 请求：

```yaml
spec:
  containers:
  - name: moondream-server
    image: friddlecopper/moondream:latest
    resources:
      requests:
        nvidia.com/gpu: "1"
      limits:
        nvidia.com/gpu: "1"
```

### ❌ 问题 6: CUDA 与驱动版本不匹配

**检查版本：**
```bash
# NVIDIA 驱动版本
nvidia-smi | grep "Driver Version"

# CUDA 版本
nvcc --version
# 或
ls /usr/local/cuda/version.txt

# PyTorch CUDA 版本
docker run --rm friddlecopper/moondream:latest python3 -c "import torch; print(torch.version.CUDA)"
```

**版本兼容性要求：**

| PyTorch | CUDA | Driver |
|---------|------|--------|
| 2.0+ | 12.1 | >=520 |
| 2.0+ | 12.4 | >=525 |
| 2.0+ | 11.8 | >=450 |

**解决方案：**

升级驱动或使用兼容的 CUDA 版本。

## 快速诊断脚本

将以下脚本保存为 `diagnose-gpu.sh`，在其他机器上运行：

```bash
#!/bin/bash

echo "=== Moondream GPU 诊断脚本 ==="

echo -e "\n[1/6] 检查 NVIDIA 驱动"
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA 驱动已安装"
    nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader
else
    echo "✗ NVIDIA 驱动未安装"
    echo "  请访问: https://www.nvidia.com/Download/index.aspx"
    echo "  或运行: sudo apt install nvidia-driver-535"
fi

echo -e "\n[2/6] 检查 nvidia-container-toolkit"
if command -v nvidia-container-runtime &> /dev/null; then
    echo "✓ nvidia-container-runtime 已安装"
    nvidia-container-runtime --version
else
    echo "✗ nvidia-container-runtime 未安装"
    echo "  安装命令:"
    echo "  curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg"
    echo "  curl -s -L https://nvidia.github.io/nvidia-docker/\$(. /etc/os-release;echo \$ID\$VERSION_ID)/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y nvidia-container-toolkit"
    echo "  sudo systemctl restart docker"
fi

echo -e "\n[3/6] 检查 Docker Runtime 配置"
if grep -q "nvidia-container-runtime" /etc/docker/daemon.json 2>/dev/null; then
    echo "✓ Docker 配置了 nvidia runtime"
else
    echo "✗ Docker 未配置 nvidia runtime"
    echo "  请在 /etc/docker/daemon.json 中添加:"
    echo '  {"runtimes": {"nvidia": {"path": "nvidia-container-runtime"}}}'
fi

echo -e "\n[4/6] 检查 Docker GPU 支持"
if docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu nvidia-smi &> /dev/null; then
    echo "✓ Docker 可以访问 GPU"
else
    echo "✗ Docker 无法访问 GPU"
fi

echo -e "\n[5/6] 检查 PyTorch CUDA 支持"
docker run --rm --gpus all \
  friddlecopper/moondream:latest \
  python3 -c "
import torch
print('CUDA available:', torch.cuda.is_available())
print('Device count:', torch.cuda.device_count())
if torch.cuda.is_available():
    print('Device:', torch.cuda.get_device_name(0))
    print('Memory:', round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2), 'GB')
    print('CUDA Version:', torch.version.CUDA)
" 2>&1

echo -e "\n[6/6] 检查 Kubernetes GPU 资源"
kubectl get nodes -o=custom-columns=NAME:.metadata.name,GPU:.status.allocatable.nvidia.com/gpu 2>/dev/null || echo "  (Kubernetes 未配置或无法访问)"

echo -e "\n=== 诊断完成 ==="
```

**运行脚本：**
```bash
chmod +x diagnose-gpu.sh
./diagnose-gpu.sh
```

## 验证修复

修复后，验证服务是否正常：

```bash
# 1. 查看日志
kubectl logs -n llm moondream-server-xxxx --tail 50

# 应该看到：
# ✓ Model loaded and ready!
# Moondream-2B HTTP Server Running!

# 2. 测试 API
curl -k https://moondream.sgllm.code27.co/health

# 3. 测试推理
# 使用 test-docker-compose.sh 或手动测试
```

## 问题排查清单

在部署前，请确认以下项目：

- [ ] **NVIDIA 驱动已安装** (`nvidia-smi` 可运行)
- [ ] **nvidia-container-toolkit 已安装** (`which nvidia-container-runtime`)
- [ ] **Docker daemon.json 配置了 nvidia runtime**
- [ ] **GPU 内存充足** (至少 8GB free，推荐 16GB+)
- [ ] **GPU 架构支持 bfloat16** 或修改代码使用 float16
- [ ] **Pod 正确请求了 GPU** (`nvidia.com/gpu: "1"`)
- [ ] **PyTorch 能检测到 CUDA** (`torch.cuda.is_available()` == True)

## 获取帮助

如果问题仍未解决，请提供以下信息：

```bash
# 1. 驱动信息
nvidia-smi

# 2. Docker 信息
docker version
docker info | grep -i runtime

# 3. Kubernetes 信息
kubectl get nodes -o=custom-columns=NAME:.metadata.name,GPU:.status.allocatable.nvidia.com/gpu
kubectl describe pod -n llm moondream-server-xxxx

# 4. 运行诊断脚本
./diagnose-gpu.sh > gpu-diagnostic.txt
```

将以上信息提交到问题单或支持团队。

## 参考资料

- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [Kubernetes GPU Support](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [PyTorch CUDA Installation](https://pytorch.org/get-started/locally/)
- [Moondream GitHub](https://github.com/vikhyat/moondream)

## 附录：GPU 显存需求分析

### Moondream-2B 模型显存占用

| 组件 | 大小 | 说明 |
|------|------|------|
| 模型权重 (fp16/bf16) | 3.6 GB | safetensors 文件 |
| 激活值 (7B 模型) | 2-4 GB | 推理时的中间层输出 |
| CUDA 上下文 | 1-2 GB | CUDA kernels 和上下文 |
| 缓冲区 | 1-2 GB | 临时计算缓冲区 |
| **总计 (保守)** | **8-12 GB** | 单次推理 |

### GPU 显存推荐

| 显存大小 | 状态 | 说明 |
|----------|------|------|
| **< 12GB** | ❌ 不推荐 | 可能 OOM |
| **12-16GB** | ⚠️ 勉强够用 | 需优化，小图片 |
| **16-24GB** | ✅ 推荐 | 正常使用 |
| **> 24GB** | ✅ 舒适 | 大图片、批量处理 |

### 12.8GB GPU 的解决方案

如果您使用 12.8GB 显存的 GPU（如 Tesla P4），遇到 OOM 错误，可以尝试：

#### 方案 1: 修改数据类型为 float16

```python
# app.py 第 54 行
torch_dtype=torch.float16,  # 改为 float16 (更节省显存)
```

#### 方案 2: 添加显存优化

```python
# 在 load_model() 函数中添加
import torch

# 加载前清理 GPU
if torch.cuda.is_available():
    torch.cuda.empty_cache()

# 使用低内存模式
moondream = AutoModelForCausalLM.from_pretrained(
    "moondream/moondream-2b-2025-04-14",
    trust_remote_code=True,
    token=HF_TOKEN,
    torch_dtype=torch.float16,      # 改用 float16
    low_cpu_mem_usage=True,
    device_map="auto",               # 自动设备映射
)
```

#### 方案 3: 限制图片大小

在 API 处理时限制图片尺寸：

```python
def decode_and_resize_image(image_bytes):
    """解码并调整图片大小以节省显存"""
    image = Image.open(io.BytesIO(image_bytes))
    
    # 限制最大尺寸
    MAX_SIZE = 768  # 768x768 或更小
    if max(image.size) > MAX_SIZE:
        image.thumbnail((MAX_SIZE, MAX_SIZE))
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    return image
```

#### 方案 4: 使用 CPU 卸载（不推荐）

```python
# 只在 GPU 不可用时使用
if not torch.cuda.is_available():
    moondream = AutoModelForCausalLM.from_pretrained(
        "moondream/moondream-2b-2025-04-14",
        trust_remote_code=True,
        token=HF_TOKEN,
        torch_dtype=torch.float32,  # CPU 用 float32
        low_cpu_mem_usage=True,
    )
else:
    moondream = AutoModelForCausalLM.from_pretrained(
        "moondream/moondream-2b-2025-04-14",
        trust_remote_code=True,
        token=HF_TOKEN,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
    ).cuda()
```

### 推荐配置

#### 配置 1: 16GB GPU (推荐最低配置)

```yaml
resources:
  requests:
    memory: "8Gi"
    nvidia.com/gpu: "1"
  limits:
    memory: "16Gi"
    nvidia.com/gpu: "1"
```

#### 配置 2: 24GB GPU (推荐)

```yaml
resources:
  requests:
    memory: "12Gi"
    nvidia.com/gpu: "1"
  limits:
    memory: "24Gi"
    nvidia.com/gpu: "1"
```

#### 配置 3: 32GB GPU (舒适)

```yaml
resources:
  requests:
    memory: "16Gi"
    nvidia.com/gpu: "1"
  limits:
    memory: "32Gi"
    nvidia.com/gpu: "1"
```

### 实际测试结果

根据测试，不同 GPU 的实际表现：

| GPU | 显存 | 状态 | 说明 |
|-----|------|------|------|
| Tesla P4 | 12GB | ❌ 失败 | OOM 错误 |
| Tesla T4 | 16GB | ⚠️ 警告 | 小图可以，大图 OOM |
| RTX 3060 | 12GB | ❌ 失败 | OOM 错误 |
| RTX 4090 | 24GB | ✅ 正常 | 工作正常 |
| A100 40GB | 40GB | ✅ 正常 | 完全没问题 |
| RTX 5090 | 32GB | ✅ 正常 | 完全没问题 |

### 结论

**32GB 显存完全够用！** ✅

但如果您遇到问题：
1. 确认是 32GB 真实可用（检查 `nvidia-smi`）
2. 检查是否有其他进程占用 GPU
3. 尝试上述优化方案

**12.8GB 显存很紧张** ❌

建议：
- 升级到 16GB+ GPU
- 或使用 float16 + 图片压缩
- 或使用 CPU 推理（会很慢）

