"""
SUMO Environment Wrapper
Manages SUMO simulation and provides RL interface
"""

import os
import sys
from utils.logger import Logger
from utils.sumo_checker import setup_sumo_environment
from rl.state_extractor import StateExtractor
from rl.reward_calculator import RewardCalculator

# Set up SUMO environment
setup_sumo_environment()
import traci
import sumolib

logger = Logger()


class SUMOEnvironment:
    """
    SUMO environment for traffic signal control
    Manages simulation lifecycle and provides RL interface
    """
    
    def __init__(
        self,
        network_file,
        route_file,
        use_gui=False,
        step_length=1.0,
        min_green_time=10,
        yellow_time=3,
        seed=42
    ):
        """
        Initialize SUMO environment
        
        Args:
            network_file: Path to SUMO network file
            route_file: Path to SUMO route file
            use_gui: Whether to use SUMO GUI
            step_length: Simulation step length (seconds)
            min_green_time: Minimum green phase duration (seconds)
            yellow_time: Yellow phase duration (seconds)
            seed: Random seed
        """
        self.network_file = network_file
        self.route_file = route_file
        self.use_gui = use_gui
        self.step_length = step_length
        self.min_green_time = min_green_time
        self.yellow_time = yellow_time
        self.seed = seed
        
        # SUMO binary
        sumo_home = os.environ.get('SUMO_HOME')
        if use_gui:
            self.sumo_binary = os.path.join(
                sumo_home, 'bin',
                'sumo-gui.exe' if sys.platform == 'win32' else 'sumo-gui'
            )
        else:
            self.sumo_binary = os.path.join(
                sumo_home, 'bin',
                'sumo.exe' if sys.platform == 'win32' else 'sumo'
            )
        
        # Load network to get junction info
        self.net = sumolib.net.readNet(network_file)
        
        # Get traffic light junctions
        self.tl_junctions = []
        for node in self.net.getNodes():
            if node.getType() == 'traffic_light':
                self.tl_junctions.append(node.getID())
        
        if len(self.tl_junctions) == 0:
            raise ValueError("No traffic light junctions found in network!")
        
        logger.info(f"Found {len(self.tl_junctions)} traffic light junctions")
        
        # Get incoming lanes for each junction
        self.junction_lanes = {}
        for junction_id in self.tl_junctions:
            node = self.net.getNode(junction_id)
            incoming_lanes = []
            for edge in node.getIncoming():
                for lane in edge.getLanes():
                    incoming_lanes.append(lane.getID())
            self.junction_lanes[junction_id] = incoming_lanes
        
        # State extractors and reward calculators for each junction
        self.state_extractors = {}
        self.reward_calculators = {}
        
        for junction_id in self.tl_junctions:
            lanes = self.junction_lanes[junction_id]
            self.state_extractors[junction_id] = StateExtractor(junction_id, lanes)
            self.reward_calculators[junction_id] = RewardCalculator(junction_id, lanes)
        
        # Track phase durations for minimum green time
        self.phase_durations = {jid: 0 for jid in self.tl_junctions}
        self.last_phases = {jid: None for jid in self.tl_junctions}
        self.last_switch_time = {jid: 0 for jid in self.tl_junctions}  # Track when last switch occurred
        
        # Simulation state
        self.is_running = False
        self.current_step = 0
    
    def start(self):
        """Start SUMO simulation"""
        sumo_cmd = [
            self.sumo_binary,
            '--net-file', self.network_file,
            '--route-files', self.route_file,
            '--step-length', str(self.step_length),
            '--seed', str(self.seed),
            '--no-warnings',
            '--no-step-log',
            '--time-to-teleport', '-1',  # Disable teleporting
            '--waiting-time-memory', '1000',
        ]
        
        if not self.use_gui:
            sumo_cmd.append('--start')
        
        try:
            traci.start(sumo_cmd)
            self.is_running = True
            self.current_step = 0
            logger.info("SUMO simulation started")
        except Exception as e:
            logger.error(f"Failed to start SUMO: {e}")
            raise
    
    def reset(self):
        """Reset simulation"""
        if self.is_running:
            traci.close()
        
        self.start()
        
        # Reset state extractors and reward calculators
        for extractor in self.state_extractors.values():
            extractor.reset()
        for calculator in self.reward_calculators.values():
            calculator.reset()
        
        # Reset phase tracking
        self.phase_durations = {jid: 0 for jid in self.tl_junctions}
        self.last_phases = {jid: None for jid in self.tl_junctions}
        self.last_switch_time = {jid: 0 for jid in self.tl_junctions}
        
        # Get initial states
        states = self.get_states()
        
        return states
    
    def step(self, actions):
        """
        Execute actions and step simulation
        
        Args:
            actions: Dictionary {junction_id: action} where action is 0 (keep) or 1 (switch)
        
        Returns:
            tuple: (next_states, rewards, done, info)
        """
        # Apply actions
        for junction_id, action in actions.items():
            self._apply_action(junction_id, action)
        
        # Step simulation
        traci.simulationStep()
        self.current_step += 1
        
        # Update phase durations
        for junction_id in self.tl_junctions:
            self.phase_durations[junction_id] += 1
        
        # Get next states
        next_states = self.get_states()
        
        # Calculate rewards
        rewards = {}
        for junction_id in self.tl_junctions:
            action = actions.get(junction_id, 0)
            rewards[junction_id] = self.reward_calculators[junction_id].calculate_reward(action)
        
        # Check if simulation is done
        done = traci.simulation.getMinExpectedNumber() <= 0
        
        # Get info
        info = self.get_info()
        
        return next_states, rewards, done, info
    
    def _apply_action(self, junction_id, action):
        """
        Apply action to traffic light
        
        Args:
            junction_id: Junction ID
            action: 0 (keep current phase) or 1 (switch to next phase)
        """
        if action == 1:  # Switch phase
            # Check minimum green time using time since last switch
            time_since_switch = self.current_step - self.last_switch_time[junction_id]
            
            # Enforce minimum green time (convert to steps)
            min_steps = int(self.min_green_time / self.step_length)
            
            if time_since_switch >= min_steps:
                try:
                    # Get current phase
                    current_phase = traci.trafficlight.getPhase(junction_id)
                    
                    # Get number of phases
                    logic = traci.trafficlight.getAllProgramLogics(junction_id)[0]
                    num_phases = len(logic.phases)
                    
                    # Switch to next phase
                    next_phase = (current_phase + 1) % num_phases
                    traci.trafficlight.setPhase(junction_id, next_phase)
                    
                    # Update last switch time
                    self.last_switch_time[junction_id] = self.current_step
                    
                    # Reset phase duration counter
                    self.phase_durations[junction_id] = 0
                except Exception as e:
                    logger.warning(f"Failed to switch phase for {junction_id}: {e}")
            # If minimum time not met, ignore switch request (action is rejected)
        # If action == 0, keep current phase (do nothing)
    
    def get_states(self):
        """
        Get states for all junctions
        
        Returns:
            dict: {junction_id: state}
        """
        states = {}
        for junction_id in self.tl_junctions:
            states[junction_id] = self.state_extractors[junction_id].get_state()
        return states
    
    def get_info(self):
        """
        Get additional information about simulation
        
        Returns:
            dict: Simulation info
        """
        info = {
            'step': self.current_step,
            'vehicles': traci.simulation.getMinExpectedNumber(),
        }
        
        # Add per-junction metrics
        for junction_id in self.tl_junctions:
            metrics = self.reward_calculators[junction_id].get_metrics()
            info[f'{junction_id}_waiting_time'] = metrics['waiting_time']
            info[f'{junction_id}_queue_length'] = metrics['queue_length']
        
        return info
    
    def close(self):
        """Close SUMO simulation"""
        if self.is_running:
            traci.close()
            self.is_running = False
            logger.info("SUMO simulation closed")
    
    def get_state_size(self, junction_id):
        """Get state size for a junction"""
        return self.state_extractors[junction_id].state_size
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
