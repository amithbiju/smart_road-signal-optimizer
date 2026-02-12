# Traffic Signal Optimization using SUMO + Deep Q-Learning

An academic-grade traffic signal optimization system that uses SUMO (Simulation of Urban MObility) and Deep Q-Learning (DQN) to optimize traffic signal timings at multiple junctions.

## 🎯 Overview

This system:
- Downloads OpenStreetMap data for any latitude/longitude bounding box
- Converts OSM data to SUMO network format
- Trains independent DQN agents per traffic light junction
- Optimizes signal switching to minimize congestion
- Provides quantitative comparison against baseline fixed-time signals

## 📋 Requirements

### Software
- **Python 3.8+**
- **SUMO** (Simulation of Urban MObility)
  - Download from: https://sumo.dlr.de/docs/Downloads.php
  - Set `SUMO_HOME` environment variable

### Python Dependencies
```bash
pip install -r requirements.txt
```

Dependencies include:
- PyTorch (for DQN)
- NumPy, Pandas (data processing)
- Matplotlib (visualization)
- Requests (OSM download)

## 🚀 Quick Start

### 1. Verify SUMO Installation
```bash
python utils/sumo_checker.py
```

### 2. Run Complete Pipeline
```bash
python main.py
```

This will:
1. Download OSM data for the configured bounding box
2. Generate SUMO network
3. Generate random traffic
4. Evaluate baseline (fixed-time signals)
5. Train DQN agents (~2 hours)
6. Evaluate RL-controlled signals
7. Generate comparison plots

### 3. View Results
- **Models**: `models/junction_<id>_dqn.pt`
- **Metrics**: `metrics/*.csv`
- **Plots**: `plots/*.png`

## ⚙️ Configuration

Edit `config.py` to customize:

### Bounding Box
```python
BOUNDING_BOX = {
    'south': 8.46823,
    'north': 8.47407,
    'west': 76.97605,
    'east': 76.98397
}
```

### DQN Hyperparameters
```python
LEARNING_RATE = 1e-3
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_END = 0.05
EPSILON_DECAY = 0.995
BATCH_SIZE = 64
REPLAY_BUFFER_SIZE = 50000
```

### Training Duration
```python
MAX_EPISODES = 1000
TARGET_TRAINING_TIME = 7200  # 2 hours
```

## 📊 System Architecture

```
signal_phase-1/
├── config.py              # Central configuration
├── main.py                # Pipeline orchestrator
├── train.py               # DQN training script
├── evaluate.py            # Evaluation script
├── visualize.py           # Visualization script
├── requirements.txt       # Python dependencies
│
├── osm/                   # OSM data handling
│   ├── osm_downloader.py  # Download OSM data
│   ├── network_generator.py  # Convert to SUMO network
│   └── traffic_generator.py  # Generate traffic
│
├── rl/                    # Reinforcement Learning
│   ├── dqn_network.py     # Neural network architecture
│   ├── dqn_agent.py       # DQN agent implementation
│   ├── replay_buffer.py   # Experience replay
│   ├── state_extractor.py # State extraction from SUMO
│   └── reward_calculator.py  # Reward function
│
├── sumo/                  # SUMO integration
│   └── sumo_env.py        # SUMO environment wrapper
│
├── utils/                 # Utilities
│   ├── logger.py          # Logging utilities
│   └── sumo_checker.py    # SUMO installation checker
│
├── models/                # Trained models (generated)
├── metrics/               # CSV metrics (generated)
├── plots/                 # Visualization plots (generated)
└── osm/                   # OSM data (generated)
    └── map.osm.xml
```

## 🧠 Reinforcement Learning Design

### State Space (Per Junction)
```
state = [
  queue_length_lane_1,
  queue_length_lane_2,
  ...
  waiting_time_lane_1,
  waiting_time_lane_2,
  ...
  current_phase_id,
  time_since_last_phase_change
]
```

### Action Space
- `0`: KEEP_CURRENT_PHASE
- `1`: SWITCH_TO_NEXT_PHASE

### Reward Function
```
reward = -(waiting_time + 0.5 × queue_length)
```

### DQN Architecture
```
Input (state_size) 
  → Linear(128) → ReLU 
  → Linear(128) → ReLU 
  → Linear(2)
```

## 🎮 Usage Examples

### Run Only Training (Skip Data Preparation)
```bash
python main.py --skip-download --skip-network --skip-traffic --skip-baseline
```

### Custom Training Duration (1 hour)
```bash
python main.py --training-time 3600
```

### Evaluate Existing Models
```bash
python evaluate.py --mode rl --episodes 10
```

### Generate Visualizations Only
```bash
python visualize.py
```

### Train Specific Number of Episodes
```bash
python train.py --episodes 500
```

## 📈 Expected Outputs

### 1. Trained Models
- `models/junction_<id>_dqn.pt` - One model per junction

### 2. Metrics (CSV)
- `training_rewards.csv` - Training progress
- `episode_stats.csv` - Detailed episode statistics
- `waiting_time_before.csv` - Baseline waiting times
- `waiting_time_after.csv` - RL waiting times
- `signal_timings_before.csv` - Baseline signal timings
- `signal_timings_after.csv` - RL signal timings

### 3. Visualizations
- `reward_vs_episode.png` - Training progress
- `waiting_time_comparison.png` - Before/after comparison

## ✅ Validation Checklist

- [ ] SUMO installation verified
- [ ] OSM data downloaded successfully
- [ ] Network contains traffic light junctions
- [ ] Traffic generation creates sufficient congestion
- [ ] Baseline shows high waiting times (congestion visible)
- [ ] Training completes without errors
- [ ] RL evaluation shows improvement over baseline
- [ ] Models can be loaded and reused
- [ ] Visualizations clearly show improvement

## 🔧 Troubleshooting

### No Traffic Light Junctions Found
- Try a larger bounding box
- Choose an urban area with traffic signals
- Check OSM data quality

### SUMO Not Found
- Install SUMO from https://sumo.dlr.de/docs/Downloads.php
- Set `SUMO_HOME` environment variable
- Add SUMO bin directory to PATH

### Training Too Slow
- Reduce `MAX_EPISODES` or `TARGET_TRAINING_TIME`
- Use GPU (set `DEVICE = 'cuda'` in config)
- Reduce `MAX_STEPS_PER_EPISODE`

### No Improvement Over Baseline
- Increase training time
- Adjust reward function weights
- Tune DQN hyperparameters
- Ensure sufficient traffic congestion

## 📚 Academic Context

This project demonstrates:
- **Reinforcement Learning**: DQN with experience replay and target networks
- **Multi-agent Systems**: Independent agents per junction
- **Traffic Optimization**: Real-world application of RL
- **Simulation-based Training**: Using SUMO for realistic traffic modeling

### Key Metrics
- **Waiting Time Reduction**: Primary success metric
- **Queue Length Reduction**: Secondary metric
- **Training Convergence**: Reward improvement over episodes
- **Signal Stability**: No rapid flickering (minimum green time enforced)

## 📄 License

This is an academic project for educational purposes.

## 🙏 Acknowledgments

- **SUMO**: Eclipse SUMO - Simulation of Urban MObility
- **OpenStreetMap**: Map data © OpenStreetMap contributors
- **PyTorch**: Deep learning framework

## 📧 Support

For issues or questions, please check:
1. SUMO installation is correct
2. Python dependencies are installed
3. Configuration matches your use case
4. Logs in console output for specific errors
