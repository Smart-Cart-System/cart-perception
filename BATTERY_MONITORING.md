# Smart Cart Battery Monitoring System

## Overview

The Smart Cart Battery Monitoring System provides intelligent battery level monitoring with automatic notifications and safety features for shopping cart systems.

## Features

### 🔋 Battery Level Monitoring
- **20% Battery**: Sends API notification for low battery warning
- **10% Battery**: Sends critical battery warning via API
- **5% Battery**: Automatically shuts down the Raspberry Pi to prevent corruption

### ⏰ Dynamic Monitoring Intervals
- **Above 30%**: Checks every 10 minutes (normal monitoring)
- **Below 30%**: Checks every 2 minutes (frequent monitoring)
- **Below 30%**: Uses averaging of 20 readings over 20 seconds for accuracy

### 📡 API Integration
- Integrates with existing cart API system
- Sends battery status notifications via fraud warning endpoint
- Requires active cart session for API notifications

### 🛡️ Safety Features
- Graceful shutdown sequence when battery is critically low
- Logging of all battery events
- Automatic service restart on failure
- Hardware error handling and recovery

## Hardware Requirements

### ADC Setup
- **ADC Channel**: 0 (configurable)
- **Reference Voltage**: 3.3V
- **SPI Interface**: Enabled on Raspberry Pi

### Voltage Divider
- **R1**: 19,620Ω (high side)
- **R2**: 5,080Ω (low side)
- **Divider Ratio**: ~4.86
- **Max Input Voltage**: ~16V (safe for 12V battery)

### Battery Specifications
- **Minimum Voltage**: 9.0V (0% charge)
- **Maximum Voltage**: 12.6V (100% charge)
- **Type**: 12V Lead-acid or LiFePO4

## Installation

### Quick Setup
```bash
cd /home/main/cart/cart-perception
./setup_battery_service.sh
```

### Manual Installation

1. **Enable SPI**:
   ```bash
   sudo raspi-config
   # Interface Options -> SPI -> Enable
   sudo reboot
   ```

2. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Test Hardware**:
   ```bash
   python3 hardware/battery_service.py --cart-id=1 --test
   ```

4. **Install Service**:
   ```bash
   sudo cp hardware/battery-monitor.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable battery-monitor.service
   sudo systemctl start battery-monitor.service
   ```

## Usage

### Command Line Interface

#### Test Mode (Single Reading)
```bash
python3 hardware/battery_service.py --cart-id=1 --test
```

#### Status Check
```bash
python3 hardware/battery_service.py --cart-id=1 --status
```

#### Manual Monitoring
```bash
python3 hardware/battery_service.py --cart-id=1 --monitor
```

### Python Integration

#### Basic Usage
```python
from hardware.battery_service import BatteryService

# Initialize battery service
battery = BatteryService(cart_id=1)

# Start monitoring
battery.start()

# Get current status
status = battery.get_status()
print(f"Battery level: {status['battery_level']}%")

# Stop monitoring
battery.stop()
battery.close()
```

#### Context Manager
```python
with BatteryService(cart_id=1) as battery:
    battery.start()
    # Battery monitoring runs in background
    # Automatic cleanup on exit
```

#### Integration with Cart System
```python
from hardware.integrated_system import IntegratedCartSystem

# Run complete system with battery monitoring
with IntegratedCartSystem(cart_id=1) as system:
    system.run()  # Runs until interrupted
```

### Service Management

#### Service Status
```bash
sudo systemctl status battery-monitor.service
```

#### View Logs
```bash
# Real-time logs
journalctl -u battery-monitor.service -f

# Recent logs
journalctl -u battery-monitor.service --since "1 hour ago"
```

#### Control Service
```bash
# Start service
sudo systemctl start battery-monitor.service

# Stop service
sudo systemctl stop battery-monitor.service

# Restart service
sudo systemctl restart battery-monitor.service

# Disable auto-start
sudo systemctl disable battery-monitor.service
```

## Configuration

### Hardware Configuration
Edit `hardware/battery_service.py` to modify hardware parameters:

```python
class BatteryService:
    def __init__(self, 
                 channel=0,        # ADC channel (0-7)
                 vref=3.3,         # ADC reference voltage
                 r1=19620,         # Voltage divider R1 (Ω)
                 r2=5080,          # Voltage divider R2 (Ω)
                 spi_bus=0,        # SPI bus number
                 spi_device=0,     # SPI device number
                 cart_id=None):    # Cart ID for API
```

### Battery Thresholds
Modify thresholds in the `__init__` method:

