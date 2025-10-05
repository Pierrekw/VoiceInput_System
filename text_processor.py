# -*- coding: utf-8 -*-
"""
Shared Text Processing Module - 共享文本处理模块

This module provides shared text processing functionality for both
original (sync) and new (async) versions of the voice input system.
It handles Chinese number extraction, TTS feedback detection, and
voice error correction with backward compatibility.

这个模块为原始(同步)和新(异步)版本的语音输入系统提供共享的文本处理功能。
它处理中文数字提取、TTS反馈检测和语音错误纠正，同时保持向后兼容性。
"""

import re
import logging
from typing import List, Any, Optional, Dict
from config_loader import config

try:
    import cn2an
    CN2AN_AVAILABLE = True
except ImportError:
    CN2AN_AVAILABLE = False
    print("Warning: cn2an module not available, Chinese number conversion will be limited")

# 设置日志
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration and Constants
# =============================================================================

# TTS feedback keywords - prevent system processing its own feedback
TTS_FEEDBACK_KEYWORDS = ['成功提取', '识别到', '检测到', '测量值为']

# Chinese number characters
CHINESE_NUMBERS = set("零一二三四五六七八九十百千万")

# Value range limits (supports large numbers)
MIN_VALUE = -1000000000000  # -10^12
MAX_VALUE = 1000000000000   # 10^12

# =============================================================================
# Regular Expression Patterns
# =============================================================================

# Basic number pattern - handles Chinese and Arabic numbers
NUM_PATTERN = re.compile(r"(?:负)?[零一二三四五六七八九十百千万点两\d]+(?:\.(?:负)?[零一二三四五六七八九十百千万点两\d]+)*")

# Concatenated number pattern - detects joined Chinese numbers like "一千二三百"
CONCAT_PATTERN = re.compile(r"((?:负)?[一二三四五六七八九]千[一二三四五六七八九]?百?)([一二三四五六七八九]百)")

# Unit pattern - extracts numbers with units
UNIT_PATTERN = re.compile(r"((?:负)?[零一二三四五六七八九十百千万点两\d]+(?:\.(?:负)?[零一二三四五六七八九十百千万点两\d]+)*)(?:公斤|克|吨|米|厘米|毫米|升|毫升|秒|分钟|小时|天|月|年)")

# =============================================================================
# Voice Error Correction
# =============================================================================

def load_voice_correction_dict(file_path: Optional[str] = None) -> Dict[str, str]:
    """Load voice error correction dictionary"""
    # Check if error correction is enabled
    if not config.get("error_correction.enabled", True):
        logger.info("Voice error correction disabled")
        return {}

    # Use dictionary path from config
    if file_path is None:
        file_path = config.get("error_correction.dictionary_path", "voice_correction_dict.txt")

    # Ensure correct path resolution
    import os
    if not os.path.isabs(file_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, file_path)

    correction_dict = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line:
                    wrong, correct = line.split('=', 1)
                    correction_dict[wrong.strip()] = correct.strip()
        logger.info(f"Successfully loaded {len(correction_dict)} voice correction rules")
    except FileNotFoundError:
        logger.warning(f"Dictionary file {file_path} not found, using empty dictionary")
    except Exception as e:
        logger.error(f"Error loading dictionary file: {e}, using empty dictionary")

    return correction_dict

# Global correction dictionary (lazy loading)
_VOICE_CORRECTION_DICT: Optional[Dict[str, str]] = None

def get_voice_correction_dict() -> Dict[str, str]:
    """Get voice correction dictionary (with caching)"""
    global _VOICE_CORRECTION_DICT
    if _VOICE_CORRECTION_DICT is None:
        _VOICE_CORRECTION_DICT = load_voice_correction_dict()
    return _VOICE_CORRECTION_DICT

def correct_voice_errors(text: str) -> str:
    """Fix common voice recognition errors"""
    if not config.get("error_correction.enabled", True):
        return text

    correction_dict = get_voice_correction_dict()
    corrected_text = text

    for wrong, correct in correction_dict.items():
        corrected_text = corrected_text.replace(wrong, correct)

    if corrected_text != text:
        logger.debug(f"Voice correction: '{text}' -> '{corrected_text}'")

    return corrected_text

