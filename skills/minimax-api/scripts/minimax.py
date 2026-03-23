#!/usr/bin/env python3
"""
MiniMax API 核心脚本
提供文本生成、语音合成、语音克隆等常用功能
"""

import os
import sys
import json
import argparse
import requests

DEFAULT_HOST = "https://api.minimaxi.com"


class MiniMaxAPI:
    def __init__(self, api_key=None, host=None):
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY")
        self.host = host or os.environ.get("MINIMAX_API_HOST", DEFAULT_HOST)
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY is required")

    def _headers(self, extra=None):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if extra:
            headers.update(extra)
        return headers

    def text_chat(self, message, model="MiniMax-M2.7-200k", max_tokens=1024):
        """文本对话 (Anthropic 兼容)"""
        response = requests.post(
            f"{self.host}/anthropic/v1/messages",
            headers=self._headers(
                {"Content-Type": "application/json", "anthropic-version": "2023-06-01"}
            ),
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": message}],
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def tts(self, text, model="speech-02-hd", voice_id=None, stream=False):
        """语音合成"""
        data = {"model": model, "text": text, "stream": stream}
        if voice_id:
            data["voice_setting"] = {"voice_id": voice_id}
        response = requests.post(
            f"{self.host}/v1/t2a_v2", headers=self._headers(), json=data, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def voice_clone_upload(self, file_path):
        """上传音频用于语音克隆"""
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.host}/v1/voice_cloning/upload",
                headers=self._headers(),
                files={"file": f},
                timeout=30,
            )
        response.raise_for_status()
        return response.json()

    def image_generate(self, prompt, model="image-01", aspect_ratio="1:1"):
        """文生图 (Text-to-Image)"""
        response = requests.post(
            f"{self.host}/v1/image_generation",
            headers=self._headers(),
            json={"model": model, "prompt": prompt, "aspect_ratio": aspect_ratio},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def image_i2i(self, image_path, prompt, model="image-01", aspect_ratio="1:1"):
        """图生图 (Image-to-Image)"""
        import base64

        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()
        response = requests.post(
            f"{self.host}/v1/image_generation",
            headers=self._headers(),
            json={
                "model": model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "subject_reference": [
                    {
                        "type": "character",
                        "image_file": f"data:image/jpeg;base64,{image_base64}",
                    }
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def video_generate(self, prompt, model="video-01"):
        """视频生成 (异步)"""
        response = requests.post(
            f"{self.host}/v1/video_generation",
            headers=self._headers(),
            json={"model": model, "prompt": prompt},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def video_query(self, task_id):
        """查询视频生成状态"""
        response = requests.get(
            f"{self.host}/v1/video_generation/{task_id}",
            headers=self._headers(),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


def main():
    parser = argparse.ArgumentParser(description="MiniMax API 工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    chat = subparsers.add_parser("chat", help="文本对话")
    chat.add_argument("message", help="对话消息")
    chat.add_argument("--model", default="MiniMax-M2.7-200k", help="模型名称")

    tts = subparsers.add_parser("tts", help="语音合成")
    tts.add_argument("text", help="要转换的文本")
    tts.add_argument("--voice-id", help="语音 ID")
    tts.add_argument("--model", default="speech-02-hd", help="TTS 模型")

    clone = subparsers.add_parser("clone-upload", help="上传音频用于克隆")
    clone.add_argument("file", help="音频文件路径")

    img = subparsers.add_parser("image", help="文生图")
    img.add_argument("prompt", help="图像描述")
    img.add_argument("--ratio", default="1:1", help="宽高比")

    i2i = subparsers.add_parser("i2i", help="图生图")
    i2i.add_argument("image", help="参考图像路径")
    i2i.add_argument("prompt", help="图像描述/修改指令")
    i2i.add_argument("--ratio", default="1:1", help="宽高比")

    video = subparsers.add_parser("video", help="视频生成")
    video.add_argument("prompt", help="视频描述")

    video_query = subparsers.add_parser("video-query", help="查询视频状态")
    video_query.add_argument("task_id", help="任务 ID")

    args = parser.parse_args()

    client = MiniMaxAPI()

    try:
        if args.command == "chat":
            result = client.text_chat(args.message, args.model)
            content = result.get("content", [])
            for block in content:
                if block.get("type") == "text":
                    print(block["text"])

        elif args.command == "tts":
            result = client.tts(args.text, args.model, args.voice_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "clone-upload":
            result = client.voice_clone_upload(args.file)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "image":
            result = client.image_generate(args.prompt, aspect_ratio=args.ratio)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "i2i":
            result = client.image_i2i(args.image, args.prompt, aspect_ratio=args.ratio)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "video":
            result = client.video_generate(args.prompt)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "video-query":
            result = client.video_query(args.task_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            parser.print_help()

    except requests.exceptions.HTTPError as e:
        print(
            f"API 错误: {e.response.status_code} - {e.response.text}", file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
