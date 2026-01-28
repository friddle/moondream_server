#!/usr/bin/env python3
"""
Model Download Script for Init Container
Downloads the Moondream model with progress logging
"""

import os
import sys
import time
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import snapshot_download
import torch

MODEL_ID = "moondream/moondream-2b-2025-04-14"
HF_TOKEN = os.environ.get('HF_TOKEN')
CACHE_DIR = "/root/.cache/huggingface"

def download_model():
    """Download Moondream model with progress"""
    print("=" * 60)
    print("🔥 Starting Moondream Model Download")
    print("=" * 60)
    print(f"Model ID: {MODEL_ID}")
    print(f"Cache directory: {CACHE_DIR}")
    print(f"HuggingFace Token: {'✓ Set' if HF_TOKEN else '✗ Not set (will use public access)'}")
    print()

    start_time = time.time()

    try:
        print("📥 Checking for existing model files...")
        # Check if the model is already downloaded
        try:
            AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                trust_remote_code=True,
                local_files_only=True,
                token=HF_TOKEN,
            )
            print("✅ Model already exists in cache. No download needed.")
            print("=" * 60)
            return 0
        except EnvironmentError:
            print("   Model not found in cache. Starting download...")

        print("   This may take 5-15 minutes depending on network speed")
        print("   Model size: ~4GB compressed, ~9GB uncompressed")
        print()

        # Download model using snapshot_download for better progress
        snapshot_download(
            repo_id=MODEL_ID,
            cache_dir=CACHE_DIR,
            token=HF_TOKEN,
            resume_download=True,
        )

        # Verify download by loading the model
        print("\n🔍 Verifying model files...")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            trust_remote_code=True,
            token=HF_TOKEN,
            torch_dtype=torch.bfloat16,
            attn_implementation="eager",
            low_cpu_mem_usage=True,
        ).cuda()

        elapsed = time.time() - start_time

        print()
        print("=" * 60)
        print("✅ Model Download Complete and Verified!")
        print("=" * 60)
        print(f"⏱️  Time taken: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"💾 Cache location: {CACHE_DIR}")
        print()
        print("🚀 Model ready for inference!")
        print("=" * 60)

        # Cleanup to free memory
        del model
        torch.cuda.empty_cache()

        return 0

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Model Download Failed!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Possible issues:")
        print("  • Network connectivity to huggingface.co")
        print("  • Invalid HuggingFace token")
        print("  • Insufficient disk space")
        print("  • CUDA/GPU not available")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(download_model())
