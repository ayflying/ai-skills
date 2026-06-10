#!/usr/bin/env python3
"""调用 OpenAI GPT Image 系列模型生成、图生图或编辑图片。"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests


DEFAULT_MODEL = "gpt-image-2"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
API_KEY_ENV = "GPT_IMAGE_API_KEY"
BASE_URL_ENV = "GPT_IMAGE_BASE_URL"
LEGACY_API_KEY_ENV = "OPENAI_API_KEY"
LEGACY_BASE_URL_ENV = "OPENAI_BASE_URL"


def load_env(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def api_headers() -> dict[str, str]:
    api_key = os.environ.get(API_KEY_ENV) or os.environ.get(LEGACY_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"缺少 {API_KEY_ENV}，请设置环境变量或在 .env 中填写。")
    return {"Authorization": f"Bearer {api_key}"}


def base_url() -> str:
    url = os.environ.get(BASE_URL_ENV) or os.environ.get(LEGACY_BASE_URL_ENV, DEFAULT_BASE_URL)
    return normalize_base_url(url)


def normalize_base_url(url: str) -> str:
    normalized = url.strip().rstrip("/")
    parts = urlsplit(normalized)
    if parts.scheme and parts.netloc and parts.path in ("", "/"):
        return urlunsplit((parts.scheme, parts.netloc, "/v1", "", ""))
    return normalized


def ensure_output_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def output_path(base: Path, index: int, total: int, output_format: str) -> Path:
    suffix = f".{output_format}"
    if total == 1:
        return base.with_suffix(suffix)
    return base.with_name(f"{base.stem}_{index}{suffix}")


def save_images(response_json: dict[str, Any], output: Path, output_format: str) -> list[Path]:
    data = response_json.get("data") or []
    if not data:
        raise RuntimeError(f"响应中没有图片数据：{json.dumps(response_json, ensure_ascii=False)[:1000]}")

    saved: list[Path] = []
    for index, item in enumerate(data):
        b64_json = item.get("b64_json")
        if not b64_json:
            raise RuntimeError("响应未返回 b64_json；GPT Image 模型不支持 URL 输出。")
        target = output_path(output, index, len(data), output_format)
        ensure_output_dir(target)
        target.write_bytes(base64.b64decode(b64_json))
        saved.append(target)
    return saved


def raise_for_api_error(response: requests.Response) -> None:
    if response.ok:
        return
    try:
        payload = response.json()
        message = payload.get("error", {}).get("message") or json.dumps(payload, ensure_ascii=False)
    except ValueError:
        message = response.text
    raise RuntimeError(f"OpenAI API 请求失败 ({response.status_code}): {message}")


def common_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": args.model,
        "prompt": args.prompt,
        "n": args.n,
        "size": args.size,
        "quality": args.quality,
        "output_format": args.output_format,
        "background": args.background,
        "moderation": args.moderation,
    }
    if args.user:
        payload["user"] = args.user
    if args.output_compression is not None:
        payload["output_compression"] = args.output_compression
    return payload


def generate(args: argparse.Namespace) -> list[Path]:
    payload = common_payload(args)
    headers = {"Content-Type": "application/json", **api_headers()}
    response = requests.post(
        f"{base_url()}/images/generations",
        headers=headers,
        json=payload,
        timeout=args.timeout,
    )
    raise_for_api_error(response)
    return save_images(response.json(), args.output, args.output_format)


def edit(args: argparse.Namespace) -> list[Path]:
    payload = common_payload(args)
    if args.input_fidelity:
        if args.model == "gpt-image-2":
            raise RuntimeError("gpt-image-2 会自动以高保真处理输入图，请不要传 --input-fidelity。")
        payload["input_fidelity"] = args.input_fidelity

    files = []
    handles = []
    try:
        for image_path in args.image:
            path = Path(image_path)
            handle = path.open("rb")
            handles.append(handle)
            files.append(("image[]", (path.name, handle, "application/octet-stream")))

        if args.mask:
            mask_path = Path(args.mask)
            mask_handle = mask_path.open("rb")
            handles.append(mask_handle)
            files.append(("mask", (mask_path.name, mask_handle, "application/octet-stream")))

        response = requests.post(
            f"{base_url()}/images/edits",
            headers=api_headers(),
            data={key: str(value) for key, value in payload.items() if value is not None},
            files=files,
            timeout=args.timeout,
        )
    finally:
        for handle in handles:
            handle.close()

    raise_for_api_error(response)
    return save_images(response.json(), args.output, args.output_format)


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("prompt", help="图片提示词")
    parser.add_argument("-o", "--output", type=Path, default=Path("outputs/gpt-image.png"), help="输出文件路径")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="模型名称")
    parser.add_argument("--size", default="auto", help="输出尺寸，例如 auto、1024x1024、1536x864")
    parser.add_argument("--quality", choices=["auto", "low", "medium", "high"], default="auto", help="输出质量")
    parser.add_argument("--format", dest="output_format", choices=["png", "jpeg", "webp"], default="png", help="输出格式")
    parser.add_argument("--background", choices=["auto", "opaque", "transparent"], default="auto", help="背景模式，部分 GPT Image 模型不支持 transparent")
    parser.add_argument("--moderation", choices=["auto", "low"], default="auto", help="内容审核强度")
    parser.add_argument("--compression", dest="output_compression", type=int, choices=range(0, 101), metavar="0-100", help="jpeg/webp 压缩质量")
    parser.add_argument("--n", type=int, default=1, help="生成数量")
    parser.add_argument("--user", help="终端用户标识，用于滥用检测")
    parser.add_argument("--timeout", type=int, default=300, help="请求超时时间（秒）")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="使用 OpenAI GPT Image 系列模型生成、图生图或编辑图片")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="根据文本生成图片")
    add_common_args(generate_parser)
    generate_parser.set_defaults(func=generate)

    edit_parser = subparsers.add_parser("edit", help="根据参考图编辑或重绘图片")
    add_common_args(edit_parser)
    edit_parser.add_argument("--image", action="append", required=True, help="参考图路径，可重复传入")
    edit_parser.add_argument("--mask", help="局部编辑遮罩图，需和第一张输入图尺寸一致并包含 alpha 通道")
    edit_parser.add_argument("--input-fidelity", choices=["high", "low"], help="参考图保真度")
    edit_parser.set_defaults(func=edit)

    i2i_parser = subparsers.add_parser("i2i", help="图生图：根据参考图生成新图片")
    add_common_args(i2i_parser)
    i2i_parser.add_argument("--image", action="append", required=True, help="参考图路径，可重复传入")
    i2i_parser.add_argument("--mask", help="局部编辑遮罩图，需和第一张输入图尺寸一致并包含 alpha 通道")
    i2i_parser.add_argument("--input-fidelity", choices=["high", "low"], help="参考图保真度")
    i2i_parser.set_defaults(func=edit)

    return parser


def main() -> int:
    load_env(Path(__file__).resolve().parents[1] / ".env")
    parser = build_parser()
    args = parser.parse_args()

    try:
        saved = args.func(args)
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(json.dumps({"success": True, "files": [str(path) for path in saved]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
