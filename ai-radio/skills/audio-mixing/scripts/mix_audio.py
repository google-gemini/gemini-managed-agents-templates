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
"""Mix speech audio and background music into the final AI Talk Radio radio show.

Usage:
    python3 mix_audio.py --workspace ./workspace

Requires:
    pip install pydub
    ffmpeg (system)

Output:
    {workspace}/audio/final/ai_radio.mp3
"""

import argparse
import os
from pydub import AudioSegment


def main():
    parser = argparse.ArgumentParser(description="Mix AI Talk Radio audio")
    parser.add_argument("--workspace", default="workspace", help="Workspace directory")
    args = parser.parse_args()

    speech_path = os.path.join(args.workspace, "audio", "speech", "speech.wav")
    music_path = os.path.join(args.workspace, "audio", "music", "background.mp3")
    output_dir = os.path.join(args.workspace, "audio", "final")
    os.makedirs(output_dir, exist_ok=True)

    print("=== AI Talk Radio: Audio Mixing ===\n")

    # Load speech
    print("Loading speech audio...")
    speech = AudioSegment.from_wav(speech_path)
    print(f"Speech duration: {len(speech) / 1000:.1f}s")

    # Add padding to speech (3 seconds of silence)
    print("Adding padding to speech...")
    padding = AudioSegment.silent(duration=3000)
    speech = speech + padding
    print(f"Speech duration after padding: {len(speech) / 1000:.1f}s")

    has_music = os.path.exists(music_path)

    if has_music:
        print("Loading background music...")
        music = AudioSegment.from_mp3(music_path)

        # Intro music (15s)
        intro_music = music[:15000]
        intro_music = intro_music - 15
        intro_music = intro_music.fade_in(1000).fade_out(3000)

        # Outro music (15s)
        outro_music = music[:15000]
        outro_music = outro_music - 15
        outro_music = outro_music.fade_in(3000).fade_out(1000)

        # Overlay speech on music
        print("Mixing speech + music (intro and outro)...")
        combined = speech.overlay(intro_music, position=0)
        
        outro_position = len(speech) - 15000
        if outro_position < 0:
            outro_position = 0
        combined = combined.overlay(outro_music, position=outro_position)
    else:
        print("No background music — speech-only output.")
        combined = speech

    # Overall fades
    combined = combined.fade_in(500).fade_out(2000)

    # Export MP3
    try:
        mp3_path = os.path.join(output_dir, "ai_radio.mp3")
        combined.export(mp3_path, format="mp3", bitrate="192k")
        print(f"Saved MP3: {mp3_path}")
    except Exception as e:
        print(f"MP3 export failed: {e}")
        mp3_path = None

    # Stats
    if mp3_path and os.path.exists(mp3_path):
        mp3_mb = os.path.getsize(mp3_path) / (1024 * 1024)
        print(f"\n  MP3: {mp3_mb:.1f} MB")
    print(f"  Duration: {len(combined) / 1000:.1f}s")
    print(f"\n✅ AI Talk Radio mixed successfully!")


if __name__ == "__main__":
    main()
