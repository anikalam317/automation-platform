"""
Mock notification listener for development/testing
In production, this would connect to PostgreSQL LISTEN/NOTIFY
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationListener:
    """Mock notification listener for development"""
    
    def __init__(self):
        self.running = False
        
    def start_listener(self):
        """Start the notification listener"""
        logger.info("Starting mock notification listener...")
        self.running = True
        
        # In production, this would:
        # 1. Connect to PostgreSQL
        # 2. Listen for NOTIFY events
        # 3. Handle workflow/task state changes
        # 4. Trigger next steps in workflow
        
        # For now, just log that it's running
        while self.running:
            try:
                # Simulate listening for notifications
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in notification listener: {e}")
                break
                
    def stop_listener(self):
        """Stop the notification listener"""
        logger.info("Stopping notification listener...")
        self.running = False
