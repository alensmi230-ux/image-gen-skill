#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
WORKSPACE_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"

echo "This skill no longer requires the upstream nanobanana binary for API calls."
echo "It uses the local Python runtime at:"
echo "  $SCRIPT_DIR/nanobanana_provider.py"
echo
CFG="${NANOBANANA_PROVIDER_CONFIG:-$WORKSPACE_ROOT/.openclaw/local/nanobanana-providers.json}"
echo "Expected provider config: $CFG"
