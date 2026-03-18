"""
Evaluation Script for Traffic Signal Optimization
Evaluates baseline (fixed-time) and RL-controlled signals
"""

import os
import argparse
import numpy as np
import traci

import config
from utils.logger import Logger, CSVLogger, print_header
from utils.sumo_checker import check_sumo_installation
from sumo.sumo_env import SUMOEnvironment
from rl.dqn_agent import DQNAgent


def evaluate_baseline(num_episodes=5, max_steps=3600, use_gui=False):
    """
    Evaluate baseline fixed-time traffic signals
    
    Args:
        num_episodes: Number of evaluation episodes
        max_steps: Maximum steps per episode
    
    Returns:
        dict: Evaluation metrics
    """
    logger = Logger(verbose=config.VERBOSE)
    
    print_header("Baseline Evaluation (Fixed-Time Signals)")
    
    # Initialize environment
    env = SUMOEnvironment(
        network_file=config.NETWORK_FILE,
        route_file=config.ROUTE_FILE,
        use_gui=use_gui,
        step_length=config.SUMO_STEP_LENGTH,
        min_green_time=config.MIN_GREEN_TIME,
        yellow_time=config.YELLOW_TIME,
        seed=config.SUMO_SEED
    )
    
    # CSV loggers
    waiting_time_logger = CSVLogger(
        config.WAITING_TIME_BEFORE_CSV,
        ['episode', 'junction_id', 'avg_waiting_time', 'total_waiting_time']
    )
    
    signal_timing_logger = CSVLogger(
        config.SIGNAL_TIMINGS_BEFORE_CSV,
        ['episode', 'junction_id', 'phase_id', 'duration']
    )
    
    # Metrics storage
    all_waiting_times = {jid: [] for jid in env.tl_junctions}
    all_queue_lengths = {jid: [] for jid in env.tl_junctions}
    
    try:
        for episode in range(1, num_episodes + 1):
            logger.info(f"Baseline Episode {episode}/{num_episodes}")
            
            # Reset environment
            env.reset()
            
            episode_waiting_times = {jid: [] for jid in env.tl_junctions}
            episode_queue_lengths = {jid: [] for jid in env.tl_junctions}
            
            # Run simulation with default signals (no RL control)
            for step in range(max_steps):
                # No actions - let SUMO use default signal timings
                actions = {jid: 0 for jid in env.tl_junctions}  # Keep current phase
                
                _, _, done, info = env.step(actions)
                
                # Collect metrics
                for junction_id in env.tl_junctions:
                    waiting_time = info.get(f'{junction_id}_waiting_time', 0)
                    queue_length = info.get(f'{junction_id}_queue_length', 0)
                    
                    episode_waiting_times[junction_id].append(waiting_time)
                    episode_queue_lengths[junction_id].append(queue_length)
                
                if done:
                    break
            
            # Log episode metrics
            for junction_id in env.tl_junctions:
                avg_waiting = np.mean(episode_waiting_times[junction_id])
                total_waiting = np.sum(episode_waiting_times[junction_id])
                
                waiting_time_logger.log({
                    'episode': episode,
                    'junction_id': junction_id,
                    'avg_waiting_time': avg_waiting,
                    'total_waiting_time': total_waiting
                })
                
                all_waiting_times[junction_id].append(avg_waiting)
                all_queue_lengths[junction_id].append(np.mean(episode_queue_lengths[junction_id]))
            
            logger.info(f"  Completed {step+1} steps")
    
    finally:
        env.close()
    
    # Calculate summary statistics
    results = {
        'avg_waiting_time': np.mean([np.mean(wt) for wt in all_waiting_times.values()]),
        'avg_queue_length': np.mean([np.mean(ql) for ql in all_queue_lengths.values()]),
        'per_junction': {}
    }
    
    for junction_id in env.tl_junctions:
        results['per_junction'][junction_id] = {
            'avg_waiting_time': np.mean(all_waiting_times[junction_id]),
            'avg_queue_length': np.mean(all_queue_lengths[junction_id])
        }
    
    # Print summary
    print_header("Baseline Results")
    logger.info(f"Average waiting time: {results['avg_waiting_time']:.2f}s")
    logger.info(f"Average queue length: {results['avg_queue_length']:.2f} vehicles")
    
    return results


