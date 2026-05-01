#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = str(WORKSPACE_ROOT / ".openclaw" / "local" / "nanobanana-providers.json")
UNIFIED_CONFIG_PATH = str(WORKSPACE_ROOT / ".openclaw" / "local" / "image-gen-providers.json")
DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
MODEL_ALIASES = {
    "nanobanana2": "gemini-3.1-flash-image-preview",
    "nano-banana-2": "gemini-3.1-flash-image-preview",
    "nanobananaapro": "gemini-3-pro-image-preview",
    "nanobananapro": "gemini-3-pro-image-preview",
    "nano-banana-pro": "gemini-3-pro-image-preview",
}
VALID_ASPECTS = {
    "auto", "1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1", "4:3",
    "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"
}
VALID_SIZES = {"auto", "512px", "1K", "2K", "4K"}


def err(msg: str, code: int = 1):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def load_provider_config() -> Dict[str, Any]:
    cfg_path = os.environ.get("NANOBANANA_PROVIDER_CONFIG") or os.environ.get("IMAGE_GEN_PROVIDER_CONFIG")
    if cfg_path:
        candidates = [cfg_path]
    else:
        candidates = [DEFAULT_CONFIG_PATH, UNIFIED_CONFIG_PATH]
    p = next((Path(x) for x in candidates if Path(x).exists()), None)
    if p is None:
        err(
            "provider config not found. Create either "
            f"{DEFAULT_CONFIG_PATH} or {UNIFIED_CONFIG_PATH}. "
            "Unified config example: "
            '{"default_provider":"default","providers":{"default":{"api_key":"YOUR_KEY","gemini":{"base_url":"https://generativelanguage.googleapis.com","default_model":"gemini-3.1-flash-image-preview"}}}}'
        )
    try:
        return json.loads(p.read_text())
    except Exception as e:
        err(f"failed to parse provider config {p}: {e}")


def choose_provider(cfg: Dict[str, Any], provider_name: str | None) -> tuple[str, Dict[str, Any]]:
    providers = cfg.get("providers") or {}
    if not providers:
        err("provider config has no providers")
    name = provider_name or os.environ.get("NANOBANANA_PROVIDER") or cfg.get("default_provider")
    if not name:
        err("no provider selected and no default_provider configured")
    if name not in providers:
        err(f"provider '{name}' not found in config")
    prov = providers[name]
    backend_cfg = prov.get("gemini") or prov.get("nanobanana")
    if isinstance(backend_cfg, dict):
        merged = {k: v for k, v in prov.items() if k not in {"gpt", "gemini", "nanobanana"}}
        merged.update(backend_cfg)
        prov = merged
    has_single = bool(prov.get("api_key"))
    has_multi = bool(prov.get("api_keys"))
    if not prov.get("base_url") or not (has_single or has_multi):
        err(f"provider '{name}' is missing gemini.base_url/base_url and api_key/api_keys")
    return name, prov


