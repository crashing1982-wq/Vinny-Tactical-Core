# Vinny Tactical Core - SCP Deployment Guide

## Quick Deploy to Raspberry Pi

### Option 1: Deploy Single File (main.py)

```bash
# Copy main.py to your Raspberry Pi
scp main.py pi@YOUR_PI_IP:/home/pi/

# SSH into Pi and run
ssh pi@YOUR_PI_IP
cd /home/pi
sudo python3 main.py
```

### Option 2: Deploy Entire Repository

```bash
# Clone entire repository to Pi
scp -r . pi@YOUR_PI_IP:/home/pi/Vinny-Tactical-Core/

# Or use git (if Pi has internet)
ssh pi@YOUR_PI_IP
cd /home/pi
git clone https://github.com/crashing1982-wq/Vinny-Tactical-Core.git
cd Vinny-Tactical-Core
sudo python3 main.py
```

---

## Step-by-Step Deployment

### Step 1: Find Your Pi's IP Address

```bash
# On the Pi itself
hostname -I

# Or from your computer (if on same network)
arp-scan -l | grep -i raspberry
# or
nmap -sn 192.168.1.0/24 | grep -i raspberry
```

### Step 2: Test SSH Connection

```bash
ssh pi@YOUR_PI_IP
# Default password is "raspberry"
exit
```

### Step 3: Copy Files

#### Deploy just the main code:
```bash
scp main.py pi@YOUR_PI_IP:/home/pi/
scp gpio_diagnostics.py pi@YOUR_PI_IP:/home/pi/
scp test_production_validation.py pi@YOUR_PI_IP:/home/pi/
```

#### Or deploy everything:
```bash
# Copy entire directory
scp -r . pi@YOUR_PI_IP:/home/pi/Vinny-Tactical-Core/
```

### Step 4: SSH into Pi and Verify

```bash
ssh pi@YOUR_PI_IP

# List files
ls -la /home/pi/*.py

# Check Python version
python3 --version

# Test imports
python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"
python3 -c "import serial; print('Serial OK')"
python3 -c "import ADS1x15; print('ADC OK')"
```

### Step 5: Run Diagnostics

```bash
# Test GPIO
sudo python3 /home/pi/gpio_diagnostics.py

# Run validation tests
sudo python3 /home/pi/test_production_validation.py -v
```

### Step 6: Start Robot

```bash
# Option A: Direct run (for testing)
cd /home/pi
sudo python3 main.py

# Option B: Background with logging
nohup sudo python3 /home/pi/main.py > /home/pi/vinny.log 2>&1 &

# Option C: As a systemd service (recommended)
sudo systemctl start vinny.service
```

---

## Complete SCP Examples

### Example 1: Deploy Single File

```bash
# Your computer
scp main.py pi@192.168.1.100:/home/pi/

# Then on Pi
ssh pi@192.168.1.100
sudo python3 /home/pi/main.py
```

### Example 2: Deploy Multiple Files

```bash
# Your computer
scp main.py pi@192.168.1.100:/home/pi/
scp gpio_diagnostics.py pi@192.168.1.100:/home/pi/
scp test_production_validation.py pi@192.168.1.100:/home/pi/

# Then on Pi
ssh pi@192.168.1.100
sudo python3 /home/pi/main.py
```

### Example 3: Deploy Entire Repository

```bash
# Your computer (from repo directory)
cd /path/to/Vinny-Tactical-Core
scp -r . pi@192.168.1.100:/home/pi/Vinny-Tactical-Core/

# Then on Pi
ssh pi@192.168.1.100
cd /home/pi/Vinny-Tactical-Core
sudo python3 main.py
```

### Example 4: Deploy with Authentication Key (no password)

```bash
# Setup SSH key (one time)
ssh-copy-id pi@192.168.1.100

# Then deploy (no password needed)
scp -r . pi@192.168.1.100:/home/pi/Vinny-Tactical-Core/
ssh pi@192.168.1.100 'cd /home/pi/Vinny-Tactical-Core && sudo python3 main.py'
```

---

## Find Your Raspberry Pi IP

### Method 1: Using nmap (Linux/Mac)

```bash
nmap -sn 192.168.1.0/24 | grep -i "raspberry\|b8:27:eb\|dc:a6:32"
```

### Method 2: Using arp-scan (Linux)

```bash
sudo arp-scan -l | grep -i "raspberry\|b8:27:eb"
```

### Method 3: Using Windows/PowerShell

```powershell
Get-NetNeighbor | Where-Object {$_.State -eq "Reachable"} | Select-Object IPAddress, LinkLayerAddress
```

### Method 4: Check your router's connected devices

Most routers have a web interface (192.168.1.1) where you can see connected devices

### Method 5: On the Pi itself

