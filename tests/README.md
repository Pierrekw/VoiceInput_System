# 测试文件目录

本目录包含项目的所有测试文件，用于验证系统功能的正确性和稳定性。

## 📋 测试文件列表

### 核心功能测试
- **`test_text_processor_refactor.py`** - 文本处理器重构测试 ⭐
  - 验证TextProcessor新增方法
  - 测试VoiceCommandProcessor功能
  - 检查向后兼容性
  - 验证与main_f.py的集成

### 基础功能测试
- **`test_funasr.py`** - FunASR核心功能测试
- **`test_improvements.py`** - 功能改进测试
- **`test_original_method.py`** - 原始方法对比测试

### 性能测试 (v2.5更新)
- **`test_performance.py`** - 性能测试 (从根目录移动)
- **`test_debug_performance.py`** - 性能调试测试 (从根目录移动)
- **`test_production_latency.py`** - 生产环境延迟测试
- **`test_gui_cache_fix.py`** - GUI缓存修复测试

### 功能专项测试 (v2.5更新)
- **`test_ffmpeg_preprocessing.py`** - FFmpeg预处理测试 (从根目录移动)
- **`test_vad_comparison.py`** - VAD对比测试 (从根目录移动)
- **`test_excel_functionality.py`** - Excel功能测试
- **`test_start_options.py`** - 启动选项测试

### 问题修复测试
- **`test_chinese_number_errors.py`** - 中文数字错误修复测试
- **`test_text_fixes.py`** - 文本修复测试
- **`test_voice_command_sync.py`** - 语音命令同步测试

### 集成测试
- **`text_funasr_IntegrationTest.py`** - FunASR集成测试
- **`integrated_test.py`** - 综合集成测试

## 🚀 运行测试

### 运行单个测试 (v2.5更新)
```bash
# 📊 核心功能测试
python tests/test_text_processor_refactor.py
python tests/test_funasr.py
python tests/test_improvements.py

# 🔍 性能和调试测试 (从根目录移动)
python tests/test_performance.py
python tests/test_debug_performance.py

# 🔧 功能专项测试 (从根目录移动)
python tests/test_ffmpeg_preprocessing.py
python tests/test_vad_comparison.py
python tests/test_excel_functionality.py

# 🧪 集成测试
python tests/integrated_test.py
```

### 从项目根目录运行
```bash
# 进入项目根目录
cd F:\04_AI\01_Workplace\Voice_Input

# 运行重构测试
python tests/test_text_processor_refactor.py

# 运行核心功能测试
python tests/test_funasr.py
```

## 📊 测试覆盖范围

### ✅ 已覆盖功能
- **文本处理**: 中文数字转换、文本清理、相似度计算
- **语音命令**: 模糊匹配、多语言支持、智能过滤
- **系统集成**: Excel导出、配置加载、错误处理
- **向后兼容**: 原有接口、功能保持、性能无影响
- **类型安全**: MyPy类型检查、严格模式验证

### 🎯 重点测试
**`test_text_processor_refactor.py`** 是最重要的测试文件，它验证了：
1. **重构成功**: 新功能正常工作
2. **兼容性**: 原有功能没有破坏
3. **集成性**: 与主系统完美整合
4. **类型安全**: 通过严格的类型检查

## 🔧 测试开发指南

### 添加新测试
1. 在相应的测试文件中添加测试函数
2. 遵循现有的命名规范和结构
3. 确保测试的独立性和可重复性
4. 添加适当的断言和错误处理

### 测试命名规范
- 测试函数以 `test_` 开头
- 描述性的函数名称
- 包含测试目的和预期结果

### 测试最佳实践
- 使用清晰的测试数据
- 测试边界条件和异常情况
- 保持测试代码的简洁和可读性
- 定期运行测试确保代码质量

## 📈 测试报告

所有测试都应该通过，如果遇到测试失败：

1. **检查环境**: 确保依赖项正确安装
2. **查看日志**: 分析错误信息和堆栈跟踪
3. **检查配置**: 确认配置文件正确
4. **隔离问题**: 使用单个测试文件定位问题

## 🎉 测试状态

## 📋 更新日志 (v2.5)

### 2025-10-26 - 测试文件整理
✅ **完成的改进:**
- 将4个根目录的test文件移动到tests/目录
- 统一测试文件命名规范 (test_*.py)
- 更新项目规则文档中的测试命令
- 更新测试说明文档

📁 **移动的文件:**
- `debug_performance_test.py` → `tests/test_debug_performance.py`
- `performance_test.py` → `tests/test_performance.py`
- `test_ffmpeg_preprocessing.py` → `tests/test_ffmpeg_preprocessing.py`
- `vad_comparison_test.py` → `tests/test_vad_comparison.py`

🔧 **更新的文档:**
- `.claude/project_rules.md` - 更新测试文件列表和命令
- `tests/README.md` - 更新测试文件说明和运行指南
- `performance_optimizer.py` - 更新测试命令引用

✨ **新增测试类别:**
- 性能和调试测试
- 功能专项测试

## 🎉 测试状态

- ✅ **所有测试通过** (2025-10-22)
- ✅ **MyPy类型检查通过**
- ✅ **向后兼容性验证通过**
- ✅ **集成测试通过**

---

**注意**: 测试文件设计为独立运行，无需特殊的测试框架，直接使用Python执行即可。