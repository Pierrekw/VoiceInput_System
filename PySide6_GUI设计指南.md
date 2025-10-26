# PySide6 GUI设计指南 - 基于Voice Energy Bar项目

## 📚 目录
1. [PySide6基础架构](#pySide6基础架构)
2. [项目结构设计](#项目结构设计)
3. [自定义组件开发](#自定义组件开发)
4. [布局管理系统](#布局管理系统)
5. [样式与美化](#样式与美化)
6. [事件处理与信号槽](#事件处理与信号槽)
7. [实战案例：能量条项目](#实战案例能量条项目)
8. [最佳实践总结](#最佳实践总结)

---

## 🏗️ PySide6基础架构

### 核心组件层次
```
QApplication (应用入口)
    └── QMainWindow (主窗口)
        └── QWidget (中央部件)
            └── QLayout (布局管理器)
                └── QWidgets (各种控件)
```

### 基本应用模板
```python
#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 窗口基本设置
        self.setWindowTitle("我的应用")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建布局
        layout = QVBoxLayout(central_widget)
        # ... 添加控件

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

## 📁 项目结构设计

### 推荐的项目组织
```
my_gui_app/
├── main.py              # 应用入口
├── gui/
│   ├── __init__.py
│   ├── main_window.py   # 主窗口
│   ├── widgets/         # 自定义控件
│   │   ├── __init__.py
│   │   ├── energy_bar.py
│   │   └── status_panel.py
│   ├── dialogs/         # 对话框
│   └── resources/       # 资源文件
├── core/                # 业务逻辑
├── utils/               # 工具类
└── styles/              # 样式文件
```

### 模块化设计原则
```python
# gui/widgets/__init__.py
from .energy_bar import VoiceEnergyBar
from .status_panel import StatusPanel

# 导出所有自定义组件
__all__ = ['VoiceEnergyBar', 'StatusPanel']
```

---

## 🎛️ 自定义组件开发

### 继承标准控件
```python
from PySide6.QtWidgets import QProgressBar, QPropertyAnimation
from PySide6.QtCore import QTimer, QEasingCurve

class VoiceEnergyBar(QProgressBar):
    """自定义语音能量显示条"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_animation()
        self.setup_timer()

    def setup_ui(self):
        """基础UI设置"""
        # 数值范围
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)

        # 尺寸控制
        self.setFixedHeight(20)
        self.setTextVisible(False)  # 不显示百分比文本

        # 样式设置
        self.apply_styles()

    def setup_animation(self):
        """动画效果设置"""
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(100)  # 100ms动画
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

    def setup_timer(self):
        """定时器设置"""
        self.decay_timer = QTimer()
        self.decay_timer.timeout.connect(self.decay_energy)
        self.last_activity_time = 0

    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 8px;
                background-color: #f0f0f0;
                font-weight: bold;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 6px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1E88E5, stop:0.5 #2196F3, stop:1 #42A5F5);
                width: 8px;
                margin: 2px;
            }
        """)

    def update_energy(self, level):
        """更新能量级别"""
        # 数据验证
        level = max(0, min(100, level))

        # 停止衰减定时器
        self.decay_timer.stop()

        # 启动动画
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(level)
        self.animation.start()

        # 记录活动时间
        self.last_activity_time = 0

        # 重新启动衰减定时器
        self.decay_timer.start(200)  # 每200ms检查一次

    def decay_energy(self):
        """能量衰减效果"""
        current_value = self.value()
        if current_value > 0:
            new_value = max(0, current_value - 2)  # 每次减少2%
            self.setValue(new_value)

            if new_value == 0:
                self.decay_timer.stop()
```

### 组件复用技巧
```python
# 可配置的组件
class ConfigurableProgressBar(QProgressBar):
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config or {}
        self.apply_config()

    def apply_config(self):
        """根据配置应用设置"""
        if 'height' in self.config:
            self.setFixedHeight(self.config['height'])

        if 'range' in self.config:
            min_val, max_val = self.config['range']
            self.setMinimum(min_val)
            self.setMaximum(max_val)

        if 'style' in self.config:
            self.setStyleSheet(self.config['style'])
```

---

## 📐 布局管理系统

### 布局类型详解

#### 1. QVBoxLayout (垂直布局)
```python
from PySide6.QtWidgets import QVBoxLayout, QWidget

layout = QVBoxLayout()
layout.addWidget(widget1)          # 添加控件
layout.addWidget(widget2)
layout.addStretch()               # 添加弹簧
layout.setSpacing(10)             # 设置间距
layout.setContentsMargins(20, 20, 20, 20)  # 设置边距
```

#### 2. QHBoxLayout (水平布局)
```python
from PySide6.QtWidgets import QHBoxLayout

layout = QHBoxLayout()
layout.addWidget(widget1, stretch=1)  # 设置拉伸因子
layout.addWidget(widget2, stretch=2)
layout.addSpacing(50)                 # 添加固定间距
```

#### 3. QGridLayout (网格布局)
```python
from PySide6.QtWidgets import QGridLayout

layout = QGridLayout()
layout.addWidget(widget1, 0, 0)      # 第0行第0列
layout.addWidget(widget2, 0, 1)      # 第0行第1列
layout.addWidget(widget3, 1, 0, 1, 2) # 第1行第0列，跨2列
layout.setColumnStretch(0, 1)         # 设置列拉伸
layout.setRowStretch(1, 2)            # 设置行拉伸
```

#### 4. QFormLayout (表单布局)
```python
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit

layout = QFormLayout()
layout.addRow("姓名:", QLineEdit())
layout.addRow("邮箱:", QLineEdit())
layout.addRow(QLabel("备注:"), QTextEdit())
```

### 高级布局技巧

#### 分割窗口 (QSplitter)
```python
from PySide6.QtWidgets import QSplitter

splitter = QSplitter(Qt.Horizontal)  # 水平分割
splitter.addWidget(left_panel)
splitter.addWidget(right_panel)
splitter.setSizes([300, 600])        # 初始大小
splitter.setStretchFactor(0, 1)     # 左侧不拉伸
splitter.setStretchFactor(1, 3)     # 右侧拉伸3倍
```

#### 滚动区域 (QScrollArea)
```python
from PySide6.QtWidgets import QScrollArea

scroll_area = QScrollArea()
scroll_area.setWidgetResizable(True)
scroll_area.setWidget(content_widget)
```

---

## 🎨 样式与美化

### QSS样式表基础

#### 语法结构
```css
选择器 {
    属性名: 属性值;
    属性名: 属性值;
}

/* 状态伪类 */
QPushButton:hover {
    background-color: #1976d2;
}

QPushButton:pressed {
    background-color: #0d47a1;
}

/* 子控件选择器 */
QProgressBar::chunk {
    background: qlineargradient(...);
}
```

#### 常用样式示例
```python
styles = """
/* 按钮样式 */
QPushButton {
    background-color: #2196f3;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1976d2;
}

QPushButton:pressed {
    background-color: #0d47a1;
}

QPushButton:disabled {
    background-color: #ccc;
    color: #666;
}

/* 分组框样式 */
QGroupBox {
    font-weight: bold;
    border: 2px solid #ddd;
    border-radius: 8px;
    margin-top: 1ex;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}

/* 文本框样式 */
QTextEdit {
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: white;
    font-family: 'Consolas', monospace;
    font-size: 11px;
}

/* 进度条样式 */
QProgressBar {
    border: 2px solid #2196F3;
    border-radius: 8px;
    background-color: #f0f0f0;
    text-align: center;
}

QProgressBar::chunk {
    border-radius: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1E88E5, stop:0.5 #2196F3, stop:1 #42A5F5);
    width: 8px;
    margin: 2px;
}
"""
```

### 动态样式切换
```python
class StyleManager:
    def __init__(self):
        self.styles = {
            'light': self.load_light_style(),
            'dark': self.load_dark_style(),
            'blue': self.load_blue_style()
        }

    def apply_style(self, widget, style_name):
        widget.setStyleSheet(self.styles[style_name])

    def load_light_style(self):
        return """
        QWidget {
            background-color: white;
            color: black;
        }
        """

    def load_dark_style(self):
        return """
        QWidget {
            background-color: #2b2b2b;
            color: white;
        }
        """
```

---

## ⚡ 事件处理与信号槽

### 信号槽基础
```python
from PySide6.QtCore import Signal, QObject

class Worker(QObject):
    # 自定义信号
    progress_updated = Signal(int)
    task_finished = Signal(str)

    def do_work(self):
        for i in range(101):
            self.progress_updated.emit(i)  # 发送信号
            time.sleep(0.01)

        self.task_finished.emit("工作完成")

# 连接信号槽
worker = Worker()
worker.progress_updated.connect(progress_bar.setValue)
worker.task_finished.connect(show_message)
```

### 线程间通信
```python
from PySide6.QtCore import QThread, Signal

class BackgroundWorker(QThread):
    result_ready = Signal(str)
    error_occurred = Signal(str)

    def run(self):
        try:
            result = self.long_running_task()
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

# 使用示例
worker = BackgroundWorker()
worker.result_ready.connect(lambda x: text_edit.setText(x))
worker.error_occurred.connect(lambda x: show_error(x))
worker.start()
```

### 事件过滤
```python
from PySide6.QtCore import QEvent, QObject

class EventFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                print("ESC键被按下")
                return True  # 事件已处理

        return super().eventFilter(obj, event)

# 应用事件过滤器
event_filter = EventFilter()
widget.installEventFilter(event_filter)
```

---

## 🎯 实战案例：能量条项目

### 完整的项目架构
```python
# main.py - 应用入口
import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Voice Energy Monitor")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

### 主窗口设计
```python
# gui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QGroupBox, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from .widgets import VoiceEnergyBar, ControlPanel, DisplayPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_timer()
        self.setup_connections()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("Voice Energy Monitor v2.0")
        self.setMinimumSize(1000, 700)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧控制面板
        self.control_panel = ControlPanel()
        main_layout.addWidget(self.control_panel)

        # 右侧显示面板
        self.display_panel = DisplayPanel()
        main_layout.addWidget(self.display_panel)

        # 设置比例
        main_layout.setStretchFactor(0, 1)
        main_layout.setStretchFactor(1, 2)

        # 应用样式
        self.apply_global_style()

    def setup_timer(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(50)  # 20 FPS

    def setup_connections(self):
        """设置信号连接"""
        self.control_panel.start_button.clicked.connect(self.start_monitoring)
        self.control_panel.stop_button.clicked.connect(self.stop_monitoring)

        # 模拟能量数据
        self.control_panel.test_energy.connect(self.display_panel.energy_bar.update_energy)

    def apply_global_style(self):
        """应用全局样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

    def start_monitoring(self):
        """开始监控"""
        self.update_timer.start()
        self.control_panel.set_running_state(True)

    def stop_monitoring(self):
        """停止监控"""
        self.update_timer.stop()
        self.control_panel.set_running_state(False)

    def update_display(self):
        """更新显示"""
        # 这里可以添加实际的能量数据更新逻辑
        pass
```

### 控制面板设计
```python
# gui/widgets/control_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QComboBox, QSpinBox
)
from PySide6.QtCore import Signal, QObject

class ControlPanel(QWidget):
    # 自定义信号
    test_energy = Signal(int)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_test_timer()

    def init_ui(self):
        """初始化控制面板UI"""
        layout = QVBoxLayout(self)

        # 能量显示组
        energy_group = QGroupBox("能量监控")
        energy_layout = QVBoxLayout(energy_group)

        energy_label = QLabel("🎤 语音能量检测:")
        energy_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        energy_layout.addWidget(energy_label)

        self.energy_value_label = QLabel("当前能量: 0%")
        self.energy_value_label.setStyleSheet("font-size: 12px; color: #666;")
        energy_layout.addWidget(self.energy_value_label)

        layout.addWidget(energy_group)

        # 控制按钮组
        control_group = QGroupBox("控制")
        control_layout = QVBoxLayout(control_group)

        self.start_button = QPushButton("🎙️ 开始监控")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        control_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("🛑 停止监控")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        control_layout.addWidget(self.stop_button)

        layout.addWidget(control_group)

        # 测试控制组
        test_group = QGroupBox("测试")
        test_layout = QVBoxLayout(test_group)

        self.test_button = QPushButton("🧪 测试能量条")
        self.test_button.clicked.connect(self.test_energy_bar)
        test_layout.addWidget(self.test_button)

        # 随机测试
        self.random_button = QPushButton("🎲 随机能量")
        self.random_button.clicked.connect(self.toggle_random_test)
        test_layout.addWidget(self.random_button)

        layout.addWidget(test_group)

        layout.addStretch()  # 添加弹簧

    def setup_test_timer(self):
        """设置测试定时器"""
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self.generate_random_energy)
        self.random_enabled = False

    def test_energy_bar(self):
        """测试能量条"""
        # 发送测试能量值
        test_values = [25, 50, 75, 100, 75, 50, 25, 0]
        for value in test_values:
            self.test_energy.emit(value)

    def toggle_random_test(self):
        """切换随机测试"""
        self.random_enabled = not self.random_enabled

        if self.random_enabled:
            self.test_timer.start(200)  # 每200ms更新一次
            self.random_button.setText("⏹️ 停止随机")
        else:
            self.test_timer.stop()
            self.random_button.setText("🎲 随机能量")

    def generate_random_energy(self):
        """生成随机能量值"""
        import random
        value = random.randint(0, 100)
        self.test_energy.emit(value)
        self.energy_value_label.setText(f"当前能量: {value}%")

    def set_running_state(self, running):
        """设置运行状态"""
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
```

### 显示面板设计
```python
# gui/widgets/display_panel.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QTextEdit, QLabel, QProgressBar
)
from .energy_bar import VoiceEnergyBar
from .chart_widget import EnergyChart

class DisplayPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化显示面板UI"""
        layout = QVBoxLayout(self)

        # 能量条显示
        energy_group = QGroupBox("实时能量显示")
        energy_layout = QVBoxLayout(energy_group)

        self.energy_bar = VoiceEnergyBar()
        energy_layout.addWidget(self.energy_bar)

        layout.addWidget(energy_group)

        # 能量图表
        chart_group = QGroupBox("能量历史图表")
        chart_layout = QVBoxLayout(chart_group)

        self.energy_chart = EnergyChart()
        chart_layout.addWidget(self.energy_chart)

        layout.addWidget(chart_group)

        # 日志显示
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', monospace;
                font-size: 10px;
                border: 1px solid #555;
            }
        """)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def log_message(self, message):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)

        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
```

---

## 💡 最佳实践总结

### 1. 代码组织
- **模块化设计**：将UI组件分离到独立模块
- **单一职责**：每个类只负责一个功能
- **配置外部化**：样式和配置放在外部文件

### 2. 性能优化
- **避免频繁更新**：使用定时器控制更新频率
- **合理使用线程**：耗时操作放在后台线程
- **内存管理**：及时释放不需要的资源

### 3. 用户体验
- **响应式设计**：支持窗口缩放
- **视觉反馈**：提供状态变化提示
- **键盘快捷键**：提供快捷操作方式

### 4. 错误处理
- **异常捕获**：捕获并妥善处理异常
- **用户提示**：友好的错误信息显示
- **日志记录**：记录关键操作和错误

### 5. 可维护性
- **代码注释**：添加清晰的注释
- **命名规范**：使用有意义的变量和函数名
- **版本控制**：使用Git等工具管理代码

---

## 🚀 扩展学习建议

1. **深入学习Qt框架**：了解更多Qt类和功能
2. **学习QML**：用于创建更现代的UI
3. **数据库集成**：学习如何与数据库交互
4. **网络编程**：实现客户端-服务器应用
5. **打包发布**：学习如何打包GUI应用

希望这份指南能帮助你掌握PySide6 GUI开发！记住，最好的学习方式是实践，尝试修改和扩展示例代码。