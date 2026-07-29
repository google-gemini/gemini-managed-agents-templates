#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import tarfile
import subprocess
import time

def find_env_id_recursive(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "environment_id" and isinstance(v, str):
                return v
            if k == "environment" and isinstance(v, str) and v.startswith("env_"):
                return v
            if k == "environment" and isinstance(v, dict) and "id" in v:
                return v["id"]
            res = find_env_id_recursive(v)
            if res:
                return res
    elif isinstance(obj, list):
        for item in obj:
            res = find_env_id_recursive(item)
            if res:
                return res
    return None

def get_latest_env_id_from_api(api_key):
    url = "https://generativelanguage.googleapis.com/v1beta/environments?pageSize=50"
    req = urllib.request.Request(url, headers={"x-goog-api-key": api_key})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            envs = data.get("environments", [])
            if envs:
                # Sort by last_accessed or created
                sorted_envs = sorted(envs, key=lambda x: x.get("last_accessed") or x.get("created") or "", reverse=True)
                latest = sorted_envs[0]
                print(f"[API Fallback] Selected latest environment: {latest.get('id')}")
                return latest.get("id")
    except Exception as e:
        print(f"[API Fallback Error]: {e}", file=sys.stderr)
    return None

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    prompt = sys.argv[1] if len(sys.argv) > 1 else "Make a motion graphic based on my website https://aistudio.google.com/welcome"

    print(f"Generating payload for prompt: '{prompt}'...")
    payload_str = subprocess.check_output([sys.executable, "../generate_payload.py", prompt], text=True)
    payload_data = json.loads(payload_str)

    url = f"https://generativelanguage.googleapis.com/v1beta/interactions?alt=sse&key={api_key}"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    req = urllib.request.Request(url, data=json.dumps(payload_data).encode("utf-8"), headers=headers, method="POST")

    env_id = None
    print("\nSending interaction request to Gemini Managed Agent API...")

    raw_log_path = "raw_interaction.log"
    with open(raw_log_path, "w", encoding="utf-8") as raw_log:
        try:
            with urllib.request.urlopen(req) as resp:
                for line in resp:
                    line_str = line.decode("utf-8").strip()
                    if not line_str or line_str.startswith(":"):
                        continue
                    if line_str.startswith("data: "):
                        raw_log.write(line_str + "\n")
                        raw_log.flush()
                        data_json = line_str[6:]
                        try:
                            data = json.loads(data_json)
                            
                            # Search for environment ID
                            if not env_id:
                                captured = find_env_id_recursive(data)
                                if captured:
                                    env_id = captured
                                    print(f"\n[Environment ID Captured]: {env_id}\n", flush=True)

                            # Stream output deltas
                            if "delta" in data:
                                delta = data["delta"]
                                if delta.get("type") == "text":
                                    print(delta.get("text", ""), end="", flush=True)
                                elif delta.get("type") == "tool_call":
                                    tc = delta.get("content", {})
                                    name = tc.get("name") or tc.get("function", {}).get("name") or "tool"
                                    print(f"\n[Tool Call: {name}]\n", flush=True)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"\nInteraction error or stream ended: {e}", file=sys.stderr)

    if not env_id:
        print("\nEnvironment ID not found in stream. Attempting API fallback...")
        env_id = get_latest_env_id_from_api(api_key)

    if not env_id:
        print("\nCould not capture or retrieve environment_id.", file=sys.stderr)
        sys.exit(1)

    print(f"\nDownloading environment snapshot tarball for env_id: {env_id}...")
    download_url = f"https://generativelanguage.googleapis.com/v1beta/files/environment-{env_id}:download?alt=media"
    
    tar_path = "snapshot.tar"
    dl_req = urllib.request.Request(download_url, headers={"x-goog-api-key": api_key})
    
    try:
        with urllib.request.urlopen(dl_req) as dl_resp, open(tar_path, "wb") as out_file:
            out_file.write(dl_resp.read())

        print(f"Snapshot downloaded to {tar_path}. Extracting...")
        extract_dir = os.path.abspath("../videos/managed-agent-snapshot")
        os.makedirs(extract_dir, exist_ok=True)

        with tarfile.open(tar_path) as tar:
            tar.extractall(path=extract_dir)

        print(f"\n✅ Environment snapshot extracted to: {extract_dir}")
        print("\nContents of extracted snapshot:")
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), extract_dir)
                print(f"  - {rel_path}")
    except Exception as e:
        print(f"Failed to download snapshot: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
