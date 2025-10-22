# 开发记录

## 2025年10月19日 - v2.2 性能优化重大更新

### 🎯 主要问题解决
- **用户反馈**: "语音录入到终端显示，时间间隔有点长"
- **性能分析**: 发现音频输入延迟高达~100ms，端到端延迟4-5秒
- **根本原因**: VAD静音等待时间过长 + chunk_size过大
- **解决方案**: 实现完整的性能监控系统和VAD优化配置

### ✅ 核心改进

#### 1. 性能监控系统实现
- **Debug性能追踪器** (`debug_performance_tracker.py`):
  - 详细记录语音输入→ASR→文本处理→终端显示→Excel写入的完整延迟链
  - 自动生成延迟分析报告，识别性能瓶颈
  - 支持会话级性能追踪和统计

- **生产环境延迟记录器** (`production_latency_logger.py`):
  - 轻量级延迟记录，不影响系统性能
  - 适合常态化监控，记录到debug日志
  - 支持端到端延迟统计

- **性能测试工具** (`performance_test.py`, `debug_performance_test.py`):
  - 自动化性能测试脚本
  - 配置对比分析
  - 音频设备性能测试

#### 2. VAD配置优化系统
- **集成到config.yaml**: 将VAD参数完全整合到配置系统
- **三种预设模式**:
  - **fast模式**: 0.35秒基础延迟，适合日常使用 ⭐ 推荐配置
  - **balanced模式**: 0.75秒基础延迟，默认设置
  - **accuracy模式**: 1.15秒基础延迟，适合重要场合
- **自定义配置**: 支持mode="customized"时手动调整所有VAD参数

#### 3. 音频性能优化
- **chunk_size优化**: 从8000降至400，延迟提升4倍
- **音频流参数**: 优化PyAudio配置
- **实测结果**: 音频输入延迟从100ms降至25ms

#### 4. 延迟分析结果
| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| **音频输入延迟** | ~100ms | **~25ms** | **4倍提升** |
| **最大延迟** | ~112ms | **~41ms** | **2.7倍提升** |
| **最小延迟** | ~89ms | **~9ms** | **9.9倍提升** |
| **处理频率** | 299次/30s | 1196次/30s | **4倍提升** |

#### 5. 关键参数配置
```yaml
vad:
  mode: "fast"  # fast/balanced/accuracy/customized
  # 自定义参数（仅在customized时生效）
  energy_threshold: 0.015
  min_speech_duration: 0.3
  min_silence_duration: 0.6  # 🔑 关键参数：静音等待时间
  speech_padding: 0.3
```

### 📊 性能监控数据
- **主要瓶颈**: 语音输入阶段（97%延迟）
- **ASR处理**: 仅0.14秒（3%延迟），性能良好
- **文本处理**: <1ms，几乎无延迟
- **用户感知**: 从明显延迟到响应迅速

### 🔧 技术实现亮点
- **无侵入式监控**: 性能监控系统不影响正常功能
- **配置热切换**: VAD参数修改后重启即可生效
- **详细追踪**: 每个识别步骤都有精确时间戳
- **生产友好**: debug级别日志，可常态化监控

---

## 2025年10月19日 - v2.1 重大更新

### 🎯 主要问题解决
- **根本问题**: 识别系统在60秒后突然终止
- **原因分析**: start_funasr.py中硬编码`recognition_duration=60`，配置文件`timeout_seconds: 60`
- **解决方案**: 实现真正的无限时模式，支持配置化管理

### ✅ 核心改进

#### 1. 识别时长控制重构
- **配置文件**: `timeout_seconds: -1` 表示无限时模式
- **启动脚本**: 支持命令行参数覆盖配置
- **核心逻辑**: 修改`funasr_voice_module.py`中的循环条件
- **变量说明**:
  - `-1`: 无限时模式（连续识别）
  - `0`: 立即结束（调试用）
  - `正数`: 单次识别时长（秒）

#### 2. 音频流异常处理增强
- **重试机制**: 音频设备异常时自动重试3次
- **错误分类**: 区分设备断开、缓冲区溢出等不同错误类型
- **详细日志**: 记录音频流异常和恢复过程
- **资源管理**: 确保PyAudio资源正确释放

