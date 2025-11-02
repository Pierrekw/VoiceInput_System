# VoiceInput - 快速构建指南

## ⚡ 立即开始 (Windows)

### 方式1: CMD (推荐)
```cmd
cd /d "F:\04_AI\01_Workplace\Voice_Input"
pip install -r requirements-nuitka.txt
build_nuitka.bat
```

### 方式2: PowerShell
```powershell
Set-Location "F:\04_AI\01_Workplace\Voice_Input"
pip install -r requirements-nuitka.txt
.\build_nuitka.bat
```

### 方式3: Git Bash
```bash
cd "F:/04_AI/01_Workplace/Voice_Input"
pip install -r requirements-nuitka.txt
./build_nuitka.sh
```

## ✅ 验证构建

```bash
python test_packaged_app.py
```

## 📦 输出文件

```
build/
├── VoiceInput_System.exe      # Windows可执行文件
└── VoiceInput_System.dist/    # 独立目录
```

## 🔧 故障排除

**问题**: 文件名错误
```
错误: build_nutika.sh
正确: build_nuitka.sh
```

**问题**: Python未找到
```cmd
where python
# 应该显示: F:\04_AI\01_Workplace\Voice_Input\.venv\Scripts\python.exe
```

**问题**: 权限不足
```cmd
# 以管理员身份运行CMD
```

## 📚 文档

- `README_BUILDER.md` - 快速入口
- `BUILD_INSTRUCTIONS.md` - 详细说明
- `BUILD_SYSTEM_README.md` - 系统文档

---

**状态**: ✅ 构建系统已就绪  
**版本**: v2.8  
**更新时间**: 2025-11-02
