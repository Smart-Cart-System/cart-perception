#!/usr/bin/env python3
"""
Integration example for Battery Service with Cart System
========================================================

This module shows how to integrate the battery monitoring service
into your existing cart system.
"""

import sys
import os
import time
import threading
from datetime import datetime

# Add project paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware.battery_service import BatteryService
from core.cart_system import CartSystem  # Assuming this exists


class IntegratedCartSystem:
    """Cart system with integrated battery monitoring."""
    
    def __init__(self, cart_id=1):
        self.cart_id = cart_id
        
        # Initialize battery service
        self.battery_service = BatteryService(cart_id=cart_id)
        
        # Initialize cart system (assuming it exists)
        try:
            self.cart_system = CartSystem(cart_id=cart_id)
        except ImportError:
            print("Cart system not available, running battery service only")
            self.cart_system = None
        
        self.running = False

    def start(self):
        """Start the integrated system."""
        print(f"🛒 Starting integrated cart system for cart {self.cart_id}")
        
        # Start battery monitoring
        if self.battery_service.start():
            print("✅ Battery monitoring started")
        else:
            print("❌ Failed to start battery monitoring")
            return False
        
        # Start cart system
        if self.cart_system:
            try:
                self.cart_system.start()
                print("✅ Cart system started")
            except Exception as e:
                print(f"❌ Failed to start cart system: {e}")
        
        self.running = True
        return True

    def stop(self):
        """Stop the integrated system."""
        print("🛑 Stopping integrated cart system...")
        self.running = False
        
        # Stop cart system
        if self.cart_system:
            try:
                self.cart_system.stop()
                print("✅ Cart system stopped")
            except Exception as e:
                print(f"⚠️ Error stopping cart system: {e}")
        
        # Stop battery service
        if self.battery_service.stop():
            print("✅ Battery monitoring stopped")
        
        self.battery_service.close()

    def get_system_status(self):
        """Get status of all system components."""
        battery_status = self.battery_service.get_status()
        
        system_status = {
            "timestamp": datetime.now().isoformat(),
            "cart_id": self.cart_id,
            "system_running": self.running,
            "battery": battery_status,
            "cart_system": None
        }
        
        # Get cart system status if available
        if self.cart_system and hasattr(self.cart_system, 'get_status'):
            try:
                system_status["cart_system"] = self.cart_system.get_status()
            except Exception as e:
                system_status["cart_system"] = {"error": str(e)}
        
        return system_status

    def run(self):
        """Main execution loop."""
        if not self.start():
            return
        
        try:
            print("🚀 Integrated cart system running...")
            print("Press Ctrl+C to stop")
            
            while self.running:
                # Display system status periodically
                status = self.get_system_status()
                battery_level = status["battery"].get("battery_level", 0)
                
                # Status indicator
                if battery_level <= 5:
                    indicator = "🔴 CRITICAL - SHUTDOWN IMMINENT"
                elif battery_level <= 10:
                    indicator = "🟠 CRITICAL"
                elif battery_level <= 20:
                    indicator = "🟡 LOW"
                elif battery_level <= 30:
                    indicator = "🟡 MONITORING"
                else:
                    indicator = "🟢 GOOD"
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛒 Cart {self.cart_id} | 🔋 {battery_level}% {indicator}")
                
                time.sleep(30)  # Update every 30 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user")
        except Exception as e:
            print(f"❌ System error: {e}")
        finally:
            self.stop()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# ----------------------------
# Standalone battery service launcher
# ----------------------------
def run_battery_service_only(cart_id=1):
    """Run only the battery service without cart system integration."""
    print(f"🔋 Starting standalone battery service for cart {cart_id}")
    
    with BatteryService(cart_id=cart_id) as battery_service:
        battery_service.start()
        
        try:
            while True:
                status = battery_service.get_status()
                level = status.get("battery_level", 0)
                voltage = status.get("battery_voltage", 0)
                
                # Status indicator
                if level <= 5:
                    indicator = "🔴 SHUTDOWN"
                elif level <= 10:
                    indicator = "🟠 CRITICAL"
                elif level <= 20:
                    indicator = "🟡 LOW"
                elif level <= 30:
                    indicator = "🟡 MONITOR"
                else:
                    indicator = "🟢 GOOD"
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔋 {level}% ({voltage}V) {indicator}")
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n🛑 Battery service stopped by user")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Integrated Cart System with Battery Monitoring")
    parser.add_argument("--cart-id", type=int, default=1, help="Cart ID")
    parser.add_argument("--battery-only", action="store_true", help="Run battery service only")
    
    args = parser.parse_args()
    
    if args.battery_only:
        run_battery_service_only(args.cart_id)
    else:
        # Try to run integrated system
        system = IntegratedCartSystem(args.cart_id)
        system.run()
