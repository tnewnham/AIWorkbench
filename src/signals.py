#!/usr/bin/env python
"""
Global signals for application-wide communication
"""
from PyQt5.QtCore import QObject, pyqtSignal

class GlobalSignals(QObject):
    """Global signals for application-wide communication"""
    # Signal when analysis is requested - changed to accept an object (dictionary)
    analysis_request = pyqtSignal(object)
    
    # Signal to set the assistant ID
    set_assistant_signal = pyqtSignal(str)
    
    # Signal to set the chat mode (assistant or completion)
    set_chat_mode_signal = pyqtSignal(str)
    
    # Signal to set the chat completion configuration
    set_chat_completion_config_signal = pyqtSignal(str)
    
    # Signal for updating the status bar message
    status_message = pyqtSignal(str)
    
    # Signal for keyboard shortcuts
    keyboard_shortcut = pyqtSignal(str)
    
    # Signal for tool outputs (name, result)
    tool_output = pyqtSignal(str, object)
    
    # Signal for when the theme changes
    theme_changed = pyqtSignal(str)

# Create a global instance
global_signals = GlobalSignals() 