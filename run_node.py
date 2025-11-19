#!/usr/bin/env python3
"""
Simple script to run a single process node
Usage: python run_node.py <process_id>
"""

import sys
import os
import logging
from process_node import ProcessNode

def setup_logging(process_id: int):
    """Setup logging for the process"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Setup logging configuration
    log_format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'logs/pid_{process_id}.txt', mode='w')
        ]
    )

def main():
    if len(sys.argv) != 2:
        print("Usage: python run_node.py <process_id>")
        print("Example: python run_node.py 0")
        print("Process ID should be between 0-14")
        sys.exit(1)
    
    try:
        process_id = int(sys.argv[1])
        
        if process_id < 0 or process_id > 14:
            print("Error: Process ID must be between 0-14")
            sys.exit(1)
        
        # Setup logging
        setup_logging(process_id)
        
        print(f"Starting SES Process {process_id}...")
        
        # Create and run process node
        process = ProcessNode(process_id)
        
        # Check if running in non-interactive mode (output redirected)
        if not sys.stdout.isatty():
            # Daemon mode - run without console interaction
            process.run_daemon()
        else:
            # Interactive mode for manual testing
            process.run_interactive()
        
    except ValueError:
        print("Error: Process ID must be a valid integer")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutdown requested...")
        sys.exit(0)
    except Exception as e:
        print(f"Error running process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()