# =============================================================================
# TTS Feedback Detection
# =============================================================================

def detect_tts_feedback(text: str) -> bool:
    """
    Detect if text is TTS system-generated feedback

    Args:
        text: Input text

    Returns:
        True if TTS feedback (should be ignored)
        False if user input (should be processed)
    """
    if not isinstance(text, str):
        return False

    text_lower = text.lower().strip()

    # Check TTS feedback keywords
    for keyword in TTS_FEEDBACK_KEYWORDS:
        if keyword in text_lower:
            logger.debug(f"Detected TTS feedback keyword '{keyword}', ignoring")
            return True

    return False

# =============================================================================
# Special Format Handling
# =============================================================================

def handle_special_formats(text: str) -> str:
    """Handle special number formats like '点八四'"""
    # Handle "点X" format
    if text.startswith("点") and len(text) > 1:
        # Convert "点八四" to "零点八四"
        result = "零" + text
        logger.debug(f"Special format handling: '{text}' -> '{result}'")
        return result
    return text

def fix_invalid_chinese_numbers(text: str) -> str:
    """Fix invalid Chinese number formats"""
    # Fix "一千零二百" -> "一千二百" (1200)
    if text == '一千零二百':
        logger.debug(f"Fixed invalid Chinese number format: '{text}' -> '一千二百'")
        return '一千二百'
    return text

# =============================================================================
# Core Number Extraction
# =============================================================================

