# 🎤 FunASR语音输入系统

一个功能强大的离线实时中文语音识别系统，集成数字转换、Excel导出和文本转语音反馈功能。

## 📚 项目简介
这是一个专为中文语音识别设计的系统，使用FunASR引擎提供高精度识别，支持实时记录测量数据并自动导出到Excel表格。系统具有智能控制、专业数据处理和完整的日志记录功能。

## 🌟 核心特性

### 🎯 功能亮点
- **高精度中文语音识别**：基于FunASR 1.2.7引擎
- **智能数字转换**：准确识别中文数字并转换为阿拉伯数字（如"三十七点五"→"37.5"）
- **智能序号识别**：自动识别序号上下文（如"序号二百"→"序号200"）
- **Excel自动导出**：纯数字结果自动保存到结构化Excel文件
- **完整日志记录**：所有识别结果详细记录便于追溯
- **灵活控制方式**：支持语音命令和键盘快捷键操作

### 🎮 控制方法
#### 键盘控制
- **空格键**：暂停/恢复录音
- **ESC键**：停止并退出系统

#### 语音命令
- **"暂停录音" / "暂停"**：暂停录音
- **"继续录音" / "继续" / "恢复"**：恢复录音
- **"停止录音" / "停止" / "结束"**：停止系统

## 🚀 快速开始

### 安装依赖
```bash
# 使用uv
uv pip install -r requirements.txt

# 或使用pip
pip install -r requirements.txt
```

### 运行系统

#### 生产模式（推荐日常使用）
```bash
python start_funasr.py
```

#### Debug模式（开发和调试）
```bash
python main_f.py --debug
# 或
python main_f.py -d
```

## 📊 输出说明

### 输出文件
- **Excel报告**：保存到`./reports/report_yyyymmdd_hhmmss.xlsx`
- **识别日志**：保存到`./logs/voice_recognition_yyyymmdd_hhmmss.log`

### 输出格式
- **Excel列**：编号、测量值、时间戳、原始语音
- **Production模式显示**：`1: 37.5`（简洁格式）
- **Debug模式显示**：完整的识别和转换过程

## 🔧 项目结构

```
Voice_Input/
├── main_f.py                   # 主程序（支持debug模式）
├── start_funasr.py            # 生产模式快速启动
├── funasr_voice_module.py     # FunASR语音识别模块
├── text_processor_clean.py     # 文本处理和数字转换模块
├── excel_exporter.py          # Excel导出模块
├── requirements.txt            # 项目依赖
├── reports/                    # Excel报告目录
├── logs/                       # 日志文件目录
└── FunASR_Deployment/         # 部署相关文件
```

## 🛠️ 技术栈

- **语音识别**: FunASR 1.2.7 + ModelScope 1.31.0
- **数字转换**: cn2an 0.5.23
- **音频处理**: PyAudio 0.2.14
- **Excel导出**: openpyxl 3.1.5 + pandas 2.3.2
- **开发工具**: Python 3.11.11 + mypy 1.18.2

## 📄 许可证

该项目根据MIT许可证授权 - 详见LICENSE文件。

## 📚 文档

- **README.md**: 项目概述和使用说明（当前文件）
- **DevelopmentRecord.MD**: 详细开发记录和技术实现
- **FunASR_USAGE_GUIDE.md**: FunASR使用指南

**状态**：✅ 生产就绪 | **版本**：v1.0.0

**Happy Voice Recognition!** 🎤✨