def evaluate_rl(num_episodes=5, max_steps=3600, use_gui=False):
    """
    Evaluate RL-trained traffic signals
    
    Args:
        num_episodes: Number of evaluation episodes
        max_steps: Maximum steps per episode
    
    Returns:
        dict: Evaluation metrics
    """
    logger = Logger(verbose=config.VERBOSE)
    
    print_header("RL Evaluation (DQN-Controlled Signals)")
    
    # Initialize environment
    env = SUMOEnvironment(
        network_file=config.NETWORK_FILE,
        route_file=config.ROUTE_FILE,
        use_gui=use_gui,
        step_length=config.SUMO_STEP_LENGTH,
        min_green_time=config.MIN_GREEN_TIME,
        yellow_time=config.YELLOW_TIME,
        seed=config.SUMO_SEED
    )
    
    # Load trained agents
    logger.info("Loading trained DQN agents...")
    agents = {}
    
    for junction_id in env.tl_junctions:
        state_size = env.get_state_size(junction_id)
        
        agent = DQNAgent(
            state_size=state_size,
            action_size=config.ACTION_SIZE,
            device=config.DEVICE
        )
        
        # Load model
        model_path = os.path.join(config.MODELS_DIR, f"junction_{junction_id}_dqn.pt")
        
        if not os.path.exists(model_path):
            logger.error(f"Model not found: {model_path}")
            logger.error("Please train the models first using train.py")
            return None
        
        agent.load(model_path)
        agents[junction_id] = agent
        logger.info(f"  Loaded model for {junction_id}")
    
    logger.success(f"Loaded {len(agents)} DQN agents")
    
    # CSV loggers
    waiting_time_logger = CSVLogger(
        config.WAITING_TIME_AFTER_CSV,
        ['episode', 'junction_id', 'avg_waiting_time', 'total_waiting_time']
    )
    
    signal_timing_logger = CSVLogger(
        config.SIGNAL_TIMINGS_AFTER_CSV,
        ['episode', 'junction_id', 'phase_id', 'duration']
    )
    
    # Metrics storage
    all_waiting_times = {jid: [] for jid in env.tl_junctions}
    all_queue_lengths = {jid: [] for jid in env.tl_junctions}
    
    try:
        for episode in range(1, num_episodes + 1):
            logger.info(f"RL Episode {episode}/{num_episodes}")
            
            # Reset environment
            states = env.reset()
            
            episode_waiting_times = {jid: [] for jid in env.tl_junctions}
            episode_queue_lengths = {jid: [] for jid in env.tl_junctions}
            
            # Track phases for timing logs
            current_phases = {}
            phase_start_times = {}
            for jid in env.tl_junctions:
                try:
                    current_phases[jid] = traci.trafficlight.getPhase(jid)
                    phase_start_times[jid] = 0
                except:
                    pass

            
            # Run simulation with RL control
            for step in range(max_steps):
                # Select actions using trained agents (no exploration)
                actions = {}
                for junction_id in env.tl_junctions:
                    state = states[junction_id]
                    action = agents[junction_id].select_action(state, epsilon=config.EVAL_EPSILON)
                    actions[junction_id] = action
                
                next_states, _, done, info = env.step(actions)
                
                # Collect metrics
                for junction_id in env.tl_junctions:
                    waiting_time = info.get(f'{junction_id}_waiting_time', 0)
                    queue_length = info.get(f'{junction_id}_queue_length', 0)
                    
                    episode_waiting_times[junction_id].append(waiting_time)
                    episode_queue_lengths[junction_id].append(queue_length)
                
                # Log signal timings
                for junction_id in env.tl_junctions:
                    try:
                        current_phase = traci.trafficlight.getPhase(junction_id)
                        if current_phase != current_phases.get(junction_id, -1):
                            # Phase changed, log previous phase duration
                            prev_phase = current_phases.get(junction_id, -1)
                            # Only log if it's not the initial state (prev_phase != -1)
                            if prev_phase != -1:
                                duration = step - phase_start_times[junction_id]
                                if duration > 0:
                                    signal_timing_logger.log({
                                        'episode': episode,
                                        'junction_id': junction_id,
                                        'phase_id': prev_phase,
                                        'duration': duration
                                    })
                            
                            current_phases[junction_id] = current_phase
                            phase_start_times[junction_id] = step
                    except:
                        pass

                states = next_states

                
                if done:
                    break
            
            # Log final phase duration
            for junction_id in env.tl_junctions:
                try:
                    duration = step - phase_start_times[junction_id]
                    if duration > 0:
                        signal_timing_logger.log({
                            'episode': episode,
                            'junction_id': junction_id,
                            'phase_id': current_phases[junction_id],
                            'duration': duration
                        })
                except:
                    pass

            # Log episode metrics
            for junction_id in env.tl_junctions:
                avg_waiting = np.mean(episode_waiting_times[junction_id])
                total_waiting = np.sum(episode_waiting_times[junction_id])
                
                waiting_time_logger.log({
                    'episode': episode,
                    'junction_id': junction_id,
                    'avg_waiting_time': avg_waiting,
                    'total_waiting_time': total_waiting
                })
                
                all_waiting_times[junction_id].append(avg_waiting)
                all_queue_lengths[junction_id].append(np.mean(episode_queue_lengths[junction_id]))
            
            logger.info(f"  Completed {step+1} steps")
    
    finally:
        env.close()
    
    # Calculate summary statistics
    results = {
        'avg_waiting_time': np.mean([np.mean(wt) for wt in all_waiting_times.values()]),
        'avg_queue_length': np.mean([np.mean(ql) for ql in all_queue_lengths.values()]),
        'per_junction': {}
    }
    
    for junction_id in env.tl_junctions:
        results['per_junction'][junction_id] = {
            'avg_waiting_time': np.mean(all_waiting_times[junction_id]),
            'avg_queue_length': np.mean(all_queue_lengths[junction_id])
        }
    
    # Print summary
    print_header("RL Results")
    logger.info(f"Average waiting time: {results['avg_waiting_time']:.2f}s")
    logger.info(f"Average queue length: {results['avg_queue_length']:.2f} vehicles")
    
    return results