```bash
# SSH into Pi first if you can
hostname -I

# Or check from another device
ping raspberrypi.local
```

---

## Troubleshooting SCP Issues

### Issue: "Permission denied (publickey,password)"

**Solution:**
```bash
# Try with explicit user
scp -P 22 main.py pi@192.168.1.100:/home/pi/

# Or check SSH is enabled on Pi
# On Pi: sudo raspi-config → Interface Options → SSH → Enable
```

### Issue: "scp: command not found"

**Solution:**
```bash
# On Mac/Linux, scp should be included
# If not installed:
# Ubuntu/Debian: sudo apt-get install openssh-client
# Mac: brew install openssh
```

### Issue: "No route to host"

**Solution:**
```bash
# Check Pi is powered on and on network
ping 192.168.1.100

# Check you're on same WiFi/network
ifconfig | grep inet
```

### Issue: Slow transfer

**Solution:**
```bash
# Use compression
scp -C main.py pi@192.168.1.100:/home/pi/

# Or batch files
scp -r . pi@192.168.1.100:/home/pi/Vinny/
```

---

## Deploy and Run Script

Save as `deploy.sh`:

```bash
#!/bin/bash

PI_IP="192.168.1.100"
PI_USER="pi"
PI_HOME="/home/pi"

echo "🚀 Deploying Vinny Tactical Core..."

# 1. Deploy files
echo "📁 Copying files..."
scp -r . $PI_USER@$PI_IP:$PI_HOME/Vinny-Tactical-Core/

# 2. SSH and verify
echo "✓ Verifying deployment..."
ssh $PI_USER@$PI_IP "ls -la $PI_HOME/Vinny-Tactical-Core/"

# 3. Run diagnostics
echo "🔍 Running diagnostics..."
ssh $PI_USER@$PI_IP "cd $PI_HOME/Vinny-Tactical-Core && sudo python3 gpio_diagnostics.py"

# 4. Start robot
echo "✓ Starting robot..."
ssh $PI_USER@$PI_IP "cd $PI_HOME/Vinny-Tactical-Core && nohup sudo python3 main.py > vinny.log 2>&1 &"

echo "🎉 Deployment complete!"
echo "Robot status: ssh $PI_USER@$PI_IP 'ps aux | grep main.py'"
```

Run it:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## Monitor After Deployment

### Check if Running

```bash
ssh pi@192.168.1.100 "ps aux | grep main.py"
```

### View Logs

```bash
ssh pi@192.168.1.100 "tail -f /home/pi/vinny.log"
```

### Stop Robot

```bash
ssh pi@192.168.1.100 "sudo pkill -f main.py"
```

### Restart Robot

```bash
ssh pi@192.168.1.100 "cd /home/pi && nohup sudo python3 main.py > vinny.log 2>&1 &"
```

---

## Using Git for Deployment (Recommended for Updates)

### First Time Setup

```bash
# On Pi
ssh pi@192.168.1.100
cd /home/pi
git clone https://github.com/crashing1982-wq/Vinny-Tactical-Core.git
cd Vinny-Tactical-Core
sudo python3 main.py
```

### Update Later

```bash
ssh pi@192.168.1.100
cd /home/pi/Vinny-Tactical-Core
git pull origin main
# Restart robot
sudo systemctl restart vinny.service
```

---

## Systemd Service Deployment

Create service on Pi:

```bash
ssh pi@192.168.1.100

# Create service file
sudo nano /etc/systemd/system/vinny.service
```

Add:
```ini
[Unit]
Description=Vinny Tactical Core
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Vinny-Tactical-Core
ExecStart=/usr/bin/python3 /home/pi/Vinny-Tactical-Core/main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
# Enable and start
sudo systemctl enable vinny.service
sudo systemctl start vinny.service

# Check status
sudo systemctl status vinny.service
```

---

## Final Deployment Checklist

- [ ] Found Pi IP address: `______________`
- [ ] SSH connection works: `ssh pi@YOUR_IP`
- [ ] Copied files with scp
- [ ] Verified files on Pi: `ls -la /home/pi/`
- [ ] Ran gpio_diagnostics.py
- [ ] Ran test_production_validation.py
- [ ] Started main.py
- [ ] Verified running: `ps aux | grep main.py`
- [ ] Checked logs: `tail -f vinny.log`

---

## Your Deployment Command

```bash
# Replace with your Pi's IP address
scp -r . pi@YOUR_PI_IP:/home/pi/Vinny-Tactical-Core/
ssh pi@YOUR_PI_IP 'cd /home/pi/Vinny-Tactical-Core && sudo python3 main.py'
```

---

**🚀 Ready to deploy!** Let me know your Pi's IP and I can help with the deployment! 🤖

