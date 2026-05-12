# AGENTS.md — AI Talk Radio

An AI agent that turns **any content source** into a radio show. Give it a topic, a URL, a GitHub repo, a research paper, or just say "Hacker News" — the agent researches the content, writes a radio script with a host and callers representing opposing views, generates speech with telephone effects, adds background music, and produces a polished audio file.

## Workspace

All work is performed in the `./workspace` directory. All paths are relative to `./workspace` unless absolute.

## Before You Do Anything

> [!NOTE]
> The API key is automatically injected into your prompt. You must export it as an environment variable before running any scripts:
> ```bash
> export GEMINI_API_KEY="<key_from_prompt>"
> ```

1. Install required libraries:
   ```bash
   pip install pydub "google-genai>=2.0.1"
   ```

## Workflow

> [!IMPORTANT]
> **Bias for Action**: Do NOT ask for approval before executing commands, running scripts, or proceeding to the next step. Proceed autonomously unless there is a material ambiguity or a critical decision that strictly requires user input.

> [!TIP]
> **Maximize Speed & Reduce Calls**:
> - Read all necessary `SKILL.md` files (in the .agent/skills directory) at once using a single bash command (`cat .agent/skills/*/SKILL.md`).
> - Do not use `list_files` to verify directories, script paths, or output files—trust the documentation and the script success logs.
> - Run independent tasks (like TTS and music generation) in parallel.
> - Chain sequential bash commands using `&&` in a single tool call (e.g., `python3 mix_audio.py && python3 generate_metadata.py`).

Upon execution, you should:

1. **Music Generation** — use `music-generation` skill to create ambient background music via Lyria (`lyria-3-clip-preview`). **Kick this off immediately in parallel with the research step, as it has no dependencies.**
2. **Research** — gather source material based on the user's prompt. This could be: fetching Hacker News stories, scraping a website, reading a GitHub repo's changelog, summarizing an arXiv paper, or researching a topic via Google Search using `research` skill.
3. **Write Script** — use `script-writing` skill to write a radio show script with host Paul and callers calling in from around the world. Use `--style` to control the format (debate, roundtable, interview, explainer).
4. **Generate Speech** — use `tts-generation` skill to convert each speaker turn to speech via the Interactions API. 
5. **Mix Audio** — use `audio-mixing` skill to combine speech and music into a polished radio show, with music ending early.
6. **Generate Metadata** — use `metadata-generation` skill to return audio and transcript to Gemini and get back a JSON file with show details.
7. **Generate Cover Image** — use `cover-image-generation` skill to create a 1:1 cover image based on the generated metadata.

## Architecture

```
User prompt
  ├── 1. MUSIC: python3 skills/music-generation/scripts/generate_music.py --workspace ./workspace --mood <mood>
  │       → {workspace}/audio/music/background.mp3
  ├── 2. RESEARCH: Agent picks the right script (fetch_hn.py, fetch_github.py, fetch_url.py, or Google Search)
  │       → {workspace}/data/research/*.md
  ├── 3. python3 skills/script-writing/scripts/generate_script.py --workspace ./workspace --style <style>
  │       → {workspace}/data/script.md
  ├── 4. python3 skills/tts-generation/scripts/generate_tts.py --workspace ./workspace
  │       → {workspace}/audio/speech/speech.wav
  ├── 5. python3 skills/audio-mixing/scripts/mix_audio.py --workspace ./workspace
  │       → {workspace}/audio/final/ai_radio.mp3
  ├── 6. python3 skills/metadata-generation/scripts/generate_metadata.py --workspace ./workspace
  │       → {workspace}/data/show_notes.json
  └── 7. python3 skills/cover-image-generation/scripts/generate_image.py --workspace ./workspace --metadata ./workspace/data/show_notes.json
          → {workspace}/images/cover.png
```

### Default Presets

Use these defaults unless the user specifies otherwise:

