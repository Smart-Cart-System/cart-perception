# cart-perception

## Table of Contents
- [First Time Connection Setup](#first-time-connection-setup)
- [Network Configuration](#network-configuration)
- [Remote Access Setup](#remote-access-setup)
- [Running the System](#running-the-system)
- [System Commands](#system-commands)
- [Testing Commands](#testing-commands)
- [Credentials](#credentials)

## First Time Connection Setup

### Hardware Connection
1. Connect the Ethernet cable between your laptop and Raspberry Pi
2. Configure your laptop's network settings

### Network Configuration

#### Configure Laptop IP Address
1. Open **Network and Sharing Center** (Windows)
2. Click on your Ethernet connection
3. Click **Properties**
4. Select **Internet Protocol Version 4 (TCP/IPv4)**
5. Click **Properties**
6. Select **Use the following IP address**
7. Enter the following:
   - **IP Address**: `192.168.1.33`
   - **Subnet Mask**: `255.255.255.0`
   - **Default Gateway**: (leave empty for direct connection)

#### Test Connection
Open Command Prompt and ping the Raspberry Pi:
```bash
ping 192.168.1.35
```
You should see replies if the connection is successful.

## Remote Access Setup

### Install RealVNC Viewer
1. Download and install [RealVNC Viewer](https://www.realvnc.com/en/connect/download/viewer/) on your laptop
2. Open RealVNC Viewer

### Create New Connection
1. Go to **File** → **New Connection**
2. Enter the following details:
   - **VNC Server**: `192.168.1.35` (or use hostname `cart`)
   - **Name**: Any name you prefer (e.g., "Smart Cart")
3. Click **OK**

### Connect to the Cart
1. Double-click on the connection you just created
2. Enter credentials:
   - **Username**: `main`
   - **Password**: `cart2025`
3. Check **Remember password** for convenience
4. Click **OK** to connect

### Connect to WiFi Network
Once connected via VNC:
1. Access the GUI on the Raspberry Pi
2. Connect to your hotspot or WiFi network
3. Both the cart and laptop should now be on the same network

## Running the System

### Access the Cart via SSH
When both devices are on the same network, you can SSH into the cart:
```bash
ssh main@cart
# or
ssh main@192.168.1.35
```

### Activate Virtual Environment
```bash
dd
```
This command activates the Python virtual environment.

### Run the Cart System
```bash
duck
```
This command starts the main cart perception system.

## System Commands

### Hardware Monitoring
- `tp` - Get temperature
- `volt` - Monitor voltage (real-time)
- `vol` - Check throttling status

### Camera Management
- `dev` - List available cameras

### USB Management
- `ss` - Refresh USB devices (cycles USB hub power)

## Testing Commands

Use these commands to test individual hardware components:

- `tw` - Test weight sensors
- `ts` - Test speaker
- `tl` - Test LED

## Command Aliases

The following aliases are configured on the Raspberry Pi for convenience:

```bash
alias tp="vcgencmd measure_temp"
alias volt="sudo watch -n 1 vcgencmd pmic_read_adc"
alias vol="vcgencmd get_throttled"
alias dev="v4l2-ctl --list-devices"
alias dd="cd /home/main/cart/cart-perception && source .venv/bin/activate"
alias duck="cd /home/main/cart/cart-perception && python3 main.py"
alias ss="sudo uhubctl -l 1 -a off && sleep 1 && sudo uhubctl -l 1 -a on"
alias tw="python3 ~/cart/cart-perception/hardware/total_weight.py"
alias ts="python3 ~/cart/cart-perception/tests/test_speaker.py"
alias tl="python3 ~/cart/cart-perception/tests/test_led.py"
```

To add these aliases to your system, add them to your `~/.bashrc` or `~/.bash_aliases` file.

## Credentials

### Raspberry Pi Login
- **Username**: `main`
- **Password**: `cart2025`
- **Hostname**: `cart`
- **IP Address**: `192.168.1.35` (direct connection)

## Troubleshooting

### Connection Issues
1. Verify the Ethernet cable is properly connected
2. Ensure your laptop's IP is configured correctly (`192.168.1.33`)
3. Check if the Raspberry Pi is powered on
4. Try pinging the Pi: `ping 192.168.1.35`

### VNC Connection Issues
1. Ensure VNC server is running on the Raspberry Pi
2. Check firewall settings on both devices
3. Verify you're using the correct IP address

### Camera Not Detected
Run the `dev` command to list available cameras and verify they are connected.

### USB Device Issues
If USB devices are not responding, run `ss` to refresh the USB connections.

## Additional Notes

- Make sure both the cart (Raspberry Pi) and laptop are connected to the same network for remote operations
- The cart requires internet connectivity for full functionality
- Always activate the virtual environment (`dd`) before running the cart system
- Use the testing commands to verify hardware functionality before running the full system