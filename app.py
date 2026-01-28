"""
Moondream-2B Image Recognition HTTP Service
Upload images and get AI-powered descriptions
"""

import torch
from transformers import AutoModelForCausalLM
from flask import Flask, request, jsonify
from functools import wraps
from PIL import Image
import io
import time
import os
import base64
import uuid
from datetime import datetime

app = Flask(__name__)

# Global model variable
moondream = None

# API Key for X-Moondream-Auth header (standard Moondream API)
# Read from VLM_API_KEY environment variable
VLM_API_KEY = os.environ.get('VLM_API_KEY', '')
if VLM_API_KEY:
    print(f"✓ API Key authentication enabled (X-Moondream-Auth)")

# Hugging Face token
HF_TOKEN = os.environ.get('HF_TOKEN', '')

def api_key_required(f):
    """Decorator that requires X-Moondream-Auth API key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if VLM_API_KEY:
            api_key = request.headers.get('X-Moondream-Auth', '')
            if api_key != VLM_API_KEY:
                return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated

def load_model():
    """Load Moondream2 model"""
    global moondream
    print("Loading Moondream-2B model...")
    print("This may take a few minutes for the first download...")

    # Load model with specific config to avoid transformers compatibility issues
    moondream = AutoModelForCausalLM.from_pretrained(
        "moondream/moondream-2b-2025-04-14",
        trust_remote_code=True,
        token=HF_TOKEN,
        torch_dtype=torch.bfloat16,
        attn_implementation="eager",
        low_cpu_mem_usage=True,
    ).cuda()  # Manually move to CUDA

    print("Compiling model (this may take a minute)...")
    moondream.compile()
    print("✓ Model loaded and ready!")

    # Print auth status
    if VLM_API_KEY:
        print("✓ API Key authentication enabled (X-Moondream-Auth)")
    else:
        print("⚠ No API key set - using X-Moondream-Auth header is optional")

def decode_base64_image(image_url):
    """Decode base64 image from data URL"""
    if image_url.startswith('data:image/'):
        # Extract the base64 part after the comma
        header, encoded = image_url.split(',', 1)
        image_bytes = base64.b64decode(encoded)
        return Image.open(io.BytesIO(image_bytes))
    else:
        raise ValueError("Invalid image_url format. Expected data URL format: data:image/<type>;base64,<data>")

def calculate_metrics(start_time, end_time, input_tokens=0, output_tokens=0):
    """Calculate and return metrics dict"""
    prefill_time = (start_time[1] - start_time[0]) * 1000 if len(start_time) > 1 else 0
    decode_time = (end_time[0] - start_time[-1]) * 1000 if len(start_time) > 0 else 0
    ttft = (end_time[0] - start_time[0]) * 1000 if len(start_time) > 0 else 0

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "prefill_time_ms": round(prefill_time, 2),
        "decode_time_ms": round(decode_time, 2),
        "ttft_ms": round(ttft, 2)
    }

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "model": "moondream-2b-2025-04-14", "api_key_enabled": bool(VLM_API_KEY)})

@app.route('/', methods=['GET'])
def index():
    """Serve the HTML upload page"""
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moondream-2B 图像识别</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
            padding: 40px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }

        /* Mode Selector */
        .mode-selector {
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
            background: #f0f2ff;
            padding: 8px;
            border-radius: 15px;
        }
        .mode-btn {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 12px;
            background: transparent;
            color: #666;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        .mode-btn.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        .mode-btn:hover:not(.active) {
            background: rgba(102, 126, 234, 0.1);
        }

        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #f8f9ff;
            margin-bottom: 20px;
        }
        .upload-area:hover {
            border-color: #764ba2;
            background: #f0f2ff;
        }
        .upload-area.dragover {
            border-color: #764ba2;
            background: #e8ebff;
            transform: scale(1.02);
        }
        #fileInput {
            display: none;
        }
        .upload-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        .upload-text {
            color: #667eea;
            font-size: 16px;
            font-weight: 500;
        }
        #preview {
            max-width: 100%;
            max-height: 300px;
            margin: 20px auto;
            display: none;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        /* Input Group */
        .input-group {
            margin-bottom: 20px;
        }
        .input-group.hidden {
            display: none;
        }
        label {
            display: block;
            color: #333;
            font-weight: 500;
            margin-bottom: 8px;
        }
        input[type="text"], select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }

        button.submit-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button.submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }
        button.submit-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9ff;
            border-radius: 15px;
            display: none;
        }
        .result-title {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 14px;
        }
        .result-content {
            color: #333;
            line-height: 1.6;
        }
        .time-badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 10px;
        }
        .loading {
            text-align: center;
            color: #667eea;
            padding: 20px;
            display: none;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            background: #ffe6e6;
            color: #d63031;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌙 Moondream-2B</h1>
        <p class="subtitle">AI 图像识别服务</p>

        <!-- Mode Selector -->
        <div class="mode-selector">
            <button class="mode-btn active" id="promptModeBtn" onclick="switchMode('prompt')">
                💬 问答模式
            </button>
            <button class="mode-btn" id="captionModeBtn" onclick="switchMode('caption')">
                📝 描述模式
            </button>
        </div>

        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📷</div>
            <div class="upload-text">点击或拖拽上传图片</div>
            <input type="file" id="fileInput" accept="image/*">
        </div>

        <img id="preview" alt="预览">

        <!-- Prompt Mode Input -->
        <div class="input-group" id="promptInputGroup">
            <label for="question">问题</label>
            <input type="text" id="question" value="这是什么？" placeholder="输入关于图片的问题">
        </div>

        <!-- Caption Mode Input -->
        <div class="input-group hidden" id="captionInputGroup">
            <label for="captionLength">描述长度</label>
            <select id="captionLength">
                <option value="short">简短 (~30字)</option>
                <option value="normal" selected>标准 (~80字)</option>
                <option value="long">详细 (~150字)</option>
            </select>
        </div>

        <button class="submit-btn" id="submitBtn" disabled>🚀 开始识别</button>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div id="loadingText">AI 正在分析图片，请稍候...</div>
        </div>

        <div class="result" id="result">
            <div class="result-title" id="resultTitle">✨ 识别结果</div>
            <div class="result-content" id="resultContent"></div>
            <div class="time-badge" id="timeBadge"></div>
        </div>

        <div class="error" id="error"></div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const preview = document.getElementById('preview');
        const submitBtn = document.getElementById('submitBtn');
        const question = document.getElementById('question');
        const captionLength = document.getElementById('captionLength');
        const promptInputGroup = document.getElementById('promptInputGroup');
        const captionInputGroup = document.getElementById('captionInputGroup');
        const promptModeBtn = document.getElementById('promptModeBtn');
        const captionModeBtn = document.getElementById('captionModeBtn');
        const loading = document.getElementById('loading');
        const loadingText = document.getElementById('loadingText');
        const result = document.getElementById('result');
        const resultTitle = document.getElementById('resultTitle');
        const resultContent = document.getElementById('resultContent');
        const timeBadge = document.getElementById('timeBadge');
        const error = document.getElementById('error');

        let currentMode = 'prompt'; // 'prompt' or 'caption'
        let selectedFile = null;

        // Mode switching
        function switchMode(mode) {
            currentMode = mode;

            if (mode === 'prompt') {
                promptModeBtn.classList.add('active');
                captionModeBtn.classList.remove('active');
                promptInputGroup.classList.remove('hidden');
                captionInputGroup.classList.add('hidden');
            } else {
                captionModeBtn.classList.add('active');
                promptModeBtn.classList.remove('active');
                captionInputGroup.classList.remove('hidden');
                promptInputGroup.classList.add('hidden');
            }

            // Clear previous results
            result.style.display = 'none';
            error.style.display = 'none';
        }

        uploadArea.addEventListener('click', () => fileInput.click());

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                handleFile(file);
            }
        });

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                handleFile(file);
            }
        });

        function handleFile(file) {
            selectedFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.src = e.target.result;
                preview.style.display = 'block';
                submitBtn.disabled = false;
                result.style.display = 'none';
                error.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }

        submitBtn.addEventListener('click', async () => {
            if (!selectedFile) return;

            const formData = new FormData();
            formData.append('file', selectedFile);

            let endpoint = '';
            if (currentMode === 'prompt') {
                endpoint = '/identify';
                formData.append('question', question.value || '这是什么？');
                loadingText.textContent = 'AI 正在回答问题，请稍候...';
            } else {
                endpoint = '/caption';
                formData.append('length', captionLength.value);
                loadingText.textContent = 'AI 正在生成描述，请稍候...';
            }

            loading.style.display = 'block';
            result.style.display = 'none';
            error.style.display = 'none';
            submitBtn.disabled = true;

            try {
                const startTime = Date.now();
                const response = await fetch(endpoint, {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();

                if (response.ok) {
                    if (currentMode === 'prompt') {
                        resultTitle.textContent = '✨ 回答';
                        resultContent.textContent = data.answer;
                    } else {
                        resultTitle.textContent = '✨ 图片描述';
                        resultContent.textContent = data.caption;
                    }
                    timeBadge.textContent = `⏱️ 识别时间: ${data.inference_time}`;
                    result.style.display = 'block';

                    // Also log to console
                    console.log('识别结果:', data);
                } else {
                    error.textContent = '❌ ' + (data.error || '识别失败');
                    error.style.display = 'block';
                }
            } catch (err) {
                error.textContent = '❌ 网络错误: ' + err.message;
                error.style.display = 'block';
            } finally {
                loading.style.display = 'none';
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
    '''


@app.route('/caption', methods=['POST'])
@api_key_required
def caption():
    """
    Caption endpoint - Generate natural language description of image

    Expects:
    - file: image file (multipart/form-data)
    - length: caption length - "short", "normal", or "long" (default: "normal")
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    length = request.form.get('length', 'normal')
    if length not in ['short', 'normal', 'long']:
        length = 'normal'

    try:
        # Read and load image
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Start timing
        start_time = time.time()

        # Generate caption
        result = moondream.caption(image, length=length)

        # End timing
        end_time = time.time()
        inference_time = end_time - start_time

        response = {
            "caption": result["caption"],
            "length": length,
            "inference_time": f"{inference_time:.3f}s"
        }

        # Print timing to console
        print(f"\n{'='*60}")
        print(f"Inference Time: {inference_time:.3f} seconds")
        print(f"Caption Length: {length}")
        print(f"Caption: {result['caption']}")
        print(f"{'='*60}\n")

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/v1/caption', methods=['POST'])
@api_key_required
def v1_caption():
    """
    Standard Moondream API v1/caption endpoint

    Expects JSON body:
    - image_url: base64 data URL (e.g., "data:image/jpeg;base64,...")
    - length: caption length - "short", "normal", or "long" (default: "normal")
    - stream: boolean for streaming (default: false, not yet implemented)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        image_url = data.get('image_url')
        if not image_url:
            return jsonify({"error": "Missing image_url parameter"}), 400

        length = data.get('length', 'normal')
        if length not in ['short', 'normal', 'long']:
            length = 'normal'

        stream = data.get('stream', False)

        # Decode base64 image
        image = decode_base64_image(image_url)

        # Start timing
        start_time = time.time()

        # Generate caption
        result = moondream.caption(image, length=length)

        # End timing
        end_time = time.time()
        inference_time = end_time - start_time

        # Calculate metrics (estimated token counts)
        metrics = calculate_metrics(
            [start_time],
            [end_time],
            input_tokens=735,  # Estimated
            output_tokens=len(result["caption"].split())
        )

        response = {
            "caption": result["caption"],
            "metrics": metrics,
            "finish_reason": "stop"
        }

        # Print timing to console
        print(f"\n{'='*60}")
        print(f"[v1 API] Inference Time: {inference_time:.3f} seconds")
        print(f"[v1 API] Caption Length: {length}")
        print(f"[v1 API] Caption: {result['caption']}")
        print(f"{'='*60}\n")

        return jsonify(response)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/identify', methods=['POST'])
@api_key_required
def identify():
    """
    Identify/upload image endpoint

    Expects:
    - file: image file (multipart/form-data)
    - question: optional question about the image (default: "What's in this image?")
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    question = request.form.get('question', "What's in this image?")

    try:
        # Read and load image
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Start timing
        start_time = time.time()

        # Run inference (moondream-2b doesn't support 'reasoning' parameter)
        result = moondream.query(
            image=image,
            question=question
        )

        # End timing
        end_time = time.time()
        inference_time = end_time - start_time

        response = {
            "question": question,
            "answer": result["answer"],
            "inference_time": f"{inference_time:.3f}s"
        }

        # Print timing to console
        print(f"\n{'='*60}")
        print(f"Inference Time: {inference_time:.3f} seconds")
        print(f"Question: {question}")
        print(f"Answer: {result['answer']}")
        print(f"{'='*60}\n")

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/v1/query', methods=['POST'])
@api_key_required
def v1_query():
    """
    Standard Moondream API v1/query endpoint

    Expects JSON body:
    - image_url: base64 data URL (e.g., "data:image/jpeg;base64,...")
    - question: question about the image
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON body"}), 400

        image_url = data.get('image_url')
        if not image_url:
            return jsonify({"error": "Missing image_url parameter"}), 400

        question = data.get('question')
        if not question:
            return jsonify({"error": "Missing question parameter"}), 400

        # Generate request_id
        request_id = f"query_{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}-{uuid.uuid4().hex[:6]}"

        # Decode base64 image
        image = decode_base64_image(image_url)

        # Start timing
        start_time = time.time()

        # Run inference
        result = moondream.query(
            image=image,
            question=question
        )

        # End timing
        end_time = time.time()
        inference_time = end_time - start_time

        response = {
            "request_id": request_id,
            "answer": result["answer"]
        }

        # Print timing to console
        print(f"\n{'='*60}")
        print(f"[v1 API] Request ID: {request_id}")
        print(f"[v1 API] Inference Time: {inference_time:.3f} seconds")
        print(f"[v1 API] Question: {question}")
        print(f"[v1 API] Answer: {result['answer']}")
        print(f"{'='*60}\n")

        return jsonify(response)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    load_model()
    print("\n" + "="*60)
    print("Moondream-2B HTTP Server Running!")
    print("Server: http://0.0.0.0:5000")
    print("Local: http://localhost:5000")
    if VLM_API_KEY:
        print("Auth: Required (X-Moondream-Auth header)")
    else:
        print("Auth: Disabled (no API key required)")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
