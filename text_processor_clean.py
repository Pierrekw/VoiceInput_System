#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的文本处理模块
精简逻辑，提高处理速度
"""

import re
from typing import Optional

# 尝试导入cn2an库
CN2AN_AVAILABLE = False
try:
    import cn2an
    CN2AN_AVAILABLE = True
except ImportError:
    cn2an = None

class TextProcessor:
    """优化的文本处理器类"""

    def __init__(self):
        # 简化的数字正则表达式
        self.num_pattern = re.compile(r"[零一二三四五六七八九十百千万点两]")
        # 完整数字模式（用于提取）
        self.full_num_pattern = re.compile(r"[负零一二三四五六七八九十百千万点两\d]+")
        # 扩展数字模式（用于提取）
        self.extended_num_pattern = re.compile(r"[负零一二三四五六七八九十百千万点两\d]+")
        # 常见单位
        self.units = {
            "度", "元", "块", "米", "公斤", "斤", "个", "只", "年", "月", "日", "时", "分", "秒"
        }

    def remove_spaces(self, text: str) -> str:
        """去除文本中的空格"""
        return re.sub(r'[\s　]', '', text) if text else text

    def convert_chinese_numbers_in_text(self, text: str) -> str:
        """
        在文本中转换中文数字，智能规则：
        - 序号、编号、页码等：转换为阿拉伯数字
        - 数字值大于9：转换为阿拉伯数字
        - 其他小数字：保留中文数字
        """
        if not text or not CN2AN_AVAILABLE:
            return text

        result = text
        # 查找所有中文数字
        matches = self.full_num_pattern.findall(text)

        # 按长度排序，优先处理长的数字
        matches = sorted(set(matches), key=len, reverse=True)

        # 序号相关关键词
        sequence_keywords = [
            "序号", "编号", "第", "页", "章", "节", "条", "款", "项", "级",
            "楼", "层", "号", "室", "座", "排", "列", "行"
        ]

        # 检查数字是否在序号上下文中
        def is_sequence_context(match, full_text):
            # 检查数字前后是否有序号关键词
            match_start = full_text.find(match)
            if match_start == -1:
                return False

            # 检查前后几个字符
            context_range = 10
            start = max(0, match_start - context_range)
            end = min(len(full_text), match_start + len(match) + context_range)
            context = full_text[start:end]

            return any(keyword in context for keyword in sequence_keywords)

        for match in matches:
            try:
                # 去除空格后转换
                clean_match = re.sub(r'[\s　]', '', match)
                converted = cn2an.cn2an(clean_match, "smart")
                num_value = float(converted)

                should_convert = False

                # 规则1：序号上下文，总是转换
                if is_sequence_context(match, result):
                    should_convert = True
                # 规则2：数字大于9，转换为阿拉伯数字
                elif num_value > 9:
                    should_convert = True
                # 规则3：年份，总是转换
                elif len(clean_match) >= 3 and any(keyword in result for keyword in ["年", "公元"]):
                    should_convert = True

                if should_convert:
                    # 整数不显示小数点
                    if num_value.is_integer():
                        converted = str(int(num_value))
                    result = result.replace(match, converted)

            except:
                # 转换失败，保持原样
                continue

        return result

    def chinese_to_arabic_number(self, text: str) -> str:
        """将中文数字转换为阿拉伯数字"""
        if not text or not CN2AN_AVAILABLE:
            return text

        original_text = text
        result_text = text

        try:
            # 处理特殊格式如"点八四"
            if result_text.startswith("点") and len(result_text) > 1:
                result_text = "零" + result_text

            # 使用扩展正则表达式查找所有中文数字表达式（包括负号）
            matches = self.extended_num_pattern.findall(result_text)

            # 按长度排序，优先处理长匹配
            matches = sorted(matches, key=len, reverse=True)

            # 转换每个匹配的中文数字
            for match in matches:
                try:
                    # 使用cn2an进行转换
                    converted = cn2an.cn2an(match, "smart")
                    converted_float = float(converted)

                    # 检查数值范围
                    if -1000000 <= converted_float <= 1000000:
                        # 替换原文中的数字，保持小数格式
                        converted_str = str(converted_float)
                        # 去除尾部的.0，除非是整数
                        if converted_str.endswith('.0') and '.' not in converted_str[:-2]:
                            converted_str = converted_str[:-2]

                        result_text = result_text.replace(match, converted_str, 1)

                except Exception:
                    # 如果cn2an转换失败，尝试特殊情况处理
                    try:
                        # 处理特殊情况：单个字符
                        if match == '两':
                            result_text = result_text.replace(match, '2', 1)
                        elif match == '十':
                            result_text = result_text.replace(match, '10', 1)
                        elif match == '百':
                            result_text = result_text.replace(match, '100', 1)
                        elif match == '千':
                            result_text = result_text.replace(match, '1000', 1)
                        elif match == '万':
                            result_text = result_text.replace(match, '10000', 1)
                        elif match == '百万':
                            result_text = result_text.replace(match, '1000000', 1)
                    except Exception:
                        continue

        except Exception:
            return original_text

        return result_text

    def is_pure_number_or_with_unit(self, text: str) -> bool:
        """
        简化的检查：是否为纯数字或数字+单位
        删除70%规则，简化判断逻辑
        """
        if not text or not CN2AN_AVAILABLE:
            return False

        clean_text = self.remove_spaces(text)

        # 检查是否主要是数字（至少70%的字符是数字字符）
        digit_chars = "零一二三四五六七八九十百千万点负两"
        digit_count = sum(1 for char in clean_text if char in digit_chars)

        if len(clean_text) == 0:
            return False

        digit_ratio = digit_count / len(clean_text)

        # 如果主要是数字（>70%）或者是很短的纯数字，返回True
        return digit_ratio > 0.7 or (len(clean_text) <= 3 and digit_count == len(clean_text))

    def extract_numbers(self, original_text: str, processed_text: Optional[str] = None) -> list:
        """
        简化的数字提取逻辑
        """
        if not original_text or not CN2AN_AVAILABLE:
            return []

        try:
            # 检查是否为纯数字或数字+单位格式
            if self.is_pure_number_or_with_unit(original_text):
                clean_text = self.remove_spaces(original_text)

                # 尝试直接转换
                try:
                    num = cn2an.cn2an(clean_text, "smart")
                    num_float = float(num)
                    if -1000000 <= num_float <= 1000000000000:
                        return [num_float]
                except:
                    pass

            return []

        except Exception:
            return []

    def process_text(self, text: str) -> str:
        """
        优化的文本处理流程
        新规则：数字>9转换为阿拉伯数字，否则保留中文
        """
        if not text:
            return text

        # 第一步：去除空格
        result = self.remove_spaces(text)

        # 第二步：应用新规则转换数字
        result = self.convert_chinese_numbers_in_text(result)

        return result

# 便捷函数
def process_text(text: str) -> str:
    """便捷的文本处理函数"""
    processor = TextProcessor()
    return processor.process_text(text)

if __name__ == "__main__":
    # 测试
    processor = TextProcessor()

    test_cases = [
        "三 十 七 点 五",
        "一 百 二 十 三",
        "二 十 五 点 五",
        "零 点 五",
        "九 万 八 千",
        "点 八 四",
        "负 十",
        "今天气温二 十五度",
        "价格是一 百二 十三点五元"
    ]

    print("🎯 文本处理测试")
    print("-" * 40)

    for text in test_cases:
        result = processor.process_text(text)
        numbers = processor.extract_numbers(result)
        print(f"{text} -> {result} -> 数字: {numbers}")