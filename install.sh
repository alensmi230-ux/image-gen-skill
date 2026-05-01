#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${IMAGE_GEN_SKILL_REPO:-https://github.com/clawdbot/image-gen-skill.git}"
TARGET="${IMAGE_GEN_SKILL_DIR:-${HOME}/.openclaw/workspace/skills/image-gen}"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

if command -v git >/dev/null 2>&1; then
  git clone --depth=1 "$REPO_URL" "$TMP/image-gen-skill"
else
  echo "Error: git is required to install this skill" >&2
  exit 1
fi

mkdir -p "$(dirname "$TARGET")"
if [[ -d "$TARGET" ]]; then
  backup="${TARGET}.bak.$(date +%Y%m%d%H%M%S)"
  mv "$TARGET" "$backup"
  echo "Existing skill moved to $backup"
fi
cp -a "$TMP/image-gen-skill" "$TARGET"
rm -rf "$TARGET/.git"
chmod +x "$TARGET/scripts/image.sh" 2>/dev/null || true
echo "Installed image-gen skill to $TARGET"
