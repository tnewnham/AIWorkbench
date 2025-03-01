"""
Chat completion module for interacting with OpenAI's Chat Completion API.
This module provides functionality for creating chat completions using OpenAI's API
and managing the chat history.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Union
from rich.console import Console
from openai import OpenAI
from dotenv import load_dotenv
import openai
from datetime import datetime

# Import the configuration
from .chat_completion_config import chat_completion_config

load_dotenv()
console = Console()

# Try to import optional providers
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Set API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

class Message:
    """Represents a message in the chat history"""
    
    def __init__(self, role: str, content: str):
        """
        Initialize a message
        
        Args:
            role: The role of the message sender (system, user, assistant)
            content: The content of the message
        """
        self.role = role
        self.content = content
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, str]:
        """
        Convert the message to a dictionary format for API requests
        
        Returns:
            Dictionary representation of the message
        """
        return {
            "role": self.role,
            "content": self.content
        }
    
    def __str__(self) -> str:
        """String representation of the message"""
        return f"{self.role}: {self.content}"


class ChatCompletionClient:
    """Client for handling chat completion API calls to various providers"""
    
    def __init__(self, config=None):
        """Initialize the client with a specific config or use the default"""
        self.config = config or chat_completion_config.get_config()
        self.provider = self.config.get("provider", "openai")
        
        # Initialize provider-specific clients
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients based on available providers"""
        # OpenAI client (always initialized)
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Anthropic client (optional)
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            self.anthropic_client = None
        
        # Google client (optional)
        if GEMINI_AVAILABLE and os.getenv("GOOGLE_API_KEY"):
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.gemini_available = True
        else:
            self.gemini_available = False
    
    def update_config(self, config):
        """Update the client configuration"""
        self.config = config
        self.provider = config.get("provider", "openai")
    
    def get_completion(self, messages: List[Message], stream: bool = False) -> Union[str, Any]:
        """Get a completion from the appropriate provider based on the config"""
        if self.provider == "openai":
            return self._get_openai_completion(messages, stream)
        elif self.provider == "anthropic":
            return self._get_anthropic_completion(messages, stream)
        elif self.provider == "google":
            return self._get_google_completion(messages, stream)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _get_openai_completion(self, messages: List[Message], stream: bool) -> Union[str, Any]:
        """Get a completion from OpenAI"""
        try:
            # Convert Message objects to dicts
            message_dicts = [msg.to_dict() for msg in messages]
            
            # Extract relevant parameters from config
            model = self.config.get("model", "gpt-4o")
            temperature = self.config.get("temperature", 0.7)
            max_tokens = self.config.get("max_tokens", 4000)
            top_p = self.config.get("top_p", 1.0)
            frequency_penalty = self.config.get("frequency_penalty", 0)
            presence_penalty = self.config.get("presence_penalty", 0)
            
            # Make the API call
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=message_dicts,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stream=stream
            )
            
            if stream:
                # Return the stream object for the caller to iterate
                return response
            else:
                # Return just the content
                return response.choices[0].message.content
                
        except Exception as e:
            console.print(f"Error with OpenAI completion: {str(e)}", style="bold red")
            return f"Error: {str(e)}"
    
    def _get_anthropic_completion(self, messages: List[Message], stream: bool) -> Union[str, Any]:
        """Get a completion from Anthropic"""
        if not ANTHROPIC_AVAILABLE or not self.anthropic_client:
            return "Error: Anthropic client not available. Install with 'pip install anthropic'."
        
        try:
            # Extract config parameters
            model = self.config.get("model", "claude-3-opus-20240229")
            temperature = self.config.get("temperature", 0.7)
            max_tokens = self.config.get("max_tokens", 4000)
            
            # Build the system prompt and messages
            system = None
            anthropic_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system = msg.content
                else:
                    anthropic_messages.append({"role": msg.role, "content": msg.content})
            
            # Make the API call
            response = self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=anthropic_messages,
                stream=stream
            )
            
            if stream:
                return response
            else:
                return response.content[0].text
                
        except Exception as e:
            console.print(f"Error with Anthropic completion: {str(e)}", style="bold red")
            return f"Error: {str(e)}"
    
    def _get_google_completion(self, messages: List[Message], stream: bool) -> Union[str, Any]:
        """Get a completion from Google's Gemini"""
        if not GEMINI_AVAILABLE or not self.gemini_available:
            return "Error: Google Gemini client not available. Install with 'pip install google-generativeai'."
        
        try:
            # Extract config parameters
            model_name = self.config.get("model", "gemini-1.5-pro")
            temperature = self.config.get("temperature", 0.7)
            max_tokens = self.config.get("max_tokens", 4000)
            top_p = self.config.get("top_p", 1.0)
            top_k = self.config.get("top_k", 40)
            
            # Find system message
            system_message = None
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                    break
            
            # Create generation config
            generation_config = {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "max_output_tokens": max_tokens,
            }
            
            # Initialize the model
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                system_instruction=system_message
            )
            
            # Format messages for Gemini (excluding system message)
            gemini_messages = []
            for msg in messages:
                if msg.role != "system":
                    role = "user" if msg.role == "user" else "model"
                    gemini_messages.append({"role": role, "parts": [msg.content]})
            
            # Create a chat session
            chat = model.start_chat(history=gemini_messages)
            
            # Generate a response
            response = chat.send_message(
                gemini_messages[-1]["parts"][0] if gemini_messages else "",
                stream=stream
            )
            
            if stream:
                return response
            else:
                return response.text
                
        except Exception as e:
            console.print(f"Error with Google Gemini completion: {str(e)}", style="bold red")
            return f"Error: {str(e)}"


