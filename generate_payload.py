#!/usr/bin/env python3
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
import json
import yaml
import base64
import sys

def make_payload():
    if not os.path.exists('agent.yaml'):
        print("Error: agent.yaml not found in current directory.", file=sys.stderr)
        sys.exit(1)
        
    with open('agent.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    agent_id = config.get('id')
    base_agent = config.get('base_agent', 'antigravity-preview-05-2026')
    tools = config.get('tools', [])
    instructions = config.get('instructions')
    
    sources = []
    
    # Special credentials source
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)
        
    sources.append({
        "type": "inline",
        "target": "/credentials/.env",
        "content": f"GEMINI_API_KEY={api_key}\n"
    })
    
    # Read AGENTS.md
    if os.path.exists('AGENTS.md'):
        with open('AGENTS.md', 'r') as f:
            content = f.read()
        sources.append({
            "type": "inline",
            "target": "/.agents/AGENTS.md",
            "content": content
        })
        
    # Helper function to add files
    def add_files(dir_path):
        if os.path.exists(dir_path):
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    target_path = "/.agents/" + full_path.replace('\\', '/')
                    
                    # Check if binary or text
                    # Simple heuristic: check extension
                    if file.lower().endswith(('.py', '.md', '.txt', '.sh', '.csv', '.env', '.gitignore', '.yaml')):
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            sources.append({
                                "type": "inline",
                                "target": target_path,
                                "content": content
                            })
                        except UnicodeDecodeError:
                            # Fallback to base64 if utf-8 decode fails
                            with open(full_path, 'rb') as f:
                                content = base64.b64encode(f.read()).decode('utf-8')
                            sources.append({
                                "type": "inline",
                                "target": target_path,
                                "content": content,
                                "encoding": "base64"
                            })
                    else:
                        # Assume binary, base64 encode
                        with open(full_path, 'rb') as f:
                            content = base64.b64encode(f.read()).decode('utf-8')
                        sources.append({
                            "type": "inline",
                            "target": target_path,
                            "content": content,
                            "encoding": "base64"
                        })

    add_files('skills')
    add_files('workspace')

    # Merge sources from environment.sources in agent.yaml (e.g. gcs, github)
    env = config.get('environment', {})
    if isinstance(env, dict) and env.get('type') == 'remote':
        for src in env.get('sources', []):
            sources.append(src)

    # Also merge top-level sources from agent.yaml
    for src in config.get('sources', []):
        sources.append(src)

    prompt = sys.argv[1] if len(sys.argv) > 1 else "Hello"
    
    payload = {
        "input": prompt,
        "environment": {
            "type": "remote",
            "sources": sources
        },
        "tools": tools,
        "stream": True
    }
    
    if base_agent.startswith('gemini-'):
        payload["model"] = base_agent
    else:
        payload["agent"] = base_agent
    
    if instructions:
        payload["system_instruction"] = instructions
        
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    make_payload()
