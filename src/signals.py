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

# Create a singleton instance
global_signals = GlobalSignals() 