# Source notes

This local skill started from these GitHub sources:

1. `skorfmann/nanobanana`
   - useful as a reference for Gemini image request structure
   - repo: https://github.com/skorfmann/nanobanana
2. `feedtailor/ccskill-nanobanana`
   - practical examples of reference-image editing workflows
   - repo: https://github.com/feedtailor/ccskill-nanobanana
3. `CodaLabs-xyz/openclaw-nanobanana-skill`
   - OpenClaw-oriented skill layout ideas
   - repo: https://github.com/CodaLabs-xyz/openclaw-nanobanana-skill

## Important local changes

The current runtime no longer depends on the upstream nanobanana CLI for API calls.

Reason:
- the upstream CLI hardcodes Google's public Gemini endpoint
- this workspace needs support for alternate providers that are Google/Gemini-compatible but use different base URLs and API keys

So this skill now uses:

- `scripts/nanobanana_provider.py`
  - local Python runtime
  - direct POST to a configured provider URL
  - Google/Gemini-compatible request body
  - support for image input, multi-image composition, aspect ratio, and image size
  - provider selection via local config

## Local config

Provider credentials live in:

- `<workspace>/.openclaw/local/nanobanana-providers.json`

This file is local machine configuration and should not be committed into shared repositories.

## Default behavior changes

- Aspect ratio default is now `auto` (omit `aspectRatio` unless specified)
- Image size default is now `auto` (omit `imageSize` unless specified)
- This better preserves official-provider default behavior, especially for image-edit flows with input images
