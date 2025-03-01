"""
Main window implementation for the AIWorkbench application.
This module provides the main application window with all required panels.
"""

import sys
import os
import platform
from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QFrame, QStackedWidget, QStyle
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont

from src.assistants_panel import AssistantsPanel
from src.vector_store_panel import VectorStorePanel
from src.chat_completion_panel import ChatCompletionPanel
from src.chat_ui_qt import ChatTab, VSCodeStyleHelper, WindowsStyleHelper

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Set up window
        self.setWindowTitle("AIWorkbench")
        self.resize(1200, 800)
        
        # Set dark title bar on Windows
        if platform.system() == "Windows":
            # Wait for window to be created and then set dark title bar
            QTimer.singleShot(100, lambda: WindowsStyleHelper.set_dark_title_bar(int(self.winId())))
        
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Main chat area
        self.chat_tab = ChatTab()
        
        # Left sidebar (formerly right sidebar)
        left_sidebar = self._setup_sidebar()
        
        # Add splitter to make the sidebar resizable
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_sidebar)
        splitter.addWidget(self.chat_tab)
        
        # Set the initial sizes (give more room to the chat tab)
        splitter.setSizes([500, 700])
        
        main_layout.addWidget(splitter)
    
    def _setup_sidebar(self):
        """Set up the sidebar menu panels"""
        self.sidebar = QTabWidget()
        self.sidebar.setTabPosition(QTabWidget.West)  # Tabs on the left
        self.sidebar.setMovable(True)
        
        # Add assistant panel
        self.assistants_panel = AssistantsPanel()
        self.sidebar.addTab(self.assistants_panel, "Assistants")
        
        # Add chat completion panel
        self.chat_completion_panel = ChatCompletionPanel()
        self.sidebar.addTab(self.chat_completion_panel, "Chat Completion")
        
        # Add vector store panel
        self.vector_store_panel = VectorStorePanel()
        self.sidebar.addTab(self.vector_store_panel, "Vector Store")
        
        # Set initial tab
        self.sidebar.setCurrentIndex(0)
        
        return self.sidebar

def create_main_window():
    """Create and return the main application window"""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("AIWorkbench")
    app.setApplicationDisplayName("AIWorkbench")
    
    # Apply styles
    VSCodeStyleHelper.apply_styles(app)
    
    # Create main window
    window = MainWindow()
    
    return window, app 