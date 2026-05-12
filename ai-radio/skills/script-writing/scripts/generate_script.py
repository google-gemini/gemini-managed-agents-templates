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
"""Generate the AI Talk Radio radio show script from research using the Interactions API.

Usage:
    python3 generate_script.py --workspace ./workspace
    python3 generate_script.py --workspace ./workspace --style debate
    python3 generate_script.py --workspace ./workspace --style interview

Requires:
    pip install google-genai

Output:
    {workspace}/data/script.md
"""

import argparse
import os
from google import genai

BASE_PROMPT = """You are a scriptwriter for "AI Talk Radio", a community radio show for a nerdy, tech-savvy audience.

Write a ~3-minute radio script based on the research provided. The show has:

**Host**: Paul (in the studio) — a calm, measured British moderator broadcasting from a London studio. Professional, intellectual, and polite.

**Format rules:**
- Every line MUST start with a speaker name and colon: `Paul:` or `[CallerName]:`
- You MUST include a gender tag `[Male]` or `[Female]` at the beginning of the transcript for every caller turn.
- You MUST include an **accent tag** `[Accent: <accent_description>]` matching the location the caller is supposedly calling from (e.g., `[Accent: Irish]` if calling from Dublin, `[Accent: Southern US]` if from Texas, `[Accent: Australian]` from Sydney, etc.).
- Example: `Caller1: [Male] [Accent: Irish] [hesitantly] I think...`
- You MUST include **audio tags** in square brackets to indicate how a line should be delivered.
- Use tags like `[sighs]`, `[frustratedly]`, `[calmly]`, `[whispers]`, `[indignantly]` to make performances rich.
- **CRITICAL**: The callers are amateurs. They should sound rough, imperfect, and natural. They should NOT speak in perfect, complete sentences. They should cut themselves off, use fillers like "uh", "like", "you know".
- **Tone**: Callers are smart, tech-savvy individuals (nerds), not experts but informed. Their speech is imperfect because it is spontaneous, not because they lack intelligence.
- **Host Introduction**: Host Paul MUST always introduce a new caller by name and location before they speak for the first time.
- No stage directions outside of the audio tags in the transcript.
- Keep sentences short and punchy — this is spoken word.
- Target ~450-500 words total.
- DO NOT fabricate any facts. Only use information from the research provided.
- Time of Day: Do NOT assume the time of day (avoid "Good morning", "Good evening", etc.).
- No Songs: The radio show does NOT play songs. Do not include lines about playing music tracks or songs.
- No Ad Breaks: Do NOT include ad breaks or say "stay tuned" for more.
- Clean Wrap Up: Do a clean wrap up at the end of the show without promising future segments.
- The research may come from any source (news, blogs, GitHub, papers, forums). Adapt your script to fit whatever content is provided.

**CONTENT SAFETY — strictly off-limits:**
- Do NOT discuss politics, political parties, politicians, elections, legislation, or government policy.
- Do NOT discuss international politics, geopolitics, wars, conflicts, sanctions, or diplomacy.
- Do NOT discuss race, ethnicity, racial issues, stereotypes, or discrimination.
- Do NOT discuss religion, religious beliefs or practices.
- Do NOT discuss historical controversies (colonialism, slavery, genocide, etc.).
- Do NOT discuss gender/sexuality culture wars or immigration policy.
- If a research topic touches any of the above, skip it or focus only on the technical aspects.
- Keep the tone light, nerdy, and strictly focused on technology, software, science, and engineering."""

