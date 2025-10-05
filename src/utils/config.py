"""Configuration management"""

import os
from pathlib import Path
from typing import Dict, Any
import yaml
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration manager"""
    
    def __init__(self, env: str = None):
        self.env = env or os.getenv("ENV", "development")
        self.config_dir = Path(__file__).parent.parent.parent / "config"
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from YAML files"""
        # Load default config
        default_path = self.config_dir / "default.yml"
        if default_path.exists():
            with open(default_path) as f:
                self._config = yaml.safe_load(f) or {}
        
        # Override with environment config
        env_path = self.config_dir / f"{self.env}.yml"
        if env_path.exists():
            with open(env_path) as f:
                env_config = yaml.safe_load(f) or {}
                self._config.update(env_config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)

config = Config()