def compare_results(baseline_results, rl_results):
    """
    Compare baseline and RL results
    
    Args:
        baseline_results: Baseline evaluation results
        rl_results: RL evaluation results
    """
    logger = Logger()
    
    print_header("Comparison: Baseline vs RL")
    
    # Calculate improvements
    waiting_time_improvement = (
        (baseline_results['avg_waiting_time'] - rl_results['avg_waiting_time']) /
        baseline_results['avg_waiting_time'] * 100
    )
    
    queue_length_improvement = (
        (baseline_results['avg_queue_length'] - rl_results['avg_queue_length']) /
        baseline_results['avg_queue_length'] * 100
    )
    
    logger.info(f"Baseline avg waiting time: {baseline_results['avg_waiting_time']:.2f}s")
    logger.info(f"RL avg waiting time:       {rl_results['avg_waiting_time']:.2f}s")
    logger.success(f"Improvement:               {waiting_time_improvement:+.2f}%")
    
    print()
    
    logger.info(f"Baseline avg queue length: {baseline_results['avg_queue_length']:.2f} vehicles")
    logger.info(f"RL avg queue length:       {rl_results['avg_queue_length']:.2f} vehicles")
    logger.success(f"Improvement:               {queue_length_improvement:+.2f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate traffic signal control")
    parser.add_argument('--mode', type=str, choices=['baseline', 'rl', 'both'], default='both',
                        help='Evaluation mode')
    parser.add_argument('--episodes', type=int, default=5, help='Number of evaluation episodes')
    parser.add_argument('--steps', type=int, default=3600, help='Maximum steps per episode')
    parser.add_argument('--gui', action='store_true', help='Use SUMO GUI')
    
    args = parser.parse_args()
    
    # Check SUMO installation
    logger = Logger()
    success, message = check_sumo_installation()
    if not success:
        logger.error(message)
        exit(1)
    
    # Create directories
    config.create_directories()
    
    # Run evaluations
    baseline_results = None
    rl_results = None
    
    if args.mode in ['baseline', 'both']:
        baseline_results = evaluate_baseline(args.episodes, args.steps, args.gui)
    
    if args.mode in ['rl', 'both']:
        rl_results = evaluate_rl(args.episodes, args.steps, args.gui)
    
    # Compare results
    if baseline_results and rl_results:
        compare_results(baseline_results, rl_results)
