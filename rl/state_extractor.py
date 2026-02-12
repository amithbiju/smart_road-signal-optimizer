"""
State Extractor for Traffic Signal Control
Extracts state information from SUMO simulation via TraCI
"""

import numpy as np
from utils.sumo_checker import setup_sumo_environment

# Set up SUMO environment
setup_sumo_environment()
import traci


class StateExtractor:
    """
    Extracts and normalizes state information for a traffic light junction
    """
    
    def __init__(self, junction_id, incoming_lanes):
        """
        Initialize state extractor
        
        Args:
            junction_id: Traffic light junction ID
            incoming_lanes: List of incoming lane IDs
        """
        self.junction_id = junction_id
        self.incoming_lanes = incoming_lanes
        self.num_lanes = len(incoming_lanes)
        
        # State components:
        # - Queue length per lane (num_lanes)
        # - Waiting time per lane (num_lanes)
        # - Current phase ID (1)
        # - Time since last phase change (1)
        self.state_size = 2 * self.num_lanes + 2
        
        # For normalization
        self.max_queue_length = 50  # Assume max 50 vehicles per lane
        self.max_waiting_time = 300  # Assume max 300 seconds waiting
        self.max_phase_duration = 120  # Assume max 120 seconds per phase
        
        # Track phase changes
        self.last_phase = None
        self.phase_duration = 0
    
    def get_state(self):
        """
        Extract current state from SUMO
        
        Returns:
            np.array: Normalized state vector
        """
        state = []
        
        # 1. Queue lengths per lane
        queue_lengths = []
        for lane_id in self.incoming_lanes:
            try:
                # Number of halting vehicles
                queue_length = traci.lane.getLastStepHaltingNumber(lane_id)
                queue_lengths.append(queue_length)
            except:
                queue_lengths.append(0)
        
        # Normalize queue lengths
        normalized_queues = [min(q / self.max_queue_length, 1.0) for q in queue_lengths]
        state.extend(normalized_queues)
        
        # 2. Waiting times per lane
        waiting_times = []
        for lane_id in self.incoming_lanes:
            try:
                # Total waiting time of all vehicles on lane
                waiting_time = traci.lane.getWaitingTime(lane_id)
                waiting_times.append(waiting_time)
            except:
                waiting_times.append(0)
        
        # Normalize waiting times
        normalized_waiting = [min(w / self.max_waiting_time, 1.0) for w in waiting_times]
        state.extend(normalized_waiting)
        
        # 3. Current phase ID
        try:
            current_phase = traci.trafficlight.getPhase(self.junction_id)
            
            # Track phase changes
            if self.last_phase is None:
                self.last_phase = current_phase
                self.phase_duration = 0
            elif current_phase != self.last_phase:
                self.last_phase = current_phase
                self.phase_duration = 0
            else:
                self.phase_duration += 1
            
            # Normalize phase ID (assume max 8 phases)
            normalized_phase = current_phase / 8.0
        except:
            normalized_phase = 0.0
        
        state.append(normalized_phase)
        
        # 4. Time since last phase change
        normalized_duration = min(self.phase_duration / self.max_phase_duration, 1.0)
        state.append(normalized_duration)
        
        return np.array(state, dtype=np.float32)
    
    def get_raw_metrics(self):
        """
        Get raw (unnormalized) metrics for logging
        
        Returns:
            dict: Raw metrics
        """
        total_queue = 0
        total_waiting = 0
        
        for lane_id in self.incoming_lanes:
            try:
                total_queue += traci.lane.getLastStepHaltingNumber(lane_id)
                total_waiting += traci.lane.getWaitingTime(lane_id)
            except:
                pass
        
        try:
            current_phase = traci.trafficlight.getPhase(self.junction_id)
        except:
            current_phase = 0
        
        return {
            'total_queue_length': total_queue,
            'total_waiting_time': total_waiting,
            'current_phase': current_phase,
            'phase_duration': self.phase_duration
        }
    
    def reset(self):
        """Reset phase tracking"""
        self.last_phase = None
        self.phase_duration = 0
