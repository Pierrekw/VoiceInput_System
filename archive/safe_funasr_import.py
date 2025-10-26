#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全的FunASR导入脚本
确保按照正确的顺序设置环境并导入FunASR

使用方法:
    from safe_funasr_import import safe_import_funasr

    # 安全导入FunASR
    AutoModel = safe_import_funasr()

    # 或者直接使用预导入的模块
    from safe_funasr_import import AutoModel
"""

import sys
import os
from pathlib import Path

def safe_import_funasr():
    """
    安全导入FunASR，确保所有环境都正确设置

    Returns:
        AutoModel类或None（如果导入失败）
    """
    print("🔒 开始安全导入FunASR...")

    try:
        # 步骤1: 设置FFmpeg环境
        print("📦 步骤1: 设置FFmpeg环境...")
        from .setup_ffmpeg_env import setup_ffmpeg
        if not setup_ffmpeg():
            print("❌ FFmpeg环境设置失败，但继续尝试导入FunASR")
        else:
            print("✅ FFmpeg环境设置完成")

        # 步骤2: 设置ONNX Runtime环境
        print("📦 步骤2: 检查ONNX Runtime...")
        try:
            import onnxruntime as ort
            print(f"✅ ONNX Runtime可用 (版本: {ort.__version__})")
            providers = ort.get_available_providers()
            print(f"📋 可用执行提供者: {', '.join(providers)}")
        except ImportError:
            print("⚠️ ONNX Runtime不可用，将使用默认CPU模式")
        except Exception as e:
            print(f"⚠️ ONNX Runtime检查异常: {e}")

        # 步骤3: 导入FunASR
        print("📦 步骤3: 导入FunASR...")
        try:
            from funasr import AutoModel
            print("✅ FunASR导入成功")
            return AutoModel
        except ImportError as e:
            print(f"❌ FunASR导入失败: {e}")
            print("\n💡 可能的解决方案:")
            print("1. 安装FunASR: pip install funasr")
            print("2. 检查网络连接")
            print("3. 重启Python环境")
            return None
        except Exception as e:
            print(f"❌ FunASR导入异常: {e}")
            import traceback
            traceback.print_exc()
            return None

    except Exception as e:
        print(f"❌ 安全导入过程出错: {e}")
        import traceback
        traceback.print_exc()
        return None

# 预导入（当模块被导入时自动执行）
print("🔄 执行预导入检查...")

# 立即设置FFmpeg环境
from .setup_ffmpeg_env import setup_ffmpeg
setup_ffmpeg()

# 尝试预导入FunASR
AutoModel = safe_import_funasr()

if AutoModel is not None:
    print("🎉 FunASR预导入成功！模块已准备就绪")
else:
    print("⚠️ FunASR预导入失败，但模块仍可尝试手动导入")

def verify_funasr_environment():
    """验证FunASR运行环境"""
    print("🔍 验证FunASR运行环境...")

    checks = {
        "FFmpeg": False,
        "NumPy": False,
        "PyAudio": False,
        "FunASR": False,
        "ONNX Runtime": False
    }

    # 检查FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'],
                              capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            checks["FFmpeg"] = True
            print("✅ FFmpeg: 可用")
        else:
            print("❌ FFmpeg: 不可用")
    except:
        print("❌ FFmpeg: 未找到")

    # 检查NumPy
    try:
        import numpy as np
        checks["NumPy"] = True
        print(f"✅ NumPy: 可用 (版本: {np.__version__})")
    except ImportError:
        print("❌ NumPy: 不可用")

    # 检查PyAudio
    try:
        import pyaudio
        checks["PyAudio"] = True
        print(f"✅ PyAudio: 可用")
    except ImportError:
        print("❌ PyAudio: 不可用")

    # 检查FunASR
    try:
        from funasr import AutoModel
        checks["FunASR"] = True
        print("✅ FunASR: 可用")
    except ImportError:
        print("❌ FunASR: 不可用")

    # 检查ONNX Runtime
    try:
        import onnxruntime as ort
        checks["ONNX Runtime"] = True
        print(f"✅ ONNX Runtime: 可用 (版本: {ort.__version__})")
    except ImportError:
        print("⚠️ ONNX Runtime: 不可用")

    # 统计结果
    passed = sum(checks.values())
    total = len(checks)

    print(f"\n📊 环境检查结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有依赖都已就绪！")
        return True
    else:
        missing = [name for name, status in checks.items() if not status]
        print(f"⚠️ 缺少依赖: {', '.join(missing)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🛡️ 安全FunASR导入工具")
    print("=" * 60)

    # 验证环境
    success = verify_funasr_environment()

    if success:
        print("\n🎯 环境验证通过，可以安全使用FunASR")
    else:
        print("\n⚠️ 环境验证失败，请检查缺失的依赖")

    print("\n💡 使用示例:")
    print("from safe_funasr_import import AutoModel, verify_funasr_environment")
    print("verify_funasr_environment()")
    print("model = AutoModel(model='your_model_path')")