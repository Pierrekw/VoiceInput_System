#!/usr/bin/env python3
"""
将 FunASR Paraformer 模型导出为 ONNX 格式
"""

import os
from pathlib import Path

def export_paraformer_to_onnx():
    """导出 paraformer streaming 模型到 ONNX 格式，生成 model.onnx 和 decoder.onnx"""

    # 设置模型路径
    model_path = "model/fun"
    output_path = "model/fun_onnx_full"

    print("开始导出 Paraformer Streaming 模型到 ONNX 格式...")
    print(f"源模型路径: {model_path}")
    print(f"输出路径: {output_path}")

    try:
        from funasr import AutoModel
        import shutil

        # 创建输出目录
        output_dir = Path(output_path)
        output_dir.mkdir(exist_ok=True, parents=True)

        # 加载本地模型
        print("正在加载本地 streaming 模型...")
        model = AutoModel(model=model_path, device="cpu", disable_update=True)

        # 强制导出 ONNX 模型（不量化），确保生成 encoder 和 decoder
        print("正在导出非量化 streaming ONNX 模型（包括 encoder 和 decoder）...")

        # 使用显式参数确保导出完整模型
        onnx_result = model.export(
            type="onnx",
            quantize=False,
            # 尝试添加更多参数以确保完整导出
            fallback_num=5,
            calib_num=100,
            opset_version=14
        )

        print("✅ Streaming ONNX 模型导出成功!")
        print(f"导出结果: {onnx_result}")

        # 复制必要的配置文件到输出目录
        config_files = ["config.yaml", "am.mvn", "tokens.json", "seg_dict"]
        print("正在复制配置文件...")
        for file_name in config_files:
            src_file = Path(model_path) / file_name
            if src_file.exists():
                shutil.copy2(src_file, output_dir / file_name)
                print(f"  ✓ 复制: {file_name}")

        # 强制查找并复制所有ONNX文件，包括可能遗漏的decoder
        print("正在查找并复制ONNX文件...")

        # 搜索原模型目录中的ONNX文件
        onnx_files = list(Path(model_path).glob("*.onnx"))
        print(f"在原目录中找到 {len(onnx_files)} 个ONNX文件")

        # 如果原目录没有，检查导出结果目录
        if not onnx_files and onnx_result:
            print(f"检查导出结果目录: {onnx_result}")
            if os.path.exists(onnx_result):
                onnx_files = list(Path(onnx_result).glob("*.onnx"))

        if onnx_files:
            print("复制以下ONNX文件:")
            for file in onnx_files:
                dest_file = output_dir / file.name
                shutil.copy2(file, dest_file)
                print(f"  ✓ 复制ONNX: {file.name}")

        # 检查输出目录的文件
        print(f"\n📁 输出目录内容: {output_path}")
        found_onnx = []
        for file in output_dir.iterdir():
            if file.is_file():
                print(f"  - {file.name}")
                if file.suffix == ".onnx":
                    found_onnx.append(file.name)

        # 验证是否有必要的ONNX文件
        print(f"\n🔍 找到的ONNX文件: {found_onnx}")
        if "decoder.onnx" in found_onnx:
            print("✅ 成功找到 decoder.onnx 文件!")
        else:
            print("⚠️ 未找到 decoder.onnx 文件")
            print("这可能意味着模型不是真正的streaming版本，或者导出过程有问题")
            print("让我们检查模型配置是否支持streaming")

        return output_path

    except Exception as e:
        print(f"❌ 导出失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return None

def export_quantized_onnx():
    """导出量化版本的 ONNX 模型"""

    model_path = "model/fun"

    print("\n开始导出量化版本的 ONNX 模型...")

    try:
        from funasr import AutoModel

        # 加载本地模型
        print("正在加载本地模型...")
        model = AutoModel(model=model_path, device="cpu")

        # 导出量化的 ONNX 模型
        print("正在导出量化 ONNX 模型...")
        onnx_result = model.export(quantize=True)

        print("✅ 量化 ONNX 模型导出成功!")
        print(f"导出结果: {onnx_result}")

        return onnx_result

    except Exception as e:
        print(f"❌ 量化导出失败: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("FunASR Paraformer 模型 ONNX 导出工具")
    print("=" * 60)

    # 导出普通 ONNX 模型
    result1 = export_paraformer_to_onnx()

    # 导出量化 ONNX 模型
    result2 = export_quantized_onnx()

    print("\n" + "=" * 60)
    print("导出完成!")

    if result1 or result2:
        print("\n📋 使用说明:")
        print("1. 普通 ONNX 模型: model/fun/onnx/")
        print("2. 量化 ONNX 模型: model/fun/onnx_quant/")
        print("\n🧪 测试 ONNX 模型:")
        print("from runtime.python.onnxruntime.funasr_onnx.paraformer_bin import Paraformer")
        print("model = Paraformer('model/fun', batch_size=1, quantize=False/True)")
    else:
        print("❌ 所有导出尝试都失败了")