#### 3. 语音命令配置化
- **移除硬编码**: 将语音命令从代码移至config.yaml
- **智能匹配**: 实现基于编辑距离的模糊匹配算法
- **多语言支持**: 同时支持中英文语音命令
- **参数配置**: 支持匹配模式、置信度等参数调整

#### 4. 日志系统完善
- **停止原因**: 详细记录系统停止的各种原因
- **运行统计**: 记录实际运行时间和处理结果
- **调试信息**: 增强调试模式的日志输出

### 🔧 技术实现细节

#### 无限时模式实现
```python
# 修改前（立即退出）
while time.time() - start_time < duration:

# 修改后（支持无限时）
while (duration == -1 or time.time() - start_time < duration):
```

#### 音频流重试机制
```python
max_retries = 3
retry_count = 0
while retry_count < max_retries:
    try:
        # 创建音频流
        stream = p.open(...)
        if not stream.is_active():
            raise RuntimeError("音频流创建失败：流未激活")
        yield stream
        break
    except Exception as e:
        retry_count += 1
        if retry_count >= max_retries:
            raise RuntimeError(f"音频流创建失败，已重试{max_retries}次: {e}")
```

#### 语音命令相似度计算
```python
def _calculate_similarity(self, text1: str, text2: str) -> float:
    """基于编辑距离的相似度计算"""
    len1, len2 = len(text1), len(text2)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    # ... 动态规划计算编辑距离
    similarity = 1.0 - (edit_distance / max_len)
    return max(0.0, similarity)
```

### 📊 测试验证

#### 功能测试
- ✅ 配置加载: 正确读取timeout_seconds=-1
- ✅ 无限时模式: 运行90秒未自动停止
- ✅ 限时模式: 30秒按时停止
- ✅ 语音命令: 12/12测试用例通过
- ✅ 音频重试: 3次重试机制正常工作

#### 性能测试
- **启动时间**: 模型加载1.5秒
- **内存占用**: 稳定运行无内存泄漏
- **CPU使用**: 正常范围，无明显异常
- **音频延迟**: 实时识别，延迟小于1秒

### 📝 配置文件重构

#### config.yaml增强
- 添加详细注释说明每个参数的作用
- 提供常用配置示例和使用场景
- 包含启动命令和配置说明
- 标注重要配置项和注意事项

#### 关键配置说明
```yaml
recognition:
  # ⚠️ 核心配置：识别时长
  timeout_seconds: -1  # -1=无限时，60=60秒停止

voice_commands:
  config:
    match_mode: "fuzzy"  # 模糊匹配
    confidence_threshold: 0.8  # 置信度阈值
```

### 🔄 向后兼容性

- **配置兼容**: 旧的配置文件仍然可用，会使用默认值
- **命令兼容**: 所有原有命令行参数保持不变
- **功能兼容**: Excel导出、文本处理等功能完全兼容

### 📈 用户体验改进

#### 启动信息优化
- 显示当前配置模式（无限时/限时）
- 显示可用的语音命令
- 提供清晰的使用说明

#### 错误处理改善
- 友好的错误提示信息
- 详细的解决建议
- 调试模式下的错误追踪

### 🐛 已知问题修复

1. **60秒自动停止**: 通过无限时模式完全解决
2. **音频设备异常**: 增加重试机制和错误处理
3. **语音命令硬编码**: 实现完全配置化
4. **日志信息不足**: 增加详细的停止原因记录

### 🚀 新增功能

#### 命令行参数扩展
```bash
python start_funasr.py --help
# 新增参数:
#   --show-config  显示配置信息
#   --continuous   连续识别模式
#   -d -1          明确指定无限时
```

#### 配置验证功能
- 启动时验证配置文件完整性
- 显示当前生效的配置参数
- 提供配置调整建议

### 🔮 后续优化方向

1. **性能优化**:
   - 支持GPU加速（CUDA）
   - 优化内存使用
   - 减少启动时间

2. **功能扩展**:
   - 多语言识别支持
   - 自定义语音命令界面
   - 实时翻译功能

3. **用户体验**:
   - 图形化配置界面
   - 更丰富的语音反馈
   - 移动端支持

---

## 2025年10月22日 - v2.3 质量检测系统功能规划

### 🎯 业务需求分析
- **应用场景**: 质量检测录入系统
- **核心问题**: 多零件检测，每个零件有不同测量序号（100, 200, 300等）
- **用户需求**: 语音输入零件号和测量序号，自动归类测量数据

