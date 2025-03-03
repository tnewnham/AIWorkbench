#!/usr/bin/env python
"""
Chat Completion Management Panel for Solstice.
This module provides UI components to manage chat completion configurations.
"""
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QListWidget, QListWidgetItem, QSplitter, QMessageBox, QComboBox,
    QHeaderView, QAbstractItemView, QMenu, QAction, QLineEdit
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QColor, QCursor

from .chat_completion_config import chat_completion_config
from .signals import global_signals

# Define VSCodeStyleHelper for consistent styling
class VSCodeStyleHelper:
    SIDEBAR_BG_COLOR = "#252526"
    BG_COLOR = "#212121"
    TEXT_COLOR = "#D4D4D4"
    ACCENT_COLOR = "#007ACC"
    BORDER_COLOR = "#3E3E42"
    LARGE_RADIUS = "10px"
    MEDIUM_RADIUS = "8px"
    SMALL_RADIUS = "6px"
    SCROLLBAR_BG_COLOR = "#212121"
    SCROLLBAR_HANDLE_COLOR = "#424242"
    SCROLLBAR_HANDLE_HOVER_COLOR = "#686868"

class ChatCompletionPanel(QWidget):
    """Panel for managing chat completion configurations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chat_completion_panel")
        
        # Track currently selected configuration
        self.current_config_name = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Add title and refresh button
        title_layout = QHBoxLayout()
        title_label = QLabel("Chat Completions")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_layout.addWidget(title_label)
        
        # Remove refresh button
        title_layout.addStretch(1)  # Add stretch to push title to the left
        
        main_layout.addLayout(title_layout)
        
        # Add search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by name or description...")
        self.search_box.textChanged.connect(self._filter_configurations)
        # Add rounded corners to search box
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                padding: 5px;
            }}
        """)
        search_layout.addWidget(self.search_box)
        
        main_layout.addLayout(search_layout)
        
        # Create splitter for configuration list and details
        splitter = QSplitter(Qt.Vertical)
        
        # Configuration list
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add list widget
        self.config_list = QListWidget()
        self.config_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.config_list.itemClicked.connect(self.show_config_details)
        # Add rounded corners to the list
        self.config_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {VSCodeStyleHelper.BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 5px;
            }}
            QListWidget::item {{
                border-radius: {VSCodeStyleHelper.SMALL_RADIUS};
                padding: 5px;
            }}
            QListWidget::item:selected {{
                background-color: {VSCodeStyleHelper.ACCENT_COLOR};
                color: white;
            }}
            QScrollBar:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR};
                width: 8px;
                margin: 0px;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
            }}
            QScrollBar::handle:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR};
                min-height: 30px;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
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
            QScrollBar:horizontal {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR};
                height: 8px;
                margin: 0px;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
            }}
            QScrollBar::handle:horizontal {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR};
                min-width: 30px;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_HOVER_COLOR};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)
        list_layout.addWidget(self.config_list)
        
        # Button container
        button_layout = QHBoxLayout()
        
        # Toggle button
        self.toggle_button = QPushButton("Use for Chat")
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_config_for_chat)
        button_layout.addWidget(self.toggle_button)
        
        list_layout.addLayout(button_layout)
        
        # Add status indicator
        self.status_label = QLabel("No configuration active")
        self.status_label.setStyleSheet("color: #888888;")
        list_layout.addWidget(self.status_label)
        
        # Add list container to splitter
        splitter.addWidget(list_container)
        
        # Details panel
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        # Details text area
        details_label = QLabel("Configuration Details")
        details_layout.addWidget(details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        # Apply rounded style to the details text area
        self.details_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 8px;
            }}
            QScrollBar:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR};
                width: 8px;
                margin: 0px;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
            }}
            QScrollBar::handle:vertical {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR};
                min-height: 30px;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
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
            QScrollBar:horizontal {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_BG_COLOR};
                height: 8px;
                margin: 0px;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
            }}
            QScrollBar::handle:horizontal {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_COLOR};
                min-width: 30px;
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {VSCodeStyleHelper.SCROLLBAR_HANDLE_HOVER_COLOR};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)
        details_layout.addWidget(self.details_text)
        
        # Add details container to splitter
        splitter.addWidget(details_container)
        
        # Set initial splitter sizes
        splitter.setSizes([200, 300])
        
        main_layout.addWidget(splitter)
        
        # Load configurations
        self.refresh_configurations()
    
    def refresh_configurations(self):
        """Refresh the list of available configurations"""
        self.config_list.clear()
        self.details_text.clear()
        
        # Get all configurations
        config_names = chat_completion_config.get_config_names()
        
        # Store all configurations for filtering
        self.all_configs = config_names
        
        if not config_names:
            self.config_list.addItem("No configurations found")
            return
        
        # Add all configurations to the list first
        active_item = None
        for config_name in config_names:
            item = QListWidgetItem(config_name)
            item.setData(Qt.UserRole, config_name)
            self.config_list.addItem(item)
            
            # Track active item if it exists
            if hasattr(self, 'active_config') and self.active_config and self.active_config == config_name:
                active_item = item
        
        # Now highlight only the active item if it exists (after all items are added)
        if active_item:
            active_item.setBackground(QColor("#2A4D69"))
            active_item.setSelected(True)
            self.config_list.scrollToItem(active_item)
    
    def show_config_details(self, item):
        """Show details for the selected configuration"""
        config_name = item.data(Qt.UserRole)
        if not config_name:
            return
        
        # Check if this is the active configuration
        if hasattr(self, 'active_config') and self.active_config and self.active_config == config_name:
            self.toggle_button.setChecked(True)
        else:
            self.toggle_button.setChecked(False)
        
        self.current_config_name = config_name
        
        # Get configuration details
        config = chat_completion_config.get_config(config_name)
        if not config:
            self.details_text.setPlainText(f"Error: Configuration {config_name} not found")
            return
        
        # Format details
        details = f"Name: {config.get('name', config_name)}\n"
        details += f"Model: {config.get('model', 'Not specified')}\n"
        details += f"Temperature: {config.get('temperature', 'Not specified')}\n"
        details += f"Max Tokens: {config.get('max_tokens', 'Not specified')}\n"
        
        # Add other parameters if present
        for key, value in config.items():
            if key not in ['name', 'model', 'temperature', 'max_tokens', 'system_message']:
                details += f"{key}: {value}\n"
        
        # Add system message
        if 'system_message' in config:
            details += "\nSystem Message:\n"
            details += f"{config['system_message']}\n"
        
        self.details_text.setPlainText(details)
    
    def toggle_config_for_chat(self):
        """Toggle selected configuration for chat"""
        # Get selected configuration
        selected_items = self.config_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a configuration to toggle.")
            self.toggle_button.setChecked(False)
            return
        
        config_name = selected_items[0].data(Qt.UserRole)
        if not config_name:
            self.toggle_button.setChecked(False)
            return
        
        # If the button is now checked (toggled on)
        if self.toggle_button.isChecked():
            # Store the previously active configuration (to restore later)
            self.previous_config_name = getattr(self, 'active_config', None)
            
            # First switch to completion mode
            global_signals.set_chat_mode_signal.emit("completion")
            
            # Then set the new configuration
            global_signals.set_chat_completion_config_signal.emit(config_name)
            
            # Update UI to show which configuration is active
            self.status_label.setText(f"Active: {config_name}")
            self.status_label.setStyleSheet("color: #00AA00; font-weight: bold;")
            
            # Clear all highlights first
            for i in range(self.config_list.count()):
                item = self.config_list.item(i)
                if item:
                    item.setBackground(QColor("transparent"))
            
            # Highlight the newly selected item in the list
            selected_items[0].setBackground(QColor("#2A4D69"))
            
            # Store the current configuration
            self.active_config = config_name
        else:
            # Restore previous configuration if any
            if hasattr(self, 'previous_config_name') and self.previous_config_name:
                global_signals.set_chat_completion_config_signal.emit(self.previous_config_name)
            
            # Switch back to assistant mode
            global_signals.set_chat_mode_signal.emit("assistant")
            
            # Update UI
            self.status_label.setText("No configuration active")
            self.status_label.setStyleSheet("color: #888888;")
            
            # Remove highlighting from all items
            for i in range(self.config_list.count()):
                item = self.config_list.item(i)
                if item:
                    item.setBackground(QColor("transparent"))
            
            # Clear the active configuration
            self.active_config = None
    
    def _filter_configurations(self):
        """Filter configurations based on search text"""
        search_text = self.search_box.text().lower()
        
        # If no search text, show all configurations
        if not search_text:
            for i in range(self.config_list.count()):
                self.config_list.item(i).setHidden(False)
            return
        
        # Filter based on search text
        for i in range(self.config_list.count()):
            item = self.config_list.item(i)
            config_name = item.data(Qt.UserRole)
            if not config_name:
                continue
            
            # Get full config to search in
            config = chat_completion_config.get_config(config_name)
            if not config:
                continue
                
            # Check if search text is in name or other fields
            match_found = False
            if search_text in config_name.lower():
                match_found = True
            elif 'name' in config and config['name'] and search_text in config['name'].lower():
                match_found = True
            elif 'model' in config and config['model'] and search_text in config['model'].lower():
                match_found = True
            elif 'system_message' in config and config['system_message'] and search_text in config['system_message'].lower():
                match_found = True
            
            item.setHidden(not match_found) 