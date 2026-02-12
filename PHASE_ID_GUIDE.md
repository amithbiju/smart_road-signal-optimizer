# Understanding SUMO Traffic Light Phase IDs

## 🚦 What Are Phase IDs?

**Phase IDs** are SUMO's numbering system for different signal states at an intersection. Each phase defines which traffic movements get green, yellow, or red lights.

---

## 📊 Your Phase Output Explained

```
Phase ID   Avg        Min        Max        Std        Count
----------------------------------------------------------------------
0          13.8       4.0        39.0       15.5       460
1          6.0        6.0        6.0        0.0        455
2          13.6       4.0        39.0       15.6       455
3          6.0        6.0        6.0        0.0        455
```

### Pattern Analysis:

| Phase | Type | Duration | Purpose |
|-------|------|----------|---------|
| **0** | GREEN | 13.8s avg | Main traffic flow (e.g., North-South) |
| **1** | YELLOW | 6.0s fixed | Transition/clearance |
| **2** | GREEN | 13.6s avg | Cross traffic (e.g., East-West) |
| **3** | YELLOW | 6.0s fixed | Transition/clearance |

**Cycle:** Phase 0 → Phase 1 → Phase 2 → Phase 3 → repeat

---

## 🔍 How SUMO Defines Phases

### Phase State String

Each phase has a **state string** that defines signals for all connections:

**Example:** `"GGrrrrGGrrrr"`

Each character represents one traffic movement:
- `G` = Green (with priority)
- `g` = Green (no priority, yield)
- `y` = Yellow
- `r` = Red
- `s` = Red/Yellow (German style)

### Position in String = Connection Index

```
Position 0: From lane A → To lane X: G (Green)
Position 1: From lane B → To lane Y: G (Green)
Position 2: From lane C → To lane Z: r (Red)
...
```

---

## 🛣️ Typical 4-Phase Signal Pattern

### Phase 0: North-South Green
```
State: "GGrrrrGGrrrr"
- North → South: GREEN
- South → North: GREEN
- East → West: RED
- West → East: RED
```

### Phase 1: North-South Yellow
```
State: "yyrrrryyrrrr"
- North → South: YELLOW
- South → North: YELLOW
- East → West: RED
- West → East: RED
```

### Phase 2: East-West Green
```
State: "rrGGrrrrGGrr"
- North → South: RED
- South → North: RED
- East → West: GREEN
- West → East: GREEN
```

### Phase 3: East-West Yellow
```
State: "rryyrrrryyrr"
- North → South: RED
- South → North: RED
- East → West: YELLOW
- West → East: YELLOW
```

---

## 🔧 How to Inspect Your Specific Phases

### Method 1: Use the Inspector Tool

```bash
# Inspect all junctions
python inspect_phases.py

# Inspect specific junction
python inspect_phases.py --junction cluster_6098633245_6975349630_6975349631
```

**Output shows:**
- Phase durations
- State strings
- Which lanes get which colors
- Connection mappings

### Method 2: Check SUMO Network File

```bash
# View raw XML
type sumo\network.net.xml | findstr "<phase"
```

**Example output:**
```xml
<phase duration="24" state="GGrrrrGGrrrr"/>
<phase duration="6"  state="yyrrrryyrrrr"/>
<phase duration="24" state="rrGGrrrrGGrr"/>
<phase duration="6"  state="rryyrrrryyrr"/>
```

### Method 3: Use SUMO GUI

```python
# In config.py
SUMO_GUI = True

# Then run
python evaluate.py --mode rl --episodes 1
```

Right-click junction → "Show Parameter" → See phase definitions

---

## 📐 Understanding Your Junction

### Junction: cluster_6098633245_6975349630_6975349631

**6 Phases detected:**
- Phases 0, 2, 4: Green phases (variable duration)
- Phases 1, 3, 5: Yellow phases (fixed 6s)

**This is a 3-way green cycle:**
1. Direction A gets green (Phase 0)
2. Yellow transition (Phase 1)
3. Direction B gets green (Phase 2)
4. Yellow transition (Phase 3)
5. Direction C gets green (Phase 4)
6. Yellow transition (Phase 5)
7. Repeat

### Junction: cluster_12637978186_12637992859_12663377950_305427579

**4 Phases detected:**
- Phases 0, 2: Green phases (variable duration)
- Phases 1, 3: Yellow phases (fixed 6s)

**This is a 2-way cycle:**
1. Main road gets green (Phase 0)
2. Yellow transition (Phase 1)
3. Cross road gets green (Phase 2)
4. Yellow transition (Phase 3)
5. Repeat

---

## 🎯 What Your DQN Agent Learned

### Before (Baseline):
```
Phase 0: Always 24s or 39s (fixed)
Phase 2: Always 24s or 39s (fixed)
```

### After (RL):
```
Phase 0: 4-39s (adaptive!)
  - Short (4s) when no traffic
  - Long (39s) when congested
  - Average: 13.8s

Phase 2: 4-39s (adaptive!)
  - Short (4s) when no traffic
  - Long (39s) when congested
  - Average: 13.6s
```

**The agent learned to:**
- Extend green when traffic is heavy
- Cut green short when no vehicles
- Adapt to real-time conditions

---

## 🔍 Decoding Phase States

### Example State String: `"GGrrrrGGrrrr"`

**For a 4-way intersection:**

```
Position  Signal  Meaning
0         G       North straight: GREEN
1         G       North right turn: GREEN
2         r       North left turn: RED
3         r       East straight: RED
4         r       East right turn: RED
5         r       East left turn: RED
6         G       South straight: GREEN
7         G       South right turn: GREEN
8         r       South left turn: RED
9         r       West straight: RED
10        r       West right turn: RED
11        r       West left turn: RED
```

---

## 📋 Quick Reference

### Signal Colors:
- `G` = Green (priority)
- `g` = Green (yield)
- `y` = Yellow
- `r` = Red
- `s` = Red/Yellow
- `o` = Off

### Phase Types:
- **Even phases (0, 2, 4)**: Usually green phases
- **Odd phases (1, 3, 5)**: Usually yellow/transition

### Yellow Phase Duration:
- **Fixed at 6 seconds** (SUMO default)
- Cannot be changed by RL agent
- Automatically inserted between green phases

---

## 🛠️ Tools to Explore Phases

### 1. Phase Inspector (Created)
```bash
python inspect_phases.py
```

### 2. SUMO GUI
```python
# config.py: SUMO_GUI = True
python evaluate.py --mode rl --episodes 1
```

### 3. Network XML
```bash
type sumo\network.net.xml | findstr "phase"
```

### 4. TraCI (Programmatic)
```python
import traci
logic = traci.trafficlight.getAllProgramLogics(junction_id)[0]
for i, phase in enumerate(logic.phases):
    print(f"Phase {i}: {phase.state} ({phase.duration}s)")
```

---

## 🎓 Key Takeaways

1. **Phase IDs are just numbers** (0, 1, 2, 3...)
2. **Even phases = Green** (traffic flows)
3. **Odd phases = Yellow** (transitions)
4. **State string defines colors** for each movement
5. **Your agent controls green duration**, not yellow
6. **Yellow is always 6 seconds** (fixed by SUMO)

---

## 💡 Want More Details?

Run the inspector to see exact mappings:

```bash
python inspect_phases.py --junction cluster_6098633245_6975349630_6975349631
```

This will show you:
- Exact state strings
- Which lanes connect where
- What each position means
- Full phase definitions
