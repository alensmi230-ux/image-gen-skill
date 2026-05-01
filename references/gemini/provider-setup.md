# Provider setup

This skill reads provider configuration from:

- `<workspace>/.openclaw/local/nanobanana-providers.json`

The runtime resolves `<workspace>` automatically from the current skill location. Do **not** hardcode `/home/node/...` or another machine-specific home path.

## Config shape

Example:

```json
{
  "default_provider": "vectorengine",
  "providers": {
    "vectorengine": {
      "base_url": "https://api.vectorengine.ai",
      "api_key": "sk-xxxx"
    },
    "yinli": {
      "base_url": "https://yinli.one",
      "api_key": "sk-yyyy"
    }
  }
}
```

Rules:

- `default_provider` should match one of the keys under `providers`
- each provider must have `base_url` and either `api_key` or `api_keys`
- `api_keys` can be an array of multiple keys for automatic per-request rotation/fallback
- `base_url` should be the provider root; the runtime appends the Gemini-compatible `v1beta/models/...:generateContent` path automatically
- this file is local machine config and should stay ignored by git

## First-use behavior

Before generating or editing images, check whether the provider config exists and whether the selected/default provider has both `base_url` and `api_key`.

If configuration is missing or incomplete:

1. **Do not pretend the skill is ready**
2. tell the user the skill needs a provider URL and API key before first use
3. ask the user for either:
   - a provider URL + API key to configure now, or
   - confirmation that they want to configure it themselves in the environment
4. if the user wants you to configure it, write/update `<workspace>/.openclaw/local/nanobanana-providers.json`
5. if the user prefers self-service, tell them exactly which file to create/edit

Suggested user-facing wording:

- "这个 skill 第一次使用前需要先配置 provider 的 URL 和 API key。"
- "你可以把它们给我，我直接帮你写进 `<workspace>/.openclaw/local/nanobanana-providers.json>`。"
- "如果你想自己配，也可以在当前 workspace 里创建这个文件；配好后我再继续出图。"

## Validation steps

Use:

```bash
bash <workspace>/skills/nanobanana-image-edit/scripts/check-nanobanana.sh
```

This should confirm:

- runtime installed
- config present
- default provider name
- masked API keys for configured providers

## Troubleshooting

### Config file missing

The runtime should fail with a message pointing to the expected config path.
In that case, ask the user for provider info or tell them where to create the file.

### Provider key missing

If a provider exists but lacks `api_key` or `base_url`, do not keep retrying.
Ask the user to complete the config or offer to fill it in for them.

### Wrong machine-specific path in docs or scripts

Always normalize to `<workspace>` in docs.
In scripts, derive the workspace path dynamically from the script location or use `NANOBANANA_PROVIDER_CONFIG`.
