# -*- coding: utf-8 -*-
"""
异步数值提取模块

提供异步的中文数字和阿拉伯数字提取功能。
"""

import asyncio
import re
import logging
from typing import List, Optional, Any
import cn2an

logger = logging.getLogger(__name__)

# 数值提取正则表达式
_NUM_PATTERN = re.compile(r"[零一二三四五六七八九十百千万点两\d]+(?:\.[零一二三四五六七八九十百千万点两\d]+)*")
_UNIT_PATTERN = re.compile(r"([零一二三四五六七八九十百千万点两\d]+(?:\.[零一二三四五六七八九十百千万点两\d]+)*)(?:公斤|克|吨|米|厘米|毫米|升|毫升|秒|分钟|小时|天|月|年)")


class AsyncNumberExtractor:
    """异步数值提取器"""

    def __init__(self):
        """初始化异步数值提取器"""
        self._cache: dict[str, List[float]] = {}
        self._cache_lock = asyncio.Lock()

    async def extract_measurements(self, text: Any) -> List[float]:
        """
        异步提取文本中的数值

        Args:
            text: 输入文本

        Returns:
            List[float]: 提取的数值列表
        """
        if not isinstance(text, (str, int, float)):
            return []

        txt = str(text).strip()

        # 检查缓存
        cache_key = f"extract_{txt}"
        async with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key].copy()

        try:
            # 在线程池中执行CPU密集型的数值提取
            result = await asyncio.to_thread(self._extract_sync, txt)

            # 缓存结果
            async with self._cache_lock:
                self._cache[cache_key] = result.copy()

            return result

        except Exception as e:
            logger.error(f"❌ 异步数值提取失败: {e}")
            return []

    def _extract_sync(self, txt: str) -> List[float]:
        """同步数值提取（在线程池中执行）"""
        results: List[float] = []

        # 检查负数关键词
        negative_keywords = ['负数', '负']
        for keyword in negative_keywords:
            if keyword in txt:
                logger.debug(f"检测到负数关键词 '{keyword}'，不提取数字")
                return results

        # 尝试直接转换整个文本
        try:
            num = cn2an.cn2an(txt, "smart")
            num_float = float(num)
            if 0 <= num_float <= 1000000000000:
                logger.debug(f"直接转换整个文本得到数值: {num_float} (文本: '{txt}')")
                return [num_float]
        except Exception:
            logger.debug(f"直接转换失败: (文本: '{txt}')")

        # 处理特殊格式
        txt = self._handle_special_formats(txt)

        # 按字符逐个转换连续中文数字
        if all(char in "零一二三四五六七八九十百千万" for char in txt):
            try:
                result = ""
                for char in txt:
                    num = cn2an.cn2an(char, "smart")
                    result += str(num)
                if result.isdigit():
                    num_float = float(result)
                    if 0 <= num_float <= 1000000000000:
                        logger.debug(f"按字符逐个转换连续中文数字得到数值: {num_float} (文本: '{txt}')")
                        return [num_float]
            except Exception:
                pass

        # 处理常见的误识别模式
        error_corrections = {
            '我': '五',
            '我是': '五十',
            '零点': '0.'
        }

        for wrong, correct in error_corrections.items():
            if txt == wrong:
                try:
                    num = cn2an.cn2an(correct, "smart")
                    num_float = float(num)
                    if 0 <= num_float <= 10000000000:
                        logger.debug(f"成功将'{wrong}'识别为数值: {num_float}")
                        return [num_float]
                except Exception:
                    pass

        # 使用正则表达式提取数值
        matches = _NUM_PATTERN.findall(txt)
        for match in matches:
            try:
                num = cn2an.cn2an(match, "smart")
                num_float = float(num)
                if 0 <= num_float <= 1000000000000:
                    results.append(num_float)
                    logger.debug(f"正则匹配提取数值: {num_float} (文本: '{match}')")
            except Exception as e:
                logger.debug(f"数值转换失败: {e} (文本: '{match}')")

        return results

    def _handle_special_formats(self, text: str) -> str:
        """处理特殊的数字表达格式"""
        # 处理"点X"格式
        if text.startswith("点") and len(text) > 1:
            return "零" + text
        return text

    async def extract_with_units(self, text: str) -> List[tuple[float, str]]:
        """
        异步提取带单位的数值

        Args:
            text: 输入文本

        Returns:
            List[tuple[float, str]]: 数值和单位的列表
        """
        try:
            # 在线程池中执行匹配
            matches = await asyncio.to_thread(_UNIT_PATTERN.findall, text)

            results = []
            for match in matches:
                # 提取数值部分
                number_text = match[0]
                numbers = await self.extract_measurements(number_text)

                if numbers:
                    # 提取单位部分
                    unit_match = await asyncio.to_thread(
                        lambda: _UNIT_PATTERN.search(text)
                    )
                    if unit_match:
                        full_match = unit_match.group(0)
                        unit = full_match.replace(number_text, "")
                        results.append((numbers[0], unit))

            return results

        except Exception as e:
            logger.error(f"❌ 异步带单位数值提取失败: {e}")
            return []

    async def clear_cache(self):
        """清空缓存"""
        async with self._cache_lock:
            self._cache.clear()
        logger.debug("🗑️ 数值提取缓存已清空")

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {
            "cache_size": len(self._cache),
            "cache_keys": list(self._cache.keys())
        }


# 全局实例
_global_extractor = AsyncNumberExtractor()


async def extract_measurements(text: Any) -> List[float]:
    """全局异步数值提取函数"""
    return await _global_extractor.extract_measurements(text)


async def extract_with_units(text: str) -> List[tuple[float, str]]:
    """全局异步带单位数值提取函数"""
    return await _global_extractor.extract_with_units(text)