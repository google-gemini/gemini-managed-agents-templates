#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import tarfile

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    env_id = sys.argv[1] if len(sys.argv) > 1 else "35661302b349a6fcbe929bda18974043"
    prompt = "Please proceed: write videos/aistudio-motion/compositions/index.html and render the MP4 to videos/aistudio-motion/renders/video.mp4 using hyperframes render."

    payload = {
        "agent": "antigravity-preview-05-2026",
        "input": prompt,
        "environment": env_id,
        "tools": [
            {"type": "code_execution"}
        ],
        "stream": True
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/interactions?alt=sse&key={api_key}"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

    print(f"Resuming multi-turn interaction on remote environment: {env_id}...")
    try:
        with urllib.request.urlopen(req) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if not line_str or line_str.startswith(":"):
                    continue
                if line_str.startswith("data: "):
                    data_json = line_str[6:]
                    try:
                        data = json.loads(data_json)
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
        print(f"\nInteraction error: {e}", file=sys.stderr)

    print(f"\n\nDownloading updated environment snapshot for env_id: {env_id}...")
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
        print("\nSearching for rendered video or HTML files in snapshot:")
        found = False
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if f.endswith((".mp4", ".html", ".png")):
                    rel_path = os.path.relpath(os.path.join(root, f), extract_dir)
                    print(f"  🎬 {rel_path}")
                    found = True
        if not found:
            print("  (No .mp4 / .html files found yet)")
    except Exception as e:
        print(f"Failed to download snapshot: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
