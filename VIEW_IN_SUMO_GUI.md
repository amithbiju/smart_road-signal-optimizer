# How to Visualize Your Traffic Signals in SUMO GUI

## 🎮 Quick Start - Watch Your Signals in Action

### Method 1: Enable GUI in Config (Recommended)

1. **Edit `config.py`:**
   ```python
   # Find this line (around line 25):
   SUMO_GUI = False
   
   # Change to:
   SUMO_GUI = True
   ```

2. **Run evaluation with GUI:**
   ```bash
   python evaluate.py --mode rl --episodes 1
   ```

3. **SUMO GUI will open** showing:
   - Your road network
   - Traffic lights (colored circles)
   - Vehicles moving
   - Real-time signal changes

---

### Method 2: Quick Test Script

Create a simple viewer script:

```python
# view_signals.py
import config
config.SUMO_GUI = True  # Override config

from sumo.sumo_env import SUMOEnvironment

env = SUMOEnvironment(
    network_file=config.NETWORK_FILE,
    route_file=config.ROUTE_FILE,
    use_gui=True,  # Enable GUI
    step_length=1.0
)

# Start simulation
env.reset()

# Run for 1000 steps (watch signals change)
for step in range(1000):
    actions = {jid: 0 for jid in env.tl_junctions}  # Keep current phase
    env.step(actions)

env.close()
```

Run: `python view_signals.py`

---

### Method 3: Use Trained Agent with GUI

Watch your trained DQN agent control the signals:

```bash
# 1. Enable GUI in config.py
# SUMO_GUI = True

# 2. Run RL evaluation
python evaluate.py --mode rl --episodes 1
```

---

## 🎨 SUMO GUI Features

### When GUI Opens:

**Traffic Lights:**
- 🟢 Green circle = Green phase
- 🟡 Yellow circle = Yellow phase
- 🔴 Red circle = Red phase

**Controls:**
- ▶️ Play/Pause button
- ⏩ Speed slider (slow down to watch signals)
- 🔍 Zoom in/out
- 📊 Right-click junction → "Show Parameter"

### View Signal Details:

1. **Right-click on traffic light junction**
2. **Select "Show Parameter"**
3. **See:**
   - Current phase
   - Phase duration
   - Next phase
   - State string

---

## 🚦 What You'll See

### Junction Visualization:

```
     ↑
     │ (RED)
     │
─────┼───── (GREEN) →
     │
     │ (RED)
     ↓
```

**Colors show current phase:**
- Green lanes: Traffic flows
- Red lanes: Traffic stopped
- Yellow lanes: Transition

### Signal Changes:

Watch as your DQN agent:
- Extends green when traffic is heavy
- Switches early when no vehicles
- Adapts to real-time congestion

---

## 📋 Step-by-Step Guide

### 1. Enable GUI

```python
# config.py
SUMO_GUI = True
```

### 2. Run Simulation

```bash
# Watch baseline (fixed-time)
python evaluate.py --mode baseline --episodes 1

# Watch RL agent (adaptive)
python evaluate.py --mode rl --episodes 1
```

### 3. Control Simulation Speed

In SUMO GUI:
- **Delay slider** (top right): Move left = faster, right = slower
- **Step button**: Advance one step at a time
- **Play button**: Continuous simulation

### 4. Inspect Junctions

- **Click junction**: Select it
- **Right-click**: Show menu
- **"Show Parameter"**: See phase details
- **"Show TLS-State"**: See signal states

---

## 🎯 Compare Baseline vs RL

### Run Both and Compare:

**Terminal 1 - Baseline:**
```bash
python evaluate.py --mode baseline --episodes 1
```

**Terminal 2 - RL:**
```bash
python evaluate.py --mode rl --episodes 1
```

**Watch the difference:**
- Baseline: Fixed 24s/39s green phases
- RL: Adaptive 4-39s based on traffic

---

## 🔧 Troubleshooting

### GUI Doesn't Open?

**Check SUMO installation:**
```bash
python utils/sumo_checker.py
```

**Verify sumo-gui exists:**
```bash
# Windows
dir "C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"
```

### Simulation Too Fast?

In SUMO GUI:
- Move **Delay slider** to the right
- Or click **Step** button for manual control

### Can't See Traffic Lights?

In SUMO GUI:
- **View** → **Show Traffic Lights**
- Zoom in closer to junctions

---

## 💡 Pro Tips

### 1. Slow Motion View
```python
# In config.py
SUMO_STEP_LENGTH = 0.1  # Slower simulation
```

### 2. Highlight Waiting Vehicles
In SUMO GUI:
- **View** → **Vehicles** → **Color by waiting time**
- Red vehicles = waiting long (congestion!)

### 3. Show Queue Lengths
In SUMO GUI:
- **View** → **Show lane to lane connections**
- See which lanes are congested

### 4. Track Specific Vehicle
- **Click vehicle** in GUI
- **Right-click** → "Start Tracking"
- Camera follows vehicle

---

## 🎬 Recording Your Simulation

### Save Screenshots:
In SUMO GUI:
- **Edit** → **Edit Visualization**
- **Output** tab → Enable screenshots

### Save Video:
Use screen recording software while SUMO GUI runs

---

## ✅ Quick Commands

```bash
# Enable GUI
# Edit config.py: SUMO_GUI = True

# Watch baseline signals
python evaluate.py --mode baseline --episodes 1

# Watch RL-controlled signals
python evaluate.py --mode rl --episodes 1

# View network only (no traffic)
sumo-gui -n sumo/network.net.xml
```

---

## 🎓 What to Look For

When watching your RL agent:

✅ **Good signs:**
- Green extends when vehicles waiting
- Quick switch when no traffic
- Smooth traffic flow
- Minimal queue buildup

❌ **Bad signs (before fix):**
- Rapid flickering (switching every few seconds)
- Very short green phases (1-5s)
- Vehicles can't clear intersection
- Long queues building up

**After retraining with fixes, you should see stable, intelligent signal control!**
