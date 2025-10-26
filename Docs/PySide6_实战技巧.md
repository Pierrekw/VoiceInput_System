# PySide6 实战技巧总结

## 📋 目录
1. [性能优化技巧](#性能优化技巧)
2. [UI设计模式](#ui设计模式)
3. [调试和测试](#调试和测试)
4. [常见问题解决](#常见问题解决)
5. [代码组织最佳实践](#代码组织最佳实践)
6. [部署和发布](#部署和发布)

---

## 🚀 性能优化技巧

### 1. 减少不必要的UI更新
```python
# ❌ 错误：频繁更新UI
def update_progress(self):
    while self.processing:
        self.progress_bar.setValue(self.current_value)  # 太频繁
        time.sleep(0.001)

# ✅ 正确：使用定时器控制更新频率
def __init__(self):
    self.update_timer = QTimer()
    self.update_timer.timeout.connect(self.update_ui)
    self.update_timer.start(50)  # 20 FPS，足够流畅

def update_ui(self):
    if self.needs_update:
        self.progress_bar.setValue(self.current_value)
        self.needs_update = False
```

### 2. 使用信号槽的正确方式
```python
# ❌ 错误：在信号中执行耗时操作
class Worker(QThread):
    progress = Signal(int)

    def run(self):
        for i in range(100):
            # 耗时操作在信号处理中
            self.progress.emit(i)
            time.sleep(0.1)  # 阻塞主线程

# ✅ 正确：耗时操作在工作线程中
class Worker(QThread):
    progress = Signal(int)

    def run(self):
        for i in range(100):
            # 耗时操作在工作线程
            time.sleep(0.1)
            # 只发送简单的数据
            self.progress.emit(i)
```

### 3. 优化大列表显示
```python
# ❌ 错误：一次性加载所有数据
def load_large_data(self):
    all_data = fetch_all_records()  # 可能很慢
    for item in all_data:
        self.list_widget.addItem(item)

# ✅ 正确：分页加载或懒加载
def load_large_data(self):
    # 先加载可见部分
    visible_data = fetch_visible_items(0, 50)
    for item in visible_data:
        self.list_widget.addItem(item)

    # 滚动时加载更多
    self.list_widget.verticalScrollBar().valueChanged.connect(self.load_more)

def load_more(self, scroll_value):
    if scroll_value > self.list_widget.verticalScrollBar().maximum() - 100:
        more_data = fetch_more_items(self.current_index, 50)
        for item in more_data:
            self.list_widget.addItem(item)
```

### 4. 内存管理
```python
# ❌ 错误：忘记清理资源
def open_dialog(self):
    dialog = MyDialog()
    dialog.exec()  # 对象可能没有正确释放

# ✅ 正确：及时清理资源
def open_dialog(self):
    dialog = MyDialog()
    if dialog.exec() == QDialog.Accepted:
        # 处理结果
        pass
    dialog.deleteLater()  # 确保对象被删除
```

---

## 🎨 UI设计模式

### 1. MVC模式实现
```python
# Model - 数据模型
class DataModel(QObject):
    data_changed = Signal(list)

    def __init__(self):
        super().__init__()
        self._data = []

    def add_data(self, item):
        self._data.append(item)
        self.data_changed.emit(self._data)

# View - 视图
class DataView(QWidget):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.model.data_changed.connect(self.update_view)

    def update_view(self, data):
        # 更新UI显示
        pass

# Controller - 控制器
class DataController(QObject):
    def __init__(self, model, view):
        super().__init__()
        self.model = model
        self.view = view

        # 连接视图的用户操作到模型
        self.view.add_button.clicked.connect(self.add_item)

    def add_item(self):
        # 处理用户输入，更新模型
        self.model.add_data(new_item)
```

### 2. 观察者模式
```python
class EventManager:
    def __init__(self):
        self._observers = {}

    def subscribe(self, event_type, callback):
        if event_type not in self._observers:
            self._observers[event_type] = []
        self._observers[event_type].append(callback)

    def emit(self, event_type, data=None):
        if event_type in self._observers:
            for callback in self._observers[event_type]:
                callback(data)

# 使用示例
class MyWidget(QWidget):
    def __init__(self, event_manager):
        super().__init__()
        self.event_manager = event_manager

        # 订阅事件
        self.event_manager.subscribe('data_updated', self.on_data_updated)

    def on_data_updated(self, data):
        # 处理数据更新
        pass
```

### 3. 工厂模式创建组件
```python
class WidgetFactory:
    @staticmethod
    def create_progress_bar(style='default'):
        if style == 'energy':
            return EnergyProgressBar()
        elif style == 'circular':
            return CircularProgress()
        else:
            return QProgressBar()

    @staticmethod
    def create_button(button_type, **kwargs):
        if button_type == 'primary':
            btn = QPushButton()
            btn.setStyleSheet("background-color: #2196F3; color: white;")
            return btn
        elif button_type == 'danger':
            btn = QPushButton()
            btn.setStyleSheet("background-color: #f44336; color: white;")
            return btn

# 使用示例
btn = WidgetFactory.create_button('primary', text="确认")
progress = WidgetFactory.create_progress_bar('energy')
```

---

## 🐛 调试和测试

### 1. 调试技巧
```python
# 使用QDebug进行调试
from PySide6.QtCore import Qt, qDebug

def debug_function(self):
    qDebug("调试信息")
    qDebug(f"变量值: {self.some_variable}")

# 设置调试标志
import os
os.environ['QT_DEBUG_PLUGINS'] = '1'  # 调试插件加载

# 启用Qt调试输出
from PySide6.QtCore import qInstallMessageHandler

def my_message_handler(mode, context, message):
    if mode == QtDebugMsg:
        print(f"DEBUG: {message}")
    elif mode == QtWarningMsg:
        print(f"WARNING: {message}")
    elif mode == QtCriticalMsg:
        print(f"CRITICAL: {message}")
    elif mode == QtFatalMsg:
        print(f"FATAL: {message}")

qInstallMessageHandler(my_message_handler)
```

### 2. 单元测试
```python
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

class TestMyWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self):
        self.widget = MyWidget()

    def test_button_click(self):
        # 测试按钮点击
        button = self.widget.findChild(QPushButton, "myButton")
        QTest.mouseClick(button, Qt.LeftButton)
        self.assertEqual(self.widget.get_result(), "expected")

    def test_text_input(self):
        # 测试文本输入
        text_edit = self.widget.findChild(QTextEdit, "myTextEdit")
        QTest.keyClicks(text_edit, "Hello World")
        self.assertEqual(text_edit.toPlainText(), "Hello World")

    def tearDown(self):
        self.widget.deleteLater()

if __name__ == '__main__':
    unittest.main()
```

### 3. 性能分析
```python
import time
import cProfile
from functools import wraps

def profile_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
        pr.print_stats()
        return result
    return wrapper

# 使用示例
@profile_function
def expensive_operation(self):
    # 耗时操作
    pass

# 简单的时间测量
def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 耗时: {end_time - start_time:.4f} 秒")
        return result
    return wrapper
```

---

## ❓ 常见问题解决

### 1. 线程安全问题
```python
# ❌ 错误：在工作线程中直接操作UI
class WorkerThread(QThread):
    def run(self):
        for i in range(100):
            self.parent().progress_bar.setValue(i)  # 危险！
            time.sleep(0.1)

# ✅ 正确：使用信号槽进行线程间通信
class WorkerThread(QThread):
    progress_updated = Signal(int)

    def run(self):
        for i in range(100):
            self.progress_updated.emit(i)  # 安全
            time.sleep(0.1)

# 在主窗口中连接信号
class MainWindow(QMainWindow):
    def __init__(self):
        self.worker = WorkerThread()
        self.worker.progress_updated.connect(self.progress_bar.setValue)
```

### 2. 内存泄漏问题
```python
# ❌ 错误：循环引用
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.callback = self.handle_callback  # 循环引用

    def handle_callback(self):
        pass

# ✅ 正确：避免循环引用
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        # 使用弱引用或lambda
        some_object.callback.connect(lambda: self.handle_callback())

    def handle_callback(self):
        pass
```

### 3. 样式不生效问题
```python
# 确保样式正确应用
def apply_styles(self):
    # 使用更具体的选择器
    self.setStyleSheet("""
        QMainWindow#MyWindow {
            background-color: #f0f0f0;
        }
        QPushButton[class="primary"] {
            background-color: #2196F3;
        }
    """)

    # 设置对象名称
    self.setObjectName("MyWindow")
    self.primary_button.setProperty("class", "primary")

# 检查样式是否加载
def debug_styles(self):
    print("当前样式表:")
    print(self.styleSheet())
```

### 4. 窗口显示问题
```python
# 确保窗口正确显示
def show_window(self):
    # 1. 设置窗口属性
    self.setWindowTitle("My Window")
    self.resize(800, 600)

    # 2. 显示窗口
    self.show()

    # 3. 确保窗口在最前面（可选）
    self.raise_()
    self.activateWindow()

    # 4. 处理事件循环
    QApplication.processEvents()

# 窗口居中显示
def center_window(self):
    screen = QApplication.primaryScreen().geometry()
    window_geometry = self.frameGeometry()
    center_point = screen.center()
    window_geometry.moveCenter(center_point)
    self.move(window_geometry.topLeft())
```

---

## 📁 代码组织最佳实践

### 1. 项目结构
```
my_gui_app/
├── main.py                     # 应用入口
├── requirements.txt            # 依赖列表
├── README.md                   # 项目说明
├── config/                     # 配置文件
│   ├── settings.py
│   └── styles.qss
├── src/                        # 源代码
│   ├── __init__.py
│   ├── main_window.py          # 主窗口
│   ├── widgets/                # 自定义组件
│   │   ├── __init__.py
│   │   ├── base_widget.py      # 基础组件类
│   │   ├── custom_widgets.py   # 自定义控件
│   │   └── dialogs.py          # 对话框
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   └── data_model.py
│   ├── views/                  # 视图
│   │   ├── __init__.py
│   │   └── main_view.py
│   ├── controllers/            # 控制器
│   │   ├── __init__.py
│   │   └── main_controller.py
│   ├── utils/                  # 工具类
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   └── constants.py
│   └── resources/              # 资源文件
│       ├── icons/
│       ├── images/
│       └── fonts/
├── tests/                      # 测试文件
│   ├── __init__.py
│   ├── test_widgets.py
│   └── test_models.py
└── docs/                       # 文档
    ├── api.md
    └── user_guide.md
```

### 2. 配置管理
```python
# config/settings.py
class Settings:
    WINDOW_SIZE = (800, 600)
    WINDOW_TITLE = "My Application"

    # 样式配置
    COLORS = {
        'primary': '#2196F3',
        'secondary': '#FFC107',
        'success': '#4CAF50',
        'danger': '#f44336',
        'background': '#f5f5f5',
        'text': '#212121'
    }

    # 字体配置
    FONTS = {
        'default': ('Arial', 10),
        'heading': ('Arial', 14, QFont.Bold),
        'code': ('Consolas', 10)
    }

# 使用配置
from config.settings import Settings

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.apply_settings()

    def apply_settings(self):
        self.setWindowTitle(Settings.WINDOW_TITLE)
        self.resize(*Settings.WINDOW_SIZE)
        self.setStyleSheet(f"""
            color: {Settings.COLORS['text']};
            background-color: {Settings.COLORS['background']};
        """)
```

### 3. 常量管理
```python
# src/utils/constants.py
class Constants:
    # 应用信息
    APP_NAME = "My Application"
    VERSION = "1.0.0"

    # 窗口尺寸
    MIN_WINDOW_WIDTH = 600
    MIN_WINDOW_HEIGHT = 400

    # 定时器间隔
    UPDATE_INTERVAL = 50  # ms
    ANIMATION_DURATION = 300  # ms

    # 文件路径
    CONFIG_FILE = "config.ini"
    LOG_FILE = "app.log"

    # 信号常量
    SIGNALS = {
        'DATA_UPDATED': 'data_updated',
        'PROGRESS_CHANGED': 'progress_changed',
        'ERROR_OCCURRED': 'error_occurred'
    }
```

### 4. 错误处理
```python
# src/utils/error_handler.py
import logging
from functools import wraps

def handle_errors(default_return=None, log_error=True):
    """错误处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logging.error(f"Error in {func.__name__}: {str(e)}")
                return default_return
        return wrapper
    return decorator

# 使用示例
@handle_errors(default_return=0)
def calculate_something(self):
    # 可能出错的计算
    return risky_calculation()
```

---

## 📦 部署和发布

### 1. 使用PyInstaller打包
```bash
# 安装PyInstaller
pip install pyinstaller

# 创建可执行文件
pyinstaller --name "MyApp" --windowed --onefile main.py

# 使用spec文件进行高级配置
pyinstaller myapp.spec
```

### 2. spec文件示例
```python
# myapp.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['/path/to/app'],
    binaries=[],
    datas=[
        ('config/*', 'config'),
        ('resources/*', 'resources'),
    ],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MyApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/app.ico',  # Windows图标
    version='version_info.txt',  # Windows版本信息
)
```

### 3. 版本信息文件
```ini
# version_info.txt
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'My Company'),
        StringStruct(u'FileDescription', u'My Application'),
        StringStruct(u'FileVersion', u'1.0.0'),
        StringStruct(u'InternalName', u'MyApp'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2024'),
        StringStruct(u'OriginalFilename', u'MyApp.exe'),
        StringStruct(u'ProductName', u'My Application'),
        StringStruct(u'ProductVersion', u'1.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

### 4. 自动化构建脚本
```python
# build.py
import os
import subprocess
import sys

def build_app():
    """构建应用"""
    print("开始构建应用...")

    # 清理旧的构建文件
    if os.path.exists('dist'):
        import shutil
        shutil.rmtree('dist')

    if os.path.exists('build'):
        import shutil
        shutil.rmtree('build')

    # 运行PyInstaller
    try:
        subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--name', 'MyApp',
            '--windowed',
            '--onefile',
            '--add-data', 'config;config',
            '--add-data', 'resources;resources',
            'main.py'
        ], check=True)

        print("✅ 构建成功！")
        print(f"可执行文件位置: {os.path.abspath('dist/MyApp.exe')}")

    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        return False

    return True

if __name__ == "__main__":
    build_app()
```

### 5. 测试打包结果
```python
# test_build.py
import subprocess
import time
import sys

def test_build():
    """测试构建的应用"""
    exe_path = "dist/MyApp.exe"

    if not os.path.exists(exe_path):
        print("❌ 可执行文件不存在")
        return False

    print("启动应用进行测试...")
    try:
        # 启动应用
        process = subprocess.Popen([exe_path])

        # 等待几秒
        time.sleep(5)

        # 检查进程是否还在运行
        if process.poll() is None:
            print("✅ 应用启动成功")
            # 终止进程
            process.terminate()
            return True
        else:
            print("❌ 应用启动失败")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_build()
```

---

## 💡 总结

这些实战技巧涵盖了PySide6开发中的各个方面：

1. **性能优化**：关注UI更新频率、线程安全和内存管理
2. **设计模式**：使用MVC、观察者和工厂模式提高代码质量
3. **调试测试**：掌握调试技巧和单元测试方法
4. **问题解决**：处理常见的线程、内存和样式问题
5. **代码组织**：采用模块化结构和配置管理
6. **部署发布**：使用PyInstaller打包和自动化构建

通过实践这些技巧，你可以开发出高质量、高性能的PySide6应用程序！