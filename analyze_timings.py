"""
Signal Timing Analyzer
Extracts and analyzes optimized signal timings from trained DQN agents
"""

import os
import numpy as np
import pandas as pd
from collections import defaultdict

import config
from utils.logger import Logger, CSVLogger, print_header
from utils.sumo_checker import check_sumo_installation, setup_sumo_environment
from sumo.sumo_env import SUMOEnvironment
from rl.dqn_agent import DQNAgent

# Setup SUMO
setup_sumo_environment()
import traci


def analyze_signal_timings(num_episodes=5, max_steps=3600, mode='rl'):
    """
    Analyze signal timings for baseline or RL mode
    
    Args:
        num_episodes: Number of episodes to analyze
        max_steps: Maximum steps per episode
        mode: 'baseline' or 'rl'
    
    Returns:
        dict: Signal timing statistics
    """
    logger = Logger(verbose=True)
    
    print_header(f"Signal Timing Analysis - {mode.upper()} Mode")
    
    # Initialize environment
    env = SUMOEnvironment(
        network_file=config.NETWORK_FILE,
        route_file=config.ROUTE_FILE,
        use_gui=False,
        step_length=config.SUMO_STEP_LENGTH,
        min_green_time=config.MIN_GREEN_TIME,
        yellow_time=config.YELLOW_TIME,
        seed=config.SUMO_SEED
    )
    
    # Load agents if RL mode
    agents = {}
    if mode == 'rl':
        logger.info("Loading trained DQN agents...")
        for junction_id in env.tl_junctions:
            state_size = env.get_state_size(junction_id)
            agent = DQNAgent(state_size=state_size, action_size=config.ACTION_SIZE, device=config.DEVICE)
            
            model_path = os.path.join(config.MODELS_DIR, f"junction_{junction_id}_dqn.pt")
            if not os.path.exists(model_path):
                logger.error(f"Model not found: {model_path}")
                return None
            
            agent.load(model_path)
            agents[junction_id] = agent
        logger.success(f"Loaded {len(agents)} DQN agents")
    
    # Track signal timings
    phase_durations = {jid: defaultdict(list) for jid in env.tl_junctions}
    phase_switches = {jid: 0 for jid in env.tl_junctions}
    current_phases = {jid: None for jid in env.tl_junctions}
    phase_start_times = {jid: 0 for jid in env.tl_junctions}
    
    # Track actions (for RL mode)
    action_counts = {jid: {0: 0, 1: 0} for jid in env.tl_junctions}
    
    try:
        for episode in range(1, num_episodes + 1):
            logger.info(f"Episode {episode}/{num_episodes}")
            
            # Reset environment
            if mode == 'rl':
                states = env.reset()
            else:
                env.reset()
            
            # Reset phase tracking for this episode
            for junction_id in env.tl_junctions:
                try:
                    current_phases[junction_id] = traci.trafficlight.getPhase(junction_id)
                    phase_start_times[junction_id] = 0
                except:
                    pass
            
            # Run episode
            for step in range(max_steps):
                if mode == 'rl':
                    # RL mode: use trained agents
                    actions = {}
                    for junction_id in env.tl_junctions:
                        state = states[junction_id]
                        action = agents[junction_id].select_action(state, epsilon=0.0)  # No exploration
                        actions[junction_id] = action
                        action_counts[junction_id][action] += 1
                    
                    next_states, _, done, _ = env.step(actions)
                    states = next_states
                else:
                    # Baseline mode: let SUMO control
                    actions = {jid: 0 for jid in env.tl_junctions}
                    _, _, done, _ = env.step(actions)
                
                # Track phase changes
                for junction_id in env.tl_junctions:
                    try:
                        current_phase = traci.trafficlight.getPhase(junction_id)
                        
                        # Check if phase changed
                        if current_phase != current_phases[junction_id]:
                            # Record duration of previous phase
                            duration = step - phase_start_times[junction_id]
                            if duration > 0:
                                phase_durations[junction_id][current_phases[junction_id]].append(duration)
                            
                            # Update tracking
                            current_phases[junction_id] = current_phase
                            phase_start_times[junction_id] = step
                            phase_switches[junction_id] += 1
                    except:
                        pass
                
                if done:
                    break
            
            # Record final phase durations
            for junction_id in env.tl_junctions:
                try:
                    duration = step - phase_start_times[junction_id]
                    if duration > 0:
                        phase_durations[junction_id][current_phases[junction_id]].append(duration)
                except:
                    pass
    
    finally:
        env.close()
    
    # Calculate statistics
    results = {
        'junctions': {},
        'summary': {}
    }
    
    for junction_id in env.tl_junctions:
        junction_stats = {
            'phase_timings': {},
            'total_switches': phase_switches[junction_id],
            'avg_switches_per_episode': phase_switches[junction_id] / num_episodes
        }
        
        # Calculate average duration per phase
        for phase_id, durations in phase_durations[junction_id].items():
            if durations:
                junction_stats['phase_timings'][phase_id] = {
                    'avg_duration': np.mean(durations),
                    'min_duration': np.min(durations),
                    'max_duration': np.max(durations),
                    'std_duration': np.std(durations),
                    'count': len(durations)
                }
        
        # Add action statistics for RL mode
        if mode == 'rl':
            total_actions = sum(action_counts[junction_id].values())
            junction_stats['actions'] = {
                'keep_phase': action_counts[junction_id][0],
                'switch_phase': action_counts[junction_id][1],
                'keep_percentage': action_counts[junction_id][0] / total_actions * 100 if total_actions > 0 else 0,
                'switch_percentage': action_counts[junction_id][1] / total_actions * 100 if total_actions > 0 else 0
            }
        
        results['junctions'][junction_id] = junction_stats
    
    # Overall summary
    total_switches = sum(phase_switches.values())
    results['summary'] = {
        'total_junctions': len(env.tl_junctions),
        'total_phase_switches': total_switches,
        'avg_switches_per_junction': total_switches / len(env.tl_junctions) if env.tl_junctions else 0,
        'avg_switches_per_episode': total_switches / num_episodes if num_episodes > 0 else 0
    }
    
    return results


