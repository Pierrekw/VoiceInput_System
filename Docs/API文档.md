# FunASR语音输入系统 - API文档

## 📋 概述
本文档记录了FunASR语音输入系统的所有核心类、方法和接口信息。

## 🔧 核心系统模块

### FunASRVoiceSystem (main_f.py)
**主要系统类，整合所有语音识别功能**

#### 方法
##### `__init__(self, recognition_duration: int = 60, continuous_mode: bool = True, debug_mode: bool = False)`
初始化语音系统

**参数:**
- `recognition_duration`: 识别持续时间（秒），-1表示无限时
- `continuous_mode`: 是否启用连续模式
- `debug_mode`: 是否启用debug模式

**返回值:** FunASRVoiceSystem实例

##### `initialize(self) -> bool`
初始化系统组件

**返回值:** 初始化是否成功

##### `recognize_voice_command(self, text: str) -> VoiceCommandType`
识别语音命令，优先使用新的模式匹配

**参数:**
- `text`: 识别的文本

**返回值:** VoiceCommandType枚举值

**示例:**
```python
system = FunASRVoiceSystem()
system.initialize()
command_type = system.recognize_voice_command("切换200")
if command_type == VoiceCommandType.STANDARD_ID:
    system._handle_standard_id_command("切换200")
```

##### `_handle_standard_id_command(self, text: str)`
处理标准序号命令（使用模式匹配）

**参数:**
- `text`: 识别的文本

##### `set_standard_id(self, standard_id: int)`
设置当前标准序号

**参数:**
- `standard_id`: 标准序号（必须是100的倍数）

##### `setup_excel_from_gui(self, part_no: str, batch_no: str, inspector: str) -> bool`
从GUI设置Excel模板

**参数:**
- `part_no`: 零件号
- `batch_no`: 批次号
- `inspector`: 检验员

**返回值:** 设置是否成功

##### `process_recognition_result(self, original_text: str, processed_text: str, numbers: List[float])`
处理识别结果

**参数:**
- `original_text`: 原始识别文本
- `processed_text`: 处理后文本
- `numbers`: 提取的数字列表

### VoiceCommandType (main_f.py)
**语音命令类型枚举**

#### 枚举值
- `PAUSE`: 暂停命令
- `RESUME`: 继续命令
- `STOP`: 停止命令
- `STANDARD_ID`: 标准序号命令
- `UNKNOWN`: 未知命令

## 📝 文本处理模块

### TextProcessor (text_processor.py)
**文本处理器类，处理中文数字转换和文本清理**

#### 方法
##### `__init__(self) -> None`
初始化文本处理器

##### `process_text(self, text: str) -> str`
处理文本，进行中文数字转换和清理

**参数:**
- `text`: 原始文本

**返回值:** 处理后的文本

**示例:**
```python
processor = TextProcessor()
result = processor.process_text("切换二百")
# result = "切换200"
```

##### `extract_numbers(self, original_text: str, processed_text: Optional[str] = None) -> List[float]`
从文本中提取数字

**参数:**
- `original_text`: 原始文本
- `processed_text`: 处理后文本（可选）

**返回值:** 提取的数字列表

##### `chinese_to_arabic_number(self, text: str) -> str`
将中文数字转换为阿拉伯数字

**参数:**
- `text`: 包含中文数字的文本

**返回值:** 转换后的文本

##### `calculate_similarity(self, text1: str, text2: str) -> float`
计算两个文本之间的相似度

**参数:**
- `text1`: 文本1
- `text2`: 文本2

**返回值:** 相似度（0-1之间的浮点数）

### VoiceCommandProcessor (text_processor.py)
**语音命令专用文本处理器**

#### 方法
##### `__init__(self) -> None`
初始化语音命令处理器

##### `configure(self, match_mode: str = "fuzzy", min_match_length: int = 2, confidence_threshold: float = 0.8) -> None`
配置匹配参数

**参数:**
- `match_mode`: 匹配模式（"fuzzy"或"exact"）
- `min_match_length`: 最小匹配长度
- `confidence_threshold`: 置信度阈值

##### `match_command(self, text: str, commands: Dict[str, List[str]]) -> Optional[str]`
匹配语音命令

**参数:**
- `text`: 识别的文本
- `commands`: 命令字典

**返回值:** 匹配的命令类型，如果没有匹配返回None

##### `match_standard_id_command(self, text: str, command_prefixes: List[str]) -> Optional[int]`
基于模式匹配标准序号命令

**参数:**
- `text`: 识别的文本
- `command_prefixes`: 命令前缀列表

**返回值:** 如果匹配到标准序号命令，返回标准序号数值；否则返回None

**示例:**
```python
processor = VoiceCommandProcessor()
prefixes = ["切换", "设置", "切换到", "设置标准序号"]
result = processor.match_standard_id_command("切换200", prefixes)
# result = 200
```

## 📊 Excel导出模块

### ExcelExporterEnhanced (excel_utils.py)
**增强Excel导出器**

#### 方法
##### `__init__(self, filename: str, part_no: str = "", batch_no: str = "", inspector: str = "")`
初始化Excel导出器

**参数:**
- `filename`: Excel文件名
- `part_no`: 零件号
- `batch_no`: 批次号
- `inspector`: 检验员

##### `create_from_template(self, part_no: str = "", batch_no: str = "", inspector: str = "") -> bool`
从模板创建Excel文件

**参数:**
- `part_no`: 零件号
- `batch_no`: 批次号
- `inspector`: 检验员

**返回值:** 创建是否成功

##### `append_with_text(self, data: List[Tuple[Union[float, str], str, str]]) -> bool`
添加数据到Excel

