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
"""Generate TTS audio with telephone effect on correspondent voices using the Interactions API.

Usage:
    python3 generate_tts.py --workspace ./workspace

Requires:
    pip install google-genai
    ffmpeg (system)

Output:
    {workspace}/audio/speech/speech.wav
"""

import argparse
import base64
import os
import re
import subprocess
import time
import wave
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai

# Suppress experimental warnings from SDK
warnings.filterwarnings("ignore", message="Interactions usage is experimental")

# Voice mapping — each speaker gets a unique Gemini TTS voice
VOICE_MAP = {
    "Paul": "Puck",     # Host — studio quality
}

FEMALE_VOICES = ["Kore", "Aoede"]
MALE_VOICES = ["Charon", "Fenrir"]

MAX_RETRIES = 3
MAX_WORKERS = 8

PROFILES = {
    "Paul": {
        "profile": "# AUDIO PROFILE: Paul\n## Role: Community Radio Host\n## Persona: Professional, warm, and engaging British radio host.",
        "scene": "## THE SCENE: The London Studio\nA professional studio in London. Paul is sitting comfortably, speaking into a high-quality microphone with a warm and authoritative tone.",
        "notes": "### DIRECTOR'S NOTES\nStyle: Professional, warm, engaging, and measured.\nPacing: Steady but dynamic.\nAccent: British English accent as heard in Croydon, England.",
    },
    "default_caller": {
        "profile": "# AUDIO PROFILE: Caller\n## Role: Tech-savvy individual calling in to a radio show.\n## Persona: Nerdy, conversational, not a professional broadcaster.",
        "scene": "## THE SCENE: Remote Location via Phone\nCalling in from a home, office, or public space. The audio quality is that of a telephone call.",
        "notes": "### DIRECTOR'S NOTES\nStyle: Conversational, natural.\nPacing: Normal conversational pace.\nAccent: American English.",
    },
}


def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    """Save raw PCM data as a WAV file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def split_script_by_turns(script_text):
    """Parse script into ordered (speaker, text) turns."""
    turns = []
    for line in script_text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            speaker = line.split(':')[0].strip()
            text = ':'.join(line.split(':')[1:]).strip()
            if text:
                turns.append((speaker, text))
    return turns


def generate_tts_single(client, speaker, text, output_path, voice, accent):
    """Generate TTS for a single speaker turn using the Interactions API."""
    profile_data = PROFILES.get(speaker, PROFILES.get("default_caller", {}))

    notes = profile_data.get('notes', '')
    notes = re.sub(r'Accent:.*', f'Accent: {accent}', notes)

    prompt = f"""{profile_data.get('profile', '')}

{profile_data.get('scene', '')}

{notes}

