#!/usr/bin/env python3
"""
智能 GPU 选择 Whisper 转录脚本
- 支持参数指定 GPU
- 自动检测显存，少于 4GB 则切换至最优 GPU
- 支持 .env 配置文件
- CPU 兜底
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple, List

# 尝试加载 python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_gpu_info() -> List[dict]:
    """获取所有 GPU 信息"""
    try:
        # 使用 CSV 格式更可靠
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.free', '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            gpus = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split(', ')
                    if len(parts) >= 4:
                        gpus.append({
                            'index': int(parts[0]),
                            'name': parts[1],
                            'memory_total_mb': int(parts[2]),
                            'memory_free_mb': int(parts[3])
                        })
            return gpus
    except Exception as e:
        print(f"检测 GPU 失败: {e}")
    return []


def select_best_gpu(preferred_gpu: Optional[int] = None, min_memory_mb: int = 4096) -> Tuple[str, int]:
    """
    选择最优 GPU

    返回: (device, gpu_index)
    - device: 'cuda' 或 'cpu'
    - gpu_index: GPU 索引（-1 表示 CPU）
    """
    gpus = get_gpu_info()

    if not gpus:
        print("未检测到 GPU，使用 CPU")
        return 'cpu', -1

    print(f"检测到 {len(gpus)} 个 GPU:")
    for gpu in gpus:
        print(f"  GPU {gpu['index']}: {gpu['name']}, "
              f"总显存: {gpu['memory_total_mb']}MB, "
              f"空闲: {gpu['memory_free_mb']}MB")

    # 如果指定了 GPU，检查其显存
    if preferred_gpu is not None:
        matching_gpu = None
        for gpu in gpus:
            if gpu['index'] == preferred_gpu:
                matching_gpu = gpu
                break

        if matching_gpu:
            free_mb = matching_gpu['memory_free_mb']
            print(f"\n指定使用 GPU {preferred_gpu}, 空闲显存: {free_mb}MB")

            if free_mb >= min_memory_mb:
                print(f"显存充足 (>= {min_memory_mb}MB)，使用 GPU {preferred_gpu}")
                return 'cuda', preferred_gpu
            else:
                print(f"⚠️  GPU {preferred_gpu} 显存不足 ({free_mb}MB < {min_memory_mb}MB)，切换至最优 GPU")
        else:
            print(f"⚠️  GPU {preferred_gpu} 不存在，自动选择最优 GPU")

    # 选择显存最多的 GPU
    best_gpu = max(gpus, key=lambda g: g['memory_free_mb'])
    best_index = best_gpu['index']
    best_free = best_gpu['memory_free_mb']

    if best_free >= min_memory_mb:
        print(f"选择最优 GPU {best_index} ({best_gpu['name']}), 空闲显存: {best_free}MB")
        return 'cuda', best_index
    else:
        print(f"⚠️  所有 GPU 显存都不足 ({best_free}MB < {min_memory_mb}MB)，使用 CPU")
        return 'cpu', -1


def check_and_install_whisper() -> bool:
    """检查并自动安装 faster-whisper"""
    try:
        from faster_whisper import WhisperModel
        return True
    except ImportError:
        print("⚠️  faster_whisper 未安装，尝试自动安装...")
        import subprocess
        try:
            # 尝试使用 pip3 或 pip 安装
            for pip_cmd in ['pip3', 'pip']:
                try:
                    result = subprocess.run(
                        [pip_cmd, 'install', '-q', 'faster-whisper'],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result.returncode == 0:
                        print("✅ faster-whisper 安装成功")
                        # 验证安装
                        try:
                            from faster_whisper import WhisperModel
                            print("✅ faster-whisper 验证通过")
                            return True
                        except ImportError:
                            print("⚠️  安装后验证失败")
                            return False
                    break  # pip 命令存在但安装失败，不再尝试其他 pip
                except FileNotFoundError:
                    continue  # 尝试下一个 pip 命令
            print("❌ faster-whisper 安装失败")
            print("请手动运行: pip3 install faster-whisper")
            return False
        except Exception as e:
            print(f"❌ 安装过程中出错: {e}")
            return False


def transcribe(video_path: str, output_path: str, device: str, gpu_index: int,
               model_size: str = 'medium', language: str = 'zh') -> bool:
    """执行转录"""
    # 首先检查并安装 faster-whisper
    if not check_and_install_whisper():
        return False

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("❌ faster_whisper 导入失败")
        return False

    # 设置 GPU 环境变量
    if gpu_index >= 0:
        os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_index)
        print(f"\n设置 CUDA_VISIBLE_DEVICES={gpu_index}")

    print(f"\n加载模型: {model_size}, 设备: {device}")

    try:
        # 加载模型
        if device == 'cpu':
            model = WhisperModel(model_size, device='cpu', compute_type='int8')
        else:
            model = WhisperModel(model_size, device='cuda', compute_type='float16')

        print(f"开始转录: {video_path}")
        import time
        start = time.time()

        segments, info = model.transcribe(video_path, language=language, beam_size=5)

        # 写入 VTT 文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('WEBVTT\n\n')
            for seg in segments:
                s_h = int(seg.start // 3600)
                s_m = int((seg.start % 3600) // 60)
                s_s = seg.start % 60
                e_h = int(seg.end // 3600)
                e_m = int((seg.end % 3600) // 60)
                e_s = seg.end % 60
                f.write(f'{s_h:02d}:{s_m:02d}:{s_s:03.3f} --> {e_h:02d}:{e_m:02d}:{e_s:03.3f}\n')
                f.write(f'{seg.text.strip()}\n\n')

        elapsed = time.time() - start
        print(f"\n✅ 转录完成！")
        print(f"   用时: {elapsed:.2f}秒")
        print(f"   输出: {output_path}")
        return True

    except Exception as e:
        print(f"❌ 转录失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='智能 GPU 选择 Whisper 转录',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python whisper_gpu.py video.mp4                    # 自动选择最优 GPU
  python whisper_gpu.py video.mp4 --gpu 0            # 指定 GPU 0
  python whisper_gpu.py video.mp4 --model large      # 使用 large 模型
  python whisper_gpu.py video.mp4 --output sub.vtt   # 指定输出文件

环境变量 (.env):
  WHISPER_MODEL=medium      # 默认模型
  WHISPER_LANGUAGE=zh       # 默认语言
  WHISPER_MIN_MEMORY=4096   # 最小显存要求 (MB)
        """
    )

    parser.add_argument('video', help='输入视频文件路径')
    parser.add_argument('-o', '--output', help='输出字幕文件路径 (默认: 视频名.vtt)')
    parser.add_argument('-g', '--gpu', type=int, help='指定 GPU 索引 (如: 0, 1)')
    parser.add_argument('-m', '--model', default=os.getenv('WHISPER_MODEL', 'medium'),
                       choices=['tiny', 'base', 'small', 'medium', 'large'],
                       help='Whisper 模型大小 (默认: medium)')
    parser.add_argument('-l', '--language', default=os.getenv('WHISPER_LANGUAGE', 'zh'),
                       help='识别语言 (默认: zh)')
    parser.add_argument('--min-memory', type=int,
                       default=int(os.getenv('WHISPER_MIN_MEMORY', '4096')),
                       help='最小显存要求 MB，不足则切换 GPU (默认: 4096)')
    parser.add_argument('--cpu', action='store_true', help='强制使用 CPU')

    args = parser.parse_args()

    # 检查视频文件
    if not os.path.exists(args.video):
        print(f"❌ 视频文件不存在: {args.video}")
        sys.exit(1)

    # 确定输出路径
    if args.output:
        output_path = args.output
    else:
        video_name = Path(args.video).stem
        output_path = f"{video_name}.vtt"

    print(f"🎬 输入视频: {args.video}")
    print(f"📝 输出字幕: {output_path}")
    print(f"🤖 模型: {args.model}")
    print(f"🌐 语言: {args.language}")
    print(f"💾 最小显存要求: {args.min_memory}MB\n")

    # 选择设备
    if args.cpu:
        device, gpu_index = 'cpu', -1
        print("强制使用 CPU")
    else:
        device, gpu_index = select_best_gpu(args.gpu, args.min_memory)

    # 执行转录
    success = transcribe(args.video, output_path, device, gpu_index,
                        args.model, args.language)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
