#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能小数识别配置管理
提供多种VAD配置方案，平衡精度和响应速度
"""

import yaml
import os
from typing import Dict, Any

class SmartDecimalConfig:
    """智能小数配置管理器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.original_config = None
        self.load_config()

    def load_config(self):
        """加载当前配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.original_config = yaml.safe_load(f)
        except Exception as e:
            print(f"❌ 加载配置失败: {e}")

    def get_current_vad_mode(self) -> str:
        """获取当前VAD模式"""
        if not self.original_config:
            return "unknown"

        return self.original_config.get('vad', {}).get('mode', 'unknown')

    def create_decimal_optimized_profile(self) -> Dict[str, Any]:
        """创建针对数字识别优化的VAD配置文件"""

        return {
            'name': 'decimal_optimized',
            'description': '数字识别优化配置 - 在响应速度和精度间取得平衡',
            'vad_config': {
                'energy_threshold': 0.011,      # 稍微降低敏感度
                'min_speech_duration': 0.25,    # 较短的最小语音时长
                'min_silence_duration': 0.9,    # 适中的静音容忍 (0.9秒)
                'speech_padding': 0.35          # 适中的语音填充
            },
            'pros': [
                '✅ 支持小数点后4-6位数字',
                '✅ 响应延迟适中 (+0.3秒)',
                '✅ 适合大多数数字识别场景'
            ],
            'cons': [
                '⚠️ 极长小数(8位+)可能仍有截断',
                '⚠️ 数字间需要轻微连续性'
            ],
            'best_for': '日常数字识别，如测量、价格、温度等'
        }

    def create_high_precision_profile(self) -> Dict[str, Any]:
        """创建高精度数字识别配置"""

        return {
            'name': 'high_precision_decimal',
            'description': '高精度数字识别配置 - 优先保证完整识别',
            'vad_config': {
                'energy_threshold': 0.010,      # 高敏感度
                'min_speech_duration': 0.3,     # 较长最小语音时长
                'min_silence_duration': 1.2,    # 较长静音容忍 (1.2秒)
                'speech_padding': 0.45          # 较长语音填充
            },
            'pros': [
                '✅ 支持小数点后6-8位数字',
                '✅ 对长数字序列识别效果好',
                '✅ 适合精确测量场景'
            ],
            'cons': [
                '❌ 响应延迟较明显 (+0.6秒)',
                '❌ 可能影响对话流畅性'
            ],
            'best_for': '科学测量、工程数据、精确读数'
        }

    def create_fast_response_profile(self) -> Dict[str, Any]:
        """创建快速响应配置（保持原有体验）"""

        return {
            'name': 'fast_response',
            'description': '快速响应配置 - 保持原有响应速度',
            'vad_config': {
                'energy_threshold': 0.012,      # 原始设置
                'min_speech_duration': 0.2,     # 原始设置
                'min_silence_duration': 0.6,    # 原始设置
                'speech_padding': 0.4           # 原始设置
            },
            'pros': [
                '✅ 保持最快的响应速度',
                '✅ 对话体验流畅',
                '✅ 适合日常交流'
            ],
            'cons': [
                '❌ 小数识别限制在3位以内',
                '❌ 长数字序列易被截断'
            ],
            'best_for': '日常对话、命令识别、简单交流'
        }

    def apply_profile(self, profile_name: str) -> bool:
        """应用指定的配置文件"""

        profiles = {
            'decimal_optimized': self.create_decimal_optimized_profile(),
            'high_precision_decimal': self.create_high_precision_profile(),
            'fast_response': self.create_fast_response_profile()
        }

        if profile_name not in profiles:
            print(f"❌ 未知的配置文件: {profile_name}")
            return False

        profile = profiles[profile_name]
        vad_config = profile['vad_config']

        # 备份原配置
        if self.original_config:
            backup_path = f"{self.config_path}.backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.original_config, f, allow_unicode=True, default_flow_style=False)
            print(f"✅ 原配置已备份到: {backup_path}")

        # 应用新配置
        try:
            self.original_config['vad']['mode'] = 'customized'
            self.original_config['vad']['energy_threshold'] = vad_config['energy_threshold']
            self.original_config['vad']['min_speech_duration'] = vad_config['min_speech_duration']
            self.original_config['vad']['min_silence_duration'] = vad_config['min_silence_duration']
            self.original_config['vad']['speech_padding'] = vad_config['speech_padding']

            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.original_config, f, allow_unicode=True, default_flow_style=False)

            print(f"✅ 已应用配置文件: {profile['name']}")
            print(f"📝 描述: {profile['description']}")
            print(f"🎯 适用场景: {profile['best_for']}")

            print("\n📊 配置详情:")
            for key, value in vad_config.items():
                print(f"   {key}: {value}")

            print("\n✨ 优点:")
            for pro in profile['pros']:
                print(f"   {pro}")

            if profile['cons']:
                print("\n⚠️ 缺点:")
                for con in profile['cons']:
                    print(f"   {con}")

            return True

        except Exception as e:
            print(f"❌ 应用配置失败: {e}")
            return False

    def show_current_status(self):
        """显示当前配置状态"""
        print("🔍 当前VAD配置状态")
        print("=" * 60)

        if not self.original_config:
            print("❌ 无法加载配置文件")
            return

        vad_config = self.original_config.get('vad', {})
        current_mode = vad_config.get('mode', 'unknown')

        print(f"📋 当前模式: {current_mode}")

        if current_mode == 'customized':
            print("📊 自定义参数:")
            print(f"   energy_threshold: {vad_config.get('energy_threshold', 'N/A')}")
            print(f"   min_speech_duration: {vad_config.get('min_speech_duration', 'N/A')}")
            print(f"   min_silence_duration: {vad_config.get('min_silence_duration', 'N/A')}")
            print(f"   speech_padding: {vad_config.get('speech_padding', 'N/A')}")

            # 分析当前配置的特性
            silence_duration = vad_config.get('min_silence_duration', 0.6)
            if silence_duration <= 0.6:
                print("\n⚡ 当前配置特点: 快速响应")
                print("   ✅ 响应速度快")
                print("   ⚠️ 小数识别可能限制在3位")
            elif silence_duration <= 1.0:
                print("\n⚖️ 当前配置特点: 平衡模式")
                print("   ✅ 支持小数点后4-6位")
                print("   ⚠️ 响应延迟适中")
            else:
                print("\n🎯 当前配置特点: 高精度模式")
                print("   ✅ 支持长数字序列")
                print("   ⚠️ 响应延迟较明显")

    def interactive_config_selection(self):
        """交互式配置选择"""
        print("🎛️ 智能小数识别配置选择")
        print("=" * 60)

        self.show_current_status()

        print("\n📋 可用配置文件:")
        profiles = [
            ('fast_response', self.create_fast_response_profile()),
            ('decimal_optimized', self.create_decimal_optimized_profile()),
            ('high_precision_decimal', self.create_high_precision_profile())
        ]

        for i, (key, profile) in enumerate(profiles, 1):
            print(f"\n{i}. {profile['name']}")
            print(f"   描述: {profile['description']}")
            print(f"   适用: {profile['best_for']}")

        print(f"\n{len(profiles)+1}. 恢复原配置")
        print("0. 退出")

        while True:
            try:
                choice = input(f"\n请选择配置文件 (0-{len(profiles)+1}): ").strip()

                if choice == '0':
                    print("👋 退出配置")
                    break
                elif choice == str(len(profiles)+1):
                    self.restore_backup()
                    break
                elif choice.isdigit() and 1 <= int(choice) <= len(profiles):
                    profile_key = profiles[int(choice)-1][0]
                    success = self.apply_profile(profile_key)
                    if success:
                        print(f"\n✅ 配置已更新！建议重新启动语音识别程序测试效果。")
                        break
                else:
                    print("❌ 无效选择，请重试")
            except KeyboardInterrupt:
                print("\n\n👋 配置已取消")
                break

    def restore_backup(self):
        """恢复备份配置"""
        backup_path = f"{self.config_path}.backup"
        if os.path.exists(backup_path):
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_config = yaml.safe_load(f)

                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(backup_config, f, allow_unicode=True, default_flow_style=False)

                print("✅ 已恢复原配置")
            except Exception as e:
                print(f"❌ 恢复配置失败: {e}")
        else:
            print("❌ 未找到备份配置文件")

if __name__ == "__main__":
    config_manager = SmartDecimalConfig()

    print("🎯 小数识别配置管理工具")
    print("=" * 60)

    # 显示当前状态
    config_manager.show_current_status()

    # 提供交互式选择
    print(f"\n🛠️ 是否要调整配置以改善小数识别？")
    print("   输入 'y' 进入配置选择")
    print("   输入其他任意键退出")

    user_input = input("您的选择: ").strip().lower()
    if user_input == 'y':
        config_manager.interactive_config_selection()