#!/usr/bin/env python
"""
Main entry point for the AIWorkbench application.
This script launches the application with support for both Assistant API and Chat Completion API.
It supports both terminal mode and GUI mode based on command-line arguments.
"""

import sys
import os
import platform
import argparse
from rich.console import Console
from dotenv import load_dotenv

def main():
    """
    Main entry point for the AIWorkbench application.
    Parses command-line arguments to determine whether to use the GUI or terminal interface.
    """
    # Load environment variables for API keys
    load_dotenv()
    
    console = Console()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="AIWorkbench - Advanced AI Interface")
    parser.add_argument(
        "--terminal", "-t", 
        action="store_true", 
        help="Use terminal interface instead of GUI"
    )
    args = parser.parse_args()
    
    # Validate API keys
    if not os.getenv("OPENAI_API_KEY"):
        console.print("Error: OPENAI_API_KEY environment variable is not set.", style="bold red")
        sys.exit(1)
    
    # Initialize lead assistant config
    try:
        from src.assistant_config import LeadAssistantConfig
        from src.assistant_config import WritingStyleProfilerConfig
        from src.openai_assistant import ClientConfig
        
        lead_assistant_config = LeadAssistantConfig()
        style_profiler_config = WritingStyleProfilerConfig()
        # Set the lead assistant ID in the ClientConfig
        ClientConfig.LEAD_ASSISTANT_ID = lead_assistant_config.LEAD_ASSISTANT_ID
        ClientConfig.STYLE_PROFILER_AGENT_ID = style_profiler_config.STYLE_PROFILER_AGENT_ID
        # Load other configuration settings
        ClientConfig.load_config()
    except Exception as e:
        console.print(f"Warning: Failed to initialize Assistants: {e}", style="bold yellow")
    
    if args.terminal:
        # Use terminal interface
        from src.terminal_interface import interactive_chat_session
        interactive_chat_session()
    else:
        # Set environment variable to indicate GUI mode
        os.environ["GUI_MODE"] = "1"
        
        # Set application details for proper taskbar icon handling in Windows
        if platform.system() == "Windows":
            try:
                import ctypes
                # Set app ID for Windows taskbar
                app_id = "AIWorkbench.1.0"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
                print(f"Set Windows AppUserModelID to: {app_id}")
            except Exception as e:
                print(f"Failed to set application ID: {e}")
        
        try:
            # Import GUI components here to avoid loading them if using terminal mode
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtGui import QIcon
            from src.main_window import create_main_window
            
            # Create main window and application
            window, app = create_main_window()
            
            # Add icon if available
            icon_path = os.path.join(os.path.dirname(__file__), "taskbarIcon.png")
            if os.path.exists(icon_path):
                print(f"Setting icon from: {icon_path}")
                app.setWindowIcon(QIcon(icon_path))
                window.setWindowIcon(QIcon(icon_path))
            else:
                print("Icon not found, using default")
                # Use a built-in icon as fallback
                icon = app.style().standardIcon(QApplication.style().SP_ComputerIcon)
                app.setWindowIcon(icon)
                window.setWindowIcon(icon)
            
            # Show the window
            window.show()    
            
            # Start the application
            sys.exit(app.exec_())

        
        except ImportError as e:
            console.print(f"Error loading GUI: {e}", style="bold red")
            console.print("Falling back to terminal interface.", style="bold yellow")
            from src.terminal_interface import interactive_chat_session
            interactive_chat_session()

    

        

if __name__ == "__main__":
    main() 