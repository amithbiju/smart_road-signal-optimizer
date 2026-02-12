"""
Deep Q-Network (DQN) Neural Network Architecture
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DQN(nn.Module):
    """
    Deep Q-Network for traffic signal control
    
    Architecture:
        Input (state_size) -> Linear(128) -> ReLU -> Linear(128) -> ReLU -> Linear(2)
    """
    
    def __init__(self, state_size, hidden_size_1=128, hidden_size_2=128, action_size=2):
        """
        Initialize DQN
        
        Args:
            state_size: Size of state vector
            hidden_size_1: Size of first hidden layer
            hidden_size_2: Size of second hidden layer
            action_size: Number of actions (2: keep/switch)
        """
        super(DQN, self).__init__()
        
        self.fc1 = nn.Linear(state_size, hidden_size_1)
        self.fc2 = nn.Linear(hidden_size_1, hidden_size_2)
        self.fc3 = nn.Linear(hidden_size_2, action_size)
    
    def forward(self, x):
        """
        Forward pass
        
        Args:
            x: Input state tensor
        
        Returns:
            Q-values for each action
        """
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x
    
    def save(self, filepath):
        """Save model weights"""
        torch.save(self.state_dict(), filepath)
    
    def load(self, filepath, device='cpu'):
        """Load model weights"""
        self.load_state_dict(torch.load(filepath, map_location=device))
