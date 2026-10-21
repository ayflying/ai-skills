#!/usr/bin/env python3
"""
MiniMax API 核心脚本
提供文本生成、语音合成、语音克隆等常用功能
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
import ssl
import sys
import tempfile
from urllib.parse import urlsplit

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

DEFAULT_HOST = "https://api.minimaxi.com"
DOWNLOAD_TIMEOUT = (10, 60)


def _response_json(response):
    """校验 HTTP 和业务状态，并关闭已读取的响应。"""
    try:
        if 300 <= response.status_code < 400:
            raise requests.HTTPError("接口重定向已拒绝，请直接配置可信接口地址", response=response)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError("接口返回格式无效")
        status = result.get("base_resp") or {}
        if status.get("status_code", 0) not in (0, "0"):
            raise ValueError("接口返回业务错误")
        return result
    finally:
        response.close()



class MiniMaxAPI:
    def __init__(self, api_key=None, host=None):
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY")
        self.host = host or os.environ.get("MINIMAX_API_HOST", DEFAULT_HOST)
        if not self.api_key:
            raise ValueError("缺少 MINIMAX_API_KEY，请在本机环境变量或 .env 中配置")

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
            allow_redirects=False,
        )
        return _response_json(response)

    def tts(self, text, model="speech-02-hd", voice_id=None, stream=False):
        """语音合成"""
        data = {"model": model, "text": text, "stream": stream}
        if voice_id:
            data["voice_setting"] = {"voice_id": voice_id}
        response = requests.post(
            f"{self.host}/v1/t2a_v2", headers=self._headers(), json=data, timeout=30, allow_redirects=False
        )
        return _response_json(response)

    def voice_clone_upload_file(self, file_path):
        """上传克隆音频文件 (获取 file_id)"""
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.host}/v1/files/upload",
                headers=self._headers(),
                data={"purpose": "voice_clone"},
                files={"file": f},
                timeout=30,
                allow_redirects=False,
            )
        return _response_json(response)

    def voice_clone_upload_prompt(self, file_path):
        """上传示例音频文件 (增强克隆效果)"""
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.host}/v1/files/upload",
                headers=self._headers(),
                data={"purpose": "prompt_audio"},
                files={"file": f},
                timeout=30,
                allow_redirects=False,
            )
        return _response_json(response)

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
            allow_redirects=False,
        )
        return _response_json(response)

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
        recv_timeout=30,
        total_timeout=300,
    ):
        """WebSocket 语音合成 (流式)"""
        if recv_timeout <= 0 or total_timeout <= 0:
            raise ValueError("超时必须大于 0")

        # 证书库加载是同步操作，先完成后再开始计算网络任务超时。
        ssl_context = ssl.create_default_context()

        async def synthesize():
            import websockets

            url = "wss://api.minimaxi.com/ws/v1/t2a_v2"

            async with websockets.connect(
                url, additional_headers=self._headers(), ssl=ssl_context,
                open_timeout=min(recv_timeout, total_timeout), close_timeout=5
            ) as ws:
                connected = json.loads(await asyncio.wait_for(ws.recv(), timeout=recv_timeout))
                if connected.get("event") != "connected_success":
                    raise ValueError("WebSocket 连接失败")

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

                start_resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=recv_timeout))
                if start_resp.get("event") != "task_started":
                    raise ValueError("语音任务启动失败")

                audio_data = b""
                await ws.send(json.dumps({"event": "task_continue", "text": text}))

                while True:
                    response = json.loads(await asyncio.wait_for(ws.recv(), timeout=recv_timeout))
                    if (response.get("base_resp") or {}).get("status_code", 0) not in (0, "0"):
                        raise ValueError("语音任务返回业务错误")
                    if "data" in response and "audio" in response["data"]:
                        audio_hex = response["data"]["audio"]
                        if audio_hex:
                            audio_data += bytes.fromhex(audio_hex)
                    if response.get("is_final"):
                        break

                await ws.send(json.dumps({"event": "task_finish"}))

                if not audio_data:
                    raise ValueError("语音任务未返回音频")

                if output_path:
                    with open(output_path, "wb") as f:
                        f.write(audio_data)
                    print(f"音频已保存到 {output_path}")

                return audio_data

        return await asyncio.wait_for(synthesize(), timeout=total_timeout)

    def image_generate(self, prompt, model="image-01", aspect_ratio="1:1"):
        """文生图 (Text-to-Image)"""
        response = requests.post(
            f"{self.host}/v1/image_generation",
            headers=self._headers(),
            json={"model": model, "prompt": prompt, "aspect_ratio": aspect_ratio},
            timeout=60,
            allow_redirects=False,
        )
        return _response_json(response)

    def image_i2i(
        self,
        image_path,
        prompt,
        model="image-01-live",
        aspect_ratio="1:1",
        style_type=None,
        style_weight=0.8,
        prompt_optimizer=False,
    ):
        """图生图 (Image-to-Image)

        Args:
            image_path: 参考图片路径
            prompt: 图像描述
            model: 模型 (image-01 或 image-01-live)
            aspect_ratio: 宽高比
            style_type: 画风类型 (漫画/元气/中世纪/水彩)，仅 image-01-live 支持
            style_weight: 画风权重 (0, 1]
            prompt_optimizer: 是否优化 prompt
        """
        import base64

        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()

        data = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "prompt_optimizer": prompt_optimizer,
            "subject_reference": [
                {
                    "type": "character",
                    "image_file": f"data:image/jpeg;base64,{image_base64}",
                }
            ],
        }

        if style_type and model == "image-01-live":
            data["style"] = {
                "style_type": style_type,
                "style_weight": style_weight,
            }

        response = requests.post(
            f"{self.host}/v1/image_generation",
            headers=self._headers(),
            json=data,
            timeout=60,
            allow_redirects=False,
        )
        return _response_json(response)

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
            allow_redirects=False,
        )
        return _response_json(response)

    def video_query(self, task_id):
        """查询视频生成状态"""
        response = requests.get(
            f"{self.host}/v1/video_generation/{task_id}",
            headers=self._headers(),
            timeout=30,
            allow_redirects=False,
        )
        return _response_json(response)

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
            allow_redirects=False,
        )
        return _response_json(response)


def _download_file(url, output_path):
    """仅下载 HTTP(S) 媒体；完整下载后替换目标，失败保留原文件。"""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
        raise ValueError("媒体下载地址无效")
    destination = Path(output_path)
    temporary = None
    try:
        with requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True) as response:
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
                temporary = Path(handle.name)
                size = 0
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        handle.write(chunk)
                        size += len(chunk)
                if not size:
                    raise ValueError("媒体下载内容为空")
            temporary.replace(destination)
            temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"已保存到 {output_path}")


def _download_image(result, output_path=None):
    """下载图片到本地；多图不覆盖同一输出文件。"""
    image_urls = result.get("data", {}).get("image_urls", [])
    if not image_urls:
        raise ValueError("响应中没有图片下载地址")
    for i, url in enumerate(image_urls):
        ext = "png" if urlsplit(url).path.lower().endswith(".png") else "jpg"
        path = Path(output_path or f"output_{i}.{ext}")
        if output_path and len(image_urls) > 1:
            path = path.with_name(f"{path.stem}_{i}{path.suffix}")
        _download_file(url, path)


def _download_music(result, output_path=None, audio_format="mp3"):
    """下载音乐到本地；非 URL 内容显式失败。"""
    data = result.get("data", {})
    audio_url = data.get("audio_url") or data.get("audio")
    if not audio_url:
        raise ValueError("响应中没有音频下载地址")
    _download_file(audio_url, output_path or f"output.{audio_format}")


def main():
    parser = argparse.ArgumentParser(description="MiniMax API 工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令", required=True)

    chat = subparsers.add_parser("chat", help="文本对话")
    chat.add_argument("message", help="对话消息")
    chat.add_argument("--model", default="MiniMax-M2.7-200k", help="模型名称")

    tts = subparsers.add_parser("tts", help="语音合成")
    tts.add_argument("text", help="要转换的文本")
    tts.add_argument("--voice-id", help="语音 ID")
    tts.add_argument("--model", default="speech-02-hd", help="TTS 模型")

    img = subparsers.add_parser("image", help="文生图")
    img.add_argument("prompt", help="图像描述")
    img.add_argument("--ratio", default="1:1", help="宽高比")
    img.add_argument("--output", "-o", help="保存图片路径")
    img.add_argument("--download", action="store_true", help="下载图片到本地")

    i2i = subparsers.add_parser("i2i", help="图生图")
    i2i.add_argument("image", help="参考图像路径")
    i2i.add_argument("prompt", help="图像描述/修改指令")
    i2i.add_argument("--ratio", default="1:1", help="宽高比")
    i2i.add_argument(
        "--model", default="image-01-live", help="模型 (image-01/image-01-live)"
    )
    i2i.add_argument(
        "--style",
        choices=["漫画", "元气", "中世纪", "水彩"],
        help="画风类型 (仅 image-01-live)",
    )
    i2i.add_argument("--style-weight", type=float, default=0.8, help="画风权重 (0-1)")
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

    tts_ws.add_argument("--recv-timeout", type=float, default=30, help="单次接收超时秒数")
    tts_ws.add_argument("--total-timeout", type=float, default=300, help="语音任务总超时秒数")

    args = parser.parse_args()

    try:
        client = MiniMaxAPI()
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
                    recv_timeout=args.recv_timeout,
                    total_timeout=args.total_timeout,
                )
            )

        elif args.command == "image":
            result = client.image_generate(args.prompt, aspect_ratio=args.ratio)
            if args.download or args.output:
                _download_image(result, args.output)
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "i2i":
            result = client.image_i2i(
                image_path=args.image,
                prompt=args.prompt,
                model=args.model,
                aspect_ratio=args.ratio,
                style_type=args.style,
                style_weight=args.style_weight,
            )
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

    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "未知"
        print(f"API 请求失败，HTTP 状态码：{status}；请检查权限和服务状态", file=sys.stderr)
        return 1
    except (requests.exceptions.Timeout, asyncio.TimeoutError):
        print("请求超时，请检查网络或调整超时参数", file=sys.stderr)
        return 1
    except requests.exceptions.RequestException:
        print("网络请求失败，请检查服务地址、证书和连接", file=sys.stderr)
        return 1
    except ImportError:
        print("缺少所需依赖，请按技能说明安装", file=sys.stderr)
        return 1
    except Exception:
        # 不回显第三方异常、响应或签名下载地址，避免凭证泄露。
        if not os.environ.get("MINIMAX_API_KEY"):
            message = "缺少 MINIMAX_API_KEY，请在本机环境变量或 .env 中配置"
        else:
            message = "操作失败，请检查输入、响应格式及输出目录权限"
        print(f"错误：{message}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
