#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FunASR GUI启动脚本
提供安全的GUI启动方式，包含错误处理
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """检查依赖项"""
    missing_deps = []

    try:
        import PySide6
        logger.info("✅ PySide6 可用")
    except ImportError:
        missing_deps.append("PySide6")
        logger.error("❌ PySide6 未安装")

    try:
        import torch
        logger.info(f"✅ PyTorch {torch.__version__} 可用")
    except ImportError:
        missing_deps.append("torch")
        logger.error("❌ PyTorch 未安装")

    try:
        import funasr
        logger.info(f"✅ FunASR {funasr.__version__} 可用")
    except ImportError:
        missing_deps.append("funasr")
        logger.error("❌ FunASR 未安装")

    return missing_deps

def install_dependencies(deps):
    """提示用户安装缺失的依赖"""
    if not deps:
        return True

    print("\n❌ 缺少以下依赖包:")
    for dep in deps:
        print(f"   - {dep}")

    print("\n请运行以下命令安装:")
    print(f"pip install {' '.join(deps)}")

    # 如果有PySide6，也建议安装PySide6
    if "PySide6" in deps:
        print("\n或者安装完整的GUI版本:")
        print("pip install PySide6==6.8.2")

    return False

def setup_environment():
    """设置环境变量"""
    # 抑制输出
    os.environ['TQDM_DISABLE'] = '1'
    os.environ['PYTHONWARNINGS'] = 'ignore'
    os.environ['FUNASR_LOG_LEVEL'] = 'ERROR'

    # 设置FFmpeg路径（如果存在）
    ffmpeg_paths = [
        "F:/onnx_deps/ffmpeg-master-latest-win64-gpl-shared/bin",
        "F:/04_AI/01_Workplace/Voice_Input/FunASR_Deployment/dependencies/ffmpeg-master-latest-win64-gpl-shared/bin"
    ]

    current_path = os.environ.get('PATH', '')
    for ffmpeg_path in ffmpeg_paths:
        if os.path.exists(ffmpeg_path) and ffmpeg_path not in current_path:
            os.environ['PATH'] = ffmpeg_path + os.pathsep + current_path
            logger.info(f"设置FFmpeg路径: {ffmpeg_path}")
            break

def start_gui():
    """启动GUI"""
    try:
        from voice_gui import main as gui_main
        logger.info("启动GUI界面...")
        gui_main()
    except ImportError as e:
        logger.error(f"导入GUI模块失败: {e}")
        print(f"❌ 导入GUI模块失败: {e}")
        print("请检查voice_gui.py文件是否存在")
        return False
    except Exception as e:
        logger.error(f"GUI启动失败: {e}")
        print(f"❌ GUI启动失败: {e}")
        return False

    return True

def main():
    """主函数"""
    print("🎤 FunASR语音识别系统 GUI启动器")
    print("=" * 50)

    # 检查依赖
    missing_deps = check_dependencies()

    if missing_deps:
        success = install_dependencies(missing_deps)
        if not success:
            input("\n按回车键退出...")
            return

    # 设置环境
    setup_environment()

    # 启动GUI
    print("\n🚀 启动GUI界面...")
    success = start_gui()

    if not success:
        input("\n按回车键退出...")

if __name__ == "__main__":
    main()