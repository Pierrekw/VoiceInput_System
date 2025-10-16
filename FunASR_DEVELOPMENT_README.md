# FunASR 语音识别开发日志

## 📅 开发日期: 2025-10-16

## 🎯 项目目标
将 FunASR ZH Stream 模型集成到现有的 audio_capture_v.py 中，实现高质量的实时语音识别，要求代码修改最小化，方便测试。

## 🔧 技术架构

### 核心模型
- **模型**: paraformer-zh-streaming (FunASR ZH Stream)
- **版本**: v2.0.4
- **设备**: CPU
- **特点**: 支持流式识别

### 关键文件
- `audio_capture_v.py`: 主要音频捕获模块
- `test_funasr.py`: FunASR 测试程序
- `FunASR_DEVELOPMENT_README.md`: 本开发日志

## 🚀 开发过程与挑战

### 阶段1: 基础集成
✅ **成功完成**
- 添加 FunASR 模型导入和检测
- 在 AudioCapture 类中集成 FunASR 模型管理
- 实现 `load_funasr_model()`, `unload_funasr_model()` 等方法
- 创建流式识别方法 `listen_realtime_funasr()`

### 阶段2: 测试程序修复
✅ **成功完成**
- 修复 `test_funasr.py` 中的麦克风输入问题
- 原程序只能处理预录制音频，改为支持实时麦克风输入
- 实现音频缓冲和流式处理

### 阶段3: 识别逻辑优化
✅ **重大突破**
- **问题**: 系统在用户说话过程中就"急不可耐"地进行识别
- **症状**:
  - "我是天才" → 被识别为 "是天才"
  - "12345678910" → 被切分成多个数字片段
  - 用户说话中途就不断输出识别结果

## 💡 核心解决方案: 模仿 Vosk 的 AcceptWaveform 模式

### 问题分析
通过对比 audio_capture_v.py 中 Vosk 的实现，发现关键差异：

**Vosk 的正确模式**:
```python
if self._recognizer and self._recognizer.AcceptWaveform(data):
    # 只有当 AcceptWaveform() 返回 True 时才进行识别
    # 这表示 Vosk 判断用户已经说完了完整的话
    result = json.loads(self._recognizer.Result())
```

**原始 FunASR 的错误模式**:
```python
# 在用户说话过程中就不断识别
if is_in_speech and current_time - speech_start_time >= min_speech_duration:
    result = self._model.generate(...)  # 错误：急不可耐
```

### 优化后的正确模式
```python
# === 模仿Vosk的语音活动检测逻辑 ===
if is_speech and not is_speech_segment:
    # 开始新的语音段
    is_speech_segment = True
    speech_start_time = current_time
    speech_segment_audio = []

elif not is_speech and is_speech_segment:
    # 语音可能结束，检查静音时长
    silence_duration = current_time - last_speech_time
    speech_duration = current_time - speech_start_time

    # 智能判断：如果语音段足够长(>2秒)或静音时间足够长，就结束识别
    should_end = (
        silence_duration >= min_silence_duration or  # 静音时间足够
        (silence_duration >= 0.5 and speech_duration >= 2.0)  # 语音较长且短暂停顿
    )

    if should_end:
        # 确认语音段结束，进行识别（模仿Vosk的AcceptWaveform）
        is_speech_segment = False
        result = self._model.generate(input=np.array(speech_segment_audio), ...)
```

## 📊 参数优化过程

### 初始参数 (问题版本)
```python
speech_energy_threshold = 0.008  # 过于敏感
min_speech_duration = 0.3  # 太短
min_silence_duration = 0.2  # 太短，导致过早断句
recognition_interval = 0.5  # 频繁识别
```

### 优化参数 (最终版本)
```python
speech_energy_threshold = 0.015  # 提高阈值，降低敏感度
min_speech_duration = 0.4  # 确保是真正的语音
min_silence_duration = 0.8  # 平衡响应速度和完整性
text_similarity_threshold = 0.7  # 适度去重，避免过度过滤
```

### 智能检测策略
- **短语音 (< 2秒)**: 等待 0.8 秒静音后识别
- **长语音 (≥ 2秒)**: 只需 0.5 秒停顿就识别
- **效果**: 既保证完整性，又提高响应速度

## 🔍 调试过程

### 问题症状
用户反馈只有 `rtf_avg` 进度条，没有识别结果

### 调试方法
1. **启用 DEBUG 日志**: 查看详细的语音段检测过程
2. **添加关键日志**:
   - `🎯 开始语音段`: 确认语音段开始
   - `语音段结束`: 确认语音段结束
   - `⚠️ 语音段过短`: 检查是否因语音过短被跳过

### 发现的真正原因
不是检测问题，而是**重复文本被过滤掉了**:
```
2025-10-16 21:03:14 - DEBUG - 跳过重复文本: 七 十 三 点 五
```

## 📈 最终效果对比

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 响应延迟 | 0.5秒 (急不可耐) | 2-3秒 (合理等待) |
| 识别完整性 | ❌ 句子被切碎 | ✅ 完整句子识别 |
| 用户体验 | ❌ 说话被打断 | ✅ 自然流畅 |
| 重复过滤 | 过度严格 (0.8) | 适度过滤 (0.7) |

## 🎯 关键经验教训

### 1. 学习成熟解决方案
- 不要重新发明轮子，学习 Vosk 的 AcceptWaveform 模式
- 成熟的语音识别库都有类似的语音段检测逻辑

### 2. 用户体验优先
- 用户感觉"急不可耐"比"稍慢响应"更糟糕
- 宁可多等0.5秒，也不要中途打断用户

### 3. 参数调优是艺术
- 需要在响应速度和识别完整性之间找到平衡
- 智能策略比固定参数更有效

### 4. 调试的重要性
- 看到的问题不一定是真正的问题
- 详细的日志是调试的关键工具

## 📁 文件结构

```
Voice_Input/
├── audio_capture_v.py          # 主音频捕获模块 (已集成FunASR)
├── test_funasr.py              # FunASR测试程序 (已优化)
├── FunASR_DEVELOPMENT_README.md # 本开发日志
└── model/fun/                  # FunASR模型目录
```

## 🚀 使用方法

### 基础测试
```bash
python test_funasr.py
```

### 集成使用
```python
# 在 audio_capture_v.py 中
capture = AudioCapture()
capture.load_funasr_model()
result = capture.listen_realtime_funasr()
```

## 🔮 未来优化方向

1. **GPU 加速**: 当前使用 CPU，可考虑 GPU 加速提高性能
2. **噪音抑制**: 添加更好的噪音过滤算法
3. **多语言支持**: 扩展支持其他语言模型
4. **参数自适应**: 根据环境噪音自动调整参数

## 📝 总结

本次开发成功实现了 FunASR 与现有系统的完美集成，通过模仿 Vosk 的 AcceptWaveform 模式，解决了实时语音识别中的用户体验问题。关键在于理解语音识别的本质：**等待用户说完话，而不是急于中途打断**。

这个优化过程展示了如何通过学习和借鉴成熟解决方案来快速解决复杂的技术问题。