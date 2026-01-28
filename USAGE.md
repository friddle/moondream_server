# Moondream-2B 图像识别服务

## 🎉 服务已启动

服务运行在: **http://localhost:5000**

## 🌐 访问方式

### 1. Web 界面（推荐）
直接在浏览器打开:
```
http://localhost:5000
http://127.0.0.1:5000
```

功能:
- ✅ 拖拽或点击上传图片
- ✅ 自定义问题
- ✅ 实时显示识别结果
- ✅ 显示识别时间

### 2. API 接口

#### 健康检查
```bash
curl http://localhost:5000/health
```

响应:
```json
{
  "status": "ok",
  "model": "moondream-2b-2025-04-14"
}
```

#### 图片识别
```bash
curl -X POST \
  -F "file=@photo.jpg" \
  -F "question=这是什么？" \
  http://localhost:5000/identify
```

响应:
```json
{
  "question": "这是什么？",
  "answer": "一只可爱的猫咪...",
  "inference_time": "0.234s"
}
```

### 3. Python 测试客户端
```bash
source venv/bin/activate
python test_client.py photo.jpg
python test_client.py photo.jpg "描述这张图片"
```

## 📊 性能信息

- 模型: Moondream-2B (2025-04-14)
- 精度: bfloat16
- 设备: NVIDIA L20 GPU
- 识别时间: 约 0.2-0.5 秒/张

## 🔧 服务器日志

服务器会在控制台打印每次识别的详细信息:
```
============================================================
Inference Time: 0.234 seconds
Question: 这是什么？
Answer: 这是一张照片，展示了...
============================================================
```

## 📝 API 参数说明

### POST /identify

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件 (支持 jpg, png 等) |
| question | String | 否 | 关于图片的问题，默认 "这是什么？" |

### 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| question | String | 提问的问题 |
| answer | String | AI 的回答 |
| inference_time | String | 识别耗时 |

## 🛑 停止服务

找到运行服务的终端，按 `Ctrl+C` 停止服务。

或使用命令:
```bash
pkill -f "python app.py"
```

## 🚀 重启服务

```bash
cd /root/project/vlm
source venv/bin/activate
python app.py
```
