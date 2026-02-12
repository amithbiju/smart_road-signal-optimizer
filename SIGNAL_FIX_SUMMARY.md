# Signal Timing Fix - Summary

## 🐛 Bug Found!

**Location:** `sumo/sumo_env.py`, line 208

**Problem:**
```python
if self.phase_durations[junction_id] >= self.min_green_time:
```

This checks if duration ≥ 10 **steps** (10 seconds), BUT:
1. SUMO automatically inserts yellow phases (6 seconds)
2. Phase counter includes yellow time
3. Agent can switch during/after yellow
4. Effective green time is much shorter

## ✅ Recommended Fixes

### Fix 1: Increase Minimum Green Time
```python
# In config.py
MIN_GREEN_TIME = 20  # Increase from 10 to 20 seconds
```

### Fix 2: Add Switching Penalty
```python
# In config.py
PHASE_SWITCH_PENALTY = 10.0  # Penalize unnecessary switching
```

Then update `reward_calculator.py` to use it.

### Fix 3: Retrain with Better Parameters
```bash
python train.py --episodes 200 --time 7200
```

## 📊 Expected Results After Fix

| Metric | Current | After Fix |
|--------|---------|-----------|
| Switches/Episode | 932 | 30-60 |
| Avg Phase Duration | 6-14s | 20-40s |
| Switch Actions | 36-68% | 15-25% |
| Performance Gain | 8% | **15-20%** |

## 🎯 Quick Implementation

Would you like me to:
1. Update config with new parameters
2. Add switching penalty to reward function
3. Retrain the model

This should fix the excessive switching and improve performance to 15-20%!