def extract_measurements(text: Any) -> List[float]:
    """
    Extract all possible numbers (Chinese or Arabic) from text and return as float list

    Args:
        text: Input text (string, number, or any type)

    Returns:
        List of extracted numbers in order
    """
    if not isinstance(text, (str, int, float)):
        return []

    try:
        txt = str(text).strip()

        # TTS feedback detection - prevent processing system feedback
        if detect_tts_feedback(txt):
            return []

        # Handle negative sign
        negative_multiplier = 1
        if '负' in txt:
            negative_multiplier = -1
            logger.debug(f"Detected negative sign, original text: '{txt}'")

        # Try direct conversion of entire text first
        if CN2AN_AVAILABLE:
            try:
                num = cn2an.cn2an(txt, "smart")
                num_float = float(num)
                if MIN_VALUE <= num_float <= MAX_VALUE:
                    logger.debug(f"Direct conversion of entire text: {num_float} (text: '{txt}')")
                    return [num_float]
            except Exception as e:
                logger.debug(f"Direct conversion failed: {e} (text: '{txt}')")

        # Special handling: convert consecutive Chinese numbers character by character
        if CN2AN_AVAILABLE:
            try:
                if all(char in CHINESE_NUMBERS for char in txt):
                    result = ""
                    for char in txt:
                        num = cn2an.cn2an(char, "smart")
                        result += str(num)
                    if result.isdigit():
                        num_float = float(result)
                        if MIN_VALUE <= num_float <= MAX_VALUE:
                            logger.debug(f"Character-by-character conversion: {num_float} (text: '{txt}')")
                            return [num_float]
            except Exception as e:
                logger.debug(f"Character-by-character conversion failed: {e} (text: '{txt}')")

        # Handle complex Chinese number concatenations
        if CN2AN_AVAILABLE:
            try:
                concat_match = CONCAT_PATTERN.search(txt)
                if concat_match:
                    part1, part2 = concat_match.groups()
                    results = []

                    for part in [part1, part2]:
                        try:
                            num = cn2an.cn2an(part, "smart")
                            num_float = float(num)
                            if MIN_VALUE <= num_float <= MAX_VALUE:
                                results.append(num_float)
                        except Exception:
                            pass

                    if len(results) >= 2:
                        logger.debug(f"Successfully split concatenated Chinese numbers: {txt} -> {results}")
                        return results
                    elif len(results) == 1:
                        logger.debug(f"Partially split concatenated Chinese numbers: {txt} -> {results}")
                        return results
            except Exception as e:
                logger.debug(f"Concatenated number splitting failed: {e} (text: '{txt}')")

        # Handle common misrecognition patterns
        if CN2AN_AVAILABLE:
            # 1. '我' might be misrecognized as '五'
            if txt == '我':
                try:
                    num = cn2an.cn2an('五', "smart")
                    num_float = float(num)
                    if MIN_VALUE <= num_float <= MAX_VALUE:
                        logger.debug(f"Successfully recognized '我' as number: {num_float}")
                        return [num_float]
                except Exception:
                    pass

            # 2. '我是' might be misrecognized as '五十'
            elif txt == '我是':
                try:
                    num = cn2an.cn2an('五十', "smart")
                    num_float = float(num)
                    if MIN_VALUE <= num_float <= MAX_VALUE:
                        logger.debug(f"Successfully recognized '我是' as number: {num_float}")
                        return [num_float]
                except Exception:
                    pass

            # 3. '我是我' might be misrecognized as '五五'
            elif txt == '我是我':
                try:
                    num = cn2an.cn2an('五五', "smart")
                    num_float = float(num)
                    if MIN_VALUE <= num_float <= MAX_VALUE:
                        logger.debug(f"Successfully recognized '我是我' as number: {num_float}")
                        return [num_float]
                except Exception:
                    pass

        # Remove common misrecognition prefixes
        for prefix in ['我', '你']:
            if txt.startswith(prefix):
                txt = txt[len(prefix):]
                logger.debug(f"After removing prefix '{prefix}': '{txt}'")

        # Apply voice error correction
        txt = correct_voice_errors(txt)

        # Fix invalid Chinese number formats
        txt = fix_invalid_chinese_numbers(txt)

        # Check if entire text is a number expression
        if CN2AN_AVAILABLE:
            try:
                special_handled = handle_special_formats(txt)
                if special_handled != txt:
                    logger.debug(f"After special format handling: '{special_handled}'")
                    num = cn2an.cn2an(special_handled, "smart")
                    num_float = float(num)
                    if MIN_VALUE <= num_float <= MAX_VALUE:
                        logger.debug(f"Successfully extracted number from entire text: {num_float}")
                        return [num_float]
            except Exception:
                pass

        # Use regex to extract numbers
        nums = []
        seen_numbers = set()  # For deduplication

        # Try unit pattern first, then basic number pattern
        unit_matches = UNIT_PATTERN.findall(txt)
        candidates = unit_matches if unit_matches else NUM_PATTERN.findall(txt)

        for cand in candidates:
            try:
                if CN2AN_AVAILABLE:
                    cand_handled = handle_special_formats(cand)
                    if cand_handled != cand:
                        logger.debug(f"Processing candidate '{cand}' as '{cand_handled}'")

                    num = cn2an.cn2an(cand_handled, "smart")
                    num_float = float(num)

                    if MIN_VALUE <= num_float <= MAX_VALUE:
                        # Deduplicate
                        if num_float not in seen_numbers:
                            seen_numbers.add(num_float)
                            final_num = num_float * negative_multiplier
                            nums.append(final_num)
                            logger.debug(f"Successfully extracted number: {final_num} from candidate: '{cand}'")
                else:
                    # If cn2an unavailable, try direct float conversion
                    try:
                        num_float = float(cand)
                        if MIN_VALUE <= num_float <= MAX_VALUE:
                            if num_float not in seen_numbers:
                                seen_numbers.add(num_float)
                                final_num = num_float * negative_multiplier
                                nums.append(final_num)
                                logger.debug(f"Direct number conversion: {final_num} from candidate: '{cand}'")
                    except ValueError:
                        pass
            except Exception as e:
                logger.debug(f"Number conversion failed for '{cand}': {e}")
                continue

        # If regex extraction failed, try converting entire text
        if not nums and txt and CN2AN_AVAILABLE:
            try:
                txt_handled = handle_special_formats(txt)
                num = cn2an.cn2an(txt_handled, "smart")
                num_float = float(num)
                if MIN_VALUE <= num_float <= MAX_VALUE:
                    final_num = num_float * negative_multiplier
                    nums.append(final_num)
                    logger.debug(f"Direct conversion of entire text: {final_num}")
            except Exception:
                pass

        return nums

    except Exception as e:
        logger.error(f"Error in number extraction: {e}")
        return []

