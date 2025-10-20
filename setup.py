from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()
    # 过滤空行和注释行
    requirements = [req for req in requirements if req.strip() and not req.strip().startswith("#")]

setup(
    name="voice-input",
    version="0.1.2",
    description="A powerful real-time voice recognition offline system with pause/resume functionality and automatic Excel export capabilities.",
    author="Pierre.W",
    author_email="xingw1013@gmail.com",
    packages=find_packages(),
    py_modules=["main_f", "excel_exporter", "TTSengine"],
    install_requires=[
        # 核心依赖 - 使用兼容版本
        "funasr>=1.2.7",
        "torch==2.3.1+cpu",  # 指定当前安装的CPU版本
        "torchaudio==2.3.1+cpu",
        "torchvision==0.18.1+cpu",
        # 其他必要依赖
        "numpy<2",
        "pandas==2.3.2",
        "openpyxl==3.1.5",
        "pyaudio==0.2.14",
        "cn2an==0.5.23",
        "modelscope==1.31.0",
        "onnxruntime==1.15.1",
        # 其他从requirements.txt导入的依赖
        *requirements
    ],
    python_requires=">=3.11",
    # 避免严格版本检查的兼容性标志
    setup_requires=["setuptools>=61.0", "wheel"],
    # 添加兼容性说明
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)