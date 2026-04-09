#!/usr/bin/env python3
"""
下载 YouTube 视频和字幕
使用 yt-dlp 命令行下载视频（最高 1080p）和中英文字幕
支持 PO Token 绕过 YouTube 验证
"""

import sys
import json
import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from utils import (
    validate_url,
    sanitize_filename,
    format_file_size,
    get_video_duration_display,
    ensure_directory
)


def check_po_token_server(url: str = "http://127.0.0.1:4416") -> bool:
    """检查 PO Token 服务是否运行"""
    try:
        import urllib.request
        urllib.request.urlopen(url, timeout=2)
        return True
    except:
        return False


def download_video(url: str, output_dir: str = None) -> dict:
    """
    下载 YouTube 视频和字幕

    Args:
        url: YouTube URL
        output_dir: 输出目录，默认为当前目录

    Returns:
        dict: 下载结果信息
    """
    # 验证 URL
    if not validate_url(url):
        raise ValueError(f"Invalid YouTube URL: {url}")

    # 设置输出目录
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    output_dir = ensure_directory(output_dir)

    print(f"🎬 开始下载视频...")
    print(f"   URL: {url}")
    print(f"   输出目录: {output_dir}")

    # 获取环境变量配置
    po_token_enabled = os.getenv('PO_TOKEN_ENABLED', 'true').lower() == 'true'
    po_token_url = os.getenv('PO_TOKEN_PROVIDER_URL', 'http://127.0.0.1:4416')
    cookies_path = os.getenv('YOUTUBE_COOKIES_PATH', '')

    # 检查 PO Token 服务
    use_po_token = False
    if po_token_enabled:
        if check_po_token_server(po_token_url):
            print(f"   ✅ PO Token 服务已启用: {po_token_url}")
            use_po_token = True
        else:
            print(f"   ⚠️  PO Token 服务未运行，尝试其他方式...")

    # 获取视频信息
    print("\n📊 获取视频信息...")
    info_cmd = ['yt-dlp', '--dump-json', url]

    # 添加 PO Token 参数
    if use_po_token:
        info_cmd.extend([
            '--remote-components', 'ejs:github',
            '--extractor-args', 'youtube:player_client=mweb'
        ])

    # 添加 Cookies
    if cookies_path and Path(cookies_path).exists():
        info_cmd.extend(['--cookies', cookies_path])
        print(f"   使用 Cookies: {cookies_path}")

    result = subprocess.run(info_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"获取视频信息失败: {result.stderr}")

    info = json.loads(result.stdout)
    title = info.get('title', 'Unknown')
    duration = info.get('duration', 0)
    video_id = info.get('id', 'unknown')

    print(f"   标题: {title}")
    print(f"   时长: {get_video_duration_display(duration)}")
    print(f"   视频ID: {video_id}")

    # 下载视频和字幕
    print(f"\n📥 开始下载...")
    output_template = str(output_dir / f'{video_id}.%(ext)s')

    download_cmd = [
        'yt-dlp',
        '--format', 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
        '-o', output_template,
        '--write-subs',
        '--write-auto-subs',
        '--sub-langs', 'zh,zh-CN,zh-Hans,zh-TW,zh-Hant,en',
        '--sub-format', 'vtt',
        '--no-write-thumbnail',
        '--progress',
        url
    ]

    # 添加 PO Token 参数
    if use_po_token:
        download_cmd.extend([
            '--remote-components', 'ejs:github',
            '--extractor-args', 'youtube:player_client=mweb'
        ])

    # 添加 Cookies
    if cookies_path and Path(cookies_path).exists():
        download_cmd.extend(['--cookies', cookies_path])

    subprocess.run(download_cmd, check=True)

    # 查找下载的视频文件
    video_path = None
    for ext in ['.mp4', '.webm', '.mkv']:
        potential = output_dir / f'{video_id}{ext}'
        if potential.exists():
            video_path = potential
            break

    if not video_path:
        raise Exception("Video file not found after download")

    # 查找字幕文件（支持中文和英文）
    subtitle_path = None
    for lang in ['.zh', '.zh-CN', '.zh-Hans', '.zh-TW', '.zh-Hant', '.en']:
        potential = output_dir / f'{video_id}{lang}.vtt'
        if potential.exists():
            subtitle_path = potential
            break

    # 获取文件大小
    file_size = video_path.stat().st_size

    print(f"\n✅ 视频下载完成: {video_path.name}")
    print(f"   大小: {format_file_size(file_size)}")

    if subtitle_path and subtitle_path.exists():
        print(f"✅ 字幕下载完成: {subtitle_path.name}")
    else:
        print(f"⚠️  未找到字幕，将使用 Whisper 生成...")
        # 尝试使用 Whisper 生成字幕
        whisper_result = generate_subtitle_with_whisper(str(video_path), output_dir)
        if whisper_result:
            subtitle_path = Path(whisper_result)
            print(f"✅ Whisper 字幕生成完成: {subtitle_path.name}")

    return {
        'video_path': str(video_path),
        'subtitle_path': str(subtitle_path) if subtitle_path else None,
        'title': title,
        'duration': duration,
        'file_size': file_size,
        'video_id': video_id
    }


def generate_subtitle_with_whisper(video_path: str, output_dir: Path) -> str:
    """
    使用 Whisper 生成字幕

    Returns:
        str: 生成的字幕文件路径，失败返回 None
    """
    try:
        # 检查 whisper_gpu.py 是否存在
        whisper_script = Path(__file__).parent / 'whisper_gpu.py'
        if not whisper_script.exists():
            print("   ⚠️  whisper_gpu.py 脚本不存在，跳过自动生成字幕")
            return None

        video_name = Path(video_path).stem
        output_path = output_dir / f'{video_name}.whisper.vtt'

        print(f"   🤖 正在使用 Whisper 生成字幕...")

        result = subprocess.run(
            ['python3', str(whisper_script), video_path, '-o', str(output_path)],
            capture_output=True,
            text=True,
            timeout=600
        )

        if result.returncode == 0 and output_path.exists():
            return str(output_path)
        else:
            print(f"   ⚠️  Whisper 生成失败: {result.stderr}")
            return None

    except Exception as e:
        print(f"   ⚠️  Whisper 生成出错: {e}")
        return None


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("Usage: python download_video.py <youtube_url> [output_dir]")
        print("\nExample:")
        print("  python download_video.py https://youtube.com/watch?v=Ckt1cj0xjRM")
        print("  python download_video.py https://youtube.com/watch?v=Ckt1cj0xjRM ~/Downloads")
        print("\n环境变量:")
        print("  PO_TOKEN_ENABLED - 是否启用 PO Token (默认: true)")
        print("  YOUTUBE_COOKIES_PATH - Cookies 文件路径")
        print("  WHISPER_MODEL - Whisper 模型 (默认: medium)")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = download_video(url, output_dir)
        print("\n" + "="*60)
        print("下载结果 (JSON):")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
