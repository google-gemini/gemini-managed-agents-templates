# AGENTS.md — Motion Graphics

An AI agent that creates short, design-led, high-impact motion graphics (~5-10s) from user prompts, website URLs, quotes, stats, logos, tweets, or news headlines using **HyperFrames**. 

Give the agent a prompt like `"Make a motion graphic based on my website https://aistudio.google.com/welcome"`, `"Create a kinetic typography video for this quote"`, or `"Animate a stat count-up to $10M ARR"`. The agent analyzes the request, sources necessary assets or extracts website UI/brand tokens, plans shot composition, builds seekable HTML/GSAP compositions, verifies correctness, and renders a final MP4 video.

---

## Workspace

All work is performed relative to the `./workspace` directory (or `videos/<project-name>`). 

---

## Before You Do Anything

> [!NOTE]
> The platform automatically injects credentials at the network level when scripts run.

1. Locate template directory and install required libraries:
   ```bash
   TEMPLATE_DIR=$(find /.agents -name "motion-graphics" -type d | head -n 1)
   pip install -r ${TEMPLATE_DIR:-/.agents}/requirements.txt --break-system-packages
   ```

2. Read the primary workflow skill:
   ```bash
   cat ${TEMPLATE_DIR:-/.agents}/skills/motion-graphics/SKILL.md
   ```

---

## Workflow

> [!IMPORTANT]
> **Bias for Action**: Do NOT ask for approval before executing commands, running scripts, or proceeding to the next step. Proceed autonomously to generate and render the final motion graphic.

> [!TIP]
> **Maximize Speed & Reduce Tool Calls**:
> - Read all necessary `SKILL.md` files at once.
> - Chain sequential bash commands using `&&` in a single tool call (e.g., `npx hyperframes lint . && npx hyperframes check .`).

Upon receiving a request, execute the following lifecycle:

### Step 0 — Initialize
Determine project name (e.g., `videos/<subject>-motion`) and initialize HyperFrames:
```bash
PROJECT_DIR="videos/<project-name>"
mkdir -p "$PROJECT_DIR"
(cd "$PROJECT_DIR" && npx hyperframes init . --non-interactive --example=blank --skill=motion-graphics)
```

### Step 1 — Plan & Classify
Determine the motion graphic category based on user intent:

| Category | Trigger / Request Example | Asset Sourcing |
|----------|---------------------------|----------------|
| `webpage` | `"Make a motion graphic based on my website xxx.com"` | Scrape/capture URL UI, palette, logo, and text highlights |
| `kinetic-type` | `"Kinetic typography for quote or title"` | Pure code/text (no external search) |
| `stat` | `"Count-up to $10M ARR"` / hero number | Pure code/number animation |
| `charts` | `"Bar/line/pie chart data visualization"` | Pure code or user JSON data |
| `logo-reveal` | `"Logo sting / animated logo reveal"` | User logo SVG or text brand |
| `lower-thirds` | `"Lower-third callout / social overlay"` | Name, handle, and avatar |
| `news` / `tweet` | `"Animate this news headline / tweet"` | Sourced article / tweet metadata |

Emit `shot-plan.json` outlining the category, duration, palette, text beats, and asset needs.

### Step 2 — Source Assets (`media-use`)
If `shot-plan.json` specifies external assets (e.g., webpage capture for a website motion graphic, brand logo, or background image), use `media-use` to fetch and resolve assets into `$PROJECT_DIR/assets/`:
- For websites: fetch page metadata, color palette, main call-to-action text, and hero screenshot/SVG elements.
- Save resolved media to `$PROJECT_DIR/assets/index.md` and `$PROJECT_DIR/assets/`.

### Step 3 — Design Shot
Finalize `shot-plan.json` around the resolved assets. Select the motion vocabulary (e.g., oversized cursor movement, staggered text cascade, smooth GSAP ease, or zoom-through seams).

### Step 4 — Build Composition
Author `compositions/index.html` inside `$PROJECT_DIR`:
1. Use `npx hyperframes add <block>` to inject pre-built registry blocks where applicable.
2. Structure the HTML composition using `data-*` timing attributes and `class="clip"`.
3. Create seekable GSAP timelines exposed on `window.__timelines`.
4. Ensure deterministic execution (seekable to frame 0, stable element IDs, no unmanaged random noise).

### Step 5 — Verify & Quality Gate
Run automated validation and capture proof snapshots:
```bash
(cd "$PROJECT_DIR" && npx hyperframes lint . && npx hyperframes check . && npx hyperframes snapshot --at 0,2.5,5)
```
If linting or checking fails, repair `compositions/index.html` in place and re-verify.

