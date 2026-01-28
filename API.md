# Moondream-2B VLM Server API 文档

## 基础信息

- **服务地址**: http://8.219.14.29:5000
- **认证**: 当前已禁用（无需要用户名密码）
- **模型**: Moondream-2B (2025-04-14)

---

## 📡 API 接口

### 1. 健康检查

检查服务状态和配置。

**请求:**
```bash
curl http://8.219.14.29:5000/health
```

**响应:**
```json
{
  "status": "ok",
  "model": "moondream-2b-2025-04-14",
  "auth_enabled": false
}
```

---

### 2. 图片问答 (Identify)

对图片进行问答，可以询问任何关于图片的问题。

**端点**: `POST /identify`

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件 |
| question | String | 否 | 关于图片的问题，默认 "What's in this image?" |

**请求示例:**
```bash
curl -X POST \
  -F "file=@photo.jpg" \
  -F "question=这是什么？" \
  http://8.219.14.29:5000/identify
```

**响应:**
```json
{
  "question": "这是什么？",
  "answer": "这是一只猫咪...",
  "inference_time": "0.234s"
}
```

**常见问题示例:**
```bash
# 计数问题
curl -X POST -F "file=@photo.jpg" -F "question=图片里有几个人？" http://8.219.14.29:5000/identify

# 描述问题
curl -X POST -F "file=@photo.jpg" -F "question=详细描述这张图片" http://8.219.14.29:5000/identify

# 颜色问题
curl -X POST -F "file=@photo.jpg" -F "question=图片的主色调是什么？" http://8.219.14.29:5000/identify
```

---

### 3. 图片描述 (Caption) ✨ 新功能

自动生成图片的自然语言描述，无需提供问题。

**端点**: `POST /caption`

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件 |
| length | String | 否 | 描述长度：short/normal/long (默认: normal) |

**请求示例:**

#### 简短描述
```bash
curl -X POST \
  -F "file=@photo.jpg" \
  -F "length=short" \
  http://8.219.14.29:5000/caption
```

**响应:**
```json
{
  "caption": "A black and white cat with green eyes rests on a wooden surface.",
  "length": "short",
  "inference_time": "0.664s"
}
```

#### 标准描述 (默认)
```bash
curl -X POST \
  -F "file=@photo.jpg" \
  -F "length=normal" \
  http://8.219.14.29:5000/caption
```

**响应:**
```json
{
  "caption": "A black and white cat with green eyes is comfortably perched on a light brown bamboo railing. The cat's front paws are stretched out in front of it, and its gaze is directed straight at the camera...",
  "length": "normal",
  "inference_time": "0.684s"
}
```

#### 详细描述
```bash
curl -X POST \
  -F "file=@photo.jpg" \
  -F "length=long" \
  http://8.219.14.29:5000/caption
```

**响应:**
```json
{
  "caption": "The image features a black and white cat with striking green eyes, positioned prominently in the center of the frame. The cat has a distinctive black patch on its head and a white chest, contrasting sharply with its black ears and face...",
  "length": "long",
  "inference_time": "1.315s"
}
```

**length 参数对比:**

| 长度 | 字数 | 用途 | 平均耗时 |
|------|------|------|----------|
| short | ~30 字 | 快速摘要、标签 | 0.5-0.7s |
| normal | ~80 字 | 一般描述 | 0.6-0.8s |
| long | ~150 字 | 详细分析 | 1.0-1.5s |

---

### 4. Web 界面

直接在浏览器中上传图片进行识别。

**地址**: http://8.219.14.29:5000

**功能**:
- 拖拽或点击上传图片
- 自定义问题
- 实时显示识别结果
- 显示识别时间

---

## 🔧 使用场景对比

### Identify vs Caption

| 场景 | 推荐接口 | 原因 |
|------|----------|------|
| 需要特定答案 | `/identify` | 可以问具体问题 |
| 快速生成图片说明 | `/caption` + short | 无需构思问题 |
| 详细分析图片内容 | `/caption` + long | 自动生成完整描述 |
| 计数/定位问题 | `/identify` | 可以问特定问题 |
| 批量处理图片 | `/caption` + normal | 标准化描述 |

---

## 📊 性能参考

| 任务类型 | 平均时间 | 范围 |
|---------|---------|------|
| caption (short) | 0.6s | 0.5-0.7s |
| caption (normal) | 0.7s | 0.6-0.9s |
| caption (long) | 1.3s | 1.0-1.5s |
| identify (简单) | 0.3s | 0.1-0.5s |
| identify (复杂) | 0.8s | 0.5-1.0s |

---

## 🧪 测试脚本

### 测试 caption 接口
```bash
bash test_caption.sh
```

### 测试 identify 接口
```bash
bash test_images.sh
```

### 完整 API 测试
```bash
bash test_api.sh
```

---

## 💡 Python 示例

### 使用 caption
```python
import requests

# 读取图片
with open('photo.jpg', 'rb') as f:
    files = {'file': f}
    data = {'length': 'normal'}

    # 调用 caption 接口
    response = requests.post(
        'http://8.219.14.29:5000/caption',
        files=files,
        data=data
    )

    result = response.json()
    print(f"描述: {result['caption']}")
    print(f"耗时: {result['inference_time']}")
```

### 使用 identify
```python
import requests

# 读取图片
with open('photo.jpg', 'rb') as f:
    files = {'file': f}
    data = {'question': '这是什么？'}

    # 调用 identify 接口
    response = requests.post(
        'http://8.219.14.29:5000/identify',
        files=files,
        data=data
    )

    result = response.json()
    print(f"问题: {result['question']}")
    print(f"回答: {result['answer']}")
    print(f"耗时: {result['inference_time']}")
```

---

## ⚠️ 注意事项

1. **图片格式**: 支持 JPG, PNG, WebP 等常见格式
2. **图片大小**: 建议小于 10MB
3. **并发请求**: 建议 QPS < 10
4. **识别时间**: 首次请求较慢（模型加载），后续请求会更快

---

## 📝 更新日志

### v1.1 (2025-01-27)
- ✅ 新增 `/caption` 接口
- ✅ 支持三种描述长度
- ✅ 性能优化

### v1.0 (2025-01-27)
- ✅ `/identify` 接口
- ✅ `/health` 健康检查
- ✅ Web 上传界面
- ✅ HTTP Basic Auth (可选)
