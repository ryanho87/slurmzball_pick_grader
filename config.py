"""
Configuration management for the Fantasy Roast Bot API
"""

import os
import yaml
import asyncio
import threading
import time
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# OpenAI API key will be loaded from merged config (secrets.yaml)
# Fallback to environment variable if needed
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def load_config() -> Dict[str, Any]:
    """Load configuration by merging base.yaml and secrets.yaml"""
    base_path = "config/base.yaml"
    secrets_path = "config/secrets.yaml"
    
    try:
        # Load base configuration
        with open(base_path, 'r') as file:
            base_config = yaml.safe_load(file) or {}
        
        # Load secrets configuration
        secrets_config = {}
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as file:
                secrets_config = yaml.safe_load(file) or {}
        
        # Merge configurations (secrets override base)
        merged_config = _deep_merge(base_config, secrets_config)
        
        return merged_config
        
    except FileNotFoundError as e:
        raise RuntimeError(f"Configuration file not found: {e}")
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing configuration file: {e}")


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence"""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


class ConfigManager:
    """Manages application configuration and provides reloading capabilities"""
    
    def __init__(self):
        self.config: Optional[Dict[str, Any]] = None
        self.league_webhooks: Dict[str, Dict[str, str]] = {}
        self.webhooks: Dict[str, str] = {}
        self.model: str = "gpt-4o-mini"
        self.max_tokens: int = 280
        self.api_key: Optional[str] = None
        self._load_initial_config()
    
    def _load_initial_config(self):
        """Load initial configuration"""
        self.reload_configuration()
    
    def reload_configuration(self) -> Tuple[bool, str]:
        """Reload configuration from YAML file and update global state"""
        try:
            # Load new configuration
            new_config = load_config()
            
            # Update global config
            self.config = new_config
            
            # Rebuild league webhook mapping
            new_league_webhooks = {}
            for league in new_config.get('leagues', []):
                league_name = league['name']
                new_league_webhooks[league_name] = {
                    "Mel": league['mel'],
                    "Todd": league['todd'],
                    "Shannon": league['shannon'],
                    "AB": league['ab'],
                }
            
            # Update league webhooks
            self.league_webhooks.clear()
            self.league_webhooks.update(new_league_webhooks)
            
            # Fallback to environment variables if no leagues configured
            if not self.league_webhooks:
                self.webhooks.clear()
                self.webhooks.update({
                    "Mel": os.getenv("DISCORD_WEBHOOK_MEL"),
                    "Todd": os.getenv("DISCORD_WEBHOOK_TODD"),
                    "Shannon": os.getenv("DISCORD_WEBHOOK_SHANNON"),
                    "AB": os.getenv("DISCORD_WEBHOOK_AB"),
                })
            else:
                # Use first league as default
                default_league = list(self.league_webhooks.keys())[0]
                self.webhooks.clear()
                self.webhooks.update(self.league_webhooks[default_league])
            
            # Update OpenAI settings
            self.model = new_config.get('openai', {}).get('model', os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
            self.max_tokens = new_config.get('openai', {}).get('max_tokens', int(os.getenv("MAX_TOKENS", "280")))
            self.api_key = new_config.get('openai', {}).get('api_key', os.getenv("OPENAI_API_KEY"))
            
            # Validate API key
            if not self.api_key:
                raise RuntimeError("OpenAI API key not found in config or environment variables")
            
            return True, "Configuration reloaded successfully"
            
        except Exception as e:
            return False, f"Error reloading configuration: {str(e)}"
    
    def get_api_key(self) -> str:
        """Get the OpenAI API key from merged configuration"""
        if not self.api_key:
            raise RuntimeError("OpenAI API key not configured")
        return self.api_key
    
    def get_league_config(self, league_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific league"""
        if not self.config:
            return None
        return next((league for league in self.config.get('leagues', []) if league['name'] == league_name), None)
    
    def get_full_config(self) -> Optional[Dict[str, Any]]:
        """Get the full configuration including global prompts"""
        return self.config
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get current configuration status"""
        return {
            "status": "active",
            "last_loaded": "2024-01-19T00:00:00Z",
            "config_hash": "config_hash_placeholder",
            "leagues": list(self.league_webhooks.keys())
        }


class ConfigWatcher:
    """Watches for configuration file changes and automatically reloads"""
    
    def __init__(self, config_path: str, callback):
        self.config_path = Path(config_path)
        self.callback = callback
        self.last_modified = self.config_path.stat().st_mtime if self.config_path.exists() else 0
        self.running = False
        self.thread = None
    
    def start(self):
        """Start watching for config file changes"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop watching for config file changes"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def _watch_loop(self):
        """Watch loop that runs in a separate thread"""
        while self.running:
            try:
                if self.config_path.exists():
                    current_modified = self.config_path.stat().st_mtime
                    if current_modified > self.last_modified:
                        self.last_modified = current_modified
                        print(f"🔄 Config file changed, reloading configuration...")
                        # Run callback in main thread
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                asyncio.run_coroutine_threadsafe(self.callback(), loop)
                            else:
                                # If no event loop, just call the function directly
                                self.callback()
                        except RuntimeError:
                            # No event loop available, call directly
                            self.callback()
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                print(f"⚠️ Error in config watcher: {e}")
                time.sleep(5)  # Wait longer on error


# Global configuration manager instance
config_manager = ConfigManager()
