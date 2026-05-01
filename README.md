# image-gen skill

Unified image generation/editing skill for OpenClaw AgentSkills. It routes to either:

- `gpt-image-2` / OpenAI-compatible Image API backend
- Gemini image / Nano Banana backend

## Install

```bash
git clone --depth=1 https://github.com/clawdbot/image-gen-skill ~/.openclaw/workspace/skills/image-gen
```

For China networks, if GitHub is slow, try a GitHub proxy:

```bash
git clone --depth=1 https://ghfast.top/https://github.com/clawdbot/image-gen-skill ~/.openclaw/workspace/skills/image-gen
```

Or use the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/clawdbot/image-gen-skill/main/install.sh | bash
```

## Requirements

This wrapper expects the backend skills to already be installed in the same workspace:

- `skills/gpt-image-2`
- `skills/nanobanana-image-edit`

Provider credentials/config live outside this repository, typically under `.openclaw/local/`, and are not included here.
