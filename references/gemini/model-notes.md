# Model Notes for Nanobanana Image Edit

This reference keeps the model naming and aspect-ratio guidance separate from the main SKILL so it can evolve with less churn.

## Canonical model names

- `gemini-3.1-flash-image-preview`
  - alias: `nanobanana2`
  - role: faster / lower-cost default model for generation and editing
- `gemini-3-pro-image-preview`
  - alias: `nanobananapro`
  - role: higher-end reasoning and image editing model

## Invalid / do-not-use name in this skill

- `gemini-3.1-pro-image-preview`

Do not document or suggest that name here unless a future official model page appears for it.

## Supported aspect ratios

### `gemini-3.1-flash-image-preview`

Documented supported aspect ratios:

- `1:1`
- `1:4`
- `1:8`
- `2:3`
- `3:2`
- `3:4`
- `4:1`
- `4:3`
- `4:5`
- `5:4`
- `8:1`
- `9:16`
- `16:9`
- `21:9`

### `gemini-3-pro-image-preview`

Documented supported aspect ratios:

- `1:1`
- `2:3`
- `3:2`
- `3:4`
- `4:3`
- `4:5`
- `5:4`
- `9:16`
- `16:9`
- `21:9`

## Resolution / imageSize notes

### Values exposed by the local runtime

- `auto`
- `512px`
- `1K`
- `2K`
- `4K`

### Current understanding

- Public model notes for `gemini-3.1-flash-image-preview` explicitly mention new output resolution options including `0.5K`, `2K`, and `4K`, with default `1K`.
- The local runtime uses `512px` instead of `0.5K`; treat those as equivalent in practice for this skill.
- Vertex image-editing examples explicitly show `imageSize: "4K"` in `generationConfig.imageConfig`.
- Provider relays may lag behind or partially implement the official API. If a provider ignores `imageSize`, record it as a provider-side quirk.

## TEXT / IMAGE parameter semantics

### Output control

`generationConfig.responseModalities` controls output modalities:

- `["IMAGE"]` → image output only
- `["TEXT", "IMAGE"]` → interleaved text + image output

### Input structure

Inputs are sent inside `contents.parts`:

- text prompt → `{ "text": "..." }`
- image input → inline image data or file data part

For image editing, the request usually includes:

- one or more image parts
- then a text instruction describing the edit

### Current local runtime behavior

The bundled runtime currently:

- always requests `["IMAGE"]`
- sends any provided input images as inline image parts
- appends the text prompt as the final part
- optionally sets `aspectRatio`
- optionally sets `imageSize`

This means the runtime is currently focused on producing image files, not mixed text+image responses.

## Operational guidance

- If the user wants very tall or very wide outputs like `1:8`, `8:1`, `1:4`, or `4:1`, prefer `gemini-3.1-flash-image-preview`.
- If the user wants stronger reasoning, harder edits, or multi-turn image editing, prefer `gemini-3-pro-image-preview`.
- Provider relays can lag behind official model releases. If a provider says a canonical model is unavailable, verify the provider's supported model list before assuming the skill is wrong.

## Sources checked

- Vertex AI model page for `gemini-3.1-flash-image-preview`
- Vertex AI model page for `gemini-3-pro-image-preview`
- Vertex AI guide: `Generate images with Gemini`
- Vertex AI guide: `Edit images with Gemini`
