---
name: script-writing
description: Generate the AI Talk Radio show script from research using the Interactions API.
---

# Script Writing

Generate a naturalistic, multi-character radio show script directly via the LLM. The script features host Paul taking calls from people around the world, with advanced audio tags.

## Embedded Script

```bash
python3 skills/script-writing/scripts/generate_script.py --workspace ./workspace --style debate
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--workspace` | `workspace` | Root workspace directory |
| `--style` | `default` | Show format (see styles below) |

### Styles

| Style | Callers | Format | Use when user says... |
|-------|---------|--------|----------------------|
| `debate` | 2 per topic, opposing views | Structured back-and-forth, Paul moderates | "opposing views", "debate", "both sides" |
| `roundtable` | 3-4, different angles | Collaborative discussion, callers build on each other | "roundtable", "panel", "discussion" |
| `interview` | 1-2 with direct experience | Q&A format, Paul asks probing questions | "interview", "deep dive", "expert" |
| `explainer` | 2-3, each explains an aspect | Teach the audience, Paul asks clarifying questions | "explain", "break it down", "what is" |
| `default` | Same as `debate` | Default when no style specified | *(anything else)* |

### Examples

```bash
# HN discussion with opposing views
python3 skills/script-writing/scripts/generate_script.py \
  --workspace ./workspace --style debate

# Panel discussion about a GitHub repo
python3 skills/script-writing/scripts/generate_script.py \
  --workspace ./workspace --style roundtable

# Interview with an expert about a paper
python3 skills/script-writing/scripts/generate_script.py \
  --workspace ./workspace --style interview

# Explain a new technology
python3 skills/script-writing/scripts/generate_script.py \
  --workspace ./workspace --style explainer
```

### What it does

1. Reads all research from `{workspace}/data/research/*.md`.
2. Builds a system prompt with the base format rules + style-specific caller/structure instructions.
3. Calls Gemini via the **Interactions API** (`client.interactions.create()`).
4. Saves the script to `{workspace}/data/script.md`.

### Dependencies

- `google-genai` (>= 2.0.0)
## Output

- **Script File**: `{workspace}/data/script.md`
- **Format**: Plain text, each line starting with `Speaker: dialogue`

## Cast

| Speaker | Role | Personality |
|---------|------|-------------|
| **Paul** | Host | Professional but relatable British moderator |
| **Callers** | Call-ins | Amateur, rough, natural — from various cities around the world |

## Script Format Rules

- Every line: `SpeakerName: [audio tag] Dialogue text`
- Must include audio tags in square brackets (e.g., `[sighs]`, `[excitedly]`).
- Callers should sound amateurish (include "uh", "like", natural pauses).
- Short punchy sentences — spoken word, not prose.
- ~450-500 words total (~3 minutes when spoken).
