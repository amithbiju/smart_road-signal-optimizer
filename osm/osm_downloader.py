"""
OSM Data Downloader
Downloads OpenStreetMap data for a given bounding box using Overpass API
"""

import requests
import time
import os
from utils.logger import Logger

logger = Logger()


def download_osm(bbox, output_file, max_retries=3):
    """
    Download OSM data for a bounding box
    
    Args:
        bbox: Dictionary with keys 'south', 'north', 'west', 'east'
        output_file: Path to save OSM XML file
        max_retries: Maximum number of retry attempts
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"Downloading OSM data for bounding box: {bbox}")
    
    # Overpass API endpoint
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Construct Overpass QL query
    # Download all ways (roads) and their nodes within the bounding box
    query = f"""
    [out:xml][timeout:180];
    (
      way["highway"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
      >;
    );
    out meta;
    """
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Try downloading with retries
    for attempt in range(max_retries):
        try:
            logger.info(f"Download attempt {attempt + 1}/{max_retries}...")
            
            response = requests.post(
                overpass_url,
                data={'data': query},
                timeout=300  # 5 minute timeout
            )
            
            if response.status_code == 200:
                # Save to file
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                # Verify file size
                file_size = os.path.getsize(output_file)
                logger.success(f"OSM data downloaded successfully ({file_size / 1024:.1f} KB)")
                logger.info(f"Saved to: {output_file}")
                
                return True
            
            elif response.status_code == 429:
                # Rate limited
                wait_time = 60 * (attempt + 1)
                logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            
            else:
                logger.error(f"HTTP error {response.status_code}: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"Request timed out. Retrying...")
            time.sleep(10)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            time.sleep(10)
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
    
    logger.error("Failed to download OSM data after all retries")
    return False


def validate_osm_file(osm_file):
    """
    Validate that OSM file exists and contains data
    
    Args:
        osm_file: Path to OSM XML file
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(osm_file):
        logger.error(f"OSM file not found: {osm_file}")
        return False
    
    file_size = os.path.getsize(osm_file)
    
    if file_size < 1000:  # Less than 1KB is probably empty/error
        logger.error(f"OSM file is too small ({file_size} bytes), likely invalid")
        return False
    
    # Check if file contains basic OSM structure
    try:
        with open(osm_file, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # Read first 1KB
            
            if '<osm' not in content:
                logger.error("File does not appear to be valid OSM XML")
                return False
    
    except Exception as e:
        logger.error(f"Error reading OSM file: {e}")
        return False
    
    logger.success("OSM file validation passed")
    return True


if __name__ == "__main__":
    # Test download with config
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    import config
    
    config.create_directories()
    
    success = download_osm(config.BOUNDING_BOX, config.OSM_FILE)
    
    if success:
        validate_osm_file(config.OSM_FILE)
