#!/usr/bin/env python
"""
Assistants Management Panel for Solstice.
This module provides UI components to manage OpenAI assistants.
"""
import os
import sys
import json
import platform
from typing import Dict, List, Optional, Any
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QListWidget, QListWidgetItem, QSplitter, QMessageBox, QComboBox,
    QProgressBar, QApplication, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMenu, QAction, QLineEdit, QProgressDialog
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject, QThread, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QCursor

# Import the OpenAI client
from openai import OpenAI

# Import WindowsStyleHelper for dark title bars
from src.windows_style_helper import WindowsStyleHelper

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
    SCROLLBAR_BG_COLOR = "#212121"  # Match main background
    SCROLLBAR_HANDLE_COLOR = "#424242"  # Subtle grey
    SCROLLBAR_HANDLE_HOVER_COLOR = "#686868"  # Lighter grey on hover

class WorkerSignals(QObject):
    """Signals for worker thread communication"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QThread):
    """Worker thread for running operations in background"""
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
    def run(self):
        """Run the worker function"""
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()

class AssistantsPanel(QWidget):
    """Assistants Management Panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = OpenAI()
        self.active_workers = []  # Keep track of active worker threads
        
        # Track currently selected assistant
        self.current_assistant = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Add title and refresh button
        title_layout = QHBoxLayout()
        title_label = QLabel("Assistants")
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
        self.search_box.setPlaceholderText("Search by ID, name, or description...")
        self.search_box.textChanged.connect(self._filter_assistants)
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
        
        # Create splitter for assistants list and details
        splitter = QSplitter(Qt.Vertical)
        
        # Assistants list
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add list widget
        self.assistant_list = QListWidget()
        self.assistant_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.assistant_list.itemClicked.connect(self.show_assistant_details)
        # Allow right-click context menu
        self.assistant_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.assistant_list.customContextMenuRequested.connect(self.show_context_menu)
        # Add rounded corners to the list
        self.assistant_list.setStyleSheet(f"""
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
        
        list_layout.addWidget(self.assistant_list)
        
        # Button container
        button_layout = QHBoxLayout()
        
        # Delete button
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_selected_assistants)
        button_layout.addWidget(self.delete_button)
        
        # Replace "Assign to Thread" with toggle button
        self.toggle_button = QPushButton("Toggle for Chat")
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self.toggle_assistant_for_chat)
        button_layout.addWidget(self.toggle_button)
        
        list_layout.addLayout(button_layout)
        
        # Add status indicator
        self.status_label = QLabel("No assistant assigned to chat")
        self.status_label.setStyleSheet("color: #888888;")
        list_layout.addWidget(self.status_label)
        
        # Add list container to splitter
        splitter.addWidget(list_container)
        
        # Details panel
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        # Details text area
        details_label = QLabel("Assistant Details")
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
        
        # Load assistants
        self.refresh_assistants()
    
    def refresh_assistants(self):
        """Refresh the list of assistants"""
        worker = Worker(self._fetch_assistants)
        worker.signals.result.connect(self._on_assistants_loaded)
        worker.signals.error.connect(self._show_error)
        self.active_workers.append(worker)
        worker.start()
    
    def _fetch_assistants(self):
        """Fetch all assistants from the API"""
        assistants = []
        page_cursor = None
        
        while True:
            params = {"limit": 100}
            if page_cursor:
                params["after"] = page_cursor
            
            response = self.client.beta.assistants.list(**params)
            
            assistants.extend(response.data)
            
            if response.has_more:
                page_cursor = response.last_id
            else:
                break
        
        return assistants
    
    def _on_assistants_loaded(self, assistants):
        """Handle loaded assistants data"""
        self.assistant_list.clear()
        self.details_text.clear()
        
        if not assistants:
            self.assistant_list.addItem("No assistants found")
            return
        
        # Store all assistants for filtering
        self.all_assistants = assistants
        
        # Sort assistants by created_at (newest first)
        assistants.sort(key=lambda x: x.created_at, reverse=True)
        
        # First, add all assistants to the list without highlighting
        active_item = None
        for assistant in assistants:
            item = QListWidgetItem(assistant.name or f"Assistant {assistant.id[:8]}...")
            item.setData(Qt.UserRole, assistant)
            
            # Track active assistant item if it exists
            if hasattr(self, 'active_assistant') and self.active_assistant and self.active_assistant.id == assistant.id:
                active_item = item
                
            self.assistant_list.addItem(item)
        
        # Now highlight only the active item if it exists
        if active_item:
            active_item.setBackground(QColor("#2A4D69"))
            active_item.setSelected(True)
            self.assistant_list.scrollToItem(active_item)
            self.show_assistant_details(active_item)
    
    def show_assistant_details(self, item):
        """Show details for the selected assistant"""
        assistant = item.data(Qt.UserRole)
        if not assistant:
            return
        
        # Check if this is the active assistant
        if hasattr(self, 'active_assistant') and self.active_assistant and self.active_assistant.id == assistant.id:
            self.toggle_button.setChecked(True)
            self.delete_button.setEnabled(False)
        else:
            self.toggle_button.setChecked(False)
            self.delete_button.setEnabled(True)
        
        self.current_assistant = assistant
        
        # Format created_at timestamp
        created_time = datetime.fromtimestamp(assistant.created_at)
        created_str = created_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Format details
        details = f"ID: {assistant.id}\n"
        details += f"Name: {assistant.name or 'Unnamed'}\n"
        details += f"Model: {assistant.model}\n"
        details += f"Created: {created_str}\n\n"
        
        if assistant.description:
            details += f"Description: {assistant.description}\n\n"
        
        # Show tools
        if assistant.tools:
            details += "Tools:\n"
            for tool in assistant.tools:
                details += f"- {tool.type}\n"
                if tool.type == "function" and hasattr(tool, "function"):
                    details += f"  Function: {tool.function.name}\n"
            details += "\n"
        
        # Show metadata if present
        if assistant.metadata:
            details += "Metadata:\n"
            for key, value in assistant.metadata.items():
                details += f"- {key}: {value}\n"
            details += "\n"
        
        # Show instructions
        if assistant.instructions:
            details += "Instructions:\n"
            details += f"{assistant.instructions}\n"
        
        self.details_text.setPlainText(details)
    
    def show_context_menu(self, position):
        """Show context menu for assistant list"""
        selected_items = self.assistant_list.selectedItems()
        if not selected_items:
            return
            
        menu = QMenu()
        
        # Toggle assistant action
        assistant = selected_items[0].data(Qt.UserRole)
        if assistant:
            if hasattr(self, 'active_assistant') and self.active_assistant and self.active_assistant.id == assistant.id:
                toggle_text = "Deactivate for Chat"
            else:
                toggle_text = "Activate for Chat"
            
            toggle_action = QAction(toggle_text, self)
            toggle_action.triggered.connect(self.toggle_assistant_for_chat)
            menu.addAction(toggle_action)
            
            # Add separator
            menu.addSeparator()
        
        # Delete action - disabled if this is the active assistant
        delete_text = "Delete Assistant"
        delete_action = QAction(delete_text, self)
        delete_action.triggered.connect(self.delete_selected_assistants)
        delete_action.setEnabled(not (hasattr(self, 'active_assistant') and 
                                    self.active_assistant and 
                                    self.active_assistant.id == assistant.id))
        menu.addAction(delete_action)
        
        menu.exec_(QCursor.pos())
    
    def delete_selected_assistants(self):
        """Delete selected assistants after confirmation."""
        selected_items = self.assistant_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select at least one assistant to delete.")
            return
        
        # Check if trying to delete active assistant
        for item in selected_items:
            assistant = item.data(Qt.UserRole)
            if hasattr(self, 'active_assistant') and self.active_assistant and self.active_assistant.id == assistant.id:
                QMessageBox.warning(
                    self, 
                    "Cannot Delete Active Assistant",
                    "The selected assistant is currently active in the chat. Please deactivate it first."
                )
                return
        
        # Count items to delete
        num_selected = len(selected_items)
        
        # Confirm deletion with appropriate message
        confirm_msg = f"Are you sure you want to delete {num_selected} assistant"
        if num_selected > 1:
            confirm_msg += "s"
        confirm_msg += "?\n\nThis operation cannot be undone."
        
        # For multiple assistants, list their names in the confirmation dialog
        if num_selected > 1:
            confirm_msg += "\n\nAssistants to delete:"
            for i, item in enumerate(selected_items):
                if i < 10:  # Show max 10 names to avoid huge dialogs
                    assistant = item.data(Qt.UserRole)
                    confirm_msg += f"\n- {assistant.name or assistant.id[:8]+'...'}"
                elif i == 10:
                    confirm_msg += f"\n- ...and {num_selected - 10} more"
                    break
        else:
            # Single assistant case
            assistant = selected_items[0].data(Qt.UserRole)
            confirm_msg = f"Are you sure you want to delete assistant '{assistant.name or assistant.id}'?\n\nThis operation cannot be undone."
        
        if QMessageBox.question(self, "Confirm Deletion", confirm_msg, 
                              QMessageBox.Yes | QMessageBox.No, 
                              QMessageBox.No) != QMessageBox.Yes:
            return
        
        # Create progress dialog for deleting multiple assistants
        if num_selected > 1:
            progress = QProgressDialog(f"Deleting {num_selected} assistants...", "Cancel", 0, num_selected, self)
            progress.setWindowTitle("Deleting Assistants")
            progress.setWindowModality(Qt.WindowModal)
            
            progress.show()
        
        # Delete each selected assistant
        delete_count = 0
        for i, item in enumerate(selected_items):
            assistant = item.data(Qt.UserRole)
            if not assistant:
                continue
            
            try:
                # Delete assistant in the current thread - this might be slow for many assistants
                self.client.beta.assistants.delete(assistant.id)
                delete_count += 1
                
                # Update progress if multiple deletes
                if num_selected > 1:
                    progress.setValue(i + 1)
                    QApplication.processEvents()  # Keep UI responsive
                    
                    if progress.wasCanceled():
                        break
            except Exception as e:
                QMessageBox.warning(self, "Error", 
                                  f"Error deleting assistant {assistant.name or assistant.id}: {str(e)}")
        
        # Close progress dialog if it was created
        if num_selected > 1:
            progress.close()
        
        # Show summary
        if delete_count > 0:
            QMessageBox.information(self, "Deletion Complete", 
                                  f"Successfully deleted {delete_count} assistant{'s' if delete_count > 1 else ''}.")
        
        # Refresh list
        self.refresh_assistants()
    
    def toggle_assistant_for_chat(self):
        """Toggle the selected assistant for the current chat thread"""
        # Get the selected assistant
        selected_items = self.assistant_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select an assistant to toggle.")
            self.toggle_button.setChecked(False)
            return
        
        assistant = selected_items[0].data(Qt.UserRole)
        if not assistant:
            self.toggle_button.setChecked(False)
            return
        
        # If the button is now checked (toggled on)
        if self.toggle_button.isChecked():
            # Store the previously active assistant ID (to restore later)
            from src.openai_assistant import ClientConfig
            self.previous_assistant_id = ClientConfig.LEAD_ASSISTANT_ID
            
            # Set the new assistant for the chat
            from src.signals import global_signals
            global_signals.set_assistant_signal.emit(assistant.id)
            
            # Update UI to show which assistant is active
            self.status_label.setText(f"Active: {assistant.name or assistant.id[:8]+'...'}")
            self.status_label.setStyleSheet("color: #00AA00; font-weight: bold;")
            
            # Disable delete button for the active assistant
            self.delete_button.setEnabled(False)
            
            # Clear all highlights first
            for i in range(self.assistant_list.count()):
                item = self.assistant_list.item(i)
                if item and hasattr(item, 'setBackground'):
                    item.setBackground(QColor("transparent"))
            
            # Highlight the selected item in the list
            selected_items[0].setBackground(QColor("#2A4D69"))
            
            # Store the current assistant
            self.active_assistant = assistant
            
        else:  # Button is unchecked (toggled off)
            # Restore previous assistant
            from src.signals import global_signals
            from src.openai_assistant import ClientConfig
            global_signals.set_assistant_signal.emit(ClientConfig.LEAD_ASSISTANT_ID)
            
            # Update UI
            self.status_label.setText("No assistant assigned to chat")
            self.status_label.setStyleSheet("color: #888888;")
            
            # Re-enable delete button
            self.delete_button.setEnabled(True)
            
            # Remove highlighting from all items
            for i in range(self.assistant_list.count()):
                item = self.assistant_list.item(i)
                if item and hasattr(item, 'setBackground'):
                    item.setBackground(QColor("transparent"))
            
            # Clear active assistant
            self.active_assistant = None
    
    def _show_error(self, error_message):
        """Show error message"""
        QMessageBox.critical(self, "Error", error_message)
    
    def closeEvent(self, event):
        """Clean up threads when panel is closed"""
        # Wait for all worker threads to finish
        for worker in self.active_workers:
            if worker.isRunning():
                worker.wait()
        super().closeEvent(event) 

    def _filter_assistants(self):
        """Filter assistants based on search text"""
        search_text = self.search_box.text().lower()
        
        # If no search text, show all assistants
        if not search_text:
            for i in range(self.assistant_list.count()):
                self.assistant_list.item(i).setHidden(False)
            return
        
        # Filter based on search text
        for i in range(self.assistant_list.count()):
            item = self.assistant_list.item(i)
            assistant = item.data(Qt.UserRole)
            if not assistant:
                continue
            
            # Check if search text is in ID, name, or description
            match_found = False
            if search_text in assistant.id.lower():
                match_found = True
            elif assistant.name and search_text in assistant.name.lower():
                match_found = True
            elif assistant.description and search_text in assistant.description.lower():
                match_found = True
            elif assistant.instructions and search_text in assistant.instructions.lower():
                match_found = True
            
            item.setHidden(not match_found) 