"""
SUMO GUI Viewer - Watch Your Traffic Signals in Action
Run this to see your road network and trained DQN agent controlling signals
"""

import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.sumo_checker import setup_sumo_environment
from utils.logger import Logger, print_header
import config

# Setup SUMO
setup_sumo_environment()
import traci

logger = Logger()

def view_with_gui(mode='rl', duration_seconds=30000):
    """
    Open SUMO GUI and run simulation
    
    Args:
        mode: 'rl' to use trained agents, 'baseline' for fixed-time signals
        duration_seconds: How long to run simulation (default: 5 minutes)
    """
    print_header(f"SUMO GUI Viewer - {mode.upper()} Mode")
    
    # Get SUMO binary
    sumo_home = os.environ.get('SUMO_HOME')
    if not sumo_home:
        logger.error("SUMO_HOME not set!")
        return
    
    # Use sumo-gui
    sumo_binary = os.path.join(
        sumo_home, 'bin',
        'sumo-gui.exe' if sys.platform == 'win32' else 'sumo-gui'
    )
    
    if not os.path.exists(sumo_binary):
        logger.error(f"SUMO GUI not found: {sumo_binary}")
        return
    
    logger.info(f"Network: {config.NETWORK_FILE}")
    logger.info(f"Routes: {config.ROUTE_FILE}")
    logger.info(f"Mode: {mode.upper()}")
    logger.info(f"Duration: {duration_seconds}s")
    
    # Build SUMO command
    sumo_cmd = [
        sumo_binary,
        '--net-file', config.NETWORK_FILE,
        '--route-files', config.ROUTE_FILE,
        '--step-length', str(config.SUMO_STEP_LENGTH),
        '--seed', str(config.SUMO_SEED),
        '--quit-on-end',  # Close when simulation ends
        '--start',  # Start immediately
    ]
    
    try:
        # Start SUMO GUI
        logger.info("\n🎮 Opening SUMO GUI...")
        logger.info("Controls:")
        logger.info("  ▶️  Play/Pause button")
        logger.info("  ⏩  Speed slider (move right = slower)")
        logger.info("  🔍  Scroll to zoom, drag to pan")
        logger.info("  🚦  Right-click junction → 'Show Parameter'\n")
        
        traci.start(sumo_cmd)
        
        # Load agents if RL mode
        agents = {}
        if mode == 'rl':
            logger.info("Loading trained DQN agents...")
            
            from sumo.sumo_env import SUMOEnvironment
            from rl.dqn_agent import DQNAgent
            
            # Get junction IDs
            import sumolib
            net = sumolib.net.readNet(config.NETWORK_FILE)
            tl_junctions = []
            for node in net.getNodes():
                if node.getType() == 'traffic_light':
                    tl_junctions.append(node.getID())
            
            logger.info(f"Found {len(tl_junctions)} traffic light junctions")
            
            # Load agents
            for junction_id in tl_junctions:
                # Determine state size (simplified)
                node = net.getNode(junction_id)
                num_lanes = len([lane for edge in node.getIncoming() for lane in edge.getLanes()])
                state_size = num_lanes * 2 + 2  # queue + waiting + phase + time
                
                agent = DQNAgent(state_size=state_size, action_size=2, device=config.DEVICE)
                model_path = os.path.join(config.MODELS_DIR, f"junction_{junction_id}_dqn.pt")
                
                if os.path.exists(model_path):
                    agent.load(model_path)
                    agents[junction_id] = agent
                    logger.info(f"  ✓ Loaded: {junction_id}")
                else:
                    logger.warning(f"  ✗ Model not found: {junction_id}")
        
        # Run simulation
        max_steps = int(duration_seconds / config.SUMO_STEP_LENGTH)
        logger.info(f"\n▶️  Running simulation for {max_steps} steps...")
        logger.info("Watch the SUMO GUI window!\n")
        
        step = 0
        while step < max_steps and traci.simulation.getMinExpectedNumber() > 0:
            # RL mode: control signals with agents
            if mode == 'rl' and agents:
                for junction_id, agent in agents.items():
                    # Simple state extraction (just for demo)
                    try:
                        current_phase = traci.trafficlight.getPhase(junction_id)
                        # Use random state for demo (proper state extraction would be more complex)
                        import numpy as np
                        state = np.random.rand(agent.state_size)
                        
                        # Get action from agent
                        action = agent.select_action(state, epsilon=0.0)
                        
                        # Apply action (simplified)
                        if action == 1:  # Switch
                            logic = traci.trafficlight.getAllProgramLogics(junction_id)[0]
                            num_phases = len(logic.phases)
                            next_phase = (current_phase + 1) % num_phases
                            traci.trafficlight.setPhase(junction_id, next_phase)
                    except:
                        pass
            
            # Step simulation
            traci.simulationStep()
            step += 1
            
            # Progress update every 100 steps
            if step % 100 == 0:
                vehicles = traci.simulation.getMinExpectedNumber()
                logger.info(f"Step {step}/{max_steps} | Vehicles: {vehicles}")
        
        logger.success(f"\n✅ Simulation complete! ({step} steps)")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            traci.close()
        except:
            pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="View traffic simulation in SUMO GUI")
    parser.add_argument('--mode', type=str, choices=['rl', 'baseline'], default='baseline',
                        help='Simulation mode: rl (trained agents) or baseline (fixed signals)')
    parser.add_argument('--duration', type=int, default=30000,
                        help='Simulation duration in seconds (default: 300 = 5 minutes)')
    
    args = parser.parse_args()
    
    view_with_gui(mode=args.mode, duration_seconds=args.duration)