### 📋 功能设计方案

#### 1. 系统架构设计
- **模块化原则**: GUI只负责界面显示，excel_exporter处理所有业务逻辑
- **职责分离**:
  - GUI层：用户交互和状态显示
  - excel_exporter层：零件管理、测量序号、数据归类
  - 语音识别层：专注于语音转文字

#### 2. 核心功能规划

**零件管理功能**:
- 零件号输入（支持手动输入 + 下拉搜索历史记录）
- 零件信息验证和格式化（如：345876AD）
- 常用零件号缓存和历史记录

**测量序号管理**:
- 每个零件预定义测量序号（100, 200, 300等）
- 语音命令切换测量序号（"测量序号三百"）
- GUI快捷键支持（F1-F12对应常用序号）

**智能数据归类**:
- 根据当前选中的零件号和测量序号自动归类
- Excel表格增加零件号和测量序号列
- 测量数据自动填充到对应行

#### 3. 数据结构设计

**Excel表格格式**:
```
| 时间戳 | 零件号 | 测量序号 | 测量值 | 操作员 |
|--------|--------|----------|--------|--------|
| 09:15:23 | 345876AD | 100 | 25.4 | 张三 |
```

**语音命令设计**:
- 零件号输入："零件三三四五八七六AD" → 345876AD
- 序号切换："测量序号三百" → 激活300序号
- 数据录入："25.4" → 自动保存到当前零件+当前序号

#### 4. excel_exporter模块扩展

**新增状态管理**:
```python
class ExcelExporter:
    def set_current_part(self, part_number: str)
    def set_measurement_sequence(self, sequence: int)
    def get_part_info(self, part_number: str)
    def process_voice_command(self, voice_text: str)
```

**业务逻辑处理**:
- 零件号格式验证和标准化
- 测量序号匹配逻辑
- 语音命令解析和执行
- 数据自动归类和Excel写入

#### 5. 技术实现优势
- **单一职责**: 每个模块功能明确，易于维护
- **可测试性**: 业务逻辑独立，便于单元测试
- **可扩展性**: 容易添加新的数据源和导出格式
- **复用性**: excel_exporter可被其他界面复用

#### 6. 用户工作流程
```
启动系统 → 输入零件号 → 选择测量序号 → 语音录入测量数据 → 自动保存Excel
```

#### 7. 额外优化建议
- **批量导入**: 支持Excel导入零件信息和标准测量序号
- **数据校验**: 测量值超出预设范围时警告提示
- **操作反馈**: 语音播报当前状态（"已切换到测量序号300"）
- **快捷操作**: 键盘快捷键支持，提升操作效率

### 🔧 实现优先级
1. **P0**: excel_exporter模块扩展（零件管理、测量序号）
2. **P1**: 语音命令处理和识别逻辑
3. **P2**: GUI界面适配和状态显示
4. **P3**: 高级功能（批量导入、数据校验等）

---

## 2025年10月22日 - 音频质量优化规划

### 🎯 音频处理问题分析
- **环境噪音**: 生产车间环境噪音干扰识别准确性
- **人声增强**: 需要重点识别离麦克风最近的操作员声音
- **距离控制**: 通过音频参数优化实现距离选择性识别

### 📋 降噪方案设计

#### 1. 降噪模块选型对比

**RNNoise (推荐)**:
- **优势**: 轻量级，实时性好，专门针对语音降噪
- **集成**: 可集成到PyAudio流处理中
- **性能**: CPU占用低，适合实时处理
- **适用**: 个人使用，资源有限环境

**WebRTC VAD + 降噪**:
- **优势**: Google开源，工业级质量
- **功能**: VAD + 降噪 + 回声消除一体化
- **集成**: 有Python封装库(py-webrtcvad)
- **适用**: 复杂环境，需要综合处理

**speexdsp**:
- **优势**: 专为实时通信设计，稳定成熟
- **功能**: 降噪、AGC、回声消除
- **适用**: 对稳定性要求高的场景

#### 2. 人声增强策略

**能量阈值优化**:
```yaml
vad:
  energy_threshold: 0.025    # 🔑 提高阈值，过滤远距离噪音
  min_speech_duration: 0.2   # 减少最小时长，快速响应
  min_silence_duration: 0.4  # 减少静音等待，提升流畅度
  speech_padding: 0.2        # 减少填充，减少延迟
```

