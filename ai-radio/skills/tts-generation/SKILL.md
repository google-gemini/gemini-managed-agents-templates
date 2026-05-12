---
name: tts-generation
description: Convert radio show script to speech audio with telephone effect on correspondent voices using the Interactions API.
---

# TTS Generation

Convert the radio show script into speech audio using the Gemini TTS model via the **Interactions API**. Apply a telephone bandpass filter to correspondent voices so they sound like phone call-ins, while keeping the host's voice clean studio-quality.

## Embedded Script

```bash
python3 skills/tts-generation/scripts/generate_tts.py --workspace ./workspace
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--workspace` | `workspace` | Root workspace directory |
| `--workers` | `8` | Max parallel TTS worker threads |

### What it does

1. Reads the script from `{workspace}/data/script.md`.
2. Parses it into individual `(speaker, text)` turns and assigns voices.
3. Generates TTS for all turns **in parallel** using a thread pool (default 8 workers).
4. **Retries** each failed turn up to 3 times with exponential backoff.
5. Applies an ffmpeg telephone bandpass filter (300Hz–3.4kHz) to correspondent voices.
6. Keeps the host (Paul) audio clean and unfiltered.
7. Concatenates all segments in original script order into a single WAV.

### Dependencies

- `google-genai` (>= 2.0.0)
- `ffmpeg` (system)
## API Details

Uses the **Interactions API** with single-speaker TTS — no multi-speaker workaround needed.

## Voice Assignment

Voices are assigned **dynamically** based on `[Male]` / `[Female]` gender tags in the script:

| Speaker | Voice | Audio Treatment |
|---------|-------|-----------------|
| **Paul** (host) | `Puck` | **Clean** — no filter |
| Caller `[Female]` — 1st | `Kore` | **Telephone filter** |
| Caller `[Female]` — 2nd | `Aoede` | **Telephone filter** |
| Caller `[Male]` — 1st | `Charon` | **Telephone filter** |
| Caller `[Male]` — 2nd | `Fenrir` | **Telephone filter** |

Voices cycle round-robin if there are more callers than available voices. Accent tags (`[Accent: Irish]`, etc.) are injected into the TTS prompt to influence pronunciation.

## Telephone Filter

Applied via ffmpeg to correspondent audio segments:

```
highpass=f=300, lowpass=f=3400, acompressor, volume=1.5
```

This simulates the standard telephone bandwidth (300Hz–3.4kHz) and adds compression to mimic phone codec dynamics.

## Output

- **Primary output**: `{workspace}/audio/speech/speech.wav`
- **Format**: WAV, 24kHz, 16-bit PCM, mono
- **Intermediate segments**: `{workspace}/audio/speech/segments/turn_*.wav`
