---
name: image-gen
description: Unified image generation/editing skill for both gpt-image-2/OpenAI-compatible Image API providers and Gemini image/Nano Banana providers. Use for text-to-image, image editing, restyling, compositing, reference-image workflows, banners, thumbnails, slides, and social assets. Defaults to gpt-image-2; switch to Gemini/Nano Banana with --backend gemini or a gemini/nano-banana model name. Includes backend-specific parameter rules so agents do not mix incompatible GPT and Gemini options.
---

# Image Gen

Unified front door for image generation and editing across:

- **GPT backend**: `gpt-image-2` via OpenAI-compatible Image API providers; default backend/model.
- **Gemini backend**: Gemini image / Nano Banana via Gemini-compatible providers.

Use the wrapper unless you need to debug a backend directly:

```bash
bash <workspace>/skills/image-gen/scripts/image.sh [options] "prompt text"
```

## Backend selection

Default to GPT:

```bash
bash <workspace>/skills/image-gen/scripts/image.sh -o /tmp/output.png "prompt text"
```

Switch to Gemini/Nano Banana explicitly:

```bash
bash <workspace>/skills/image-gen/scripts/image.sh \
  --backend gemini --model gemini-3.1-flash-image-preview \
  -o /tmp/output.png \
  "prompt text"
```

Auto-routing: if `--model` contains `gemini`, `nano`, or `banana`, the wrapper routes to Gemini; otherwise it routes to GPT.

## Model families and parameters

Do **not** mix backend-specific parameters. Pick the backend first, then use only that backend’s parameter set.

### GPT / OpenAI-compatible backend

Use for: default image generation, OpenAI-style editing, outputs needing `quality`, `output_format`, compression, or moderation controls.

Models:

- Default: `gpt-image-2`
- Other OpenAI-compatible image models only if the configured provider supports them.

Supported options:

- `--provider <name>`: provider from `.openclaw/local/gpt-image-providers.json`
- `--model <name>`: default provider model or `gpt-image-2`
- `-i <path>`: input/reference image; repeatable; switches to `/images/edits`
- `-o <path>`: output path
- `-size <value>`: default `auto`; for `gpt-image-2`, may be any `WIDTHxHEIGHT` satisfying the official constraints below, not just the old three preset sizes
- `-quality auto|low|medium|high`: default `auto`; use `low` for fast drafts/thumbnails/iteration, `medium` or `high` for finals
- `-n <count>`: default `1`; generate multiple images in one request
- `--output-format png|jpeg|webp`: default `png`; `jpeg` is usually faster when latency matters
- `--output-compression <0-100>`: only for jpeg/webp
- `--background auto|opaque`: default `auto`; `gpt-image-2` does **not** support transparent backgrounds, so do not use `transparent`
- `--moderation auto|low`: default `auto`; `low` is less restrictive when provider supports it
- `--user <id>`: optional end-user id
- `--image-field image|image[]`: multipart field name for edits; default `image`

`gpt-image-2` size rules:

- `auto` is valid and is the default.
- Explicit sizes use `WIDTHxHEIGHT`, e.g. `2048x1152`.
- Each edge must be **≤ 3840 px**.
- Each edge must be a **multiple of 16 px**.
- Long edge / short edge ratio must be **≤ 3:1**.
- Total pixels must be **≥ 655,360** and **≤ 8,294,400**.
- Popular valid sizes: `1024x1024`, `1536x1024`, `1024x1536`, `2048x2048`, `2048x1152`, `3840x2160`, `2160x3840`.
- Outputs above `2560x1440` total pixels are considered experimental; prefer `1024/1536` or 2K sizes for reliability.
- Square images are typically fastest.

GPT edit/reference notes:

- The Image API uses `/images/generations` without `-i` and `/images/edits` when `-i` is present.
- Multiple `-i` images are allowed for reference/composite workflows.
- Masked edits exist in the OpenAI API, but this wrapper currently does not expose a `--mask` option.
- For `gpt-image-2`, omit `input_fidelity`; the API does not allow changing it because image inputs are processed at high fidelity automatically.

