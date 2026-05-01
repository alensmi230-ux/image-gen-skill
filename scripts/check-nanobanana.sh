#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
WORKSPACE_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
CFG="${NANOBANANA_PROVIDER_CONFIG:-${IMAGE_GEN_PROVIDER_CONFIG:-}}"
if [ -z "$CFG" ]; then
  if [ -f "$WORKSPACE_ROOT/.openclaw/local/nanobanana-providers.json" ]; then
    CFG="$WORKSPACE_ROOT/.openclaw/local/nanobanana-providers.json"
  else
    CFG="$WORKSPACE_ROOT/.openclaw/local/image-gen-providers.json"
  fi
fi
PY="$SCRIPT_DIR/nanobanana_provider.py"

if [ -f "$PY" ]; then
  echo "runtime: installed"
else
  echo "runtime: missing"
  exit 1
fi

if [ -f "$CFG" ]; then
  echo "config: present"
  python3 - <<PY
import json
p="$CFG"
obj=json.load(open(p))
print('config_path:', p)
print('default_provider:', obj.get('default_provider'))
for name, cfg in obj.get('providers', {}).items():
    keys = cfg.get('api_keys') or []
    if keys:
        sample = keys[0]
        masked = (sample[:6] + '...' + sample[-4:]) if len(sample) >= 14 else ('set' if sample else 'missing')
        print(f'provider: {name} url={cfg.get("base_url")} keys={len(keys)} sample={masked}')
    else:
        key = cfg.get('api_key', '')
        masked = (key[:6] + '...' + key[-4:]) if len(key) >= 14 else ('set' if key else 'missing')
        print(f'provider: {name} url={cfg.get("base_url")} key={masked}')
PY
else
  echo "config: missing"
  echo "hint: create $CFG"
  exit 1
fi
