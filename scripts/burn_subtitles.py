#!/usr/bin/env python3
"""
烧录字幕到视频
处理 FFmpeg libass 支持和路径空格问题
"""

import sys
import os
import shutil
import subprocess
import tempfile
import platform
from pathlib import Path
from typing import Dict, Optional

from utils import format_file_size


def detect_ffmpeg_variant() -> Dict:
    """
    检测 FFmpeg 版本和 libass 支持

    Returns:
        Dict: {
            'type': 'full' | 'standard' | 'none',
            'path': FFmpeg 可执行文件路径,
            'has_libass': 是否支持 libass
        }
    """
    print("🔍 检测 FFmpeg 环境...")

    # 优先检查平台特定的 FFmpeg 路径
    system = platform.system()

    if system == 'Darwin':
        # macOS: 优先检查 ffmpeg-full（Apple Silicon 和 Intel）
        full_path_arm = '/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg'
        full_path_intel = '/usr/local/opt/ffmpeg-full/bin/ffmpeg'

        for full_path in [full_path_arm, full_path_intel]:
            if Path(full_path).exists():
                has_libass = check_libass_support(full_path)
                print(f"   找到 ffmpeg-full: {full_path}")
                print(f"   libass 支持: {'✅ 是' if has_libass else '❌ 否'}")
                return {
                    'type': 'full',
                    'path': full_path,
                    'has_libass': has_libass
                }

    elif system == 'Linux':
        # Linux: 检查常见的 FFmpeg 安装路径
        linux_paths = [
            '/usr/bin/ffmpeg',           # 包管理器安装（apt, yum等）
            '/usr/local/bin/ffmpeg',     # 源码编译安装
            '/snap/bin/ffmpeg',          # Snap 安装
            '/opt/ffmpeg/bin/ffmpeg',    # 自定义安装
        ]

        for full_path in linux_paths:
            if Path(full_path).exists():
                has_libass = check_libass_support(full_path)
                variant_type = 'full' if has_libass else 'standard'
                print(f"   找到 FFmpeg: {full_path}")
                print(f"   类型: {variant_type}")
                print(f"   libass 支持: {'✅ 是' if has_libass else '❌ 否'}")
                return {
                    'type': variant_type,
                    'path': full_path,
                    'has_libass': has_libass
                }

    elif system == 'Windows':
        # Windows: 检查常见的 FFmpeg 安装路径
        from pathlib import PureWindowsPath
        import os

        # 获取 Program Files 路径
        program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
        program_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
        localappdata = os.environ.get('LOCALAPPDATA', os.path.expandvars('%LOCALAPPDATA%'))
        userprofile = os.environ.get('USERPROFILE', os.path.expanduser('~'))

        windows_paths = [
            # winget 安装路径 (Gyan's builds)
            f"{program_files}\\ffmpeg\\bin\\ffmpeg.exe",
            f"{program_files_x86}\\ffmpeg\\bin\\ffmpeg.exe",
            # Chocolatey 安装路径
            'C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe',
            # Scoop 安装路径
            f"{userprofile}\\scoop\\shims\\ffmpeg.exe",
            # 手动安装路径
            f"{program_files}\\FFmpeg\\bin\\ffmpeg.exe",
            f"{program_files_x86}\\FFmpeg\\bin\\ffmpeg.exe",
            # 其他常见路径
            'C:\\ffmpeg\\bin\\ffmpeg.exe',
            f"{localappdata}\\ffmpeg\\bin\\ffmpeg.exe",
        ]

        for full_path in windows_paths:
            if Path(full_path).exists():
                has_libass = check_libass_support(full_path)
                variant_type = 'full' if has_libass else 'standard'
                print(f"   找到 FFmpeg: {full_path}")
                print(f"   类型: {variant_type}")
                print(f"   libass 支持: {'✅ 是' if has_libass else '❌ 否'}")
                return {
                    'type': variant_type,
                    'path': full_path,
                    'has_libass': has_libass
                }

    # 检查标准 FFmpeg（PATH 中的）
    standard_path = shutil.which('ffmpeg')
    if standard_path:
        has_libass = check_libass_support(standard_path)
        variant_type = 'full' if has_libass else 'standard'
        print(f"   找到 FFmpeg: {standard_path}")
        print(f"   类型: {variant_type}")
        print(f"   libass 支持: {'✅ 是' if has_libass else '❌ 否'}")
        return {
            'type': variant_type,
            'path': standard_path,
            'has_libass': has_libass
        }

    # 未找到 FFmpeg
    print("   ❌ 未找到 FFmpeg")
    return {
        'type': 'none',
        'path': None,
        'has_libass': False
    }


