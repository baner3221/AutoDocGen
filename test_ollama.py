"""Test Ollama 3B model connectivity and response time."""
import urllib.request
import json
import time

def test_ollama():
    # Check if Ollama is running
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = [m['name'] for m in data.get('models', [])]
            print(f"Ollama is UP. Available models: {models}")
            
            if 'qwen2.5-coder:3b' not in models:
                print("WARNING: qwen2.5-coder:3b not found!")
                return False
    except Exception as e:
        print(f"Ollama connection failed: {e}")
        return False
    
    # Test 3B model response time
    print("\nTesting qwen2.5-coder:3b response time...")
    payload = {
        "model": "qwen2.5-coder:3b",
        "prompt": "What is a C++ class? Answer in one sentence.",
        "stream": False,
        "options": {"num_predict": 50}
    }
    
    start = time.time()
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            elapsed = time.time() - start
            print(f"Response time: {elapsed:.2f}s")
            print(f"Response: {result.get('response', '')[:200]}")
            return True
    except Exception as e:
        print(f"Model test failed: {e}")
        return False

if __name__ == "__main__":
    test_ollama()
