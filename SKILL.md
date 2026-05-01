---
name: image-gen
description: Complete, standalone image generation/editing skill for GPT/OpenAI-compatible Image API providers and Gemini image/Nano Banana providers. Use for text-to-image, image editing, restyling, compositing, reference-image workflows, banners, thumbnails, slides, and social assets. Includes its own GPT and Gemini backend scripts; defaults to gpt-image-2 and can switch to Gemini/Nano Banana with --backend gemini or a gemini/nano-banana model name.
---

# Image Gen

Standalone front door for image generation and editing across:

- **GPT backend**: `gpt-image-2` via OpenAI-compatible Image API providers; default backend/model.
- **Gemini backend**: Gemini image / Nano Banana via Gemini-compatible providers.

Use:

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
- `-size <value>`: default `auto`; for `gpt-image-2`, may be any `WIDTHxHEIGHT` satisfying the constraints below
- `-quality auto|low|medium|high`: default `auto`; use `low` for drafts, `medium` or `high` for finals
- `-n <count>`: default `1`; generate multiple images in one request
- `--output-format png|jpeg|webp`: default `png`; `jpeg` is usually faster when latency matters
- `--output-compression <0-100>`: only for jpeg/webp
- `--background auto|opaque`: default `auto`; `gpt-image-2` does **not** support transparent backgrounds
- `--moderation auto|low`: default `auto`; `low` is less restrictive when provider supports it
- `--user <id>`: optional end-user id
- `--image-field image|image[]`: multipart field name for edits; default `image`

`gpt-image-2` size rules:

- `auto` is valid and is the default.
- Explicit sizes use `WIDTHxHEIGHT`, e.g. `2048x1152`.
- Each edge must be ≤3840 px, multiple of 16, ratio ≤3:1.
- Total pixels must be 655,360–8,294,400.
- Useful sizes: `1024x1024`, `1536x1024`, `1024x1536`, `2048x2048`, `2048x1152`, `3840x2160`, `2160x3840`.

### Gemini / Nano Banana backend

Use for: Gemini image models, Nano Banana style/edit workflows, image-conditioned generation where Gemini performs better, or when requested.

Models and aliases:

- `gemini-3.1-flash-image-preview`
- `gemini-3-pro-image-preview`
- `nanobanana2`, `nano-banana-2` → `gemini-3.1-flash-image-preview`
- `nanobananapro`, `nanobananaapro`, `nano-banana-pro` → `gemini-3-pro-image-preview`

Supported options:

- `--provider <name>`: provider from `.openclaw/local/nanobanana-providers.json`
- `--model <name>`: default `gemini-3.1-flash-image-preview`
- `-i <path>`: input/reference image; repeatable
- `-o <path>`: output path
- `-aspect auto|1:1|1:4|1:8|2:3|3:2|3:4|4:1|4:3|4:5|5:4|8:1|9:16|16:9|21:9`
- `-size auto|512px|1K|2K|4K`

Gemini does **not** use GPT options like `-quality`, `--output-format`, `--output-compression`, `--background`, `--moderation`, or `--image-field`.

## Examples

GPT generation:

```bash
bash <workspace>/skills/image-gen/scripts/image.sh \
  --backend gpt --model gpt-image-2 \
  -size auto -quality auto --output-format png \
  -o /tmp/gpt.png \
  "clean product hero image, premium studio lighting"
```

GPT edit:

```bash
bash <workspace>/skills/image-gen/scripts/image.sh \
  --backend gpt \
  -i /tmp/input.png -o /tmp/gpt-edit.png \
  "replace the background with a warm sunset, keep the subject unchanged"
```

Gemini generation:

```bash
bash <workspace>/skills/image-gen/scripts/image.sh \
  --backend gemini --model gemini-3.1-flash-image-preview \
  -aspect 16:9 -size 2K \
  -o /tmp/gemini.png \
  "cinematic wide banner, soft rim light, clean composition"
```

Gemini multi-reference edit:

```bash
bash <workspace>/skills/image-gen/scripts/image.sh \
  --backend gemini --model nano-banana-pro \
  -i /tmp/character.png -i /tmp/style.png \
  -aspect auto -size 1K \
  -o /tmp/gemini-edit.png \
  "use image 1 as the character reference and image 2 as the visual style reference; keep identity consistent"
```

## Provider config

This skill is standalone, but credentials are still local. It reads:

- GPT: `<workspace>/.openclaw/local/gpt-image-providers.json`
- Gemini: `<workspace>/.openclaw/local/nanobanana-providers.json`

Use `scripts/check-gpt-image.sh` or `scripts/check-nanobanana.sh` to validate setup. For config examples, read `references/gpt/provider-setup.md` or `references/gemini/provider-setup.md`.

## Prompting notes

- For edits, explicitly say what must remain unchanged.
- For multi-image work, assign roles: “image 1 is subject”, “image 2 is style”, “image 3 is background”.
- For Gemini/Nano Banana character/style transfer, be explicit about identity, outfit, pose, background, and which source controls each.

## Output and delivery

Send the final path printed by the script; providers may return a different extension than requested.

On QQ/NapCat setups, local images often work best with:

```text
<qqmedia>/absolute/path/to/output.png</qqmedia>
```