| Content Source | `--style` | `--mood` | Why |
|---------------|-----------|----------|-----|
| Hacker News | `debate` | `news` | HN stories spark debate; BBC news music fits |
| GitHub repo | `explainer` | `tech` | Explaining what changed; tech vibe |
| URL / article | `roundtable` | `chill` | Multi-angle discussion of the content |
| General topic | `interview` | `chill` | Deep-dive Q&A on the subject |

## API Surface

All Gemini API calls use the **Interactions API** (`client.interactions.create()`), NOT `generateContent`:

| Step | Model | API |
|------|-------|-----|
| Script writing | `gemini-3-flash-preview` | `interactions.create()` |
| TTS generation | `gemini-3.1-flash-tts-preview` | `interactions.create()` |
| Music generation | `lyria-3-clip-preview` | `interactions.create()` |

## Skills

Each skill lives in `skills/<name>/` with a `SKILL.md` and a `scripts/` directory containing ready-to-run Python scripts.

| Skill | Script(s) | Purpose |
|-------|--------|---------|
| `research` | `fetch_hn.py`, `fetch_github.py`, `fetch_url.py` | Gather content from HN, GitHub repos, URLs, or any source |
| `script-writing` | `generate_script.py` | LLM writes the radio script (supports `--style` flag) |
| `tts-generation` | `generate_tts.py` | Single-speaker TTS + telephone filter for callers |
| `music-generation` | `generate_music.py` | Lyria ambient music |
| `audio-mixing` | `mix_audio.py` | Mix speech + music with fades |
| `metadata-generation` | `generate_metadata.py` | Generate show title, summary, and timecoded transcript |
| `cover-image-generation` | `generate_image.py` | Generate cover image based on metadata |

## Execution Order

Run strictly in order (except music which can run in parallel at the start):

1. `music-generation` → `audio/music/background.mp3` (Run in parallel with step 2)
2. `research` → `data/research/*.md` (one or more files)
3. `script-writing` → `data/script.md`
4. `tts-generation` → `audio/speech/speech.wav`
5. `audio-mixing` → `audio/final/ai_radio.mp3`
6. `metadata-generation` → `data/show_notes.json`
7. `cover-image-generation` → `images/cover.png`

## Content Rules

- **Duration**: ~3 minutes of final audio.
- **Format**: Radio show — host Paul + callers calling in from different cities around the world.
- **Source**: Whatever the user asked for. The research must be grounded in real content — never fabricate stories or data.
- **NO FAKE DATA**: All stories, insights, and perspectives must come from real research gathered in step 1.

### Topics to AVOID — strictly off-limits

Do NOT select, discuss, or reference any of the following:

- **Politics** — no political parties, politicians, elections, legislation, government policy, political commentary
- **International politics** — no geopolitics, wars, conflicts, sanctions, territorial disputes, diplomacy
- **Race and ethnicity** — no racial topics, stereotypes, discrimination, identity politics
- **Religion** — no religious debates, beliefs, practices, or commentary
- **Historical controversies** — no colonialism, slavery, genocide, or historically divisive events
- **Gender and sexuality debates** — no culture war topics
- **Immigration** — no immigration policy or debate
- **Anything potentially offensive** — when in doubt, skip it

### Topics that ARE safe

Stick to: **technology, software, programming, open source, AI/ML, science, engineering, developer tools, startups, product launches, creative projects, and tech culture.**

## File Locations

| What | Path |
|------|------|
| Research data | `./workspace/data/research/` |
| Radio script | `./workspace/data/script.md` |
| Speech segments | `./workspace/audio/speech/segments/` |
| Speech (combined) | `./workspace/audio/speech/speech.wav` |
| Background music | `./workspace/audio/music/background.mp3` |
| Final output | `./workspace/audio/final/ai_radio.mp3` |
| Metadata | `./workspace/data/show_notes.json` |
| Cover Image | `./workspace/images/cover.png` |

## Edge Cases

- **Rate limits**: Retry once with a brief pause, or skip the turn.
- **Lyria availability**: Experimental model. If it fails, proceed without background music.
- **ffmpeg missing**: Skip telephone filter, use raw TTS audio.
- **No web access for a source**: Use Google Search as a fallback to find the content or related discussion.
