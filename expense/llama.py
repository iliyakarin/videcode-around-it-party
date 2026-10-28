import base64
import json
import os
import urllib.error
import urllib.request

from expense.extract import InferenceError


def complete(prompt: str, image_path: str) -> str:
    url = os.environ["LLAMA_BASE_URL"].rstrip("/") + "/chat/completions"
    with open(image_path, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode()
    body = {
        "model": os.environ.get("LLAMA_MODEL", "Qwen3VL-8B-Instruct-Q4_K_M.gguf"),
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
            ],
        }],
        "temperature": 0,
    }
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise InferenceError(str(exc)) from exc
    return payload["choices"][0]["message"]["content"]
