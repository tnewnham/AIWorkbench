#!/usr/bin/env python
"""
This module provides a GUI interface for the OpenAI Assistant chat bot using PyQt5.
It implements a Matrix-themed chat interface with support for markdown rendering,
JSON formatting, and side panels with placeholder tabs.
"""
import sys
import threading
import queue
import time
import json
import os
from typing import List, Tuple, Optional, Dict, Any
import platform
import ctypes

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QTabWidget, 
                           QLabel, QScrollArea, QFrame, QStackedWidget, QSizePolicy, QInputDialog, QDialog, QStyle, QButtonGroup)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
import markdown2

# Import the WindowsStyleHelper for dark title bars
from src.windows_style_helper import WindowsStyleHelper

# VSCode dark theme styling
class VSCodeStyleHelper:
    """Helper class for Visual Studio Code dark theme styling"""
    # VS Code dark theme colors
    BG_COLOR = "#212121"  # Main background
    SIDEBAR_BG_COLOR = "#252526"  # Sidebar background
    TEXT_COLOR = "#D4D4D4"  # Standard text
    ACCENT_COLOR = "#007ACC"  # VS Code blue
    BUTTON_COLOR = "#2D2D30"
    BUTTON_HOVER_COLOR = "#3E3E42"
    USER_BG_COLOR = "#303030"  # User messages
    ASSISTANT_BG_COLOR = "#212121"  # Assistant messages
    BORDER_COLOR = "#3E3E42"  # Border color
    
    # Scrollbar colors
    SCROLLBAR_BG_COLOR = "#212121"  # Same as main background
    SCROLLBAR_HANDLE_COLOR = "#424242"  # Subtle grey
    SCROLLBAR_HANDLE_HOVER_COLOR = "#686868"  # Lighter grey on hover
    
    # Border radius values
    LARGE_RADIUS = "10px"    # Used for panels and scrollbars
    MEDIUM_RADIUS = "8px"    # Used for mid-size elements
    SMALL_RADIUS = "6px"     # Used for smaller elements
    
    @staticmethod
    def apply_styles(app):
        """Apply VS Code dark theme to the application"""
        from PyQt5.QtGui import QPalette, QColor
        from PyQt5.QtCore import Qt
        
        app.setStyle("Fusion")
        
        # Set the dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(VSCodeStyleHelper.BG_COLOR))
        palette.setColor(QPalette.WindowText, QColor(VSCodeStyleHelper.TEXT_COLOR))
        palette.setColor(QPalette.Base, QColor(VSCodeStyleHelper.BG_COLOR))
        palette.setColor(QPalette.AlternateBase, QColor(VSCodeStyleHelper.SIDEBAR_BG_COLOR))
        palette.setColor(QPalette.ToolTipBase, QColor(VSCodeStyleHelper.SIDEBAR_BG_COLOR))
        palette.setColor(QPalette.ToolTipText, QColor(VSCodeStyleHelper.TEXT_COLOR))
        palette.setColor(QPalette.Text, QColor(VSCodeStyleHelper.TEXT_COLOR))
        palette.setColor(QPalette.Button, QColor(VSCodeStyleHelper.BUTTON_COLOR))
        palette.setColor(QPalette.ButtonText, QColor(VSCodeStyleHelper.TEXT_COLOR))
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(VSCodeStyleHelper.ACCENT_COLOR))
        palette.setColor(QPalette.Highlight, QColor(VSCodeStyleHelper.ACCENT_COLOR))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(palette)
        
        # Add custom stylesheet for scrollbars - using f-strings for better syntax
        app.setStyleSheet(f"""
            /* Scrollbar styling */
            QScrollBar:vertical,
            QTextEdit QScrollBar:vertical,
            QTableWidget QScrollBar:vertical,
            QListWidget QScrollBar:vertical,
            QTreeView QScrollBar:vertical,
            QScrollArea QScrollBar:vertical,
            *::vertical-scrollbar {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR} !important;
                width: 8px !important;
                margin: 0px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS} !important;
            }}
            
            QScrollBar::handle:vertical,
            QTextEdit QScrollBar::handle:vertical, 
            QTableWidget QScrollBar::handle:vertical,
            QListWidget QScrollBar::handle:vertical,
            QTreeView QScrollBar::handle:vertical,
            QScrollArea QScrollBar::handle:vertical,
            *::vertical-scrollbar-handle {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR} !important;
                min-height: 30px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS} !important;
            }}
            
            QScrollBar::handle:vertical:hover,
            QTextEdit QScrollBar::handle:vertical:hover,
            QTableWidget QScrollBar::handle:vertical:hover,
            QListWidget QScrollBar::handle:vertical:hover,
            QTreeView QScrollBar::handle:vertical:hover,
            QScrollArea QScrollBar::handle:vertical:hover,
            *::vertical-scrollbar-handle:hover {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_HOVER_COLOR} !important;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QTextEdit QScrollBar::add-line:vertical, QTextEdit QScrollBar::sub-line:vertical,
            QTableWidget QScrollBar::add-line:vertical, QTableWidget QScrollBar::sub-line:vertical,
            QListWidget QScrollBar::add-line:vertical, QListWidget QScrollBar::sub-line:vertical,
            QTreeView QScrollBar::add-line:vertical, QTreeView QScrollBar::sub-line:vertical,
            QScrollArea QScrollBar::add-line:vertical, QScrollArea QScrollBar::sub-line:vertical {{
                height: 0px !important;
            }}
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QTextEdit QScrollBar::add-page:vertical, QTextEdit QScrollBar::sub-page:vertical,
            QTableWidget QScrollBar::add-page:vertical, QTableWidget QScrollBar::sub-page:vertical,
            QListWidget QScrollBar::add-page:vertical, QListWidget QScrollBar::sub-page:vertical,
            QTreeView QScrollBar::add-page:vertical, QTreeView QScrollBar::sub-page:vertical,
            QScrollArea QScrollBar::add-page:vertical, QScrollArea QScrollBar::sub-page:vertical {{
                background: none !important;
            }}
            
            /* Horizontal scrollbars */
            QScrollBar:horizontal,
            QTextEdit QScrollBar:horizontal,
            QTableWidget QScrollBar:horizontal,
            QListWidget QScrollBar:horizontal,
            QTreeView QScrollBar:horizontal,
            QScrollArea QScrollBar:horizontal,
            *::horizontal-scrollbar {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR} !important;
                height: 8px !important;
                margin: 0px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS} !important;
            }}
            
            QScrollBar::handle:horizontal,
            QTextEdit QScrollBar::handle:horizontal,
            QTableWidget QScrollBar::handle:horizontal,
            QListWidget QScrollBar::handle:horizontal,
            QTreeView QScrollBar::handle:horizontal,
            QScrollArea QScrollBar::handle:horizontal,
            *::horizontal-scrollbar-handle {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR} !important;
                min-width: 30px !important;
                border: none !important;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS} !important;
            }}
            
            QScrollBar::handle:horizontal:hover,
            QTextEdit QScrollBar::handle:horizontal:hover,
            QTableWidget QScrollBar::handle:horizontal:hover,
            QListWidget QScrollBar::handle:horizontal:hover,
            QTreeView QScrollBar::handle:horizontal:hover,
            QScrollArea QScrollBar::handle:horizontal:hover,
            *::horizontal-scrollbar-handle:hover {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_HOVER_COLOR} !important;
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
            QTextEdit QScrollBar::add-line:horizontal, QTextEdit QScrollBar::sub-line:horizontal,
            QTableWidget QScrollBar::add-line:horizontal, QTableWidget QScrollBar::sub-line:horizontal,
            QListWidget QScrollBar::add-line:horizontal, QListWidget QScrollBar::sub-line:horizontal,
            QTreeView QScrollBar::add-line:horizontal, QTreeView QScrollBar::sub-line:horizontal,
            QScrollArea QScrollBar::add-line:horizontal, QScrollArea QScrollBar::sub-line:horizontal {{
                width: 0px !important;
            }}
            
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal,
            QTextEdit QScrollBar::add-page:horizontal, QTextEdit QScrollBar::sub-page:horizontal,
            QTableWidget QScrollBar::add-page:horizontal, QTableWidget QScrollBar::sub-page:horizontal,
            QListWidget QScrollBar::add-page:horizontal, QListWidget QScrollBar::sub-page:horizontal,
            QTreeView QScrollBar::add-page:horizontal, QTreeView QScrollBar::sub-page:horizontal,
            QScrollArea QScrollBar::add-page:horizontal, QScrollArea QScrollBar::sub-page:horizontal {{
                background: none !important;
            }}
            
            /* Menu styling */
            QMenu {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 5px;
            }}
            
            QMenu::item {{
                padding: 5px 30px 5px 20px;
                border-radius: {VSCodeStyleHelper.SMALL_RADIUS};
            }}
            
            QMenu::item:selected {{
                background-color: {VSCodeStyleHelper.ACCENT_COLOR};
                color: white;
            }}
        """)

