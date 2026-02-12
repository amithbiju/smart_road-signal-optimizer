# SUMO GUI Visualization - Quick Guide

## ✅ I've Created a GUI Viewer for You!

### 🎮 How to View Your Traffic Network:

**Simple Command:**
```bash
# View with baseline (fixed-time signals) - 3 minutes
python view_gui.py --mode baseline --duration 180

# View with RL agent (adaptive signals) - 5 minutes  
python view_gui.py --mode rl --duration 300
```

**Currently Running:** Baseline mode for 180 seconds

---

## 🖥️ What Should Happen:

1. **SUMO GUI window opens** showing:
   - Your Kerala road network
   - 2 traffic light junctions
   - Vehicles driving
   - Traffic signals changing colors

2. **Watch the simulation:**
   - 🟢 Green = Traffic flowing
   - 🟡 Yellow = Transition
   - 🔴 Red = Stopped

---

## 🎯 GUI Controls:

- **▶️ Play/Pause**: Start/stop simulation
- **⏩ Speed Slider**: Move right = slower (easier to watch)
- **Scroll**: Zoom in/out
- **Drag**: Pan around map
- **Right-click junction**: Show signal details

---

## 🚨 If GUI Doesn't Open:

### Check 1: SUMO GUI Installed?
```bash
# Check if sumo-gui exists
dir "C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe"
```

### Check 2: Run Verification
```bash
python utils/sumo_checker.py
```

### Alternative: Use SUMO Directly
```bash
# Open network in SUMO GUI (no traffic)
"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe" -n sumo/network.net.xml

# Open with traffic
"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe" -n sumo/network.net.xml -r sumo/routes.rou.xml
```

---

## 📋 Quick Commands:

```bash
# Baseline (fixed signals) - 3 min
python view_gui.py --mode baseline --duration 180

# RL agent (adaptive) - 5 min
python view_gui.py --mode rl --duration 300

# Longer simulation - 10 min
python view_gui.py --mode baseline --duration 600
```

---

## 🎓 What to Look For:

**Baseline Mode:**
- Signals change at fixed intervals (24s or 39s)
- Same timing regardless of traffic
- May see queues building up

**RL Mode (after retraining with fixes):**
- Signals adapt to traffic
- Longer green when congested
- Shorter green when no vehicles
- Better traffic flow

---

## ⚙️ Why evaluate.py Didn't Show GUI:

The `evaluate.py` script may have imported config before the change took effect. The `view_gui.py` script forces GUI mode directly, so it should work!

---

## ✅ Next Steps:

1. **Watch the current simulation** (baseline mode running now)
2. **Try RL mode**: `python view_gui.py --mode rl --duration 300`
3. **After retraining**: Watch improved signal behavior
4. **Remember**: Set `SUMO_GUI = False` before retraining (GUI slows training)