STYLE_PROMPTS = {
    "debate": """
**Style: DEBATE**

**Callers**: For each topic, generate TWO callers representing opposing views. They should disagree respectfully but firmly.

**Structure:**
1. Cold Open (10 sec): Paul teases the most controversial take.
2. Intro (15 sec): Paul welcomes listeners, sets up the debate format.
3. Debate Segments (2.5 min): Paul introduces a topic, takes calls from two sides. Callers argue their positions, Paul moderates.
4. Closing (15 sec): Paul summarizes both sides, thanks callers.""",

    "roundtable": """
**Style: ROUNDTABLE**

**Callers**: 3-4 callers each bringing a different angle on the topic. Collaborative, building on each other's points rather than arguing.

**Structure:**
1. Cold Open (10 sec): Paul previews the topic.
2. Intro (15 sec): Paul welcomes the panel and introduces each caller.
3. Discussion (2.5 min): Open conversation — callers riff on each other's points, Paul guides the flow.
4. Closing (15 sec): Paul ties the threads together.""",

    "interview": """
**Style: INTERVIEW**

**Callers**: 1-2 callers presented as people with direct experience or deep knowledge. Paul asks probing questions — this is more Q&A than conversation.

**Structure:**
1. Cold Open (10 sec): Paul teases what the guest will reveal.
2. Intro (15 sec): Paul introduces the guest(s) and their background.
3. Interview (2.5 min): Paul asks questions, guest(s) answer in depth. Follow-up questions encouraged.
4. Closing (15 sec): Paul thanks the guest(s) and summarizes key takeaways.""",

    "explainer": """
**Style: EXPLAINER**

**Callers**: 2-3 callers who each explain a different aspect of the topic. Think of it as a collaborative "teach the audience" format.

**Structure:**
1. Cold Open (10 sec): Paul poses a question the audience might be wondering.
2. Intro (15 sec): Paul sets up the topic and says we have people who can break it down.
3. Explainer Segments (2.5 min): Each caller explains their piece. Paul asks clarifying questions on behalf of the audience.
4. Closing (15 sec): Paul recaps the key points.""",
}

# Default style when none specified
STYLE_PROMPTS["default"] = STYLE_PROMPTS["debate"]

VALID_STYLES = list(STYLE_PROMPTS.keys())


def main():
    parser = argparse.ArgumentParser(description="Generate AI Talk Radio radio script")
    parser.add_argument("--workspace", default="workspace", help="Workspace directory")
    parser.add_argument(
        "--style",
        default="default",
        choices=VALID_STYLES,
        help=f"Show format: {', '.join(VALID_STYLES)}",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=3,
        help="Target duration in minutes",
    )
    args = parser.parse_args()

    client = genai.Client()

    # Read research
    research_dir = os.path.join(args.workspace, "data", "research")
    research = ""
    for fname in sorted(os.listdir(research_dir)):
        if fname.endswith(".md"):
            with open(os.path.join(research_dir, fname)) as f:
                research += f.read() + "\n\n"

    if not research.strip():
        print("ERROR: No research found in data/research/. Run the research step first.")
        return

    # Build system prompt = base + style
    target_words = args.duration * 125
    modified_base_prompt = BASE_PROMPT.replace(
        "Write a ~3-minute radio script",
        f"Write a ~{args.duration}-minute radio script"
    ).replace(
        "- Target ~450-500 words total.",
        f"- Target ~{target_words} words total."
    )

    # Make style prompt durations dynamic
    main_seg_min = (args.duration * 60 - 40) / 60
    main_seg_str = f"{main_seg_min:.1f} min"
    style_prompt = STYLE_PROMPTS[args.style].replace("2.5 min", main_seg_str)

    system_prompt = modified_base_prompt + style_prompt

    print(f"=== AI Talk Radio: Script Generation ===\n")
    print(f"Style: {args.style}")
    print(f"Read {len(research)} characters of research.")
    print("Generating script via Interactions API...\n")

    interaction = client.interactions.create(
        model="gemini-3-flash-preview",
        input=f"Write the radio script based on this research:\n\n{research}",
        system_instruction=system_prompt,
    )

    script = interaction.steps[-1].content[0].text

    # Save
    out_path = os.path.join(args.workspace, "data", "script.md")
    with open(out_path, "w") as f:
        f.write(script)

    word_count = len(script.split())
    print(f"✅ Script saved to {out_path}")
    print(f"   Word count: {word_count}")
    print(f"\n--- Preview ---\n")
    print(script[:800])
    if len(script) > 800:
        print(f"\n... ({len(script) - 800} more characters)")


if __name__ == "__main__":
    main()