# Import the necessary components from the existing code
from src.openai_assistant import (
    initialize_chat,
    send_user_message,
    start_run,
    poll_run_status_and_submit_outputs,
    ClientConfig,
    pretty_print,
    send_assistant_message
)
from src.workflow_manager import WorkflowManager
from src.signals import global_signals
from src.vector_store_panel import VectorStorePanel
from src.assistants_panel import AssistantsPanel

class SignalHandler(QObject):
    """Signal handler for thread communication"""
    message_signal = pyqtSignal(str, str, object)
    enable_input_signal = pyqtSignal()

class MessageWidget(QFrame):
    """Widget to display a chat message with appropriate styling based on role"""
    
    def __init__(self, role, content, formatted_content=None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        
        # Set styling based on role
        is_user = role.lower() == "user"
        bg_color = VSCodeStyleHelper.USER_BG_COLOR if is_user else VSCodeStyleHelper.ASSISTANT_BG_COLOR
        text_color = VSCodeStyleHelper.TEXT_COLOR
        
        # Set border only for user messages, not for assistant messages
        border_style = f"border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};" if is_user else "border: none;"
        
        # Apply styling
        self.setStyleSheet(f"""
            MessageWidget {{
                background-color: {bg_color};
                {border_style}
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                margin: 5px;
                padding: 5px;
            }}
            QLabel {{
                color: {text_color};
                background-color: transparent;
            }}
            QTextEdit {{
                background-color: {bg_color};
                color: {text_color};
                border: none;
                padding: 0px;
                margin: 0px;
                border-radius: 0px;
            }}
            QTextEdit QScrollBar:vertical {{
                background-color: {bg_color};
                width: 10px;
                margin: 0px;
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
            }}
            QTextEdit QScrollBar::handle:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR};
                min-height: 20px;
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
            }}
            QTextEdit QScrollBar::handle:vertical:hover {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_HOVER_COLOR};
            }}
            QTextEdit QScrollBar::add-line:vertical, QTextEdit QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add role label
        role_label = QLabel(f"{role.upper()}:")
        role_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(role_label)
        
        # Process and add content
        try:
            # Try parsing as JSON
            json_content = json.loads(content)
            json_str = json.dumps(json_content, indent=2)
            
            content_widget = QTextEdit()
            content_widget.setReadOnly(True)
            content_widget.setFont(QFont("Courier New", 10))
            content_widget.setText(json_str)
            
            # Remove any additional frame or border
            content_widget.setFrameShape(QFrame.NoFrame)
            content_widget.setLineWidth(0)
            
            # Calculate approximate height based on content
            line_count = json_str.count('\n') + 1
            content_height = min(max(line_count * 20, 100), 500)  # Between 100 and 500 pixels
            content_widget.setMinimumHeight(content_height)
            
            # Make it expand vertically with content
            content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            content_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            layout.addWidget(content_widget)
            
        except json.JSONDecodeError:
            # Check for markdown
            if "```" in content or "#" in content or "*" in content:
                # Convert markdown to HTML
                html_content = markdown2.markdown(content)
                
                content_widget = QTextEdit()
                content_widget.setReadOnly(True)
                content_widget.setHtml(html_content)
                
                # Remove any additional frame or border
                content_widget.setFrameShape(QFrame.NoFrame)
                content_widget.setLineWidth(0)
                
                # Calculate height based on content
                line_count = content.count('\n') + 1
                content_height = min(max(line_count * 20, 100), 600)  # Between 100 and 600 pixels
                content_widget.setMinimumHeight(content_height)
                
                # Make it expand vertically with content
                content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                content_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                
                layout.addWidget(content_widget)
                
            else:
                # Regular text
                content_widget = QTextEdit()
                content_widget.setReadOnly(True)
                content_widget.setText(content)
                
                # Remove any additional frame or border
                content_widget.setFrameShape(QFrame.NoFrame)
                content_widget.setLineWidth(0)
                
                # Calculate height based on content
                line_count = content.count('\n') + 1
                content_height = min(max(line_count * 20, 100), 400)  # Between 100 and 400 pixels
                content_widget.setMinimumHeight(content_height)
                
                # Make it expand vertically with content
                content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                content_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                
                layout.addWidget(content_widget)
        
        # Add any formatted content (files, URLs)
        if formatted_content:
            for content_type, content_value in formatted_content:
                if content_type == "file":
                    file_label = QLabel(f"File: {content_value}")
                    file_label.setStyleSheet("color: #00FFCC;")
                    layout.addWidget(file_label)
                elif content_type == "url":
                    url_label = QLabel(f"Image URL: {content_value}")
                    url_label.setStyleSheet("color: #00FFCC;")
                    layout.addWidget(url_label)
        
        # Set layout margins
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

class ChatArea(QScrollArea):
    """Scrollable area for chat messages"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        
        # Remove the border frame
        self.setFrameShape(QFrame.NoFrame)
        
        # Container widget for messages
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(10)
        
        self.setWidget(self.container)
        self.messages = []
        
    def add_message(self, role, content, formatted_content=None):
        """Add a message to the chat area"""
        message_widget = MessageWidget(role, content, formatted_content)
        self.layout.addWidget(message_widget)
        self.messages.append((role, content, formatted_content))
        
        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        """Scroll to the bottom of the chat area"""
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
    
    def clear_chat(self):
        """Clear all messages"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.messages = []

    def get_last_system_message(self):
        """Get the text of the last system message"""
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i][0] == "system":
                return self.messages[i][1]
        return ""

class SidePanel(QWidget):
    """Side panel with vertical buttons and stacked content"""
    
    def __init__(self, position, parent=None):
        super().__init__(parent)
        is_right_panel = position == "right"
        
        # Create a container widget for the entire panel
        self.container = QWidget()
        self.container.setStyleSheet(f"""
            background-color: {VSCodeStyleHelper.BG_COLOR};
            border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
            border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
        """)
        
        # Main layout for the panel
        main_container_layout = QVBoxLayout(self.container)
        main_container_layout.setContentsMargins(10, 10, 10, 10)
        
        # Main layout for the panel
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(self.container)
        
        # Create a horizontal layout for buttons and content
        panel_layout = QHBoxLayout()
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        
        # Create vertical button layout
        self.button_layout = QVBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(1)
        self.button_layout.setAlignment(Qt.AlignTop)
        
        # Button widget container
        button_widget = QWidget()
        button_widget.setLayout(self.button_layout)
        button_widget.setFixedWidth(120)  # Make wider to accommodate "Vector Stores" text
        button_widget.setStyleSheet(f"""
            background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
            border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
            border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
            padding: 5px;
        """)
        
        # Create stacked widget for content
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"""
            background-color: {VSCodeStyleHelper.BG_COLOR};
            border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
            border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
        """)
        
        # Add the button panel and content stack to the panel layout
        # For right panel, add content first then buttons
        if is_right_panel:
            panel_layout.addWidget(self.content_stack)
            panel_layout.addWidget(button_widget)
        else:
            panel_layout.addWidget(button_widget)
            panel_layout.addWidget(self.content_stack)
        
        # Add panel layout to main container layout
        main_container_layout.addLayout(panel_layout)
        
        # Keep track of buttons and their indexes
        self.buttons = []
        self.active_index = -1
        
        # Set default width
        self.setMinimumWidth(250)
        
        # When button is clicked, show the corresponding page
        self.button_group = QButtonGroup(self)
        self.button_group.buttonClicked.connect(
            lambda button: self._on_button_clicked(self.buttons.index(button))
        )
        
        # Add default pages
        self.add_page("Settings", f"{position} Settings Panel")
        self.add_page("History", f"{position} History Panel")
        self.add_page("Help", f"{position} Help Panel")
        
        # Select first button by default
        if self.button_layout.count() > 0:
            button = self.button_layout.itemAt(0).widget()
            button.setChecked(True)
    
    def add_page(self, title, content_text):
        """Add a new page with text content to the panel"""
        # Create button
        button = QPushButton(title)
        button.setCheckable(True)
        button.setMinimumHeight(40)
        
        # Add consistent styling to the button
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                padding: 8px;
                text-align: left;
                margin: 2px 0px;
            }}
            QPushButton:checked {{
                background-color: {VSCodeStyleHelper.ACCENT_COLOR};
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover:!checked {{
                background-color: {VSCodeStyleHelper.BORDER_COLOR};
            }}
        """)
        
        # Add to button layout
        self.button_layout.addWidget(button)
        button_index = len(self.buttons)
        self.buttons.append(button)
        
        # Connect button to switch pages
        button.clicked.connect(lambda checked, idx=button_index: self._on_button_clicked(idx))
        
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Create text area for content
        content_area = QTextEdit()
        content_area.setReadOnly(True)
        content_area.setPlainText(content_text)
        # Apply consistent style to the content area
        content_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 8px;
            }}
            QScrollBar:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR};
                width: 12px;
                margin: 3px 3px 3px 3px;
                border-radius: {VSCodeStyleHelper.SMALL_RADIUS};
            }}
            QScrollBar::handle:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR};
                min-height: 20px;
                border-radius: {VSCodeStyleHelper.SMALL_RADIUS};
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_HOVER_COLOR};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        content_layout.addWidget(content_area)
        
        # Add to stack
        self.content_stack.addWidget(content_widget)
        
        # If this is the first button, activate it
        if button_index == 0:
            button.setChecked(True)
            self.active_index = 0
            self.content_stack.setCurrentIndex(0)
        
        return button_index
    
    def _on_button_clicked(self, index):
        """Handle button clicks to switch content pages"""
        # First uncheck all buttons
        for i, btn in enumerate(self.buttons):
            if i != index:
                btn.setChecked(False)
        
        # Ensure the clicked button is checked
        self.buttons[index].setChecked(True)
        
        # Show the corresponding content
        self.content_stack.setCurrentIndex(index)
        self.active_index = index
    
    def add_custom_page(self, title, widget):
        """Add a custom widget page to the panel"""
        # Create button
        button = QPushButton(title)
        button.setCheckable(True)
        button.setMinimumHeight(40)
        
        # Add consistent styling to the button
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                padding: 8px;
                text-align: left;
                margin: 2px 0px;
            }}
            QPushButton:checked {{
                background-color: {VSCodeStyleHelper.ACCENT_COLOR};
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover:!checked {{
                background-color: {VSCodeStyleHelper.BORDER_COLOR};
            }}
        """)
        
        # Add to button layout
        self.button_layout.addWidget(button)
        button_index = len(self.buttons)
        self.buttons.append(button)
        
        # Connect button to switch pages
        button.clicked.connect(lambda checked, idx=button_index: self._on_button_clicked(idx))
        
        # Add to stack
        self.content_stack.addWidget(widget)
        
        # If this is the first button, activate it
        if button_index == 0:
            button.setChecked(True)
            self.active_index = 0
            self.content_stack.setCurrentIndex(0)
        
        return button_index

class ChatInputTextEdit(QTextEdit):
    """Custom text edit for chat input with Ctrl+Enter handling"""
    
    def __init__(self, send_callback, parent=None):
        super().__init__(parent)
        self.send_callback = send_callback
        # Apply VSCode-style rounded corners
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {VSCodeStyleHelper.USER_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 8px;
            }}
            QScrollBar:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR};
                width: 12px;
                margin: 3px 3px 3px 3px;
                border-radius: {VSCodeStyleHelper.SMALL_RADIUS};
            }}
            QScrollBar::handle:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR};
                min-height: 20px;
                border-radius: {VSCodeStyleHelper.SMALL_RADIUS};
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_HOVER_COLOR};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # Check for Ctrl+Enter (Return)
        if event.modifiers() == Qt.ControlModifier and (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter):
            self.send_callback()
            return
        
        # For all other key presses, use the default handler
        super().keyPressEvent(event)

class ChatTab(QWidget):
    """Main chat interface tab"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up layout
        layout = QVBoxLayout(self)
        
        # Chat display area
        self.chat_display = ChatArea()
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        # Add margins to make the input box less wide, matching user message boxes
        input_layout.setContentsMargins(13, 0, 13, 0)
        
        # Use our custom TextEdit with a callback to the send method
        self.input_box = ChatInputTextEdit(self._send_message)
        self.input_box.setMaximumHeight(80)
        self.input_box.setPlaceholderText("Type your message here... (Ctrl+Enter to send)")
        # Set the input box background color to match user message blocks
        self.input_box.setStyleSheet(f"""
            QTextEdit {{
                background-color: {VSCodeStyleHelper.USER_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 5px;
            }}
        """)
        input_layout.addWidget(self.input_box)
        
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("send_button")  # Set object name for CSS targeting
        self.send_button.clicked.connect(self._send_message)
        # Make the send button narrower
        self.send_button.setFixedWidth(60)
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {VSCodeStyleHelper.BUTTON_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: none;
                border-radius: {VSCodeStyleHelper.SMALL_RADIUS};
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {VSCodeStyleHelper.BUTTON_HOVER_COLOR};
            }}
        """)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Set up signal handler for thread communication
        self.signal_handler = SignalHandler()
        self.signal_handler.message_signal.connect(self._add_message)
        self.signal_handler.enable_input_signal.connect(self._enable_input)
        
        # Initialize state
        self.chat_thread = None
        self.processing = False
        
        # Add workflow manager
        self.workflow_manager = WorkflowManager()
        self.workflow_manager.signals.progress.connect(self._on_workflow_progress)
        self.workflow_manager.signals.result.connect(self._on_workflow_result)
        self.workflow_manager.signals.error.connect(self._on_workflow_error)
        self.workflow_manager.signals.log.connect(self._on_workflow_log)
        
        # Connect to global signals
        global_signals.analysis_request.connect(self._handle_analysis_request)
        global_signals.set_assistant_signal.connect(self.set_assistant)
        global_signals.set_chat_mode_signal.connect(self.set_chat_mode)
        global_signals.set_chat_completion_config_signal.connect(self.set_chat_completion_config)
        
        # Initialize with the lead assistant
        self.current_assistant_id = ClientConfig.LEAD_ASSISTANT_ID
        
        # Chat mode (assistant or completion)
        self.chat_mode = "assistant"
        
        # Initialize chat history for chat completion mode
        self.chat_history = None
        self.current_completion_config = None
        
        # Start initialization thread
        threading.Thread(target=self._initialize_chat, daemon=True).start()
    
    def _initialize_chat(self):
        """Initialize chat in a background thread"""
        try:
            # Initialize the lead assistant first if not already done
            if not ClientConfig.LEAD_ASSISTANT_ID:
                from src.assistant_config import LeadAssistantConfig
                lead_assistant_config = LeadAssistantConfig()
                ClientConfig.LEAD_ASSISTANT_ID = lead_assistant_config.LEAD_ASSISTANT_ID
            
            # Check configuration - only validates API keys now
            ClientConfig.validate_config()
            
            # Initialize chat thread for assistant mode
            self.chat_thread = initialize_chat()
            if not self.chat_thread or not hasattr(self.chat_thread, "id"):
                self.signal_handler.message_signal.emit(
                    "system", "Error: Chat thread could not be initialized.", None
                )
                return
            
            # Initialize chat history for completion mode
            try:
                from src.chat_completion import ChatHistory
                from src.chat_completion_config import chat_completion_config
                self.chat_history = ChatHistory()
                
                # Add system message from current config
                config = chat_completion_config.get_config()
                self.current_completion_config = config
                if config and "system_message" in config:
                    self.chat_history.add_message("system", config["system_message"])
            except ImportError:
                self.signal_handler.message_signal.emit(
                    "system", "Warning: Chat completion mode not available.", None
                )
            
            # Add welcome message
            welcome_msg = """
            Hello, I pass butter. 
            
            I'm in Assistant API mode by default, but you can switch to Chat Completion API mode 
            through the Chat Completion panel.
            """
            self.signal_handler.message_signal.emit("assistant", welcome_msg, None)
            
        except Exception as e:
            self.signal_handler.message_signal.emit(
                "system", f"Error initializing chat: {str(e)}", None
            )
    
    def _send_message(self):
        """Send the user's message"""
        if self.processing:
            return
        
        # Get message text
        message_text = self.input_box.toPlainText().strip()
        if not message_text:
            return
        
        # Check for exit command
        if message_text.lower() in ["exit", "quit"]:
            QApplication.instance().quit()
            return
        
        # Clear input
        self.input_box.clear()
        
        # Add user message to display
        self.chat_display.add_message("user", message_text)
        
        # Disable input while processing
        self.processing = True
        self.input_box.setEnabled(False)
        self.send_button.setEnabled(False)
        
        # Process in background thread
        threading.Thread(
            target=self._process_message,
            args=(message_text,),
            daemon=True
        ).start()
    
    def _process_message(self, message_text):
        """Process user message"""
        # Check for analysis command
        if message_text.startswith("/analyze"):
            self._handle_analysis_command(message_text)
            return
        
        # Use different processing based on chat mode
        if self.chat_mode == "assistant":
            self._process_assistant_message(message_text)
        else:  # chat_mode == "completion"
            self._process_completion_message(message_text)
    
    def _process_assistant_message(self, message_text):
        """Process message using the Assistant API"""
        try:
            if not self.chat_thread:
                self.signal_handler.message_signal.emit(
                    "system", "Error: Chat thread not initialized.", None
                )
                return
            
            # Send the user message to the thread before starting the run
            send_user_message(self.chat_thread.id, message_text)
            
            # If we also have chat history initialized, mirror the message there
            if self.chat_history:
                self.chat_history.add_message("user", message_text)
            
            # Start run with the current assistant ID
            run = start_run(self.chat_thread.id, self.current_assistant_id)
            
            # Add thinking message
            self.signal_handler.message_signal.emit(
                "system", "Assistant is thinking...", None
            )
            
            # Poll for response
            last_message, text_content, formatted_content = poll_run_status_and_submit_outputs(
                self.chat_thread.id, run.id
            )
            
            # Mirror the assistant response to chat history
            if self.chat_history:
                self.chat_history.add_message("assistant", text_content)
            
            # Update UI with response - remove thinking message and add response
            self.signal_handler.message_signal.emit(
                "remove_thinking", "", None
            )
            self.signal_handler.message_signal.emit(
                "assistant", text_content, formatted_content
            )
            
        except Exception as e:
            self.signal_handler.message_signal.emit(
                "system", f"Error: {str(e)}", None
            )
        finally:
            # Re-enable input
            self.signal_handler.enable_input_signal.emit()
    
    def _process_completion_message(self, message_text):
        """Process message using the Chat Completion API"""
        try:
            # Attempt to initialize chat history if it's missing
            if not self.chat_history:
                try:
                    from src.chat_completion import ChatHistory
                    from src.chat_completion_config import chat_completion_config
                    
                    self.chat_history = ChatHistory()
                    
                    # Get default config if not already set
                    if not self.current_completion_config:
                        self.current_completion_config = chat_completion_config.get_config()
                        
                    # Add system message from current config
                        if self.current_completion_config and "system_message" in self.current_completion_config:
                            self.chat_history.add_message("system", self.current_completion_config["system_message"])
                        
                        self.signal_handler.message_signal.emit(
                            "system", "Chat history initialized for completion mode.", None
                        )
                except Exception as e:
                    self.signal_handler.message_signal.emit(
                        "system", f"Error: Could not initialize chat history. {str(e)}", None
                    )
                    self.signal_handler.enable_input_signal.emit()
                    return
            
            # Add message to chat history
            self.chat_history.add_message("user", message_text)
            
            # Mirror message to assistant thread if available
            if self.chat_thread:
                send_user_message(self.chat_thread.id, message_text)
            
            # Add thinking message
            self.signal_handler.message_signal.emit(
                "system", "Assistant is thinking...", None
            )
            
            # Get completion from API
            from src.chat_completion import create_chat_completion
            messages = self.chat_history.get_messages_for_completion()
            
            # Convert Message objects to dicts for API call
            message_dicts = [msg.to_dict() for msg in messages]
            
            # Get the current chat completion config
            config = self.current_completion_config
            
            # Make the API call
            completion_text = create_chat_completion(message_dicts, config)
            
            # Add the response to chat history
            self.chat_history.add_message("assistant", completion_text)
            
            # Mirror to assistant thread if available
            if self.chat_thread:
                send_assistant_message(self.chat_thread.id, completion_text)
            
            # Update UI with response - remove thinking message and add response
            self.signal_handler.message_signal.emit(
                "remove_thinking", "", None
            )
            self.signal_handler.message_signal.emit(
                "assistant", completion_text, None
            )
            
        except Exception as e:
            self.signal_handler.message_signal.emit(
                "system", f"Error: {str(e)}", None
            )
            import traceback
            self.signal_handler.message_signal.emit(
                "system", f"Traceback: {traceback.format_exc()}", None
            )
        finally:
            # Re-enable input
            self.signal_handler.enable_input_signal.emit()
            
    def set_chat_mode(self, mode):
        """Set the chat mode (assistant or completion)"""
        if mode not in ["assistant", "completion"]:
            self.signal_handler.message_signal.emit(
                "system", f"Error: Invalid chat mode: {mode}", None
            )
            return
        
        # Only switch if different
        if self.chat_mode != mode:
            old_mode = self.chat_mode
            self.chat_mode = mode
            
            # Notify the user about the mode change
            self.signal_handler.message_signal.emit(
                "system", f"Switched from {old_mode.title()} API mode to {mode.title()} API mode.", None
            )
            
            # If switching to completion mode, ensure we have history
            if mode == "completion":
                try:
                    # Import required modules
                    from src.chat_completion import ChatHistory
                    from src.chat_completion_config import chat_completion_config
                    
                    # Create chat history if it doesn't exist
                    if not self.chat_history:
                        self.chat_history = ChatHistory()
                        
                        # Get default config if not already set
                        if not self.current_completion_config:
                            self.current_completion_config = chat_completion_config.get_config()
                            
                        # Add system message from current config
                        if self.current_completion_config and "system_message" in self.current_completion_config:
                            self.chat_history.add_message("system", self.current_completion_config["system_message"])
                        
                        # Log success
                        self.signal_handler.message_signal.emit(
                            "system", "Chat history initialized for completion mode.", None
                        )
                    
                    # Import all previous messages from the thread if available (optional future enhancement)
                    # if self.chat_thread:
                    #     # This would require additional implementation to import history
                    #     pass
                        
                except Exception as e:
                    import traceback
                    self.signal_handler.message_signal.emit(
                        "system", f"Error initializing chat completion mode: {str(e)}", None
                    )
                    self.signal_handler.message_signal.emit(
                        "system", f"Traceback: {traceback.format_exc()}", None
                    )
                    self.chat_mode = "assistant"  # Revert back
    
    def set_chat_completion_config(self, config_name):
        """Set the active chat completion configuration"""
        try:
            from src.chat_completion_config import chat_completion_config
            from src.chat_completion import ChatHistory
            
            # Get the config
            config = chat_completion_config.get_config(config_name)
            if not config:
                self.signal_handler.message_signal.emit(
                    "system", f"Error: Configuration not found: {config_name}", None
                )
                return
            
            # Update our current config
            self.current_completion_config = config
            
            # Initialize chat history if not already initialized
            if not self.chat_history and self.chat_mode == "completion":
                self.chat_history = ChatHistory()
                self.signal_handler.message_signal.emit(
                    "system", "Chat history initialized for completion mode.", None
                )
            
            # If we have chat history, update the system message
            if self.chat_history and "system_message" in config:
                # Replace system message
                self.chat_history.system_message = None
                self.chat_history.add_message("system", config["system_message"])
            
            # Notify the user
            self.signal_handler.message_signal.emit(
                "system", f"Switched to chat completion configuration: {config.get('name', config_name)}", None
            )
            
        except Exception as e:
            import traceback
            self.signal_handler.message_signal.emit(
                "system", f"Error setting chat completion configuration: {str(e)}", None
            )
            self.signal_handler.message_signal.emit(
                "system", f"Traceback: {traceback.format_exc()}", None
            )

    def _handle_analysis_command(self, command):
        """Handle analysis command"""
        # Extract prompt from command
        # Format is: /analyze [prompt]
        prompt = command[9:].strip()
        
        if not prompt:
            self.signal_handler.message_signal.emit(
                "system", "Error: Analysis prompt is required. Use /analyze [your prompt]", None
            )
            self._enable_input()
            return
        
        # Show file selection dialog
        self._show_file_selection()
    
    def _show_file_selection(self):
        """Show file selection dialog"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files for Analysis",
            "",
            "All Files (*.*)"
        )
        
        if not file_paths:
            self.signal_handler.message_signal.emit(
                "system", "Analysis cancelled - no files selected.", None
            )
            self._enable_input()
            return
        
        # Show selected files
        files_str = "\n".join([f"- {os.path.basename(path)}" for path in file_paths])
        self.signal_handler.message_signal.emit(
            "system", f"Analyzing files:\n{files_str}", None
        )
        
        # Get agent config
        agent_config = {
            "OUTLINE_AGENT_ID": os.getenv("OUTLINE_AGENT_ID"),
            "FORMULATE_QUESTIONS_AGENT_ID": os.getenv("FORMULATE_QUESTIONS_AGENT_ID"),
            "VECTOR_STORE_SEARCH_AGENT_ID": os.getenv("VECTOR_STORE_SEARCH_AGENT_ID"),
            "WRITER_AGENT_SYSTEM_MESSAGE": os.getenv("WRITER_AGENT_SYSTEM_MESSAGE", "You are a helpful AI assistant."),
            "WRITER_AGENT_CONFIG": {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
            "REVIEWER_AGENT_ID": os.getenv("REVIEWER_AGENT_ID"),
            "GOOGLE_GEMINI_API_KEY": os.getenv("GOOGLE_GEMINI_API_KEY"),
            "OPEN_AI_API_KEY": os.getenv("OPENAI_API_KEY")
        }
        
        # Start analysis
        self.workflow_manager.run_analysis(
            user_prompt=prompt,
            file_paths=file_paths,
            agent_config=agent_config
        )
    
    def _on_workflow_progress(self, message, percent):
        """Handle workflow progress updates"""
        # Skip progress messages if we've already shown the assistants
        # Only show the initial "Analysis running" message
        if "Using assistants:" in self.chat_display.get_last_system_message():
            if percent == 0 and message == "Starting analysis":
                self.signal_handler.message_signal.emit(
                    "system", "Analysis running...", None
                )
            # Skip other progress messages to keep the UI clean
            return
        
        # Show other important progress messages (especially at the beginning)
        self.signal_handler.message_signal.emit(
            "system", message, None
        )
    
    def _on_workflow_result(self, result, context):
        """Handle workflow result"""
        self.signal_handler.message_signal.emit(
            "system", "Analysis complete", None
        )
        
        # Add the analysis result to the chat display
        self.signal_handler.message_signal.emit(
            "assistant", result, None
        )
        
        # Add the analysis result to the thread as an assistant message
        # This ensures the analysis result becomes part of the conversation history
        if self.chat_thread and hasattr(self.chat_thread, "id"):
            try:
                # Add the result to the thread as an assistant message
                send_assistant_message(self.chat_thread.id, result)
                
                print("Analysis result added to chat thread history")
            except Exception as e:
                print(f"Error adding analysis result to thread: {str(e)}")
        
        # Re-enable input
        self.signal_handler.enable_input_signal.emit()
    
    def _on_workflow_error(self, error_message):
        """Handle workflow errors"""
        self.signal_handler.message_signal.emit(
            "system", f"Analysis Error: {error_message}", None
        )
        self._enable_input()
    
    def _on_workflow_log(self, log_message):
        """Handle workflow log messages"""
        # We could display these or just log them
        print(f"Workflow Log: {log_message}")
    
    def _add_message(self, role, content, formatted_content):
        """Add a message to the chat display (called from signal)"""
        if role == "remove_thinking":
            # Remove the "thinking" message
            for i in range(len(self.chat_display.messages) - 1, -1, -1):
                role, content, _ = self.chat_display.messages[i]
                if role == "system" and "thinking" in content.lower():
                    # Remove the widget
                    widget = self.chat_display.layout.itemAt(i).widget()
                    self.chat_display.layout.removeWidget(widget)
                    widget.deleteLater()
                    # Remove from messages list
                    self.chat_display.messages.pop(i)
                    break
        else:
            # Add the message
            self.chat_display.add_message(role, content, formatted_content)
    
    def _enable_input(self):
        """Re-enable input controls"""
        self.processing = False
        self.input_box.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_box.setFocus()

    def _handle_analysis_request(self, signal_payload):
        """Handle analysis request from assistant"""
        # Extract function name and other data
        function_name = signal_payload.get("function_name", "")
        thread_id = signal_payload.get("thread_id", "")
        tool_call_id = signal_payload.get("tool_call_id", "")
        
        # Simpler prompt with just function name in title
        title = f"{function_name.replace('_', ' ').title()}"
        default_text = f"Please analyze the selected files and provide insights about {function_name.replace('_', ' ')}."
        
        # Get prompt from user using our simplified dialog
        user_prompt, ok = AnalysisPromptDialog.get_prompt(
            self,
            title=title,
            default_text=default_text
        )
        
        if not ok or not user_prompt:
            self.signal_handler.message_signal.emit(
                "system", "Analysis cancelled - no prompt provided.", None
            )
            self._enable_input()
            return
        
        # Show the request in the chat
        self.signal_handler.message_signal.emit(
            "system", f"Analysis requested: {user_prompt}\n\nPlease select files to analyze.", None
        )
        
        # Update the signal payload with the user-provided prompt
        signal_payload["user_prompt"] = user_prompt
        
        # Show file selection dialog
        self._show_file_selection_for_prompt(user_prompt, function_name, signal_payload)

    def _show_file_selection_for_prompt(self, prompt, function_name, signal_payload):
        """Show file selection dialog for an existing prompt"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            f"Select Files for {function_name.replace('_', ' ')}",
            "",
            "All Files (*.*)"
        )
        
        if not file_paths:
            self.signal_handler.message_signal.emit(
                "system", "Analysis cancelled - no files selected.", None
            )
            self._enable_input()
            return
        
        # Show selected files
        files_str = "\n".join([f"- {os.path.basename(path)}" for path in file_paths])
        self.signal_handler.message_signal.emit(
            "system", f"Analyzing files:\n{files_str}", None
        )
        
        # Configure agent based on function name
        config_type = "financial" if "financial" in function_name else "research"
        
        # Create assistant config and generate assistants
        self.signal_handler.message_signal.emit(
            "system", "Creating assistants...", None
        )
        
        try:
            # Import the appropriate assistant config class
            if config_type == "financial":
                from src.assistant_config import FinancialAssistantConfig
                assistant_config = FinancialAssistantConfig()
            else:
                from src.assistant_config import ResearchAssistantConfig
                assistant_config = ResearchAssistantConfig()
            
            # Create the assistants - this will set the ID fields
            assistant_config.create_agents()
            
            # Verify that we got the IDs
            missing_ids = []
            if not assistant_config.OUTLINE_AGENT_ID: missing_ids.append("OUTLINE_AGENT_ID")
            if not assistant_config.FORMULATE_QUESTIONS_AGENT_ID: missing_ids.append("FORMULATE_QUESTIONS_AGENT_ID")
            if not assistant_config.VECTOR_STORE_SEARCH_AGENT_ID: missing_ids.append("VECTOR_STORE_SEARCH_AGENT_ID")
            if not assistant_config.REVIEWER_AGENT_ID: missing_ids.append("REVIEWER_AGENT_ID")
            
            if missing_ids:
                error_msg = f"Failed to create some assistants: {', '.join(missing_ids)}"
                self.signal_handler.message_signal.emit(
                    "system", error_msg, None
                )
                self._enable_input()
                return
            
            # Get agent config from the created assistants but INCLUDE THE CONFIG OBJECT
            agent_config = {
                "assistant_config": assistant_config,  # Pass the whole config object
                "OUTLINE_AGENT_ID": assistant_config.OUTLINE_AGENT_ID,
                "FORMULATE_QUESTIONS_AGENT_ID": assistant_config.FORMULATE_QUESTIONS_AGENT_ID, 
                "VECTOR_STORE_SEARCH_AGENT_ID": assistant_config.VECTOR_STORE_SEARCH_AGENT_ID,
                "WRITER_AGENT_SYSTEM_MESSAGE": assistant_config.WRITER_AGENT_SYSTEM_MESSAGE,
                "WRITER_AGENT_CONFIG": assistant_config.writer_agent_config,
                "REVIEWER_AGENT_ID": assistant_config.REVIEWER_AGENT_ID,
                "GOOGLE_GEMINI_API_KEY": os.getenv("GOOGLE_GEMINI_API_KEY"),
                "OPEN_AI_API_KEY": os.getenv("OPENAI_API_KEY"),
                "CONFIG_TYPE": config_type
            }
            
            # Add debug output
            self.signal_handler.message_signal.emit(
                "system", f"Using assistants:\n- Outline: {agent_config['OUTLINE_AGENT_ID'][:8]}...\n- Questions: {agent_config['FORMULATE_QUESTIONS_AGENT_ID'][:8]}...\n- Search: {agent_config['VECTOR_STORE_SEARCH_AGENT_ID'][:8]}...\n- Reviewer: {agent_config['REVIEWER_AGENT_ID'][:8]}...", None
            )
            
            # Start analysis with the user-provided prompt
            self.workflow_manager.run_analysis(
                user_prompt=prompt,
                file_paths=file_paths,
                agent_config=agent_config,
                callback=lambda result, context: self._handle_analysis_result(result, context, signal_payload)
            )
            
        except Exception as e:
            self.signal_handler.message_signal.emit(
                "system", f"Error creating assistants: {str(e)}", None
            )
            import traceback
            traceback_str = traceback.format_exc()
            self.signal_handler.message_signal.emit(
                "system", f"Traceback: {traceback_str}", None
            )
            self._enable_input()

    def _handle_analysis_result(self, result, context, signal_payload):
        """Handle analysis result and optionally send back to the assistant"""
        # If we have all required parameters for a tool call submission
        if (signal_payload and 'thread_id' in signal_payload and 
            'tool_call_id' in signal_payload and 'run_id' in signal_payload):
            try:
                from src.openai_assistant import OpenAI, ClientConfig
                client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
                
                # Submit the result to complete the tool call
                client.beta.threads.runs.submit_tool_outputs(
                    thread_id=signal_payload['thread_id'],
                    run_id=signal_payload['run_id'],
                    tool_outputs=[
                        {
                            "tool_call_id": signal_payload['tool_call_id'],
                            "output": result
                        }
                    ]
                )
                
                # Log success
                self.signal_handler.message_signal.emit(
                    "system", "Analysis result submitted to assistant", None
                )
                
            except Exception as e:
                # Log error
                self.signal_handler.message_signal.emit(
                    "system", f"Error submitting analysis result: {str(e)}", None
                )
                
                # Fall back to adding the result as a regular assistant message
                self._add_result_as_assistant_message(result)
        else:
            # Missing required parameters for tool submission
            if signal_payload and ('thread_id' not in signal_payload or 
                                 'tool_call_id' not in signal_payload or 
                                 'run_id' not in signal_payload):
                missing = []
                if 'thread_id' not in signal_payload:
                    missing.append('thread_id')
                if 'tool_call_id' not in signal_payload:
                    missing.append('tool_call_id')
                if 'run_id' not in signal_payload:
                    missing.append('run_id')
                print(f"Cannot complete tool call - missing required parameters: {', '.join(missing)}")
            
            # Add the result to the thread as an assistant message
            self._add_result_as_assistant_message(result)
    
    def _add_result_as_assistant_message(self, result):
        """Helper method to add an analysis result as an assistant message to the thread"""
        if self.chat_thread and hasattr(self.chat_thread, "id"):
            try:
                # Add the result to the thread as an assistant message
                send_assistant_message(self.chat_thread.id, result)
                print("Analysis result added to thread as assistant message")
            except Exception as e:
                print(f"Error adding analysis result to thread: {str(e)}")

    def _check_env_file(self):
        """Debug helper to check contents of .env file"""
        try:
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
            if os.path.exists(env_path):
                print(f"\nDEBUG - .env file exists at: {env_path}")
                with open(env_path, 'r') as f:
                    content = f.read()
                    # Print keys without values
                    for line in content.splitlines():
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            print(f"{key}: {'[SET]' if value.strip() else '[EMPTY]'}")
            else:
                print(f"\nDEBUG - .env file not found at: {env_path}")
        except Exception as e:
            print(f"Error reading .env file: {str(e)}")

    def set_assistant(self, assistant_id):
        """Set the assistant for the chat thread"""
        if assistant_id:
            self.current_assistant_id = assistant_id
            # Log the change
            self.signal_handler.message_signal.emit(
                "system", f"Chat assistant changed. Assistant ID: {assistant_id[:8]}...", None
            )
        else:
            # If no assistant_id provided, fall back to lead assistant
            self.current_assistant_id = ClientConfig.LEAD_ASSISTANT_ID
            self.signal_handler.message_signal.emit(
                "system", "Chat assistant reset to default", None
            )

