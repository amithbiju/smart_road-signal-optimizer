"""
Simple Traffic Light Phase Inspector
Shows phase definitions directly from SUMO network file
"""

import os
import sys
import xml.etree.ElementTree as ET
from utils.logger import Logger, print_header

logger = Logger()


def inspect_phases_from_xml(network_file, junction_id=None):
    """
    Read phase definitions directly from network XML file
    
    Args:
        network_file: Path to SUMO network file
        junction_id: Specific junction ID (None = all junctions)
    """
    print_header("Traffic Light Phase Inspector")
    
    try:
        # Parse XML
        tree = ET.parse(network_file)
        root = tree.getroot()
        
        # Find all traffic light logic elements
        tl_logics = root.findall('.//tlLogic')
        
        if not tl_logics:
            logger.error("No traffic light logic found in network file")
            return
        
        logger.info(f"Found {len(tl_logics)} traffic light programs\n")
        
        # Process each traffic light
        for tl_logic in tl_logics:
            tl_id = tl_logic.get('id')
            
            # Skip if specific junction requested and this isn't it
            if junction_id and tl_id != junction_id:
                continue
            
            print("\n" + "=" * 100)
            logger.info(f"Junction ID: {tl_id}")
            print("=" * 100)
            
            tl_type = tl_logic.get('type', 'unknown')
            program_id = tl_logic.get('programID', '0')
            
            logger.info(f"Program ID: {program_id}")
            logger.info(f"Type: {tl_type}")
            
            # Get all phases
            phases = tl_logic.findall('phase')
            logger.info(f"Total Phases: {len(phases)}\n")
            
            if not phases:
                logger.warning("No phases found for this traffic light")
                continue
            
            # Display phase table
            print(f"{'Phase':<8} {'Duration':<12} {'State':<60} {'Type':<20}")
            print("-" * 100)
            
            for i, phase in enumerate(phases):
                duration = phase.get('duration', '0')
                state = phase.get('state', '')
                phase_type = classify_phase_simple(state)
                
                # Truncate state if too long
                display_state = state if len(state) <= 55 else state[:52] + "..."
                
                print(f"{i:<8} {duration:<12} {display_state:<60} {phase_type:<20}")
            
            # Show legend
            print("\n" + "-" * 100)
            logger.info("State Encoding:")
            print("  G = Green (priority)      g = Green (yield)      y = Yellow")
            print("  r = Red                   s = Red/Yellow         o = Off")
            
            # Analyze pattern
            print("\n" + "-" * 100)
            logger.info("Phase Pattern Analysis:")
            
            green_phases = []
            yellow_phases = []
            
            for i, phase in enumerate(phases):
                state = phase.get('state', '')
                if 'G' in state or 'g' in state:
                    if 'y' not in state.lower():
                        green_phases.append(i)
                if 'y' in state.lower() and 'g' not in state.lower():
                    yellow_phases.append(i)
            
            print(f"  Green Phases: {green_phases} (traffic flows)")
            print(f"  Yellow Phases: {yellow_phases} (transitions)")
            
            # Show cycle
            if green_phases and yellow_phases:
                print(f"\n  Typical Cycle:")
                for i in range(min(len(green_phases), len(yellow_phases))):
                    if i < len(green_phases):
                        print(f"    Phase {green_phases[i]}: GREEN → ", end="")
                    if i < len(yellow_phases):
                        print(f"Phase {yellow_phases[i]}: YELLOW")
                print(f"    → Repeat")
            
            # Decode first green phase as example
            if green_phases:
                print("\n" + "-" * 100)
                logger.info(f"Example: Phase {green_phases[0]} State Breakdown")
                
                first_green = phases[green_phases[0]]
                state = first_green.get('state', '')
                
                print(f"\n  State String: {state}")
                print(f"  Length: {len(state)} signals")
                print(f"\n  Signal Breakdown:")
                print(f"  {'Position':<12} {'Signal':<10} {'Meaning':<20}")
                print("  " + "-" * 50)
                
                for idx, signal in enumerate(state):
                    meaning = {
                        'G': 'GREEN (priority)',
                        'g': 'GREEN (yield)',
                        'y': 'YELLOW',
                        'r': 'RED',
                        's': 'RED/YELLOW',
                        'o': 'OFF'
                    }.get(signal, signal)
                    
                    print(f"  {idx:<12} {signal:<10} {meaning:<20}")
                    
                    # Only show first 20 to avoid clutter
                    if idx >= 19:
                        remaining = len(state) - 20
                        if remaining > 0:
                            print(f"  ... and {remaining} more signals")
                        break
    
    except FileNotFoundError:
        logger.error(f"Network file not found: {network_file}")
    except ET.ParseError as e:
        logger.error(f"Error parsing XML: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


def classify_phase_simple(state):
    """Classify phase based on state string"""
    state_lower = state.lower()
    
    green_count = state_lower.count('g')
    yellow_count = state_lower.count('y')
    red_count = state_lower.count('r')
    
    if yellow_count > 0 and green_count == 0:
        return "Yellow/Transition"
    elif green_count > len(state) / 2:
        return "Green (Major)"
    elif green_count > 0:
        return "Green (Minor)"
    elif red_count == len(state):
        return "All Red"
    else:
        return "Mixed"


if __name__ == "__main__":
    import argparse
    import config
    
    parser = argparse.ArgumentParser(description="Inspect traffic light phases")
    parser.add_argument('--junction', type=str, default=None, help='Specific junction ID')
    
    args = parser.parse_args()
    
    inspect_phases_from_xml(config.NETWORK_FILE, args.junction)
