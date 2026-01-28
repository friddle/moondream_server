"""
Simple test client for Moondream3 HTTP Service
"""

import requests
import sys

def test_identify(image_path, question="What's in this image?"):
    """Test the identification endpoint"""
    url = "http://localhost:5000/identify"

    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {'question': question}

            print(f"Uploading {image_path}...")
            print(f"Question: {question}\n")

            response = requests.post(url, files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                print(f"✓ Success!")
                print(f"Answer: {result['answer']}")
                print(f"Inference Time: {result['inference_time']}\n")
            else:
                print(f"✗ Error: {response.status_code}")
                print(response.json())

    except FileNotFoundError:
        print(f"✗ File not found: {image_path}")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Is it running?")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <image_path> [question]")
        print("Example: python test_client.py photo.jpg")
        print("Example: python test_client.py photo.jpg 'What color is the sky?'")
        sys.exit(1)

    image_path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else "What's in this image?"

    test_identify(image_path, question)