**自适应阈值机制**:
- 根据环境噪音动态调整能量阈值
- 实时监测背景噪音水平
- 平衡识别距离和抗干扰能力

#### 3. 音频设备优化建议

**硬件层面推荐**:
- **定向麦克风**: 心形指向，只收前方声音
- **麦克风阵列**: 支持声源定位，自动跟踪说话人
- **防风罩**: 减少气流噪音干扰
- **近场设计**: 鼓励用户靠近麦克风说话

**软件层面处理**:
- **AGC (自动增益控制)**: 放大近距声音，压制远距噪音
- **均衡器**: 增强人声频段(1-4kHz)，抑制噪音频段
- **动态范围压缩**: 平衡不同说话人的音量差异

#### 4. 配置方案设计

**安静环境配置** (办公室、实验室):
```yaml
vad:
  energy_threshold: 0.02
  min_speech_duration: 0.15
  min_silence_duration: 0.3
  mode: "fast"
noise_reduction:
  enabled: true
  method: "rnnoise"
  intensity: 0.5
```

**嘈杂环境配置** (生产车间):
```yaml
vad:
  energy_threshold: 0.035  # 更高阈值，过滤远距离噪音
  min_speech_duration: 0.25
  min_silence_duration: 0.5
  mode: "accuracy"
noise_reduction:
  enabled: true
  method: "webrtc"
  intensity: 0.8
audio_processing:
  auto_gain_control: true
  noise_suppression: true
  echo_cancellation: false
```

#### 5. 渐进式实现策略

**第一阶段**: 基础参数调优
- 提高能量阈值到0.025-0.035
- 优化VAD参数组合
- 测试不同距离的识别效果

**第二阶段**: 集成降噪模块
- 选择RNNoise进行集成
- 实时降噪处理
- 性能影响评估

**第三阶段**: 智能音频处理
- 自适应阈值算法
- AGC自动增益控制
- 人声频段增强

#### 6. 技术实现要点

**RNNoise集成示例**:
```python
import rnnoise
denoiser = rnnoise.RNNoise()

def process_audio(audio_chunk):
    denoised = denoiser.filter(audio_chunk)
    return denoised
```

**自适应阈值算法**:
```python
def adaptive_energy_threshold(audio_chunk, base_threshold=0.025):
    """根据环境噪音动态调整阈值"""
    current_noise = estimate_noise_level(audio_chunk)
    threshold = base_threshold + (current_noise * 0.5)
    return min(threshold, 0.05)  # 限制最大阈值
```

#### 7. 性能优化考虑

**实时性要求**:
- 降噪处理延迟 < 50ms
- CPU占用率 < 20%
- 内存占用 < 100MB

**质量评估指标**:
- 识别准确率提升 > 15%
- 噪音抑制比 > 10dB
- 端到端延迟增加 < 100ms

### 🔧 实现优先级
1. **P0**: VAD参数调优（能量阈值、时长参数）
2. **P1**: RNNoise降噪模块集成
3. **P2**: 自适应阈值算法实现
4. **P3**: 高级音频处理（AGC、均衡器）

---

## 2025年10月22日 - Paraformer-large流式识别精度优化

### 🎯 模型现状分析
- **当前模型**: Paraformer-large流式版本 (`iic/speech_paraformer_asr_nat-zh-cn-16k-common-vocab8404-online`)
- **核心优势**: 支持实时流式输入，延迟低，识别稳定
- **优化目标**: 在保持流式性能的同时，提升口音适应性和识别精度

### 📋 流式识别精度优化方案

#### 1. 流式参数配置优化

**Chunk配置策略**:
```python
# 针对不同口音程度的配置
chunk_configs = {
    "standard": {
        "chunk_size": [0, 10, 5],           # 480ms标准延迟
        "encoder_chunk_look_back": 4,       # 标准回看
        "decoder_chunk_look_back": 1
    },
    "slight_accent": {
        "chunk_size": [0, 12, 6],           # 600ms稍长延迟，更多上下文
        "encoder_chunk_look_back": 6,       # 增加回看窗口
        "decoder_chunk_look_back": 2
    },
    "strong_accent": {
        "chunk_size": [0, 16, 8],           # 768ms更长延迟，最大上下文
        "encoder_chunk_look_back": 8,       # 最大回看窗口
        "decoder_chunk_look_back": 3
    }
}
```

