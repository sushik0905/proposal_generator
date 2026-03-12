import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "gemma3:4b"


def generate_proposal(prompt: str) -> str:
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500
            }
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        response.raise_for_status()

        data = response.json()

        if "response" not in data:
            raise Exception(f"Unexpected Ollama response: {data}")

        text = str(data["response"]).strip()
        if not text:
            raise Exception("Ollama returned empty response.")

        return text

    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to Ollama on 127.0.0.1:11434.")
    except requests.exceptions.ReadTimeout:
        raise Exception("Ollama response timed out. Try a smaller prompt or increase timeout.")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"Ollama HTTP error: {e} | Response: {response.text}")
    except Exception as e:
        raise Exception(f"Generator failed: {e}")