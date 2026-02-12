# Ubuntu Server Deployment Guide

## ✅ Yes, Your Code Will Run on Ubuntu!

Your project is **fully compatible** with Ubuntu server. Here's everything you need to know.

---

## 📋 System Requirements

### Minimum Requirements:
- **OS**: Ubuntu 18.04 LTS or later (20.04/22.04 recommended)
- **RAM**: 4GB minimum, 8GB recommended
- **CPU**: 2+ cores
- **Storage**: 10GB free space
- **Python**: 3.8 or later

### Optional:
- **GPU**: NVIDIA GPU with CUDA for faster training (optional)

---

## 🚀 Installation Steps

### Step 1: Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 2: Install Python and Dependencies

```bash
# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Install system dependencies
sudo apt install -y build-essential git wget curl
```

### Step 3: Install SUMO

**Option A: From Ubuntu Repository (Easier)**
```bash
sudo add-apt-repository ppa:sumo/stable
sudo apt update
sudo apt install -y sumo sumo-tools sumo-doc
```

**Option B: Build from Source (Latest Version)**
```bash
# Install dependencies
sudo apt install -y cmake g++ libxerces-c-dev libfox-1.6-dev \
    libgdal-dev libproj-dev libgl2ps-dev swig

# Download and build SUMO
cd /tmp
git clone --recursive https://github.com/eclipse/sumo
cd sumo
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

### Step 4: Set SUMO_HOME Environment Variable

```bash
# Add to ~/.bashrc
echo 'export SUMO_HOME="/usr/share/sumo"' >> ~/.bashrc
source ~/.bashrc

# Verify
echo $SUMO_HOME
```

### Step 5: Clone/Upload Your Project

**Option A: Upload from Windows**
```bash
# On your Windows machine, compress the project
# Then upload to server using scp:
scp -r signal_phase-1.zip user@server:/home/user/

# On server, extract:
cd /home/user
unzip signal_phase-1.zip
cd signal_phase-1
```

**Option B: Git (if using version control)**
```bash
git clone <your-repo-url>
cd signal_phase-1
```

### Step 6: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 7: Verify Installation

```bash
# Check SUMO
python utils/sumo_checker.py

# Should show:
# ✅ SUMO is properly installed and configured!
```

---

## 🔧 Code Modifications for Ubuntu

### 1. Update SUMO Binary Paths (Already Compatible!)

Your code already handles Linux:

```python
# In sumo_env.py - Already correct!
if sys.platform == 'win32':
    sumo_binary = 'sumo.exe'
else:
    sumo_binary = 'sumo'  # Linux/Ubuntu
```

### 2. Ensure Headless Mode for Server

```python
# In config.py - Set to False for server
SUMO_GUI = False  # No GUI on server
```

### 3. Path Compatibility (Already Using os.path.join - Good!)

Your code already uses `os.path.join()` which works on both Windows and Linux. ✅

---

## 🏃 Running on Ubuntu Server

### Quick Test

```bash
# Activate virtual environment
source venv/bin/activate

# Run SUMO checker
python utils/sumo_checker.py

# Test network generation (quick)
python -c "from osm.network_generator import generate_network; import config; print('Test OK')"
```

### Run Complete Pipeline

```bash
# Make sure GUI is disabled
# config.py: SUMO_GUI = False

# Run full pipeline
nohup python main.py > training.log 2>&1 &

# Monitor progress
tail -f training.log

# Check process
ps aux | grep python
```

### Run Training Only

```bash
# Start training in background
nohup python train.py --episodes 200 --time 7200 > training.log 2>&1 &

# Monitor
tail -f training.log

# Or use screen/tmux for persistent sessions
screen -S training
python train.py --episodes 200 --time 7200
# Ctrl+A, D to detach
# screen -r training to reattach
```

---

## 📊 Using Screen or Tmux (Recommended)

### Using Screen

```bash
# Install screen
sudo apt install -y screen

# Start new session
screen -S traffic_training

# Run your training
python train.py --episodes 200 --time 7200

# Detach: Ctrl+A, then D
# Reattach: screen -r traffic_training
# List sessions: screen -ls
```

### Using Tmux

```bash
# Install tmux
sudo apt install -y tmux

# Start new session
tmux new -s training

