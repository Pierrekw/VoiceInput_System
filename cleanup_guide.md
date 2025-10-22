# 📁 文件清理指南

## 🎯 核心系统文件 (必须保留)

### 主要功能模块
- ✅ `main_f.py` - 主系统控制器
- ✅ `funasr_voice_module.py` - 核心语音识别引擎
- ✅ `text_processor_clean.py` - 文本处理模块
- ✅ `excel_exporter.py` - Excel导出功能
- ✅ `config_loader.py` - 配置管理
- ✅ `performance_monitor.py` - 性能监控

### GUI界面
- ✅ `stable_gui.py` - 稳定版GUI (推荐使用)
- ✅ `voice_gui.py` - 原版GUI
- ✅ `start_voice_gui.py` - GUI启动器

### 启动入口
- ✅ `start_funasr.py` - 命令行启动脚本

### 配置文件
- ✅ `config.yaml` - 主配置文件

## 🧪 开发测试文件 (可删除)

### 小数问题调试文件 (已解决问题)
- ❌ `test_decimal_precision.py` - 小数精度测试
- ❌ `test_voice_decimal.py` - 语音小数测试
- ❌ `decimal_precision_fix.py` - 小数修复方案
- ❌ `debug_vad_decimal_issue.py` - VAD问题调试
- ❌ `test_decimal_fix.py` - 修复效果测试
- ❌ `smart_decimal_config.py` - 智能配置管理

### 其他调试文件
- ❌ `debug_text_processing.py` - 文本处理调试
- ❌ `diagnose_cache_issue.py` - 缓存问题诊断

## ⚠️ 暂时保留但可选的文件

### 性能优化相关 (根据需要保留)
- 🔄 `performance_optimizer.py` - 性能优化器
- 🔄 `audio_performance_optimizer.py` - 音频性能优化
- 🔄 `debug_performance_tracker.py` - 性能追踪调试
- 🔄 `production_latency_logger.py` - 延迟日志
- 🔄 `performance_test.py` - 性能测试

### 辅助工具
- 🔄 `setup_ffmpeg_env.py` - FFmpeg环境设置
- 🔄 `safe_funasr_import.py` - 安全导入模块
- 🔄 `debug_gui_issues.py` - GUI问题调试

## 🔧 问题修复总结

### ✅ 已解决: 小数点后3位限制问题

**问题原因**: VAD静音检测过早截断音频采集

**解决方案**:
- 修改 `config.yaml` 中的 VAD 自定义配置
- `min_silence_duration: 0.6s → 0.9s` (平衡方案)
- `speech_padding: 0.4s → 0.5s`
- `energy_threshold: 0.012 → 0.010`

**效果**:
- ✅ 支持小数点后4-6位数字
- ⚠️ 响应延迟增加0.3秒 (可接受)

### ⚠️ 需要修复: voice_gui.py 不支持 customized 模式

**问题**: GUI只支持 fast/balanced/accuracy 三种预设模式

**影响**: 无法通过GUI享受修复后的小数识别改进

## 🎯 推荐操作

### 1. 立即清理 (安全删除)
```bash
rm test_decimal_precision.py
rm test_voice_decimal.py
rm decimal_precision_fix.py
rm debug_vad_decimal_issue.py
rm test_decimal_fix.py
rm smart_decimal_config.py
rm debug_text_processing.py
rm diagnose_cache_issue.py
```

### 2. 保留备用 (可选)
性能优化文件可根据实际使用情况决定是否保留

### 3. 修复GUI支持
需要修改 `voice_gui.py` 以支持 customized VAD模式