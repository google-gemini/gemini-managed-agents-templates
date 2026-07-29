#!/bin/bash
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
if [ -z "$GEMINI_API_KEY" ]; then
  echo "Error: GEMINI_API_KEY is not set."
  exit 1
fi

# Read prompt from first example in agent.yaml
PROMPT=$(python3 -c "import yaml; print(yaml.safe_load(open('agent.yaml'))['examples'][0]['prompt'])")

# Generate payload
python3 ../generate_payload.py "$PROMPT" > probers.json

# Send request (saving output to prober_output.log)
curl -X POST "https://generativelanguage.googleapis.com/v1beta/interactions" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Api-Revision: 2026-05-20" \
  -H "x-server-timeout: 600" \
  -d @probers.json > prober_output.log

# Clean up
rm probers.json