def build_endpoint(base_url: str, model: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith(":generateContent"):
        return base
    if "/v1beta/models/" in base:
        return f"{base}:generateContent"
    return f"{base}/v1beta/models/{model}:generateContent"


def resolve_model_alias(model: str) -> str:
    return MODEL_ALIASES.get(model.strip().lower(), model)


def load_image_part(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        err(f"input image not found: {path}")
    mime, _ = mimetypes.guess_type(str(p))
    if not mime:
        mime = "application/octet-stream"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return {"inlineData": {"mimeType": mime, "data": data}}


def extension_for_mime(mime: str) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    return mapping.get((mime or "").lower(), ".bin")


def build_request(prompt: str, inputs: list[str], aspect: str, size: str) -> Dict[str, Any]:
    parts = [load_image_part(p) for p in inputs]
    parts.append({"text": prompt})
    gen_cfg: Dict[str, Any] = {"responseModalities": ["IMAGE"]}
    image_cfg: Dict[str, Any] = {}
    if aspect != "auto":
        image_cfg["aspectRatio"] = aspect
    if size != "auto":
        image_cfg["imageSize"] = size
    if image_cfg:
        gen_cfg["imageConfig"] = image_cfg
    return {
        "contents": [{"parts": parts}],
        "generationConfig": gen_cfg,
    }


def api_post(url: str, api_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        data = e.read().decode("utf-8", errors="replace")
        try:
            obj = json.loads(data)
            err(json.dumps(obj, ensure_ascii=False))
        except Exception:
            err(f"HTTP {e.code}: {data}")
    except urllib.error.URLError as e:
        err(f"request failed: {e}")


def api_post_with_rotation(url: str, provider: Dict[str, Any], payload: Dict[str, Any]) -> tuple[Dict[str, Any], str, int, int]:
    keys = []
    if provider.get("api_keys"):
        keys.extend([k for k in provider.get("api_keys", []) if k])
    if provider.get("api_key"):
        keys.append(provider["api_key"])
    # dedupe while preserving order
    seen = set()
    deduped = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            deduped.append(k)
    if not deduped:
        err("provider has no usable api_key/api_keys")

    last_error = None
    total = len(deduped)
    for idx, key in enumerate(deduped, start=1):
        masked = (key[:6] + '...' + key[-4:]) if len(key) >= 14 else 'set'
        print(f"  Key:      {idx}/{total} {masked}")
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": key,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.loads(resp.read().decode("utf-8")), masked, idx, total
        except urllib.error.HTTPError as e:
            data = e.read().decode("utf-8", errors="replace")
            try:
                obj = json.loads(data)
                msg = json.dumps(obj, ensure_ascii=False)
            except Exception:
                msg = f"HTTP {e.code}: {data}"
            last_error = msg
            low = msg.lower()
            if ("insufficient_user_quota" in low or "额度" in msg or "quota" in low) and idx < total:
                print(f"  Rotate:   key {idx}/{total} quota-limited, trying next key")
                continue
            if idx < total:
                print(f"  Rotate:   key {idx}/{total} failed, trying next key")
                continue
            err(msg)
        except urllib.error.URLError as e:
            last_error = f"request failed: {e}"
            if idx < total:
                print(f"  Rotate:   key {idx}/{total} network error, trying next key")
                continue
            err(last_error)
    err(last_error or "all rotated keys failed")


def extract_image(response: Dict[str, Any]) -> tuple[bytes, str]:
    candidates = response.get("candidates") or []
    for cand in candidates:
        parts = ((cand.get("content") or {}).get("parts") or [])
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                mime = inline.get("mimeType") or inline.get("mime_type") or "application/octet-stream"
                return base64.b64decode(inline["data"]), mime
    if response.get("error"):
        err(json.dumps(response["error"], ensure_ascii=False))
    err("no image returned by provider")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate/edit images via Gemini-compatible providers")
    p.add_argument("prompt", nargs="?", help="Prompt text")
    p.add_argument("-i", dest="inputs", action="append", default=[], help="Input image (repeatable)")
    p.add_argument("-o", dest="output", default="", help="Output filename")
    p.add_argument("-aspect", default="auto", help="Aspect ratio or auto")
    p.add_argument("-size", default="auto", help="Image size or auto")
    p.add_argument("--provider", default=None, help="Provider name from local config")
    p.add_argument("--model", default=DEFAULT_MODEL, help="Model name")
    p.add_argument("-version", action="store_true", help="Show version")
    return p.parse_args()


def main():
    args = parse_args()
    if args.version:
        print("nanobanana-provider 1.0")
        return
    if not args.prompt:
        err("no prompt provided")
    if args.aspect not in VALID_ASPECTS:
        err(f"invalid aspect ratio: {args.aspect}")
    if args.size not in VALID_SIZES:
        err(f"invalid image size: {args.size}")

    cfg = load_provider_config()
    provider_name, provider = choose_provider(cfg, args.provider)
    model_arg = args.model or provider.get("default_model") or cfg.get("default_model") or DEFAULT_MODEL
    resolved_model = resolve_model_alias(model_arg)
    endpoint = build_endpoint(provider["base_url"], resolved_model)
    payload = build_request(args.prompt, args.inputs, args.aspect, args.size)

    print("Generating image...")
    print(f"  Provider: {provider_name}")
    print(f"  Endpoint: {endpoint}")
    print(f"  Model:    {resolved_model}")
    if resolved_model != model_arg:
        print(f"  Alias:    {model_arg} -> {resolved_model}")
    print(f"  Aspect:   {args.aspect}")
    print(f"  Size:     {args.size}")
    if args.inputs:
        print(f"  Inputs:   {', '.join(args.inputs)}")

    response, used_key_masked, used_key_idx, used_key_total = api_post_with_rotation(endpoint, provider, payload)
    print(f"  Selected: key {used_key_idx}/{used_key_total} {used_key_masked}")
    image_bytes, mime = extract_image(response)

    output = args.output
    ext = extension_for_mime(mime)
    if not output:
        from datetime import datetime
        output = f"image_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{ext}"
    else:
        current_ext = Path(output).suffix.lower()
        if current_ext != ext:
            output = str(Path(output).with_suffix(ext))
            print(f"Info: adjusted output extension to match returned mime type: {output}")

    Path(output).write_bytes(image_bytes)
    print(f"\nImage saved to: {output}")


if __name__ == "__main__":
    main()
