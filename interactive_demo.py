#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Voice Input System Demo
===================================

Manual control demo with simple menu interface:
- Start voice recognition
- Simulate voice input
- Control with keyboard (F6/F7/F8)
- View Excel results
- Check system status
"""

import time
import threading
from datetime import datetime
from audio_capture_v import AudioCapture, start_keyboard_listener
from excel_exporter import ExcelExporter


class InteractiveDemo:
    def __init__(self):
        self.excel_exporter = ExcelExporter(filename=f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        self.audio_capture = AudioCapture(excel_exporter=self.excel_exporter)
        self.keyboard_listener = None
        self.is_running = False
        
    def display_menu(self):
        """Display interactive menu"""
        print("\n" + "="*50)
        print("🎤 VOICE INPUT SYSTEM - INTERACTIVE DEMO")
        print("="*50)
        print("1. Start voice recognition system")
        print("2. Simulate voice input")
        print("3. Show system status")
        print("4. Show Excel data")
        print("5. Stop system")
        print("6. Exit")
        print("-"*50)
        print("Keyboard controls: F6=Pause, F7=Resume, F8=Stop")
        print("="*50)
        
    def start_system(self):
        """Start the voice recognition system"""
        if self.is_running:
            print("\n⚠️  System already running!")
            return
            
        print("\n🔧 Starting voice recognition system...")
        
        # Single startup - keyboard listener
        self.keyboard_listener = start_keyboard_listener(self.audio_capture)
        if self.keyboard_listener:
            print("✅ Keyboard listener started")
        else:
            print("⚠️  Keyboard listener not available")
            
        # Start voice recognition
        self.audio_capture.is_listening = True
        self.audio_capture.is_paused = False
        self.is_running = True
        
        print("✅ Voice recognition system started!")
        print("🎤 System is listening for voice input...")
        
    def simulate_voice_input(self):
        """Simulate voice input with test data"""
        if not self.is_running:
            print("\n❌ System not running! Please start system first.")
            return
            
        print("\n🎤 Simulating voice input...")
        
        # Test data that represents voice recognition results
        test_phrases = [
            ("测量值为十二点五和三十三点八", [12.5, 33.8]),
            ("五十五点五和七十七点七", [55.5, 77.7]),
            ("九十九点九", [99.9]),
            ("一百二十三点四", [123.4]),
        ]
        
        print("\nSelect test phrase:")
        for i, (phrase, values) in enumerate(test_phrases, 1):
            print(f"{i}. '{phrase}' → {values}")
        print("5. Custom input")
        
        try:
            choice = int(input("\nEnter choice (1-5): "))
            
            if 1 <= choice <= 4:
                phrase, values = test_phrases[choice-1]
            elif choice == 5:
                phrase = input("Enter voice text: ")
                values_str = input("Enter values (comma-separated): ")
                values = [float(x.strip()) for x in values_str.split(",")]
            else:
                print("❌ Invalid choice")
                return
                
            # Simulate the voice recognition process
            print(f"\n🎤 Voice recognized: '{phrase}'")
            print(f"📊 Values extracted: {values}")
            
            # Process through the audio capture system
            self.audio_capture.filtered_callback(phrase)
            
            print("✅ Voice input processed successfully!")
            
        except ValueError:
            print("❌ Invalid input format")
        except Exception as e:
            print(f"❌ Error: {e}")
            
    def show_system_status(self):
        """Display current system status"""
        print("\n" + "="*40)
        print("💻 SYSTEM STATUS")
        print("="*40)
        
        if not self.is_running:
            print("❌ System: STOPPED")
            return
            
        status = "RUNNING" if self.audio_capture.is_running else "PAUSED"
        buffer_size = len(self.audio_capture.buffered_values)
        
        print(f"🔄 System: {status}")
        print(f"📊 Buffered values: {buffer_size}")
        print(f"📁 Excel file: {self.excel_exporter.filename}")
        
        if self.is_running:
            print(f"🎤 Listening: {'Yes' if self.audio_capture.is_listening else 'No'}")
            print(f"⏸️ Paused: {'Yes' if self.audio_capture.is_paused else 'No'}")
            
    def show_excel_data(self):
        """Display Excel data"""
        print("\n" + "="*40)
        print("📊 EXCEL DATA")
        print("="*40)
        
        try:
            import pandas as pd
            import os
            
            if not os.path.exists(self.excel_exporter.filename):
                print("❌ Excel file not found")
                return
                
            df = pd.read_excel(self.excel_exporter.filename)
            
            if len(df) == 0:
                print("📋 Excel file is empty")
                return
                
            print(f"📊 Total rows: {len(df)}")
            print(f"📈 ID range: {int(df['编号'].min())} - {int(df['编号'].max())}")
            print(f"💾 Values: {df['测量值'].tolist()}")
            print(f"🕐 Last updated: {df['时间戳'].iloc[-1] if len(df) > 0 else 'N/A'}")
            
            print(f"\n📋 Data preview:")
            print("-" * 30)
            for i, row in df.head().iterrows():
                print(f"Row {int(row['编号'])}: {row['测量值']} | {row['时间戳']}")
                
            if len(df) > 5:
                print(f"... and {len(df) - 5} more rows")
                
        except Exception as e:
            print(f"❌ Error reading Excel: {e}")
            
    def stop_system(self):
        """Stop the voice recognition system"""
        if not self.is_running:
            print("\n⚠️  System not running!")
            return
            
        print("\n🛑 Stopping voice recognition system...")
        self.audio_capture.stop()
        self.is_running = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            
        print("✅ System stopped successfully!")
        
    def run_demo(self):
        """Run the interactive demo"""
        print("🚀 VOICE INPUT SYSTEM - INTERACTIVE DEMO")
        print("="*50)
        print("Welcome to the voice input system demo!")
        print("Use keyboard F6/F7/F8 or menu options to control.")
        print("="*50)
        
        while True:
            self.display_menu()
            
            try:
                choice = input("\nEnter your choice (1-6): ").strip()
                
                if choice == "1":
                    self.start_system()
                elif choice == "2":
                    self.simulate_voice_input()
                elif choice == "3":
                    self.show_system_status()
                elif choice == "4":
                    self.show_excel_data()
                elif choice == "5":
                    self.stop_system()
                elif choice == "6":
                    if self.is_running:
                        self.stop_system()
                    print("\n👋 Demo completed. Thank you!")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-6.")
                    
            except KeyboardInterrupt:
                print("\n\n🛑 Demo interrupted by user")
                if self.is_running:
                    self.stop_system()
                break
                
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main demo function"""
    demo = InteractiveDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()