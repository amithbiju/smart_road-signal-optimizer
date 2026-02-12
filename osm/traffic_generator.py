"""
Traffic Generator
Generates random traffic trips and routes for SUMO simulation
"""

import os
import sys
import subprocess
from utils.logger import Logger
from utils.sumo_checker import setup_sumo_environment

logger = Logger()


def generate_random_trips(network_file, trips_file, period=1, probability=0.3, min_distance=100):
    """
    Generate random trips using SUMO's randomTrips.py
    
    Args:
        network_file: Path to SUMO network file
        trips_file: Path to output trips file
        period: Period for trip generation (seconds)
        probability: Probability of vehicle generation per edge
        min_distance: Minimum trip distance (meters)
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Generating random traffic trips...")
    
    try:
        setup_sumo_environment()
    except EnvironmentError as e:
        logger.error(str(e))
        return False
    
    # Get SUMO tools path
    sumo_home = os.environ.get('SUMO_HOME')
    random_trips_script = os.path.join(sumo_home, 'tools', 'randomTrips.py')
    
    # Create output directory
    os.makedirs(os.path.dirname(trips_file), exist_ok=True)
    
    # randomTrips.py command
    cmd = [
        sys.executable,  # Python interpreter
        random_trips_script,
        '--net-file', network_file,
        '--output-trip-file', trips_file,
        '--period', str(period),
        '--fringe-factor', '10',  # Prefer trips starting at network fringe
        '--min-distance', str(min_distance),
        '--random',
        '--validate',
    ]
    
    try:
        logger.info(f"Running randomTrips.py...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )
        
        if result.returncode == 0:
            logger.success("Random trips generated successfully")
            
            if os.path.exists(trips_file):
                file_size = os.path.getsize(trips_file)
                logger.info(f"Trips file created: {trips_file} ({file_size / 1024:.1f} KB)")
                
                # Count trips
                trip_count = result.stdout.count('<trip ')
                logger.info(f"Generated approximately {trip_count} trips")
                
                return True
            else:
                logger.error("Trips file was not created")
                return False
        
        else:
            logger.error(f"randomTrips.py failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        logger.error("randomTrips.py timed out")
        return False
    
    except Exception as e:
        logger.error(f"Error running randomTrips.py: {e}")
        return False


def generate_routes(network_file, trips_file, routes_file):
    """
    Convert trips to routes using duarouter
    
    Args:
        network_file: Path to SUMO network file
        trips_file: Path to input trips file
        routes_file: Path to output routes file
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Converting trips to routes...")
    
    try:
        setup_sumo_environment()
    except EnvironmentError as e:
        logger.error(str(e))
        return False
    
    # Get duarouter path
    sumo_home = os.environ.get('SUMO_HOME')
    duarouter = os.path.join(
        sumo_home, 'bin',
        'duarouter.exe' if sys.platform == 'win32' else 'duarouter'
    )
    
    # duarouter command
    cmd = [
        duarouter,
        '--net-file', network_file,
        '--trip-files', trips_file,
        '--output-file', routes_file,
        '--ignore-errors',  # Ignore routing errors
        '--no-warnings',
        '--verbose',
    ]
    
    try:
        logger.info(f"Running duarouter...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )
        
        if result.returncode == 0:
            logger.success("Routes generated successfully")
            
            if os.path.exists(routes_file):
                file_size = os.path.getsize(routes_file)
                logger.info(f"Routes file created: {routes_file} ({file_size / 1024:.1f} KB)")
                
                # Count routes
                with open(routes_file, 'r') as f:
                    content = f.read()
                    route_count = content.count('<vehicle ')
                
                logger.info(f"Generated {route_count} vehicle routes")
                
                return True
            else:
                logger.error("Routes file was not created")
                return False
        
        else:
            logger.error(f"duarouter failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        logger.error("duarouter timed out")
        return False
    
    except Exception as e:
        logger.error(f"Error running duarouter: {e}")
        return False


def generate_traffic(network_file, trips_file, routes_file, period=1, probability=0.3):
    """
    Complete traffic generation pipeline
    
    Args:
        network_file: Path to SUMO network file
        trips_file: Path to output trips file
        routes_file: Path to output routes file
        period: Period for trip generation
        probability: Probability of vehicle generation
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Generate trips
    if not generate_random_trips(network_file, trips_file, period, probability):
        return False
    
    # Convert to routes
    if not generate_routes(network_file, trips_file, routes_file):
        return False
    
    logger.success("Traffic generation complete!")
    return True


if __name__ == "__main__":
    # Test traffic generation
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    import config
    
    success = generate_traffic(
        config.NETWORK_FILE,
        config.TRIPS_FILE,
        config.ROUTE_FILE,
        period=config.TRAFFIC_PERIOD,
        probability=config.TRAFFIC_PROBABILITY
    )
    
    if success:
        print("\n✅ Traffic generation successful!")
