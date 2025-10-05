# Shared Text Processing Module Guide

## Overview
This document describes the consolidated text processing module that enables both the original synchronous system and the new asynchronous system to use the same text processing functionality. The module has been consolidated into a single file for simplicity and maintainability.

## Architecture

### Module Structure
```
text_processor.py           # Consolidated shared module with all functionality
audio_capture_v.py          # Original system (uses shared module)
main_production.py          # New async system (uses shared module via audio_capture_v)
```

### Key Features
- **Chinese Number Concatenation**: "一千二三百" → [1200.0, 300.0]
- **TTS Feedback Prevention**: Filters out system-generated audio
- **Voice Error Correction**: Configurable dictionary-based corrections
- **Special Format Handling**: "点八四" → 0.84
- **Negative Number Support**: "负数二十五点五" → -25.5
- **Invalid Format Fixing**: "一千零二百" → 1200.0
- **Backward Compatibility**: Maintains compatibility with existing code

## Usage

### For Original System (audio_capture_v.py)
The original system automatically uses the shared module through conditional imports:
```python
# In audio_capture_v.py
try:
    from text_processor import extract_measurements, correct_voice_errors
    SHARED_TEXT_PROCESSOR_AVAILABLE = True
except ImportError:
    SHARED_TEXT_PROCESSOR_AVAILABLE = False
    # Fallback to built-in implementation
```

### For New Async System (main_production.py)
The new system imports from audio_capture_v, which automatically uses the shared module:
```python
# In main_production.py
from audio_capture_v import extract_measurements
```

### Direct Usage (for testing or new implementations)
```python
# Basic functions
from text_processor import extract_measurements, correct_voice_errors

# Advanced processing
from text_processor import process_voice_text, detect_tts_feedback

# Backward compatibility functions
from text_processor import correct_voice_errors_compat, detect_tts_feedback_compat
```

## Testing

### Test Module
```bash
python text_processor.py
```

### Test Integration
```bash
# Test original system
python -c "from audio_capture_v import extract_measurements; print(extract_measurements('一千二三百'))"

# Test new system
python -c "from main_production import extract_measurements; print(extract_measurements('一千二三百'))"

# Test advanced features
python -c "from text_processor import process_voice_text; print(process_voice_text('成功提取温度二十五点五度'))"
```

## Fallback Mechanism

If the shared module is not available, the system automatically falls back to a basic implementation that:
- Uses simple regex for number extraction
- Skips TTS feedback detection
- Provides basic error correction
- Maintains core functionality

## Benefits

1. **Maintainability**: Single consolidated module for all text processing logic
2. **Simplicity**: One file to maintain and update
3. **Consistency**: Both old and new systems behave identically
4. **Extensibility**: Easy to add new features or fix bugs
5. **Backward Compatibility**: Original system continues to work
6. **Testing**: Centralized testing of text processing functionality
7. **Performance**: Shared optimizations benefit both systems

## Configuration

The shared module respects the same configuration settings as the original system:
- `error_correction.enabled`: Enable/disable error correction
- `error_correction.dictionary_path`: Path to correction dictionary
- All other configuration options from config_loader.py

## Error Handling

The shared module includes comprehensive error handling:
- Graceful fallback when cn2an is unavailable
- TTS feedback detection to prevent loops
- Input validation and sanitization
- Detailed logging for debugging

## Consolidation Changes

The module architecture was consolidated from two files (`text_processor.py` and `text_processor_adapter.py`) into a single `text_processor.py` file to:
- Reduce complexity
- Eliminate redundant code
- Simplify maintenance
- Improve performance
- Reduce potential for inconsistencies

## Future Improvements

This architecture enables easy future improvements:
- Enhanced Chinese number parsing algorithms
- Machine learning-based error correction
- Multi-language support
- Performance optimizations
- New text processing features

All improvements will automatically benefit both the original and new systems.