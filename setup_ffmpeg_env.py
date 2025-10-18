#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFmpeg环境设置脚本
必须在导入FunASR之前运行，用于设置FFmpeg路径环境变量

使用方法:
    import setup_ffmpeg_env  # 在导入funasr之前
    from funasr import AutoModel  # 然后安全导入FunASR
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_ffmpeg():
    """
    设置FFmpeg环境变量

    Returns:
        bool: 是否成功找到并设置FFmpeg
    """
    print("🔧 设置FFmpeg环境...")

    try:
        # 获取当前脚本所在目录的父目录（Voice_Input目录）
        current_dir = Path(__file__).parent
        project_root = current_dir

        # 定义可能的FFmpeg路径
        ffmpeg_paths = [
            # 1. 项目内的FunASR_Deployment目录
            project_root / "FunASR_Deployment" / "dependencies" / "ffmpeg-master-latest-win64-gpl-shared" / "bin",

            # 2. F盘根目录
            Path("F:/onnx_deps/ffmpeg-master-latest-win64-gpl-shared/bin"),

            # 3. 常见安装位置
            Path("C:/ffmpeg/bin"),
            Path("C:/Program Files/ffmpeg/bin"),
            Path("D:/ffmpeg/bin"),

            # 4. 系统PATH（最后检查）
        ]

        ffmpeg_found = False
        ffmpeg_path_used = ""

        for ffmpeg_path in ffmpeg_paths:
            if ffmpeg_path is None:  # 系统PATH检查
                # 检查系统PATH中是否已有FFmpeg
                try:
                    result = subprocess.run(['ffmpeg', '-version'],
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        print("✅ 系统PATH中已存在FFmpeg")
                        ffmpeg_found = True
                        ffmpeg_path_used = "系统PATH"
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
                except Exception as e:
                    print(f"⚠️ 检查系统FFmpeg时出错: {e}")
                    continue
            else:
                # 检查具体路径
                if ffmpeg_path.exists():
                    ffmpeg_exe = ffmpeg_path / "ffmpeg.exe"
                    if ffmpeg_exe.exists():
                        # 添加到PATH环境变量
                        path_str = str(ffmpeg_path)
                        current_path = os.environ.get('PATH', '')

                        if path_str not in current_path:
                            os.environ['PATH'] = path_str + os.pathsep + current_path
                            print(f"✅ 已添加FFmpeg到PATH: {path_str}")

                        ffmpeg_found = True
                        ffmpeg_path_used = str(ffmpeg_path)
                        break

        if ffmpeg_found:
            print(f"🎯 FFmpeg环境设置成功 (来源: {ffmpeg_path_used})")

            # 验证FFmpeg是否真正可用
            try:
                result = subprocess.run(['ffmpeg', '-version'],
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    print(f"📋 FFmpeg版本: {version_line}")
                    return True
                else:
                    print("⚠️ FFmpeg添加到PATH但无法执行")
                    return False
            except Exception as e:
                print(f"⚠️ FFmpeg验证失败: {e}")
                return False
        else:
            print("❌ 未找到FFmpeg")
            print("\n💡 解决方案:")
            print("1. 下载FFmpeg并解压到 FunASR_Deployment/dependencies/ 目录")
            print("2. 或者安装FFmpeg到系统PATH")
            print("3. 或者将FFmpeg放置在 F:/onnx_deps/ffmpeg-master-latest-win64-gpl-shared/bin/")

            print("\n📦 推荐下载地址:")
            print("https://ffmpeg.org/download.html")
            print("https://www.gyan.dev/ffmpeg/builds/")

            return False

    except Exception as e:
        print(f"❌ FFmpeg环境设置失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_ffmpeg_status():
    """检查FFmpeg状态"""
    print("🔍 检查FFmpeg状态...")

    try:
        # 检查PATH中是否有FFmpeg
        result = subprocess.run(['ffmpeg', '-version'],
                              capture_output=True, text=True, timeout=3)

        if result.returncode == 0:
            lines = result.stdout.split('\n')
            version = lines[0] if lines else "未知版本"
            print(f"✅ FFmpeg可用: {version}")

            # 检查PATH环境变量
            path_dirs = os.environ.get('PATH', '').split(os.pathsep)
            ffmpeg_dirs = [d for d in path_dirs if 'ffmpeg' in d.lower()]

            if ffmpeg_dirs:
                print(f"📂 PATH中的FFmpeg目录: {ffmpeg_dirs}")

            return True
        else:
            print("❌ FFmpeg不可用")
            return False

    except FileNotFoundError:
        print("❌ FFmpeg未找到")
        return False
    except Exception as e:
        print(f"❌ 检查FFmpeg状态时出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 FFmpeg环境设置工具")
    print("必须在导入FunASR之前运行")
    print("=" * 60)

    # 检查当前状态
    print("\n1️⃣ 检查当前FFmpeg状态...")
    current_status = check_ffmpeg_status()

    if current_status:
        print("\n✅ FFmpeg环境已就绪，无需额外设置")
        return True

    # 设置FFmpeg环境
    print("\n2️⃣ 设置FFmpeg环境...")
    success = setup_ffmpeg()

    if success:
        print("\n3️⃣ 最终验证...")
        final_check = check_ffmpeg_status()

        if final_check:
            print("\n🎉 FFmpeg环境设置完成！")
            print("现在可以安全导入FunASR了")
        else:
            print("\n⚠️ FFmpeg设置后验证失败")
    else:
        print("\n❌ FFmpeg环境设置失败")
        print("请手动安装FFmpeg或检查路径")

    return success

# 立即执行设置（当作为模块导入时）
if __name__ != "__main__":
    # 作为模块导入时自动执行设置
    setup_ffmpeg()
else:
    # 作为脚本运行时显示详细信息
    main()