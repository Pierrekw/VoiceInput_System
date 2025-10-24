#!/usr/bin/env python3
"""
精简voice_gui.py的脚本
删除测试代码、注释掉的代码和调试输出
"""

import re

def clean_voice_gui():
    """清理voice_gui.py文件"""
    file_path = "voice_gui.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    cleaned_lines = []
    skip_mode = False
    skip_indent = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # 删除测试相关方法
        if line.strip().startswith('def add_test_controls('):
            skip_mode = True
            skip_indent = len(line) - len(line.lstrip())
            i += 1
            continue
        elif line.strip().startswith('def direct_energy_test('):
            skip_mode = True
            skip_indent = len(line) - len(line.lstrip())
            i += 1
            continue
        elif line.strip().startswith('def test_energy_bar('):
            skip_mode = True
            skip_indent = len(line) - len(line.lstrip())
            i += 1
            continue
        elif line.strip().startswith('def update_energy_bar_randomly('):
            skip_mode = True
            skip_indent = len(line) - len(line.lstrip())
            i += 1
            continue

        # 检查是否应该退出跳过模式
        if skip_mode:
            current_indent = len(line) - len(line.lstrip())
            if line.strip() and current_indent <= skip_indent:
                skip_mode = False
            else:
                i += 1
                continue

        # 删除注释掉的代码行
        if line.strip().startswith('# ') and any(keyword in line for keyword in [
            '测试', 'test', 'Test', 'TEST', '调试', 'debug', 'Debug', 'DEBUG',
            '随机', 'random', 'Random', '移除', '删除', '废弃'
        ]):
            i += 1
            continue

        # 删除空的注释行
        if line.strip() == '#' or line.strip().startswith('# '):
            # 但保留有意义的注释
            if any(keyword in line for keyword in ['TODO', 'FIXME', '重要', '注意']):
                cleaned_lines.append(line)
            i += 1
            continue

        # 删除调试print语句
        if 'print(' in line and any(keyword in line for keyword in [
            'DEBUG', 'debug', 'CRITICAL', '测试', 'test', 'TEST', '随机'
        ]):
            i += 1
            continue

        # 删除空的append_log调试语句
        if 'append_log(' in line and any(keyword in line for keyword in [
            '[CRITICAL]', '[DEBUG]', '测试', 'test'
        ]):
            i += 1
            continue

        # 保留有用的行
        cleaned_lines.append(line)
        i += 1

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)

    print(f"✅ 已精简 {file_path}")
    print(f"📊 原始行数: {len(lines)}")
    print(f"📊 精简后行数: {len(cleaned_lines)}")
    print(f"📉 减少了 {len(lines) - len(cleaned_lines)} 行")

if __name__ == "__main__":
    clean_voice_gui()