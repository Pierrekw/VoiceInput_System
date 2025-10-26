#!/usr/bin/env python3
"""
VoiceInput v2.5 优化打包脚本
快速打包，排除不必要的ML依赖
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_dependencies():
    """检查打包依赖"""
    print("🔍 检查打包依赖...")

    required_packages = ["pyinstaller"]
    missing_packages = []

    for package in required_packages:
        try:
            subprocess.run([sys.executable, "-m", package, "--version"],
                         check=True, capture_output=True)
            print(f"✅ {package} 已安装")
        except subprocess.CalledProcessError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("正在安装依赖包...")

        for package in missing_packages:
            print(f"📦 安装 {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

    print("✅ 依赖检查完成")

def clean_build():
    """清理之前的构建文件"""
    print("🧹 清理构建文件...")

    dirs_to_clean = ["build", "dist", "__pycache__", "*.spec"]

    for pattern in dirs_to_clean:
        if pattern.startswith("*"):
            for item in Path(".").glob(pattern):
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        else:
            dir_path = Path(pattern)
            if dir_path.exists():
                shutil.rmtree(dir_path)

    print("✅ 构建文件清理完成")

def build_exe_optimized():
    """优化构建exe文件"""
    print("🚀 开始优化构建exe文件...")

    # 优化的PyInstaller命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=VoiceInput_v2.5",
        "--windowed",  # GUI应用
        "--onedir",    # 目录模式
        "--add-data=config.yaml:.",
        "--add-data=voice_correction_dict.txt:.",
        # 隐藏导入 - 只包含核心必需的
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=openpyxl",
        "--hidden-import=pyyaml",
        "--hidden-import=cn2an",
        # 排除大量不必要的模块
        "--exclude-module=model",
        "--exclude-module=modelscope",
        "--exclude-module=onnx_deps",
        "--exclude-module=tests",
        "--exclude-module=debug",
        "--exclude-module=logs",
        "--exclude-module=reports",
        "--exclude-module=torch",
        "--exclude-module=funasr",
        "--exclude-module=onnxruntime",
        "--exclude-module=sklearn",
        "--exclude-module=scipy",
        "--exclude-module=matplotlib",
        "--exclude-module=jupyter",
        "--exclude-module=IPython",
        "--exclude-module=pandas",
        "--exclude-module=numba",
        "--exclude-module=llvmlite",
        "--exclude-module=tkinter",
        "--exclude-module=sqlite3",
        "--exclude-module=xml",
        "--exclude-module=urllib3",
        "--exclude-module=cryptography",
        "--exclude-module=aliyunsdkcore",
        "--exclude-module=huggingface_hub",
        "--exclude-module=transformers",
        "--exclude-module=datasets",
        "--exclude-module=tokenizers",
        "--exclude-module=sentencepiece",
        "--exclude-module=protobuf",
        "--exclude-module=grpcio",
        "--exclude-module=absl",
        # 运行时钩子
        "--runtime-hook=hooks/pyi_rthook_optimized.py",
        # 主程序
        "voice_gui.py"
    ]

    print("执行优化命令:", " ".join(cmd))

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("警告信息:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        if e.stdout:
            print("输出:", e.stdout)
        if e.stderr:
            print("错误:", e.stderr)
        return False

    return True

def create_distribution():
    """创建发布包"""
    print("📦 创建发布包...")

    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("❌ 构建目录不存在")
        return False

    # 找到构建目录
    build_dirs = [d for d in dist_dir.iterdir() if d.is_dir() and d.name.startswith("VoiceInput")]
    if not build_dirs:
        print("❌ 找不到构建目录")
        return False

    build_dir = build_dirs[0]

    # 创建发布目录
    release_dir = Path(f"release/VoiceInput_v2.5_Lite")
    release_dir.mkdir(parents=True, exist_ok=True)

    # 复制构建文件
    print(f"📋 复制构建文件到 {release_dir}")
    shutil.copytree(build_dir, release_dir / build_dir.name, dirs_exist_ok=True)

    # 复制配置文件
    config_files = ["config.yaml", "voice_correction_dict.txt", "README.md", "requirements.txt"]
    for file_name in config_files:
        src = Path(file_name)
        if src.exists():
            dst = release_dir / file_name
            shutil.copy2(src, dst)
            print(f"  📄 复制: {file_name}")

    # 创建说明文件
    readme = release_dir / "部署说明.txt"
    with open(readme, 'w', encoding='utf-8') as f:
        f.write("""VoiceInput v2.5 Lite 部署说明
==================================

⚠️  重要提示：
此版本为轻量版，不包含AI模型文件。
如需完整功能，请配置以下环境：

1. 模型文件配置：
   - 将 model/fun 文件夹放置在程序同目录下
   - 模型文件包含：FunASR语音识别模型等

2. Python环境配置（如需要本地开发）：
   - Python 3.11+
   - 安装 requirements.txt 中的依赖

3. 启动程序：
   - 双击 VoiceInput_v2.5.exe 启动
   - 首次运行会检查环境完整性

4. 注意事项：
   - 此版本体积小，适合快速部署
   - 完整功能需要配置模型文件
   - 如有问题，请检查模型文件完整性

版本：v2.5 Lite
更新日期：2025-10-26
""")

    print(f"✅ 发布包创建完成: {release_dir}")

    # 显示大小信息
    build_size = sum(f.stat().st_size for f in build_dir.rglob('*') if f.is_file())
    release_size = sum(f.stat().st_size for f in release_dir.rglob('*') if f.is_file())

    print(f"📊 构建目录大小: {build_size / (1024*1024):.1f} MB")
    print(f"📊 发布包大小: {release_size / (1024*1024):.1f} MB")

    return True

def main():
    """主函数"""
    print("🚀 VoiceInput v2.5 Lite 优化打包工具")
    print("=" * 50)

    try:
        # 1. 检查依赖
        check_dependencies()

        # 2. 清理构建文件
        clean_build()

        # 3. 构建exe文件
        if not build_exe_optimized():
            print("❌ 构建失败")
            return False

        # 4. 创建发布包
        if not create_distribution():
            print("❌ 发布包创建失败")
            return False

        print("\n🎉 轻量版打包完成！")
        print("=" * 50)
        print("📁 输出文件:")
        print("  📦 release/VoiceInput_v2.5_Lite/ - 轻量版程序包")
        print("\n📋 部署说明:")
        print("1. 将整个 release/VoiceInput_v2.5_Lite/ 文件夹复制到目标计算机")
        print("2. 根据需要配置模型文件到 model/ 目录")
        print("3. 双击 VoiceInput_v2.5.exe 启动程序")
        print("4. 首次运行会检查环境和文件完整性")

        return True

    except KeyboardInterrupt:
        print("\n❌ 用户中断打包过程")
        return False
    except Exception as e:
        print(f"❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)