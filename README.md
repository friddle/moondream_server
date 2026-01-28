# Moondream3 图像识别 HTTP 服务

基于 Moondream3 的简单图像识别服务，支持上传图片并进行 AI 分析。

## 前置准备

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 登录 Hugging Face

Moondream3 是一个受限制的模型，需要先获得访问权限并登录：

1. 访问 https://huggingface.co/moondream/moondream3-preview
2. 点击页面上的 "Request Access" 或同意使用条款
3. 获取访问权限后，使用以下命令登录：

```bash
# 安装 huggingface-cli（如果没有）
pip install huggingface_hub

# 登录（需要你的 Hugging Face token）
huggingface-cli login
```

登录时会提示输入 token，可以从 https://huggingface.co/settings/tokens 获取。

## 启动服务

```bash
python app.py
```

服务启动后会在 `http://localhost:5000` 运行

## API 使用

### 1. 健康检查

```bash
curl http://localhost:5000/health
```

### 2. 图片识别

**使用 curl:**

```bash
# 基本识别
curl -X POST -F "file=@photo.jpg" http://localhost:5000/identify

# 自定义问题
curl -X POST -F "file=@photo.jpg" -F "question=What color is the sky?" http://localhost:5000/identify
```

**使用 Python 测试客户端:**

```bash
# 基本识别
python test_client.py photo.jpg

# 自定义问题
python test_client.py photo.jpg "描述这张图片中的所有物体"
```

## 功能特点

- ✓ 上传图片并进行智能识别
- ✓ 支持自定义问题
- ✓ 自动打印推理时间
- ✓ 支持 CUDA 加速（需要 GPU）
- ✓ 使用 bfloat16 精度优化

## 识别时间输出

服务会在控制台打印每次识别的耗时：

```
============================================================
Inference Time: 0.234 seconds
Question: What's in this image?
Answer: A cat sitting on a red couch...
============================================================
```

## 注意事项

1. 需要 NVIDIA GPU 和 CUDA 支持
2. 首次启动会下载模型（约 9GB）
3. 模型加载和编译需要一些时间
