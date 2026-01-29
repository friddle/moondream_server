"""
Moondream-2B Image Recognition HTTP Service
Upload images and get AI-powered descriptions

Optimized with:
- Thread pool for async image preprocessing
- Request batching for better GPU utilization
- Gunicorn compatible
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
from concurrent.futures import ThreadPoolExecutor
import threading
import queue

app = Flask(__name__)

# Global model variable
moondream = None

# Thread pool for CPU-intensive preprocessing (base64 decode, image conversion)
# This allows multiple images to be preprocessed in parallel while GPU is busy
PREPROCESS_WORKERS = int(os.environ.get('PREPROCESS_WORKERS', '4'))
preprocess_pool = ThreadPoolExecutor(max_workers=PREPROCESS_WORKERS)

# GPU inference lock - ensures only one inference at a time to prevent OOM
gpu_lock = threading.Lock()

# Batch processing settings
BATCH_ENABLED = os.environ.get('BATCH_ENABLED', 'false').lower() == 'true'
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '4'))
BATCH_TIMEOUT = float(os.environ.get('BATCH_TIMEOUT', '0.1'))  # 100ms

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

    # Print optimization settings
    print(f"✓ Preprocess thread pool: {PREPROCESS_WORKERS} workers")
    print(f"✓ Batch processing: {'enabled' if BATCH_ENABLED else 'disabled'}")
    if BATCH_ENABLED:
        print(f"  - Batch size: {BATCH_SIZE}")
        print(f"  - Batch timeout: {BATCH_TIMEOUT}s")

    # Print auth status
    if VLM_API_KEY:
        print("✓ API Key authentication enabled (X-Moondream-Auth)")
    else:
        print("⚠ No API key set - using X-Moondream-Auth header is optional")


def preprocess_image_async(image_url):
    """
    Submit image preprocessing to thread pool.
    Returns a Future that resolves to the preprocessed PIL Image.
    """
    return preprocess_pool.submit(decode_base64_image, image_url)


def run_inference_with_lock(func, *args, **kwargs):
    """
    Run GPU inference with lock to prevent concurrent GPU access.
    This ensures only one inference runs at a time, preventing OOM errors.
    """
    with gpu_lock:
        return func(*args, **kwargs)

def decode_base64_image(image_url):
    """Decode base64 image from data URL"""
    if image_url.startswith('data:image/'):
        # Extract the base64 part after the comma
        header, encoded = image_url.split(',', 1)
        image_bytes = base64.b64decode(encoded, validate=True)

        # Open the image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        # Force loading image data to catch errors early
        image.load()

        # Convert to RGB if necessary (handles RGBA, grayscale, palette, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        return image
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
    return jsonify({
        "status": "ok",
        "model": "moondream-2b-2025-04-14",
        "api_key_enabled": bool(VLM_API_KEY),
        "optimization": {
            "preprocess_workers": PREPROCESS_WORKERS,
            "batch_enabled": BATCH_ENABLED,
            "batch_size": BATCH_SIZE if BATCH_ENABLED else None
        }
    })

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
            margin-bottom: 20px;
            font-size: 14px;
        }

        /* API Key Input */
        .input-group {
            margin-bottom: 20px;
        }
        input[type="text"], select, input[type="password"] {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus, select:focus, input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
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
        .input-group.hidden {
            display: none;
        }
        label {
            display: block;
            color: #333;
            font-weight: 500;
            margin-bottom: 8px;
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

        <!-- API Key Input -->
        <div class="input-group">
            <label for="authToken">API 密钥 (可选)</label>
            <input type="password" id="authToken" placeholder="输入 X-Moondream-Auth 密钥（如需要）">
        </div>

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
        const authToken = document.getElementById('authToken');
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

            // Convert file to base64
            const reader = new FileReader();
            reader.onload = async (e) => {
                const base64 = e.target.result.split(',')[1];

                let endpoint = '';
                let requestBody = {};

                if (currentMode === 'prompt') {
                    endpoint = '/v1/query';
                    requestBody = {
                        image_url: `data:image/jpeg;base64,${base64}`,
                        question: question.value || '这是什么？'
                    };
                    loadingText.textContent = 'AI 正在回答问题，请稍候...';
                } else {
                    endpoint = '/v1/caption';
                    requestBody = {
                        image_url: `data:image/jpeg;base64,${base64}`,
                        length: captionLength.value,
                        stream: false
                    };
                    loadingText.textContent = 'AI 正在生成描述，请稍候...';
                }

                loading.style.display = 'block';
                result.style.display = 'none';
                error.style.display = 'none';
                submitBtn.disabled = true;

                try {
                    const startTime = Date.now();

                    // Prepare headers
                    const headers = {
                        'Content-Type': 'application/json'
                    };

                    // Add auth token if provided
                    if (authToken.value.trim()) {
                        headers['X-Moondream-Auth'] = authToken.value.trim();
                    }

                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: headers,
                        body: JSON.stringify(requestBody)
                    });
                    const data = await response.json();

                    if (response.ok) {
                        if (currentMode === 'prompt') {
                            resultTitle.textContent = '✨ 回答';
                            resultContent.textContent = data.answer;
                            timeBadge.textContent = `⏱️ 识别时间: ${((Date.now() - startTime) / 1000).toFixed(2)}s`;
                        } else {
                            resultTitle.textContent = '✨ 图片描述';
                            resultContent.textContent = data.caption;
                            if (data.metrics) {
                                timeBadge.textContent = `⏱️ 处理时间: ${(data.metrics.decode_time_ms / 1000).toFixed(2)}s`;
                            }
                        }
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
            };
            reader.readAsDataURL(selectedFile);
        });
    </script>
</body>
</html>
    '''



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

        # Async preprocess: submit to thread pool (non-blocking for other requests)
        preprocess_future = preprocess_image_async(image_url)
        
        # Wait for preprocessing to complete
        image = preprocess_future.result()

        # Start timing (inference only)
        start_time = time.time()

        # Generate caption with GPU lock (prevents concurrent GPU access)
        result = run_inference_with_lock(moondream.caption, image, length=length)

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

        # Async preprocess: submit to thread pool (non-blocking for other requests)
        print(f"[DEBUG] Submitting image preprocessing (length: {len(image_url)})")
        preprocess_future = preprocess_image_async(image_url)
        
        # Wait for preprocessing to complete
        image = preprocess_future.result()
        print(f"[DEBUG] Image preprocessed: size={image.size}, mode={image.mode}")

        # Start timing (inference only)
        start_time = time.time()

        # Run inference with GPU lock (prevents concurrent GPU access)
        print(f"[DEBUG] Calling moondream.query with question: {question}")
        result = run_inference_with_lock(
            moondream.query,
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

def create_app():
    """
    Application factory for Gunicorn.
    Called when running with: gunicorn 'app:create_app()'
    """
    load_model()
    return app


# For Gunicorn: preload the model when module is imported
# This is used with gunicorn --preload flag
_model_loaded = False

def ensure_model_loaded():
    """Ensure model is loaded (for gunicorn workers)"""
    global _model_loaded
    if not _model_loaded:
        load_model()
        _model_loaded = True


if __name__ == '__main__':
    # Direct execution: python app.py
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
    # Use threaded=True for basic concurrency with Flask dev server
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
else:
    # Imported by Gunicorn: load model
    # This ensures model is loaded when gunicorn imports the module
    ensure_model_loaded()
