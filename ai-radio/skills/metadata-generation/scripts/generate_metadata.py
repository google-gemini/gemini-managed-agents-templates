#!/usr/bin/env python3
"""Generate show metadata (JSON) from audio and transcript using the Interactions API.

Usage:
    python3 generate_metadata.py --workspace ./workspace

Requires:
    pip install google-genai pydub

Output:
    {workspace}/data/show_notes.json
"""

import argparse
import os
import json
from datetime import datetime
from google import genai
from pydub import AudioSegment

def main():
    parser = argparse.ArgumentParser(description="Generate AI Talk Radio show metadata")
    parser.add_argument("--workspace", default="workspace", help="Workspace directory")
    args = parser.parse_args()

    client = genai.Client()

    # Paths
    transcript_path = os.path.join(args.workspace, "data", "script.md")
    audio_mp3 = os.path.join(args.workspace, "audio", "final", "ai_radio.mp3")
    audio_wav = os.path.join(args.workspace, "audio", "final", "ai_radio.wav")
    output_path = os.path.join(args.workspace, "data", "show_notes.json")

    # Check inputs
    if not os.path.exists(transcript_path):
        print(f"ERROR: Transcript not found at {transcript_path}")
        return

    audio_path = None
    if os.path.exists(audio_mp3):
        audio_path = audio_mp3
    elif os.path.exists(audio_wav):
        audio_path = audio_wav

    if not audio_path:
        print(f"ERROR: Audio file not found in {os.path.dirname(audio_mp3)}")
        return

    print("=== AI Talk Radio: Metadata Generation ===\n")
    print(f"Transcript: {transcript_path}")
    print(f"Audio: {audio_path}")

    # Read transcript
    with open(transcript_path, "r") as f:
        transcript_text = f.read()

    # Get duration via pydub
    duration_str = "Unknown"
    try:
        audio = AudioSegment.from_file(audio_path)
        duration_seconds = len(audio) / 1000.0
        duration_str = f"{int(duration_seconds // 60):02d}:{int(duration_seconds % 60):02d}"
        print(f"Audio duration: {duration_str}")
    except Exception as e:
        print(f"Warning: Could not determine duration via pydub: {e}")

    # Upload audio to Gemini Files API
    print("Uploading audio to Gemini Files API...")
    try:
        uploaded_file = client.files.upload(file=audio_path)
        print(f"Uploaded file URI: {uploaded_file.uri}")
    except Exception as e:
        print(f"ERROR: Failed to upload audio: {e}")
        return

    today_date = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""You are an AI assistant analyzing a radio show production.
You are provided with the audio file of the show and the text transcript.

Based on the audio and transcript, generate a JSON object containing the following information:
1. `show_title`: A catchy title for this show episode (maximum of 5 words).
2. `show_duration`: The duration of the show (use "{duration_str}" if accurate, or estimate from audio).
3. `two_sentence_summary`: A two-sentence summary of the show's content.
4. `date_of_generation`: The date this show was generated (use "{today_date}").
5. `timecoded_transcript`: A list of objects, each containing:
    - `timecode`: The approximate timecode when this line starts (in MM:SS format).
    - `speaker`: The name of the speaker.
    - `text`: The text spoken.

The transcript provided is:
{transcript_text}

You MUST align the transcript with the audio to provide accurate timecodes. Callers usually have a telephone effect.

Return ONLY a valid JSON object. Do NOT wrap it in markdown code blocks. Ensure the output is parseable by json.loads.
"""

    print("Calling Gemini via Interactions API...")
    try:
        interaction = client.interactions.create(
            model="gemini-3-flash-preview",
            input=[
                {"type": "text", "text": prompt},
                {
                    "type": "audio",
                    "uri": uploaded_file.uri,
                    "mime_type": "audio/mpeg" if audio_path.endswith(".mp3") else "audio/wav"
                }
            ]
        )

        # Access response
        response_text = ""
        if hasattr(interaction, "steps") and interaction.steps and interaction.steps[-1].content:
            response_text = interaction.steps[-1].content[0].text
        else:
             print("ERROR: No output received from Gemini.")
             return

        # Clean up potential markdown wrapping if Gemini ignored the instruction
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Validate JSON
        try:
            json_data = json.loads(response_text)

            # Save
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(json_data, f, indent=2)

            print(f"✅ Metadata saved to {output_path}")

        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON response: {e}")
            print("Raw response was:")
            print(response_text)

    except Exception as e:
        print(f"ERROR: API call failed: {e}")

if __name__ == "__main__":
    main()
