---
name: audio-mixing
description: Mix speech audio and background music into a polished radio show file.
---

# Audio Mixing

Combine the TTS speech audio and Lyria background music into a single, polished radio show file.

## Embedded Script

```bash
python3 skills/audio-mixing/scripts/mix_audio.py --workspace ./workspace
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--workspace` | `workspace` | Root workspace directory |

### What it does

1. Loads speech from `{workspace}/audio/speech/speech.wav`.
2. Adds 3 seconds of silence padding to the end of the speech to prevent it from being faded out.
3. Loads background music from `{workspace}/audio/music/background.mp3` (if exists).
4. Loops music to match speech duration, lowers volume to -18dB.
5. Overlays speech on music with a 1-second music intro.
6. Adds fade-in/fade-out.
7. Exports as MP3.

### Dependencies

- `pydub`
- `ffmpeg` (system)

## Mixing Guidelines

| Element | Level | Notes |
|---------|-------|-------|
| Speech | 0 dB | Untouched, full volume |
| Background music | -18 dB | Barely audible — subtle bed under speech |

### Transitions

- Music fade-in: 3 seconds
- Music fade-out: 5 seconds
- Overall fade-in: 500ms
- Overall fade-out: 2 seconds

## Output

| File | Path | Format |
|------|------|--------|
| MP3 (distribution) | `{workspace}/audio/final/ai_radio.mp3` | MP3, 192kbps |

## Fallback

If no background music exists, produces speech-only output with just fade-in/fade-out applied.
