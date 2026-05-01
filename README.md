# image-gen skill

Standalone OpenClaw AgentSkill for image generation/editing. It includes both backend implementations:

- `gpt-image-2` / OpenAI-compatible Image API
- Gemini image / Nano Banana compatible API

No separate `gpt-image-2` or `nanobanana-image-edit` skill install is required.

## Install

```bash
git clone --depth=1 https://github.com/alensmi230-ux/image-gen-skill ~/.openclaw/workspace/skills/image-gen
```

For China networks, if GitHub is slow:

```bash
git clone --depth=1 https://ghfast.top/https://github.com/alensmi230-ux/image-gen-skill ~/.openclaw/workspace/skills/image-gen
```

Or use the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/alensmi230-ux/image-gen-skill/main/install.sh | bash
```

China proxy installer:

```bash
curl -fsSL https://ghfast.top/https://raw.githubusercontent.com/alensmi230-ux/image-gen-skill/main/install.sh | bash
```

## Configure providers

Credentials are not included. Create one or both local config files:

- `~/.openclaw/workspace/.openclaw/local/gpt-image-providers.json`
- `~/.openclaw/workspace/.openclaw/local/nanobanana-providers.json`

Minimal GPT config:

```json
{
  "default_provider": "default",
  "providers": {
    "default": {
      "base_url": "https://YOUR_OPENAI_COMPATIBLE_BASE_URL/v1",
      "api_key": "YOUR_API_KEY",
      "default_model": "gpt-image-2"
    }
  }
}
```

Minimal Gemini/Nano Banana config:

```json
{
  "default_provider": "default",
  "providers": {
    "default": {
      "base_url": "https://generativelanguage.googleapis.com",
      "api_key": "YOUR_API_KEY",
      "default_model": "gemini-3.1-flash-image-preview"
    }
  }
}
```

Validate:

```bash
bash ~/.openclaw/workspace/skills/image-gen/scripts/check-gpt-image.sh
bash ~/.openclaw/workspace/skills/image-gen/scripts/check-nanobanana.sh
```
