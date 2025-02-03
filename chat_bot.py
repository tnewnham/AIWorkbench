#!/usr/bin/env python
"""
This program is an interactive terminal-based chat bot that leverages the OpenAI Assistant API.
It reproduces a classic terminal interface (with a retro flair) but uses modern styling via the rich library.
The program:
Validates configuration (like API keys),
Initializes a chat thread via the OpenAI Assistant API,
Repeatedly accepts user messages,
Sends those messages via the API, and
Polls for and prints the assistant's responses.
"""
import time
import sys
from rich.console import Console
from src.openai_assistant import (
    initialize_chat,
    send_user_message,
    start_run,
    poll_run_status_and_submit_outputs,
    ClientConfig
)
from openai import OpenAI  # Importing the OpenAI client library for polling responses
bender_assistant_id = ClientConfig.BENDER

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
    Welcome to ClassicChat
    A Modern Take on Retro Terminal Chatbot
    """
    console.print(welcome_banner, style="bold cyan")

    # Initialize a new chat thread using the API.
    chat_thread = initialize_chat()
    if not chat_thread or not hasattr(chat_thread, "id"):
        console.print("Error: Chat thread could not be initialized.", style="bold red")
        sys.exit(1)

    thread_identifier = chat_thread.id  # The chat thread identifier is used to send and retrieve messages.
    console.print("Chat session successfully started. Type 'exit' to leave the session.", style="bold green")

    # Main interactive loop.
    while True:
        user_message_text = prompt_user_for_input()
        if user_message_text.lower() in ["exit", "quit"]:
            console.print("Exiting chat session. Goodbye!", style="bold magenta")
            break

        # Send the user's message to the chat thread.
        send_user_message(chat_thread.id, user_message_text)
        run = start_run(chat_thread.id, bender_assistant_id)
        poll_run_status_and_submit_outputs(chat_thread.id, run.id)

    else:
        console.print("No response received from the assistant. Please try again later.", style="bold red")

def main():
    """
    Entry point for the interactive chat program.
    """
    interactive_chat_session()

if __name__ == "__main__":
    main()