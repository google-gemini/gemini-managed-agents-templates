# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import json
import yaml
import urllib.request
import urllib.error

# Add parent directory to import generate_payload
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import generate_payload


def run():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("\n❌ Error: GEMINI_API_KEY is not set.", file=sys.stderr)
        print("Please set your Gemini API key before running:\n", file=sys.stderr)
        print("  In PowerShell:", file=sys.stderr)
        print('    $env:GEMINI_API_KEY="your_api_key_here"', file=sys.stderr)
        print('    python run_agent.py\n', file=sys.stderr)
        print("  In Bash:", file=sys.stderr)
        print('    export GEMINI_API_KEY="your_api_key_here"', file=sys.stderr)
        print('    ./probers.sh\n', file=sys.stderr)
        sys.exit(1)

    # Determine prompt
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        with open('agent.yaml', 'r') as f:
            config = yaml.safe_load(f) or {}
            examples = config.get('examples') or []
            prompt = examples[0].get('prompt') if examples and isinstance(examples[0], dict) else None
            if not prompt:
                prompt = "Find the best wireless noise-cancelling headphones under $200."

    print(f"\n🛒 Starting Shopping Agent...")
    print(f"📌 Query: {prompt}\n")
    print("-" * 60)

    # Generate payload
    # Temporary set sys.argv for make_payload
    orig_argv = sys.argv
    sys.argv = ['generate_payload.py', prompt]
    try:
        # We can capture payload using generate_payload logic
        import io
        from contextlib import redirect_stdout
        f_out = io.StringIO()
        with redirect_stdout(f_out):
            generate_payload.make_payload()
        payload_json = f_out.getvalue()
    except SystemExit as e:
        print(f"\n❌ Error generating payload: generate_payload exited with code {e.code}", file=sys.stderr)
        sys.exit(e.code)
    finally:
        sys.argv = orig_argv

    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "x-goog-api-key": api_key,
        "Api-Revision": "2026-05-20",
        "x-server-timeout": "600"
    }

    req = urllib.request.Request(url, data=payload_json.encode('utf-8'), headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            with open('prober_output.log', 'w', encoding='utf-8') as log_file:
                for line in response:
                    decoded = line.decode('utf-8')
                    log_file.write(decoded)
                    
                    if decoded.startswith('data: '):
                        data_str = decoded[6:].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)
                                if isinstance(data, dict):
                                    # Extract content chunks if present
                                    delta = data.get('delta', {}) or data.get('content', {})
                                    if isinstance(delta, str):
                                        print(delta, end='', flush=True)
                                    elif isinstance(delta, dict):
                                        text = delta.get('text', '')
                                        if text:
                                            print(text, end='', flush=True)
                                        else:
                                            # Fallback print event summary
                                            print(data_str)
                                else:
                                    print(data_str)
                            except json.JSONDecodeError:
                                print(data_str)
                    elif decoded.strip() and not decoded.startswith('event:'):
                        print(decoded, end='', flush=True)

        print("\n\n" + "-" * 60)
        print("✅ Finished! Log saved to prober_output.log")

    except urllib.error.HTTPError as e:
        err_content = e.read().decode('utf-8')
        print(f"\n❌ API Error ({e.code}): {err_content}", file=sys.stderr)
        with open('prober_output.log', 'w', encoding='utf-8') as log_file:
            log_file.write(f"HTTPError {e.code}: {err_content}")
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)


if __name__ == '__main__':
    run()
