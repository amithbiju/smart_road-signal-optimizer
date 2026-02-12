"""
Visualization Script for Traffic Signal Optimization
Creates plots and graphs from training and evaluation metrics
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import config
from utils.logger import Logger, print_header


def plot_training_rewards():
    """Plot training rewards over episodes"""
    logger = Logger()
    
    if not os.path.exists(config.TRAINING_REWARDS_CSV):
        logger.warning(f"Training rewards file not found: {config.TRAINING_REWARDS_CSV}")
        return
    
    logger.info("Plotting training rewards...")
    
    # Load data
    df = pd.read_csv(config.TRAINING_REWARDS_CSV)
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 1: Total reward
    ax1.plot(df['episode'], df['total_reward'], linewidth=1, alpha=0.6, label='Total Reward')
    
    # Add moving average
    window = min(50, len(df) // 10)
    if window > 1:
        moving_avg = df['total_reward'].rolling(window=window).mean()
        ax1.plot(df['episode'], moving_avg, linewidth=2, color='red', label=f'Moving Avg ({window} episodes)')
    
    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Total Reward')
    ax1.set_title('Training Reward vs Episode')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Epsilon decay
    ax2.plot(df['episode'], df['epsilon'], linewidth=2, color='green')
    ax2.set_xlabel('Episode')
    ax2.set_ylabel('Epsilon (Exploration Rate)')
    ax2.set_title('Epsilon Decay')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(config.REWARD_PLOT, dpi=300, bbox_inches='tight')
    logger.success(f"Saved: {config.REWARD_PLOT}")
    plt.close()


def plot_waiting_time_comparison():
    """Plot waiting time comparison between baseline and RL"""
    logger = Logger()
    
    if not os.path.exists(config.WAITING_TIME_BEFORE_CSV):
        logger.warning(f"Baseline waiting time file not found: {config.WAITING_TIME_BEFORE_CSV}")
        return
    
    if not os.path.exists(config.WAITING_TIME_AFTER_CSV):
        logger.warning(f"RL waiting time file not found: {config.WAITING_TIME_AFTER_CSV}")
        return
    
    logger.info("Plotting waiting time comparison...")
    
    # Load data
    df_before = pd.read_csv(config.WAITING_TIME_BEFORE_CSV)
    df_after = pd.read_csv(config.WAITING_TIME_AFTER_CSV)
    
    # Calculate average waiting time per junction
    before_avg = df_before.groupby('junction_id')['avg_waiting_time'].mean()
    after_avg = df_after.groupby('junction_id')['avg_waiting_time'].mean()
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Per-junction comparison
    junctions = before_avg.index.tolist()
    x = np.arange(len(junctions))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, before_avg.values, width, label='Baseline', color='#e74c3c', alpha=0.8)
    bars2 = ax1.bar(x + width/2, after_avg.values, width, label='RL (DQN)', color='#2ecc71', alpha=0.8)
    
    ax1.set_xlabel('Junction ID')
    ax1.set_ylabel('Average Waiting Time (s)')
    ax1.set_title('Waiting Time Comparison by Junction')
    ax1.set_xticks(x)
    ax1.set_xticklabels(junctions, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=8)
    
    # Plot 2: Overall comparison
    overall_before = before_avg.mean()
    overall_after = after_avg.mean()
    improvement = (overall_before - overall_after) / overall_before * 100
    
    bars = ax2.bar(['Baseline', 'RL (DQN)'], [overall_before, overall_after],
                   color=['#e74c3c', '#2ecc71'], alpha=0.8, width=0.5)
    
    ax2.set_ylabel('Average Waiting Time (s)')
    ax2.set_title(f'Overall Comparison\n(Improvement: {improvement:.1f}%)')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}s',
                ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(config.WAITING_TIME_PLOT, dpi=300, bbox_inches='tight')
    logger.success(f"Saved: {config.WAITING_TIME_PLOT}")
    plt.close()


def plot_queue_length_comparison():
    """Plot queue length comparison (if data available)"""
    logger = Logger()
    
    # For now, we'll create a simple plot based on waiting time data
    # In a full implementation, we'd track queue lengths separately
    
    logger.info("Queue length plot would be generated here (using waiting time as proxy)")


def generate_summary_report():
    """Generate a text summary report"""
    logger = Logger()
    
    print_header("Summary Report")
    
    # Load training data
    if os.path.exists(config.TRAINING_REWARDS_CSV):
        df_train = pd.read_csv(config.TRAINING_REWARDS_CSV)
        logger.info(f"Training episodes: {len(df_train)}")
        logger.info(f"Final reward: {df_train['total_reward'].iloc[-1]:.2f}")
        logger.info(f"Best reward: {df_train['total_reward'].max():.2f}")
    
    # Load evaluation data
    if os.path.exists(config.WAITING_TIME_BEFORE_CSV) and os.path.exists(config.WAITING_TIME_AFTER_CSV):
        df_before = pd.read_csv(config.WAITING_TIME_BEFORE_CSV)
        df_after = pd.read_csv(config.WAITING_TIME_AFTER_CSV)
        
        before_avg = df_before['avg_waiting_time'].mean()
        after_avg = df_after['avg_waiting_time'].mean()
        improvement = (before_avg - after_avg) / before_avg * 100
        
        print()
        logger.info(f"Baseline avg waiting time: {before_avg:.2f}s")
        logger.info(f"RL avg waiting time: {after_avg:.2f}s")
        logger.success(f"Improvement: {improvement:.2f}%")
    
    print()
    logger.info(f"Plots saved to: {config.PLOTS_DIR}")
    logger.info(f"Models saved to: {config.MODELS_DIR}")
    logger.info(f"Metrics saved to: {config.METRICS_DIR}")


def visualize_all():
    """Generate all visualizations"""
    logger = Logger()
    
    print_header("Generating Visualizations")
    
    # Create plots directory
    os.makedirs(config.PLOTS_DIR, exist_ok=True)
    
    # Generate plots
    plot_training_rewards()
    plot_waiting_time_comparison()
    plot_queue_length_comparison()
    
    # Generate summary
    generate_summary_report()
    
    print_header("Visualization Complete")


if __name__ == "__main__":
    visualize_all()
