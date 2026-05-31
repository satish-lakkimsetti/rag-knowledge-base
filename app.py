import urllib.request
import urllib.error
import json


def check_ollama(host="http://localhost:11434"):
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=5) as response:
            if response.status == 200:
                print(f"[OK] Ollama is reachable at {host}")
                return True
    except urllib.error.URLError as e:
        print(f"[FAIL] Ollama is NOT reachable at {host}: {e.reason}")
    except Exception as e:
        print(f"[FAIL] Ollama check failed: {e}")
    return False


def check_weaviate(host="http://localhost:8080"):
    try:
        with urllib.request.urlopen(f"{host}/v1/.well-known/ready", timeout=5) as response:
            if response.status == 200:
                print(f"[OK] Weaviate is reachable at {host}")
                return True
    except urllib.error.URLError as e:
        print(f"[FAIL] Weaviate is NOT reachable at {host}: {e.reason}")
    except Exception as e:
        print(f"[FAIL] Weaviate check failed: {e}")
    return False


if __name__ == "__main__":
    ollama_ok = check_ollama()
    weaviate_ok = check_weaviate()

    if ollama_ok and weaviate_ok:
        print("\nBoth services are up and ready.")
    else:
        print("\nOne or more services are unavailable. Check that Ollama and Weaviate are running.")
