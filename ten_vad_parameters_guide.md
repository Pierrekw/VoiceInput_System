# TEN VAD 参数详解与优化指南

## 📋 当前配置

当前系统中TEN VAD的配置：
```python
ten_vad_model = TenVad(hop_size=256, threshold=0.5)
```

## 🔧 参数详解

### 1. **Threshold (阈值) - 0.5**
**作用**: 控制语音检测的敏感度
- **范围**: 0.0 - 1.0
- **当前值**: 0.5 (中等敏感度)

**影响**:
- **高阈值 (0.6-0.8)**: 更严格，只检测明显的语音，减少误报但可能漏掉轻声
- **低阈值 (0.2-0.4)**: 更敏感，能检测轻声语音，但可能误判噪音为语音
- **中等阈值 (0.5)**: 平衡点，适合大多数场景

### 2. **Hop Size (跳跃大小) - 256**
**作用**: 每次处理的音频采样点数量
- **单位**: 采样点
- **当前值**: 256
- **对应时间**: 256/16000 = 16ms (16毫秒)

**影响**:
- **小hop_size (128-256)**:
  - ✅ 检测延迟更低 (8-16ms)
  - ✅ 语音边界检测更精确
  - ❌ 计算量更大，CPU使用率更高
- **大hop_size (512-1024)**:
  - ✅ 计算量更小，CPU使用率更低
  - ❌ 检测延迟更高 (32-64ms)
  - ❌ 语音边界检测不够精确

## 🎯 场景优化建议

### 1. **实时对话场景**
```python
ten_vad_model = TenVad(hop_size=128, threshold=0.4)
```
- **用途**: 视频会议、实时通话
- **特点**: 低延迟、高敏感度
- **优势**: 快速响应说话开始

### 2. **安静办公室环境**
```python
ten_vad_model = TenVad(hop_size=256, threshold=0.6)
```
- **用途**: 办公室录音、正式演讲
- **特点**: 高精度、低误报
- **优势**: 避免键盘声、空调声误判

### 3. **嘈杂环境**
```python
ten_vad_model = TenVad(hop_size=512, threshold=0.3)
```
- **用途**: 咖啡厅、户外录音
- **特点**: 适应背景噪音
- **优势**: 在噪音中仍能检测语音

### 4. **低功耗设备**
```python
ten_vad_model = TenVad(hop_size=1024, threshold=0.5)
```
- **用途**: 嵌入式设备、移动应用
- **特点**: 低计算量、电池友好
- **优势**: 节省CPU资源

## 📊 性能对比表

| Hop Size | 延迟 | CPU使用 | 精度 | 适用场景 |
|----------|------|---------|------|----------|
| 128 | 8ms | 高 | 最高 | 实时应用 |
| 256 | 16ms | 中等 | 高 | 通用场景 |
| 512 | 32ms | 低 | 中等 | 后台处理 |
| 1024 | 64ms | 最低 | 基础 | 低功耗设备 |

| Threshold | 敏感度 | 误报率 | 漏检率 | 适用环境 |
|-----------|---------|--------|--------|----------|
| 0.2-0.4 | 很高 | 高 | 低 | 轻声检测 |
| 0.5-0.6 | 中等 | 中等 | 中等 | 通用环境 |
| 0.7-0.8 | 低 | 低 | 高 | 安静环境 |

## 🔬 测试和调优

### 参数测试脚本
```python
from ten_vad import TenVad
import numpy as np

def test_vad_parameters(hop_size, threshold):
    model = TenVad(hop_size=hop_size, threshold=threshold)

    # 测试不同场景
    test_results = {
        'silence': 0,      # 静音检测
        'quiet_speech': 0,  # 轻声语音
        'normal_speech': 0,  # 正常语音
        'noise': 0          # 噪音检测
    }

    return test_results

# 推荐配置组合
configs = [
    (128, 0.4),   # 低延迟高敏感
    (256, 0.5),   # 当前配置平衡
    (512, 0.3),   # 噪音环境
    (256, 0.6),   # 安静环境
]

for hop_size, threshold in configs:
    print(f"测试配置: hop_size={hop_size}, threshold={threshold}")
```

## ⚠️ 注意事项

1. **采样率兼容性**: 确保音频采样率为16000Hz
2. **内存使用**: hop_size越小，需要的处理频率越高
3. **实时性要求**: 根据应用场景选择合适的延迟
4. **环境噪音**: 在嘈杂环境中可能需要调整threshold

## 🚀 如何在系统中修改

### 方法1: 修改源码
```python
# 在 funasr_voice_TENVAD.py 第51行
ten_vad_model = TenVad(hop_size=128, threshold=0.4)  # 自定义配置
```

### 方法2: 通过配置文件
```yaml
# config.yaml 中添加
vad:
  type: "ten_vad"
  hop_size: 256      # 可选: 128, 256, 512, 1024
  threshold: 0.5     # 可选: 0.2-0.8
```

## 💡 最佳实践

1. **默认配置**: `hop_size=256, threshold=0.5` 适合大多数场景
2. **实时应用**: 降低hop_size到128以减少延迟
3. **安静环境**: 提高threshold到0.6减少误报
4. **嘈杂环境**: 降低threshold到0.3避免漏检
5. **性能优先**: 增加hop_size到512或1024节省CPU

---

*根据你的具体使用场景选择合适的参数组合！*