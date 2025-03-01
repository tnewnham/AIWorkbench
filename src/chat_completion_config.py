"""
Configuration module for chat completions.
This module provides a way to configure different chat completion settings
for use with OpenAI's Chat Completion API and potentially other providers.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

console = Console()

# Default configurations
DEFAULT_CONFIGS = {
    "default": {
        "name": "Default Chat Completion",
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "system_message": "You are a helpful assistant. when asked say your name is default"
    },
    "developer": {
        "name": "Developer Assistant",
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_tokens": 4000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "system_message": "You are a senior software developer with expertise in multiple programming languages and frameworks. Provide detailed, accurate, and well-structured code examples. Explain your reasoning and highlight best practices. when asked say your name is developer"
    },
    "concise": {
        "name": "Concise Assistant",
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 1000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "system_message": "You are a helpful assistant that provides concise, accurate responses. Keep your answers brief and to the point. when asked say your name is concise"
    },
    "creative": {
        "name": "Creative Assistant",
        "model": "gpt-4o",
        "temperature": 1.0,
        "max_tokens": 3000,
        "top_p": 1.0,
        "frequency_penalty": 0.2,
        "presence_penalty": 0.2,
        "system_message": "You are a creative assistant with a vivid imagination. Generate unique, innovative ideas and think outside the box. when asked say your name is creative"
    }
}

class ChatCompletionConfig:
    """Configuration manager for chat completions"""
    
    def __init__(self):
        """Initialize the chat completion configuration"""
        # Get user config directory
        self.config_dir = Path.home() / ".config" / "gpt_terminal" / "chat_completion"
        self.config_file = self.config_dir / "config.json"
        
        # Initialize configurations with defaults
        self.configs = DEFAULT_CONFIGS.copy()
        
        # Load custom configurations if they exist
        self._load_configs()
    
    def _load_configs(self) -> None:
        """Load custom configurations from config file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as file:
                    custom_configs = json.load(file)
                    
                    # Update configs with custom ones (overwrite defaults if they exist)
                    self.configs.update(custom_configs)
                    
                    print(f"Loaded {len(custom_configs)} custom chat completion configurations")
        except Exception as e:
            print(f"Error loading chat completion configurations: {str(e)}")
    
    def _save_configs(self) -> None:
        """Save current configurations to config file"""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Filter out default configs to save only custom ones
            custom_configs = {k: v for k, v in self.configs.items() 
                             if k not in DEFAULT_CONFIGS or v != DEFAULT_CONFIGS[k]}
            
            # Save configurations
            with open(self.config_file, 'w', encoding='utf-8') as file:
                json.dump(custom_configs, file, indent=2)
                
            print(f"Saved {len(custom_configs)} custom chat completion configurations")
        except Exception as e:
            print(f"Error saving chat completion configurations: {str(e)}")
    
    def get_config(self, config_name: str = "default") -> Optional[Dict[str, Any]]:
        """
        Get a configuration by name
        
        Args:
            config_name: Name of the configuration to get
            
        Returns:
            Configuration dict or None if not found
        """
        return self.configs.get(config_name)
    
    def add_config(self, config_name: str, config: Dict[str, Any]) -> bool:
        """
        Add a new configuration
        
        Args:
            config_name: Name for the new configuration
            config: Configuration dict
            
        Returns:
            True if added successfully, False otherwise
        """
        if not config_name or not isinstance(config, dict):
            return False
        
        # Add or update configuration
        self.configs[config_name] = config
        
        # Save to disk
        self._save_configs()
        
        return True
    
    def delete_config(self, config_name: str) -> bool:
        """
        Delete a configuration
        
        Args:
            config_name: Name of the configuration to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        # Don't allow deletion of default configs
        if config_name in DEFAULT_CONFIGS:
            return False
            
        # Remove configuration if it exists
        if config_name in self.configs:
            del self.configs[config_name]
            
            # Save changes
            self._save_configs()
            
            return True
            
        return False
    
    def get_config_names(self) -> List[str]:
        """
        Get a list of all available configuration names
        
        Returns:
            List of configuration names
        """
        return list(self.configs.keys())

# Create global instance
chat_completion_config = ChatCompletionConfig()

class AnthropicConfig(ChatCompletionConfig):
    """Configuration specifically for Anthropic's Claude models"""
    
    def __init__(self):
        super().__init__()
        self.configs = {
            "claude": self._create_claude_config(),
            "claude_precise": self._create_claude_precise_config(),
        }
        self.active_config_name = "claude"
        self.active_config = self.configs["claude"]
    
    def _create_claude_config(self):
        """Create a configuration for Claude"""
        return {
            "provider": "anthropic",
            "model": "claude-3-opus-20240229",
            "temperature": 0.7,
            "max_tokens": 4000,
            "top_p": 1.0,
            "system_message": """You are Claude, a helpful and harmless AI assistant.""",
            "name": "Claude",
            "description": "Anthropic's Claude model with balanced settings."
        }
    
    def _create_claude_precise_config(self):
        """Create a precise configuration for Claude"""
        return {
            "provider": "anthropic",
            "model": "claude-3-opus-20240229",
            "temperature": 0.1,
            "max_tokens": 4000,
            "top_p": 1.0,
            "system_message": """You are Claude, a precise and technically accurate AI assistant that specializes in factual information.""",
            "name": "Claude Precise",
            "description": "Anthropic's Claude with settings optimized for precise, factual responses."
        }


class GeminiConfig(ChatCompletionConfig):
    """Configuration specifically for Google's Gemini models"""
    
    def __init__(self):
        super().__init__()
        self.configs = {
            "gemini": self._create_gemini_config(),
            "gemini_creative": self._create_gemini_creative_config(),
        }
        self.active_config_name = "gemini"
        self.active_config = self.configs["gemini"]
    
    def _create_gemini_config(self):
        """Create a configuration for Gemini"""
        return {
            "provider": "google",
            "model": "gemini-1.5-pro",
            "temperature": 0.7,
            "max_tokens": 4000,
            "top_p": 1.0,
            "top_k": 40,
            "system_message": """You are a helpful AI assistant powered by Google's Gemini model.""",
            "name": "Gemini",
            "description": "Google's Gemini model with balanced settings."
        }
    
    def _create_gemini_creative_config(self):
        """Create a creative configuration for Gemini"""
        return {
            "provider": "google",
            "model": "gemini-1.5-pro",
            "temperature": 0.9,
            "max_tokens": 4000,
            "top_p": 1.0,
            "top_k": 40,
            "system_message": """You are a creative AI assistant powered by Google's Gemini model. Feel free to be imaginative and think outside the box.""",
            "name": "Gemini Creative",
            "description": "Google's Gemini optimized for creative and imaginative responses."
        } 