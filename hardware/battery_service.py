#!/usr/bin/env python3
"""
Smart Battery Service for Shopping Cart
========================================

Features:
- API notification at 20% battery level
- Critical warning at 10% battery level  
- Automatic Pi shutdown at 5% battery level
- Dynamic monitoring intervals:
  * 10 minutes when battery > 30%
  * 2 minutes when battery ≤ 30%
- Averaging mechanism when below 30%:
  * Takes 20 readings over 20 seconds
  * Uses average for more accurate level detection

Usage:
    # As a service
    battery_service = BatteryService(cart_id=1)
    battery_service.start()
    
    # Manual monitoring
    battery_service = BatteryService(cart_id=1)
    level = battery_service.get_current_battery_level()
"""

import spidev
import time
import threading
import subprocess
import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, List

# Add the project root to the path to import API modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.api_interaction import CartAPI
except ImportError:
    print("Warning: API module not available. Battery notifications will be logged only.")
    CartAPI = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/battery_service.log'),
        logging.StreamHandler()
    ]
)

class BatteryService:
    """Smart battery monitoring service with API integration."""
    
    def __init__(self, channel=0, vref=3.3, r1=19620, r2=5080, spi_bus=0, spi_device=0, cart_id=None):
        self.logger = logging.getLogger(__name__)
        
        # Hardware configuration
        self.channel = channel
        self.vref = vref
        self.r1 = r1
        self.r2 = r2
        self.divider_ratio = (r1 + r2) / r2

        # Initialize SPI
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(spi_bus, spi_device)
            self.spi.max_speed_hz = 1350000
            self.logger.info("SPI interface initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize SPI: {e}")
            raise
        
        # Battery monitoring state
        self.last_battery_level = None
        self.low_battery_notified = False
        self.critical_battery_notified = False
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # API integration
        self.cart_id = cart_id
        self.api = None
        if CartAPI and cart_id:
            try:
                self.api = CartAPI(cart_id=cart_id)
                if self.api.session_id:
                    self.logger.info(f"API connection established for cart {cart_id}")
                else:
                    self.logger.warning(f"No active session found for cart {cart_id}")
            except Exception as e:
                self.logger.error(f"Failed to initialize API: {e}")
        
        # Battery level thresholds (percentages)
        self.LOW_BATTERY_THRESHOLD = 20.0
        self.CRITICAL_BATTERY_THRESHOLD = 10.0
        self.SHUTDOWN_THRESHOLD = 5.0
        self.FREQUENT_MONITORING_THRESHOLD = 30.0
        
        # Monitoring intervals (seconds)
        self.NORMAL_INTERVAL = 600  # 10 minutes when above 30%
        self.FREQUENT_INTERVAL = 120  # 2 minutes when below 30%
        self.AVERAGING_SAMPLES = 20  # Number of samples for averaging
        self.AVERAGING_DURATION = 20  # Duration in seconds for averaging
        
        # Voltage range for battery level calculation
        self.MIN_VOLTAGE = 9.0
        self.MAX_VOLTAGE = 12.6

    def read_adc(self) -> int:
        """Read ADC value from the specified channel."""
        if not 0 <= self.channel <= 7:
            raise ValueError("ADC channel must be 0-7")
        
        try:
            command = [1, (8 + self.channel) << 4, 0]
            reply = self.spi.xfer2(command)
            result = ((reply[1] & 3) << 8) | reply[2]
            return result
        except Exception as e:
            self.logger.error(f"ADC read error: {e}")
            raise

    def adc_to_voltage(self, adc_value: int) -> float:
        """Convert ADC value to voltage."""
        return (adc_value * self.vref) / 1023.0

    def get_battery_voltage(self) -> tuple:
        """Get battery voltage readings."""
        adc_val = self.read_adc()
        adc_voltage = self.adc_to_voltage(adc_val)
        battery_voltage = adc_voltage * self.divider_ratio
        return round(battery_voltage, 2), adc_val, round(adc_voltage, 2)

    def get_battery_level(self, battery_voltage: float) -> float:
        """Calculate battery level percentage from voltage."""
        voltage = max(self.MIN_VOLTAGE, min(self.MAX_VOLTAGE, battery_voltage))
        level = ((voltage - self.MIN_VOLTAGE) / (self.MAX_VOLTAGE - self.MIN_VOLTAGE)) * 100
        return round(level, 1)

    def get_averaged_battery_level(self) -> float:
        """Get battery level by averaging multiple readings over a specified duration."""
        readings = []
        sample_interval = self.AVERAGING_DURATION / self.AVERAGING_SAMPLES
        
        self.logger.info(f"Taking {self.AVERAGING_SAMPLES} battery readings over {self.AVERAGING_DURATION} seconds...")
        
        for i in range(self.AVERAGING_SAMPLES):
            try:
                voltage, _, _ = self.get_battery_voltage()
                level = self.get_battery_level(voltage)
                readings.append(level)
                
                if i < self.AVERAGING_SAMPLES - 1:  # Don't sleep after the last reading
                    time.sleep(sample_interval)
            except Exception as e:
                self.logger.error(f"Error taking battery reading {i+1}: {e}")
        
        if not readings:
            raise RuntimeError("Failed to take any battery readings")
        
        avg_level = sum(readings) / len(readings)
        self.logger.info(f"Average battery level: {avg_level:.1f}% (from {len(readings)} readings)")
        return round(avg_level, 1)

    def get_current_battery_level(self) -> float:
        """Get current battery level using appropriate method based on last known level."""
        if self.last_battery_level is not None and self.last_battery_level < self.FREQUENT_MONITORING_THRESHOLD:
            return self.get_averaged_battery_level()
        else:
            voltage, _, _ = self.get_battery_voltage()
            return self.get_battery_level(voltage)

    def send_battery_notification(self, level: float, status: str) -> bool:
        """Send battery status notification via API."""
        if self.api and self.api.session_id:
            try:
                # Using the fraud warning system to report battery status
                message = f"Battery {status}: {level}%"
                result = self.api.report_fraud_warning(message)
                if result:
                    self.logger.info(f"Battery notification sent: {message}")
                    return True
                else:
                    self.logger.error(f"Failed to send battery notification: {message}")
                    return False
            except Exception as e:
                self.logger.error(f"Error sending battery notification: {e}")
                return False
        else:
            self.logger.warning(f"No API session available. Battery {status}: {level}%")
            return False

    def shutdown_pi(self):
        """Safely shutdown the Raspberry Pi."""
        self.logger.critical(f"CRITICAL: Battery level too low (≤{self.SHUTDOWN_THRESHOLD}%). Shutting down Raspberry Pi...")
        
        try:
            # Log the shutdown
            shutdown_log = f"/tmp/battery_shutdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(shutdown_log, "w") as f:
                f.write(f"Battery shutdown initiated at {datetime.now()}\n")
                f.write(f"Last battery level: {self.last_battery_level}%\n")
                f.write(f"Cart ID: {self.cart_id}\n")
            
            # Send final notification if possible
            if self.api and self.api.session_id:
                self.send_battery_notification(self.last_battery_level, "SHUTDOWN")
            
            # Stop monitoring
            self.monitoring_active = False
            
            # Initiate shutdown with a 30-second delay to allow for cleanup
            self.logger.info("Initiating shutdown in 30 seconds...")
            subprocess.run(["sudo", "shutdown", "-h", "+0.5"], check=True)
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            # Force shutdown as fallback
            os.system("sudo halt")

    def check_battery_and_notify(self, battery_level: float):
        """Check battery level and send appropriate notifications."""
        # Update last known level
        self.last_battery_level = battery_level
        
        # Check for shutdown threshold
        if battery_level <= self.SHUTDOWN_THRESHOLD:
            self.shutdown_pi()
            return
        
        # Check for critical battery (10%)
        if battery_level <= self.CRITICAL_BATTERY_THRESHOLD and not self.critical_battery_notified:
            self.send_battery_notification(battery_level, "CRITICAL")
            self.critical_battery_notified = True
            self.logger.warning(f"CRITICAL BATTERY: {battery_level}%")
        
        # Check for low battery (20%)
        elif battery_level <= self.LOW_BATTERY_THRESHOLD and not self.low_battery_notified:
            self.send_battery_notification(battery_level, "LOW")
            self.low_battery_notified = True
            self.logger.warning(f"LOW BATTERY: {battery_level}%")
        
        # Reset notification flags if battery level improves
        if battery_level > self.LOW_BATTERY_THRESHOLD:
            if self.low_battery_notified or self.critical_battery_notified:
                self.logger.info(f"Battery level recovered: {battery_level}%")
            self.low_battery_notified = False
            self.critical_battery_notified = False

    def monitor_battery(self):
        """Main battery monitoring loop."""
        self.logger.info("Battery monitoring started")
        
        while self.monitoring_active:
            try:
                # Determine if we need frequent monitoring
                if self.last_battery_level is not None and self.last_battery_level < self.FREQUENT_MONITORING_THRESHOLD:
                    # Below 30% - use averaging and frequent monitoring
                    battery_level = self.get_averaged_battery_level()
                    interval = self.FREQUENT_INTERVAL
                    monitoring_mode = "frequent"
                else:
                    # Above 30% - single reading and normal monitoring
                    voltage, adc_val, adc_voltage = self.get_battery_voltage()
                    battery_level = self.get_battery_level(voltage)
                    interval = self.NORMAL_INTERVAL
                    monitoring_mode = "normal"
                
                self.logger.info(f"Battery: {battery_level}% ({monitoring_mode} monitoring - next check in {interval//60} min)")
                
                # Check battery status and send notifications
                self.check_battery_and_notify(battery_level)
                
                # Wait for next check
                if self.monitoring_active:
                    time.sleep(interval)
                    
            except Exception as e:
                self.logger.error(f"Error in battery monitoring: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    def start(self):
        """Start battery monitoring service."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self.monitor_battery, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("Battery monitoring service started")
            return True
        else:
            self.logger.warning("Battery monitoring is already active")
            return False

    def stop(self):
        """Stop battery monitoring service."""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            self.logger.info("Battery monitoring service stopped")
            return True
        else:
            self.logger.warning("Battery monitoring is not active")
            return False

    def get_status(self) -> dict:
        """Get current battery service status."""
        try:
            voltage, adc_val, adc_voltage = self.get_battery_voltage()
            level = self.get_battery_level(voltage)
            
            status = {
                "monitoring_active": self.monitoring_active,
                "battery_voltage": voltage,
                "battery_level": level,
                "adc_value": adc_val,
                "adc_voltage": adc_voltage,
                "last_level": self.last_battery_level,
                "low_battery_notified": self.low_battery_notified,
                "critical_battery_notified": self.critical_battery_notified,
                "api_connected": self.api is not None and self.api.session_id is not None,
                "cart_id": self.cart_id,
                "thresholds": {
                    "low": self.LOW_BATTERY_THRESHOLD,
                    "critical": self.CRITICAL_BATTERY_THRESHOLD,
                    "shutdown": self.SHUTDOWN_THRESHOLD,
                    "frequent_monitoring": self.FREQUENT_MONITORING_THRESHOLD
                }
            }
            return status
        except Exception as e:
            self.logger.error(f"Error getting battery status: {e}")
            return {"error": str(e)}

    def close(self):
        """Close SPI connection and stop monitoring."""
        self.stop()
        try:
            self.spi.close()
            self.logger.info("SPI connection closed")
        except Exception as e:
            self.logger.error(f"Error closing SPI: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# ----------------------------
# CLI Interface
# ----------------------------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Battery Service for Shopping Cart")
    parser.add_argument("--cart-id", type=int, default=1, help="Cart ID for API notifications")
    parser.add_argument("--test", action="store_true", help="Run in test mode (single reading)")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring service")
    
    args = parser.parse_args()
    
    # Initialize battery service
    battery_service = BatteryService(cart_id=args.cart_id)
    
    try:
        if args.test:
            # Test mode - single reading
            status = battery_service.get_status()
            print("🔋 Battery Test Mode")
            print(f"Voltage: {status['battery_voltage']}V")
            print(f"Level: {status['battery_level']}%")
            print(f"ADC: {status['adc_value']} ({status['adc_voltage']}V)")
            
        elif args.status:
            # Status mode
            status = battery_service.get_status()
            print("🔋 Battery Service Status")
            print(f"Monitoring Active: {status['monitoring_active']}")
            print(f"Battery Level: {status['battery_level']}%")
            print(f"Battery Voltage: {status['battery_voltage']}V")
            print(f"API Connected: {status['api_connected']}")
            print(f"Cart ID: {status['cart_id']}")
            
        else:
            # Default monitoring mode
            print("🔋 Smart Battery Service Starting...")
            print("Features:")
            print("- API notification at 20% battery")
            print("- Critical warning at 10% battery") 
            print("- Automatic shutdown at 5% battery")
            print("- Dynamic monitoring: 10min above 30%, 2min below 30%")
            print("- Averaging 20 readings over 20s when below 30%")
            print()
            
            battery_service.start()
            
            try:
                while True:
                    time.sleep(10)
                    status = battery_service.get_status()
                    level = status.get('battery_level', 0)
                    
                    # Status indicators
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
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Battery: {level}% {indicator}")
                    
            except KeyboardInterrupt:
                print("\n🛑 Stopped by user.")
                
    finally:
        battery_service.close()
        print("🔋 Battery service shut down.")
