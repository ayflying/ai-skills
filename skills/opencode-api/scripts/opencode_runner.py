#!/usr/bin/env python3
"""
opencode-api 技能核心执行器
负责调用 OpenCode CLI 执行任务并返回结果
"""

import sys
import os
import subprocess
import json
import argparse

def run_opencode(prompt, server_url=None, model=None, session_id=None, title=None):
    """
    执行 OpenCode 任务并返回结果
    """
    # 默认配置
    if server_url is None:
        server_url = os.environ.get("OPENCODE_SERVER_URL", "http://127.0.0.1:9091")
    if model is None:
        model = os.environ.get("OPENCODE_MODEL", "opencode/mimo-v2-omni-free")
    
    opencode_path = os.environ.get("OPencode_CLI_PATH", r"D:\Users\ay\AppData\Local\OpenCode\opencode-cli.exe")
    
    # 构建命令参数
    args = [opencode_path, "run", "--attach", server_url, "--model", model]
    
    if title:
        args.extend(["--title", title])
    
    if session_id:
        args.extend(["-s", session_id])
    
    args.append(prompt)
    
    # 执行命令
    try:
        env = os.environ.copy()
        result = subprocess.run(
            args,
            capture_output=True,
            timeout=120  # 2分钟超时
        )
        
        # 读取原始字节
        output_bytes = result.stdout
        error_bytes = result.stderr
        
        # 尝试用 utf-8 解码，失败则用 gbk，再失败则用 latin-1（不丢数据）
        output = ""
        for encoding in ['utf-8', 'gbk', 'gb18030', 'latin-1']:
            try:
                output = output_bytes.decode(encoding)
                if '�' not in output[:100]:  # 检查前100个字符是否有乱码
                    break
            except:
                pass
        
        error = ""
        for encoding in ['utf-8', 'gbk', 'gb18030', 'latin-1']:
            try:
                error = error_bytes.decode(encoding)
                if '�' not in error[:100]:
                    break
            except:
                pass
        
        # 解析结果
        if result.returncode != 0:
            return {
                "success": False,
                "error": error,
                "output": output
            }
        
        return {
            "success": True,
            "output": output,
            "error": error
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "执行超时（120秒）",
            "output": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "output": ""
        }

def main():
    parser = argparse.ArgumentParser(description="OpenCode API 执行器")
    parser.add_argument("prompt", help="要执行的任务描述")
    parser.add_argument("--server", help="OpenCode 服务器地址", default=None)
    parser.add_argument("--model", help="使用的模型", default=None)
    parser.add_argument("--session", help="会话 ID", default=None)
    parser.add_argument("--title", help="会话标题", default=None)
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    
    args = parser.parse_args()
    
    result = run_opencode(
        prompt=args.prompt,
        server_url=args.server,
        model=args.model,
        session_id=args.session,
        title=args.title
    )
    
    if args.json:
        sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8'))
    else:
        if result["success"]:
            sys.stdout.buffer.write(result["output"].encode('utf-8'))
        else:
            sys.stderr.buffer.write(f"错误: {result['error']}".encode('utf-8'))
            if result["output"]:
                sys.stderr.buffer.write(f"输出: {result['output']}".encode('utf-8'))
            sys.exit(1)

if __name__ == "__main__":
    main()
