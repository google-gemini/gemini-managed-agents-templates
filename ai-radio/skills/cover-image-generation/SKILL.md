---
name: cover-image-generation
description: Generate cover images for the radio show using Gemini 3 Flash Image (with fallback to Pro).
---

# Image Generation Skill

This skill generates an appropriate cover image for the radio show based on a prompt, using the Gemini 3 Flash Image model, with a fallback to the Gemini 3 Pro Image model ("Nano Banana Pro") if needed.

## Requirements

- Python 3.10+
- `google-genai` Python package (>= 2.0.1)
## Instructions

1. **Generate an image** (Recommended: use the metadata file directly):
   ```bash
   python3 skills/cover-image-generation/scripts/generate_image.py \
     --workspace ./workspace \
     --metadata ./workspace/data/show_notes.json
   ```
   *Note: Using `--metadata` will automatically extract the show title and apply a random, high-quality prompt template. This is the preferred method.*

   **Alternative** (Manual prompt):
   ```bash
   python3 skills/cover-image-generation/scripts/generate_image.py \
     --workspace ./workspace \
     --prompt "A prompt describing the image"
   ```

2. **Output**:
   - The image will be saved to `{workspace}/images/cover.png`.

## Model

- Primary Model: `gemini-3-flash-image-preview`
- Fallback Model: `gemini-3-pro-image-preview`
- Resolution: 1:1 (default)

## Prompting rules

When using the `--metadata` option, this skill uses a set of predefined prompt templates and selects one at random to generate cover images. It dynamically inserts the show title into the selected template.

- **Example Prompt**: `"A professional podcast cover image for a show titled 'AI Talk Radio' on the 'AI Talk Radio' station. The design features the text 'AI Talk Radio' in a bold, stylish white font centered on the cover. The background is a vibrant purple with a textured water ripple effect that covers the entire frame, creating a dynamic and clean aesthetic."`

If you choose to use the `--prompt` option instead, you must construct the prompt yourself. In that case, follow these rules:

## Forbidden themes

- Do not ask for futuristic, cyberpunk or neon themes
- Do not include any text other than the show title
