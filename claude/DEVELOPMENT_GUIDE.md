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
├── model_server/              # Flask model API server
│   ├── flask_model_api.py     # API server implementation
│   ├── model_api_client.py    # Client SDK
│   └── README.md              # API documentation
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

### Using Flask Model API

#### Starting the API Server
```bash
# Start the model loading API server
python model_server/flask_model_api.py
```

#### API Endpoints
- `GET /api/health` - Health check
- `GET /api/models` - List all loaded models
- `GET /api/models/status/<path>` - Get specific model status
- `POST /api/models/load` - Load a model
- `POST /api/models/unload` - Unload a model

#### Client Usage
```python
from model_server.model_api_client import ModelAPIClient

# Create client instance
client = ModelAPIClient()

# Load model
result = client.load_model("model/cn")

# List models
models = client.list_models()

# Unload model
client.unload_model("model/cn")
```

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

## 🔄 Synchronization and Asynchronous System Separation

### Overview
The project currently contains both synchronous and asynchronous voice input systems. To improve maintainability and scalability, we're planning to separate these systems. This section outlines the proposed separation approaches.

### Approach 1: Directory Restructuring (Recommended)
**Core Idea**: Restructure the codebase within the existing Git repository to separate synchronous and asynchronous systems into different directories while maintaining shared components.

**Proposed Structure**:
```
Voice_Input/
├── shared/              # Shared components (interfaces, utilities, configs)
│   ├── interfaces/
│   ├── text_processor.py
│   ├── config_loader.py
│   └── ...
├── sync_system/         # Synchronous system
│   ├── main.py
│   ├── audio_capture_v.py
│   └── ...
├── async_system/        # Asynchronous system
│   ├── main_production.py
│   ├── async_audio/
│   ├── events/
│   └── ...
├── models/              # Shared model files
├── configs/             # Configuration files
│   ├── sync_config.yaml
│   └── async_config.yaml
├── tests/               # Test code
└── requirements.txt     # Shared dependencies
```

**Advantages**:
- Maintains Git history in a single repository
- Simplified shared component maintenance
- Relatively low implementation complexity
- Clearer project structure
- Good IDE support

**Disadvantages**:
- Complex dependency management
- Cannot version the systems independently
- More complex release process
- Potential import conflicts

### Approach 2: Separate Repositories
**Core Idea**: Split the synchronous and asynchronous systems into two completely independent Git repositories, each containing all necessary code, dependencies, and configurations.

**Proposed Structure**:

Synchronous system repository:
```
Voice_Input_Sync/
├── src/
│   ├── main.py
│   ├── audio_capture_v.py
│   ├── text_processor.py
│   └── ...
├── models/
├── config.yaml
├── requirements.txt
└── README.md
```

Asynchronous system repository:
```
Voice_Input_Async/
├── src/
│   ├── main_production.py
│   ├── async_audio/
│   ├── events/
│   ├── text_processor.py
│   └── ...
├── models/
├── config.yaml
├── requirements.txt
└── README.md
```

**Advantages**:
- Complete isolation of code, dependencies, and environments
- Independent version control
- Independent dependency management
- Clearer ownership
- Easier system-specific optimizations

**Disadvantages**:
- Difficult shared code maintenance
- Split Git history
- Increased project management complexity
- Higher storage requirements
- Complex workflow when modifying features affecting both systems

### Approach 3: Git Submodules
**Core Idea**: Use Git submodules to manage shared components while maintaining some level of separation between the systems.

**Implementation Options**:
1. Keep the main project (synchronous system) in one repository and the asynchronous system as a submodule
2. Extract shared components into submodules that are referenced by both systems

**Advantages**:
- Code sharing with independent version control
- Potential for independent virtual environments

**Disadvantages**:
- Complex Git submodule usage
- Additional steps for updates and synchronization
- Steeper learning curve for team members

### Implementation Steps (for Approach 1)
1. Create the proposed directory structure
2. Move relevant code to corresponding directories
3. Update import paths across the codebase
4. Update the `.gitignore` file if necessary
5. Create `__init__.py` files to ensure modules are importable
6. Test both systems thoroughly to ensure functionality is preserved
7. Update documentation to reflect the new structure

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