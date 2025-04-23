from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Account credentials
    account_name: str
    phone_number: str
    password: Optional[str]
    api_id: str
    api_hash: str

    origin_group: int
    destiny_group: int
    
    # Anti-ban settings with default values
    min_delay: int = 3            # Minimum delay between messages (seconds)
    max_delay: int = 5            # Maximum delay between messages (seconds)
    daily_limit: int = 1000       # Maximum number of messages per day
    hourly_limit: int = 100       # Maximum number of messages per hour
    daily_media_limit: int = 500  # Maximum number of media messages per day
    max_batch_size: int = 50      # Maximum messages to process before taking a longer break
    batch_cooldown: int = 300     # Cooldown time after reaching batch size (seconds)
    night_mode: bool = True       # Reduce activity during night hours
    night_start: int = 0          # Night mode start hour (24h format)
    night_end: int = 7            # Night mode end hour (24h format)
    night_multiplier: float = 2.0 # Multiply delays by this factor during night hours
    weekend_mode: bool = False    # Whether to reduce activity during weekends
    weekend_multiplier: float = 1.5 # Multiply delays by this factor during weekends
    check_interval: int = 300    # Intervalo para verificar novas mensagens (segundos)
    continuous_mode: bool = True # Executar continuamente verificando novas mensagens

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False