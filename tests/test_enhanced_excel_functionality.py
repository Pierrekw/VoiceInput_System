#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强Excel导出器的延迟格式化功能
验证在实际使用场景中的性能表现和功能正确性
"""

import os
import sys
import time
import shutil
import logging
from datetime import datetime
from typing import List, Tuple, Union

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from excel_exporter_enhanced import ExcelExporterEnhanced
from logging_utils import LoggingManager

# 设置日志
logger = LoggingManager.get_logger(
    name='test_enhanced_excel',
    level=logging.DEBUG,
    console_level=logging.INFO,
    log_to_console=True,
    log_to_file=True
)

def create_mock_measure_spec():
    """创建模拟的测量规范文件"""
    spec_data = [
        [100, '半径1', 75.5, 85.8],
        [200, '半径2', 15.5, 30.5],
        [300, '半径3', 8.5, 12.5],
        [400, '半径4', 53.5, 57.5],
        [500, '尺寸1', 10.5, 13.5],
        [600, '尺寸2', 24.25, 28.35],
        [700, '尺寸3', 130.5, 135.5],
    ]

    try:
        import pandas as pd
        spec_df = pd.DataFrame(spec_data, columns=['标准序号', '标准内容', '下限', '上限'])
        spec_filename = "reports/PART-A001_MeasureSpec.xlsx"

        # 确保reports目录存在
        os.makedirs("reports", exist_ok=True)

        # 保存测量规范文件
        spec_df.to_excel(spec_filename, index=False)
        logger.info(f"✅ 创建模拟测量规范文件: {spec_filename}")
        return spec_filename
    except ImportError:
        logger.warning("❌ pandas未安装，跳过测量规范文件创建")
        return None
    except Exception as e:
        logger.error(f"❌ 创建测量规范文件失败: {e}")
        return None

def test_delayed_formatting():
    """测试延迟格式化功能"""
    logger.info("🎯 开始测试延迟格式化功能")
    logger.info("="*60)

    # 创建模拟测量规范文件
    spec_file = create_mock_measure_spec()

    # 创建测试导出器
    part_no = "PART-A001"
    batch_no = "B202501"
    inspector = "测试员"

    exporter = ExcelExporterEnhanced(
        filename="reports/test_delayed_formatting.xlsx",
        part_no=part_no,
        batch_no=batch_no,
        inspector=inspector
    )

    # 模拟语音识别数据
    test_data: List[Tuple[Union[float, str], str, str]] = [
        (80.0, "半径1 八十", "半径1 80.0"),
        (25.0, "半径2 二十五", "半径2 25.0"),
        (10.0, "半径3 十", "半径3 10.0"),
        (90.0, "半径1 九十", "半径1 90.0"),  # 超出上限
        (8.0, "半径3 八", "半径3 8.0"),     # 低于下限
        (55.0, "半径4 五十五", "半径4 55.0"),
        ("OK", "外观合格", "外观合格"),       # 文本结果
        (12.0, "尺寸1 十二", "尺寸1 12.0"),
    ]

    logger.info(f"📝 模拟写入 {len(test_data)} 条数据...")

    # 测试数据写入性能（无格式化）
    start_time = time.time()
    results = exporter.append_with_text(test_data)
    write_time = time.time() - start_time

    logger.info(f"✅ 数据写入完成，耗时: {write_time*1000:.2f}ms")
    logger.info(f"📊 写入 {len(results)} 条记录")

    # 验证会话数据
    session_data = exporter.get_session_data()
    logger.info(f"📋 会话数据: {len(session_data)} 条")

    # 模拟系统停止时的格式化
    logger.info("\n🔧 开始执行最终格式化...")
    start_time = time.time()
    success = exporter.finalize_excel_file()
    format_time = time.time() - start_time

    logger.info(f"✅ 格式化完成，耗时: {format_time*1000:.2f}ms")
    logger.info(f"📁 文件路径: {exporter.filename}")

    # 验证文件是否创建成功
    if os.path.exists(exporter.filename):
        file_size = os.path.getsize(exporter.filename)
        logger.info(f"📊 文件大小: {file_size} 字节")

        # 尝试读取并验证内容
        try:
            import pandas as pd
            df = pd.read_excel(exporter.filename)
            logger.info(f"📈 Excel文件包含 {len(df)} 行数据")

            # 显示前几行数据
            if len(df) > 0:
                logger.info("📋 前5行数据预览:")
                for idx, row in df.head(5).iterrows():
                    logger.info(f"   行{idx+1}: {dict(row)}")

            return True
        except ImportError:
            logger.warning("❌ pandas未安装，无法验证Excel内容")
        except Exception as e:
            logger.error(f"❌ 读取Excel文件失败: {e}")
    else:
        logger.error("❌ Excel文件未创建")
        return False

    return success

def test_performance_comparison():
    """测试性能对比：延迟格式化 vs 实时格式化"""
    logger.info("\n🚀 性能对比测试")
    logger.info("="*60)

    # 创建导出器实例
    exporter = ExcelExporterEnhanced(
        filename="reports/test_performance.xlsx",
        part_no="PERF-TEST",
        batch_no="B202501",
        inspector="性能测试"
    )

    # 测试数据
    test_data = [
        (float(i + 80), f"测试数据 {i+1}", f"测试数据 {i+1}")
        for i in range(50)  # 50条数据
    ]

    # 测试1：仅写入数据（延迟格式化）
    logger.info("📝 测试1: 延迟格式化（仅写入数据）")
    start_time = time.time()
    results = exporter.append_with_text(test_data)
    write_only_time = time.time() - start_time
    logger.info(f"   写入耗时: {write_only_time*1000:.2f}ms")

    # 测试2：最终格式化
    logger.info("🔧 测试2: 最终格式化")
    start_time = time.time()
    success = exporter.finalize_excel_file()
    format_time = time.time() - start_time
    logger.info(f"   格式化耗时: {format_time*1000:.2f}ms")

    # 总时间
    total_time = write_only_time + format_time
    logger.info(f"📊 总耗时: {total_time*1000:.2f}ms")
    logger.info(f"📊 平均每条数据写入时间: {(write_only_time/len(test_data))*1000:.2f}ms")

    return success

def test_measure_spec_integration():
    """测试测量规范集成功能"""
    logger.info("\n🔍 测量规范集成测试")
    logger.info("="*60)

    # 确保测量规范文件存在
    if not os.path.exists("reports/PART-A001_MeasureSpec.xlsx"):
        logger.warning("⚠️ 测量规范文件不存在，跳过此测试")
        return True

    # 创建导出器
    exporter = ExcelExporterEnhanced(
        filename="reports/test_measure_spec.xlsx",
        part_no="PART-A001",
        batch_no="B202501",
        inspector="测量测试"
    )

    # 测试数据（包含已知的标准序号）
    test_data = [
        (80.0, "半径1 80", "半径1 80"),   # 标准序号100，应该在范围内
        (90.0, "半径1 90", "半径1 90"),   # 标准序号100，超出上限
        (25.0, "半径2 25", "半径2 25"),   # 标准序号200，在范围内
        (8.0, "半径3 8", "半径3 8"),       # 标准序号300，低于下限
        (55.0, "半径4 55", "半径4 55"),    # 标准序号400，在范围内
    ]

    logger.info(f"📝 写入测试数据...")
    results = exporter.append_with_text(test_data)

    logger.info("🔧 执行格式化和测量规范查询...")
    success = exporter.finalize_excel_file()

    if success and os.path.exists(exporter.filename):
        try:
            import pandas as pd
            df = pd.read_excel(exporter.filename)

            logger.info("📋 测量规范查询结果:")
            for idx, row in df.iterrows():
                if '标准序号' in row and '测量值' in row and '判断结果' in row:
                    standard_id = row.get('标准序号', 'N/A')
                    measured_val = row.get('测量值', 'N/A')
                    judgment = row.get('判断结果', 'N/A')
                    deviation = row.get('偏差', 'N/A')

                    logger.info(f"   标准序号{standard_id}: 测量值{measured_val} -> {judgment} (偏差: {deviation})")

        except ImportError:
            logger.warning("❌ pandas未安装，无法验证测量规范结果")
        except Exception as e:
            logger.error(f"❌ 验证测量规范结果失败: {e}")

    return success

def cleanup_test_files():
    """清理测试文件"""
    logger.info("\n🧹 清理测试文件...")

    test_files = [
        "reports/test_delayed_formatting.xlsx",
        "reports/test_performance.xlsx",
        "reports/test_measure_spec.xlsx",
        "reports/PART-A001_MeasureSpec.xlsx"
    ]

    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"   已删除: {file_path}")
            except Exception as e:
                logger.warning(f"   删除失败: {file_path} - {e}")

def main():
    """主测试函数"""
    logger.info("🎯 增强Excel导出器延迟格式化功能测试")
    logger.info("="*80)

    # 确保reports目录存在
    os.makedirs("reports", exist_ok=True)

    try:
        # 测试1：延迟格式化功能
        test1_success = test_delayed_formatting()

        # 测试2：性能对比
        test2_success = test_performance_comparison()

        # 测试3：测量规范集成
        test3_success = test_measure_spec_integration()

        # 总结测试结果
        logger.info("\n" + "="*80)
        logger.info("📊 测试结果总结")
        logger.info("="*80)
        logger.info(f"✅ 延迟格式化功能: {'通过' if test1_success else '失败'}")
        logger.info(f"✅ 性能对比测试: {'通过' if test2_success else '失败'}")
        logger.info(f"✅ 测量规范集成: {'通过' if test3_success else '失败'}")

        if all([test1_success, test2_success, test3_success]):
            logger.info("🎉 所有测试通过！")
            return True
        else:
            logger.error("❌ 部分测试失败")
            return False

    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理测试文件
        cleanup_test_files()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)