class ChatHistory:
    """Manages the history of messages in a chat"""
    
    def __init__(self):
        """Initialize an empty chat history"""
        self.messages: List[Message] = []
        self.system_message: Optional[Message] = None
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the chat history
        
        Args:
            role: The role of the message sender (system, user, assistant)
            content: The content of the message
        """
        # Validate role
        if role not in ["system", "user", "assistant"]:
            raise ValueError(f"Invalid role: {role}. Must be 'system', 'user', or 'assistant'")
        
        # Handle system message specially - we only keep one
        if role == "system":
            self.system_message = Message(role, content)
            return
        
        # Add the message to the history
        self.messages.append(Message(role, content))
    
    def get_messages_for_completion(self) -> List[Message]:
        """
        Get messages formatted for the chat completion API
        
        Returns:
            List of messages for completion API
        """
        result = []
        
        # Add system message first if it exists
        if self.system_message:
            result.append(self.system_message)
        
        # Add all other messages in order
        result.extend(self.messages)
        
        return result
    
    def clear(self) -> None:
        """Clear the chat history (except system message)"""
        self.messages = []
    
    def __len__(self) -> int:
        """Get the number of messages in the history (excluding system message)"""
        return len(self.messages)


def create_chat_completion(messages: List[Dict[str, str]], config: Dict[str, Any]) -> str:
    """
    Create a chat completion using OpenAI's API
    
    Args:
        messages: List of message dictionaries
        config: Configuration parameters for the API call
    
    Returns:
        The response text from the assistant
    """
    try:
        # Extract configuration parameters
        model = config.get("model", "gpt-4o")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)
        top_p = config.get("top_p", 1.0)
        frequency_penalty = config.get("frequency_penalty", 0.0)
        presence_penalty = config.get("presence_penalty", 0.0)
        
        # Make the API call
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        
        # Extract and return the response text
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            return "No response generated."
        
    except Exception as e:
        # Handle errors
        error_message = f"Error creating chat completion: {str(e)}"
        print(error_message)
        return error_message


def stream_chat_completion(messages: List[Dict[str, str]], config=None):
    """
    Stream a chat completion using the specified messages and configuration.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        config: Optional configuration dictionary (uses default if not provided)
    
    Returns:
        A generator yielding completion chunks
    """
    # Convert dict messages to Message objects
    message_objects = [Message(msg["role"], msg["content"]) for msg in messages]
    
    # Create client with config
    client = ChatCompletionClient(config)
    
    # Get streaming completion
    return client.get_completion(message_objects, stream=True) 