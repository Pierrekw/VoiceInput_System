# FunASR语音输入系统

基于FunASR框架的中文语音识别系统，支持实时语音识别、文本处理和Excel数据导出功能。

## 🎯 主要特性

- **🎤 实时语音识别**: 基于FunASR的高精度中文语音识别
- **⏱️ 灵活时长控制**: 支持无限时模式和指定时长模式
- **🗣️ 智能语音命令**: 支持中英文语音控制（暂停、继续、停止）
- **📊 Excel自动导出**: 实时将识别结果写入Excel文件
- **🔧 配置化管理**: 所有参数可通过config.yaml灵活配置
- **🔄 音频异常恢复**: 自动重试机制，防止突然终止
- **📝 数字智能提取**: 自动识别和转换中文数字

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Windows操作系统
- 麦克风设备

### 安装依赖

```bash
pip install funasr torch pyaudio numpy openpyxl pyyaml
```

### 基本使用

1. **启动系统（推荐）**
   ```bash
   python start_funasr.py
   ```
   默认使用无限时模式，可以一直识别直到手动停止。

2. **指定识别时长**
   ```bash
   # 识别60秒后自动停止
   python start_funasr.py -d 60

   # 识别5分钟
   python start_funasr.py -d 300
   ```

3. **调试模式**
   ```bash
   python start_funasr.py --debug
   ```

4. **查看配置**
   ```bash
   python start_funasr.py --show-config
   ```

## 📋 使用说明

### 控制方式

- **键盘控制**:
  - `空格键`: 暂停/恢复识别
  - `ESC键`: 停止程序

- **语音命令**:
  - 暂停: "暂停"、"暂停录音"、"pause"、"暂停一下"
  - 继续: "继续"、"继续录音"、"resume"、"恢复"
  - 停止: "停止"、"停止录音"、"结束"、"stop"、"exit"

### 识别模式

| 模式 | 说明 | 配置 | 适用场景 |
|------|------|------|----------|
| 无限时模式 | 连续识别，手动停止 | `timeout_seconds: -1` | 会议记录、长时间录入 |
| 限时模式 | 指定时长后自动停止 | `timeout_seconds: 60` | 定时任务、短时录入 |

## ⚙️ 配置文件

主要配置在 `config.yaml` 文件中：

### 重要配置项

```yaml
# 识别配置
recognition:
  # ⚠️ 核心配置：识别时长
  timeout_seconds: -1  # -1=无限时模式，60=60秒自动停止

# 语音命令配置
voice_commands:
  pause_commands: ["暂停", "暂停录音", "pause"]
  resume_commands: ["继续", "继续录音", "resume"]
  stop_commands: ["停止", "停止录音", "stop", "exit"]
  config:
    match_mode: "fuzzy"  # 模糊匹配模式
    confidence_threshold: 0.8  # 命令识别置信度

# Excel导出配置
excel:
  file_name: "report"  # Excel文件基础名
  auto_export: true  # 自动导出
  formatting:
    header_language: "zh"  # 中文表头
    include_original: true  # 包含原文
```

### 完整配置说明

配置文件中包含详细注释，说明每个参数的作用和取值范围。修改配置后需要重启系统生效。

## 📊 数据导出

系统会自动将识别结果导出到Excel文件：

- **文件位置**: `reports/` 目录
- **文件命名**: `report_YYYYMMDD_HHMMSS.xlsx`
- **表头格式**:
  - 中文: `序号, 数值, 原文, 处理后文本, 时间`
  - 英文: `ID, Number, Original, Processed, Time`

### 特殊文本识别

系统支持特定词汇的自动识别和标记：

- **OK状态**: 识别到"好"、"可以"、"OK"等词汇时写入1.0
- **Not OK状态**: 识别到"不行"、"错误"、"NG"等词汇时写入0.0

## 🔧 高级功能

### 数字处理

系统智能处理中文数字：

- "一二三" → 123
- "三十五点六" → 35.6
- "一千二百三十四" → 1234

### 音频异常处理

- **自动重试**: 音频设备异常时自动重试3次
- **错误日志**: 详细记录音频流异常信息
- **设备兼容**: 支持多种音频设备

### 语音命令识别

- **模糊匹配**: 支持相似度计算，提高识别准确率
- **多语言**: 同时支持中文和英文命令
- **智能过滤**: 避免误识别短文本为命令

## 📁 项目结构

```
Voice_Input/
├── start_funasr.py          # 主启动脚本
├── main_f.py                # 核心系统类
├── funasr_voice_module.py   # FunASR识别模块
├── config_loader.py         # 配置加载器
├── text_processor_clean.py  # 文本处理模块
├── excel_exporter.py        # Excel导出模块
├── config.yaml             # 配置文件
├── model/                   # 模型文件目录
├── reports/                 # Excel输出目录
└── logs/                    # 日志文件目录
```

## 🛠️ 开发调试

### 查看日志

系统日志文件位于 `logs/` 目录：
- `voice_input_funasr.log`: 系统主日志
- `voice_recognition_YYYYMMDD_HHMMSS.log`: 识别详细日志

### 调试模式

```bash
# 启用调试模式查看详细信息
python start_funasr.py --debug

# 使用短时间进行快速测试
python start_funasr.py -d 10 --debug
```

### 配置测试

```bash
# 验证配置文件是否正确加载
python -c "from config_loader import config; print(config.get_timeout_seconds())"
```

## 🔍 常见问题

### Q: 系统在60秒后自动停止怎么办？
A: 修改 `config.yaml` 中的 `timeout_seconds: -1` 启用无限时模式。

### Q: 如何添加自定义语音命令？
A: 在 `config.yaml` 的 `voice_commands` 部分添加新词汇。

### Q: 识别准确率不高怎么办？
A:
1. 确保麦克风质量良好
2. 调整 `chunk_size` 参数
3. 增加 `encoder_chunk_look_back` 值

### Q: 如何更换识别语言？
A: 目前主要支持中文，英文识别需要更换相应的模型文件。

### Q: 系统占用内存过高怎么办？
A: 设置 `global_unload: true` 在识别完成后自动卸载模型。

## 📈 性能优化建议

1. **内存优化**: 对于低配置电脑，设置 `global_unload: true`
2. **速度优化**: 使用CUDA设备（如果有NVIDIA显卡）
3. **准确性优化**: 适当增加 `encoder_chunk_look_back` 值
4. **实时性优化**: 调整 `chunk_size` 参数

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目：

1. Bug报告和功能建议
2. 代码优化和性能改进
3. 文档完善和使用案例
4. 新功能开发和测试

## 📄 许可证

本项目采用Apache 2.0许可证，详见LICENSE文件。

## 📞 支持

如遇到问题，请：
1. 查看本文档的常见问题部分
2. 检查 `logs/` 目录下的日志文件
3. 提交Issue描述详细问题

---

**版本**: v2.1
**更新时间**: 2025年10月19日
**状态**: ✅ 稳定版本