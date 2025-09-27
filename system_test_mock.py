#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice Input System - Comprehensive Mock Test
=============================================

This script provides a complete system test that simulates:
1. Voice recognition with predefined test data
2. Keyboard control simulation (F6/F7/F8)
3. Real-time display of text and numeric data
4. Excel auto-save on pause functionality
5. Resource-efficient single startup

Usage:
    python system_test_mock.py
"""

import time
import threading
import random
import os
from datetime import datetime
from audio_capture_v import AudioCapture, start_keyboard_listener
from excel_exporter import ExcelExporter

# Mock test data - simulates voice recognition results
MOCK_VOICE_DATA = [
    # Session 1: Initial measurements
    {"text": "测量值为十二点五和三十三点八", "values": [12.5, 33.8], "delay": 2},
    {"text": "五十五点五", "values": [55.5], "delay": 1.5},
    
    # Session 2: After pause/resume
    {"text": "七十七点七和九十九点九", "values": [77.7, 99.9], "delay": 2.5},
    {"text": "一百一十一点一", "values": [111.1], "delay": 1},
    
    # Session 3: Final measurements
    {"text": "测量数据为一百二十三点四", "values": [123.4], "delay": 2},
    {"text": "二百五十六点七八", "values": [256.78], "delay": 1.5},
]

# Keyboard control simulation
KEYBOARD_COMMANDS = [
    {"key": "F6", "action": "PAUSE", "delay": 4, "description": "Pause recording"},
    {"key": "F7", "action": "RESUME", "delay": 2, "description": "Resume recording"},
    {"key": "F6", "action": "PAUSE", "delay": 5, "description": "Pause again"},
    {"key": "F7", "action": "RESUME", "delay": 1.5, "description": "Resume again"},
    {"key": "F8", "action": "STOP", "delay": 4, "description": "Stop and exit"},
]


class MockAudioCapture(AudioCapture):
    """Enhanced AudioCapture with mock voice data for testing"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mock_data_index = 0
        self.is_test_running = True
        self.total_values_extracted = 0
        self.session_count = 0
        
    def mock_voice_input(self):
        """Simulate voice input with predefined test data"""
        while self.is_test_running and self.mock_data_index < len(MOCK_VOICE_DATA):
            if not self.is_paused and self.is_listening:
                # Get next mock voice data
                voice_data = MOCK_VOICE_DATA[self.mock_data_index]
                
                print(f"\n🎤 [VOICE] {voice_data['text']}")
                print(f"📊 [VALUES] {voice_data['values']}")
                
                # Simulate the filtered_callback processing
                for value in voice_data['values']:
                    self.filtered_callback(str(value))
                
                self.mock_data_index += 1
                self.total_values_extracted += len(voice_data['values'])
                
                # Wait before next voice input
                time.sleep(voice_data['delay'])
            else:
                time.sleep(0.1)  # Small delay when paused
    
    def listen_realtime_vosk(self):
        """Override to use mock voice input instead of real audio"""
        print("🎯 Mock Voice Input System Started")
        print("📋 Test data sequence will simulate real voice recognition")
        print("⌨️  Keyboard controls: F6=Pause, F7=Resume, F8=Stop")
        print("-" * 60)
        
        self.is_listening = True
        self.is_paused = False
        self._pause_event.set()
        self.session_count = 0
        
        # Start mock voice input in separate thread
        voice_thread = threading.Thread(target=self.mock_voice_input, daemon=True)
        voice_thread.start()
        
        # Wait for test completion or stop
        try:
            while self.is_listening and self.is_test_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
        
        # Ensure mock input stops
        self.is_test_running = False
        voice_thread.join(timeout=1)
        
        print(f"\n📈 Test Summary:")
        print(f"   Total sessions: {self.session_count}")
        print(f"   Values extracted: {self.total_values_extracted}")
        print(f"   Excel rows: {len(self.buffered_values)}")
        
        return {
            "final": "Mock test completed",
            "buffered_values": list(self.buffered_values),
        }


