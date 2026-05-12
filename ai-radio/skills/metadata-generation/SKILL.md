---
name: metadata-generation
description: Generate show metadata (JSON) containing timecoded transcript, title, duration, summary, and date by sending audio and transcript to Gemini.
---

# Metadata Generation

Generate a structured JSON file containing metadata for the radio show. This is done by sending the final mixed audio file and the original transcript back to Gemini.

## Prerequisites

```bash
pip install google-genai
```

## Workflow

1.  **Read Inputs**: Load the transcript from `./workspace/data/script.md` and the final audio from `./workspace/audio/final/ai_radio.mp3`.
2.  **Upload Audio**: Upload the audio file to the Gemini Files API.
3.  **Generate Metadata**: Call Gemini (e.g., `gemini-3-flash-preview`) using the Interactions API, passing the uploaded audio file and the transcript.
4.  **Save Output**: Save the resulting JSON to `./workspace/data/show_notes.json`.

## Python Code

The skill is implemented in `scripts/generate_metadata.py`.

```bash
# Example usage
python3 skills/metadata-generation/scripts/generate_metadata.py --workspace ./workspace
```

## Output

The skill produces a JSON file at `./workspace/data/show_notes.json` with the following structure:

```json
{
  "show_title": "...",
  "show_duration": "...",
  "two_sentence_summary": "...",
  "date_of_generation": "YYYY-MM-DD",
  "timecoded_transcript": [
    {
      "timecode": "MM:SS",
      "speaker": "...",
      "text": "..."
    },
    ...
  ]
}
```

## Error Handling

- If the audio file is missing, the script will fail.
- If the transcript is missing, it will fail.
- If the Gemini API call fails, it will report the error and exit.
