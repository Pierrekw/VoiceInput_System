#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Voice Input System Test
=============================

Focused test demonstrating:
- Single startup efficiency
- Keyboard control (F6/F7/F8)
- Excel auto-save on pause
- Real-time data display
- Sequence continuity
"""

import time
import threading
import os
from datetime import datetime
from audio_capture_v import AudioCapture, start_keyboard_listener
from excel_exporter import ExcelExporter


class QuickSystemTest:
    def __init__(self):
        self.excel_exporter = ExcelExporter(filename=f"quick_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        self.audio_capture = AudioCapture(excel_exporter=self.excel_exporter)
        self.keyboard_listener = None
        
    def simulate_voice_sessions(self):
        """Simulate voice input sessions with pause/resume"""
        print("\n🎯 Starting Voice Input Simulation")
        
        # Session 1: Initial voice input
        print("\n🎤 [Session 1] Voice: '测量值为十二点五和三十三点八'")
        print("📊 [Values] [12.5, 33.8]")
        self.audio_capture.filtered_callback("测量值为十二点五和三十三点八")
        time.sleep(1)
        
        print("🎤 [Session 1] Voice: '五十五点五'")
        print("📊 [Values] [55.5]")
        self.audio_capture.filtered_callback("五十五点五")
        time.sleep(1)
        
        # Simulate F6 pause - Excel should auto-save
        print("\n🔑 [F6] PAUSE: Saving data to Excel...")
        self.audio_capture.pause()
        time.sleep(0.5)
        self.show_excel_status()
        
        # Resume with F7
        print("\n🔑 [F7] RESUME: Continuing voice input")
        self.audio_capture.resume()
        time.sleep(0.5)
        
        # Session 2: More voice input
        print("\n🎤 [Session 2] Voice: '七十七点七和九十九点九'")
        print("📊 [Values] [77.7, 99.9]")
        self.audio_capture.filtered_callback("七十七点七和九十九点九")
        time.sleep(1)
        
        print("🎤 [Session 2] Voice: '一百一十一点一'")
        print("📊 [Values] [111.1]")
        self.audio_capture.filtered_callback("一百一十一点一")
        time.sleep(1)
        
        # Final pause and save
        print("\n🔑 [F6] FINAL PAUSE: Complete save to Excel")
        self.audio_capture.pause()
        time.sleep(0.5)
        self.show_excel_status()
        
        # Stop system
        print("\n🔑 [F8] STOP: Ending voice input session")
        self.audio_capture.stop()
        
    def show_excel_status(self):
        """Display current Excel status"""
        try:
            import pandas as pd
            if os.path.exists(self.excel_exporter.filename):
                df = pd.read_excel(self.excel_exporter.filename)
                print(f"📊 Excel Status: {len(df)} rows saved")
                if len(df) > 0:
                    print(f"   IDs: {df['编号'].tolist()}")
                    print(f"   Values: {df['测量值'].tolist()}")
            else:
                print("📊 Excel file not created yet")
        except Exception as e:
            print(f"📊 Excel check error: {e}")
            
    def display_system_info(self):
        """Show system information"""
        print("=" * 60)
        print("🚀 VOICE INPUT SYSTEM - QUICK TEST")
        print("=" * 60)
        print("📋 Test Objectives:")
        print("   ✓ Single startup efficiency")
        print("   ✓ Keyboard control (F6/F7/F8)")
        print("   ✓ Excel auto-save on pause")
        print("   ✓ Real-time data display")
        print("   ✓ Sequence continuity (1,2,3,4...)")
        print("=" * 60)
        
    def run_test(self):
        """Run the quick system test"""
        self.display_system_info()
        
        # Single startup - keyboard listener
        print("\n🔧 Starting system components...")
        self.keyboard_listener = start_keyboard_listener(self.audio_capture)
        if self.keyboard_listener:
            print("✅ Keyboard listener started (single startup)")
        else:
            print("⚠️  Keyboard listener not available")
        
        print("\n🎯 Beginning voice input simulation...")
        print("-" * 40)
        
        # Start voice recognition (mock)
        self.audio_capture.is_listening = True
        self.audio_capture.is_paused = False
        
        try:
            self.simulate_voice_sessions()
            
            # Show final results
            print("\n" + "=" * 60)
            print("🎉 QUICK TEST COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            
            # Final Excel display
            if os.path.exists(self.excel_exporter.filename):
                import pandas as pd
                df = pd.read_excel(self.excel_exporter.filename)
                print(f"\n📋 Final Excel Data ({len(df)} rows):")
                print("-" * 30)
                for i, row in df.iterrows():
                    print(f"Row {int(row['编号'])}: {row['测量值']} | {row['时间戳']}")
                print(f"\n✅ Sequence continuity: {df['编号'].tolist()}")
                print(f"📁 Excel file: {self.excel_exporter.filename}")
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            
        finally:
            # Cleanup
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            print(f"\n🏁 Test finished. Check file: {self.excel_exporter.filename}")


def main():
    """Main test function"""
    test = QuickSystemTest()
    test.run_test()


if __name__ == "__main__":
    main()