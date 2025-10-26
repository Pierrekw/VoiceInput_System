#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的文本处理模块
精简逻辑，提高处理速度
"""

import re
import logging
from typing import Optional, Dict, Any, List, Tuple

from utils.logging_utils import LoggingManager

logger = LoggingManager.get_logger(
    name='text_processor_clean',
    level=logging.DEBUG,
    console_level=logging.INFO,
    log_to_console=True,
    log_to_file=True
)

# 尝试导入cn2an库
CN2AN_AVAILABLE = False
try:
    import cn2an  # type: ignore
    CN2AN_AVAILABLE = True
except ImportError:
    cn2an = None

class TextProcessor:
    """优化的文本处理器类"""

    def __init__(self) -> None:
        logger.debug("初始化TextProcessor实例")
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
        logger.debug(f"开始转换中文数字: {text[:50]}...")
        if not text or not CN2AN_AVAILABLE:
            logger.debug("文本为空或cn2an不可用，跳过转换")
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
        def is_sequence_context(match: str, full_text: str) -> bool:
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
                logger.debug(f"转换中文数字: '{match}' -> '{clean_match}'")
                converted = cn2an.cn2an(clean_match, "smart")
                num_value = float(converted)
                logger.debug(f"转换结果: {num_value}")

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
                # 规则4：小数（包含点），总是转换
                elif '点' in clean_match:
                    should_convert = True

                if should_convert:
                    # 整数不显示小数点
                    if num_value.is_integer():
                        converted = str(int(num_value))
                    result = result.replace(match, converted)

            except Exception as e:
                # 转换失败，保持原样
                logger.debug(f"中文数字转换失败: '{match}'，错误: {str(e)}")
                continue

        return result

    def chinese_to_arabic_number(self, text: str) -> str:
        """将中文数字转换为阿拉伯数字"""
        logger.debug(f"开始中文转阿拉伯数字: {text}")
        if not text or not CN2AN_AVAILABLE:
            logger.debug("文本为空或cn2an不可用，跳过转换")
            return text

        original_text = text
        result_text = text

        try:
            # 预处理：修复中文数字语法错误（关键修复）
            # 处理"一百十三" -> "一百一十三"的情况
            if '一百十三' in result_text:
                result_text = result_text.replace('一百十三', '一百一十三')
            if '二百十三' in result_text:
                result_text = result_text.replace('二百十三', '二百一十三')
            if '三百十三' in result_text:
                result_text = result_text.replace('三百十三', '三百一十三')
            if '四百十三' in result_text:
                result_text = result_text.replace('四百十三', '四百一十三')
            if '五百十三' in result_text:
                result_text = result_text.replace('五百十三', '五百一十三')
            if '六百十三' in result_text:
                result_text = result_text.replace('六百十三', '六百一十三')
            if '七百十三' in result_text:
                result_text = result_text.replace('七百十三', '七百一十三')
            if '八百十三' in result_text:
                result_text = result_text.replace('八百十三', '八百一十三')
            if '九百十三' in result_text:
                result_text = result_text.replace('九百十三', '九百一十三')

            # 通用模式：处理"[X]百十三"的情况
            import re
            pattern = r'([一二三四五六七八九十])百十三'
            def replace_hundred_thirteen(match: re.Match[str]) -> str:
                first_digit = match.group(1)
                return f'{first_digit}百一十三'
            result_text = re.sub(pattern, replace_hundred_thirteen, result_text)

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

        except Exception as e:
            logger.error(f"中文数字转换过程出错: {str(e)}")
            return original_text

        return result_text

    def is_pure_number_or_with_unit(self, text: str) -> bool:
        """
        简化的检查：是否为纯数字或数字+单位
        提高阈值到90%，避免误判含非数字字符的文本
        """
        if not text or not CN2AN_AVAILABLE:
            return False

        clean_text = self.remove_spaces(text)

        # 检查是否主要是数字（至少90%的字符是数字字符）
        digit_chars = "零一二三四五六七八九十百千万点负两幺"
        digit_count = sum(1 for char in clean_text if char in digit_chars)

        if len(clean_text) == 0:
            return False

        digit_ratio = digit_count / len(clean_text)

        # 如果主要是数字（>90%）或者是很短的纯数字，返回True
        return digit_ratio > 0.9 or (len(clean_text) <= 3 and digit_count == len(clean_text))

    def extract_numbers(self, original_text: str, processed_text: Optional[str] = None) -> List[float]:
        """
        简化的数字提取逻辑
        重构后优先从processed_text中提取阿拉伯数字
        """
        logger.debug(f"开始提取数字: '{original_text[:50]}...'，处理后文本: {processed_text[:50]+'...' if processed_text is not None else None}")
        if not original_text:
            logger.debug("原始文本为空，返回空列表")
            return []

        try:
            # 优先从处理后的文本中提取数字（重构后的逻辑）
            text_to_extract = processed_text if processed_text else original_text

            # 如果处理后的文本包含阿拉伯数字，直接提取
            import re
            if CN2AN_AVAILABLE and processed_text:
                # 提取阿拉伯数字（包括小数）
                arabic_numbers = re.findall(r'\d+\.?\d*', text_to_extract)
                if arabic_numbers:
                    numbers = []
                    for num_str in arabic_numbers:
                        try:
                            num = float(num_str)
                            # 限制数字范围
                            if -1000000 <= num <= 1000000000000:
                                numbers.append(num)
                        except ValueError:
                            continue
                    return numbers

            # 如果没有阿拉伯数字，尝试转换中文数字
            if not CN2AN_AVAILABLE:
                return []

            # 尝试用cn2an直接转换处理后的文本
            try:
                converted_num = cn2an.cn2an(text_to_extract, "smart")
                converted_float = float(converted_num)
                if -1000000 <= converted_float <= 1000000000000:
                    return [converted_float]
            except Exception:
                pass

            # 回退到原来的逻辑（从中文数字转换）

            # 检查是否为纯数字或数字+单位格式
                # 应用与process_text相同的预处理逻辑（关键修复）
                text_to_convert = self.remove_spaces(original_text)

                # 特殊处理"幺"字符
                text_to_convert = text_to_convert.replace('幺', '一')

                # 修复中文数字语法错误（关键修复）
                # 处理"一百十三" -> "一百一十三"的情况
                if '一百十三' in text_to_convert:
                    text_to_convert = text_to_convert.replace('一百十三', '一百一十三')
                if '二百十三' in text_to_convert:
                    text_to_convert = text_to_convert.replace('二百十三', '二百一十三')
                if '三百十三' in text_to_convert:
                    text_to_convert = text_to_convert.replace('三百十三', '三百一十三')
                if '四百十三' in text_to_convert:
                    text_to_convert = text_to_convert.replace('四百十三', '四百一十三')
                if '五百十三' in text_to_convert:
                    text_to_convert = text_to_convert.replace('五百十三', '五百一十三')
                if '六百十三' in text_to_convert:
                    text_to_convert = text_to_convert.replace('六百十三', '六百一十三')
                if '七百十三' in text_to_convert:
                    text_to_convert = text_to_convert.replace('七百十三', '七百一十三')
                if '八百十三' in text_to_convert:
                    text_to_convert = text_to_convert.replace('八百十三', '八百一十三')
                if '九百十三' in text_to_convert:
                    text_to_convert = text_to_convert.replace('九百十三', '九百一十三')

                # 通用模式：处理"[X]百十三"的情况
                pattern = r'([一二三四五六七八九十])百十三'
                def replace_hundred_thirteen(match: re.Match[str]) -> str:
                    first_digit = match.group(1)
                    return f'{first_digit}百一十三'
                import re
                text_to_convert = re.sub(pattern, replace_hundred_thirteen, text_to_convert)

                # 尝试转换预处理后的文本
                try:
                    num = cn2an.cn2an(text_to_convert, "smart")
                    num_float = float(num)
                    if -1000000 <= num_float <= 1000000000000:
                        return [num_float]
                except:
                    pass

            return []

        except Exception as e:
            logger.error(f"数字提取过程出错: {str(e)}")
            return []

    def process_text(self, text: str) -> str:
        """
        优化的文本处理流程
        新规则：数字>9转换为阿拉伯数字，否则保留中文
        """
        logger.debug(f"开始处理文本: {text[:100]}...")
        if not text:
            logger.debug("文本为空，直接返回")
            return text

        # 第一步：去除空格
        result = self.remove_spaces(text)
        logger.debug(f"去除空格后: {result[:100]}...")

        # 第二步：特殊处理"幺"字符
        result = result.replace('幺', '一')
        logger.debug(f"替换'幺'后: {result[:100]}...")

        # 第三步：修复中文数字语法错误（关键修复）
        # 处理"一百十三" -> "一百一十三"的情况
        if '一百十三' in result:
            result = result.replace('一百十三', '一百一十三')
            logger.debug(f"修复数字语法后: {result[:100]}...")
        if '二百十三' in result:
            result = result.replace('二百十三', '二百一十三')
        if '三百十三' in result:
            result = result.replace('三百十三', '三百一十三')
        if '四百十三' in result:
            result = result.replace('四百十三', '四百一十三')
        if '五百十三' in result:
            result = result.replace('五百十三', '五百一十三')
        if '六百十三' in result:
            result = result.replace('六百十三', '六百一十三')
        if '七百十三' in result:
            result = result.replace('七百十三', '七百一十三')
        if '八百十三' in result:
            result = result.replace('八百十三', '八百一十三')
        if '九百十三' in result:
            result = result.replace('九百十三', '九百一十三')

        # 通用模式：处理"[X]百十三"的情况
        import re
        pattern = r'([一二三四五六七八九十])百十三'
        def replace_hundred_thirteen(match: re.Match[str]) -> str:
            first_digit = match.group(1)
            return f'{first_digit}百一十三'
        result = re.sub(pattern, replace_hundred_thirteen, result)

        # 第四步：应用新规则转换数字
        result = self.convert_chinese_numbers_in_text(result)
        logger.debug(f"文本处理完成，结果: {result[:100]}...")

        return result

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本之间的相似度
        使用编辑距离算法

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度 (0-1之间的浮点数)
        """
        if not text1 or not text2:
            return 0.0

        # 如果完全相等，返回1.0
        if text1 == text2:
            return 1.0

        # 计算编辑距离
        len1, len2 = len(text1), len(text2)
        if len1 == 0:
            return 0.0
        if len2 == 0:
            return 0.0

        # 创建动态规划表
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

        # 初始化边界条件
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j

        # 填充动态规划表
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if text1[i-1] == text2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(
                        dp[i-1][j] + 1,      # 删除
                        dp[i][j-1] + 1,      # 插入
                        dp[i-1][j-1] + 1     # 替换
                    )

        # 计算相似度
        max_len = max(len1, len2)
        edit_distance = dp[len1][len2]
        similarity = 1.0 - (edit_distance / max_len)

        return max(0.0, similarity)

    def check_special_text(self, text: str, exportable_texts: List[Dict[str, Any]], export_enabled: bool = True) -> Optional[str]:
        """
        检查文本是否匹配特定文本配置

        Args:
            text: 要检查的文本
            exportable_texts: 可导出文本配置列表
            export_enabled: 是否启用特殊文本导出

        Returns:
            如果匹配，返回对应的基础文本；否则返回None
        """
        if not export_enabled or not exportable_texts:
            return None

        text_lower = text.lower().strip()

        for text_config in exportable_texts:
            base_text = text_config.get('base_text')
            if base_text is None:
                continue
            variants = text_config.get('variants', [])

            # 检查文本是否匹配任何变体
            for variant in variants:
                if variant.lower() == text_lower or text_lower in variant.lower():
                    return str(base_text)

        return None

    def clean_text_for_command_matching(self, text: str) -> str:
        """
        清理文本用于命令匹配

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        text_clean = text.lower().strip()

        # 移除常见的标点符号
        text_clean = re.sub(r'[。！？\.,!?\s]', '', text_clean)

        return text_clean

# 新增语音命令处理器类
class VoiceCommandProcessor:
    """语音命令专用文本处理器"""

    def __init__(self) -> None:
        logger.debug("初始化VoiceCommandProcessor实例")
        self.text_processor = TextProcessor()
        self.match_mode = "fuzzy"
        self.min_match_length = 2
        self.confidence_threshold = 0.8

    def configure(self, match_mode: str = "fuzzy", min_match_length: int = 2, confidence_threshold: float = 0.8) -> None:
        """配置匹配参数"""
        logger.debug(f"配置命令处理器: match_mode={match_mode}, min_match_length={min_match_length}, confidence_threshold={confidence_threshold}")
        self.match_mode = match_mode
        self.min_match_length = min_match_length
        self.confidence_threshold = confidence_threshold

    def process_command_text(self, text: str) -> str:
        """处理命令文本"""
        result = self.text_processor.clean_text_for_command_matching(text)
        logger.debug(f"命令文本处理: '{text}' -> '{result}'")
        return result

    def match_command(self, text: str, commands: Dict[str, List[str]]) -> Optional[str]:
        """
        匹配语音命令

        Args:
            text: 识别的文本
            commands: 命令字典 {command_type: [keywords]}

        Returns:
            匹配的命令类型，如果没有匹配返回None
        """
        logger.debug(f"尝试匹配命令: '{text}'")
        if not text or len(text.strip()) < self.min_match_length:
            logger.debug(f"文本长度小于最小匹配长度({self.min_match_length})，跳过匹配")
            return None

        text_clean = self.process_command_text(text)

        for command_type, keywords in commands.items():
            for keyword in keywords:
                keyword_clean = self.text_processor.clean_text_for_command_matching(keyword)

                if self.match_mode == "exact":
                    # 精确匹配模式
                    if text_clean == keyword_clean:
                        return command_type

                elif self.match_mode == "fuzzy":
                    # 模糊匹配模式
                    similarity = self.text_processor.calculate_similarity(text_clean, keyword_clean)

                    # 对于停止命令，要求更高的匹配度
                    if command_type == "stop":
                        if similarity >= 0.7 or keyword_clean in text_clean:
                            return command_type
                    else:
                        # 其他命令使用标准的相似度阈值
                        if similarity >= self.confidence_threshold:
                            return command_type

        return None

    def match_standard_id_command(self, text: str, command_prefixes: List[str]) -> Optional[int]:
        """
        基于模式匹配标准序号命令

        Args:
            text: 识别的文本
            command_prefixes: 命令前缀列表，如 ["切换", "设置", "切换到", "设置序号"]

        Returns:
            如果匹配到标准序号命令，返回标准序号数值；否则返回None
        """
        logger.debug(f"尝试匹配标准序号命令: '{text}'")
        if not text:
            return None

        text_clean = self.process_command_text(text)

        # 检查是否包含任何命令前缀
        for prefix in command_prefixes:
            prefix_clean = self.text_processor.clean_text_for_command_matching(prefix)

            # 检查文本是否以命令前缀开头
            if text_clean.startswith(prefix_clean) or prefix_clean in text_clean:
                # 提取前缀后的数字部分
                remaining_text = text_clean.replace(prefix_clean, '', 1).strip()

                # 如果没有剩余文本，尝试从原始文本中提取数字
                if not remaining_text:
                    remaining_text = text_clean.replace(prefix_clean, '', 1).strip()

                logger.debug(f"命令前缀匹配: '{prefix}', 剩余文本: '{remaining_text}'")

                # 从剩余文本中提取数字
                if remaining_text:
                    numbers = self.text_processor.extract_numbers(remaining_text)
                    if numbers:
                        standard_id = int(numbers[0])
                        # 验证是否为有效的标准序号（100的倍数）
                        if standard_id > 0 and standard_id % 100 == 0:
                            logger.info(f"匹配到标准序号命令: {prefix} -> {standard_id}")
                            return standard_id
                        else:
                            logger.debug(f"提取的数字不是有效的标准序号: {standard_id}")

                # 如果直接提取数字失败，尝试中文数字转换
                try:
                    # 使用TextProcessor处理剩余文本
                    processed_remaining = self.text_processor.process_text(remaining_text)
                    numbers = self.text_processor.extract_numbers(processed_remaining)
                    if numbers:
                        standard_id = int(numbers[0])
                        if standard_id > 0 and standard_id % 100 == 0:
                            logger.info(f"通过转换匹配到标准序号命令: {prefix} -> {standard_id}")
                            return standard_id
                except Exception as e:
                    logger.debug(f"中文数字转换失败: {e}")
                    continue

        logger.debug(f"未匹配到标准序号命令: '{text}'")
        return None

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