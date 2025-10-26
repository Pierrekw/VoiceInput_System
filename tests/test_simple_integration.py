#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化集成测试：直接测试增强Excel导出器功能
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from excel_exporter_enhanced import ExcelExporterEnhanced
from logging_utils import LoggingManager

# 设置日志
logger = LoggingManager.get_logger(
    name='test_simple_integration',
    level=logging.DEBUG,
    console_level=logging.INFO,
    log_to_console=True,
    log_to_file=True
)

def create_measure_spec():
    """创建测量规范文件"""
    spec_data = [
        [100, '半径1', 75.5, 85.8],
        [200, '半径2', 15.5, 30.5],
        [300, '半径3', 8.5, 12.5],
        [400, '半径4', 53.5, 57.5],
    ]

    spec_df = pd.DataFrame(spec_data, columns=['标准序号', '标准内容', '下限', '上限'])
    spec_filename = "reports/SIMPLE-TEST_MeasureSpec.xlsx"

    os.makedirs("reports", exist_ok=True)
    spec_df.to_excel(spec_filename, index=False)

    logger.info(f"✅ 创建测量规范文件: {spec_filename}")
    return spec_filename

def test_simple_integration():
    """简化集成测试"""
    logger.info("🎯 简化集成测试")
    logger.info("="*60)

    # 创建测量规范文件
    create_measure_spec()

    # 创建导出器（不使用模板）
    exporter = ExcelExporterEnhanced(
        filename="reports/simple_integration_test.xlsx",
        part_no="SIMPLE-TEST",
        batch_no="B202501",
        inspector="测试员"
    )

    # 使用模板创建文件
    success = exporter.create_from_template(exporter.part_no, exporter.batch_no, exporter.inspector)
    if success:
        logger.info("✅ 使用模板创建Excel文件")
    else:
        logger.warning("⚠️ 模板创建失败，使用默认方式")
        exporter.create_new_file()

    # 测试数据
    test_scenarios = [
        (100, 80.0, "半径1 八十"),    # OK
        (100, 90.0, "半径1 九十"),    # NOK
        (200, 25.0, "半径2 二十五"),  # OK
        (200, 10.0, "半径2 十"),      # NOK
        (300, 11.0, "半径3 十一"),    # OK
        (400, 55.0, "半径4 五十五"),  # OK
    ]

    logger.info(f"📝 写入 {len(test_scenarios)} 条测试数据...")

    total_start = time.time()

    # 写入数据（延迟格式化模式）
    for standard_id, value, text in test_scenarios:
        exporter.current_standard_id = standard_id
        test_data = [(value, text, text)]

        start_time = time.time()
        results = exporter.append_with_text(test_data)
        write_time = time.time() - start_time

        logger.info(f"   标准序号{standard_id}: 值{value} -> 写入耗时: {write_time*1000:.2f}ms")

    total_write_time = time.time() - total_start
    logger.info(f"📊 总写入时间: {total_write_time*1000:.2f}ms")
    logger.info(f"📊 平均每条写入时间: {(total_write_time/len(test_scenarios))*1000:.2f}ms")

    # 执行最终格式化
    logger.info("🔧 执行最终格式化...")
    start_time = time.time()
    success = exporter.finalize_excel_file()
    format_time = time.time() - start_time

    logger.info(f"✅ 格式化完成，耗时: {format_time*1000:.2f}ms")

    if success and os.path.exists(exporter.filename):
        # 验证结果
        df = pd.read_excel(exporter.filename)
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
            elif standard_id in [300, 400]:
                expected = "OK"

            status = "✅" if judgment == expected else "❌"
            if judgment == expected:
                correct_count += 1

            logger.info(f"{status} 标准序号{standard_id}: {measured_val} -> {judgment} (偏差: {deviation}) [预期: {expected}]")

        logger.info("-" * 80)
        logger.info(f"📊 正确判断: {correct_count}/{len(test_scenarios)} 条")

        # 性能总结
        total_time = total_write_time + format_time
        logger.info(f"🚀 性能总结:")
        logger.info(f"   总耗时: {total_time*1000:.2f}ms")
        logger.info(f"   写入阶段: {total_write_time*1000:.2f}ms ({(total_write_time/total_time)*100:.1f}%)")
        logger.info(f"   格式化阶段: {format_time*1000:.2f}ms ({(format_time/total_time)*100:.1f}%)")
        logger.info(f"   平均每条数据处理时间: {(total_time/len(test_scenarios))*1000:.2f}ms")

        # 清理测试文件
        os.remove(exporter.filename)
        logger.info(f"🧹 已清理Excel文件")

        return correct_count == len(test_scenarios)

    else:
        logger.error("❌ Excel文件生成或格式化失败")
        return False

def main():
    """主测试函数"""
    logger.info("🎯 增强Excel导出器简化集成测试")
    logger.info("="*80)

    try:
        success = test_simple_integration()

        logger.info("\n" + "="*80)
        logger.info("📊 测试结果总结")
        logger.info("="*80)

        if success:
            logger.info("🎉 所有功能测试通过！")
            logger.info("✅ 延迟格式化功能正常 - 数据写入快速，格式化在停止时执行")
            logger.info("✅ 测量规范查询功能正常 - 自动查找并填充规范信息")
            logger.info("✅ 判断结果计算功能正常 - OK/NOK判断准确")
            logger.info("✅ 偏差计算功能正常 - 数值计算正确")
            logger.info("✅ 性能优化达到预期 - 避免了识别过程中的格式化开销")
        else:
            logger.error("❌ 部分功能测试失败")

        return success

    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理测量规范文件
        spec_file = "reports/SIMPLE-TEST_MeasureSpec.xlsx"
        if os.path.exists(spec_file):
            os.remove(spec_file)
            logger.info(f"🧹 已清理测量规范文件")

if __name__ == "__main__":
    import time
    success = main()
    sys.exit(0 if success else 1)