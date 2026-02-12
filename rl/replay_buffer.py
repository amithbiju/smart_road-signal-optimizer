"""
Experience Replay Buffer for DQN
Stores and samples transitions for training
"""

import numpy as np
import random
from collections import deque


class ReplayBuffer:
    """
    Experience replay buffer for DQN training
    Stores transitions and provides random sampling
    """
    
    def __init__(self, capacity=50000):
        """
        Initialize replay buffer
        
        Args:
            capacity: Maximum number of transitions to store
        """
        self.buffer = deque(maxlen=capacity)
        self.capacity = capacity
    
    def push(self, state, action, reward, next_state, done):
        """
        Add a transition to the buffer
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Whether episode is done
        """
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        """
        Sample a random batch of transitions
        
        Args:
            batch_size: Number of transitions to sample
        
        Returns:
            tuple: (states, actions, rewards, next_states, dones)
        """
        batch = random.sample(self.buffer, batch_size)
        
        states, actions, rewards, next_states, dones = zip(*batch)
        
        return (
            np.array(states, dtype=np.float32),
            np.array(actions, dtype=np.int64),
            np.array(rewards, dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones, dtype=np.float32)
        )
    
    def __len__(self):
        """Return current size of buffer"""
        return len(self.buffer)
    
    def is_ready(self, batch_size):
        """Check if buffer has enough samples for training"""
        return len(self.buffer) >= batch_size
    
    def clear(self):
        """Clear the buffer"""
        self.buffer.clear()
