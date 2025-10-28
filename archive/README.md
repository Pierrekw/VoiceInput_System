# Archive 目录

此目录包含从项目根目录清理出来的Python文件。

## 📁 文件分类

### 🔄 旧版本和替代文件
- `funasr_voice_module.py` - 原版FunASR模块，已被TEN VAD版本替代
- `funasr_voice_module_onnx.py` - ONNX版本，当前未使用
- `funasr_voice_Silero.py` - Silero VAD版本，已被TEN VAD版本替代
- `voice_gui_refractor.py` - 重构版GUI，功能已整合到主GUI中

### 🐛 调试和性能工具
- `debug_gui_issues.py` - GUI问题调试工具
- `debug_performance_tracker.py` - 性能调试工具
- `performance_optimizer.py` - 性能优化工具
- `production_latency_logger.py` - 生产环境延迟日志
- `audio_performance_optimizer.py` - 音频性能优化工具

### 🔧 配置和演示文件
- `setup.py` - 项目安装脚本
- `demo_paraformer_onnx_online.py` - 演示文件
- `export_paraformer_onnx.py` - ONNX模型导出工具
- `TTSengine.py` - 语音合成引擎（当前未使用）

### 📊 其他文件
- `integration_test.log` - 集成测试日志
- `measurement_data.xlsx` - 测量数据
- `voice_input_funasr.log` - 语音输入日志

## ⚠️ 注意事项

这些文件已经从主项目中移除，但被保留以备将来参考。
如果需要重新使用某个文件，请先评估其与当前项目的兼容性。

## 📅 清理日期
2025-10-26 - 项目规范化清理