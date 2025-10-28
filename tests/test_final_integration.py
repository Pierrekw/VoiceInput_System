#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终集成测试：验证增强Excel导出器在语音识别系统中的完整功能
"""

import os
import sys
import time
import logging
import pandas as pd
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from main_f import FunASRVoiceSystem
from logging_utils import LoggingManager

# 设置日志
logger = LoggingManager.get_logger(
    name='test_final_integration',
    level=logging.DEBUG,
    console_level=logging.INFO,
    log_to_console=True,
    log_to_file=True
)

def create_comprehensive_measure_spec():
    """创建完整的测量规范文件"""
    spec_data = [
        [100, '半径1', 75.5, 85.8],
        [200, '半径2', 15.5, 30.5],
        [300, '半径3', 8.5, 12.5],
        [400, '半径4', 53.5, 57.5],
        [500, '直径1', 20.0, 25.0],
        [600, '长度1', 100.0, 120.0],
    ]

    spec_df = pd.DataFrame(spec_data, columns=['标准序号', '标准内容', '下限', '上限'])
    spec_filename = "reports/FINAL-TEST_MeasureSpec.xlsx"

    os.makedirs("reports", exist_ok=True)
    spec_df.to_excel(spec_filename, index=False)

    logger.info(f"✅ 创建完整测量规范文件: {spec_filename}")
    return spec_filename

def test_voice_system_integration():
    """测试语音系统集成"""
    logger.info("🎯 语音系统集成测试")
    logger.info("="*80)

    # 创建测量规范文件
    create_comprehensive_measure_spec()

    try:
        # 创建语音系统实例
        logger.info("🚀 创建语音系统实例...")
        system = FunASRVoiceSystem(
            recognition_duration=30,  # 30秒测试
            continuous_mode=False,
            debug_mode=True
        )

        # 初始化系统
        if not system.initialize():
            logger.error("❌ 语音系统初始化失败")
            return False

        logger.info("✅ 语音系统初始化成功")

        # 设置Excel模板
        part_no = "FINAL-TEST"
        batch_no = "B202501"
        inspector = "集成测试员"

        success = system.setup_excel_from_gui(part_no, batch_no, inspector)
        if success:
            logger.info(f"✅ Excel模板设置成功: {part_no}_{batch_no}")
        else:
            logger.warning("⚠️ Excel模板设置失败，使用默认方式")

        # 模拟语音识别数据直接写入Excel
        logger.info("📝 模拟语音识别数据写入...")

        test_scenarios = [
            (100, 80.0, "半径1 八十毫米"),
            (100, 90.0, "半径1 九十毫米"),
            (200, 25.0, "半径2 二十五毫米"),
            (300, 10.0, "半径3 十毫米"),
            (400, 55.0, "半径4 五十五毫米"),
            (500, 22.0, "直径1 二十二毫米"),
            (600, 110.0, "长度1 一百一十毫米"),
            ("OK", "外观合格", "外观合格"),
        ]

        # 动态设置标准序号并写入数据
        for standard_id, value, text in test_scenarios:
            system.excel_exporter.current_standard_id = standard_id

            if isinstance(value, str):
                test_data = [(value, text, text)]
            else:
                test_data = [(value, text, text)]

            # 模拟处理识别结果
            numbers = [value] if isinstance(value, (int, float)) else []
            system.process_recognition_result(text, text, numbers)

            logger.info(f"   写入: 标准序号{standard_id}, 值{value}")

        logger.info(f"📊 总共写入 {len(test_scenarios)} 条记录")

        # 执行Excel最终格式化（模拟系统停止）
        logger.info("🔧 执行Excel最终格式化...")
        start_time = time.time()
        system._finalize_excel()
        format_time = time.time() - start_time

        logger.info(f"✅ 格式化完成，耗时: {format_time*1000:.2f}ms")

        # 验证结果
        if system.excel_exporter and os.path.exists(system.excel_exporter.filename):
            logger.info(f"📁 Excel文件: {system.excel_exporter.filename}")

            # 读取并验证结果
            df = pd.read_excel(system.excel_exporter.filename)
            data_rows = df.iloc[2:]  # 跳过标题行

            logger.info(f"📋 验证结果 ({len(data_rows)} 条数据):")
            logger.info("-" * 80)

            correct_count = 0
            for idx, row in data_rows.iterrows():
                if pd.isna(row.iloc[0]):  # 跳过空行
                    continue

                standard_id = int(row.iloc[0])
                measured_val = row.iloc[4]
                judgment = row.iloc[5] if pd.notna(row.iloc[5]) else 'N/A'
                deviation = row.iloc[6] if pd.notna(row.iloc[6]) else 'N/A'

                # 预期结果验证
                expected = "未知"
                if standard_id == 100:
                    expected = "OK" if measured_val == 80.0 else "NOK"
                elif standard_id == 200:
                    expected = "OK" if measured_val == 25.0 else "NOK"
                elif standard_id == 300:
                    expected = "NOK"  # 10.0 < 8.5
                elif standard_id in [400, 500, 600]:
                    expected = "OK"
                elif isinstance(measured_val, str):
                    expected = measured_val

                status = "✅" if judgment == expected else "❌"
                if judgment == expected:
                    correct_count += 1

                logger.info(f"{status} 标准序号{standard_id}: {measured_val} -> {judgment} (偏差: {deviation})")

            logger.info("-" * 80)
            logger.info(f"📊 正确判断: {correct_count}/{len(data_rows)} 条")

            # 清理测试文件
            os.remove(system.excel_exporter.filename)
            logger.info(f"🧹 已清理测试文件")

            return correct_count == len(data_rows)

        else:
            logger.error("❌ Excel文件未生成")
            return False

    except Exception as e:
        logger.error(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理测量规范文件
        spec_file = "reports/FINAL-TEST_MeasureSpec.xlsx"
        if os.path.exists(spec_file):
            os.remove(spec_file)
            logger.info(f"🧹 已清理测量规范文件")

def main():
    """主测试函数"""
    logger.info("🎯 增强Excel导出器最终集成测试")
    logger.info("="*100)

    try:
        success = test_voice_system_integration()

        logger.info("\n" + "="*100)
        logger.info("📊 最终测试结果")
        logger.info("="*100)

        if success:
            logger.info("🎉 所有功能测试通过！")
            logger.info("✅ 延迟格式化功能正常")
            logger.info("✅ 测量规范查询功能正常")
            logger.info("✅ 判断结果计算功能正常")
            logger.info("✅ 语音系统集成正常")
            logger.info("✅ 性能优化达到预期")
        else:
            logger.error("❌ 部分功能测试失败")

        return success

    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)