#### TRANSCRIPT
{text}
"""

    interaction = client.interactions.create(
        model="gemini-3.1-flash-tts-preview",
        input=prompt,
        response_modalities=["audio"],
        generation_config={
            "speech_config": [{"voice": voice, "language": "en-US"}]
        },
        store=False,
    )

    for step in getattr(interaction, "steps", []):
        for item in getattr(step, "content", []):
            item_type = getattr(item, "type", "")
            mime_type = getattr(item, "mime_type", "")
            if item_type == "audio" or (isinstance(mime_type, str) and mime_type.startswith("audio/")):
                pcm_data = base64.b64decode(item.data)
                wave_file(output_path, pcm_data)
                return True

    return False


def apply_telephone_filter(input_path, output_path, boost=False):
    """Apply telephone bandpass filter (300Hz-3400Hz) via ffmpeg.

    Simulates a phone call:
    1. Highpass at 300Hz — cuts rumble
    2. Lowpass at 3400Hz — cuts highs (telephone bandwidth)
    3. Compression — mimics phone codec dynamics
    4. Volume adjustment (boosted if requested)
    """
    vol = "1.8" if boost else "1.5"
    subprocess.run([
        "ffmpeg", "-y",
        "-loglevel", "warning",
        "-i", input_path,
        "-af", (
            "highpass=f=300,"
            "lowpass=f=3400,"
            "acompressor=threshold=-20dB:ratio=4:attack=5:release=50,"
            f"volume={vol}"
        ),
        output_path
    ], check=True, capture_output=True)


def concatenate_wav_files(file_list, output_path):
    """Concatenate WAV files (same format) into one."""
    all_pcm = b""
    for f in file_list:
        with wave.open(f, "rb") as wf:
            all_pcm += wf.readframes(wf.getnframes())
    wave_file(output_path, all_pcm)


def process_turn(client, turn_index, speaker, text, voice, accent, segments_dir, boost=False):
    """Generate TTS for a single turn with retries and post-processing.

    Returns (turn_index, final_path) on success, or (turn_index, None) on failure.
    """
    raw_path = os.path.join(segments_dir, f"turn_{turn_index:03d}_raw.wav")
    final_path = os.path.join(segments_dir, f"turn_{turn_index:03d}.wav")

    # Generate TTS with retries
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            success = generate_tts_single(client, speaker, text, raw_path, voice, accent)
            if success:
                break
            print(f"    [{turn_index}] Attempt {attempt}/{MAX_RETRIES}: no audio returned")
        except Exception as e:
            print(f"    [{turn_index}] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2 * attempt)  # Exponential-ish backoff
    else:
        print(f"    [{turn_index}] ✗ All {MAX_RETRIES} attempts failed, skipping")
        return (turn_index, None)

    # Apply telephone filter for callers (not Paul)
    if speaker != "Paul":
        try:
            apply_telephone_filter(raw_path, final_path, boost=boost)
            print(f"    [{turn_index}] ✓ {speaker} ({voice}) + telephone filter{' (boosted)' if boost else ''}")
        except Exception:
            os.rename(raw_path, final_path)
            print(f"    [{turn_index}] ✓ {speaker} ({voice}) (filter failed, using raw)")
    else:
        os.rename(raw_path, final_path)
        print(f"    [{turn_index}] ✓ {speaker} ({voice}) clean studio")

    return (turn_index, final_path)


def main():
    parser = argparse.ArgumentParser(description="Generate TTS with telephone effect")
    parser.add_argument("--workspace", default="workspace", help="Workspace directory")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="Max parallel TTS workers")
    args = parser.parse_args()

    client = genai.Client()

    # Read script
    script_path = os.path.join(args.workspace, "data", "script.md")
    with open(script_path) as f:
        script = f.read()

    turns = split_script_by_turns(script)
    print(f"=== AI Talk Radio: TTS Generation ===\n")
    print(f"Found {len(turns)} speaker turns")
    print(f"Generating in parallel with {args.workers} workers\n")

    segments_dir = os.path.join(args.workspace, "audio", "speech", "segments")
    os.makedirs(segments_dir, exist_ok=True)

    # --- Phase 1: Parse all turns and assign voices (sequential) ---
    assigned_voices = {"Paul": "Puck"}
    assigned_accents = {"Paul": "British English accent as heard in Croydon, England"}
    female_index = 0
    male_index = 0
    prepared_turns = []

    for i, (speaker, text) in enumerate(turns):
        # Parse gender tag
        gender = "Male"  # default
        if "[Female]" in text:
            gender = "Female"
            text = text.replace("[Female]", "").strip()
        elif "[Male]" in text:
            gender = "Male"
            text = text.replace("[Male]", "").strip()

        # Parse accent tag
        accent = "American English"  # default
        accent_match = re.search(r'\[Accent: ([^\]]+)\]', text)
        if accent_match:
            accent = accent_match.group(1)
            text = re.sub(r'\[Accent: [^\]]+\]', '', text).strip()

        # Parse boost tag
        boost = False
        if "[boost]" in text:
            boost = True
            text = text.replace("[boost]", "").strip()

        if speaker not in assigned_voices:
            if gender == "Female":
                assigned_voices[speaker] = FEMALE_VOICES[female_index % len(FEMALE_VOICES)]
                female_index += 1
            else:
                assigned_voices[speaker] = MALE_VOICES[male_index % len(MALE_VOICES)]
                male_index += 1

        if speaker not in assigned_accents:
            assigned_accents[speaker] = accent

        voice = assigned_voices[speaker]
        accent = assigned_accents[speaker]

        prepared_turns.append((i, speaker, text, voice, accent, boost))
        print(f"  [{i+1}/{len(turns)}] {speaker} ({voice}, {accent}){' [boost]' if boost else ''}: {text[:60]}...")

    # --- Phase 2: Generate TTS in parallel ---
    print(f"\nStarting parallel generation...")
    results = {}

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                process_turn, client, i, speaker, text, voice, accent, segments_dir, boost
            ): i
            for i, speaker, text, voice, accent, boost in prepared_turns
        }

        for future in as_completed(futures):
            turn_index, final_path = future.result()
            results[turn_index] = final_path

    # --- Phase 3: Concatenate in original order ---
    segment_files = []
    for i in range(len(turns)):
        path = results.get(i)
        if path is not None:
            segment_files.append(path)

    output_path = os.path.join(args.workspace, "audio", "speech", "speech.wav")
    concatenate_wav_files(segment_files, output_path)

    # Stats
    with wave.open(output_path, "rb") as wf:
        duration = wf.getnframes() / wf.getframerate()

    failed = len(turns) - len(segment_files)
    print(f"\n✅ TTS complete!")
    print(f"   Output: {output_path}")
    print(f"   Duration: {duration:.1f}s | Segments: {len(segment_files)}/{len(turns)}", end="")
    if failed:
        print(f" ({failed} failed)")
    else:
        print()


if __name__ == "__main__":
    main()
