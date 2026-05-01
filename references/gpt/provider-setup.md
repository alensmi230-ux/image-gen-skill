# Provider setup

Config path: `<workspace>/.openclaw/local/gpt-image-providers.json`.

```json
{
  "default_provider": "sealineai",
  "providers": {
    "sealineai": {
      "base_url": "https://sealineai.com/v1",
      "api_key": "YOUR_API_KEY",
      "default_model": "gpt-image-2"
    }
  }
}
```

Use `api_keys` as an array when rotating multiple keys. Keep credentials local and never commit them.
