#!/bin/bash

# Smart Cart Battery Service Setup Script
# =======================================

set -e

echo "🔋 Smart Cart Battery Service Setup"
echo "===================================="

# Check if running as root for service installation
if [[ $EUID -eq 0 ]]; then
    echo "❌ Please do not run this script as root. Run as pi user."
    exit 1
fi

# Check if SPI is enabled
echo "🔧 Checking SPI configuration..."
if ! lsmod | grep -q spi_bcm2835; then
    echo "⚠️  SPI is not enabled. Please enable SPI using raspi-config:"
    echo "   sudo raspi-config -> Interface Options -> SPI -> Enable"
    echo "   Then reboot and run this script again."
    exit 1
else
    echo "✅ SPI is enabled"
fi

# Check if user is in spi and gpio groups
echo "🔧 Checking user permissions..."
if ! groups | grep -q spi; then
    echo "⚠️  Adding user to spi group..."
    sudo usermod -a -G spi $USER
    GROUP_ADDED=1
fi

if ! groups | grep -q gpio; then
    echo "⚠️  Adding user to gpio group..."
    sudo usermod -a -G gpio $USER
    GROUP_ADDED=1
fi

if [[ $GROUP_ADDED -eq 1 ]]; then
    echo "⚠️  User groups updated. You may need to log out and back in for changes to take effect."
fi

# Get cart ID from user
read -p "Enter Cart ID (default: 1): " CART_ID
CART_ID=${CART_ID:-1}

# Create updated service file with correct cart ID
echo "🔧 Creating systemd service file..."
cat > /tmp/battery-monitor.service << EOF
[Unit]
Description=Smart Cart Battery Monitoring Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PWD
Environment=PYTHONPATH=$PWD
ExecStart=/usr/bin/python3 $PWD/hardware/battery_service.py --cart-id=$CART_ID --monitor
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Ensure the service has access to SPI
SupplementaryGroups=spi gpio

[Install]
WantedBy=multi-user.target
EOF

# Install the service
echo "🔧 Installing systemd service..."
sudo cp /tmp/battery-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload

# Test the battery service
echo "🧪 Testing battery service..."
if python3 hardware/battery_service.py --cart-id=$CART_ID --test; then
    echo "✅ Battery service test passed"
else
    echo "❌ Battery service test failed"
    echo "Please check your hardware connections and try again."
    exit 1
fi

# Ask if user wants to enable the service
read -p "Enable battery monitoring service to start automatically on boot? (y/N): " ENABLE_SERVICE
if [[ $ENABLE_SERVICE =~ ^[Yy]$ ]]; then
    sudo systemctl enable battery-monitor.service
    echo "✅ Battery monitoring service enabled"
    
    read -p "Start the service now? (y/N): " START_SERVICE
    if [[ $START_SERVICE =~ ^[Yy]$ ]]; then
        sudo systemctl start battery-monitor.service
        echo "✅ Battery monitoring service started"
        echo ""
        echo "📊 Service status:"
        sudo systemctl status battery-monitor.service --no-pager -l
        echo ""
        echo "📝 To view logs: journalctl -u battery-monitor.service -f"
    fi
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "💡 Usage:"
echo "   Test:           python3 hardware/battery_service.py --cart-id=$CART_ID --test"
echo "   Status:         python3 hardware/battery_service.py --cart-id=$CART_ID --status"
echo "   Monitor:        python3 hardware/battery_service.py --cart-id=$CART_ID --monitor"
echo "   Service status: sudo systemctl status battery-monitor.service"
echo "   Service logs:   journalctl -u battery-monitor.service -f"
echo "   Stop service:   sudo systemctl stop battery-monitor.service"
echo "   Start service:  sudo systemctl start battery-monitor.service"
echo ""
echo "🔋 Battery Monitoring Features:"
echo "   • API notification at 20% battery"
echo "   • Critical warning at 10% battery"
echo "   • 2-minute delayed shutdown at 5% battery with recovery monitoring"
echo "   • Dynamic monitoring intervals:"
echo "     - 10 minutes when battery > 30%"
echo "     - 2 minutes when battery ≤ 30%"
echo "   • Averaging 20 readings over 20s when below 30%"
echo ""
echo "⚠️  Note: If you added groups, you may need to log out and back in."
