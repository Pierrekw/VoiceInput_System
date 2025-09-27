# 🎤 Voice Input System

A powerful offline real-time voice recognition system with pause/resume functionality and automatic Excel export capabilities.

## 🌟 Features

### 🎯 Core Features
- **Real-time Voice Recognition**: Continuous speech-to-text conversion using Vosk
- **Pause/Resume Control**: Smart state management with space bar and voice commands
- **Automatic Excel Export**: Data automatically saved to Excel on pause/stop
- **Bilingual Number Recognition**: Supports both Chinese and Arabic numerals
- **Professional Excel Formatting**: Auto-numbering, timestamps, headers with proper formatting

### 🎮 Control Methods
#### Keyboard Controls
- **Space Bar**: Start/Pause/Resume (cycle control)
- **ESC Key**: Stop and exit

#### Voice Commands
- **"开始录音" / "启动" / "开始"**: Start system
- **"暂停录音" / "暂停"**: Pause recording
- **"继续录音" / "继续" / "恢复"**: Resume recording
- **"停止录音" / "停止" / "结束"**: Stop system

### 🔧 Technical Features
- **Unified State Management**: Clean state machine (idle/recording/paused/stopped)
- **Voice Error Correction**: Customizable dictionary for fixing recognition errors
- **Thread Safety**: Proper concurrent operation handling
- **Memory Management**: Automatic resource cleanup and garbage collection
- **Comprehensive Logging**: Detailed operation logs with file and console output

## 🚀 Quick Start

### Prerequisites
```bash
# Ensure virtual environment is activated
source .venv/scripts/activate  # Windows Git Bash
# or
.venv\Scripts\activate  # Windows Command Prompt
```

### Basic Usage
```bash
# Start the system
python main.py
```

### Testing
```bash
# Run all tests
python -m pytest -v

# Run specific test file
python -m pytest test_main_integration.py -v
```

## 📁 Project Structure

```
Voice_Input/
├── main.py                    # Main entry point
├── audio_capture_v.py         # Audio capture and recognition
├── excel_exporter.py          # Excel export functionality
├── claude/                    # Documentation folder
│   ├── PROJECT_SUMMARY.md     # Complete project overview
│   ├── QUICK_REFERENCE.md     # Quick commands reference
│   ├── TEST_RESULTS.md        # Test results and status
│   ├── CHANGELOG.md          # Version history
│   └── README.md             # Documentation navigation
├── test_*.py                  # Test files (7 test files)
├── voice_correction_dict.txt  # Voice error corrections
├── model/                     # Vosk voice models
│   ├── cn/                   # Chinese standard model
│   ├── cns/                  # Chinese small model
│   ├── us/                   # English standard model
│   └── uss/                  # English small model
├── pyproject.toml            # Project configuration
└── voice_input.log           # Runtime logs
```

## ⚙️ Configuration

### Model Selection
```python
# Configure in AudioCapture constructor
model_path="model/cn"   # Chinese standard (high accuracy)
model_path="model/cns"  # Chinese small (fast loading)
model_path="model/us"   # English standard
model_path="model/uss"  # English small
```

### Timeout Configuration
```python
# Set timeout for voice recognition
system = VoiceInputSystem(timeout_seconds=30)
```

## 🧪 Testing

### Test Results
- **Total Tests**: 18
- **Passing**: 18
- **Success Rate**: 100%
- **Coverage**: Comprehensive core functionality

### Run Tests
```bash
# Run all tests
python -m pytest -v

# Run integration tests
python -m pytest test_main_integration.py -v

# Run full system tests
python -m pytest test_main_full_system.py -v
```

### Test Files
- `integration_test.py` - Core functionality tests (5 tests)
- `test_main_full_system.py` - End-to-end workflow tests (6 tests)
- `test_main_integration.py` - Main system integration tests (7 tests)

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

### Excel Output Format
- **File**: `measurement_data.xlsx`
- **Columns**: 编号 (ID) | 测量值 (Value) | 时间戳 (Timestamp)
- **Features**: Auto-numbering, professional formatting, continuous IDs

## 🔧 Advanced Features

### Voice Error Correction
- **File**: `voice_correction_dict.txt`
- **Format**: `wrong_word=correct_word`
- **Purpose**: Fix common recognition errors automatically

### Data Buffering
- **Buffer**: Circular deque (10,000 records max)
- **Export**: Automatic on pause/stop
- **Thread Safety**: Proper locking mechanisms

### State Management
- **States**: idle → recording → paused → stopped
- **Transitions**: Space key cycles, voice commands, ESC stops
- **Safety**: Proper cleanup and resource management

## 🚨 Error Handling

### Model Loading Errors
```
❌ Model loading failed: [error details]
💡 Please check:
   1. Model path is correct: model/cn
   2. Model files exist and are complete
   3. Model files are compatible with current VOSK version
```

### Common Issues
- **PyAudio not found**: Install in virtual environment
- **Excel locked**: Close Excel file before writing
- **Memory issues**: Check buffer size and cleanup

## 📈 Performance

- **Real-time Processing**: Low latency voice recognition
- **Memory Efficient**: Circular buffer prevents memory leaks
- **Auto-cleanup**: Automatic resource management
- **Thread Safety**: Proper concurrent operation handling

## 🛠️ Development Environment

### Virtual Environment
```bash
# Python version: 3.11.11
# Activation: source .venv/scripts/activate
# Dependencies: See pyproject.toml
```

### Key Dependencies
- **pyaudio**: 0.2.14 - Audio capture
- **vosk**: 0.3.45 - Voice recognition
- **pandas**: 2.3.2 - Data manipulation
- **openpyxl**: 3.1.5 - Excel handling
- **pynput**: 1.8.1 - Keyboard monitoring
- **cn2an**: 0.5.23 - Chinese number conversion

## 📚 Documentation

### Claude Documentation
Complete documentation available in `claude/` folder:
- **Project Summary**: Complete feature overview
- **Quick Reference**: Commands and usage
- **Test Results**: Current test status
- **Changelog**: Version history

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Ensure all tests pass: `python -m pytest -v`
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Vosk](https://alphacephei.com/vosk/) for voice recognition engine
- [pandas](https://pandas.pydata.org/) for data manipulation
- [openpyxl](https://openpyxl.readthedocs.io/) for Excel handling
- [pynput](https://pypi.org/project/pynput/) for keyboard monitoring
- [cn2an](https://pypi.org/project/cn2an/) for Chinese number conversion

---

## 📞 Support

For issues and questions:
1. Check `voice_input.log` for error details
2. Review documentation in `claude/` folder
3. Run tests to verify functionality
4. Create issue in GitHub repository

**Status**: ✅ Production Ready | **Tests**: 18/18 Passing | **Version**: v1.1.0

**Happy Voice Recognition!** 🎤✨