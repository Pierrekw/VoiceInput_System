# Voice Input System - Development Guide (Consolidated)

## 🛠️ Environment Setup

### Requirements
- **Python**: 3.11.x (required)
- **Virtual Environment**: `.venv`
- **Package Manager**: `uv`
- **Git**: Latest version

### Quick Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/scripts/activate  # Git Bash
# or
.venv\Scripts\activate          # CMD

# Install dependencies
uv sync

# Verify setup
python --version  # Should show 3.11.x
python text_processor.py  # Test text processing
```

## 📁 Project Structure
```
Voice_Input/
├── main.py                    # Main entry point
├── audio_capture_v.py         # Audio capture and recognition
├── text_processor.py          # Shared text processing module
├── excel_exporter.py          # Excel export functionality
├── config_loader.py           # Configuration management
├── model_manager.py           # Model loading and management
├── TTSengine.py               # Text-to-speech engine
├── claude/                    # Documentation
│   ├── CONSOLIDATED_DOCUMENTATION.md
│   ├── PROJECT_SUMMARY_CONCISE.md
│   └── DEVELOPMENT_GUIDE.md   # This file
├── tests/                     # Test suites
├── model/                     # Vosk models
└── pyproject.toml            # Project configuration
```

## 🔄 Development Workflow

### Before Development
1. **Check Environment**: Ensure Python 3.11 virtual environment is active
2. **Update Dependencies**: Run `uv sync` to ensure latest dependencies
3. **Verify Setup**: Test basic functionality

### During Development
1. **Code Changes**: Implement features following coding standards
2. **Module Testing**: Run module self-tests
3. **Integration Testing**: Run full test suite
4. **Documentation**: Update relevant documentation

### After Development
1. **Full Testing**: Run all tests to ensure no regressions
2. **Documentation Check**: Verify all docs are updated
3. **Code Review**: Check quality and consistency

## 🧪 Testing Guidelines

### Module Self-Tests
Each core module should include self-test functionality:
```python
# Example pattern for text_processor.py
if __name__ == "__main__":
    test_results = test_text_processor()
    print(f"Module test: {'PASSED' if test_results else 'FAILED'}")
```

### Test Coverage Requirements
- **Core Functions**: 100% test coverage
- **Text Processing**: Chinese numbers, TTS filtering, error correction
- **System Integration**: Both versions compatibility
- **Edge Cases**: Invalid input, error handling

### Running Tests
```bash
# Test individual modules
python text_processor.py
python audio_capture_v.py

# Run full test suite
python -m pytest -v

# Run specific test categories
python -m pytest tests/integration_test.py -v
python -m pytest tests/test_text_processing.py -v
```

## 📖 Documentation Standards

### Mandatory Updates
- **New Features**: Update README.md and PROJECT_SUMMARY.md
- **Architecture Changes**: Update project structure documentation
- **API Changes**: Update usage examples and API docs
- **Configuration Changes**: Update setup instructions

### Documentation Priority
1. **README.md**: Primary user-facing documentation
2. **PROJECT_SUMMARY.md**: Technical project overview
3. **DEVELOPMENT_GUIDE.md**: Developer instructions
4. **CHANGELOG.md**: Version history and changes

### Content Guidelines
- **Concise**: Keep documentation brief but comprehensive
- **Clear**: Use simple language, avoid jargon
- **Current**: Always reflect latest code state
- **Complete**: Cover all essential information

## 🔧 Technical Standards

### Code Quality
- **Type Annotations**: Use Python type hints
- **Documentation**: All public functions need docstrings
- **Error Handling**: Comprehensive exception handling
- **Configuration**: Use config system, avoid hardcoding

### Performance Requirements
- **Response Time**: Text processing < 0.01 seconds
- **Memory Usage**: No memory leaks, support large number ranges
- **Thread Safety**: Thread-safe implementations
- **Resource Cleanup**: Automatic resource management

### Module Integration
- **Single Responsibility**: Each module has clear purpose
- **Backward Compatibility**: Maintain compatibility with original system
- **Configuration Integration**: Auto-integrate with config system
- **Error Handling**: Robust fallback mechanisms

## 🚀 Common Development Tasks

### Adding New Text Processing Features
1. **Modify** `text_processor.py`
2. **Update** module self-test
3. **Test** with both system versions
4. **Document** new functionality
5. **Update** configuration if needed

### Creating New Tests
1. **Add** test cases to appropriate test file
2. **Include** edge cases and error scenarios
3. **Verify** backward compatibility
4. **Document** test purpose and expected results

### Updating Dependencies
1. **Modify** `pyproject.toml`
2. **Run** `uv sync`
3. **Test** all functionality
4. **Update** documentation if API changes

## 📊 Version Management

### Version Numbering
- **Major (X.0.0)**: Breaking changes, major features
- **Minor (0.X.0)**: New features, backward compatible
- **Patch (0.0.X)**: Bug fixes, minor improvements

### Release Process
1. **Feature Complete**: All planned features implemented
2. **Testing Complete**: All tests passing
3. **Documentation Complete**: All docs updated
4. **Version Tag**: Create git tag for release
5. **Changelog**: Update CHANGELOG.md

---

## 🔮 Future Development Areas

### Planned Improvements
- Enhanced Chinese number parsing algorithms
- Machine learning-based error correction
- Multi-language support
- Performance optimizations
- Advanced async patterns

### Technical Debt
- Regular code refactoring
- Performance monitoring
- Dependency updates
- Security reviews

---

*Last Updated: October 5, 2025*
*Consolidated from multiple development documents*