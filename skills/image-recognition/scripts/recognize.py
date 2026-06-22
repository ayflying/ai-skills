#!/usr/bin/env python3
"""调用 OpenAI 兼容视觉模型识别图片，只输出精简中文文字描述。

设计目标：让 AI 把"看图"交给外部视觉模型，自己只读取本脚本返回的文字，
从而避免大量图片占用上下文、被反复压缩消耗 token。

配置只从系统环境变量读取（不使用 .env 文件）：
- IMAGE_RECOGNITION_API_KEY（回退 OPENAI_API_KEY）
- IMAGE_RECOGNITION_BASE_URL（回退 OPENAI_BASE_URL）
- IMAGE_RECOGNITION_MODEL
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests


API_KEY_ENV = "IMAGE_RECOGNITION_API_KEY"
BASE_URL_ENV = "IMAGE_RECOGNITION_BASE_URL"
MODEL_ENV = "IMAGE_RECOGNITION_MODEL"
LEGACY_API_KEY_ENV = "OPENAI_API_KEY"
LEGACY_BASE_URL_ENV = "OPENAI_BASE_URL"

DEFAULT_PROMPT = (
    "请用简体中文精炼地描述这张图片的主要内容，"
    "包括关键对象、文字、布局或数据等重点信息。"
    "只输出描述本身，不要加多余的客套话或解释。"
)


def normalize_base_url(url: str) -> str:
    """规范化接口地址：仅给裸域名补上 /v1，其它路径保持原样。"""
    normalized = url.strip().rstrip("/")
    parts = urlsplit(normalized)
    if parts.scheme and parts.netloc and parts.path in ("", "/"):
        return urlunsplit((parts.scheme, parts.netloc, "/v1", "", ""))
    return normalized


def missing_config_message(missing: list[str]) -> str:
    """生成缺失配置的中文引导提示。"""
    lines = [
        "缺少图片识别所需的配置，请向用户索要后设置以下系统环境变量：",
        "",
    ]
    hints = {
        API_KEY_ENV: "视觉模型的 API Key",
        BASE_URL_ENV: "OpenAI 兼容接口地址，例如 https://api.openai.com/v1",
        MODEL_ENV: "视觉模型名称，例如 gpt-4o-mini",
    }
    for var in missing:
        lines.append(f"- {var}（{hints[var]}）")
    lines += [
        "",
        "PowerShell 临时设置（仅当前终端有效）：",
    ]
    for var in missing:
        lines.append(f'  $env:{var}="<你的取值>"')
    lines += [
        "",
        "PowerShell 永久设置（需重开终端后生效）：",
    ]
    for var in missing:
        lines.append(f'  setx {var} "<你的取值>"')
    lines += [
        "",
        "注意：API Key 属于敏感信息，绝不要写入文件或日志。",
    ]
    return "\n".join(lines)


def resolve_config(model_override: str | None) -> dict[str, str]:
    """读取并校验三项配置；任一缺失则报错退出。"""
    api_key = os.environ.get(API_KEY_ENV) or os.environ.get(LEGACY_API_KEY_ENV)
    base = os.environ.get(BASE_URL_ENV) or os.environ.get(LEGACY_BASE_URL_ENV)
    model = model_override or os.environ.get(MODEL_ENV)

    missing: list[str] = []
    if not api_key:
        missing.append(API_KEY_ENV)
    if not base:
        missing.append(BASE_URL_ENV)
    if not model:
        missing.append(MODEL_ENV)
    if missing:
        raise RuntimeError(missing_config_message(missing))

    return {
        "api_key": api_key,
        "base_url": normalize_base_url(base),
        "model": model,
    }


def is_remote_url(target: str) -> bool:
    return target.startswith("http://") or target.startswith("https://")


def build_image_url(target: str) -> str:
    """远程图片直接返回 URL，本地图片转为 data URL。"""
    if is_remote_url(target):
        return target

    path = Path(target)
    if not path.exists():
        raise RuntimeError(f"找不到图片文件：{target}")

    mime, _ = mimetypes.guess_type(path.name)
    if not mime or not mime.startswith("image/"):
        mime = "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def recognize_one(config: dict[str, str], target: str, args: argparse.Namespace) -> str:
    prompt = args.question or DEFAULT_PROMPT
    image_url = build_image_url(target)
    payload: dict[str, Any] = {
        "model": config["model"],
        "max_tokens": args.max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url, "detail": args.detail},
                    },
                ],
            }
        ],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
    }
    response = requests.post(
        f"{config['base_url']}/chat/completions",
        headers=headers,
        json=payload,
        timeout=args.timeout,
    )
    if not response.ok:
        try:
            data = response.json()
            message = data.get("error", {}).get("message") or response.text
        except ValueError:
            message = response.text
        raise RuntimeError(f"视觉接口请求失败 ({response.status_code}): {message}")

    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("响应中没有可用的识别结果。")
    content = (choices[0].get("message") or {}).get("content")
    if not content or not str(content).strip():
        raise RuntimeError("视觉模型未返回文字内容。")
    return str(content).strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="调用 OpenAI 兼容视觉模型识别图片，只输出精简中文文字描述"
    )
    parser.add_argument("image", nargs="+", help="一个或多个图片路径或 URL")
    parser.add_argument(
        "-q", "--question", help="对图片提问或 OCR，覆盖默认的通用描述提示词"
    )
    parser.add_argument("-m", "--model", help="临时覆盖模型名（缺省取环境变量）")
    parser.add_argument(
        "--detail",
        choices=["auto", "low", "high"],
        default="auto",
        help="图片细节级别，默认 auto",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=500,
        help="单图回答的最大 token 数，默认 500",
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="请求超时时间（秒），默认 120"
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = resolve_config(args.model)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    targets = args.image
    multiple = len(targets) > 1
    failed = False
    for index, target in enumerate(targets):
        try:
            result = recognize_one(config, target, args)
        except RuntimeError as exc:
            failed = True
            print(f"错误：{exc}", file=sys.stderr)
            if multiple:
                print(f"### {target}\n[识别失败]")
            continue

        if multiple:
            if index > 0:
                print()
            print(f"### {target}")
            print(result)
        else:
            print(result)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
