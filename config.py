import os
import json

# ============================================================================
# PROJECT PATHS
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Output Base Directory (Dynamic for Multi-Project Support)
# If PROJECT_OUTPUT_DIR is set, all outputs go there.
# Otherwise, default to BASE_DIR
PROJECT_OUTPUT_DIR = os.environ.get('PROJECT_OUTPUT_DIR', BASE_DIR)

# Enable/Disable Directory Creation (Prevent creating default dirs if using project dir)
CREATE_DEFAULT_DIRS = os.environ.get('CREATE_DEFAULT_DIRS', 'True').lower() == 'true'

# OSM Data
OSM_DIR = os.path.join(PROJECT_OUTPUT_DIR, "osm")
OSM_FILE = os.path.join(OSM_DIR, "map.osm.xml")

# SUMO Files
SUMO_DIR = os.path.join(PROJECT_OUTPUT_DIR, "sumo")
NETWORK_FILE = os.path.join(SUMO_DIR, "network.net.xml")
ROUTE_FILE = os.path.join(SUMO_DIR, "routes.rou.xml")
TRIPS_FILE = os.path.join(SUMO_DIR, "trips.trips.xml")
SUMO_CONFIG_FILE = os.path.join(SUMO_DIR, "config.sumocfg")

# Output Directories
MODELS_DIR = os.path.join(PROJECT_OUTPUT_DIR, "models")
METRICS_DIR = os.path.join(PROJECT_OUTPUT_DIR, "metrics")
PLOTS_DIR = os.path.join(PROJECT_OUTPUT_DIR, "plots")

# ============================================================================
# BOUNDING BOX (Latitude/Longitude)
# ============================================================================
# Default: Kerala, India coordinates
# Can be overridden by env var 'BOUNDING_BOX' as JSON string
bbox_env = os.environ.get('BOUNDING_BOX')
if bbox_env:
    try:
        BOUNDING_BOX = json.loads(bbox_env)
    except json.JSONDecodeError:
        print("Warning: Invalid BOUNDING_BOX env var, using default.")
        BOUNDING_BOX = {
            'south': 8.46823,
            'north': 8.47407,
            'west': 76.97605,
            'east': 76.98397
        }
else:
    BOUNDING_BOX = {
        'south': 8.46823,
        'north': 8.47407,
        'west': 76.97605,
        'east': 76.98397
    }

# ============================================================================
# SUMO SIMULATION PARAMETERS
# ============================================================================
SUMO_STEP_LENGTH = 1.0  # Simulation step in seconds
SUMO_GUI = os.environ.get('SUMO_GUI', 'False').lower() == 'true'
SUMO_SEED = 42  # Random seed for reproducibility

# Traffic Generation
TRAFFIC_PERIOD = 1  # Period for random trips (seconds)
TRAFFIC_PROBABILITY = 0.3  # Probability of vehicle generation
MIN_TRIP_LENGTH = 100  # Minimum trip length in meters

# Signal Control
# Allow override via env var
MIN_GREEN_TIME = int(os.environ.get('MIN_GREEN_TIME', 20))
YELLOW_TIME = 3  # Yellow phase duration (seconds)

# ============================================================================
# DQN HYPERPARAMETERS
# ============================================================================
# Network Architecture
STATE_SIZE = None  # Will be determined dynamically based on junction
HIDDEN_SIZE_1 = 128
HIDDEN_SIZE_2 = 128
ACTION_SIZE = 2  # KEEP_CURRENT_PHASE (0), SWITCH_TO_NEXT_PHASE (1)

# Training Parameters
LEARNING_RATE = float(os.environ.get('LEARNING_RATE', 1e-3))
GAMMA = 0.99  # Discount factor
BATCH_SIZE = 64
REPLAY_BUFFER_SIZE = 50000

# Exploration
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_DECAY = 0.997

# Target Network
TARGET_UPDATE_FREQUENCY = 1000  # Update target network every N steps

# Training Duration
MAX_EPISODES = int(os.environ.get('MAX_EPISODES', 1000))
MAX_STEPS_PER_EPISODE = 3600  # Maximum steps per episode (1 hour simulation)
TARGET_TRAINING_TIME = 25200  # Target training time in seconds (~7 hours)

# ============================================================================
# REWARD FUNCTION PARAMETERS
# ============================================================================
WAITING_TIME_WEIGHT = 1.0
QUEUE_LENGTH_WEIGHT = 0.5
PHASE_SWITCH_PENALTY = 10.0  # Penalty for switching phases

# ============================================================================
# EVALUATION PARAMETERS
# ============================================================================
EVAL_EPISODES = 5  # Number of episodes for evaluation
EVAL_EPSILON = 0.0  # No exploration during evaluation

# ============================================================================
# LOGGING & CHECKPOINTING
# ============================================================================
LOG_INTERVAL = 10  # Log metrics every N episodes
CHECKPOINT_INTERVAL = 50  # Save models every N episodes
VERBOSE = True  # Print progress to console

# ============================================================================
# DEVICE CONFIGURATION
# ============================================================================
import torch
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ============================================================================
# METRIC FILE NAMES
# ============================================================================
TRAINING_REWARDS_CSV = os.path.join(METRICS_DIR, "training_rewards.csv")
EPISODE_STATS_CSV = os.path.join(METRICS_DIR, "episode_stats.csv")
WAITING_TIME_BEFORE_CSV = os.path.join(METRICS_DIR, "waiting_time_before.csv")
WAITING_TIME_AFTER_CSV = os.path.join(METRICS_DIR, "waiting_time_after.csv")
QUEUE_LENGTH_BEFORE_CSV = os.path.join(METRICS_DIR, "queue_length_before.csv")
QUEUE_LENGTH_AFTER_CSV = os.path.join(METRICS_DIR, "queue_length_after.csv")
SIGNAL_TIMINGS_BEFORE_CSV = os.path.join(METRICS_DIR, "signal_timings_before.csv")
SIGNAL_TIMINGS_AFTER_CSV = os.path.join(METRICS_DIR, "signal_timings_after.csv")

# ============================================================================
# PLOT FILE NAMES
# ============================================================================
REWARD_PLOT = os.path.join(PLOTS_DIR, "reward_vs_episode.png")
WAITING_TIME_PLOT = os.path.join(PLOTS_DIR, "waiting_time_comparison.png")
QUEUE_LENGTH_PLOT = os.path.join(PLOTS_DIR, "queue_length_comparison.png")

# ============================================================================
# CREATE DIRECTORIES
# ============================================================================
def create_directories():
    """Create all necessary directories if they don't exist"""
    # Only create if we are using default dirs OR if explicitly told to via project dir
    if CREATE_DEFAULT_DIRS:
        for directory in [OSM_DIR, SUMO_DIR, MODELS_DIR, METRICS_DIR, PLOTS_DIR]:
            os.makedirs(directory, exist_ok=True)
        print(f"[OK] Created project directories in {PROJECT_OUTPUT_DIR}")

if __name__ == "__main__":
    create_directories()
    print(f"Device: {DEVICE}")
    print(f"Bounding Box: {BOUNDING_BOX}")
