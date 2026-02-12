"""
Logging utilities for the traffic signal optimization system
"""

import os
import csv
import time
from datetime import datetime


class Logger:
    """Simple logger for console and file output"""
    
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.start_time = time.time()
    
    def log(self, message, level="INFO"):
        """Log a message with timestamp"""
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def info(self, message):
        """Log info message"""
        self.log(message, "INFO")
    
    def warning(self, message):
        """Log warning message"""
        self.log(message, "WARN")
    
    def error(self, message):
        """Log error message"""
        self.log(message, "ERROR")
    
    def success(self, message):
        """Log success message"""
        self.log(message, "SUCCESS")
    
    def elapsed_time(self):
        """Get elapsed time since logger creation"""
        return time.time() - self.start_time
    
    def format_time(self, seconds):
        """Format seconds into human-readable time"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


class CSVLogger:
    """Logger for writing metrics to CSV files"""
    
    def __init__(self, filepath, headers):
        """
        Initialize CSV logger
        
        Args:
            filepath: Path to CSV file
            headers: List of column headers
        """
        self.filepath = filepath
        self.headers = headers
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Create file with headers
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def log(self, data):
        """
        Log a row of data
        
        Args:
            data: Dictionary with keys matching headers, or list in header order
        """
        with open(self.filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            
            if isinstance(data, dict):
                row = [data.get(header, '') for header in self.headers]
            else:
                row = data
            
            writer.writerow(row)
    
    def log_batch(self, data_list):
        """
        Log multiple rows at once
        
        Args:
            data_list: List of dictionaries or lists
        """
        with open(self.filepath, 'a', newline='') as f:
            writer = csv.writer(f)
            
            for data in data_list:
                if isinstance(data, dict):
                    row = [data.get(header, '') for header in self.headers]
                else:
                    row = data
                
                writer.writerow(row)


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_progress(current, total, prefix="Progress", bar_length=40):
    """
    Print a progress bar
    
    Args:
        current: Current progress value
        total: Total value
        prefix: Prefix string
        bar_length: Length of progress bar
    """
    percent = current / total
    filled = int(bar_length * percent)
    bar = "=" * filled + "-" * (bar_length - filled)
    print(f"\r{prefix}: |{bar}| {percent*100:.1f}% ({current}/{total})", end="", flush=True)
    
    if current == total:
        print()  # New line when complete