```python
# Battery level thresholds (percentages)
self.LOW_BATTERY_THRESHOLD = 20.0      # API notification
self.CRITICAL_BATTERY_THRESHOLD = 10.0  # Critical warning
self.SHUTDOWN_THRESHOLD = 5.0           # Auto shutdown
self.FREQUENT_MONITORING_THRESHOLD = 30.0  # Frequent monitoring

# Monitoring intervals (seconds)
self.NORMAL_INTERVAL = 600      # 10 minutes above 30%
self.FREQUENT_INTERVAL = 120    # 2 minutes below 30%
```

### Voltage Range
Adjust for different battery types:

```python
# Voltage range for battery level calculation
self.MIN_VOLTAGE = 9.0   # 0% charge voltage
self.MAX_VOLTAGE = 12.6  # 100% charge voltage
```

## API Integration

The battery service integrates with the existing cart API system using the `CartAPI` class. Battery notifications are sent through the fraud warning endpoint.

### API Configuration
- **Base URL**: Configured in `api/api_interaction.py`
- **API Key**: Set in headers (`X-API-Key`)
- **Session**: Requires active cart session

### Notification Format
Battery notifications are sent as fraud warnings with descriptive messages:
- `"Battery LOW: 18.5%"`
- `"Battery CRITICAL: 9.2%"`
- `"Battery SHUTDOWN: 4.8%"`

## Monitoring Behavior

### Normal Mode (Battery > 30%)
- Single voltage reading every 10 minutes
- Minimal system overhead
- Standard accuracy

### Frequent Mode (Battery ≤ 30%)
- 20 voltage readings over 20 seconds every 2 minutes
- Average of readings for improved accuracy
- Higher monitoring frequency for critical range

### Critical Actions
1. **20% Battery**: Send low battery API notification
2. **10% Battery**: Send critical battery API notification
3. **5% Battery**: 
   - Send shutdown notification
   - Log shutdown event
   - Initiate safe system shutdown

## Troubleshooting

### Common Issues

#### SPI Not Available
```bash
# Check if SPI is enabled
lsmod | grep spi_bcm2835

# Enable SPI
sudo raspi-config
# Interface Options -> SPI -> Enable
sudo reboot
```

#### Permission Denied
```bash
# Add user to required groups
sudo usermod -a -G spi,gpio $USER
# Log out and back in
```

#### Service Won't Start
```bash
# Check service status
sudo systemctl status battery-monitor.service

# Check logs
journalctl -u battery-monitor.service --since "10 minutes ago"

# Test manually
python3 hardware/battery_service.py --cart-id=1 --test
```

#### Inaccurate Readings
1. Check voltage divider resistor values
2. Verify ADC reference voltage (3.3V)
3. Calibrate using known battery voltage
4. Check for loose connections

### Calibration

To calibrate the system:

1. **Measure Actual Battery Voltage** with a multimeter
2. **Compare with System Reading**:
   ```bash
   python3 hardware/battery_service.py --cart-id=1 --test
   ```
3. **Adjust Voltage Divider Ratio** if needed:
   ```python
   # Measure actual resistor values and update
   r1 = 19620  # Actual measured value
   r2 = 5080   # Actual measured value
   ```

## File Structure

```
hardware/
├── battery_service.py          # Main battery service class
├── integrated_system.py       # Cart system integration
├── battery-monitor.service     # Systemd service file
└── ...

setup_battery_service.sh        # Setup script
t.py                           # Original battery monitor (enhanced)
```

## Logs and Debugging

### Log Files
- **Service Logs**: `journalctl -u battery-monitor.service`
- **Application Logs**: `/tmp/battery_service.log`
- **Shutdown Logs**: `/tmp/battery_shutdown_*.log`

### Debug Mode
For detailed debugging, modify the logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Test Hardware
```bash
# Basic hardware test
python3 -c "
import spidev
spi = spidev.SpiDev()
spi.open(0, 0)
print('SPI test successful')
spi.close()
"
```

## Safety Considerations

⚠️ **Important Safety Notes**:

1. **Voltage Limits**: Ensure input voltage never exceeds ADC limits
2. **Shutdown Timing**: System shuts down automatically at 5% - save work frequently
3. **Hardware Protection**: Use appropriate voltage divider for your battery voltage
4. **Testing**: Always test with known good battery before deployment
5. **Backup Power**: Consider UPS for critical operations during battery changes

## Support

For issues or questions:
1. Check logs: `journalctl -u battery-monitor.service -f`
2. Test hardware: `python3 hardware/battery_service.py --test`
3. Verify configuration in `hardware/battery_service.py`
4. Check API connectivity and cart session