Examples:

```bash
bash <workspace>/skills/image-gen/scripts/image.sh \
  --backend gpt --model gpt-image-2 \
  -size auto -quality auto --output-format png \
  -o /tmp/gpt.png \
  "clean product hero image, premium studio lighting"
```

```bash
bash <workspace>/skills/image-gen/scripts/image.sh \
  --backend gpt \
  -i /tmp/input.png -o /tmp/gpt-edit.png \
  "replace the background with a warm sunset, keep the subject unchanged"
```

### Gemini / Nano Banana backend

Use for: Gemini image models, Nano Banana style/edit workflows, image-conditioned generation where Gemini performs better, or when the user asks for Gemini/Nano Banana specifically.

Models and aliases:

- `gemini-3.1-flash-image-preview`
- `gemini-3-pro-image-preview`
- Aliases accepted by the backend: `nanobanana2`, `nano-banana-2`, `nanobananapro`, `nanobananaapro`, `nano-banana-pro`

Supported options:

- `--provider <name>`: provider from `.openclaw/local/nanobanana-providers.json`
- `--model <name>`: default `gemini-3.1-flash-image-preview`
- `-i <path>`: input/reference image; repeatable; sent as Gemini `inlineData`
- `-o <path>`: output path
- `-aspect auto|1:1|1:4|1:8|2:3|3:2|3:4|4:1|4:3|4:5|5:4|8:1|9:16|16:9|21:9`
- `-size auto|512px|1K|2K|4K`

Gemini does **not** use GPT options like `-quality`, `--output-format`, `--output-compression`, `--background`, `--moderation`, or `--image-field`. Do not pass them unless the backend script has been updated to support them.

Examples:

```bash
bash <workspace>/skills/image-gen/scripts/image.sh \
  --backend gemini --model gemini-3.1-flash-image-preview \
  -aspect 16:9 -size 2K \
  -o /tmp/gemini.png \
  "cinematic wide banner, soft rim light, clean composition"
```

```bash
bash <workspace>/skills/image-gen/scripts/image.sh \
  --backend gemini --model nano-banana-pro \
  -i /tmp/character.png -i /tmp/style.png \
  -aspect auto -size 1K \
  -o /tmp/gemini-edit.png \
  "use image 1 as the character reference and image 2 as the visual style reference; keep identity consistent"
```

## Quick parameter map

- Want `quality`: use GPT.
- Want `output_format` or jpeg/webp compression: use GPT.
- Want `background: transparent`: do **not** use `gpt-image-2`; it only supports `auto`/`opaque`.
- Want custom pixel dimensions under 4K: use GPT if the size satisfies `gpt-image-2` constraints: both edges ≤3840, multiples of 16, aspect ratio ≤3:1, total pixels 655,360–8,294,400.
- Want `aspectRatio`: use Gemini `-aspect`.
- Want `imageSize` as `512px/1K/2K/4K`: use Gemini `-size`.
- Want multiple variants via `-n`: use GPT; Gemini wrapper currently returns one image.

## Editing / reference image prompting

Both backends accept repeatable `-i`, but prompt wording matters:

- For edits, explicitly say what must remain unchanged.
- For multi-image work, assign roles: “image 1 is subject”, “image 2 is style”, “image 3 is background”.
- For Gemini/Nano Banana character/style transfer, be extra explicit about identity, outfit, pose, background, and which source image controls each.
- For GPT edits, describe the target edit and preserve constraints clearly.

## Provider config

This wrapper reuses the existing backend configs:

- GPT: `<workspace>/.openclaw/local/gpt-image-providers.json`
- Gemini: `<workspace>/.openclaw/local/nanobanana-providers.json`

If a backend config is missing, run that backend’s check script or ask the user for provider URL + API key. Do not fake readiness.

## Output and delivery

Send the final path printed by the script; providers may return a different extension than requested.

On this QQ/NapCat setup, send local images with:

```text
<qqmedia>/absolute/path/to/output.png</qqmedia>
```

Do not default to `<qqimg>`.