# Run training
python train.py --episodes 200 --time 7200

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t training
# List sessions: tmux ls
```

---

## 🐳 Docker Deployment (Optional)

### Create Dockerfile

```dockerfile
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    sumo sumo-tools \
    && rm -rf /var/lib/apt/lists/*

# Set SUMO_HOME
ENV SUMO_HOME=/usr/share/sumo

# Copy project
WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Run training
CMD ["python3", "train.py"]
```

### Build and Run

```bash
# Build image
docker build -t traffic-signal-rl .

# Run container
docker run -v $(pwd)/models:/app/models \
           -v $(pwd)/metrics:/app/metrics \
           traffic-signal-rl
```

---

## ⚡ Performance Optimization for Server

### 1. Use Multiple CPU Cores

```python
# In config.py - Adjust based on server
import os
NUM_WORKERS = os.cpu_count()  # Use all cores
```

### 2. Disable Unnecessary Logging

```python
# In config.py
VERBOSE = False  # Less console output
LOG_INTERVAL = 50  # Log less frequently
```

### 3. Use GPU (if available)

```bash
# Install CUDA and PyTorch with GPU support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify GPU
python -c "import torch; print(torch.cuda.is_available())"
```

Your code already uses GPU automatically:
```python
# In config.py - Already correct!
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

---

## 📁 File Transfer Between Windows and Ubuntu

### Upload to Server

```bash
# From Windows (using WSL or Git Bash)
scp -r signal_phase-1 user@server:/home/user/

# Or use rsync (faster for updates)
rsync -avz signal_phase-1/ user@server:/home/user/signal_phase-1/
```

### Download Results from Server

```bash
# Download trained models
scp -r user@server:/home/user/signal_phase-1/models ./

# Download metrics
scp -r user@server:/home/user/signal_phase-1/metrics ./

# Download plots
scp -r user@server:/home/user/signal_phase-1/plots ./
```

---

## 🔍 Monitoring Training on Server

### Check Progress

```bash
# View training log
tail -f training.log

# Check GPU usage (if using GPU)
nvidia-smi

# Check CPU/Memory
htop

# Check disk space
df -h
```

### Monitor Metrics

```bash
# Check latest training rewards
tail metrics/training_rewards.csv

# Count episodes completed
wc -l metrics/training_rewards.csv
```

---

## 🐛 Troubleshooting Ubuntu

### Issue 1: SUMO Not Found

```bash
# Check if SUMO is installed
which sumo

# Check SUMO_HOME
echo $SUMO_HOME

# Reinstall if needed
sudo apt install -y sumo sumo-tools
```

### Issue 2: Permission Denied

```bash
# Make scripts executable
chmod +x *.py

# Fix ownership
sudo chown -R $USER:$USER signal_phase-1/
```

### Issue 3: Out of Memory

```bash
# Check memory usage
free -h

# Reduce batch size in config.py
BATCH_SIZE = 32  # Instead of 64

# Or add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue 4: Python Module Not Found

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

---

## 📋 Quick Start Script for Ubuntu

Create `setup_ubuntu.sh`:

```bash
#!/bin/bash

echo "Setting up Traffic Signal Optimization on Ubuntu..."

# Update system
sudo apt update

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv

# Install SUMO
sudo add-apt-repository ppa:sumo/stable -y
sudo apt update
sudo apt install -y sumo sumo-tools

# Set SUMO_HOME
echo 'export SUMO_HOME="/usr/share/sumo"' >> ~/.bashrc
export SUMO_HOME="/usr/share/sumo"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python utils/sumo_checker.py

echo "Setup complete! Activate venv with: source venv/bin/activate"
```

Run it:
```bash
chmod +x setup_ubuntu.sh
./setup_ubuntu.sh
```

---

## ✅ Deployment Checklist

- [ ] Ubuntu 18.04+ installed
- [ ] Python 3.8+ installed
- [ ] SUMO installed and SUMO_HOME set
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] SUMO checker passes (`python utils/sumo_checker.py`)
- [ ] Config set to headless mode (`SUMO_GUI = False`)
- [ ] Project files uploaded to server
- [ ] Screen/tmux session started
- [ ] Training running in background
- [ ] Monitoring logs (`tail -f training.log`)

---

## 🎯 Recommended Server Workflow

```bash
# 1. Connect to server
ssh user@server

# 2. Navigate to project
cd signal_phase-1

# 3. Activate virtual environment
source venv/bin/activate

# 4. Start screen session
screen -S training

# 5. Run training
python train.py --episodes 200 --time 7200

# 6. Detach (Ctrl+A, D)

# 7. Logout (training continues)
exit

# 8. Later, reconnect and check
ssh user@server
screen -r training

# 9. Download results when done
# (from local machine)
scp -r user@server:~/signal_phase-1/models ./
scp -r user@server:~/signal_phase-1/metrics ./
```

---

## 🚀 Summary

**Your code is 100% compatible with Ubuntu!**

**Key Points:**
- ✅ All paths use `os.path.join()` (cross-platform)
- ✅ SUMO binary detection handles Linux
- ✅ No Windows-specific dependencies
- ✅ Can run headless (no GUI needed)
- ✅ GPU support works on Linux

**Just remember:**
1. Install SUMO on Ubuntu
2. Set `SUMO_GUI = False` in config
3. Use screen/tmux for long training
4. Monitor with `tail -f training.log`

**You're ready to deploy! 🎉**
