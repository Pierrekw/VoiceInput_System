# Voice Input System - 系统工作流程与版本备案

## 📋 Git版本信息

### 基础信息
- **Git版本**: 2.51.0.windows.2
- **当前分支**: develop
- **工作区状态**: 干净 (无未提交更改)
- **远程仓库**: https://github.com/Pierrekw/VoiceInput_System.git

### 最新提交记录
```
提交ID: cce297fb5b4a3ab4ef537b517233c8444aae11ed
提交信息: 删除启动空格键,TTS语音会被监测到问题待修复
提交时间: 2025-10-05 06:50:43 +0800
提交作者: pierrekw
```

### 最近提交历史
```
cce297f 删除启动空格键,TTS语音会被监测到问题待修复
51adb02 移除preload恢复成本地录入，还需修复键盘控制问题，
3581060 修复bug，优化程序
faf0ff2 mypy checked
78fdd79 更新项目配置：添加测试文件配置导入，调整pytest和mypy配置
```

---

## 🔄 系统工作流程详细分析

### 1. 系统启动流程
```
main.py 启动
├── 加载配置系统 (config_loader.py + config.yaml)
├── 设置日志系统 (voice_input.log + 控制台输出)
├── 创建 VoiceInputSystem 实例
├── 根据 excel.auto_export 配置决定是否创建 ExcelExporter
├── 初始化 AudioCapture 核心模块
├── 启动键盘监听器 (pynput)
├── 加载 VOSK 语音识别模型
├── 5秒倒计时开始识别
└── 进入实时语音识别主循环
```

### 2. 音频捕获与处理核心流
```
AudioCapture.listen_realtime_vosk()
├── audio_stream() 上下文管理
│   ├── PyAudio 初始化
│   ├── 音频设备检测
│   └── 音频流创建 (16kHz, 16bit, 单声道)
├── 实时音频处理循环
│   ├── 状态检查 (recording/paused/stopped)
│   ├── TTS 播放状态检查 (避免自激)
│   ├── VOSK 语音识别
│   ├── 语音命令处理
│   ├── 数值提取 (extract_measurements)
│   ├── 中文数字转换 (cn2an)
│   ├── 语音纠错 (VOICE_CORRECTION_DICT)
│   ├── 数据缓冲存储
│   ├── Excel 实时写入
│   └── TTS 语音播报
└── 识别结束处理
    ├── 模型卸载
    ├── 资源清理
    └── 结果统计输出
```

### 3. 数值提取与转换流程
```
语音文本 → extract_measurements()
├── 负数关键词过滤 (['负数', '负'])
├── 直接文本转换尝试 (cn2an.cn2an)
├── 特殊格式处理 ("点X" → "零点X")
├── 连续中文数字逐字符转换
├── 常见误识别模式处理
│   ├── "我" → "五"
│   ├── "我是" → "五十"
│   └── "我是我" → "五五"
├── 前缀移除 (['我', '你'])
├── 语音纠错词典应用
├── 正则表达式匹配
│   ├── _NUM_PATTERN (中文数字)
│   └── _UNIT_PATTERN (带单位数值)
├── 数值范围验证 (0 ≤ value ≤ 1,000,000)
├── 去重处理
└── 浮点数转换
```

### 4. 数据存储与Excel导出流程
```
数值+原始文本 → ExcelExporter.append_with_text()
├── 线程锁获取 (threading.Lock)
├── Excel文件存在性检查
├── 创建新文件 (如不存在)
├── 读取现有数据 (pandas)
├── 配置参数读取
│   ├── auto_numbering (自动编号)
│   ├── include_timestamp (时间戳)
│   ├── header_language (表头语言)
│   └── include_original (原始语音)
├── 新记录生成
│   ├── ID 分配 (get_next_id)
│   ├── 数值转换 (_float_cell)
│   ├── 时间戳生成
│   └── 原始文本保存
├── 数据合并 (pandas.concat)
├── Excel文件写入
├── 格式化处理 (openpyxl)
│   ├── 列宽设置
│   ├── 表头字体加粗
│   └── 居中对齐
├── 会话数据缓存
└── 线程锁释放
```

### 5. TTS语音反馈流程
```
数值识别结果 → TTS 播报
├── TTS 状态检查 (tts_state == "on")
├── TTS 锁获取 (_tts_lock)
├── 播放状态设置 (_tts_playing = True)
├── 音频识别临时暂停
├── Piper语音合成
│   ├── 模型加载 (zh_CN-huayan-medium.onnx)
│   ├── SynthesisConfig 配置
│   ├── 文本合成
│   └── 音频数据生成
├── sounddevice 播放
│   ├── numpy 数组转换
│   ├── float32 归一化
│   └── 非阻塞播放
├── 播放完成等待
├── 音频识别状态恢复
├── 播放状态重置 (_tts_playing = False)
└── TTS 锁释放
```

### 6. 配置系统架构流程
```
config.yaml → ConfigLoader → 全局config实例
├── 单例模式初始化
├── 默认配置加载
├── YAML文件解析
├── 配置合并 (_merge_configs)
├── 环境变量覆盖
│   ├── MODEL_PATH
│   ├── TIMEOUT_SECONDS
│   ├── VOICE_INPUT_GLOBAL_UNLOAD
│   ├── VOICE_INPUT_TEST_MODE
│   └── VOSK_LOG_LEVEL
├── 配置验证
├── 全局实例创建
└── 模块配置提供
    ├── get_model_path()
    ├── get_timeout_seconds()
    ├── get_test_mode()
    ├── get_sleep_time()
    ├── get_excel_file_name()
    └── 自定义路径获取 (get("section.key"))
```

### 7. 键盘与语音控制流程
```
用户输入 → 控制命令处理
├── 键盘输入 (pynput)
│   ├── 空格键: recording ↔ paused 状态切换
│   ├── ESC键: 任意状态 → stopped
│   └── T键: TTS on/off 切换
└── 语音命令 (VOSK识别)
    ├── 暂停命令 (["暂停录音", "暂停"])
    ├── 恢复命令 (["继续录音", "继续", "恢复"])
    └── 停止命令 (["停止录音", "停止", "结束"])
```

---

## 🔧 关键技术栈与依赖

### 核心技术
- **语音识别**: Vosk (离线中文语音识别)
- **音频处理**: PyAudio (实时音频流)
- **数字转换**: cn2an (中文数字转换)
- **Excel操作**: openpyxl + pandas
- **语音合成**: Piper-tts (离线中文TTS)
- **键盘控制**: pynput
- **配置管理**: PyYAML
- **音频播放**: sounddevice + numpy

### Python环境
- **系统Python**: 3.12.10
- **虚拟环境Python**: 3.11.11
- **包管理**: uv 0.8.0
- **代码质量**: MyPy类型检查, pre-commit钩子

---

## 📊 系统状态监控

### 性能指标
- **测试通过率**: 18/18 (100%)
- **缓冲区大小**: 10,000条记录
- **音频采样**: 16kHz
- **识别超时**: 60秒
- **检测间隔**: 50ms (生产环境)

### 错误处理机制
- **音频设备异常**: 自动重试和设备切换
- **模型加载失败**: 降级处理和错误日志
- **Excel写入冲突**: 线程锁和重试机制
- **TTS播放异常**: 静默处理和状态恢复

---

*📅 备案时间: 2025-10-05*
*🔍 分析工具: Claude Code*
*📝 文档版本: v1.0*