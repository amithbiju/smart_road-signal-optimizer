"""
DQN Agent for Traffic Signal Control
Implements ε-greedy policy, experience replay, and target network
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
from rl.dqn_network import DQN
from rl.replay_buffer import ReplayBuffer


class DQNAgent:
    """
    DQN Agent for controlling traffic signals
    Uses ε-greedy exploration and experience replay
    """
    
    def __init__(
        self,
        state_size,
        action_size=2,
        hidden_size_1=128,
        hidden_size_2=128,
        learning_rate=1e-3,
        gamma=0.99,
        epsilon_start=1.0,
        epsilon_end=0.05,
        epsilon_decay=0.995,
        buffer_size=50000,
        batch_size=64,
        target_update_freq=1000,
        device='cpu'
    ):
        """
        Initialize DQN Agent
        
        Args:
            state_size: Dimension of state space
            action_size: Number of actions (2: keep/switch)
            hidden_size_1: First hidden layer size
            hidden_size_2: Second hidden layer size
            learning_rate: Learning rate for optimizer
            gamma: Discount factor
            epsilon_start: Initial exploration rate
            epsilon_end: Minimum exploration rate
            epsilon_decay: Epsilon decay rate per episode
            buffer_size: Replay buffer capacity
            batch_size: Training batch size
            target_update_freq: Steps between target network updates
            device: Device to run on (cpu/cuda)
        """
        self.state_size = state_size
        self.action_size = action_size
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.device = device
        
        # Networks
        self.policy_net = DQN(state_size, hidden_size_1, hidden_size_2, action_size).to(device)
        self.target_net = DQN(state_size, hidden_size_1, hidden_size_2, action_size).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()  # Target network is always in eval mode
        
        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        
        # Loss function
        self.criterion = nn.MSELoss()
        
        # Replay buffer
        self.memory = ReplayBuffer(buffer_size)
        
        # Training step counter
        self.steps = 0
    
    def select_action(self, state, epsilon=None):
        """
        Select action using ε-greedy policy
        
        Args:
            state: Current state
            epsilon: Exploration rate (uses self.epsilon if None)
        
        Returns:
            int: Selected action (0 or 1)
        """
        if epsilon is None:
            epsilon = self.epsilon
        
        # ε-greedy exploration
        if np.random.random() < epsilon:
            return np.random.randint(self.action_size)
        
        # Greedy action
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()
    
    def store_transition(self, state, action, reward, next_state, done):
        """Store transition in replay buffer"""
        self.memory.push(state, action, reward, next_state, done)
    
    def train(self):
        """
        Train the DQN using experience replay
        
        Returns:
            float: Training loss (None if not enough samples)
        """
        # Check if we have enough samples
        if not self.memory.is_ready(self.batch_size):
            return None
        
        # Sample batch
        states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
        
        # Convert to tensors
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # Current Q-values
        current_q_values = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Target Q-values
        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(1)[0]
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        # Compute loss
        loss = self.criterion(current_q_values, target_q_values)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        
        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        
        self.optimizer.step()
        
        # Update step counter
        self.steps += 1
        
        # Update target network
        if self.steps % self.target_update_freq == 0:
            self.update_target_network()
        
        return loss.item()
    
    def update_target_network(self):
        """Copy weights from policy network to target network"""
        self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def decay_epsilon(self):
        """Decay epsilon after each episode"""
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
    
    def reset_epsilon(self):
        """Reset epsilon to initial value"""
        self.epsilon = self.epsilon_start
    
    def save(self, filepath):
        """
        Save agent state
        
        Args:
            filepath: Path to save model
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        torch.save({
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'steps': self.steps,
        }, filepath)
    
    def load(self, filepath):
        """
        Load agent state
        
        Args:
            filepath: Path to load model from
        """
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.steps = checkpoint['steps']
