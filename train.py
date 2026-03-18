"""
Training Script for DQN Traffic Signal Optimization
Trains independent DQN agents for each traffic light junction
"""

import os
import time
import argparse
from tqdm import tqdm

import config
from utils.logger import Logger, CSVLogger, print_header
from utils.sumo_checker import check_sumo_installation
from sumo.sumo_env import SUMOEnvironment
from rl.dqn_agent import DQNAgent


def train(
    max_episodes=None,
    max_training_time=None,
    max_steps_per_episode=3600,
    log_interval=10,
    checkpoint_interval=50
):
    """
    Train DQN agents for traffic signal control
    
    Args:
        max_episodes: Maximum number of episodes (None = use config)
        max_training_time: Maximum training time in seconds (None = use config)
        max_steps_per_episode: Maximum steps per episode
        log_interval: Log metrics every N episodes
        checkpoint_interval: Save models every N episodes
    """
    logger = Logger(verbose=config.VERBOSE)
    
    print_header("DQN Traffic Signal Optimization - Training")
    
    # Use config defaults if not specified
    if max_episodes is None:
        max_episodes = config.MAX_EPISODES
    if max_training_time is None:
        max_training_time = config.TARGET_TRAINING_TIME
    
    # Check SUMO installation
    logger.info("Checking SUMO installation...")
    success, message = check_sumo_installation()
    if not success:
        logger.error(message)
        return
    
    # Create directories
    config.create_directories()
    
    # Initialize CSV loggers
    training_logger = CSVLogger(
        config.TRAINING_REWARDS_CSV,
        ['episode', 'total_reward', 'avg_reward_per_junction', 'epsilon', 'duration']
    )
    
    episode_logger = CSVLogger(
        config.EPISODE_STATS_CSV,
        ['episode', 'step', 'total_waiting_time', 'total_queue_length', 'avg_loss']
    )
    
    # Initialize SUMO environment
    logger.info("Initializing SUMO environment...")
    env = SUMOEnvironment(
        network_file=config.NETWORK_FILE,
        route_file=config.ROUTE_FILE,
        use_gui=config.SUMO_GUI,
        step_length=config.SUMO_STEP_LENGTH,
        min_green_time=config.MIN_GREEN_TIME,
        yellow_time=config.YELLOW_TIME,
        seed=config.SUMO_SEED
    )
    
    logger.success(f"Environment initialized with {len(env.tl_junctions)} junctions")
    
    # Initialize DQN agents for each junction
    logger.info("Initializing DQN agents...")
    agents = {}
    
    for junction_id in env.tl_junctions:
        state_size = env.get_state_size(junction_id)
        
        agent = DQNAgent(
            state_size=state_size,
            action_size=config.ACTION_SIZE,
            hidden_size_1=config.HIDDEN_SIZE_1,
            hidden_size_2=config.HIDDEN_SIZE_2,
            learning_rate=config.LEARNING_RATE,
            gamma=config.GAMMA,
            epsilon_start=config.EPSILON_START,
            epsilon_end=config.EPSILON_END,
            epsilon_decay=config.EPSILON_DECAY,
            buffer_size=config.REPLAY_BUFFER_SIZE,
            batch_size=config.BATCH_SIZE,
            target_update_freq=config.TARGET_UPDATE_FREQUENCY,
            device=config.DEVICE
        )
        
        agents[junction_id] = agent
        logger.info(f"  {junction_id}: state_size={state_size}")
    
    logger.success(f"Initialized {len(agents)} DQN agents")
    logger.info(f"Device: {config.DEVICE}")
    
    # Training loop
    print_header("Starting Training")
    logger.info(f"Max episodes: {max_episodes}")
    logger.info(f"Max training time: {max_training_time}s (~{max_training_time/3600:.1f}h)")
    logger.info(f"Max steps per episode: {max_steps_per_episode}")
    
    training_start_time = time.time()
    
    try:
        for episode in range(1, max_episodes + 1):
            episode_start_time = time.time()
            
            # Reset environment
            states = env.reset()
            
            episode_rewards = {jid: 0 for jid in env.tl_junctions}
            episode_losses = []
            
            # Episode loop
            for step in range(max_steps_per_episode):
                # Select actions for all junctions
                actions = {}
                for junction_id in env.tl_junctions:
                    state = states[junction_id]
                    action = agents[junction_id].select_action(state)
                    actions[junction_id] = action
                
                # Execute actions
                next_states, rewards, done, info = env.step(actions)
                
                # Store transitions and train
                for junction_id in env.tl_junctions:
                    state = states[junction_id]
                    action = actions[junction_id]
                    reward = rewards[junction_id]
                    next_state = next_states[junction_id]
                    
                    # Store transition
                    agents[junction_id].store_transition(state, action, reward, next_state, done)
                    
                    # Train
                    loss = agents[junction_id].train()
                    if loss is not None:
                        episode_losses.append(loss)
                    
                    # Accumulate reward
                    episode_rewards[junction_id] += reward
                
                # Update states
                states = next_states
                
                # Log episode stats periodically
                if step % 100 == 0:
                    total_waiting = sum([info.get(f'{jid}_waiting_time', 0) for jid in env.tl_junctions])
                    total_queue = sum([info.get(f'{jid}_queue_length', 0) for jid in env.tl_junctions])
                    avg_loss = sum(episode_losses[-100:]) / len(episode_losses[-100:]) if episode_losses else 0
                    
                    episode_logger.log({
                        'episode': episode,
                        'step': step,
                        'total_waiting_time': total_waiting,
                        'total_queue_length': total_queue,
                        'avg_loss': avg_loss
                    })
                
                # Check if done
                if done:
                    break
            
            # Decay epsilon for all agents
            for agent in agents.values():
                agent.decay_epsilon()
            
            # Calculate episode metrics
            total_reward = sum(episode_rewards.values())
            avg_reward = total_reward / len(env.tl_junctions)
            episode_duration = time.time() - episode_start_time
            epsilon = agents[env.tl_junctions[0]].epsilon
            
            # Log training metrics
            training_logger.log({
                'episode': episode,
                'total_reward': total_reward,
                'avg_reward_per_junction': avg_reward,
                'epsilon': epsilon,
                'duration': episode_duration
            })
            
            # Print progress
            if episode % log_interval == 0:
                elapsed_time = time.time() - training_start_time
                logger.info(
                    f"Episode {episode}/{max_episodes} | "
                    f"Reward: {total_reward:.1f} | "
                    f"Avg: {avg_reward:.1f} | "
                    f"eps: {epsilon:.3f} | "
                    f"Steps: {step+1} | "
                    f"Time: {logger.format_time(elapsed_time)}"
                )
            
            # Save checkpoints
            if episode % checkpoint_interval == 0:
                logger.info(f"Saving checkpoint at episode {episode}...")
                for junction_id, agent in agents.items():
                    model_path = os.path.join(config.MODELS_DIR, f"junction_{junction_id}_ep{episode}.pt")
                    agent.save(model_path)
                logger.success("Checkpoint saved")
            
            # Check training time limit
            elapsed_time = time.time() - training_start_time
            if elapsed_time >= max_training_time:
                logger.info(f"Reached training time limit ({logger.format_time(elapsed_time)})")
                break
    
    except KeyboardInterrupt:
        logger.warning("Training interrupted by user")
    
    finally:
        # Save final models
        logger.info("Saving final models...")
        for junction_id, agent in agents.items():
            model_path = os.path.join(config.MODELS_DIR, f"junction_{junction_id}_dqn.pt")
            agent.save(model_path)
        logger.success("Final models saved")
        
        # Close environment
        env.close()
        
        # Print summary
        total_time = time.time() - training_start_time
        print_header("Training Complete")
        logger.success(f"Total training time: {logger.format_time(total_time)}")
        logger.success(f"Total episodes: {episode}")
        logger.success(f"Models saved to: {config.MODELS_DIR}")
        logger.success(f"Metrics saved to: {config.METRICS_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train DQN agents for traffic signal control")
    parser.add_argument('--episodes', type=int, default=None, help='Maximum number of episodes')
    parser.add_argument('--time', type=int, default=None, help='Maximum training time (seconds)')
    parser.add_argument('--steps', type=int, default=3600, help='Maximum steps per episode')
    
    args = parser.parse_args()
    
    train(
        max_episodes=args.episodes,
        max_training_time=args.time,
        max_steps_per_episode=args.steps
    )
