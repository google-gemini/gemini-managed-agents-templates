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
import json
import os
import sys

import yaml

# Import build_payload from generate_payload
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from generate_payload import build_payload


def test_build_payload_forwards_network_allowlist(tmp_path):
    agent_yaml = tmp_path / "agent.yaml"
    agent_yaml.write_text(
        yaml.dump({
            "id": "test-agent",
            "base_agent": "antigravity-preview-09-2026",
            "tools": [{"type": "code_execution"}],
            "environment": {
                "type": "remote",
                "sources": [{"type": "gcs", "source": "gs://test-bucket", "target": ".agents/workspace"}],
                "network": {
                    "allowlist": [{"domain": "example.com"}, {"domain": "api.github.com"}]
                },
            },
        }),
        encoding="utf-8",
    )

    payload = build_payload(config_dir=str(tmp_path), prompt="Run test", api_key="secret-api-key")

    assert payload["input"] == "Run test"
    assert payload["agent"] == "antigravity-preview-09-2026"
    assert "network" in payload["environment"]
    assert payload["environment"]["network"]["allowlist"] == [
        {"domain": "example.com"},
        {"domain": "api.github.com"},
    ]


def test_build_payload_includes_requirements_txt(tmp_path):
    agent_yaml = tmp_path / "agent.yaml"
    agent_yaml.write_text(
        yaml.dump({
            "id": "test-agent",
            "base_agent": "antigravity-preview-09-2026",
        }),
        encoding="utf-8",
    )
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("pandas>=2.0.0\nscikit-learn\n", encoding="utf-8")

    payload = build_payload(config_dir=str(tmp_path), api_key="test-key")

    targets = [s["target"] for s in payload["environment"]["sources"]]
    assert "/.agents/requirements.txt" in targets
    req_source = next(s for s in payload["environment"]["sources"] if s["target"] == "/.agents/requirements.txt")
    assert "pandas>=2.0.0" in req_source["content"]


def test_build_payload_posix_paths_and_json_extension(tmp_path):
    agent_yaml = tmp_path / "agent.yaml"
    agent_yaml.write_text(
        yaml.dump({
            "id": "test-agent",
            "base_agent": "gemini-2.5-pro",
        }),
        encoding="utf-8",
    )
    skills_dir = tmp_path / "skills" / "sub_skill"
    skills_dir.mkdir(parents=True)
    skill_file = skills_dir / "SKILL.md"
    skill_file.write_text("# Sub Skill", encoding="utf-8")

    json_file = skills_dir / "config.json"
    json_file.write_text(json.dumps({"key": "value"}), encoding="utf-8")

    payload = build_payload(config_dir=str(tmp_path), api_key="test-key")

    # When base_agent starts with gemini-, it should map to model instead of agent
    assert payload["model"] == "gemini-2.5-pro"
    assert "agent" not in payload

    targets = [s["target"] for s in payload["environment"]["sources"]]
    # POSIX slash required, no backslashes
    assert "/.agents/skills/sub_skill/SKILL.md" in targets
    assert "/.agents/skills/sub_skill/config.json" in targets

    # JSON should be inline text, not base64
    json_source = next(s for s in payload["environment"]["sources"] if s["target"] == "/.agents/skills/sub_skill/config.json")
    assert json_source.get("encoding") is None
    assert json.loads(json_source["content"]) == {"key": "value"}


def test_build_payload_seeds_interests_default(tmp_path):
    agent_yaml = tmp_path / "agent.yaml"
    agent_yaml.write_text(
        yaml.dump({
            "id": "news-curator",
            "base_agent": "antigravity-preview-09-2026",
        }),
        encoding="utf-8",
    )
    default_interests = tmp_path / "interests.default.json"
    default_interests.write_text('{"topics": ["ai"]}', encoding="utf-8")

    payload = build_payload(config_dir=str(tmp_path), api_key="test-key")

    targets = [s["target"] for s in payload["environment"]["sources"]]
    assert "/.agents/workspace/interests.json" in targets


def test_build_payload_missing_agent_yaml_raises(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError, match="agent.yaml not found"):
        build_payload(config_dir=str(tmp_path), api_key="test-key")


def test_build_payload_missing_api_key_raises(tmp_path, monkeypatch):
    import pytest

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    agent_yaml = tmp_path / "agent.yaml"
    agent_yaml.write_text("id: test-agent\n", encoding="utf-8")

    with pytest.raises(ValueError, match="GEMINI_API_KEY environment variable not set"):
        build_payload(config_dir=str(tmp_path), api_key=None)


def test_build_payload_empty_yaml_and_null_sources(tmp_path):
    agent_yaml = tmp_path / "agent.yaml"
    # Null / empty sources in YAML should not raise TypeError
    agent_yaml.write_text("id: test-agent\nsources:\nenvironment:\n  type: remote\n  sources:\n", encoding="utf-8")

    payload = build_payload(config_dir=str(tmp_path), api_key="test-key")
    assert payload["agent"] == "antigravity-preview-09-2026"
    assert isinstance(payload["environment"]["sources"], list)