def check_libass_support(ffmpeg_path: str) -> bool:
    """
    检查 FFmpeg 是否支持 libass（字幕烧录必需）

    Args:
        ffmpeg_path: FFmpeg 可执行文件路径

    Returns:
        bool: 是否支持 libass
    """
    try:
        # 检查是否有 subtitles 滤镜
        result = subprocess.run(
            [ffmpeg_path, '-filters'],
            capture_output=True,
            text=True,
            timeout=5
        )

        # 查找 subtitles 滤镜
        return 'subtitles' in result.stdout.lower()

    except Exception:
        return False


def install_ffmpeg_full_guide():
    """
    显示安装 ffmpeg-full 的指南
    """
    print("\n" + "="*60)
    print("⚠️  需要安装支持 libass 的 FFmpeg 才能烧录字幕")
    print("="*60)

    system = platform.system()

    if system == 'Darwin':
        print("\nmacOS 安装方法:")
        print("  brew install ffmpeg-full")
        print("\n安装后，FFmpeg 路径:")
        print("  /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg  (Apple Silicon)")
        print("  /usr/local/opt/ffmpeg-full/bin/ffmpeg     (Intel)")

    elif system == 'Linux':
        print("\nLinux 安装方法:")
        print("  # Ubuntu/Debian")
        print("  sudo apt-get update")
        print("  sudo apt-get install ffmpeg libass-dev")
        print("")
        print("  # CentOS/RHEL/Fedora")
        print("  sudo dnf install ffmpeg libass")
        print("")
        print("  # Arch Linux")
        print("  sudo pacman -S ffmpeg libass")
        print("\n如果包管理器的 FFmpeg 不支持 libass，请编译安装:")
        print("  参考: https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu")

    elif system == 'Windows':
        print("\nWindows 安装方法:")
        print("  # 方法 1: 使用 winget (推荐)")
        print("  winget install ffmpeg")
        print("  # 或使用 Gyan's full build (包含 libass):")
        print("  winget install ffmpeg")
        print("")
        print("  # 方法 2: 使用 Chocolatey")
        print("  choco install ffmpeg-full")
        print("")
        print("  # 方法 3: 使用 Scoop")
        print("  scoop install ffmpeg")
        print("")
        print("  # 方法 4: 手动安装")
        print("  1. 下载: https://www.gyan.dev/ffmpeg/builds/")
        print("     选择 'release-full' 或 'release-full-shared'")
        print("  2. 解压到 C:\\ffmpeg")
        print("  3. 将 C:\\ffmpeg\\bin 添加到系统 PATH")
        print("")
        print("验证安装:")
        print("  ffmpeg -filters | findstr subtitles")

    else:
        print("\n其他系统:")
        print("  请从源码编译 FFmpeg，确保包含 libass 支持")
        print("  参考: https://trac.ffmpeg.org/wiki/CompilationGuide")

    print("\n验证安装:")
    print("  ffmpeg -filters 2>&1 | grep subtitles")
    print("="*60)


