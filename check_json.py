import os
import json

# 指定文件路径
file_path = 'tests/test_config.json'

# 检查文件是否存在
if not os.path.exists(file_path):
    print(f"错误: 文件 {file_path} 不存在")
    exit(1)

# 尝试读取并解析JSON文件
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"文件内容长度: {len(content)} 字符")
        print(f"前50个字符: {content[:50]}")
        print(f"后50个字符: {content[-50:]}")
        
        # 尝试解析JSON
        data = json.loads(content)
        print("✅ JSON格式验证成功")
        
        # 打印文件结构
        print("\n文件结构:")
        for key in data:
            print(f"- {key}: {type(data[key])}")
            if isinstance(data[key], list):
                print(f"  列表长度: {len(data[key])}")
            elif isinstance(data[key], dict):
                print(f"  字典键数量: {len(data[key])}")
                for subkey in data[key]:
                    print(f"    - {subkey}: {type(data[key][subkey])}")
                    
except json.JSONDecodeError as e:
    print(f"❌ JSON解析错误: {e}")
    print(f"错误位置: 第{e.lineno}行, 第{e.colno}列")
except UnicodeDecodeError as e:
    print(f"❌ 编码错误: {e}")
    print("尝试使用其他编码...")
    # 尝试使用其他常见编码
    for encoding in ['utf-8-sig', 'gbk', 'gb2312', 'ansi']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                print(f"✅ 使用 {encoding} 编码成功读取文件")
                try:
                    data = json.loads(content)
                    print(f"✅ 使用 {encoding} 编码解析JSON成功")
                    break
                except json.JSONDecodeError:
                    print(f"❌ 使用 {encoding} 编码解析JSON失败")
        except UnicodeDecodeError:
            print(f"❌ 使用 {encoding} 编码读取失败")
except Exception as e:
    print(f"❌ 发生未知错误: {e}")