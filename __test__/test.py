from contextlib import contextmanager

@contextmanager
def my_context():
    # 1. __enter__ 部分（前置操作）
    print("进入上下文")
    try:
        yield "资源对象"  # 类似于 __enter__ 的返回值
    finally:
        # 2. __exit__ 部分（后置操作）
        print("退出上下文")

# 使用方式
with my_context() as resource:
    print(f"使用资源: {resource}")