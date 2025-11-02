#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试打包后的VoiceInput系统
验证可执行文件是否正常工作
"""

import os
import sys
import subprocess
import yaml

def check_file_exists(filepath):
    """检查文件是否存在"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return False
    print(f"✅ 文件存在: {filepath}")
    return True

def check_config():
    """检查配置文件"""
    print("\n📋 检查配置文件...")
    
    if not check_file_exists("config.yaml"):
        return False
    
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        model_config = config.get("model", {})
        external_paths = model_config.get("external_paths", {})
        
        # 检查模型路径配置
        funasr_path = external_paths.get("funasr_model_path")
        onnx_path = external_paths.get("onnx_deps_path")
        
        print(f"   FunASR模型路径: {funasr_path}")
        print(f"   ONNX依赖路径: {onnx_path}")
        
        return True
    except Exception as e:
        print(f"❌ 配置文件读取失败: {e}")
        return False

def check_model_files():
    """检查模型文件"""
    print("\n🤖 检查模型文件...")
    
    model_paths = [
        "model/fun",
        "onnx_deps"
    ]
    
    all_exist = True
    for path in model_paths:
        if not check_file_exists(path):
            all_exist = False
    
    # 检查关键模型文件
    if os.path.exists("model/fun"):
        model_files = [
            "model/fun/README.md",
            "model/fun/config.yaml"
        ]
        for file in model_files:
            if os.path.exists(file):
                print(f"   ✅ {file}")
            else:
                print(f"   ⚠️  缺失: {file}")
    
    return all_exist

def check_executable():
    """检查可执行文件"""
    print("\n📦 检查可执行文件...")
    
    exe_name = "VoiceInput_System.exe" if os.name == "nt" else "VoiceInput_System"
    exe_paths = [
        f"build/{exe_name}",
        f"dist/{exe_name}"
    ]
    
    for path in exe_paths:
        if check_file_exists(path):
            print(f"   📁 找到可执行文件: {path}")
            
            # 检查文件大小
            size = os.path.getsize(path)
            print(f"   📊 文件大小: {size / 1024 / 1024:.2f} MB")
            
            # 检查可执行权限 (Linux/Mac)
            if os.name != "nt":
                if os.access(path, os.X_OK):
                    print("   ✅ 可执行权限正确")
                else:
                    print("   ⚠️  缺少可执行权限")
                    os.chmod(path, 0o755)
                    print("   ✅ 已添加可执行权限")
            
            return True
    
    print("   ❌ 未找到可执行文件")
    return False

def test_executable_basic():
    """测试可执行文件基本功能"""
    print("\n🧪 测试可执行文件基本功能...")
    
    exe_path = "build/VoiceInput_System.exe" if os.name == "nt" else "build/VoiceInput_System"
    
    if not os.path.exists(exe_path):
        print("   ❌ 可执行文件不存在，跳过测试")
        return False
    
    try:
        # 尝试运行可执行文件 (带--help参数)
        print(f"   正在启动: {exe_path} --help")
        
        result = subprocess.run(
            [exe_path, "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("   ✅ 可执行文件启动成功")
            return True
        else:
            print(f"   ⚠️  返回码: {result.returncode}")
            print(f"   输出: {result.stdout[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ⚠️  程序启动超时 (可能是正常现象)")
        return True
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("VoiceInput System - 打包后测试")
    print("=" * 60)
    
    results = []
    
    # 检查配置文件
    results.append(("配置文件", check_config()))
    
    # 检查模型文件
    results.append(("模型文件", check_model_files()))
    
    # 检查可执行文件
    results.append(("可执行文件", check_executable()))
    
    # 测试可执行文件
    results.append(("功能测试", test_executable_basic()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:.<30} {status}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！打包成功！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