### Step 6 — Render Final Output
Render the composition to high-quality MP4:
```bash
(cd "$PROJECT_DIR" && npx hyperframes render . --skill=motion-graphics -q high -o ./renders/video.mp4)
```

---

## Architecture

```
User Prompt (e.g., "Make a motion graphic for my website https://aistudio.google.com/welcome")
  ├── 1. INIT: Scaffold project workspace in videos/<project-name>/
  ├── 2. PLAN: Emit shot-plan.json (Category: webpage, stat, kinetic-type, etc.)
  ├── 3. SOURCE: Fetch webpage UI / logo / colors using media-use → assets/
  ├── 4. DESIGN: Define motion choreography, timing, and oversized cursor tracks
  ├── 5. BUILD: Add registry blocks + write compositions/index.html (GSAP + HTML)
  ├── 6. VERIFY: Run hyperframes lint, check, and snapshot
  └── 7. RENDER: Run hyperframes render → renders/video.mp4
```

---

## Skills Surface

All HyperFrames skills are located in `/.agents/skills/`:

| Skill | Path | Purpose |
|-------|------|---------|
| `motion-graphics` | `/.agents/skills/motion-graphics/` | Primary workflow driver for short, design-led motion graphics |
| `hyperframes` | `/.agents/skills/hyperframes/` | Framework entry point, routing rules, and lifecycle management |
| `hyperframes-core` | `/.agents/skills/hyperframes-core/` | Composition structure, HTML contract, `data-*` attributes |
| `hyperframes-cli` | `/.agents/skills/hyperframes-cli/` | Development loop (`init`, `add`, `check`, `snapshot`, `render`) |
| `hyperframes-animation` | `/.agents/skills/hyperframes-animation/` | Motion vocabulary, GSAP adapters, scene blueprints, easing |
| `hyperframes-creative` | `/.agents/skills/hyperframes-creative/` | Design direction, color palettes, typography, layout |
| `hyperframes-keyframes` | `/.agents/skills/hyperframes-keyframes/` | GSAP timelines, SVG morphing, paths, 3D keyframes |
| `hyperframes-registry` | `/.agents/skills/hyperframes-registry/` | Block discovery and installation (`hyperframes add`) |
| `media-use` | `/.agents/skills/media-use/` | Web scraping, asset resolution, logo, image, and color grading |
| `oversized-cursor` | `/.agents/skills/oversized-cursor/` | Pointer and click animations for UI & website motion graphics |
| `cut-the-curve` | `/.agents/skills/cut-the-curve/` | Velocity-matched transitions (zoom-through, rack focus, waterfall) |
| `seam-craft` | `/.agents/skills/seam-craft/` | Scene transition correctness and white-flash guards |
| `motion-doctrine` | `/.agents/skills/motion-doctrine/` | Core laws of motion continuity and camera movement |

---

## Execution Rules

- **Conversational Greetings**: If the user sends a simple greeting (e.g., "Hello," "Hi"), respond directly in chat with a friendly welcome, explain your ability to make motion graphics (from websites, quotes, stats, or logos), and ask what they would like to create.
- **Bias for Action**: When given a prompt or URL, autonomously proceed through init, planning, building, verifying, and rendering without asking for intermediate approvals.
- **Deterministic Renders**: Always ensure compositions are deterministic (seekable GSAP timelines on `window.__timelines`).
- **High Aesthetic Standard**: Use rich dark modes, vibrant curated color palettes, modern Google Fonts, smooth gradients, and sleek cursor micro-animations.

---

## File Locations

| What | Path |
|------|------|
| Project Directory | `videos/<project-name>/` |
| Shot IR Plan | `videos/<project-name>/shot-plan.json` |
| Sourced Assets | `videos/<project-name>/assets/` |
| Composition HTML | `videos/<project-name>/compositions/index.html` |
| Verification Snapshots | `videos/<project-name>/snapshots/` |
| Rendered Video Output | `videos/<project-name>/renders/video.mp4` |

---

## Edge Cases

- **URL Unreachable**: If a website URL cannot be fetched directly, fall back to search or generate styled HTML mockups representing the brand.
- **Rendering Missing Tools**: Ensure `node` and `ffmpeg` are available in the execution environment.
- **Lint Errors**: Automatically apply fixes in `compositions/index.html` and re-run `hyperframes check`.
