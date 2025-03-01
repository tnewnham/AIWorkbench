#!/usr/bin/env python
"""
Terminal interface for the AIWorkbench application.
This module provides a text-based interface that leverages the OpenAI Assistant API.
It handles:
- Configuration validation
- Chat thread initialization
- User message processing
- Assistant response display
"""
import sys
import os
from rich.console import Console
from src.openai_assistant import (
    initialize_chat,
    send_user_message,
    start_run,
    poll_run_status_and_submit_outputs,
    ClientConfig
)
from dotenv import load_dotenv

def prompt_user_for_input(prompt_message="You> "):
    """
    Prompt the user to enter text.
    
    Args:
        prompt_message (str): The prompt text to display to the user
        
    Returns:
        str: A stripped string containing the user's input
    """
    try:
        user_input_text = input(prompt_message)
        return user_input_text.strip()
    except KeyboardInterrupt:
        # Allows graceful exit if the user interrupts using Ctrl+C
        return "exit"

def interactive_chat_session():
    """
    Initializes and runs an interactive terminal-based chat session.
    
    Performs the following steps:
    1. Validates that required environment variables are set
    2. Displays a welcome banner
    3. Initializes a chat thread using the OpenAI Assistant API
    4. Manages the message loop: prompt user → send message → receive response
    """
    console = Console()
    # Validate that all required configuration parameters are present.
    try:
        ClientConfig.validate_config()
    except EnvironmentError as config_error:
        console.print(f"Configuration Error: {config_error}", style="bold red")
        sys.exit(1)

    # Display a welcome banner
    welcome_banner = """
    ╔════════════════════════════════════════════════════════╗
    ║                   AIWorkbench Chat                     ║
    ║                                                        ║
    ║  Interactive terminal interface for OpenAI Assistant   ║
    ║  Type 'exit' or 'quit' to end the session              ║
    ╚════════════════════════════════════════════════════════╝
    """
    console.print(welcome_banner, style="bold cyan")

    # Initialize a new chat thread using the API.
    console.print("Initializing chat session...", style="yellow")
    chat_thread = initialize_chat()
    if not chat_thread or not hasattr(chat_thread, "id"):
        console.print("Error: Chat thread could not be initialized.", style="bold red")
        sys.exit(1)

    console.print("Chat session successfully started. Type 'exit' to leave the session.", style="bold green")

    # Main interactive loop.
    while True:
        user_message_text = prompt_user_for_input()
        if user_message_text.lower() in ["exit", "quit"]:
            console.print("Exiting chat session. Goodbye!", style="bold magenta")
            break
        
        if not user_message_text:
            continue
            
        # Send the user's message to the chat thread
        console.print("Sending message...", style="dim")
        send_user_message(chat_thread.id, user_message_text)
        
        # Run the assistant
        console.print("Waiting for response...", style="dim")
        run = start_run(chat_thread.id, ClientConfig.LEAD_ASSISTANT_ID)
        poll_run_status_and_submit_outputs(chat_thread.id, run.id)

def load_and_validate_environment():
    """
    Loads environment variables and validates that key variables are set.
    
    Returns:
        dict: A dictionary with all valid environment variables
    """
    console = Console()
    
    # Load environment variables
    load_dotenv()
    
    # Required variables for basic chat
    required_vars = ["OPENAI_API_KEY", "ASSISTANT_ID"]
    
    # Additional variables for analysis workflow
    analysis_vars = [
        "OUTLINE_AGENT_ID",
        "FORMULATE_QUESTIONS_AGENT_ID", 
        "VECTOR_STORE_SEARCH_AGENT_ID",
        "REVIEWER_AGENT_ID",
        "GOOGLE_GEMINI_API_KEY"
    ]
    
    # Check required variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        console.print(f"Error: Missing required environment variables: {', '.join(missing_vars)}", style="bold red")
        console.print("Please set these variables in your .env file or as environment variables.", style="yellow")
        sys.exit(1)
    
    # Check analysis variables and warn if missing
    missing_analysis_vars = [var for var in analysis_vars if not os.getenv(var)]
    if missing_analysis_vars:
        console.print(f"Warning: Missing environment variables for analysis workflow: {', '.join(missing_analysis_vars)}", style="bold yellow")
        console.print("Analysis features may not work properly.", style="yellow")
    
    # Return a dictionary with all environment variables
    return {var: os.getenv(var) for var in required_vars + analysis_vars if os.getenv(var)} 