def burn_subtitles(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    ffmpeg_path: str = None,
    font_size: int = 24,
    margin_v: int = 30
) -> str:
    """
    烧录字幕到视频（使用临时目录解决路径空格问题）

    Args:
        video_path: 输入视频路径
        subtitle_path: 字幕文件路径（SRT 格式）
        output_path: 输出视频路径
        ffmpeg_path: FFmpeg 可执行文件路径（可选）
        font_size: 字体大小，默认 24
        margin_v: 底部边距，默认 30

    Returns:
        str: 输出视频路径

    Raises:
        FileNotFoundError: 输入文件不存在
        RuntimeError: FFmpeg 执行失败
    """
    video_path = Path(video_path)
    subtitle_path = Path(subtitle_path)
    output_path = Path(output_path)

    # 验证输入文件
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not subtitle_path.exists():
        raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")

    # 检测 FFmpeg
    if ffmpeg_path is None:
        ffmpeg_info = detect_ffmpeg_variant()

        if ffmpeg_info['type'] == 'none':
            install_ffmpeg_full_guide()
            raise RuntimeError("FFmpeg not found")

        if not ffmpeg_info['has_libass']:
            install_ffmpeg_full_guide()
            raise RuntimeError("FFmpeg does not support libass (subtitles filter)")

        ffmpeg_path = ffmpeg_info['path']

    print(f"\n🎬 烧录字幕到视频...")
    print(f"   视频: {video_path.name}")
    print(f"   字幕: {subtitle_path.name}")
    print(f"   输出: {output_path.name}")
    print(f"   FFmpeg: {ffmpeg_path}")

    # 创建临时目录（解决路径空格问题）
    temp_dir = tempfile.mkdtemp(prefix='youtube_clipper_')
    print(f"   使用临时目录: {temp_dir}")

    try:
        # 复制文件到临时目录（路径无空格）
        temp_video = os.path.join(temp_dir, 'video.mp4')
        temp_subtitle = os.path.join(temp_dir, 'subtitle.srt')
        temp_output = os.path.join(temp_dir, 'output.mp4')

        print(f"   复制文件到临时目录...")
        shutil.copy(video_path, temp_video)
        shutil.copy(subtitle_path, temp_subtitle)

        # 构建 FFmpeg 命令
        # 使用 subtitles 滤镜烧录字幕
        subtitle_filter = f"subtitles={temp_subtitle}:force_style='FontSize={font_size},MarginV={margin_v}'"

        cmd = [
            ffmpeg_path,
            '-i', temp_video,
            '-vf', subtitle_filter,
            '-c:a', 'copy',  # 音频直接复制，不重新编码
            '-y',  # 覆盖输出文件
            temp_output
        ]

        print(f"   执行 FFmpeg...")
        print(f"   命令: {' '.join(cmd)}")

        # 执行 FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"\n❌ FFmpeg 执行失败:")
            print(result.stderr)
            raise RuntimeError(f"FFmpeg failed with return code {result.returncode}")

        # 验证输出文件
        if not Path(temp_output).exists():
            raise RuntimeError("Output file not created")

        # 移动输出文件到目标位置
        print(f"   移动输出文件...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(temp_output, output_path)

        # 获取文件大小
        output_size = output_path.stat().st_size
        print(f"✅ 字幕烧录完成")
        print(f"   输出文件: {output_path}")
        print(f"   文件大小: {format_file_size(output_size)}")

        return str(output_path)

    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"   清理临时目录")
        except Exception:
            pass


def main():
    """命令行入口"""
    if len(sys.argv) < 4:
        print("Usage: python burn_subtitles.py <video> <subtitle> <output> [font_size] [margin_v]")
        print("\nArguments:")
        print("  video      - 输入视频文件路径")
        print("  subtitle   - 字幕文件路径（SRT 格式）")
        print("  output     - 输出视频文件路径")
        print("  font_size  - 字体大小，默认 24")
        print("  margin_v   - 底部边距，默认 30")
        print("\nExample:")
        print("  python burn_subtitles.py input.mp4 subtitle.srt output.mp4")
        print("  python burn_subtitles.py input.mp4 subtitle.srt output.mp4 28 40")
        sys.exit(1)

    video_path = sys.argv[1]
    subtitle_path = sys.argv[2]
    output_path = sys.argv[3]
    font_size = int(sys.argv[4]) if len(sys.argv) > 4 else 24
    margin_v = int(sys.argv[5]) if len(sys.argv) > 5 else 30

    try:
        result_path = burn_subtitles(
            video_path,
            subtitle_path,
            output_path,
            font_size=font_size,
            margin_v=margin_v
        )

        print(f"\n✨ 完成！输出文件: {result_path}")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
