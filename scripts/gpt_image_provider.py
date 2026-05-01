#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Dict

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = str(WORKSPACE_ROOT / ".openclaw" / "local" / "gpt-image-providers.json")
UNIFIED_CONFIG_PATH = str(WORKSPACE_ROOT / ".openclaw" / "local" / "image-gen-providers.json")
DEFAULT_MODEL = "gpt-image-2"
VALID_QUALITIES = {"auto", "low", "medium", "high"}
VALID_OUTPUT_FORMATS = {"png", "jpeg", "webp"}
VALID_BACKGROUNDS = {"auto", "opaque"}


def err(msg: str, code: int = 1):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def load_provider_config() -> Dict[str, Any]:
    cfg_path = os.environ.get("GPT_IMAGE_PROVIDER_CONFIG") or os.environ.get("IMAGE_GEN_PROVIDER_CONFIG")
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
            '{"default_provider":"default","providers":{"default":{"api_key":"YOUR_KEY","gpt":{"base_url":"https://example.com/v1","default_model":"gpt-image-2"}}}}'
        )
    try:
        return json.loads(p.read_text())
    except Exception as e:
        err(f"failed to parse provider config {p}: {e}")


def choose_provider(cfg: Dict[str, Any], provider_name: str | None) -> tuple[str, Dict[str, Any]]:
    providers = cfg.get("providers") or {}
    if not providers:
        err("provider config has no providers")
    name = provider_name or os.environ.get("GPT_IMAGE_PROVIDER") or cfg.get("default_provider")
    if not name:
        err("no provider selected and no default_provider configured")
    if name not in providers:
        err(f"provider '{name}' not found in config")
    prov = providers[name]
    if isinstance(prov.get("gpt"), dict):
        merged = {k: v for k, v in prov.items() if k not in {"gpt", "gemini", "nanobanana"}}
        merged.update(prov["gpt"])
        prov = merged
    has_single = bool(prov.get("api_key"))
    has_multi = bool(prov.get("api_keys"))
    if not prov.get("base_url") or not (has_single or has_multi):
        err(f"provider '{name}' is missing gpt.base_url/base_url and api_key/api_keys")
    return name, prov


def build_endpoint(base_url: str, edits: bool = False) -> str:
    path = "images/edits" if edits else "images/generations"
    return f"{base_url.rstrip('/')}/{path}"


def extension_for_mime(mime: str, output_format: str) -> str:
    mapping = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}
    return mapping.get((mime or "").lower(), ".jpg" if output_format == "jpeg" else f".{output_format}")


def build_generation_payload(args: argparse.Namespace, model: str) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": args.prompt,
        "n": args.n,
        "quality": args.quality,
        "size": args.size,
        "output_format": args.output_format,
        "background": args.background,
        "moderation": args.moderation,
        "stream": False,
    }
    if args.user:
        payload["user"] = args.user
    if args.output_format in {"jpeg", "webp"} and args.output_compression is not None:
        payload["output_compression"] = args.output_compression
    return payload


def build_edit_form(args: argparse.Namespace, model: str) -> tuple[bytes, str]:
    boundary = "----openclaw-gpt-image-" + uuid.uuid4().hex
    chunks: list[bytes] = []

    def add_field(name: str, value: Any):
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    def add_file(name: str, path: str):
        p = Path(path)
        if not p.exists():
            err(f"input image not found: {path}")
        mime, _ = mimetypes.guess_type(str(p))
        if not mime:
            mime = "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"; filename="{p.name}"\r\n'.encode())
        chunks.append(f"Content-Type: {mime}\r\n\r\n".encode())
        chunks.append(p.read_bytes())
        chunks.append(b"\r\n")

    fields: Dict[str, Any] = {
        "model": model,
        "prompt": args.prompt,
        "n": args.n,
        "quality": args.quality,
        "size": args.size,
        "output_format": args.output_format,
        "background": args.background,
        "moderation": args.moderation,
        "stream": "false",
    }
    if args.user:
        fields["user"] = args.user
    if args.output_format in {"jpeg", "webp"} and args.output_compression is not None:
        fields["output_compression"] = args.output_compression
    for k, v in fields.items():
        add_field(k, v)
    image_field = args.image_field
    for path in args.inputs:
        add_file(image_field, path)
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary

def collect_keys(provider: Dict[str, Any]) -> list[str]:
    keys: list[str] = []
    if provider.get("api_keys"):
        keys.extend([k for k in provider.get("api_keys", []) if k])
    if provider.get("api_key"):
        keys.append(provider["api_key"])
    seen = set()
    deduped = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            deduped.append(k)
    if not deduped:
        err("provider has no usable api_key/api_keys")
    return deduped


