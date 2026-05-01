#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GPT_SCRIPT="$SCRIPT_DIR/gpt-image.sh"
GEMINI_SCRIPT="$SCRIPT_DIR/nanobanana.sh"

backend="auto"
model=""
args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend|--engine)
      backend="${2:-}"
      shift 2
      ;;
    --model)
      model="${2:-}"
      args+=("--model" "$2")
      shift 2
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

if [[ "$backend" == "auto" ]]; then
  shopt -s nocasematch
  if [[ -n "$model" && ( "$model" == *gemini* || "$model" == *banana* || "$model" == *nano* ) ]]; then
    backend="gemini"
  else
    backend="gpt"
  fi
  shopt -u nocasematch
fi

case "$backend" in
  gpt|openai|gpt-image|gpt-image-2)
    exec bash "$GPT_SCRIPT" "${args[@]}"
    ;;
  gemini|nanobanana|nano-banana|banana)
    exec bash "$GEMINI_SCRIPT" "${args[@]}"
    ;;
  *)
    echo "Error: unknown backend '$backend' (use gpt or gemini)" >&2
    exit 1
    ;;
esac
