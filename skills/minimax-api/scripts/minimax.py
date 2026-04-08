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

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

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

    def voice_clone_upload_file(self, file_path):
        """上传克隆音频文件 (获取 file_id)"""
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.host}/v1/files/upload",
                headers=self._headers(),
                data={"purpose": "voice_clone"},
                files={"file": f},
                timeout=30,
            )
        response.raise_for_status()
        return response.json()

    def voice_clone_upload_prompt(self, file_path):
        """上传示例音频文件 (增强克隆效果)"""
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.host}/v1/files/upload",
                headers=self._headers(),
                data={"purpose": "prompt_audio"},
                files={"file": f},
                timeout=30,
            )
        response.raise_for_status()
        return response.json()

    def voice_clone(
        self,
        file_id,
        voice_id,
        text,
        model="speech-2.8-hd",
        prompt_file_id=None,
        prompt_text=None,
    ):
        """音色克隆"""
        payload = {
            "file_id": file_id,
            "voice_id": voice_id,
            "text": text,
            "model": model,
        }
        if prompt_file_id and prompt_text:
            payload["clone_prompt"] = {
                "prompt_audio": prompt_file_id,
                "prompt_text": prompt_text,
            }
        response = requests.post(
            f"{self.host}/v1/voice_clone",
            headers=self._headers({"Content-Type": "application/json"}),
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    async def tts_websocket(
        self,
        text,
        model="speech-2.8-hd",
        voice_id="male-qn-qingse",
        speed=1,
        vol=1,
        pitch=0,
        sample_rate=32000,
        bitrate=128000,
        audio_format="mp3",
        output_path=None,
    ):
        """WebSocket 语音合成 (流式)"""
        import websockets
        import ssl

        url = "wss://api.minimaxi.com/ws/v1/t2a_v2"
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with websockets.connect(
            url, additional_headers=self._headers(), ssl=ssl_context
        ) as ws:
            connected = json.loads(await ws.recv())
            if connected.get("event") != "connected_success":
                raise Exception("WebSocket 连接失败")

            await ws.send(
                json.dumps(
                    {
                        "event": "task_start",
                        "model": model,
                        "voice_setting": {
                            "voice_id": voice_id,
                            "speed": speed,
                            "vol": vol,
                            "pitch": pitch,
                            "english_normalization": False,
                        },
                        "audio_setting": {
                            "sample_rate": sample_rate,
                            "bitrate": bitrate,
                            "format": audio_format,
                            "channel": 1,
                        },
                    }
                )
            )

            start_resp = json.loads(await ws.recv())
            if start_resp.get("event") != "task_started":
                raise Exception(f"任务启动失败: {start_resp}")

            audio_data = b""
            await ws.send(json.dumps({"event": "task_continue", "text": text}))

            while True:
                response = json.loads(await ws.recv())
                if "data" in response and "audio" in response["data"]:
                    audio_hex = response["data"]["audio"]
                    if audio_hex:
                        audio_data += bytes.fromhex(audio_hex)
                if response.get("is_final"):
                    break

            await ws.send(json.dumps({"event": "task_finish"}))

            if output_path:
                with open(output_path, "wb") as f:
                    f.write(audio_data)
                print(f"Audio saved to {output_path}")

            return audio_data

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

    def video_generate(
        self,
        prompt=None,
        model="MiniMax-Hailuo-2.3",
        first_frame_image=None,
        last_frame_image=None,
        duration=6,
        resolution="768P",
        prompt_optimizer=True,
        fast_pretreatment=False,
        aigc_watermark=False,
    ):
        """视频生成 (异步)

        支持三种模式:
        - T2V (文生视频): 只传 prompt
        - I2V (图生视频): 传 prompt + first_frame_image
        - FL2V (首尾帧视频): 传 prompt + first_frame_image + last_frame_image
        """
        data = {
            "model": model,
            "duration": duration,
            "resolution": resolution,
            "prompt_optimizer": prompt_optimizer,
            "aigc_watermark": aigc_watermark,
        }
        if prompt:
            data["prompt"] = prompt
        if first_frame_image:
            data["first_frame_image"] = first_frame_image
        if last_frame_image:
            data["last_frame_image"] = last_frame_image
        if model.startswith("MiniMax-Hailuo-2.3") or model.startswith(
            "MiniMax-Hailuo-02"
        ):
            data["fast_pretreatment"] = fast_pretreatment

        response = requests.post(
            f"{self.host}/v1/video_generation",
            headers=self._headers(),
            json=data,
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

    def music_generate(
        self,
        prompt,
        model="music-2.5+",
        lyrics=None,
        is_instrumental=False,
        lyrics_optimizer=False,
        output_format="url",
        stream=False,
        sample_rate=44100,
        bitrate=256000,
        audio_format="mp3",
        aigc_watermark=False,
    ):
        """音乐生成"""
        data = {
            "model": model,
            "prompt": prompt,
            "is_instrumental": is_instrumental,
            "lyrics_optimizer": lyrics_optimizer,
            "output_format": output_format,
            "stream": stream,
            "audio_setting": {
                "sample_rate": sample_rate,
                "bitrate": bitrate,
                "format": audio_format,
            },
            "aigc_watermark": aigc_watermark,
        }
        if lyrics:
            data["lyrics"] = lyrics
        response = requests.post(
            f"{self.host}/v1/music_generation",
            headers=self._headers(),
            json=data,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()


def _download_image(result, output_path=None):
    """下载图片到本地"""
    image_urls = result.get("data", {}).get("image_urls", [])
    if not image_urls:
        print("No image URLs in response", file=sys.stderr)
        return

    for i, url in enumerate(image_urls):
        ext = "jpg"
        if ".png" in url:
            ext = "png"
        path = output_path or f"output_{i}.{ext}"
        print(f"Downloading to {path}...")
        resp = requests.get(url)
        resp.raise_for_status()
        with open(path, "wb") as f:
            f.write(resp.content)
        print(f"Saved to {path}")


def _download_music(result, output_path=None, audio_format="mp3"):
    """下载音乐到本地"""
    data = result.get("data", {})
    audio_url = data.get("audio_url") or data.get("audio")
    if not audio_url:
        print("No audio URL in response", file=sys.stderr)
        return
    if not audio_url.startswith("http"):
        print(
            "Audio is hex-encoded, not a URL. Output format must be url.",
            file=sys.stderr,
        )
        return
    path = output_path or f"output.{audio_format}"
    print(f"Downloading to {path}...")
    resp = requests.get(audio_url)
    resp.raise_for_status()
    with open(path, "wb") as f:
        f.write(resp.content)
    print(f"Saved to {path}")


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
    img.add_argument("--output", "-o", help="保存图片路径")
    img.add_argument("--download", action="store_true", help="下载图片到本地")

    i2i = subparsers.add_parser("i2i", help="图生图")
    i2i.add_argument("image", help="参考图像路径")
    i2i.add_argument("prompt", help="图像描述/修改指令")
    i2i.add_argument("--ratio", default="1:1", help="宽高比")
    i2i.add_argument("--output", "-o", help="保存图片路径")
    i2i.add_argument("--download", action="store_true", help="下载图片到本地")

    video = subparsers.add_parser("video", help="文生视频 (T2V)")
    video.add_argument("prompt", help="视频描述")
    video.add_argument("--model", default="MiniMax-Hailuo-2.3", help="模型")
    video.add_argument("--duration", type=int, default=6, help="时长 (6/10秒)")
    video.add_argument(
        "--resolution", default="768P", help="分辨率 (512P/720P/768P/1080P)"
    )
    video.add_argument(
        "--no-prompt-optimizer", action="store_true", help="禁用 prompt 优化"
    )

    video_query = subparsers.add_parser("video-query", help="查询视频状态")
    video_query.add_argument("task_id", help="任务 ID")

    i2v = subparsers.add_parser("i2v", help="图生视频 (I2V)")
    i2v.add_argument("prompt", help="视频描述")
    i2v.add_argument("image", help="起始帧图片路径或URL")
    i2v.add_argument("--model", default="MiniMax-Hailuo-2.3", help="模型")
    i2v.add_argument("--duration", type=int, default=6, help="时长 (6/10秒)")
    i2v.add_argument("--resolution", default="768P", help="分辨率")
    i2v.add_argument(
        "--no-prompt-optimizer", action="store_true", help="禁用 prompt 优化"
    )

    fl2v = subparsers.add_parser("fl2v", help="首尾帧视频 (FL2V)")
    fl2v.add_argument("prompt", help="视频描述")
    fl2v.add_argument("first_image", help="起始帧图片路径或URL")
    fl2v.add_argument("last_image", help="结束帧图片路径或URL")
    fl2v.add_argument("--model", default="MiniMax-Hailuo-02", help="模型")
    fl2v.add_argument("--duration", type=int, default=6, help="时长 (6/10秒)")
    fl2v.add_argument("--resolution", default="768P", help="分辨率")

    music = subparsers.add_parser("music", help="音乐生成")
    music.add_argument("prompt", help="音乐描述（风格、情绪、场景）")
    music.add_argument("--lyrics", help="歌词（使用 \\n 分隔行）")
    music.add_argument("--model", default="music-2.5+", help="模型")
    music.add_argument("--instrumental", action="store_true", help="生成纯音乐")
    music.add_argument("--lyrics-optimizer", action="store_true", help="自动生成歌词")
    music.add_argument("--format", default="mp3", choices=["mp3", "wav", "pcm"])
    music.add_argument("--bitrate", type=int, default=256000)
    music.add_argument("--sample-rate", type=int, default=44100)
    music.add_argument("--output", "-o", help="保存路径")
    music.add_argument("--download", action="store_true", help="下载到本地")

    clone_upload = subparsers.add_parser("clone-upload", help="上传克隆音频")
    clone_upload.add_argument("file", help="音频文件路径 (mp3/m4a/wav)")

    clone_upload_prompt = subparsers.add_parser(
        "clone-upload-prompt", help="上传示例音频"
    )
    clone_upload_prompt.add_argument("file", help="示例音频文件路径 (<8s)")

    voice_clone = subparsers.add_parser("voice-clone", help="音色克隆")
    voice_clone.add_argument("file_id", help="克隆音频的 file_id")
    voice_clone.add_argument("voice_id", help="自定义音色 ID")
    voice_clone.add_argument("text", help="克隆文本")
    voice_clone.add_argument("--model", default="speech-2.8-hd", help="克隆模型")
    voice_clone.add_argument("--prompt-file-id", help="示例音频 file_id")
    voice_clone.add_argument("--prompt-text", help="示例音频对应的文本")

    tts_ws = subparsers.add_parser("tts-ws", help="WebSocket 语音合成")
    tts_ws.add_argument("text", help="要转换的文本")
    tts_ws.add_argument("--voice-id", default="male-qn-qingse", help="语音 ID")
    tts_ws.add_argument("--model", default="speech-2.8-hd", help="TTS 模型")
    tts_ws.add_argument("--speed", type=float, default=1.0, help="语速")
    tts_ws.add_argument("--pitch", type=float, default=0, help="音调")
    tts_ws.add_argument("--format", default="mp3", choices=["mp3", "wav", "pcm"])
    tts_ws.add_argument("--bitrate", type=int, default=128000, help="比特率")
    tts_ws.add_argument("--sample-rate", type=int, default=32000, help="采样率")
    tts_ws.add_argument("--output", "-o", help="保存路径")

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
            result = client.voice_clone_upload_file(args.file)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "clone-upload-prompt":
            result = client.voice_clone_upload_prompt(args.file)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "voice-clone":
            result = client.voice_clone(
                file_id=args.file_id,
                voice_id=args.voice_id,
                text=args.text,
                model=args.model,
                prompt_file_id=args.prompt_file_id,
                prompt_text=args.prompt_text,
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "tts-ws":
            import asyncio

            asyncio.run(
                client.tts_websocket(
                    text=args.text,
                    model=args.model,
                    voice_id=args.voice_id,
                    speed=args.speed,
                    pitch=args.pitch,
                    audio_format=args.format,
                    bitrate=args.bitrate,
                    sample_rate=args.sample_rate,
                    output_path=args.output,
                )
            )

        elif args.command == "image":
            result = client.image_generate(args.prompt, aspect_ratio=args.ratio)
            if args.download or args.output:
                _download_image(result, args.output)
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "i2i":
            result = client.image_i2i(args.image, args.prompt, aspect_ratio=args.ratio)
            if args.download or args.output:
                _download_image(result, args.output)
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "video":
            result = client.video_generate(
                prompt=args.prompt,
                model=args.model,
                duration=args.duration,
                resolution=args.resolution,
                prompt_optimizer=not args.no_prompt_optimizer,
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "video-query":
            result = client.video_query(args.task_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "i2v":
            result = client.video_generate(
                prompt=args.prompt,
                model=args.model,
                first_frame_image=args.image,
                duration=args.duration,
                resolution=args.resolution,
                prompt_optimizer=not args.no_prompt_optimizer,
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "fl2v":
            result = client.video_generate(
                prompt=args.prompt,
                model=args.model,
                first_frame_image=args.first_image,
                last_frame_image=args.last_image,
                duration=args.duration,
                resolution=args.resolution,
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "music":
            result = client.music_generate(
                prompt=args.prompt,
                model=args.model,
                lyrics=args.lyrics,
                is_instrumental=args.instrumental,
                lyrics_optimizer=args.lyrics_optimizer,
                audio_format=args.format,
                bitrate=args.bitrate,
                sample_rate=args.sample_rate,
            )
            if args.download or args.output:
                _download_music(result, args.output, args.format)
            else:
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
