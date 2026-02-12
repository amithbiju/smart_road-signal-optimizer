"""
Main Pipeline Orchestrator
Runs the complete traffic signal optimization pipeline end-to-end
"""

import os
import sys
import argparse

import config
from utils.logger import Logger, print_header
from utils.sumo_checker import check_sumo_installation
from osm.osm_downloader import download_osm, validate_osm_file
from osm.network_generator import generate_network, extract_traffic_light_junctions
from osm.traffic_generator import generate_traffic
from train import train
from evaluate import evaluate_baseline, evaluate_rl, compare_results
from visualize import visualize_all


def run_pipeline(
    skip_download=False,
    skip_network=False,
    skip_traffic=False,
    skip_baseline=False,
    skip_training=False,
    skip_evaluation=False,
    skip_visualization=False,
    training_episodes=None,
    training_time=None
):
    """
    Run the complete pipeline
    
    Args:
        skip_download: Skip OSM download
        skip_network: Skip network generation
        skip_traffic: Skip traffic generation
        skip_baseline: Skip baseline evaluation
        skip_training: Skip DQN training
        skip_evaluation: Skip RL evaluation
        skip_visualization: Skip visualization
        training_episodes: Number of training episodes
        training_time: Training time in seconds
    """
    logger = Logger(verbose=True)
    
    print_header("Traffic Signal Optimization Pipeline")
    logger.info("Academic-grade DQN-based traffic signal control system")
    logger.info(f"Bounding Box: {config.BOUNDING_BOX}")
    print()
    
    # ========================================================================
    # Step 1: Check SUMO Installation
    # ========================================================================
    print_header("Step 1: SUMO Installation Check")
    success, message = check_sumo_installation()
    if not success:
        logger.error(message)
        return False
    print()
    
    # ========================================================================
    # Step 2: Create Directories
    # ========================================================================
    print_header("Step 2: Setup")
    config.create_directories()
    logger.success("Project directories created")
    print()
    
    # ========================================================================
    # Step 3: Download OSM Data
    # ========================================================================
    if not skip_download:
        print_header("Step 3: Download OSM Data")
        
        if os.path.exists(config.OSM_FILE):
            logger.info(f"OSM file already exists: {config.OSM_FILE}")
            if validate_osm_file(config.OSM_FILE):
                logger.info("Using existing OSM file")
            else:
                logger.warning("Existing file is invalid, re-downloading...")
                success = download_osm(config.BOUNDING_BOX, config.OSM_FILE)
                if not success:
                    logger.error("Failed to download OSM data")
                    return False
        else:
            success = download_osm(config.BOUNDING_BOX, config.OSM_FILE)
            if not success:
                logger.error("Failed to download OSM data")
                return False
        
        print()
    else:
        logger.info("Skipping OSM download")
    
    # ========================================================================
    # Step 4: Generate SUMO Network
    # ========================================================================
    if not skip_network:
        print_header("Step 4: Generate SUMO Network")
        
        if os.path.exists(config.NETWORK_FILE):
            logger.info(f"Network file already exists: {config.NETWORK_FILE}")
            logger.info("Using existing network file")
        else:
            success = generate_network(config.OSM_FILE, config.NETWORK_FILE)
            if not success:
                logger.error("Failed to generate SUMO network")
                return False
        
        # Extract junctions
        junctions = extract_traffic_light_junctions(config.NETWORK_FILE)
        
        if len(junctions) == 0:
            logger.error("No traffic light junctions found!")
            logger.error("Try using a larger bounding box or different area")
            return False
        
        print()
    else:
        logger.info("Skipping network generation")
    
    # ========================================================================
    # Step 5: Generate Traffic
    # ========================================================================
    if not skip_traffic:
        print_header("Step 5: Generate Traffic")
        
        if os.path.exists(config.ROUTE_FILE):
            logger.info(f"Route file already exists: {config.ROUTE_FILE}")
            logger.info("Using existing route file")
        else:
            success = generate_traffic(
                config.NETWORK_FILE,
                config.TRIPS_FILE,
                config.ROUTE_FILE,
                period=config.TRAFFIC_PERIOD,
                probability=config.TRAFFIC_PROBABILITY
            )
            if not success:
                logger.error("Failed to generate traffic")
                return False
        
        print()
    else:
        logger.info("Skipping traffic generation")
    
    # ========================================================================
    # Step 6: Baseline Evaluation
    # ========================================================================
    baseline_results = None
    
    if not skip_baseline:
        print_header("Step 6: Baseline Evaluation")
        baseline_results = evaluate_baseline(
            num_episodes=config.EVAL_EPISODES,
            max_steps=config.MAX_STEPS_PER_EPISODE
        )
        print()
    else:
        logger.info("Skipping baseline evaluation")
    
    # ========================================================================
    # Step 7: DQN Training
    # ========================================================================
    if not skip_training:
        print_header("Step 7: DQN Training")
        train(
            max_episodes=training_episodes,
            max_training_time=training_time,
            max_steps_per_episode=config.MAX_STEPS_PER_EPISODE
        )
        print()
    else:
        logger.info("Skipping DQN training")
    
    # ========================================================================
    # Step 8: RL Evaluation
    # ========================================================================
    rl_results = None
    
    if not skip_evaluation:
        print_header("Step 8: RL Evaluation")
        rl_results = evaluate_rl(
            num_episodes=config.EVAL_EPISODES,
            max_steps=config.MAX_STEPS_PER_EPISODE
        )
        print()
    else:
        logger.info("Skipping RL evaluation")
    
    # ========================================================================
    # Step 9: Compare Results
    # ========================================================================
    if baseline_results and rl_results:
        compare_results(baseline_results, rl_results)
        print()
    
    # ========================================================================
    # Step 10: Visualization
    # ========================================================================
    if not skip_visualization:
        print_header("Step 10: Visualization")
        visualize_all()
        print()
    else:
        logger.info("Skipping visualization")
    
    # ========================================================================
    # Final Summary
    # ========================================================================
    print_header("Pipeline Complete!")
    logger.success("All steps completed successfully")
    logger.info(f"Models: {config.MODELS_DIR}")
    logger.info(f"Metrics: {config.METRICS_DIR}")
    logger.info(f"Plots: {config.PLOTS_DIR}")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run traffic signal optimization pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python main.py
  
  # Run with custom training time (1 hour)
  python main.py --training-time 3600
  
  # Skip data preparation and only train
  python main.py --skip-download --skip-network --skip-traffic --skip-baseline
  
  # Only evaluate existing models
  python main.py --skip-all --no-skip-evaluation --no-skip-visualization
        """
    )
    
    # Skip options
    parser.add_argument('--skip-download', action='store_true', help='Skip OSM download')
    parser.add_argument('--skip-network', action='store_true', help='Skip network generation')
    parser.add_argument('--skip-traffic', action='store_true', help='Skip traffic generation')
    parser.add_argument('--skip-baseline', action='store_true', help='Skip baseline evaluation')
    parser.add_argument('--skip-training', action='store_true', help='Skip DQN training')
    parser.add_argument('--skip-evaluation', action='store_true', help='Skip RL evaluation')
    parser.add_argument('--skip-visualization', action='store_true', help='Skip visualization')
    parser.add_argument('--skip-all', action='store_true', help='Skip all steps (use with --no-skip-* to run specific steps)')
    
    # Training options
    parser.add_argument('--training-episodes', type=int, default=None, help='Number of training episodes')
    parser.add_argument('--training-time', type=int, default=None, help='Training time in seconds')
    
    # No-skip options (for use with --skip-all)
    parser.add_argument('--no-skip-evaluation', action='store_true', help='Do not skip evaluation')
    parser.add_argument('--no-skip-visualization', action='store_true', help='Do not skip visualization')
    
    args = parser.parse_args()
    
    # Handle --skip-all
    if args.skip_all:
        skip_download = True
        skip_network = True
        skip_traffic = True
        skip_baseline = True
        skip_training = True
        skip_evaluation = True
        skip_visualization = True
        
        # Apply no-skip overrides
        if args.no_skip_evaluation:
            skip_evaluation = False
        if args.no_skip_visualization:
            skip_visualization = False
    else:
        skip_download = args.skip_download
        skip_network = args.skip_network
        skip_traffic = args.skip_traffic
        skip_baseline = args.skip_baseline
        skip_training = args.skip_training
        skip_evaluation = args.skip_evaluation
        skip_visualization = args.skip_visualization
    
    # Run pipeline
    success = run_pipeline(
        skip_download=skip_download,
        skip_network=skip_network,
        skip_traffic=skip_traffic,
        skip_baseline=skip_baseline,
        skip_training=skip_training,
        skip_evaluation=skip_evaluation,
        skip_visualization=skip_visualization,
        training_episodes=args.training_episodes,
        training_time=args.training_time
    )
    
    sys.exit(0 if success else 1)
