#!/usr/bin/env python3
"""Generate cover image for AI Talk Radio using Gemini 3 Pro Image (Nano Banana Pro).

Usage:
    python3 generate_image.py --workspace ./workspace --prompt "Futuristic radio station"

Requires:
    pip install google-genai
"""

import argparse
import base64
import json
import os
import sys
import warnings
from google import genai

import random

# Suppress experimental warnings from SDK
warnings.filterwarnings("ignore", message="Interactions usage is experimental")

BASE_PROMPT = "A professional podcast cover image for a show titled '{title}' on the 'AI Talk Radio' station. The design features the text '{title}' in a bold, stylish font"

PROMPT_STYLES = [
    " centered on the cover. The background is a vibrant purple with a textured water ripple effect that covers the entire frame, creating a dynamic and clean aesthetic.",
    ". The background is a dark slate blue and charcoal gray with abstract technical blueprints and database diagrams, creating a technical and sophisticated aesthetic.",
    ". The background is a warm orange gradient with clean geometric shapes and subtle grain texture, creating a modern and energetic aesthetic.",
    " in white. The background features abstract organic shapes in earthy tones of terracotta and sage green, with a linen texture, creating a calm and natural aesthetic.",
    ". The background is a clean grid pattern in light gray with colorful isometric 3D blocks scattered around, creating a playful and structural aesthetic.",
    ". The background is a dark moody scene with abstract light leaks and smoke effects in deep blue and crimson, creating a dramatic and mysterious aesthetic.",
    ". The background is a composition of flat color blocks in a Swiss design style (red, black, yellow) with bold typography and negative space, creating a clean and powerful aesthetic.",
    ". The background is a soft pastel gradient of pink and blue with floating abstract 3D spheres and a frosted glass overlay effect, creating a dreamlike and premium aesthetic.",
    ". The background features a dense pattern of stylized monstera leaves and tropical foliage in deep greens, with a subtle paper cutout texture, creating a lush and organic aesthetic.",
    ". The background is a minimalist dark mode design with a subtle carbon fiber texture and a single thin accent line in emerald green, creating a sleek and modern aesthetic.",
    ". The background is a collage of abstract black and white photography fragments and torn paper edges, creating a raw and artistic aesthetic.",
    ". The background is a smooth liquid gold gradient with dynamic flowing curves and a metallic sheen, creating a luxurious and elegant aesthetic.",
    ". The background is a vintage-inspired design with a sepia tone, subtle film grain, and abstract circular shapes overlapping, creating a nostalgic and timeless aesthetic."
]

def generate_image(prompt, output_path, reference=None, aspect_ratio="1:1"):
    client = genai.Client()

    print(f"Generating image with prompt: '{prompt}'")

    input_content = [{"type": "text", "text": prompt}]
    if reference and os.path.exists(reference):
        print(f"Uploading reference image {reference}...")
        ref_file = client.files.upload(file=reference)
        input_content.append({
            "type": "image",
            "uri": ref_file.uri
        })
        print(f"Uploaded as {ref_file.name}")

    models_to_try = [
        "gemini-3.1-flash-image-preview",
        "gemini-3-pro-image-preview"
    ]

    for model_name in models_to_try:
        print(f"Trying model: {model_name}")
        try:
            interaction = client.interactions.create(
                model=model_name,
                input=input_content,
                response_format={
                    "type": "image",
                    "aspect_ratio": aspect_ratio
                }
            )

            for step in getattr(interaction, "steps", []):
                content_list = getattr(step, "content", [])
                for item in content_list:
                    item_type = getattr(item, "type", "")
                    mime_type = getattr(item, "mime_type", "")
                    if item_type == "image" or (isinstance(mime_type, str) and mime_type.startswith("image/")):
                        image_data = base64.b64decode(item.data)
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(image_data)
                        print(f"✅ Image saved to {output_path}")
                        return True

            print(f"⚠️  No image returned in response from {model_name}.")

        except Exception as e:
            print(f"⚠️  Image generation failed with {model_name}: {e}")
            if "500" in str(e) or "api_error" in str(e):
                print("Falling back to next model...")
                continue
            else:
                # If it's a different error (e.g., auth), we might still want to try the fallback, 
                # but let's just continue to the next model anyway.
                print("Falling back to next model...")
                continue

    print("❌ All models failed to generate an image.")
    return False

def main():
    parser = argparse.ArgumentParser(description="Generate cover image with Gemini")
    parser.add_argument("--workspace", default="workspace", help="Workspace directory")
    parser.add_argument("--prompt", help="Image prompt")
    parser.add_argument("--metadata", help="Path to show_notes.json metadata file")
    parser.add_argument("--output", help="Output image path")
    parser.add_argument("--reference", help="Reference image path for consistency")
    parser.add_argument("--aspect_ratio", default="1:1", help="Aspect ratio (e.g., 1:1, 16:9)")
    args = parser.parse_args()

    if not args.prompt and not args.metadata:
        parser.error("Either --prompt or --metadata must be provided")

    prompt = args.prompt

    if args.metadata:
        if not os.path.exists(args.metadata):
            print(f"ERROR: Metadata file not found at {args.metadata}")
            sys.exit(1)

        with open(args.metadata, "r") as f:
            metadata = json.load(f)

        title = metadata.get("show_title", "AI Talk Radio")
        summary = metadata.get("two_sentence_summary", "")

        print(f"Selecting prompt template for title: '{title}'")

        style = random.choice(PROMPT_STYLES)
        prompt = BASE_PROMPT.format(title=title) + style
        print(f"Selected random style. Prompt: '{prompt}'")

    output_path = args.output
    if not output_path:
        output_path = os.path.join(args.workspace, "images", "cover.png")

    success = generate_image(prompt, output_path, reference=args.reference, aspect_ratio=args.aspect_ratio)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