class SettingsPanel(QWidget):
    """Panel for viewing and editing assistant configuration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Assistant Configuration")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("View and edit assistant IDs used for analysis workflows:")
        layout.addWidget(desc_label)
        
        # ID fields
        self.id_fields = {}
        self._add_id_field(layout, "ASSISTANT_ID", "Main Assistant")
        self._add_id_field(layout, "OUTLINE_AGENT_ID", "Outline Agent")
        self._add_id_field(layout, "FORMULATE_QUESTIONS_AGENT_ID", "Questions Agent")
        self._add_id_field(layout, "VECTOR_STORE_SEARCH_AGENT_ID", "Search Agent")
        self._add_id_field(layout, "REVIEWER_AGENT_ID", "Reviewer Agent")
        self._add_id_field(layout, "GOOGLE_GEMINI_API_KEY", "Google Gemini API Key")
        
        # Save button
        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self._save_configuration)
        layout.addWidget(save_button)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Add spacing at the bottom
        layout.addStretch()
    
    def _add_id_field(self, layout, env_var, display_name):
        """Add a field for an ID with label"""
        # Container for label and field
        field_container = QWidget()
        field_layout = QHBoxLayout(field_container)
        field_layout.setContentsMargins(0, 5, 0, 5)
        
        # Label
        label = QLabel(f"{display_name}:")
        label.setFixedWidth(150)
        field_layout.addWidget(label)
        
        # Text field
        text_field = QTextEdit()
        text_field.setPlaceholderText(f"Enter {display_name} ID")
        text_field.setMaximumHeight(40)
        
        # Set current value from environment
        current_value = os.getenv(env_var, "")
        text_field.setText(current_value)
        
        text_field.setStyleSheet("border-radius: 10px;")
        
        field_layout.addWidget(text_field)
        
        # Store reference to field
        self.id_fields[env_var] = text_field
        
        # Add to main layout
        layout.addWidget(field_container)
    
    def _save_configuration(self):
        """Save configuration to .env file"""
        try:
            # Find .env file in project root
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env_path = os.path.join(script_dir, '.env')
            
            # Read existing .env file
            env_content = {}
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env_content[key.strip()] = value.strip()
            
            # Update with new values
            for env_var, text_field in self.id_fields.items():
                value = text_field.toPlainText().strip()
                if value:
                    env_content[env_var] = value
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                for key, value in env_content.items():
                    f.write(f"{key}={value}\n")
            
            # Update environment variables in current process
            for env_var, text_field in self.id_fields.items():
                value = text_field.toPlainText().strip()
                if value:
                    os.environ[env_var] = value
            
            # Update status
            self.status_label.setText("Configuration saved successfully!")
            self.status_label.setStyleSheet("color: #00FF00;")
            
            # Clear status after 3 seconds
            QTimer.singleShot(3000, lambda: self.status_label.setText(""))
            
        except Exception as e:
            self.status_label.setText(f"Error saving configuration: {str(e)}")
            self.status_label.setStyleSheet("color: #FF0000;")

class AnalysisPromptDialog(QDialog):
    """Custom dialog for entering analysis prompts with a large text area"""
    
    def __init__(self, parent=None, title="Analysis Prompt", default_text=""):
        super().__init__(parent)
        
        # Set window properties
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)  # Much larger dialog
        
        # Apply VSCode styling to the dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {VSCodeStyleHelper.BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
            }}
            QTextEdit {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                padding: 8px;
                font-size: 13px;
                selection-background-color: {VSCodeStyleHelper.ACCENT_COLOR};
            }}
            QPushButton {{
                background-color: {VSCodeStyleHelper.BUTTON_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: none;
                border-radius: {VSCodeStyleHelper.SMALL_RADIUS};
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {VSCodeStyleHelper.BUTTON_HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {VSCodeStyleHelper.ACCENT_COLOR};
            }}
        """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add text edit (larger input area)
        self.text_edit = QTextEdit()
        self.text_edit.setText(default_text)
        self.text_edit.setMinimumHeight(300)  # Make it even taller
        layout.addWidget(self.text_edit)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.ok_button = QPushButton("Analyze")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Set dark title bar on Windows
        if platform.system() == "Windows":
            # Schedule setting the dark title bar after the dialog is created
            QTimer.singleShot(0, lambda: WindowsStyleHelper.set_dark_title_bar(int(self.winId())))
        
        # Set focus to the text area
        self.text_edit.setFocus()
    
    def get_text(self):
        """Return the entered text"""
        return self.text_edit.toPlainText()
    
    @staticmethod
    def get_prompt(parent=None, title="Analysis Prompt", default_text=""):
        """Static method to create the dialog and return (text, ok) tuple"""
        dialog = AnalysisPromptDialog(parent, title, default_text)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            return dialog.get_text(), True
        else:
            return "", False

class ChatBotApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Set up window
        self.setWindowTitle("AIWorkbench")
        self.resize(1200, 800)
        
        # Ensure the window uses the application icon
        if QApplication.instance().windowIcon():
            self.setWindowIcon(QApplication.instance().windowIcon())
        
        # Set dark title bar on Windows
        if platform.system() == "Windows":
            # Wait for window to be created and then set dark title bar
            QTimer.singleShot(100, lambda: WindowsStyleHelper.set_dark_title_bar(int(self.winId())))
        
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Create with Vector Stores as the first tab
        self.left_panel = SidePanel("Left")
        
        # Clear existing tabs
        while self.left_panel.button_layout.count() > 0:
            item = self.left_panel.button_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        while self.left_panel.content_stack.count() > 0:
            self.left_panel.content_stack.removeWidget(self.left_panel.content_stack.widget(0))
        
        # Add Vector Stores as first tab
        vs_panel = VectorStorePanel()
        self.left_panel.add_custom_page("Vector Stores", vs_panel)
        
        # Add other tabs after
        self.left_panel.add_page("Settings", "Left Settings Panel")
        self.left_panel.add_page("History", "Left History Panel")
        self.left_panel.add_page("Help", "Left Help Panel")
        
        # Select Vector Stores tab by default
        if self.left_panel.button_layout.count() > 0:
            button = self.left_panel.button_layout.itemAt(0).widget()
            button.setChecked(True)
            self.left_panel.content_stack.setCurrentIndex(0)
        
        main_layout.addWidget(self.left_panel, 2)
        
        # Main chat area
        self.chat_tab = ChatTab()
        main_layout.addWidget(self.chat_tab, 4)
        
        # Right panel
        self.right_panel = SidePanel("Right")
        assistants_panel = AssistantsPanel()
        self.right_panel.add_custom_page("Assistants", assistants_panel)
        
        main_layout.addWidget(self.right_panel, 3)

        # Set Assistants tab as the default selected one
        if self.right_panel.button_layout.count() > 0:
            button = self.right_panel.button_layout.itemAt(0).widget()
            button.setChecked(True)
            self.right_panel.content_stack.setCurrentIndex(0)