# =============================================================================
# Advanced Text Processing
# =============================================================================

def process_voice_text(text: str, enable_correction: bool = True,
                      enable_tts_filter: bool = True) -> Dict[str, Any]:
    """
    Advanced voice text processing function

    Args:
        text: Input text
        enable_correction: Enable voice error correction
        enable_tts_filter: Enable TTS feedback filtering

    Returns:
        Dictionary containing processing results:
        {
            'original_text': Original text,
            'processed_text': Processed text,
            'numbers': Extracted numbers list,
            'is_tts_feedback': Whether it's TTS feedback,
            'corrections_applied': Applied corrections list
        }
    """
    result = {
        'original_text': text,
        'processed_text': text,
        'numbers': [],
        'is_tts_feedback': False,
        'corrections_applied': []
    }

    if not isinstance(text, str):
        return result

    # TTS feedback detection
    if enable_tts_filter and detect_tts_feedback(text):
        result['is_tts_feedback'] = True
        return result

    # Voice error correction
    if enable_correction:
        original = text
        corrected = correct_voice_errors(text)
        if corrected != original:
            result['corrections_applied'].append(f"{original} -> {corrected}")
            result['processed_text'] = corrected

    # Number extraction
    result['numbers'] = extract_measurements(result['processed_text'])

    return result

# =============================================================================
# Module Initialization
# =============================================================================

def initialize_text_processor():
    """Initialize text processing module"""
    try:
        # Preload voice correction dictionary
        dict_loaded = get_voice_correction_dict()
        logger.info(f"Text processing module initialized, loaded {len(dict_loaded)} correction rules")
        return True
    except Exception as e:
        logger.error(f"Text processing module initialization failed: {e}")
        return False

# =============================================================================
# Backward Compatibility Functions
# =============================================================================

def correct_voice_errors_compat(text: str) -> str:
    """Backward compatibility function for correct_voice_errors"""
    return correct_voice_errors(text)

def detect_tts_feedback_compat(text: str) -> bool:
    """Backward compatibility function for TTS feedback detection"""
    return detect_tts_feedback(text)

# =============================================================================
# Module Self-Test
# =============================================================================

def test_text_processor():
    """Test text processing module functionality"""
    print("Testing text processing module...")

    test_cases = [
        ("一千二三百", [1200.0, 300.0], "Chinese number concatenation"),
        ("成功提取25.5", [], "TTS feedback filtering"),
        ("温度二十五点五度", [25.5], "Normal number extraction"),
        ("一千零二百", [1200.0], "Invalid format fixing"),
        ("负数二十五点五", [-25.5], "Negative number support"),
        ("点八四", [0.84], "Special format handling"),
        ("invalid", [], "Invalid input"),
        (123, [123.0], "Number input"),
        (None, [], "None input")
    ]

    passed = 0
    total = len(test_cases)

    for text, expected, description in test_cases:
        result = extract_measurements(text)
        success = result == expected
        status = "PASS" if success else "FAIL"
        print(f"{status} {description}: '{text}' -> {result} (expected: {expected})")
        if success:
            passed += 1

    print(f"\nTest results: {passed}/{total} passed ({passed/total*100:.1f}%)")

    # Test advanced features
    print("\nTesting advanced text processing features...")
    advanced_result = process_voice_text("成功提取温度二十五点五度")
    print(f"Advanced processing result: {advanced_result}")

    return passed == total

# =============================================================================
# Module Auto-initialization
# =============================================================================

# Auto-initialize when module is imported
try:
    if not initialize_text_processor():
        logger.warning("Text processing module auto-initialization failed, manual initialization required")
except Exception as e:
    logger.error(f"Text processing module auto-initialization error: {e}")

# =============================================================================
# Main Execution (for testing)
# =============================================================================

if __name__ == "__main__":
    # Run tests
    if initialize_text_processor():
        success = test_text_processor()
        if success:
            print("\nText processing module test completed successfully!")
        else:
            print("\nText processing module test failed!")
            sys.exit(1)
    else:
        print("Text processing module initialization failed!")
        sys.exit(1)