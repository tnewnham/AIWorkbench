#!/usr/bin/env python
"""
This program provides a chat bot interface that leverages the OpenAI Assistant API.
It offers both a terminal-based interface and a graphical user interface.
The program:
- Validates configuration (like API keys),
- Initializes a chat thread via the OpenAI Assistant API,
- Accepts user messages,
- Sends those messages via the API, and
- Displays the assistant's responses.
"""
import sys
import argparse
from rich.console import Console
from src.openai_assistant import (
    initialize_chat,
    send_user_message,
    start_run,
    poll_run_status_and_submit_outputs,
    ClientConfig
)
import os
from dotenv import load_dotenv

def prompt_user_for_input(prompt_message="You> "):
    """
    Prompt the user to enter text.
    Returns:
    A stripped string containing the user's input.
    """
    try:
        user_input_text = input(prompt_message)
        return user_input_text.strip()
    except KeyboardInterrupt:
        # Allows graceful exit if the user interrupts using Ctrl+C
        return "exit"

def interactive_chat_session():
    """
    Initializes an interactive chat session.
    Performs the following steps:
    1. Validates that required environment variables are set
    2. Prints a classic terminal-style welcome banner
    3. Initializes a chat thread using the OpenAI Assistant API
    Repeatedly prompts the user for input, sends their message, and polls for an assistant response
    """
    console = Console()
    # Validate that all required configuration parameters are present.
    try:
        ClientConfig.validate_config()
    except EnvironmentError as config_error:
        console.print(f"Configuration Error: {config_error}", style="bold red")
        sys.exit(1)

    # Display a retro-style welcome banner.ts
    welcome_banner = """
    Hello User
    I am a skillful with chatbot some pre configured rag extraction tasks
    """
    console.print(welcome_banner, style="bold cyan")


    # Initialize a new chat thread using the API.
    chat_thread = initialize_chat()
    if not chat_thread or not hasattr(chat_thread, "id"):
        console.print("Error: Chat thread could not be initialized.", style="bold red")
        sys.exit(1)

    #thread_identifier = chat_thread.id  # The chat thread identifier is used to send and retrieve messages.
    console.print("Chat session successfully started. Type 'exit' to leave the session.", style="bold green")

    # Main interactive loop.
    while True:
        user_message_text = prompt_user_for_input()
        if user_message_text.lower() in ["exit", "quit"]:
            console.print("Exiting chat session. Goodbye!", style="bold magenta")
            break
        # Send the user's message to the chat thread.
        send_user_message(chat_thread.id, user_message_text)
        run = start_run(chat_thread.id, ClientConfig.BENDER)
        poll_run_status_and_submit_outputs(chat_thread.id, run.id)
    else:
        console.print("No response received from the assistant. Please try again later.", style="bold red")

def load_and_validate_environment():
    """
    Loads environment variables and validates that key variables are set.
    Returns a dictionary with key environment variables.
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

def main():
    """
    Entry point for the interactive chat program.
    Parses command-line arguments to determine whether to use the GUI or terminal interface.
    """
    # Load environment variables for API keys
    load_dotenv()
    
    # Validate API keys
    console = Console()
    if not os.getenv("OPENAI_API_KEY"):
        console.print("Error: OPENAI_API_KEY environment variable is not set.", style="bold red")
        sys.exit(1)
    
    # Initialize lead assistant config first
    try:
        from src.assistant_config import LeadAssistantConfig
        lead_assistant_config = LeadAssistantConfig()
        
        # Set the lead assistant ID in the ClientConfig
        from src.openai_assistant import ClientConfig
        ClientConfig.LEAD_ASSISTANT_ID = lead_assistant_config.LEAD_ASSISTANT_ID
        ClientConfig.BENDER = lead_assistant_config.LEAD_ASSISTANT_ID  # Use lead assistant as default
    except Exception as e:
        console = Console()
        console.print(f"Warning: Failed to initialize Lead Assistant: {e}", style="bold yellow")
    
    parser = argparse.ArgumentParser(description="Chat bot using OpenAI Assistant API")
    parser.add_argument(
        "--terminal", "-t", 
        action="store_true", 
        help="Use terminal interface instead of GUI"
    )
    args = parser.parse_args()
    
    if args.terminal:
        # Use terminal interface
        interactive_chat_session()
    else:
        # Use GUI interface
        try:
            from src.chat_ui_qt import main as gui_main
            gui_main()
        except ImportError as e:
            console = Console()
            console.print(f"Error loading GUI: {e}", style="bold red")
            console.print("Falling back to terminal interface.", style="bold yellow")
            interactive_chat_session()

if __name__ == "__main__":
    main()