# 🚀 FunASR GUI打包工具

这个目录包含了FunASR语音输入系统的GUI版本Nuitka打包脚本，提供完整、精简、分步等多种打包解决方案。

## 📋 快速开始

### 1️⃣ 交互式GUI打包菜单 (推荐)
```bash
cd build_scripts
GUI_BUILD_MENU.bat
```
提供完整的GUI打包选项菜单，适合不同需求的用户。

### 2️⃣ 一键完整版打包
```bash
cd build_scripts
build_gui_complete.bat
```
包含GUI界面 + 模型文件 + FFmpeg依赖，适合发布。

### 3️⃣ 精简版打包
```bash
cd build_scripts
build_gui_minimal.bat
```
仅GUI和基础依赖，适合开发测试。

### 4️⃣ 分步打包
```bash
cd build_scripts
# 先打包程序
quick_build.bat
# 然后添加模型文件
package_with_models.bat
# 最后添加FFmpeg
package_with_ffmpeg.bat
```
完全控制打包参数，灵活配置。

## 📦 打包模式对比

| 模式 | 包含内容 | 文件大小 | 打包时间 | 适用场景 |
|------|----------|----------|----------|----------|
| 🚀 完整版 | GUI+模型+FFmpeg | 2-3GB | 30-60分钟 | 最终发布 |
| ⚡ 精简版 | 仅GUI+基础依赖 | 200-500MB | 10-20分钟 | 开发测试 |
| 🧪 快速测试 | 最小依赖 | 100-200MB | 5-10分钟 | 功能验证 |
| 📁 分步打包 | 自定义组合 | 可变 | 可变 | 灵活配置 |

## 🎯 打包目标结构

### 完整版输出
```
FunASR_VoiceInput_GUI.dist/
├── FunASR_VoiceInput_GUI.exe    # GUI主程序
├── start_gui.bat               # 一键启动脚本
├── model/                      # 语音识别模型
│   ├── fun/                   # FunASR模型
│   ├── vad/                   # VAD模型
│   └── punc/                  # 标点模型
├── ffmpeg/                     # 音视频处理
│   ├── bin/                   # FFmpeg可执行文件
│   └── lib/                   # FFmpeg库文件
├── config/                     # 配置文件
├── config.yaml                # 主配置
├── voice_correction_dict.txt  # 纠错词典
└── README.txt                 # 使用说明
```

### 精简版输出
```
FunASR_VoiceInput_GUI_Minimal.dist/
├── FunASR_VoiceInput_GUI_Minimal.exe  # GUI主程序
├── start_minimal.bat                  # 启动脚本
├── config.yaml                        # 配置文件
├── voice_correction_dict.txt         # 纠错词典
└── README.txt                        # 使用说明
```

## 🧪 测试方法

### 基础测试
```bash
# 运行启动脚本
start_gui.bat

# 或直接运行程序
FunASR_VoiceInput_GUI.exe
```

### 命令行测试
```bash
# 查看帮助
FunASR_VoiceInput_GUI.exe --help

# 启动GUI界面
FunASR_VoiceInput_GUI.exe --gui

# 快速识别模式
FunASR_VoiceInput_GUI.exe --mode=fast
```

### 功能验证
- 检查GUI界面是否正常显示
- 测试语音识别功能
- 验证音频文件处理
- 检查日志文件生成

## ⚠️ 打包前检查

### 必需文件
- [x] `main_f.py` - 主程序文件
- [x] `config.yaml` - 配置文件
- [x] `voice_correction_dict.txt` - 纠错词典

### 可选文件
- [ ] `model/fun/` - FunASR模型目录
- [ ] `model/vad/` - VAD模型目录
- [ ] `model/punc/` - 标点模型目录
- [ ] `onnx_deps/ffmpeg-master-latest-win64-gpl-shared/` - FFmpeg依赖

### 环境要求
- [x] Python 3.8+
- [x] Nuitka已安装
- [x] 足够的磁盘空间 (建议5GB+)
- [x] 管理员权限 (Windows)

## 🔧 高级配置

### 自定义打包参数
编辑 `build_nuitka_custom.bat` 修改打包参数

### 优化选项
- `--jobs=8` - 并行编译线程数
- `--lto=yes` - 启用链接时优化
- `--windows-icon-from-ico=icon.ico` - 自定义图标
- `--windows-disable-console` - 禁用控制台窗口

### 包含额外文件
```bash
--include-data-file=源文件=目标路径
--include-data-dir=源目录=目标目录
```

## 🛠️ 故障排除

### 常见问题
1. **打包失败** - 检查Python环境和依赖
2. **文件过大** - 使用精简版或分步打包
3. **启动失败** - 验证模型文件和FFmpeg依赖
4. **功能异常** - 检查配置文件和日志

### 日志文件
- 打包日志: `build_*/` 目录中的输出
- 运行日志: `logs/` 目录中的日志文件

## 📚 相关文档

- [完整打包指南](../nuitka_build_guide.md)
- [Nuitka官方文档](https://nuitka.net/doc/)
- [FunASR项目文档](../README.md)

## 🆘 获取帮助

1. 查看详细错误信息
2. 检查 [nuitka_build_guide.md](../nuitka_build_guide.md)
3. 确认所有依赖已安装
4. 验证模型文件完整性

## 💡 使用建议

1. **开发阶段**: 使用精简版快速迭代
2. **测试阶段**: 使用快速测试版验证功能
3. **发布阶段**: 使用完整版打包发布
4. **模型更新**: 使用分步打包更新模型文件

---
🎯 **推荐流程**: 开发用精简版 → 测试用快速版 → 发布用完整版

*打包脚本版本: 2.0*  
*最后更新: 2025年*