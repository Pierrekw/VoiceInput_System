# Voice Input System - Change Log

## v1.2.0 - Current Release
**Date**: October 5, 2025
**Status**: Production Ready ✅

### ✅ 文本处理模块统一化
### ✅ Text Processing Module Unification
- **共享模块**: 新老版本共用统一文本处理逻辑 (`text_processor.py`)
- **模块整合**: 将多个文本处理模块整合为单一模块，降低复杂度
- **向后兼容**: 保持与原始系统的完全兼容性
- **持续改进**: 为后续语音识别准确率优化奠定基础
- **功能完整**: 包含中文数字提取、TTS反馈检测、语音错误纠正等所有功能

### 🔧 技术改进
### 🔧 Technical Improvements
- **架构简化**: 从多模块架构简化为单一统一模块
- **性能优化**: 移除不必要的抽象层，提升处理效率
- **维护简化**: 单一入口点，便于后续功能增强和bug修复
- **测试集中**: 所有文本处理测试集中在单一模块

### 🧪 测试增强
### 🧪 Testing Enhancements
- **模块自检**: 新增 `text_processor.py` 自检功能
- **集成验证**: 验证新旧系统使用统一模块的正确性
- **性能基准**: 建立文本处理性能基准测试
- **兼容性测试**: 确保向后兼容性不受影响

## v1.1.0
**Date**: September 27, 2025
**Status**: Production Ready ✅

### ✅ Completed Features
- **Enhanced Pause/Resume System**: Space key cycling (start/pause/resume)
- **Voice Command Integration**: Voice-based control commands
- **Unified State Management**: Consolidated state machine (idle/recording/paused/stopped)
- **Automatic Excel Export**: Seamless data writing with timestamps
- **Voice Error Correction**: Customizable dictionary for recognition fixes
- **Professional Excel Formatting**: Auto-numbering, headers, column formatting
- **Comprehensive Test Suite**: 18/18 tests passing
- **Special Number Sequence Handling**: Added support for "一二三四五六七八九十" as a single number 1234567890

### 🔧 Technical Improvements
- **Modular Architecture**: Clean separation of concerns
- **Thread Safety**: Proper locking mechanisms
- **Memory Management**: Automatic resource cleanup
- **Error Handling**: Comprehensive exception handling
- **Logging System**: Detailed operation logging
- **Improved Text-to-Number Conversion**: Fixed regex escape sequences and enhanced Chinese number handling

### 🧪 Test Suite Updates
- **Fixed Integration Tests**: Updated test_main_integration.py for new API
- **Static Method Fixes**: Corrected ExcelExporter method decorators
- **Attribute Access**: Fixed timeout_seconds access patterns
- **Callback Integration**: Proper callback setup verification

## v1.0.0 - Initial Release
**Date**: September 27, 2025
**Status**: Basic functionality implemented

### Initial Features
- Basic voice recognition with Vosk
- Simple pause/resume functionality
- Excel export capability
- Keyboard controls (space/ESC)

---
*Last Updated: October 5, 2025*

## ⚠️ Current Limitations
- **Negative Numbers**: Currently not supported (returns empty list for texts with negative numbers like "负数二十五点五")