def print_timing_analysis(results, mode='rl'):
    """Print signal timing analysis in readable format"""
    logger = Logger()
    
    print_header(f"{mode.upper()} Signal Timing Analysis")
    
    # Summary
    logger.info(f"Total Junctions: {results['summary']['total_junctions']}")
    logger.info(f"Total Phase Switches: {results['summary']['total_phase_switches']}")
    logger.info(f"Avg Switches per Junction: {results['summary']['avg_switches_per_junction']:.1f}")
    logger.info(f"Avg Switches per Episode: {results['summary']['avg_switches_per_episode']:.1f}")
    print()
    
    # Per-junction details
    for junction_id, stats in results['junctions'].items():
        print("=" * 70)
        logger.info(f"Junction: {junction_id}")
        print("=" * 70)
        
        logger.info(f"Total Phase Switches: {stats['total_switches']}")
        logger.info(f"Avg Switches per Episode: {stats['avg_switches_per_episode']:.1f}")
        print()
        
        # Phase timings
        if stats['phase_timings']:
            logger.info("Phase Timings (seconds):")
            print()
            print(f"{'Phase ID':<10} {'Avg':<10} {'Min':<10} {'Max':<10} {'Std':<10} {'Count':<10}")
            print("-" * 70)
            
            for phase_id, timing in sorted(stats['phase_timings'].items()):
                print(f"{phase_id:<10} {timing['avg_duration']:<10.1f} {timing['min_duration']:<10.1f} "
                      f"{timing['max_duration']:<10.1f} {timing['std_duration']:<10.1f} {timing['count']:<10}")
        
        # Action statistics (RL only)
        if 'actions' in stats:
            print()
            logger.info("Agent Actions:")
            logger.info(f"  Keep Phase: {stats['actions']['keep_phase']} ({stats['actions']['keep_percentage']:.1f}%)")
            logger.info(f"  Switch Phase: {stats['actions']['switch_phase']} ({stats['actions']['switch_percentage']:.1f}%)")
        
        print()


def save_timing_comparison(baseline_results, rl_results, output_file):
    """Save timing comparison to CSV"""
    logger = Logger()
    
    rows = []
    
    for junction_id in baseline_results['junctions'].keys():
        baseline_stats = baseline_results['junctions'][junction_id]
        rl_stats = rl_results['junctions'][junction_id]
        
        # Get all phase IDs
        all_phases = set(baseline_stats['phase_timings'].keys()) | set(rl_stats['phase_timings'].keys())
        
        for phase_id in sorted(all_phases):
            baseline_timing = baseline_stats['phase_timings'].get(phase_id, {})
            rl_timing = rl_stats['phase_timings'].get(phase_id, {})
            
            row = {
                'junction_id': junction_id,
                'phase_id': phase_id,
                'baseline_avg_duration': baseline_timing.get('avg_duration', 0),
                'rl_avg_duration': rl_timing.get('avg_duration', 0),
                'difference': rl_timing.get('avg_duration', 0) - baseline_timing.get('avg_duration', 0),
                'baseline_count': baseline_timing.get('count', 0),
                'rl_count': rl_timing.get('count', 0)
            }
            rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)
    logger.success(f"Saved timing comparison to: {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze signal timings")
    parser.add_argument('--mode', type=str, choices=['baseline', 'rl', 'both'], default='both',
                        help='Analysis mode')
    parser.add_argument('--episodes', type=int, default=5, help='Number of episodes to analyze')
    
    args = parser.parse_args()
    
    # Check SUMO
    logger = Logger()
    success, message = check_sumo_installation()
    if not success:
        logger.error(message)
        exit(1)
    
    baseline_results = None
    rl_results = None
    
    # Analyze baseline
    if args.mode in ['baseline', 'both']:
        baseline_results = analyze_signal_timings(args.episodes, mode='baseline')
        if baseline_results:
            print_timing_analysis(baseline_results, mode='baseline')
    
    # Analyze RL
    if args.mode in ['rl', 'both']:
        rl_results = analyze_signal_timings(args.episodes, mode='rl')
        if rl_results:
            print_timing_analysis(rl_results, mode='rl')
    
    # Save comparison
    if baseline_results and rl_results:
        output_file = os.path.join(config.METRICS_DIR, 'signal_timing_comparison.csv')
        save_timing_comparison(baseline_results, rl_results, output_file)
        
        print_header("Comparison Summary")
        logger.info(f"Baseline switches per episode: {baseline_results['summary']['avg_switches_per_episode']:.1f}")
        logger.info(f"RL switches per episode: {rl_results['summary']['avg_switches_per_episode']:.1f}")
        
        switch_diff = rl_results['summary']['avg_switches_per_episode'] - baseline_results['summary']['avg_switches_per_episode']
        logger.info(f"Difference: {switch_diff:+.1f} switches per episode")
