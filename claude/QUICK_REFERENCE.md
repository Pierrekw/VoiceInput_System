# Voice Input System - Quick Reference

## 🚀 Quick Start
```bash
# Activate virtual environment
source .venv/scripts/activate

# Run tests
.venv/scripts/python -m pytest -v

# Start system
.venv/scripts/python main.py
```

## 🎯 Key Features Status
| Feature | Status | Test Coverage |
|---------|--------|---------------|
| Real-time voice recognition | ✅ Working | ✅ Tested |
| Pause/resume functionality | ✅ Working | ✅ Tested |
| Excel auto-export | ✅ Working | ✅ Tested |
| Voice commands | ✅ Working | ✅ Tested |
| Keyboard controls | ✅ Working | ✅ Tested |
| Chinese number conversion | ✅ Working | ✅ Tested |
| Error handling | ✅ Working | ✅ Tested |

## 🎮 Controls Reference
| Input | Action | State Required |
|-------|--------|----------------|
| Space | Start/Pause/Resume | Any |
| ESC | Stop & Exit | Any |
| "开始录音" | Start via voice | idle |
| "暂停录音" | Pause via voice | recording |
| "继续录音" | Resume via voice | paused |
| "停止录音" | Stop via voice | Any |

## 📊 Test Commands
```bash
# Run all tests
.venv/scripts/python -m pytest -v

# Run specific test file
.venv/scripts/python -m pytest test_main_integration.py -v

# Run with coverage (if installed)
.venv/scripts/python -m pytest --cov=. --cov-report=html
```

## 🔧 Common Issues & Solutions

### PyAudio Not Found
```bash
# Install in virtual environment
.venv/scripts/python -m pip install pyaudio
```

### Vosk Model Missing
```bash
# Download models to model/ directory
# model/cn - Chinese standard
# model/cns - Chinese small
# model/us - English standard
# model/uss - English small
```

### Excel Export Errors
- Check file permissions
- Ensure Excel file not open in another program
- Verify pandas and openpyxl installation

## 📁 File Locations
- **Main Script**: `main.py`
- **Audio Module**: `audio_capture_v.py`
- **Excel Module**: `excel_exporter.py`
- **Test Files**: `test_*.py`
- **Output Excel**: `measurement_data.xlsx`
- **Log File**: `voice_input.log`

## 🧪 Test Status
- **Total Tests**: 18
- **Passing**: 18
- **Failing**: 0
- **Coverage**: Comprehensive core functionality

## ⚡ Performance Tips
- Use smaller Vosk model (cns/uss) for faster loading
- Adjust timeout_seconds for longer sessions
- Monitor memory usage for extended recordings
- Regular Excel file cleanup for large datasets

## 🔍 Debugging
- Check `voice_input.log` for detailed logs
- Enable debug mode: `logging.basicConfig(level=logging.DEBUG)`
- Test individual components: `audio_capture_v.py` and `excel_exporter.py`
- Verify PyAudio installation: `import pyaudio; print(pyaudio.get_portaudio_version_text())`

---
*Keep this handy for quick reference during development*