"""
Reward Calculator for Traffic Signal Control
Computes rewards based on traffic metrics
"""

from utils.sumo_checker import setup_sumo_environment

# Set up SUMO environment
setup_sumo_environment()
import traci


class RewardCalculator:
    """
    Calculates reward for traffic signal control
    Reward = -(waiting_time + 0.5 * queue_length)
    """
    
    def __init__(
        self,
        junction_id,
        incoming_lanes,
        waiting_time_weight=1.0,
        queue_length_weight=0.5,
        switch_penalty=0.0
    ):
        """
        Initialize reward calculator
        
        Args:
            junction_id: Traffic light junction ID
            incoming_lanes: List of incoming lane IDs
            waiting_time_weight: Weight for waiting time in reward
            queue_length_weight: Weight for queue length in reward
            switch_penalty: Penalty for switching phases (optional)
        """
        self.junction_id = junction_id
        self.incoming_lanes = incoming_lanes
        self.waiting_time_weight = waiting_time_weight
        self.queue_length_weight = queue_length_weight
        self.switch_penalty = switch_penalty
        
        # Track previous action for switch penalty
        self.last_action = None
    
    def calculate_reward(self, action=None):
        """
        Calculate reward based on current traffic state
        
        Args:
            action: Action taken (0=keep, 1=switch) - for switch penalty
        
        Returns:
            float: Reward value (negative = bad, less negative = better)
        """
        # Get total waiting time across all lanes
        total_waiting_time = 0
        for lane_id in self.incoming_lanes:
            try:
                total_waiting_time += traci.lane.getWaitingTime(lane_id)
            except:
                pass
        
        # Get total queue length across all lanes
        total_queue_length = 0
        for lane_id in self.incoming_lanes:
            try:
                total_queue_length += traci.lane.getLastStepHaltingNumber(lane_id)
            except:
                pass
        
        # Base reward: minimize waiting time and queue length
        reward = -(
            self.waiting_time_weight * total_waiting_time +
            self.queue_length_weight * total_queue_length
        )
        
        # Penalize unnecessary switching to reduce flickering
        if self.switch_penalty > 0 and action is not None:
            if action == 1:  # Switch action
                reward -= self.switch_penalty
                # Additional penalty if switching very frequently
                if self.last_action == 1:  # Switched last time too
                    reward -= self.switch_penalty * 0.5  # Extra 50% penalty for consecutive switches
        
        self.last_action = action
        
        return reward
    
    def get_metrics(self):
        """
        Get current traffic metrics
        
        Returns:
            dict: Traffic metrics
        """
        total_waiting_time = 0
        total_queue_length = 0
        
        for lane_id in self.incoming_lanes:
            try:
                total_waiting_time += traci.lane.getWaitingTime(lane_id)
                total_queue_length += traci.lane.getLastStepHaltingNumber(lane_id)
            except:
                pass
        
        return {
            'waiting_time': total_waiting_time,
            'queue_length': total_queue_length
        }
    
    def reset(self):
        """Reset tracking variables"""
        self.last_action = None
