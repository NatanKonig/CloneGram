import json
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger('CloneGram.Progress')

class ProgressTracker:
    def __init__(self):
        self.progress_file = Path('./progress.json')
        self._ensure_progress_file()
    
    def _ensure_progress_file(self):
        """Make sure the progress file exists"""
        if not self.progress_file.exists():
            with open(self.progress_file, 'w') as f:
                json.dump({}, f)
    
    def _load_progress(self) -> dict:
        """Load progress data from file"""
        try:
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Progress file corrupted, creating new one")
            with open(self.progress_file, 'w') as f:
                json.dump({}, f)
            return {}
    
    def save_progress(self, origin_chat_id: int, last_message_id: int) -> None:
        """Save progress to file"""
        progress_data = self._load_progress()
        
        progress_data[str(origin_chat_id)] = {
            "last_message_id": last_message_id,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
        
        logger.info(f"Progress saved: Last processed message for chat {origin_chat_id} is {last_message_id}")
    
    def get_progress(self, origin_chat_id: int) -> int:
        """Get the last processed message ID for a specific chat"""
        progress_data = self._load_progress()
        chat_data = progress_data.get(str(origin_chat_id), {})
        return chat_data.get("last_message_id", 0)