**参数:**
- `data`: 数据列表，每个元素为(值, 原始文本, 处理后文本)

**返回值:** 添加是否成功

##### `finalize_excel_file(self) -> bool`
完成Excel文件格式化

**返回值:** 格式化是否成功

## ⚙️ 配置管理模块

### ConfigLoader (config_loader.py)
**配置加载器**

#### 方法
##### `__init__(self, config_file_path: str = "config.yaml")`
初始化配置加载器

**参数:**
- `config_file_path`: 配置文件路径

##### `get(self, key: str, default: Any = None) -> Any`
获取配置值

**参数:**
- `key`: 配置键（支持点分隔的嵌套键）
- `default`: 默认值

**返回值:** 配置值

##### `get_standard_id_command_prefixes(self) -> List[str]`
获取标准序号命令前缀列表

**返回值:** 命令前缀列表

**示例:**
```python
config = ConfigLoader()
prefixes = config.get_standard_id_command_prefixes()
# prefixes = ["设置标准序号", "切换标准序号", "设置序号", ...]
```

##### `get_voice_commands_config(self) -> Dict[str, Any]`
获取语音命令配置

**返回值:** 语音命令配置字典

##### `get_vad_config(self) -> Dict[str, Any]`
获取VAD配置

**返回值:** VAD配置字典

## 🎛️ GUI模块

### VoiceRecognitionApp (voice_gui.py)
**主要GUI应用类**

#### 方法
##### `__init__(self)`
初始化GUI应用

##### `start_recognition(self)`
开始识别

##### `stop_recognition(self)`
停止识别

##### `toggle_pause(self)`
切换暂停/继续状态

##### `validate_part_no(self, text: str)`
验证零件号输入

**参数:**
- `text`: 输入文本

##### `validate_batch_no(self, text: str)`
验证批次号输入

**参数:**
- `text`: 输入文本

##### `validate_inspector(self, text: str)`
验证检验员输入

**参数:**
- `text`: 输入文本

##### `are_inputs_valid(self) -> bool`
检查所有输入是否有效

**返回值:** 验证是否通过

##### `get_input_values(self) -> Dict[str, str]`
获取输入值

**返回值:** 输入值字典

## 🔍 性能监控模块

### PerformanceMonitor (utils/performance_monitor.py)
**性能监控器**

#### 方法
##### `__init__(self)`
初始化性能监控器

##### `start_timer(self, name: str)`
开始计时

**参数:**
- `name`: 计时器名称

##### `end_timer(self, name: str) -> float`
结束计时

**参数:**
- `name`: 计时器名称

**返回值:** 耗时（秒）

##### `get_stats(self) -> Dict[str, Any]`
获取性能统计

**返回值:** 性能统计字典

### PerformanceStep (上下文管理器)
**性能步骤监控器**

#### 方法
##### `__init__(self, name: str, metadata: Optional[Dict[str, Any]] = None)`
初始化性能步骤

**参数:**
- `name`: 步骤名称
- `metadata`: 元数据

##### `__enter__(self)`
进入上下文

##### `__exit__(self, exc_type, exc_val, exc_tb)`
退出上下文

**示例:**
```python
with PerformanceStep("语音识别", {"text_length": len(text)}):
    result = recognizer.recognize(text)
```

## 📝 使用示例

### 完整的语音识别流程
```python
from main_f import FunASRVoiceSystem
from text_processor import TextProcessor

# 创建和初始化系统
system = FunASRVoiceSystem()
system.initialize()

# 处理语音命令
text = "切换标准200"
command_type = system.recognize_voice_command(text)

if command_type == VoiceCommandType.STANDARD_ID:
    system._handle_standard_id_command(text)

# 处理测量数据
processor = TextProcessor()
processed_text = processor.process_text("二十五点四")
numbers = processor.extract_numbers(processed_text)

if numbers:
    system.process_recognition_result("二十五点四", processed_text, numbers)
```

### 文本处理示例
```python
from text_processor import TextProcessor, VoiceCommandProcessor
from config_loader import ConfigLoader

# 文本转换
processor = TextProcessor()
result = processor.process_text("切换三百五十一")
# result = "切换351"

# 命令识别
command_processor = VoiceCommandProcessor()
config = ConfigLoader()
prefixes = config.get_standard_id_command_prefixes()

standard_id = command_processor.match_standard_id_command("设置400", prefixes)
# standard_id = 400
```

### Excel导出示例
```python
from excel_utils import ExcelExporterEnhanced

# 创建Excel导出器
exporter = ExcelExporterEnhanced("report.xlsx", "PART-A001", "B202501", "张三")

# 使用模板创建
success = exporter.create_from_template("PART-A001", "B202501", "张三")

# 添加数据
data = [(25.4, "二十五点四", "25.4"), (30.1, "三十点一", "30.1")]
exporter.append_with_text(data)

# 完成格式化
exporter.finalize_excel_file()
```

## 🔧 配置示例

### 语音命令配置
```yaml
voice_commands:
  standard_id_commands:
    prefixes:
      - 设置标准序号
      - 切换标准序号
      - 设置序号
      - 切换序号
      - 切换到
      - 切换标准
      - 序号
      - 切换
      - 设置
```

### VAD配置
```yaml
vad:
  energy_threshold: 0.010
  min_speech_duration: 0.2
  min_silence_duration: 0.8
  speech_padding: 0.3
```

---

**文档版本**: v1.0
**创建时间**: 2025-10-26
**最后更新**: 2025-10-26
**对应系统版本**: v2.6 - 模式匹配语音命令系统