**自适应延迟调整**:
- **标准模式**: 480ms延迟，适合清晰普通话
- **口音模式**: 600ms延迟，增加上下文信息
- **强口音模式**: 768ms延迟，最大化识别精度

#### 2. 热词增强系统

**质量检测专用热词库**:
```python
quality_hotwords = [
    # 零件管理
    "零件号", "产品编号", "型号", "规格", "批次号",

    # 测量术语
    "测量序号", "尺寸", "公差", "直径", "长度", "宽度", "高度",

    # 质量判定
    "合格", "不合格", "优等", "良品", "次品", "返工", "报废",

    # 数字单位
    "毫米", "厘米", "微米", "丝", "道",

    # 常用零件号前缀
    "ABCD", "EFGH", "IJKL", "MNOP"
]

# 动态热词权重配置
hotword_config = {
    "weight": 2.5,              # 热词权重
    "boost_factor": 1.8,        # 提升因子
    "decay_factor": 0.95        # 衰减因子
}
```

#### 3. 流式VAD精准调优

**针对流式识别的VAD配置**:
```yaml
vad_streaming:
  model: "fsmn-vad-streaming"

  # 敏感度配置
  speech_noise_threshold: 0.45     # 降低阈值，捕获更多语音
  min_speech_duration: 150         # 150ms最小语音时长
  min_silence_duration: 250        # 250ms静音检测

  # 流式特定参数
  max_single_segment_time: 8000    # 8秒最大分段
  window_size: 300                 # 300ms分析窗口

  # 自适应参数
  adaptive_threshold: true         # 启用自适应阈值
  noise_reduction_level: 0.6       # 噪音抑制级别
```

#### 4. 流式微调策略

**数据准备要求**:
```python
# 流式训练数据格式
streaming_data_format = {
    "source": "path/to/audio.wav",
    "target": "零件号345876AD测量序号一百合格",
    "duration": 5.2,
    "task": "asr_streaming",       # 标记流式任务
    "chunk_info": {                # Chunk信息
        "optimal_chunk": [0, 12, 6],
        "look_back": 6
    }
}
```

**微调配置**:
```bash
# 使用流式模型进行微调
model_name="iic/speech_paraformer_asr_nat-zh-cn-16k-common-vocab8404-online"

# 微调参数
--train_conf.max_epoch=50
--dataset_conf.batch_size=16
--optim_conf.lr=0.0001            # 较小学习率
--train_conf.warmup_steps=1000
```

#### 5. 音频预处理增强

**流式音频增强流程**:
```python
def streaming_audio_enhancement(audio_chunk):
    """流式音频增强处理"""

    # 1. 实时噪音检测
    noise_level = estimate_noise_level(audio_chunk)

    # 2. 自适应滤波
    if noise_level > 0.3:
        audio_chunk = apply_noise_reduction(audio_chunk, intensity=0.7)

    # 3. 人声频段增强 (1-4kHz)
    audio_chunk = boost_frequency_range(audio_chunk, 1000, 4000, boost_db=2)

    # 4. 动态范围压缩
    audio_chunk = apply_compression(audio_chunk, ratio=3:1)

    return audio_chunk
```

#### 6. 智能后处理系统

**质量检测专用后处理**:
```python
class QualityInspectionPostProcessor:
    def __init__(self):
        self.part_number_patterns = [
            r'[A-Z]{2,4}\d{4,6}[A-Z]{0,2}',  # 标准零件号格式
            r'[A-Z]\d{6,8}[A-Z]',            # 变体格式
        ]
        self.measurement_sequences = ["100", "200", "300", "400", "500"]

    def process_recognition_result(self, text):
        """处理识别结果"""

        # 1. 零件号纠正
        text = self.correct_part_numbers(text)

        # 2. 测量序号标准化
        text = self.standardize_measurement_sequence(text)

        # 3. 数字表达转换
        text = self.convert_chinese_numbers(text)

        # 4. 质量术语标准化
        text = self.standardize_quality_terms(text)

        return text
```

#### 7. 实时质量监控

