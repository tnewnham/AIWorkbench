#!/usr/bin/env python
"""
Global signals for application-wide communication
"""
from PyQt5.QtCore import QObject, pyqtSignal

class GlobalSignals(QObject):
    """Global signals for cross-component communication"""
    # Signal for requesting analysis from anywhere in the app
    # Emits: dict of function arguments
    analysis_request = pyqtSignal(dict)

    # Signals for inter-component communication
    refresh_signal = pyqtSignal()
    progress_signal = pyqtSignal(str, int)  # message, percentage
    set_assistant_signal = pyqtSignal(str)  # assistant_id

# Create a global instance
global_signals = GlobalSignals() 