def api_post_with_rotation(
    url: str, provider: Dict[str, Any], body: bytes, content_type: str
) -> tuple[Dict[str, Any], str, int, int]:
    keys = collect_keys(provider)
    total = len(keys)
    last_error = None
    for idx, key in enumerate(keys, start=1):
        masked = (key[:6] + "..." + key[-4:]) if len(key) >= 14 else "set"
        print(f"  Key:      {idx}/{total} {masked}")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": content_type},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.loads(resp.read().decode("utf-8")), masked, idx, total
        except urllib.error.HTTPError as e:
            data = e.read().decode("utf-8", errors="replace")
            try:
                msg = json.dumps(json.loads(data), ensure_ascii=False)
            except Exception:
                msg = f"HTTP {e.code}: {data}"
            last_error = msg
            low = msg.lower()
            if idx < total and ("quota" in low or "rate" in low or "额度" in msg):
                print(f"  Rotate:   key {idx}/{total} failed/quota-limited, trying next key")
                continue
            err(msg)
        except urllib.error.URLError as e:
            last_error = f"request failed: {e}"
            if idx < total:
                print(f"  Rotate:   key {idx}/{total} network error, trying next key")
                continue
            err(last_error)
    err(last_error or "all rotated keys failed")

def extract_images(response: Dict[str, Any]) -> list[tuple[bytes, str]]:
    if response.get("error"):
        err(json.dumps(response["error"], ensure_ascii=False))
    out = []
    for item in response.get("data") or []:
        b64 = item.get("b64_json") or item.get("base64")
        if b64:
            mime = item.get("mime_type") or item.get("mimeType") or "image/png"
            out.append((base64.b64decode(b64), mime))
            continue
        url = item.get("url")
        if url:
            with urllib.request.urlopen(url, timeout=300) as resp:
                mime = resp.headers.get_content_type() or "application/octet-stream"
                out.append((resp.read(), mime))
    if not out:
        err("no image returned by provider")
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate/edit images via OpenAI-compatible gpt-image-2 Image API")
    p.add_argument("prompt", nargs="?", help="Prompt text")
    p.add_argument("-i", dest="inputs", action="append", default=[], help="Reference/input image (repeatable)")
    p.add_argument("--image-field", default="image", choices=["image", "image[]"], help="Multipart image field for edits; default image")
    p.add_argument("-o", dest="output", default="", help="Output filename")
    p.add_argument("-size", default="auto", help="Image size, default auto")
    p.add_argument("-quality", default="auto", choices=sorted(VALID_QUALITIES), help="Quality, default auto")
    p.add_argument("-n", type=int, default=1, help="Number of images, default 1")
    p.add_argument("--output-format", default="png", choices=sorted(VALID_OUTPUT_FORMATS), help="png, jpeg, or webp")
    p.add_argument("--output-compression", type=int, default=None, help="0-100, only for jpeg/webp")
    p.add_argument("--background", default="auto", choices=sorted(VALID_BACKGROUNDS), help="auto or opaque")
    p.add_argument("--moderation", default="auto", help="Provider-supported moderation value, default auto")
    p.add_argument("--user", default="", help="Optional end-user identifier")
    p.add_argument("--provider", default=None, help="Provider name from local config")
    p.add_argument("--model", default=None, help="Model name, default provider.default_model or gpt-image-2")
    p.add_argument("-version", action="store_true", help="Show version")
    return p.parse_args()


def output_path_for(base: str, index: int, total: int, ext: str) -> str:
    if not base:
        from datetime import datetime
        stem = f"image_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        return f"{stem}{('-' + str(index)) if total > 1 else ''}{ext}"
    p = Path(base)
    if total > 1:
        return str(p.with_name(f"{p.stem}-{index}{ext}"))
    if p.suffix.lower() != ext:
        adjusted = str(p.with_suffix(ext))
        print(f"Info: adjusted output extension to match returned mime type: {adjusted}")
        return adjusted
    return str(p)


def main():
    args = parse_args()
    if args.version:
        print("gpt-image-provider 1.0")
        return
    if not args.prompt:
        err("no prompt provided")
    if args.n < 1:
        err("n must be >= 1")
    if args.output_compression is not None and not (0 <= args.output_compression <= 100):
        err("output_compression must be 0-100")

    cfg = load_provider_config()
    provider_name, provider = choose_provider(cfg, args.provider)
    model = args.model or provider.get("default_model") or cfg.get("default_model") or DEFAULT_MODEL
    use_edits = bool(args.inputs)
    endpoint = build_endpoint(provider["base_url"], edits=use_edits)
    if use_edits:
        body, boundary = build_edit_form(args, model)
        content_type = f"multipart/form-data; boundary={boundary}"
    else:
        body = json.dumps(build_generation_payload(args, model)).encode("utf-8")
        content_type = "application/json"

    print("Generating image...")
    print(f"  Provider: {provider_name}")
    print(f"  Endpoint: {endpoint}")
    print(f"  Model:    {model}")
    print(f"  Size:     {args.size}")
    print(f"  Quality:  {args.quality}")
    print(f"  Format:   {args.output_format}")
    if args.inputs:
        print(f"  Inputs:   {', '.join(args.inputs)}")

    response, used_key_masked, used_key_idx, used_key_total = api_post_with_rotation(endpoint, provider, body, content_type)
    print(f"  Selected: key {used_key_idx}/{used_key_total} {used_key_masked}")
    images = extract_images(response)
    saved = []
    for idx, (image_bytes, mime) in enumerate(images, start=1):
        ext = extension_for_mime(mime, args.output_format)
        path = output_path_for(args.output, idx, len(images), ext)
        Path(path).write_bytes(image_bytes)
        saved.append(path)
    for path in saved:
        print(f"Image saved to: {path}")


if __name__ == "__main__":
    main()
