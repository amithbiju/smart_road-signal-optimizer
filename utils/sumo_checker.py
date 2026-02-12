"""
SUMO Installation Checker
Verifies SUMO is properly installed and accessible
"""

import os
import sys
import subprocess


def check_sumo_installation():
    """
    Check if SUMO is installed and SUMO_HOME is set correctly
    Returns: (bool, str) - (is_installed, message)
    """
    print("=" * 70)
    print("SUMO Installation Check")
    print("=" * 70)
    
    # Check SUMO_HOME environment variable
    sumo_home = os.environ.get('SUMO_HOME')
    
    if not sumo_home:
        return False, (
            "[ERROR] SUMO_HOME environment variable is not set.\n\n"
            "Please install SUMO and set SUMO_HOME:\n"
            "1. Download SUMO from: https://sumo.dlr.de/docs/Downloads.php\n"
            "2. Install SUMO\n"
            "3. Set SUMO_HOME environment variable to SUMO installation directory\n"
            "   Example (Windows): C:\\Program Files (x86)\\Eclipse\\Sumo\n"
            "   Example (Linux): /usr/share/sumo\n"
            "4. Add SUMO bin directory to PATH\n"
        )
    
    print(f"[OK] SUMO_HOME is set: {sumo_home}")
    
    # Check if SUMO_HOME directory exists
    if not os.path.isdir(sumo_home):
        return False, f"[ERROR] SUMO_HOME directory does not exist: {sumo_home}"
    
    print(f"[OK] SUMO_HOME directory exists")
    
    # Check for essential SUMO binaries
    tools_dir = os.path.join(sumo_home, 'tools')
    bin_dir = os.path.join(sumo_home, 'bin')
    
    # Check for netconvert
    netconvert = 'netconvert.exe' if sys.platform == 'win32' else 'netconvert'
    netconvert_path = os.path.join(bin_dir, netconvert)
    
    if not os.path.isfile(netconvert_path):
        return False, f"[ERROR] netconvert not found at: {netconvert_path}"
    
    print(f"[OK] netconvert found")
    
    # Check for duarouter
    duarouter = 'duarouter.exe' if sys.platform == 'win32' else 'duarouter'
    duarouter_path = os.path.join(bin_dir, duarouter)
    
    if not os.path.isfile(duarouter_path):
        return False, f"[ERROR] duarouter not found at: {duarouter_path}"
    
    print(f"[OK] duarouter found")
    
    # Check for sumo binary
    sumo_binary = 'sumo.exe' if sys.platform == 'win32' else 'sumo'
    sumo_path = os.path.join(bin_dir, sumo_binary)
    
    if not os.path.isfile(sumo_path):
        return False, f"[ERROR] sumo binary not found at: {sumo_path}"
    
    print(f"[OK] sumo binary found")
    
    # Check for tools directory
    if not os.path.isdir(tools_dir):
        return False, f"[ERROR] SUMO tools directory not found at: {tools_dir}"
    
    print(f"[OK] SUMO tools directory found")
    
    # Check for randomTrips.py
    random_trips = os.path.join(tools_dir, 'randomTrips.py')
    if not os.path.isfile(random_trips):
        return False, f"[ERROR] randomTrips.py not found at: {random_trips}"
    
    print(f"[OK] randomTrips.py found")
    
    # Try to import traci
    try:
        # Add tools to Python path
        if tools_dir not in sys.path:
            sys.path.append(tools_dir)
        
        import traci
        print(f"[OK] TraCI module imported successfully")
        print(f"  TraCI version: {traci.__version__ if hasattr(traci, '__version__') else 'Unknown'}")
    except ImportError as e:
        return False, f"[ERROR] Failed to import TraCI: {e}\n\nMake sure SUMO tools are in PYTHONPATH"
    
    # Try to import sumolib
    try:
        import sumolib
        print(f"[OK] sumolib module imported successfully")
    except ImportError as e:
        return False, f"[ERROR] Failed to import sumolib: {e}\n\nMake sure SUMO tools are in PYTHONPATH"
    
    # Test SUMO version
    try:
        result = subprocess.run(
            [sumo_path, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_info = result.stdout.strip().split('\n')[0]
            print(f"[OK] SUMO version: {version_info}")
        else:
            print(f"[WARN] Could not determine SUMO version")
    except Exception as e:
        print(f"[WARN] Could not run SUMO version check: {e}")
    
    print("=" * 70)
    print("[SUCCESS] SUMO is properly installed and configured!")
    print("=" * 70)
    
    return True, "SUMO installation verified successfully"


def setup_sumo_environment():
    """
    Set up SUMO environment for Python scripts
    Adds SUMO tools to sys.path
    """
    sumo_home = os.environ.get('SUMO_HOME')
    if not sumo_home:
        raise EnvironmentError("SUMO_HOME environment variable is not set")
    
    tools_dir = os.path.join(sumo_home, 'tools')
    if tools_dir not in sys.path:
        sys.path.append(tools_dir)
    
    return tools_dir


if __name__ == "__main__":
    success, message = check_sumo_installation()
    
    if not success:
        print(message)
        sys.exit(1)
    else:
        print("\n✅ All checks passed! You can proceed with the project.")
        sys.exit(0)