def main():
    """Run the chat bot application"""
    # Set environment variable to indicate GUI mode
    os.environ["GUI_MODE"] = "1"
    
    # Set application details for proper taskbar icon handling
    if platform.system() == "Windows":
        # Import windows-specific libraries
        try:
            import ctypes
            # Set app ID so Windows properly associates icon with the application in taskbar
            app_id = "AIWorkbench.1.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            print(f"Set Windows AppUserModelID to: {app_id}")
        except Exception as e:
            print(f"Failed to set application ID: {e}")
    
    app = QApplication(sys.argv)
    app.setApplicationName("AIWorkbench")
    app.setApplicationDisplayName("AIWorkbench")
    VSCodeStyleHelper.apply_styles(app)
    
    # Get absolute path to the current file's directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Move up one directory to get to the project root
    project_root = os.path.dirname(current_dir)
    # Path to the icon
    icon_path = os.path.join(project_root, "taskbarIcon.png")
    
    # Print debug info
    print(f"Looking for icon at: {icon_path}")
    print(f"File exists: {os.path.exists(icon_path)}")
    
    # Create QIcon instance
    icon = QIcon()
    
    # Try to set the icon
    if os.path.exists(icon_path):
        print("Setting custom icon")
        # Load the icon with multiple sizes to ensure proper scaling
        icon = QIcon(icon_path)
        # Set it for the application
        app.setWindowIcon(icon)
    else:
        print("Custom icon not found, using built-in icon")
        # Use a built-in icon as fallback
        icon = app.style().standardIcon(QStyle.SP_ComputerIcon)
        app.setWindowIcon(icon)
    
    # Create and show the window
    window = ChatBotApp()
    # Also set the icon on the main window
    window.setWindowIcon(icon)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 