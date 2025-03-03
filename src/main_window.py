#!/usr/bin/env python
"""
Main window for the OpenAI Chat Interface.
This module provides the main application window and UI components.
"""

import sys
import os
import platform
from typing import List, Dict, Any, Optional
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QFrame, QStackedWidget, QStyle, QPushButton
)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QIcon, QFont

from src.assistants_panel import AssistantsPanel
from src.vector_store_panel import VectorStorePanel
from src.chat_completion_panel import ChatCompletionPanel
from src.chat_ui_qt import ChatTab, VSCodeStyleHelper
from src.windows_style_helper import WindowsStyleHelper

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
        
        # Apply additional scrollbar styling to ensure rounded corners
        self.setStyleSheet(f"""
            QScrollBar:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR} !important;
                width: 8px !important;
                margin: 0px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS} !important;
            }}
            QScrollBar::handle:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR} !important;
                min-height: 30px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS} !important;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_HOVER_COLOR} !important;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px !important;
                border: none !important;
                background: none !important;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none !important;
                border: none !important;
            }}
            QScrollBar:horizontal {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR} !important;
                height: 8px !important;
                margin: 0px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS} !important;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR} !important;
                min-width: 30px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS} !important;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_HOVER_COLOR} !important;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px !important;
                border: none !important;
                background: none !important;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none !important;
                border: none !important;
            }}
            QScrollBar::corner {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR} !important;
                border: none !important;
            }}
        """)
        
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
        
        # Set the initial sizes (give more room to the sidebar)
        splitter.setSizes([650, 580])
        
        main_layout.addWidget(splitter)
    
    def _setup_sidebar(self):
        """Set up the sidebar menu panels"""
        self.sidebar = QTabWidget()
        self.sidebar.setTabPosition(QTabWidget.West)  # Tabs on the left
        self.sidebar.setMovable(True)
        
        # Set minimum width for the sidebar
        self.sidebar.setMinimumWidth(300)
        
        # Add assistant panel
        self.assistants_panel = AssistantsPanel()
        self.sidebar.addTab(self.assistants_panel, "Assistants")
        
        # Add vector store management panel
        self.vector_store_panel = VectorStorePanel()
        self.sidebar.addTab(self.vector_store_panel, "Vector Stores")
        
        # Add chat completions panel
        self.chat_completion_panel = ChatCompletionPanel()
        self.sidebar.addTab(self.chat_completion_panel, "Chat Models")
        
        # Apply scrollbar styling to all panels
        scrollbar_style = f"""
            QScrollBar:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR} !important;
                width: 8px !important;
                margin: 0px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS} !important;
            }}
            QScrollBar::handle:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR} !important;
                min-height: 30px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS} !important;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_HOVER_COLOR} !important;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px !important;
                border: none !important;
                background: none !important;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none !important;
                border: none !important;
            }}
            QScrollBar:horizontal {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR} !important;
                height: 8px !important;
                margin: 0px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS} !important;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR} !important;
                min-width: 30px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS} !important;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_HOVER_COLOR} !important;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px !important;
                border: none !important;
                background: none !important;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none !important;
                border: none !important;
            }}
            QScrollBar::corner {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR} !important;
                border: none !important;
            }}
        """
        
        # Apply style to each panel
        self.assistants_panel.setStyleSheet(scrollbar_style)
        self.vector_store_panel.setStyleSheet(scrollbar_style)
        self.chat_completion_panel.setStyleSheet(scrollbar_style)
        self.sidebar.setStyleSheet(scrollbar_style)
        
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