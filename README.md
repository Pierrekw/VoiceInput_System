# 🎤 Voice Input System

A powerful real-time voice recognition system with pause/resume functionality and automatic Excel export capabilities.

## 🌟 Features

### 🎯 Core Features
- **Real-time Voice Recognition**: Continuous speech-to-text conversion using Vosk
- **Pause/Resume Control**: Smart state management with space bar and voice commands
- **Automatic Excel Export**: Data automatically saved to Excel on pause/stop
- **Bilingual Number Recognition**: Supports both Chinese and Arabic numerals

### 🎮 Control Methods
#### Keyboard Controls
- **Space Bar**: Start/Pause/Resume (cycle control)
- **ESC Key**: Stop and exit

#### Voice Commands
- **"开始录音" / "启动" / "开始"**: Start system
- **"暂停录音" / "暂停"**: Pause recording
- **"继续录音" / "继续" / "恢复"**: Resume recording
- **"停止录音" / "停止" / "结束"**: Stop system

## 🚀 Quick Start

### Prerequisites
```bash
# Install dependencies
uv pip install -r requirements.txt
# or
pip install -r requirements.txt
```

### Basic Usage
```bash
# Start the system
python main.py
```

## 📁 Project Structure

```
Voice_Input/
├── main.py                    # Main entry point
├── audio_capture_v.py         # Audio capture and recognition
├── excel_exporter.py          # Excel export functionality
├── New_method.py             # State machine reference
├── voice_correction_dict.txt  # Voice error corrections
├── model/                    # Vosk voice models
│   ├── cn/                   # Chinese model
│   ├── cns/                  # Chinese small model
│   ├── us/                   # English model
│   └── uss/                  # English small model
└── requirements.txt          # Dependencies
```

## ⚙️ Configuration

### Model Selection
```python
# Default: Chinese standard model
model_path="model/cn"

# Options:
# - "model/cn"   : Chinese standard (high accuracy)
# - "model/cns"  : Chinese small (fast loading)
# - "model/us"   : English standard
# - "model/uss"  : English small
```

## 🧪 Testing

### Run Integration Tests
```bash
# Test AudioCapture functionality
python integration_test.py

# Test main system workflow
python test_main_full_system.py
```

## 📊 Usage Examples

### Basic Voice Input
```
User says: "温度二十五点五度"
System recognizes: temperature 25.5 degrees
Excel output:| ID | Value | Timestamp |
          |  1   |  25.5  | 2024-... |
```

### Voice Commands
```
User says: "暂停录音"
System response: ⏸️ Paused recognition
         📝 Writing X records to Excel...
         ✅ Excel write successful
```

## 🔧 Advanced Features

### Voice Error Correction
The system includes automatic voice error correction via `voice_correction_dict.txt`

### Model Configuration
Supports multiple Vosk models for different languages and accuracy requirements

### Data Buffering
Uses deque for efficient circular buffering of measurement data

## 🚨 Error Handling

### Model Loading Errors
```
❌ Model loading failed: [error details]
💡 Please check:
   1. Model path is correct: model/cn
   2. Model files exist and are complete
   3. Model files are compatible with current VOSK version
```

## 📈 Performance

- **Real-time Processing**: Low latency voice recognition
- **Memory Efficient**: Circular buffer prevents memory leaks
- **Auto-cleanup**: Automatic resource management

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Vosk](https://alphacephei.com/vosk/) for voice recognition engine
- [pandas](https://pandas.pydata.org/) for data manipulation
- [openpyxl](https://openpyxl.readthedocs.io/) for Excel handling
- [pynput](https://pypi.org/project/pynput/) for keyboard monitoring

---

## 📞 Support

For issues and questions, please create an issue in the GitHub repository.

**Happy Voice Recognition!** 🎤✨
