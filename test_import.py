import sys
import os

# 打印当前工作目录
print(f"当前工作目录: {os.getcwd()}")

# 打印Python路径
print("\nPython路径:")
for path in sys.path:
    print(f"- {path}")

# 尝试导入async_audio模块
print("\n尝试导入async_audio模块...")
try:
    import async_audio
    print(f"成功导入async_audio模块，版本: {async_audio.__version__}")
    
    # 尝试导入async_audio_capture模块
    from async_audio import async_audio_capture
    print(f"成功导入async_audio_capture模块")
    
    # 打印模块中的类
    print("\nasync_audio_capture模块中的类和函数:")
    for attr in dir(async_audio_capture):
        if not attr.startswith('_'):
            print(f"- {attr}")
            
except ImportError as e:
    print(f"导入失败: {e}")
    
    # 尝试手动添加项目根目录到Python路径
    print("\n尝试手动添加项目根目录到Python路径...")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
    print(f"项目根目录: {project_root}")
    
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"已添加项目根目录到Python路径")
    
    # 再次尝试导入
    try:
        import async_audio
        print(f"成功导入async_audio模块，版本: {async_audio.__version__}")
    except ImportError as e2:
        print(f"仍然导入失败: {e2}")