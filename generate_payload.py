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
import base64
import json
import os
import sys

import yaml


def build_payload(config_dir=".", prompt=None, api_key=None):
    agent_yaml_path = os.path.join(config_dir, "agent.yaml")
    if not os.path.exists(agent_yaml_path):
        raise FileNotFoundError(f"agent.yaml not found in {config_dir}.")

    with open(agent_yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    base_agent = config.get("base_agent", "antigravity-preview-09-2026")
    tools = config.get("tools", [])
    instructions = config.get("instructions")

    sources = []

    # Special credentials source
    key = api_key if api_key is not None else os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")

    sources.append({
        "type": "inline",
        "target": "/credentials/.env",
        "content": f"GEMINI_API_KEY={key}\n",
    })

    # Read AGENTS.md
    agents_md_path = os.path.join(config_dir, "AGENTS.md")
    if os.path.exists(agents_md_path):
        with open(agents_md_path, "r", encoding="utf-8") as f:
            content = f.read()
        sources.append({
            "type": "inline",
            "target": "/.agents/AGENTS.md",
            "content": content,
        })

    # Read requirements.txt if present
    req_path = os.path.join(config_dir, "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path, "r", encoding="utf-8") as f:
            content = f.read()
        sources.append({
            "type": "inline",
            "target": "/.agents/requirements.txt",
            "content": content,
        })

    text_extensions = (
        ".py",
        ".md",
        ".txt",
        ".sh",
        ".csv",
        ".env",
        ".gitignore",
        ".yaml",
        ".yml",
        ".json",
    )

    # Helper function to add files
    def add_files(dir_name):
        dir_path = os.path.join(config_dir, dir_name)
        if os.path.exists(dir_path):
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, config_dir).replace(os.sep, "/")
                    target_path = "/.agents/" + rel_path

                    if file.lower().endswith(text_extensions):
                        try:
                            with open(full_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            sources.append({
                                "type": "inline",
                                "target": target_path,
                                "content": content,
                            })
                        except UnicodeDecodeError:
                            with open(full_path, "rb") as f:
                                content = base64.b64encode(f.read()).decode("utf-8")
                            sources.append({
                                "type": "inline",
                                "target": target_path,
                                "content": content,
                                "encoding": "base64",
                            })
                    else:
                        with open(full_path, "rb") as f:
                            content = base64.b64encode(f.read()).decode("utf-8")
                        sources.append({
                            "type": "inline",
                            "target": target_path,
                            "content": content,
                            "encoding": "base64",
                        })

    add_files("skills")
    add_files("scripts")
    add_files("workspace")

    # Seed fallback default workspace files if workspace copy is not present
    default_interests = os.path.join(config_dir, "interests.default.json")
    workspace_interests = os.path.join(config_dir, "workspace", "interests.json")
    if os.path.exists(default_interests) and not os.path.exists(workspace_interests):
        with open(default_interests, "r", encoding="utf-8") as f:
            content = f.read()
        sources.append({
            "type": "inline",
            "target": "/.agents/workspace/interests.json",
            "content": content,
        })

    # Merge sources from environment.sources in agent.yaml (e.g. gcs, github)
    env = config.get("environment") or {}
    if isinstance(env, dict) and env.get("type") == "remote":
        sources.extend(env.get("sources") or [])

    # Also merge top-level sources from agent.yaml
    sources.extend(config.get("sources") or [])

    environment_payload = {
        "type": "remote",
        "sources": sources,
    }

    # Forward network allowlist configuration if present
    if isinstance(env, dict) and "network" in env:
        environment_payload["network"] = env["network"]
    elif "network" in config:
        environment_payload["network"] = config["network"]

    input_prompt = prompt if prompt is not None else "Hello"

    payload = {
        "input": input_prompt,
        "environment": environment_payload,
        "tools": tools,
        "stream": True,
    }

    if base_agent.startswith("gemini-"):
        payload["model"] = base_agent
    else:
        payload["agent"] = base_agent

    if instructions:
        payload["system_instruction"] = instructions

    return payload


def make_payload():
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Hello"
    try:
        payload = build_payload(config_dir=".", prompt=prompt)
        print(json.dumps(payload, indent=2))
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    make_payload()
