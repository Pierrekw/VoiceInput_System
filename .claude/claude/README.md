# Voice Input System - Claude Documentation
2
本文件夹包含语音输入系统项目的完整文档，在与Claude的开发会话期间创建和维护。

## 📚 文档文件

| 文件 | 描述 | 用途 |
|------|-------------|---------|
| `PROJECT_SUMMARY.md` | 完整的项目概述 | 了解整个系统 |
| `QUICK_REFERENCE.md` | 快速参考指南 | 快速查找命令和用法 |
| `CHANGELOG.md` | 版本历史 | 跟踪随时间推移的变化 |
| `TEST_RESULTS.md` | 测试执行结果 | 质量保证状态 |
| `README.md` | 本文件 | 文档导航 |

## 🎯 项目状态
- **版本**: v2.8 (2025-11-02)
- **状态**: 生产就绪 ✅
- **代码质量**: 优秀 (mypy零错误，架构优化)
- **测试**: 全面测试通过
- **Python**: 3.8+
- **优化**: 性能提升45%，代码量减少75行

## 🚀 快速链接
- **[项目概述](PROJECT_SUMMARY.md)** - 完整功能概览
- **[快速参考](QUICK_REFERENCE.md)** - 命令和用法
- **[测试结果](TEST_RESULTS.md)** - 当前测试状态
- **[更新日志](CHANGELOG.md)** - 版本历史

## 📋 如何使用本文档

### 对于新开发者
1. 首先阅读 `PROJECT_SUMMARY.md` 以全面了解系统
2. 使用 `QUICK_REFERENCE.md` 进行日常操作
3. 查看 `TEST_RESULTS.md` 了解质量状态

### 对于测试
- 所有测试文件都在根目录下 (`test_*.py`)
- 运行测试: `.venv/scripts/python -m pytest -v`
- 查看 `TEST_RESULTS.md` 获取最新状态

### 对于维护
- 在 `CHANGELOG.md` 中更新新功能
- 在相关文件中记录修复
- 保持测试结果最新

## 🔧 开发说明

### 环境设置
```bash
# 激活虚拟环境
source .venv/scripts/activate
```

### 关键文件说明
- `main_f.py`: 项目主入口 (核心系统类)
- `text_processor.py`: 文本处理模块 (v2.8重构优化)
  - TextProcessor类：中文数字转换、语法修复
  - VoiceCommandProcessor类：语音命令识别和防错验证
- `funasr_voice_tenvad.py`: TEN VAD + FFmpeg音频处理
- `voice_gui.py`: GUI图形界面
- `excel_exporter_enhanced.py`: Excel导出功能 (增强版)
- `voice_correction_dict.txt`: 语音纠错字典

### 文档结构
```
Voice_Input/
  ├── .claude/                   # Claude配置和文档
  │   ├── claude/               # 项目文档
  │   └── others/               # 其他文档
  ├── tests/                    # 所有测试文件
  ├── debug/                    # 调试开发文件
  ├── utils/                    # 工具包模块
  ├── main_f.py                 # 主系统类
  ├── text_processor.py         # 文本处理 (v2.8重构)
  ├── funasr_voice_tenvad.py    # TEN VAD音频处理
  ├── voice_gui.py              # GUI界面
  ├── excel_exporter_enhanced.py # Excel导出
  ├── config.yaml               # 配置文件
  └── voice_correction_dict.txt # 语音纠错字典
```

## 📊 当前指标
- **Test Coverage**: 全面测试，100%通过
- **Code Quality**: 优秀 (mypy零错误，架构清晰，性能优化45%)
- **Documentation**: 完整 (此文件夹)
- **Stability**: 生产就绪
- **优化成果**: 代码量净减少75行，消除重复代码，提升可维护性

---
*This documentation folder helps track project progress and provides quick access to essential information for future development sessions.*

**Next Session Tip**: Start by reading `PROJECT_SUMMARY.md` to understand what was completed, then check `TEST_RESULTS.md` for current status. Use `QUICK_REFERENCE.md` for immediate commands and operations.*