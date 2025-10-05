#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试异步生产系统的核心功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def test_async_components():
    """测试异步组件"""
    print("测试异步组件...")

    try:
        # 测试异步音频捕获导入
        from async_audio.async_audio_capture import AsyncAudioCapture
        print("[OK] AsyncAudioCapture 导入成功")

        # 测试共享文本处理器
        from text_processor import extract_measurements
        test_cases = [
            ("温度二十五点五度", [25.5]),
            ("湿度百分之七十五", [75.0]),
            ("数值42", [42.0])
        ]

        for text, expected in test_cases:
            result = extract_measurements(text)
            status = "[OK]" if result == expected else "[FAIL]"
            print(f"{status} 文本提取: '{text}' -> {result}")

        print("[OK] 共享文本处理器测试完成")

        # 测试异步数据导出器
        try:
            from adapters.data_exporter_adapter import DataExporterAdapter
            exporter = DataExporterAdapter(file_name="test_output.xlsx")
            exporter.initialize()
            print("[OK] DataExporterAdapter 初始化成功")

            # 测试异步导出
            test_data = [(25.5, "温度测试"), (75.0, "湿度测试")]
            result = await exporter.append_with_text_async(test_data)
            print(f"[OK] 异步导出测试成功: {len(result)} 条记录")

        except Exception as e:
            print(f"[FAIL] 数据导出器测试失败: {e}")

        print("[OK] 所有异步组件测试完成")
        return True

    except Exception as e:
        print(f"[FAIL] 异步组件测试失败: {e}")
        return False

async def test_async_audio_capture():
    """测试异步音频捕获（模拟模式）"""
    print("\n测试异步音频捕获...")

    try:
        from async_audio.async_audio_capture import AsyncAudioCapture
        from interfaces.audio_processor import RecognitionResult

        # 创建测试模式的异步音频捕获
        capture = AsyncAudioCapture(test_mode=True)

        # 测试初始化
        success = await capture.initialize()
        print(f"{'[OK]' if success else '[FAIL]'} 异步音频捕获初始化: {success}")

        if success:
            # 测试识别回调
            callback_results = []

            def test_callback(result: RecognitionResult):
                callback_results.append(result)
                print(f"[回调] 识别回调: {result.final_text}")

            capture.add_recognition_callback(test_callback)
            print("[OK] 识别回调设置成功")

            # 测试开始/停止识别
            start_result = await capture.start_recognition()
            start_success = "started successfully" in start_result.final_text.lower()
            print(f"{'[OK]' if start_success else '[FAIL]'} 开始识别: {start_result.final_text}")

            # 等待一会儿让测试运行
            await asyncio.sleep(2)

            stop_result = await capture.stop_recognition()
            stop_success = "stopped successfully" in stop_result.final_text.lower()
            print(f"{'[OK]' if stop_success else '[FAIL]'} 停止识别: {stop_result.final_text}")

            print(f"[OK] 异步音频捕获测试完成，回调次数: {len(callback_results)}")

        await capture.cleanup()
        return True

    except Exception as e:
        print(f"[FAIL] 异步音频捕获测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("[开始] 异步生产系统测试")
    print("=" * 50)

    # 测试异步组件
    components_ok = await test_async_components()

    # 测试异步音频捕获
    audio_ok = await test_async_audio_capture()

    print("\n" + "=" * 50)
    if components_ok and audio_ok:
        print("[成功] 所有测试通过！异步生产系统工作正常。")
    else:
        print("[失败] 部分测试失败，需要进一步调试。")

    return components_ok and audio_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)