class SystemTestController:
    """Controller to manage the complete system test"""
    
    def __init__(self):
        self.excel_exporter = ExcelExporter(filename=f"voice_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        self.audio_capture = MockAudioCapture(
            timeout_seconds=60,
            excel_exporter=self.excel_exporter
        )
        self.keyboard_listener = None
        self.test_start_time = None
        
    def simulate_keyboard_controls(self):
        """Simulate keyboard controls in a separate thread"""
        print("\n⌨️  Keyboard Control Simulation Started")
        
        for cmd in KEYBOARD_COMMANDS:
            time.sleep(cmd["delay"])
            
            if not self.audio_capture.is_listening:
                break
                
            print(f"\n🔑 [{cmd['key']}] {cmd['action']}: {cmd['description']}")
            
            if cmd["action"] == "PAUSE":
                self.audio_capture.pause()
                # During pause, check Excel file
                if os.path.exists(self.excel_exporter.filename):
                    self.show_excel_status()
                    
            elif cmd["action"] == "RESUME":
                self.audio_capture.resume()
                
            elif cmd["action"] == "STOP":
                self.audio_capture.stop()
                break
    
    def show_excel_status(self):
        """Display current Excel file status"""
        try:
            import pandas as pd
            if os.path.exists(self.excel_exporter.filename):
                df = pd.read_excel(self.excel_exporter.filename)
                print(f"\n📊 Excel Status: {len(df)} rows saved")
                if len(df) > 0:
                    print(f"   Last row: ID={int(df.iloc[-1]['编号'])}, Value={df.iloc[-1]['测量值']}")
                    print(f"   IDs range: {int(df['编号'].min())} - {int(df['编号'].max())}")
            else:
                print("\n📊 Excel file not created yet")
        except Exception as e:
            print(f"📊 Excel status check failed: {e}")
    
    def display_system_status(self):
        """Display real-time system status"""
        while self.audio_capture.is_listening:
            status = "RUNNING" if self.audio_capture.is_running else "PAUSED"
            buffer_size = len(self.audio_capture.buffered_values)
            
            print(f"\n💻 System Status: {status} | Buffer: {buffer_size} values | "
                  f"Total extracted: {self.audio_capture.total_values_extracted}")
            
            time.sleep(3)  # Update every 3 seconds
    
    def run_test(self):
        """Run the complete system test"""
        print("🚀 Voice Input System - Comprehensive Mock Test")
        print("=" * 60)
        print("This test simulates the complete workflow:")
        print("• Voice recognition with test data")
        print("• Keyboard controls (F6/F7/F8)")
        print("• Real-time data display")
        print("• Excel auto-save on pause")
        print("• Resource-efficient operation")
        print("=" * 60)
        
        self.test_start_time = time.time()
        
        # Start keyboard listener (single startup)
        self.keyboard_listener = start_keyboard_listener(self.audio_capture)
        if self.keyboard_listener:
            print("✅ Keyboard listener started successfully")
        else:
            print("⚠️  Keyboard listener failed to start")
        
        # Start system status display
        status_thread = threading.Thread(target=self.display_system_status, daemon=True)
        status_thread.start()
        
        # Start keyboard control simulation
        keyboard_thread = threading.Thread(target=self.simulate_keyboard_controls, daemon=True)
        keyboard_thread.start()
        
        # Start the main voice recognition (mock)
        try:
            result = self.audio_capture.listen_realtime_vosk()
            
            # Show final results
            print(f"\n🎉 Test completed successfully!")
            print(f"⏱️  Total test time: {time.time() - self.test_start_time:.1f} seconds")
            print(f"📊 Final Excel file: {self.excel_exporter.filename}")
            
            # Display final Excel contents
            self.show_excel_status()
            
            if os.path.exists(self.excel_exporter.filename):
                import pandas as pd
                df = pd.read_excel(self.excel_exporter.filename)
                print(f"\n📋 Final Excel Contents:")
                print(df.to_string(index=False))
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            
        finally:
            # Cleanup
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            
            print(f"\n🏁 Test finished. Excel file saved as: {self.excel_exporter.filename}")


def main():
    """Main test entry point"""
    controller = SystemTestController()
    controller.run_test()


if __name__ == "__main__":
    main()