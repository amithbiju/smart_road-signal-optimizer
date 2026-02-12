"""
SUMO Network Generator
Converts OSM data to SUMO network and extracts traffic light junctions
"""

import os
import sys
import subprocess
from utils.logger import Logger
from utils.sumo_checker import setup_sumo_environment

logger = Logger()


def generate_network(osm_file, network_file):
    """
    Convert OSM file to SUMO network using netconvert
    
    Args:
        osm_file: Path to input OSM XML file
        network_file: Path to output SUMO network file
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Converting OSM data to SUMO network...")
    
    # Set up SUMO environment
    try:
        setup_sumo_environment()
    except EnvironmentError as e:
        logger.error(str(e))
        return False
    
    # Get SUMO_HOME and netconvert path
    sumo_home = os.environ.get('SUMO_HOME')
    netconvert = os.path.join(
        sumo_home, 'bin',
        'netconvert.exe' if sys.platform == 'win32' else 'netconvert'
    )
    
    # Create output directory
    os.makedirs(os.path.dirname(network_file), exist_ok=True)
    
    # netconvert command
    cmd = [
        netconvert,
        '--osm-files', osm_file,
        '--output-file', network_file,
        '--geometry.remove',  # Remove geometry
        '--roundabouts.guess',  # Guess roundabouts
        '--ramps.guess',  # Guess ramps
        '--junctions.join',  # Join junctions
        '--tls.guess',  # Guess traffic lights
        '--tls.default-type', 'static',  # Use static traffic lights initially
        '--verbose',
    ]
    
    try:
        logger.info(f"Running netconvert...")
        logger.info(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.success("Network conversion successful")
            
            # Check output file
            if os.path.exists(network_file):
                file_size = os.path.getsize(network_file)
                logger.info(f"Network file created: {network_file} ({file_size / 1024:.1f} KB)")
                return True
            else:
                logger.error("Network file was not created")
                return False
        
        else:
            logger.error(f"netconvert failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        logger.error("netconvert timed out")
        return False
    
    except Exception as e:
        logger.error(f"Error running netconvert: {e}")
        return False


def extract_traffic_light_junctions(network_file):
    """
    Extract traffic light junction IDs from SUMO network
    
    Args:
        network_file: Path to SUMO network file
    
    Returns:
        list: List of traffic light junction IDs
    """
    logger.info("Extracting traffic light junctions...")
    
    try:
        setup_sumo_environment()
        import sumolib
        
        # Read network
        net = sumolib.net.readNet(network_file)
        
        # Get all traffic light junctions
        tl_junctions = []
        
        for node in net.getNodes():
            if node.getType() == 'traffic_light':
                tl_junctions.append(node.getID())
        
        logger.success(f"Found {len(tl_junctions)} traffic light junctions")
        
        if len(tl_junctions) > 0:
            logger.info(f"Junction IDs: {tl_junctions[:10]}{'...' if len(tl_junctions) > 10 else ''}")
        else:
            logger.warning("No traffic light junctions found! Network may be too small.")
            logger.warning("Consider using a larger bounding box or different area.")
        
        return tl_junctions
    
    except Exception as e:
        logger.error(f"Error extracting junctions: {e}")
        return []


def get_junction_info(network_file, junction_id):
    """
    Get detailed information about a junction
    
    Args:
        network_file: Path to SUMO network file
        junction_id: Junction ID
    
    Returns:
        dict: Junction information (lanes, phases, etc.)
    """
    try:
        setup_sumo_environment()
        import sumolib
        
        net = sumolib.net.readNet(network_file)
        node = net.getNode(junction_id)
        
        # Get incoming lanes
        incoming_lanes = []
        for edge in node.getIncoming():
            for lane in edge.getLanes():
                incoming_lanes.append(lane.getID())
        
        # Get traffic light logic if available
        tls = net.getTLS(junction_id) if node.getType() == 'traffic_light' else None
        
        info = {
            'id': junction_id,
            'type': node.getType(),
            'coord': node.getCoord(),
            'incoming_lanes': incoming_lanes,
            'num_lanes': len(incoming_lanes),
            'has_tls': tls is not None
        }
        
        return info
    
    except Exception as e:
        logger.error(f"Error getting junction info: {e}")
        return None


if __name__ == "__main__":
    # Test network generation
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    import config
    
    # Generate network
    success = generate_network(config.OSM_FILE, config.NETWORK_FILE)
    
    if success:
        # Extract junctions
        junctions = extract_traffic_light_junctions(config.NETWORK_FILE)
        
        # Print info for first junction
        if junctions:
            info = get_junction_info(config.NETWORK_FILE, junctions[0])
            print(f"\nSample junction info: {info}")
