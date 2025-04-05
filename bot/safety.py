import random
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
from pathlib import Path
import asyncio

logger = logging.getLogger('CloneGram.Safety')

class AntiDetectionSafety:
    """
    Safety mechanisms to prevent account bans by making the bot behave more human-like
    and respecting Telegram's rate limits.
    """
    
    def __init__(self, settings):
        self.settings = settings
        self.counters_file = Path('./activity_counters.json')
        
        # Initialize counters for tracking message activity
        self.hourly_counters = defaultdict(int)
        self.daily_counters = defaultdict(int)
        self.daily_media_counters = defaultdict(int)
        
        # Queue to keep track of message timestamps for rolling window calculations
        self.hourly_timestamps = deque(maxlen=self.settings.hourly_limit)
        self.daily_timestamps = deque(maxlen=self.settings.daily_limit)
        self.daily_media_timestamps = deque(maxlen=self.settings.daily_media_limit)
        
        # Batch processing tracking
        self.current_batch_count = 0
        
        # Create the counters file if it doesn't exist
        if not self.counters_file.exists():
            try:
                with open(self.counters_file, 'w') as f:
                    json.dump({
                        'hourly': {},
                        'daily': {},
                        'daily_media': {},
                        'timestamps': {
                            'hourly': [],
                            'daily': [],
                            'daily_media': []
                        }
                    }, f, indent=2)
                logger.info(f"Created new activity counters file: {self.counters_file}")
            except Exception as e:
                logger.error(f"Error creating counters file: {str(e)}")
        
        # Load previous counters if available
        self._load_counters()
        
        # Clean up expired counters
        self._cleanup_expired_counters()
        
        # Log current limits
        logger.info(f"Safety system initialized with limits: daily={self.settings.daily_limit}, "
                   f"hourly={self.settings.hourly_limit}, media={self.settings.daily_media_limit}, "
                   f"delay={self.settings.min_delay}-{self.settings.max_delay}s")
    
    def _load_counters(self):
        """Load activity counters from file"""
        if not self.counters_file.exists():
            logger.warning(f"Counters file {self.counters_file} does not exist. Will be created.")
            return
        
        try:
            with open(self.counters_file, 'r') as f:
                data = json.load(f)
                
            # Load hourly counters (only those from the current hour)
            current_hour = self._get_current_hour_key()
            if 'hourly' in data and current_hour in data['hourly']:
                self.hourly_counters[current_hour] = data['hourly'][current_hour]
            
            # Load daily counters (only those from the current day)
            current_day = self._get_current_day_key()
            if 'daily' in data and current_day in data['daily']:
                self.daily_counters[current_day] = data['daily'][current_day]
                
            # Load daily media counters
            if 'daily_media' in data and current_day in data['daily_media']:
                self.daily_media_counters[current_day] = data['daily_media'][current_day]
                
            # Load timestamps (for more accurate tracking)
            if 'timestamps' in data:
                for ts_str in data['timestamps'].get('hourly', []):
                    try:
                        self.hourly_timestamps.append(datetime.fromisoformat(ts_str))
                    except Exception as e:
                        logger.error(f"Error parsing hourly timestamp {ts_str}: {str(e)}")
                
                for ts_str in data['timestamps'].get('daily', []):
                    try:
                        self.daily_timestamps.append(datetime.fromisoformat(ts_str))
                    except Exception as e:
                        logger.error(f"Error parsing daily timestamp {ts_str}: {str(e)}")
                
                for ts_str in data['timestamps'].get('daily_media', []):
                    try:
                        self.daily_media_timestamps.append(datetime.fromisoformat(ts_str))
                    except Exception as e:
                        logger.error(f"Error parsing media timestamp {ts_str}: {str(e)}")
                    
            logger.info(f"Loaded activity counters: hourly={self.hourly_counters.get(current_hour, 0)}, "
                       f"daily={self.daily_counters.get(current_day, 0)}, "
                       f"daily_media={self.daily_media_counters.get(current_day, 0)}")
        except Exception as e:
            logger.error(f"Error loading counters: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _save_counters(self):
        """Save activity counters to file"""
        try:
            # Prepare data structure
            data = {
                'hourly': dict(self.hourly_counters),
                'daily': dict(self.daily_counters),
                'daily_media': dict(self.daily_media_counters),
                'timestamps': {
                    'hourly': [ts.isoformat() for ts in self.hourly_timestamps],
                    'daily': [ts.isoformat() for ts in self.daily_timestamps],
                    'daily_media': [ts.isoformat() for ts in self.daily_media_timestamps]
                }
            }
            
            # Write to file (ensure the path exists)
            with open(self.counters_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Saved activity counters to {self.counters_file}")
        except Exception as e:
            logger.error(f"Error saving counters: {str(e)}")
            # Print detailed information for debugging
            import traceback
            logger.error(traceback.format_exc())
    
    def _cleanup_expired_counters(self):
        """Clean up counters that are no longer relevant (older than a day)"""
        current_hour = self._get_current_hour_key()
        current_day = self._get_current_day_key()
        
        # Keep only the current hour and the previous hour
        self.hourly_counters = {
            k: v for k, v in self.hourly_counters.items()
            if k == current_hour or k == self._get_hour_key(hours_ago=1)
        }
        
        # Keep only the current day and the previous day
        self.daily_counters = {
            k: v for k, v in self.daily_counters.items()
            if k == current_day or k == self._get_day_key(days_ago=1)
        }
        
        # Same for media counters
        self.daily_media_counters = {
            k: v for k, v in self.daily_media_counters.items()
            if k == current_day or k == self._get_day_key(days_ago=1)
        }
    
    def _get_current_hour_key(self):
        """Get a string key for the current hour"""
        return datetime.now().strftime('%Y-%m-%d-%H')
    
    def _get_hour_key(self, hours_ago=0):
        """Get a string key for X hours ago"""
        return (datetime.now() - timedelta(hours=hours_ago)).strftime('%Y-%m-%d-%H')
    
    def _get_current_day_key(self):
        """Get a string key for the current day"""
        return datetime.now().strftime('%Y-%m-%d')
    
    def _get_day_key(self, days_ago=0):
        """Get a string key for X days ago"""
        return (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    
    def _is_night_time(self):
        """Check if current time is within night hours"""
        if not self.settings.night_mode:
            return False
            
        current_hour = datetime.now().hour
        # Handle cases where night spans across midnight
        if self.settings.night_start <= self.settings.night_end:
            return self.settings.night_start <= current_hour < self.settings.night_end
        else:
            return current_hour >= self.settings.night_start or current_hour < self.settings.night_end
    
    def _is_weekend(self):
        """Check if current day is a weekend day"""
        if not self.settings.weekend_mode:
            return False
            
        # 5 = Saturday, 6 = Sunday
        return datetime.now().weekday() >= 5
    
    def _get_delay_multiplier(self):
        """Calculate the current delay multiplier based on time factors"""
        multiplier = 1.0
        
        # Apply night mode multiplier if applicable
        if self._is_night_time():
            multiplier *= self.settings.night_multiplier
            
        # Apply weekend multiplier if applicable
        if self._is_weekend():
            multiplier *= self.settings.weekend_multiplier
            
        return multiplier
        
    def _get_random_delay(self):
        """Get a random delay between min and max delay, adjusted for time-based factors"""
        base_delay = random.uniform(self.settings.min_delay, self.settings.max_delay)
        return base_delay * self._get_delay_multiplier()
    
    def _update_counters(self, is_media=False):
        """Update activity counters"""
        try:
            now = datetime.now()
            
            # Update hourly counter
            current_hour = self._get_current_hour_key()
            if current_hour not in self.hourly_counters:
                self.hourly_counters[current_hour] = 0
            self.hourly_counters[current_hour] += 1
            self.hourly_timestamps.append(now)
            
            # Update daily counter
            current_day = self._get_current_day_key()
            if current_day not in self.daily_counters:
                self.daily_counters[current_day] = 0
            self.daily_counters[current_day] += 1
            self.daily_timestamps.append(now)
            
            # Update media counter if applicable
            if is_media:
                if current_day not in self.daily_media_counters:
                    self.daily_media_counters[current_day] = 0
                self.daily_media_counters[current_day] += 1
                self.daily_media_timestamps.append(now)
            
            # Increment batch counter
            self.current_batch_count += 1
            
            # Log current counts
            logger.info(f"Updated counters: hourly={self.hourly_counters[current_hour]}/{self.settings.hourly_limit}, "
                      f"daily={self.daily_counters[current_day]}/{self.settings.daily_limit}"
                      + (f", media={self.daily_media_counters[current_day]}/{self.settings.daily_media_limit}" if is_media else ""))
            
            # Save counters every time (for debugging)
            self._save_counters()
        except Exception as e:
            logger.error(f"Error updating counters: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Error in updating counters shouldn't prevent the message from being processed
    
    def _check_rate_limits(self, is_media=False):
        """Check if we've hit any rate limits"""
        current_hour = self._get_current_hour_key()
        current_day = self._get_current_day_key()
        
        # Check hourly limit
        hourly_count = self.hourly_counters.get(current_hour, 0)
        if hourly_count >= self.settings.hourly_limit:
            # If we have timestamps to check, calculate remaining time more precisely
            if self.hourly_timestamps:
                remaining = 3600 - (datetime.now() - min(self.hourly_timestamps)).total_seconds()
                wait_time = max(60, int(remaining))
                logger.warning(f"Hourly limit reached ({hourly_count}/{self.settings.hourly_limit}). Waiting {wait_time} seconds")
                return False, wait_time
            else:
                # If no timestamps, just wait for an hour
                logger.warning(f"Hourly limit reached ({hourly_count}/{self.settings.hourly_limit}). Waiting 3600 seconds")
                return False, 3600
        
        # Check daily limit
        daily_count = self.daily_counters.get(current_day, 0)
        if daily_count >= self.settings.daily_limit:
            # Calculate seconds until midnight
            now = datetime.now()
            tomorrow = datetime(now.year, now.month, now.day) + timedelta(days=1)
            wait_time = int((tomorrow - now).total_seconds())
            logger.warning(f"Daily limit reached ({daily_count}/{self.settings.daily_limit}). Waiting until midnight ({wait_time} seconds)")
            return False, wait_time
            
        # Check daily media limit (if applicable)
        if is_media:
            daily_media_count = self.daily_media_counters.get(current_day, 0)
            if daily_media_count >= self.settings.daily_media_limit:
                # Calculate seconds until midnight
                now = datetime.now()
                tomorrow = datetime(now.year, now.month, now.day) + timedelta(days=1)
                wait_time = int((tomorrow - now).total_seconds())
                logger.warning(f"Daily media limit reached ({daily_media_count}/{self.settings.daily_media_limit}). Waiting until midnight ({wait_time} seconds)")
                return False, wait_time
        
        # Check batch size limit
        if self.current_batch_count >= self.settings.max_batch_size:
            self.current_batch_count = 0  # Reset batch counter
            logger.warning(f"Batch size limit reached ({self.settings.max_batch_size}). Taking a break for {self.settings.batch_cooldown} seconds")
            return False, self.settings.batch_cooldown
        
        return True, 0
    
    async def apply_delay(self, is_media=False):
        """
        Apply appropriate delay and check rate limits.
        Returns True if should continue, False if should stop.
        """
        try:
            # Get current counts for logging
            current_hour = self._get_current_hour_key()
            current_day = self._get_current_day_key()
            hourly_count = self.hourly_counters.get(current_hour, 0)
            daily_count = self.daily_counters.get(current_day, 0)
            daily_media_count = self.daily_media_counters.get(current_day, 0) if is_media else 0
            
            logger.info(f"Current counts: hourly={hourly_count}/{self.settings.hourly_limit}, "
                      f"daily={daily_count}/{self.settings.daily_limit}, "
                      f"media={daily_media_count}/{self.settings.daily_media_limit}")
            
            # Check if we're within rate limits
            can_proceed, wait_time = self._check_rate_limits(is_media)
            
            if not can_proceed:
                await asyncio.sleep(wait_time)
                # After waiting, check again
                can_proceed, wait_time = self._check_rate_limits(is_media)
                if not can_proceed:
                    logger.error("Still hitting rate limits after waiting. Stopping.")
                    return False
            
            # Add a random delay to make the bot seem more human-like
            delay = self._get_random_delay()
            logger.info(f"Applying safety delay of {delay:.2f} seconds")
            await asyncio.sleep(delay)
            
            # Update counters after successful delay
            self._update_counters(is_media)
            
            return True
        except Exception as e:
            logger.error(f"Error in safety delay mechanism: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Return True to allow the operation to continue anyway
            # This prevents the safety mechanism from blocking normal operation
            return True