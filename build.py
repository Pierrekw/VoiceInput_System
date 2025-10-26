#!/usr/bin/env python3
"""
VoiceInput v2.5 打包脚本
支持打包成exe文件，将大文件单独处理
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_dependencies():
    """检查打包依赖"""
    print("🔍 检查打包依赖...")

    required_packages = ["pyinstaller", "setuptools"]
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

def prepare_build():
    """准备构建环境"""
    print("📦 准备构建环境...")

    # 确保必要目录存在
    required_dirs = ["logs", "reports", "reports/templates"]
    for dir_path in required_dirs:
        Path(dir_path).mkdir(exist_ok=True)

    print("✅ 构建环境准备完成")

def build_exe():
    """构建exe文件"""
    print("🚀 开始构建exe文件...")

    # PyInstaller命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=VoiceInput_v2.5",
        "--windowed",  # GUI应用
        "--onedir",    # 目录模式
        "--add-data=config.yaml:.",
        "--add-data=voice_correction_dict.txt:.",
        "--add-data=reports/templates:reports/templates",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=funasr",
        "--hidden-import=onnxruntime",
        "--hidden-import=torch",
        "--hidden-import=numpy",
        "--hidden-import=openpyxl",
        "--hidden-import=pyyaml",
        "--hidden-import=cn2an",
        "--exclude-module=model",
        "--exclude-module=onnx_deps",
        "--exclude-module=tests",
        "--exclude-module=debug",
        "--exclude-module=logs",
        "--exclude-module=reports/templates/*.xlsx",
        "--runtime-hook=hooks/pyi_rthook.py",
        "voice_gui.py"
    ]

    print("执行命令:", " ".join(cmd))

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
    release_dir = Path(f"release/VoiceInput_v2.5")
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

    # 创建模型文件说明
    model_readme = release_dir / "MODEL_SETUP.txt"
    with open(model_readme, 'w', encoding='utf-8') as f:
        f.write("""模型文件设置说明
===============

1. 模型文件目录结构：
   VoiceInput_v2.5/
   ├── model/
   │   └── fun/           # FunASR模型文件 (需要单独下载)
   ├── onnx_deps/        # ONNX依赖文件 (如果需要)
   └── ...

2. 模型文件获取：
   - 从原开发环境复制 model/fun 文件夹
   - 下载官方模型文件包
   - 确保文件结构完整

3. 文件清单：
   model/fun/ 应包含：
   - damo/speech_asr_nat-zh-cn_16k-common-vocab8484-pytorch.model
   - damo/speech_asr_nat-zh-cn_16k-common-vocab8484-pytorch.yaml
   - damo/fsmn_vad_common-zh-cn-16k-common-pytorch
   - damo/speech_separation_noh_16k_1684_snapshot.onnx
   - damo/speech_timestamp_prediction-16k-common-zh-cn-2024-03-14.model.onnx

4. 启动说明：
   - 确保model/fun目录存在且包含必要文件
   - 双击 VoiceInput_v2.5.exe 启动程序
   - 首次运行会自动检查文件完整性

5. 依赖说明：
   - 程序已内置所有Python依赖
   - 不需要单独安装Python环境
   - 模型文件外部管理，减小exe体积
""")

    print(f"✅ 发布包创建完成: {release_dir}")

    # 显示大小信息
    build_size = sum(f.stat().st_size for f in build_dir.rglob('*') if f.is_file())
    release_size = sum(f.stat().st_size for f in release_dir.rglob('*') if f.is_file())

    print(f"📊 构建目录大小: {build_size / (1024*1024):.1f} MB")
    print(f"📊 发布包大小: {release_size / (1024*1024):.1f} MB")

    return True

def create_model_package():
    """创建模型文件包"""
    print("📦 创建模型文件包...")

    if not Path("model/fun").exists():
        print("❌ model/fun目录不存在，跳过模型包创建")
        return False

    model_package_dir = Path("release/VoiceInput_v2.5_Models")
    model_package_dir.mkdir(parents=True, exist_ok=True)

    # 复制模型文件
    model_src = Path("model/fun")
    model_dst = model_package_dir / "fun"

    print("📋 复制模型文件...")
    if model_src.exists():
        shutil.copytree(model_src, model_dst)

        # 显示模型文件大小
        model_size = sum(f.stat().st_size for f in model_dst.rglob('*') if f.is_file())
        print(f"📊 模型文件大小: {model_size / (1024*1024):.1f} MB")

        # 创建说明文件
        model_readme = model_package_dir / "README.txt"
        with open(model_readme, 'w', encoding='utf-8') as f:
            f.write(f"""VoiceInput v2.5 模型文件包
======================

包含内容:
- FunASR语音识别模型
- VAD语音活动检测模型
- 时间戳预测模型

文件大小: {model_size / (1024*1024):.1f} MB

使用方法:
1. 将 fun 文件夹复制到程序目录下的 model/ 文件夹中
2. 确保目录结构为: model/fun/
3. 启动 VoiceInput_v2.5.exe

说明:
- 这些模型文件较大，因此从exe中分离
- 程序启动时会自动检查模型文件是否存在
- 如果模型文件缺失，程序会提示用户""")

        print(f"✅ 模型包创建完成: {model_package_dir}")
        return True
    else:
        print("❌ model/fun目录不存在")
        return False

def main():
    """主函数"""
    print("🚀 VoiceInput v2.5 打包工具")
    print("=" * 50)

    try:
        # 1. 检查依赖
        check_dependencies()

        # 2. 清理构建文件
        clean_build()

        # 3. 准备构建环境
        prepare_build()

        # 4. 构建exe文件
        if not build_exe():
            print("❌ 构建失败")
            return False

        # 5. 创建发布包
        if not create_distribution():
            print("❌ 发布包创建失败")
            return False

        # 6. 创建模型包（可选）
        create_model_package()

        print("\n🎉 打包完成！")
        print("=" * 50)
        print("📁 输出文件:")
        print("  📦 release/VoiceInput_v2.5/ - 主程序包")
        print("  📦 release/VoiceInput_v2.5_Models/ - 模型文件包（如果存在）")
        print("\n📋 部署说明:")
        print("1. 将整个 release/VoiceInput_v2.5/ 文件夹复制到目标计算机")
        print("2. 如果有模型包，将模型文件复制到程序的 model/ 目录")
        print("3. 双击 VoiceInput_v2.5.exe 启动程序")
        print("4. 首次运行会自动检查环境和文件完整性")

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