**流式识别质量评估**:
```python
class StreamingQualityMonitor:
    def __init__(self):
        self.confidence_history = deque(maxlen=20)
        self.accent_detection_model = AccentDetector()
        self.performance_metrics = {}

    def evaluate_and_adapt(self, result, audio_chunk):
        """评估识别质量并自适应调整"""

        confidence = result.get('confidence', 0.0)
        self.confidence_history.append(confidence)

        # 口音检测
        accent_type = self.accent_detection_model.detect(audio_chunk)

        # 基于历史性能调整参数
        if len(self.confidence_history) >= 10:
            avg_confidence = sum(self.confidence_history) / len(self.confidence_history)

            if avg_confidence < 0.75:
                return self.switch_to_high_precision_mode(accent_type)
            elif avg_confidence > 0.9:
                return self.switch_to_fast_mode()

        return result
```

#### 8. 配置文件优化

**最终推荐配置**:
```yaml
# 流式识别优化配置
streaming_asr_optimized:
  model: "iic/speech_paraformer_asr_nat-zh-cn-16k-common-vocab8404-online"

  # 流式核心参数
  chunk_size: [0, 12, 6]              # 平衡延迟和精度
  encoder_chunk_look_back: 6          # 增加上下文信息
  decoder_chunk_look_back: 2          # 解码器回看

  # 解码优化
  beam_size: 8                        # 增加beam搜索
  length_penalty: 0.0
  ctc_weight: 0.15                    # 调整CTC权重
  lm_weight: 0.3                      # 语言模型权重

  # 音频处理
  sample_rate: 16000
  normalize: true
  feature_extraction: "fbank"
  n_mels: 80                          # 增加梅尔频带

  # 热词配置
  hotwords_file: "config/quality_hotwords.txt"
  hotword_weight: 2.5
  dynamic_hotword: true               # 动态热词更新

  # 自适应配置
  adaptive_mode: true                 # 启用自适应模式
  accent_detection: true              # 口音检测
  quality_monitoring: true            # 质量监控
```

#### 9. 性能基准测试

**优化效果预期**:
| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| **识别准确率** | 85-90% | **92-95%** | **5-7%** |
| **口音适应性** | 70-80% | **88-92%** | **12-18%** |
| **专业术语识别** | 75-85% | **90-93%** | **10-15%** |
| **流式延迟** | 480ms | **600ms** | +120ms |
| **处理效率** | RTF=0.05 | **RTF=0.06** | +20% |

#### 10. 实施路线图

**分阶段实施计划**:

**第一阶段 (1-2周)**:
- 调整流式参数配置
- 添加质量检测专用热词
- 优化VAD参数

**第二阶段 (2-3周)**:
- 实施音频预处理增强
- 集成智能后处理系统
- 开发质量监控模块

**第三阶段 (3-4周)**:
- 收集本地口音数据
- 进行流式模型微调
- 性能测试和调优

**第四阶段 (4-5周)**:
- 自适应模式完善
- 系统集成测试
- 用户培训和部署

### 🔧 技术实现要点

#### 关键代码示例
```python
# 自适应流式识别配置
class AdaptiveStreamingASR:
    def __init__(self):
        self.model = AutoModel(model="paraformer-zh-streaming")
        self.quality_monitor = StreamingQualityMonitor()
        self.post_processor = QualityInspectionPostProcessor()

    def recognize_with_adaptation(self, audio_stream):
        """带自适应的流式识别"""
        results = []

        for chunk in audio_stream:
            # 音频增强
            enhanced_chunk = streaming_audio_enhancement(chunk)

            # 流式识别
            result = self.model.generate(
                input=enhanced_chunk,
                cache=self.cache,
                **self.current_config
            )

            # 质量评估和自适应
            adapted_result = self.quality_monitor.evaluate_and_adapt(
                result, enhanced_chunk
            )

            # 后处理
            final_result = self.post_processor.process_recognition_result(
                adapted_result
            )

            results.append(final_result)

        return results
```

这个优化方案专门针对Paraformer-large流式模型的特点设计，可以在保持实时性能的同时显著提升识别精度和口音适应性。

---

## 版本历史

### v2.3 (2025-10-22) - 规划中
- 质量检测系统功能设计
- 模块化架构重构规划
- 零件管理和测量序号功能

### v2.2 (2025-10-19)
- 性能优化重大更新
- VAD配置优化系统
- 性能监控工具实现