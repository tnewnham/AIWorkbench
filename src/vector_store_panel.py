#!/usr/bin/env python
"""
Vector Store Management Panel for the OpenAI Chat Interface.
This module provides UI components to manage OpenAI vector stores and files.
"""
import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import platform
import re
import ctypes
from pathlib import Path

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='vector_store_panel.log',
    filemode='w'
)

# Import libraries
import requests
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Import WindowsStyleHelper for Windows-specific styling
from src.windows_style_helper import WindowsStyleHelper

# Import the OpenAI client
from openai import OpenAI

# Import the OpenAI resource manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.openai_resource_manager import OpenAIResourceManager as OpenAIStorageManager

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

class VectorStorePanel(QWidget):
    """Vector Store Management Panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize signals for thread communication
        self.signals = WorkerSignals()
        
        try:
            self.storage_manager = OpenAIStorageManager()
            self.signals.error.connect(self._show_error)
            self.active_workers = []  # Keep track of active worker threads
            self.init_ui()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize the OpenAI storage manager: {str(e)}\n\n"
                f"Please check your OpenAI API key and connectivity."
            )
            # Set up a minimal UI for error state
            layout = QVBoxLayout(self)
            error_label = QLabel(
                "Vector Store panel is not available. Please check your API key and configuration."
            )
            error_label.setWordWrap(True)
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)
            
            retry_button = QPushButton("Retry Connection")
            retry_button.clicked.connect(self._retry_initialization)
            layout.addWidget(retry_button)
    
    def __del__(self):
        """Destructor to clean up threads"""
        self._cleanup_threads()
    
    def _cleanup_threads(self):
        """Clean up any running threads"""
        for worker in self.active_workers[:]:
            if worker.isRunning():
                worker.quit()
                worker.wait(1000)  # Wait up to 1 second for thread to finish
    
    def _create_worker(self, fn, *args, **kwargs):
        """Create and configure a worker thread"""
        worker = Worker(fn, *args, **kwargs)
        
        # Connect finished signal to remove from active workers
        worker.signals.finished.connect(lambda: self._remove_worker(worker))
        
        # Add to active workers
        self.active_workers.append(worker)
        
        return worker
    
    def _remove_worker(self, worker):
        """Remove a worker from the active workers list"""
        if worker in self.active_workers:
            self.active_workers.remove(worker)
    
    def init_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create tabs for different operations
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ 
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR}; 
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS}; 
            }}
            QTabBar::tab {{ 
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-bottom-color: {VSCodeStyleHelper.BORDER_COLOR};
                border-top-left-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                border-top-right-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                min-width: 8ex;
                padding: 5px 10px;
            }}
            QTabBar::tab:selected {{ 
                background-color: {VSCodeStyleHelper.BG_COLOR};
                border-bottom-color: {VSCodeStyleHelper.BG_COLOR};
            }}
            QTabBar::tab:!selected {{ 
                margin-top: 2px;
            }}
        """)
        
        # Create tabs
        self.vector_stores_tab = self.create_vector_stores_tab()
        self.files_tab = self.create_files_tab()
        self.upload_tab = self.create_upload_tab()
        
        # Add tabs to the tab widget
        self.tabs.addTab(self.vector_stores_tab, "Vector Stores")
        self.tabs.addTab(self.files_tab, "Files")
        self.tabs.addTab(self.upload_tab, "Upload")
        
        main_layout.addWidget(self.tabs)
        
        # Initialize data
        self.refresh_vector_stores()
        self.refresh_files()
    
    def create_vector_stores_tab(self):
        """Create the Vector Stores tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Add search and filter section
        search_filter_layout = QHBoxLayout()
        
        # Search field
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.vs_search_field = QLineEdit()
        self.vs_search_field.setPlaceholderText("Search by name or ID...")
        self.vs_search_field.textChanged.connect(self._filter_vector_stores)
        # Add rounded corners to search box
        self.vs_search_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                padding: 5px;
            }}
        """)
        search_layout.addWidget(self.vs_search_field)
        search_filter_layout.addLayout(search_layout)
        
        # Date filter
        date_filter_layout = QHBoxLayout()
        date_filter_layout.addWidget(QLabel("Date:"))
        
        # Date range options
        self.date_filter = QComboBox()
        self.date_filter.addItem("All Time")
        self.date_filter.addItem("Today")
        self.date_filter.addItem("Last 7 Days")
        self.date_filter.addItem("Last 30 Days")
        self.date_filter.addItem("Last 90 Days")
        self.date_filter.currentIndexChanged.connect(self._filter_vector_stores)
        # Add styling to the combo box
        self.date_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                padding: 5px;
                min-width: 100px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {VSCodeStyleHelper.BORDER_COLOR};
                border-left-style: solid;
                border-top-right-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                border-bottom-right-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
            }}
        """)
        
        date_filter_layout.addWidget(self.date_filter)
        search_filter_layout.addLayout(date_filter_layout)
        
        layout.addLayout(search_filter_layout)
        
        # Vector Store operations panel
        operations_layout = QHBoxLayout()
        self.refresh_vs_btn = QPushButton("Refresh")
        self.refresh_vs_btn.clicked.connect(self.refresh_vector_stores)
        self.create_vs_btn = QPushButton("Create")
        self.create_vs_btn.clicked.connect(self.show_create_vector_store_dialog)
        self.delete_vs_btn = QPushButton("Delete Selected")
        self.delete_vs_btn.clicked.connect(self.delete_selected_vector_store)
        self.analyze_vs_btn = QPushButton("Analyze Files")
        self.analyze_vs_btn.clicked.connect(self.analyze_vector_store_files)
        
        operations_layout.addWidget(self.refresh_vs_btn)
        operations_layout.addWidget(self.create_vs_btn)
        operations_layout.addWidget(self.delete_vs_btn)
        operations_layout.addWidget(self.analyze_vs_btn)
        
        layout.addLayout(operations_layout)
        
        # Vector Stores list and details splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Vector Stores list
        self.vs_list = QTableWidget()
        self.vs_list.setColumnCount(4)
        self.vs_list.setHorizontalHeaderLabels(["ID", "Name", "Created", "Files"])
        # Set fixed column widths
        self.vs_list.setColumnWidth(0, 180)  # ID column (was 220)
        self.vs_list.setColumnWidth(1, 183)  # Name column (was 250)
        self.vs_list.setColumnWidth(2, 115)  # Created column (was 180)
        self.vs_list.setColumnWidth(3, 50)   # Files count column (was 100)
        # Set vertical header (row numbers) width
        self.vs_list.verticalHeader().setFixedWidth(20)  # Narrow width for row numbers
        # Prevent column resizing
        header = self.vs_list.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.Fixed)
        self.vs_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.vs_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.vs_list.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Disable editing triggers
        self.vs_list.itemSelectionChanged.connect(self.on_vector_store_selected)
        # Style the table with rounded corners
        self.vs_list.setStyleSheet(f"""
            QTableWidget {{
                background-color: {VSCodeStyleHelper.BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {VSCodeStyleHelper.BG_COLOR};  /* Match table background */
                color: {VSCodeStyleHelper.TEXT_COLOR};
                padding: 5px;
                border: none;  /* Keep borders hidden */
                height: 10px;
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
        
        # Vector Store details
        details_group = QGroupBox("Vector Store Details")
        details_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {VSCodeStyleHelper.TEXT_COLOR};
            }}
        """)
        details_layout = QVBoxLayout(details_group)
        
        self.vs_details = QTextEdit()
        self.vs_details.setReadOnly(True)
        # Style the text edit
        self.vs_details.setStyleSheet(f"""
            QTextEdit {{
                background-color: {VSCodeStyleHelper.BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 5px;
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
        details_layout.addWidget(self.vs_details)
        
        # Vector Store files panel
        files_group = QGroupBox("Files in Vector Store")
        files_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {VSCodeStyleHelper.TEXT_COLOR};
            }}
        """)
        files_layout = QVBoxLayout(files_group)
        
        # Add files search field
        files_search_layout = QHBoxLayout()
        files_search_layout.addWidget(QLabel("Search Files:"))
        self.vs_files_search = QLineEdit()
        self.vs_files_search.setPlaceholderText("Search by file ID or name...")
        self.vs_files_search.textChanged.connect(self._filter_vector_store_files)
        # Style the search field
        self.vs_files_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                padding: 5px;
            }}
        """)
        files_search_layout.addWidget(self.vs_files_search)
        files_layout.addLayout(files_search_layout)
        
        # Files table
        self.vs_files_table = QTableWidget()
        self.vs_files_table.setColumnCount(4)
        self.vs_files_table.setHorizontalHeaderLabels(["Filename", "Created", "Status", "File Size"])
        # Set fixed column widths
        self.vs_files_table.setColumnWidth(0, 100)  # Filename column (was 250)
        self.vs_files_table.setColumnWidth(1, 142)  # Created column (was 180)
        self.vs_files_table.setColumnWidth(2, 80)   # Status column (was 100)
        self.vs_files_table.setColumnWidth(3, 80)   # File Size column (was 120)
        # Set vertical header (row numbers) width
        self.vs_files_table.verticalHeader().setFixedWidth(20)  # Narrow width for row numbers
        # Prevent column resizing
        header = self.vs_files_table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.Fixed)
        self.vs_files_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.vs_files_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.vs_files_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Disable editing triggers
        # Style the table
        self.vs_files_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {VSCodeStyleHelper.BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {VSCodeStyleHelper.BG_COLOR};  /* Match table background */
                color: {VSCodeStyleHelper.TEXT_COLOR};
                padding: 5px;
                border: none;  /* Keep borders hidden */
                height: 10px;  /* Consistent with other tables */
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
        
        files_layout.addWidget(self.vs_files_table)
        
        # Add files button panel
        add_files_layout = QHBoxLayout()
        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.clicked.connect(self.add_files_to_vector_store)
        self.refresh_files_btn = QPushButton("Refresh Files")
        self.refresh_files_btn.clicked.connect(self.refresh_vector_store_files)
        self.remove_files_btn = QPushButton("Remove Selected")
        self.remove_files_btn.clicked.connect(self.remove_selected_files)
        
        add_files_layout.addWidget(self.add_files_btn)
        add_files_layout.addWidget(self.refresh_files_btn)
        add_files_layout.addWidget(self.remove_files_btn)
        files_layout.addLayout(add_files_layout)
        
        # Add widgets to splitter
        splitter.addWidget(self.vs_list)
        splitter.addWidget(details_group)
        splitter.addWidget(files_group)
        
        layout.addWidget(splitter)
        return tab
    
    def create_files_tab(self):
        """Create the Files tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search and filter section
        search_filter_layout = QHBoxLayout()
        
        # Search field
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.file_search_field = QLineEdit()
        self.file_search_field.setPlaceholderText("Search by filename or ID...")
        self.file_search_field.textChanged.connect(self._filter_files)
        # Add rounded styling to search box
        self.file_search_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                padding: 5px;
            }}
        """)
        search_layout.addWidget(self.file_search_field)
        search_filter_layout.addLayout(search_layout)
        
        # Purpose filter
        purpose_layout = QHBoxLayout()
        purpose_layout.addWidget(QLabel("Purpose:"))
        self.purpose_filter = QComboBox()
        self.purpose_filter.addItem("All Purposes")
        self.purpose_filter.addItem("assistants")
        self.purpose_filter.addItem("vision")
        self.purpose_filter.addItem("fine-tune")
        self.purpose_filter.addItem("batch")
        self.purpose_filter.currentTextChanged.connect(self.refresh_files)
        # Add styling to the combo box
        self.purpose_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                padding: 5px;
                min-width: 100px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {VSCodeStyleHelper.BORDER_COLOR};
                border-left-style: solid;
                border-top-right-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                border-bottom-right-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
            }}
        """)
        purpose_layout.addWidget(self.purpose_filter)
        search_filter_layout.addLayout(purpose_layout)
        
        layout.addLayout(search_filter_layout)
        
        # File operations panel
        operations_layout = QHBoxLayout()
        self.refresh_files_btn = QPushButton("Refresh")
        self.refresh_files_btn.clicked.connect(self.refresh_files)
        self.browse_file_btn = QPushButton("Browse")
        self.browse_file_btn.clicked.connect(self.browse_file)
        self.upload_file_btn = QPushButton("Upload")
        self.upload_file_btn.clicked.connect(self.upload_file)
        self.batch_upload_btn = QPushButton("Batch Upload")
        self.batch_upload_btn.clicked.connect(self.add_batch_files)
        self.delete_file_btn = QPushButton("Delete Selected")
        self.delete_file_btn.clicked.connect(self.delete_selected_file)
        self.download_file_btn = QPushButton("Download Selected")
        self.download_file_btn.clicked.connect(self.download_selected_file)
        
        operations_layout.addWidget(self.refresh_files_btn)
        operations_layout.addWidget(self.browse_file_btn)
        operations_layout.addWidget(self.upload_file_btn)
        operations_layout.addWidget(self.batch_upload_btn)
        operations_layout.addWidget(self.delete_file_btn)
        operations_layout.addWidget(self.download_file_btn)
        
        layout.addLayout(operations_layout)
        
        # Files list and details splitter
        splitter = QSplitter(Qt.Vertical)
        
        # Files list
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["Filename", "Purpose", "Size", "Created"])
        # Set fixed column widths
        self.files_table.setColumnWidth(0, 245)  # Filename column (expanded)
        self.files_table.setColumnWidth(1, 80)   # Purpose column
        self.files_table.setColumnWidth(2, 75)   # Size column
        self.files_table.setColumnWidth(3, 115)  # Created column
        # Set vertical header (row numbers) width
        self.files_table.verticalHeader().setFixedWidth(28)  # Narrow width for row numbers
        # Prevent column resizing
        header = self.files_table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.Fixed)
        self.files_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.files_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.files_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # Disable editing triggers
        self.files_table.itemSelectionChanged.connect(self.on_file_selected)
        # Style the table
        self.files_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {VSCodeStyleHelper.BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {VSCodeStyleHelper.BG_COLOR};  /* Match table background */
                color: {VSCodeStyleHelper.TEXT_COLOR};
                padding: 5px;
                border: none;  /* Keep borders hidden */
                height: 10px;  /* Consistent with other tables */
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
        
        # File details
        details_group = QGroupBox("File Details")
        details_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {VSCodeStyleHelper.TEXT_COLOR};
            }}
        """)
        details_layout = QVBoxLayout(details_group)
        
        self.file_details = QTextEdit()
        self.file_details.setReadOnly(True)
        # Style the text edit
        self.file_details.setStyleSheet(f"""
            QTextEdit {{
                background-color: {VSCodeStyleHelper.BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 5px;
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
        details_layout.addWidget(self.file_details)
        
        # Add widgets to splitter
        splitter.addWidget(self.files_table)
        splitter.addWidget(details_group)
        
        layout.addWidget(splitter)
        return tab
    
    def create_upload_tab(self):
        """Create the Upload tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Upload section title
        title_layout = QHBoxLayout()
        title_label = QLabel("Upload Files")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_layout.addWidget(title_label)
        layout.addLayout(title_layout)
        
        # Upload form
        form_group = QGroupBox("Upload Options")
        form_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                margin-top: 10px;
                padding-top: 15px;
                padding-bottom: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {VSCodeStyleHelper.TEXT_COLOR};
            }}
        """)
        form_layout = QVBoxLayout(form_group)
        
        # File path selection
        file_path_layout = QHBoxLayout()
        file_path_layout.addWidget(QLabel("File:"))
        
        self.file_path_field = QLineEdit()
        self.file_path_field.setReadOnly(True)
        self.file_path_field.setPlaceholderText("Select a file to upload...")
        # Style the file path field
        self.file_path_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                padding: 5px;
            }}
        """)
        file_path_layout.addWidget(self.file_path_field)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_file)
        file_path_layout.addWidget(self.browse_button)
        
        form_layout.addLayout(file_path_layout)
        
        # Purpose selection
        purpose_layout = QHBoxLayout()
        purpose_layout.addWidget(QLabel("Purpose:"))
        
        self.file_purpose = QComboBox()
        self.file_purpose.addItem("assistants")
        self.file_purpose.addItem("vision")
        self.file_purpose.addItem("fine-tune")
        self.file_purpose.addItem("batch")
        # Style the purpose dropdown
        self.file_purpose.setStyleSheet(f"""
            QComboBox {{
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                padding: 5px;
                min-width: 150px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 1px;
                border-left-color: {VSCodeStyleHelper.BORDER_COLOR};
                border-left-style: solid;
                border-top-right-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                border-bottom-right-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
            }}
        """)
        purpose_layout.addWidget(self.file_purpose)
        purpose_layout.addStretch()
        
        form_layout.addLayout(purpose_layout)
        
        # Upload button
        upload_layout = QHBoxLayout()
        upload_layout.addStretch()
        
        self.upload_button = QPushButton("Upload File")
        self.upload_button.clicked.connect(self.upload_file)
        upload_layout.addWidget(self.upload_button)
        
        self.batch_button = QPushButton("Batch Upload")
        self.batch_button.clicked.connect(self.add_batch_files)
        upload_layout.addWidget(self.batch_button)
        
        form_layout.addLayout(upload_layout)
        
        # Progress section
        progress_layout = QVBoxLayout()
        progress_label = QLabel("Upload Progress:")
        progress_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        # Style the progress bar
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.MEDIUM_RADIUS};
                background-color: {VSCodeStyleHelper.SIDEBAR_BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                text-align: center;
                height: 25px;
                padding: 0px;
            }}
            QProgressBar::chunk {{
                background-color: {VSCodeStyleHelper.ACCENT_COLOR};
                border-radius: {VSCodeStyleHelper.SMALL_RADIUS};
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        
        form_layout.addLayout(progress_layout)
        
        # Add form to main layout
        layout.addWidget(form_group)
        
        # Upload log
        log_group = QGroupBox("Upload Log")
        log_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {VSCodeStyleHelper.TEXT_COLOR};
            }}
        """)
        log_layout = QVBoxLayout(log_group)
        
        self.upload_log = QTextEdit()
        self.upload_log.setReadOnly(True)
        # Style the upload log
        self.upload_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {VSCodeStyleHelper.BG_COLOR};
                color: {VSCodeStyleHelper.TEXT_COLOR};
                border: 1px solid {VSCodeStyleHelper.BORDER_COLOR};
                border-radius: {VSCodeStyleHelper.LARGE_RADIUS};
                padding: 5px;
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
        log_layout.addWidget(self.upload_log)
        
        layout.addWidget(log_group)
        
        return tab
    
    def refresh_vector_stores(self):
        """Refresh the list of vector stores"""
        worker = self._create_worker(self.storage_manager.list_vector_stores)
        worker.signals.result.connect(self._on_vector_stores_loaded)
        worker.signals.error.connect(self._show_error)
        worker.start()
    
    def _on_vector_stores_loaded(self, stores_data):
        """Process vector stores data and update the UI"""
        if not stores_data or "data" not in stores_data:
            return
        
        self.vs_list.setRowCount(len(stores_data["data"]))
        for row, store in enumerate(stores_data["data"]):
            # ID
            id_item = QTableWidgetItem(store["id"])
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            id_item.setData(Qt.UserRole, store)  # Restore user data
            self.vs_list.setItem(row, 0, id_item)
            
            # Name
            name_item = QTableWidgetItem(store["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            self.vs_list.setItem(row, 1, name_item)
            
            # Created
            created_str = datetime.fromtimestamp(store["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
            created_item = QTableWidgetItem(created_str)
            created_item.setFlags(created_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            self.vs_list.setItem(row, 2, created_item)
            
            # Files count
            files_count = store["file_counts"]["total"]
            files_count_item = QTableWidgetItem(str(files_count))
            files_count_item.setFlags(files_count_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            self.vs_list.setItem(row, 3, files_count_item)
    
    def on_vector_store_selected(self):
        """Handle vector store selection"""
        selected_items = self.vs_list.selectedItems()
        if not selected_items:
            self.vs_details.clear()
            self.vs_files_table.setRowCount(0)
            return
        
        # If multiple items selected, show count in the details panel
        if len(set(item.row() for item in selected_items)) > 1:
            selection_count = len(set(item.row() for item in selected_items))
            self.vs_details.setText(f"{selection_count} vector stores selected")
            self.vs_files_table.setRowCount(0)
            return
        
        # Otherwise, show details for the single selected store
        store_data = selected_items[0].data(Qt.UserRole)
        if not store_data:
            return
        
        # Display details
        details_text = f"ID: {store_data['id']}\n"
        details_text += f"Name: {store_data['name']}\n"
        details_text += f"Created: {datetime.fromtimestamp(store_data['created_at']).strftime('%Y-%m-%d %H:%M:%S')}\n"
        details_text += f"Size: {store_data['bytes']:,} bytes\n"
        details_text += f"Files: {store_data['file_counts']['total']} total, "
        details_text += f"{store_data['file_counts']['completed']} completed, "
        details_text += f"{store_data['file_counts']['in_progress']} in progress, "
        details_text += f"{store_data['file_counts']['failed']} failed"
        
        self.vs_details.setText(details_text)
        
        # Load files for this vector store
        self.refresh_vector_store_files()
    
    def refresh_vector_store_files(self):
        """Refresh the list of files in the selected vector store"""
        selected_items = self.vs_list.selectedItems()
        if not selected_items:
            return
        
        # Get the vector store ID from the selected item
        store_item = None
        for item in selected_items:
            if item.column() == 0:  # ID column
                store_item = item
                break
        
        if not store_item:
            return
        
        store_data = store_item.data(Qt.UserRole)
        if not store_data or not store_data.get('id'):
            return
        
        # Show a loading indicator
        self.vs_files_table.setRowCount(1)
        self.vs_files_table.setItem(0, 0, QTableWidgetItem("Loading..."))
        self.vs_files_table.setItem(0, 1, QTableWidgetItem(""))
        self.vs_files_table.setItem(0, 2, QTableWidgetItem(""))
        self.vs_files_table.setItem(0, 3, QTableWidgetItem(""))
        
        # Create a worker to fetch both vector store files and general files
        worker = self._create_worker(self._fetch_and_join_files, store_data['id'])
        worker.signals.result.connect(self._on_vector_store_files_loaded)
        worker.signals.error.connect(self._show_error)
        worker.start()
    
    def _fetch_and_join_files(self, vector_store_id):
        """Fetch vector store files and join with general files to get filenames"""
        
        # Get vector store files
        vector_store_files = self.storage_manager.list_vector_store_files(vector_store_id)
        print(f"Vector store files response type: {type(vector_store_files)}")
        if hasattr(vector_store_files, 'data'):
            print(f"Vector store files count: {len(vector_store_files.data)}")
            if vector_store_files.data:
                first_file = vector_store_files.data[0]
                print(f"First vector store file type: {type(first_file)}")
                print(f"First vector store file ID: {first_file.id}")
        
        # Get all files (which include filenames)
        all_files = self.storage_manager.list_files()
        print(f"All files response type: {type(all_files)}")
        if 'data' in all_files:
            print(f"All files count: {len(all_files['data'])}")
            if all_files['data']:
                first_file = all_files['data'][0]
                print(f"First all files type: {type(first_file)}")
                if isinstance(first_file, dict):
                    print(f"First all files keys: {first_file.keys()}")
                    print(f"First all files ID: {first_file.get('id', 'N/A')}")
                    print(f"First all files filename: {first_file.get('filename', 'N/A')}")
                    print(f"First all files bytes: {first_file.get('bytes', 'N/A')}")
        
        # Create a lookup dictionary for filenames and file sizes by file ID
        file_info_lookup = {}
        if all_files and 'data' in all_files:
            for file_data in all_files['data']:
                if 'id' in file_data:
                    file_info = {
                        'filename': file_data.get('filename', ''),
                        'bytes': file_data.get('bytes', 0)  # Get file size in bytes
                    }
                    file_info_lookup[file_data['id']] = file_info
        
        print(f"Created file info lookup with {len(file_info_lookup)} entries")
        
        # Add filename and bytes to vector store files
        if vector_store_files and hasattr(vector_store_files, 'data'):
            for file in vector_store_files.data:
                if hasattr(file, 'id') and file.id in file_info_lookup:
                    # Add filename and bytes attributes to the file object
                    file_info = file_info_lookup[file.id]
                    file.filename = file_info['filename']
                    file.bytes = file_info['bytes']
                    print(f"Set filename '{file.filename}' and size {file.bytes} bytes for file ID {file.id}")
                else:
                    # For files that don't have a match in the general files list
                    # Try to get any existing filename or use a placeholder
                    file.filename = getattr(file, 'filename', f"Unknown file ({file.id[:8]}...)")
                    file.bytes = getattr(file, 'bytes', 0)
                    print(f"No match found for file ID {file.id}, using placeholder")
        
        return vector_store_files
    
    def _on_vector_store_files_loaded(self, files_data):
        """Process vector store files data and update the UI"""
        self.vs_files_table.setRowCount(0)
        
        if not files_data or not hasattr(files_data, 'data') or not files_data.data:
            return
        
        # Set up table for multi-selection
        self.vs_files_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.vs_files_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Update column headers - Change order to [Filename, Created, Status, File Size]
        self.vs_files_table.setColumnCount(4)
        self.vs_files_table.setHorizontalHeaderLabels(["Filename", "Created", "Status", "File Size"])
        
        # Add the files to the table
        self.vs_files_table.setRowCount(len(files_data.data))
        for row, file in enumerate(files_data.data):
            # Store file ID as user data but don't show it as a column
            id_item = QTableWidgetItem(getattr(file, 'filename', ''))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            id_item.setData(Qt.UserRole, file)  # Restore user data
            self.vs_files_table.setItem(row, 0, id_item)
            
            # Filename - now first column
            created_str = datetime.fromtimestamp(file.created_at).strftime("%Y-%m-%d %H:%M:%S")
            created_item = QTableWidgetItem(created_str)
            created_item.setFlags(created_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            self.vs_files_table.setItem(row, 1, created_item)
            
            # Status - now third column
            status = getattr(file, 'status', 'unknown')
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            self.vs_files_table.setItem(row, 2, status_item)
            
            # File Size - now fourth column
            file_size_bytes = getattr(file, 'bytes', 0)
            file_size_str = self._format_file_size(file_size_bytes)
            size_item = QTableWidgetItem(file_size_str)
            size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            self.vs_files_table.setItem(row, 3, size_item)
        
        # Resize columns to fit content
        self.vs_files_table.resizeColumnsToContents()
    
    def _format_file_size(self, size_bytes):
        """Format file size in bytes to a human-readable string"""
        if size_bytes == 0:
            return "0 B"
        
        # Define size units and their thresholds
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        
        # Convert to appropriate unit
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024.0
            i += 1
        
        # Format with 2 decimal places if needed
        if i > 0:
            return f"{size_bytes:.2f} {units[i]}"
        else:
            return f"{size_bytes} {units[i]}"
    
    def show_create_vector_store_dialog(self):
        """Show dialog to create a new vector store"""
        dialog = QWidget()
        dialog.setWindowTitle("Create Vector Store")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        # Form for vector store properties
        form_layout = QFormLayout()
        
        # Name field
        self.vs_name_edit = QLineEdit()
        form_layout.addRow("Name:", self.vs_name_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.close)
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(lambda: self._create_vector_store(dialog))
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(create_btn)
        layout.addLayout(buttons_layout)
        
        dialog.setLayout(layout)
        dialog.show()
    
    def _create_vector_store(self, dialog):
        """Create a new vector store"""
        name = self.vs_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a name for the vector store.")
            return
        
        dialog.close()
        
        worker = self._create_worker(self.storage_manager.create_vector_store, name)
        worker.signals.result.connect(lambda result: (
            QMessageBox.information(self, "Success", f"Vector store '{result.get('name')}' created successfully."),
            self.refresh_vector_stores()
        ))
        worker.signals.error.connect(self._show_error)
        worker.start()
    
    def delete_selected_vector_store(self):
        """Delete the selected vector stores"""
        selected_rows = set()
        selected_stores = []
        
        # Get all selected items
        for item in self.vs_list.selectedItems():
            row = item.row()
            if row not in selected_rows:
                selected_rows.add(row)
                store_data = self.vs_list.item(row, 0).data(Qt.UserRole)
                if store_data:
                    selected_stores.append(store_data)
        
        if not selected_stores:
            # Update details text instead of showing a popup
            self.vs_details.setPlainText("Error: Please select at least one vector store to delete.")
            return
        
        # Confirm deletion
        stores_text = "\n".join([f"• {store['name']} ({store['id']})" for store in selected_stores])
        
        confirm_dialog = QMessageBox(
            QMessageBox.Question,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_stores)} vector store(s)?\n\n{stores_text}\n\nThis operation cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            self
        )
        confirm_dialog.setDefaultButton(QMessageBox.No)
        
        # Set dark title bar for confirmation dialog
        if platform.system() == "Windows":
            QTimer.singleShot(0, lambda: WindowsStyleHelper.set_dark_title_bar(int(confirm_dialog.winId())))
        
        if confirm_dialog.exec_() != QMessageBox.Yes:
            return
        
        # Add a progress bar to the details panel if it doesn't exist
        if not hasattr(self, 'progress_bar'):
            self.progress_bar = QProgressBar()
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setRange(0, len(selected_stores))
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("%v/%m")  # Show as "current/total"
            # Add to layout just above details_text
            details_layout = self.vs_details.parent().layout()
            details_layout.insertWidget(details_layout.indexOf(self.vs_details), self.progress_bar)
        else:
            self.progress_bar.show()
            self.progress_bar.setRange(0, len(selected_stores))
            self.progress_bar.setValue(0)
        
        # Track deletion progress
        self.deletion_progress = 0
        self.total_to_delete = len(selected_stores)
        self.deletion_success = 0
        self.deletion_errors = []
        
        # Set initial status
        self.vs_details.setPlainText(f"Deleting {self.total_to_delete} vector stores...\n\n")
        
        # Process each deletion in sequence
        for store in selected_stores:
            try:
                # Update status in the details text
                current_text = self.vs_details.toPlainText()
                self.vs_details.setPlainText(f"{current_text}Deleting {store['name']} ({store['id']})...\n")
                
                # Delete synchronously to avoid overwhelming the API
                try:
                    # Assume deletion is successful if no exception is raised
                    self.storage_manager.delete_vector_store(store['id'])
                    self.deletion_success += 1
                    self.vs_details.setPlainText(f"{self.vs_details.toPlainText()}✓ Successfully deleted.\n")
                except Exception as api_error:
                    error_msg = f"API error: {str(api_error)}"
                    self.deletion_errors.append(error_msg)
                    self.vs_details.setPlainText(f"{self.vs_details.toPlainText()}✗ {error_msg}\n")
            except Exception as e:
                error_msg = f"Error deleting {store['name']}: {str(e)}"
                self.deletion_errors.append(error_msg)
                self.vs_details.setPlainText(f"{self.vs_details.toPlainText()}✗ {error_msg}\n")
            
            # Update progress
            self.deletion_progress += 1
            self.progress_bar.setValue(self.deletion_progress)
            QApplication.processEvents()  # Keep UI responsive
        
        # Show final result in details
        if self.deletion_errors:
            self.vs_details.setPlainText(
                f"{self.vs_details.toPlainText()}\n"
                f"Deletion Complete: {self.deletion_success} of {self.total_to_delete} vector stores deleted successfully.\n\n"
                f"Errors occurred during deletion:\n{chr(10).join(self.deletion_errors)}"
            )
        else:
            self.vs_details.setPlainText(
                f"{self.vs_details.toPlainText()}\n"
                f"Deletion Complete: All {self.deletion_success} vector stores deleted successfully."
            )
        
        # Hide progress bar after completion
        QTimer.singleShot(3000, lambda: self.progress_bar.hide() if hasattr(self, 'progress_bar') else None)
        
        # Refresh vector store list
        self.refresh_vector_stores()
    
    def add_files_to_vector_store(self):
        """Add files to the selected vector store"""
        selected_items = self.vs_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a vector store first.")
            return
        
        # Get the vector store ID from the selected item
        store_item = None
        for item in selected_items:
            if item.column() == 0:  # ID column
                store_item = item
                break
            
        if not store_item:
            QMessageBox.warning(self, "Error", "Please select a valid vector store.")
            return
        
        store_data = store_item.data(Qt.UserRole)
        if not store_data or not store_data.get('id'):
            QMessageBox.warning(self, "Error", "Invalid vector store selection.")
            return
        
        vector_store_id = store_data['id']
        
        # Create dialog to choose between local files and OpenAI files
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Files to Vector Store")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Options
        local_files_radio = QRadioButton("Upload Local Files")
        openai_files_radio = QRadioButton("Select from OpenAI Files")
        local_files_radio.setChecked(True)
        
        layout.addWidget(QLabel("Choose file source:"))
        layout.addWidget(local_files_radio)
        layout.addWidget(openai_files_radio)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        continue_btn = QPushButton("Continue")
        continue_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(continue_btn)
        
        layout.addLayout(button_layout)
        
        # Connect buttons
        cancel_btn.clicked.connect(dialog.reject)
        continue_btn.clicked.connect(dialog.accept)
        
        # Show dialog
        if dialog.exec_() != QDialog.Accepted:
            return
        
        # Handle the selected option
        if local_files_radio.isChecked():
            self._add_local_files_to_vector_store(vector_store_id)
        else:
            self._add_openai_files_to_vector_store(vector_store_id)

    def _add_local_files_to_vector_store(self, vector_store_id):
        """Add local files to a vector store"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Add",
            "",
            "All Files (*.*)"
        )
        
        if not file_paths:
            return
        
        # Show progress dialog
        progress = QProgressDialog("Uploading files to vector store...", "Cancel", 0, len(file_paths), self)
        progress.setWindowTitle("Uploading Files")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        # Create a worker to upload the files
        def upload_files():
            results = []
            for i, file_path in enumerate(file_paths):
                try:
                    # First upload the file to OpenAI
                    with open(file_path, "rb") as file:
                        upload_response = self.storage_manager.client.files.create(
                            file=file,
                            purpose="assistants"
                        )
                        
                    # Wait for the file to process
                    file_id = upload_response.id
                    
                    # Now attach the file to the vector store
                    response = self.storage_manager.client.beta.vector_stores.files.create(
                        vector_store_id=vector_store_id,
                        file_id=file_id
                    )
                    
                    results.append(response)
                    progress.setValue(i + 1)
                    
                    if progress.wasCanceled():
                        break
                        
                except Exception as e:
                    self.signals.error.emit(str(e))
                    
            return results
        
        worker = self._create_worker(upload_files)
        worker.signals.error.connect(self._show_error)
        worker.signals.finished.connect(progress.close)
        worker.signals.finished.connect(lambda: self.refresh_vector_store_files())
        worker.start()

    def _add_openai_files_to_vector_store(self, vector_store_id):
        """Add existing OpenAI files to a vector store"""
        # Create a file selection dialog
        file_dialog = QDialog(self)
        file_dialog.setWindowTitle("Select Files to Add")
        file_dialog.setMinimumWidth(600)
        file_dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(file_dialog)
        
        # Search field
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        search_field = QLineEdit()
        search_field.setPlaceholderText("Search by filename...")
        search_layout.addWidget(search_field)
        layout.addLayout(search_layout)
        
        # Create scroll area for checkboxes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        checkbox_container = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_container)
        scroll_area.setWidget(checkbox_container)
        layout.addWidget(scroll_area)
        
        checkboxes = []  # To store references to checkboxes
        
        # Buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        deselect_all_btn = QPushButton("Deselect All")
        add_btn = QPushButton("Add Selected")
        cancel_btn = QPushButton("Cancel")
        
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Show a loading progress dialog while fetching files
        progress = QProgressDialog("Loading files...", "Cancel", 0, 100, self)
        progress.setWindowTitle("Loading Files")
        progress.setWindowModality(Qt.WindowModal)
        progress.setValue(0)
        progress.show()
        
        def populate_files(files_data):
            progress.close()
            
            if not files_data or "data" not in files_data or not files_data["data"]:
                QMessageBox.information(file_dialog, "No Files", "No files found.")
                file_dialog.reject()
                return
                
            # Clear existing checkboxes
            for i in reversed(range(checkbox_layout.count())):
                widget = checkbox_layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()
                    
            checkboxes.clear()
            
            # Add checkboxes for each file
            for file in files_data["data"]:
                filename = file.get("filename", "Unnamed")
                created = datetime.fromtimestamp(file.get("created_at", 0)).strftime("%Y-%m-%d")
                purpose = file.get("purpose", "unknown")
                
                checkbox = QCheckBox(f"{filename} ({created}) - {purpose}")
                checkbox.setProperty("file_id", file.get("id"))
                checkbox_layout.addWidget(checkbox)
                checkboxes.append(checkbox)
            
            # Apply initial filter
            apply_search_filter("")
        
        def apply_search_filter(search_text):
            search_text = search_text.lower()
            for checkbox in checkboxes:
                if search_text and search_text not in checkbox.text().lower():
                    checkbox.setVisible(False)
                else:
                    checkbox.setVisible(True)
        
        def select_all():
            for checkbox in checkboxes:
                if checkbox.isVisible():
                    checkbox.setChecked(True)
        
        def deselect_all():
            for checkbox in checkboxes:
                if checkbox.isVisible():
                    checkbox.setChecked(False)
        
        def add_selected_files():
            selected_file_ids = []
            for checkbox in checkboxes:
                if checkbox.isChecked():
                    file_id = checkbox.property("file_id")
                    if file_id:
                        selected_file_ids.append(file_id)
            
            if not selected_file_ids:
                QMessageBox.warning(file_dialog, "No Selection", "Please select at least one file.")
                return
            
            # Close the dialog and proceed with adding files
            file_dialog.accept()
            
            # Show progress dialog for adding files
            add_progress = QProgressDialog(
                "Adding files to vector store...", "Cancel", 0, len(selected_file_ids), self
            )
            add_progress.setWindowTitle("Adding Files")
            add_progress.setWindowModality(Qt.WindowModal)
            add_progress.show()
            
            def add_files_to_store():
                results = []
                for i, file_id in enumerate(selected_file_ids):
                    try:
                        response = self.storage_manager.client.beta.vector_stores.files.create(
                            vector_store_id=vector_store_id,
                            file_id=file_id
                        )
                        results.append(response)
                        add_progress.setValue(i + 1)
                        
                        if add_progress.wasCanceled():
                            break
                            
                    except Exception as e:
                        self.signals.error.emit(str(e))
                        
                return results
            
            add_worker = self._create_worker(add_files_to_store)
            add_worker.signals.error.connect(self._show_error)
            add_worker.signals.finished.connect(add_progress.close)
            add_worker.signals.finished.connect(lambda: self.refresh_vector_store_files())
            add_worker.start()
        
        # Connect signals
        search_field.textChanged.connect(apply_search_filter)
        select_all_btn.clicked.connect(select_all)
        deselect_all_btn.clicked.connect(deselect_all)
        add_btn.clicked.connect(add_selected_files)
        cancel_btn.clicked.connect(file_dialog.reject)
        
        # Create a worker to fetch files
        def get_files():
            purpose = None  # Get all files
            return self.storage_manager.list_files(purpose)
        
        worker = self._create_worker(get_files)
        
        # Connect worker signals
        worker.signals.result.connect(populate_files)
        worker.signals.error.connect(lambda e: (progress.close(), self._show_error(e)))
        worker.start()
        
        # Show dialog (will block until accepted or rejected)
        file_dialog.exec_()
    
    def refresh_files(self):
        """Refresh the list of files"""
        purpose = self.purpose_filter.currentText()
        if purpose == "All Purposes":
            purpose = None
        
        worker = self._create_worker(self.storage_manager.list_files, purpose)
        worker.signals.result.connect(self._on_files_loaded)
        worker.signals.error.connect(self._show_error)
        worker.start()
    
    def _on_files_loaded(self, files_data):
        """Process files data and update the UI"""
        self.files_table.setRowCount(0)
        self.file_details.clear()
        
        if not files_data or "data" not in files_data:
            return
        
        self.files_table.setRowCount(len(files_data["data"]))
        for row, file in enumerate(files_data["data"]):
            # Filename (now column 0)
            filename_item = QTableWidgetItem(file["filename"])
            filename_item.setFlags(filename_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            filename_item.setData(Qt.UserRole, file)  # Store file data for reference
            self.files_table.setItem(row, 0, filename_item)
            
            # Purpose (now column 1)
            purpose_item = QTableWidgetItem(file["purpose"])
            purpose_item.setFlags(purpose_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            self.files_table.setItem(row, 1, purpose_item)
            
            # Size (now column 2)
            size_str = self._format_file_size(file.get("bytes", 0))
            size_item = QTableWidgetItem(size_str)
            size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            self.files_table.setItem(row, 2, size_item)
            
            # Created (now column 3)
            created_str = datetime.fromtimestamp(file["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
            created_item = QTableWidgetItem(created_str)
            created_item.setFlags(created_item.flags() & ~Qt.ItemIsEditable)  # Make item not editable
            self.files_table.setItem(row, 3, created_item)
    
    def on_file_selected(self):
        """Handle file selection"""
        selected_items = self.files_table.selectedItems()
        if not selected_items:
            self.file_details.clear()
            return
        
        # If multiple items selected, show count in the details panel
        if len(set(item.row() for item in selected_items)) > 1:
            selection_count = len(set(item.row() for item in selected_items))
            self.file_details.setText(f"{selection_count} files selected")
            return
        
        # Otherwise, show details for the single selected file
        file_data = selected_items[0].data(Qt.UserRole)
        if not file_data:
            return
        
        # Display details
        details_text = f"ID: {file_data.get('id', '')}\n"
        details_text += f"Filename: {file_data.get('filename', '')}\n"
        details_text += f"Purpose: {file_data.get('purpose', '')}\n"
        
        # Format size
        file_size = file_data.get('bytes', 0)
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.2f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.2f} MB"
        
        details_text += f"Size: {size_str}\n"
        
        created_time = datetime.fromtimestamp(file_data.get('created_at', 0))
        details_text += f"Created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if 'status' in file_data:
            details_text += f"Status: {file_data.get('status', '')}\n"
        
        self.file_details.setText(details_text)
    
    def delete_selected_file(self):
        """Delete the selected file(s)"""
        selected_items = self.files_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select at least one file to delete.")
            return
        
        # Get unique rows
        selected_rows = set(item.row() for item in selected_items)
        
        # Collect file IDs to delete
        file_ids = []
        filenames = []
        for row in selected_rows:
            filename_item = self.files_table.item(row, 0)  # Column 0 is now Filename
            if not filename_item:
                continue
            
            file_data = filename_item.data(Qt.UserRole)
            if not file_data:
                continue
            
            file_ids.append(file_data.get('id'))
            filenames.append(file_data.get('filename', f"File {file_data.get('id')[:8]}..."))
        
        if not file_ids:
            QMessageBox.warning(self, "Error", "No valid files selected for deletion.")
            return
        
        # Confirmation message
        files_str = "\n".join(filenames[:10])
        if len(filenames) > 10:
            files_str += f"\n... and {len(filenames) - 10} more"
        
        confirm_dialog = QMessageBox(
            QMessageBox.Question,
            "Confirm Deletion",
            f"Are you sure you want to delete the following {len(file_ids)} file(s)?\n\n{files_str}",
            QMessageBox.Yes | QMessageBox.No,
            self
        )
        confirm_dialog.setDefaultButton(QMessageBox.No)
        
        # Set dark title bar for confirmation dialog
        if platform.system() == "Windows":
            QTimer.singleShot(0, lambda: WindowsStyleHelper.set_dark_title_bar(int(confirm_dialog.winId())))
        
        if confirm_dialog.exec_() != QMessageBox.Yes:
            return
        
        # Show progress dialog
        progress = QProgressDialog(
            "Deleting files...", "Cancel", 0, len(file_ids), self
        )
        progress.setWindowTitle("Deleting Files")
        progress.setWindowModality(Qt.WindowModal)
        
        # Set dark title bar for progress dialog
        if platform.system() == "Windows":
            QTimer.singleShot(0, lambda: WindowsStyleHelper.set_dark_title_bar(int(progress.winId())))
        
        progress.show()
        
        # Delete files in a worker thread
        def delete_files():
            results = []
            for i, file_id in enumerate(file_ids):
                try:
                    result = self.storage_manager.delete_file(file_id)
                    results.append(result)
                    progress.setValue(i + 1)
                    
                    if progress.wasCanceled():
                        break
                    
                except Exception as e:
                    self.signals.error.emit(str(e))
                
            return results
        
        worker = self._create_worker(delete_files)
        worker.signals.error.connect(self._show_error)
        worker.signals.finished.connect(progress.close)
        worker.signals.finished.connect(lambda: self.refresh_files())
        worker.start()
    
    def download_selected_file(self):
        """Download the selected file(s)"""
        selected_items = self.files_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select at least one file to download.")
            return
        
        # Get unique rows
        selected_rows = set(item.row() for item in selected_items)
        
        # Collect file data for download
        file_data_list = []
        for row in selected_rows:
            filename_item = self.files_table.item(row, 0)  # Column 0 is now Filename
            if not filename_item:
                continue
            
            file_data = filename_item.data(Qt.UserRole)
            if not file_data:
                continue
            
            file_data_list.append(file_data)
        
        if not file_data_list:
            QMessageBox.warning(self, "Error", "No valid files selected for download.")
            return
        
        # If only one file, download directly
        if len(file_data_list) == 1:
            file_data = file_data_list[0]
            # Choose download directory
            download_dir = QFileDialog.getExistingDirectory(
                self, "Select Folder for Download", ""
            )
            
            if not download_dir:
                return
            
            # Construct the full path
            file_path = os.path.join(download_dir, file_data.get('filename', f"file_{file_data.get('id')}.txt"))
            
            # Show progress dialog
            progress = QProgressDialog(
                f"Downloading {file_data.get('filename')}...", 
                "Cancel", 0, 100, self
            )
            progress.setWindowTitle("Downloading File")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Create a worker to download the file
            def download_file():
                try:
                    content = self.storage_manager.get_file_content(
                        file_data.get('id'), output_path=file_path
                    )
                    return {"success": True, "path": file_path}
                except Exception as e:
                    self.signals.error.emit(str(e))
                    return {"success": False, "error": str(e)}
            
            worker = self._create_worker(download_file)
            worker.signals.result.connect(lambda result: (
                progress.close(),
                QMessageBox.information(
                    self, 
                    "Download Complete", 
                    f"File downloaded successfully to:\n{file_path}" if result.get('success') else f"Error: {result.get('error')}"
                )
            ))
            worker.signals.error.connect(lambda e: (
                progress.close(),
                self._show_error(e)
            ))
            worker.start()
        else:
            # Multiple files - choose download directory
            download_dir = QFileDialog.getExistingDirectory(
                self, "Select Folder for Download", ""
            )
            
            if not download_dir:
                return
            
            # Show progress dialog for all files
            progress = QProgressDialog(
                f"Downloading {len(file_data_list)} files...", 
                "Cancel", 0, len(file_data_list), self
            )
            progress.setWindowTitle("Downloading Files")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Create a worker to download all files
            def download_files():
                results = []
                for i, file_data in enumerate(file_data_list):
                    try:
                        if progress.wasCanceled():
                            break
                        
                        # Update progress dialog
                        progress.setValue(i)
                        progress.setLabelText(f"Downloading {file_data.get('filename')}...")
                        
                        # Construct the full path
                        file_path = os.path.join(download_dir, file_data.get('filename', f"file_{file_data.get('id')}.txt"))
                        
                        # Download the file
                        content = self.storage_manager.get_file_content(
                            file_data.get('id'), output_path=file_path
                        )
                        
                        results.append({
                            "success": True,
                            "path": file_path,
                            "filename": file_data.get('filename')
                        })
                        
                    except Exception as e:
                        results.append({
                            "success": False,
                            "error": str(e),
                            "filename": file_data.get('filename')
                        })
                        self.signals.error.emit(str(e))
                
                return results
            
            worker = self._create_worker(download_files)
            worker.signals.result.connect(lambda results: (
                progress.close(),
                self._show_download_summary(results, download_dir)
            ))
            worker.signals.error.connect(lambda e: (
                progress.close(),
                self._show_error(e)
            ))
            worker.start()

    def _show_download_summary(self, results, download_dir):
        """Show a summary of download results"""
        success_count = sum(1 for r in results if r.get('success'))
        failed_count = len(results) - success_count
        
        message = f"Download summary:\n\n"
        message += f"Successfully downloaded: {success_count} files\n"
        if failed_count > 0:
            message += f"Failed: {failed_count} files\n\n"
            message += "Failed files:\n"
            for result in results:
                if not result.get('success'):
                    message += f"- {result.get('filename')}: {result.get('error')}\n"
        
        message += f"\nFiles were saved to:\n{download_dir}"
        
        QMessageBox.information(self, "Download Complete", message)
    
    def browse_file(self):
        """Open file browser dialog"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*.*)"
        )
        
        if filename:
            self.file_path_field.setText(filename)
    
    def upload_file(self):
        """Upload a file to OpenAI"""
        file_path = self.file_path_field.text()
        if not file_path:
            QMessageBox.warning(self, "Error", "Please select a file to upload.")
            return
        
        purpose = self.file_purpose.currentText()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create a timer to update progress (simulated)
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress)
        self.progress_timer.start(100)
        
        # Start upload in worker thread
        worker = self._create_worker(self.storage_manager.upload_file, file_path, purpose)
        worker.signals.result.connect(self._on_file_uploaded)
        worker.signals.error.connect(self._on_upload_error)
        worker.start()
    
    def _update_progress(self):
        """Update the progress bar (simulated)"""
        current = self.progress_bar.value()
        if current < 95:  # Don't reach 100 until we get confirmation
            self.progress_bar.setValue(current + 5)
    
    def _on_file_uploaded(self, file_data):
        """Handle uploaded file data"""
        self.progress_timer.stop()
        self.progress_bar.setValue(100)
        
        QMessageBox.information(
            self, 
            "Success", 
            f"File '{file_data.get('filename', 'unknown')}' uploaded successfully."
        )
        
        # Clear form and refresh
        self.file_path_field.clear()
        self.progress_bar.setVisible(False)
        self.refresh_files()
    
    def _on_upload_error(self, error_message):
        """Handle upload error"""
        self.progress_timer.stop()
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Upload Error", f"Error uploading file: {error_message}")
    
    def add_batch_files(self):
        """Add files to batch upload"""
        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "All Files (*.*)"
        )
        
        if filenames:
            for filename in filenames:
                if self.batch_files_list.findItems(filename, Qt.MatchExactly):
                    continue  # Skip if already in list
                self.batch_files_list.addItem(filename)
    
    def upload_batch_files(self):
        """Upload all files in the batch"""
        if self.batch_files_list.count() == 0:
            QMessageBox.warning(self, "Error", "Please add files to the batch.")
            return
        
        purpose = self.file_purpose.currentText()
        
        # TODO: Implement batch upload with progress tracking
        QMessageBox.information(self, "Info", "Batch upload is coming soon.")
    
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

    def analyze_vector_store_files(self):
        """Analyze files in the selected vector store"""
        selected_items = self.vs_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a vector store first.")
            return
        
        store_data = selected_items[0].data(Qt.UserRole)
        if not store_data:
            return
        
        # Get the files from this vector store
        # This will need to be implemented in the OpenAIStorageManager class
        # to download the files from the vector store
        
        # For now, show a dialog explaining this feature is coming soon
        QMessageBox.information(
            self,
            "Coming Soon",
            "Direct analysis of vector store files will be available in a future update."
        )

    def _filter_vector_stores(self):
        """Filter the vector stores list based on search text and date filter"""
        search_text = self.vs_search_field.text().lower()
        date_filter = self.date_filter.currentText()
        
        # Get the current timestamp for date filtering
        now = datetime.now().timestamp()
        one_day = 24 * 60 * 60
        
        # Calculate the cutoff time based on the selected filter
        if date_filter == "Today":
            cutoff_time = now - one_day
        elif date_filter == "Last 7 Days":
            cutoff_time = now - (7 * one_day)
        elif date_filter == "Last 30 Days":
            cutoff_time = now - (30 * one_day)
        elif date_filter == "Last 90 Days":
            cutoff_time = now - (90 * one_day)
        else:
            cutoff_time = 0  # All time
        
        # Loop through all rows and apply filters
        for row in range(self.vs_list.rowCount()):
            # Get the store data from the ID column item
            id_item = self.vs_list.item(row, 0)
            if not id_item:
                continue
            
            store_data = id_item.data(Qt.UserRole)
            if not store_data:
                continue
            
            # Check if the store matches the search text
            store_id = store_data.get('id', '').lower()
            store_name = store_data.get('name', '').lower()
            
            matches_search = (not search_text or 
                             search_text in store_id or 
                             search_text in store_name)
            
            # Check if the store matches the date filter
            created_at = store_data.get('created_at', 0)
            matches_date = created_at >= cutoff_time
            
            # Show/hide the row based on the filters
            self.vs_list.setRowHidden(row, not (matches_search and matches_date))

    def _filter_vector_store_files(self):
        """Filter the vector store files table based on search text"""
        search_text = self.vs_files_search.text().lower()
        
        for row in range(self.vs_files_table.rowCount()):
            # Get file ID and filename for filtering
            id_item = self.vs_files_table.item(row, 0)
            filename_item = self.vs_files_table.item(row, 3)
            
            if not id_item:
                continue
            
            file_id = id_item.text().lower()
            filename = filename_item.text().lower() if filename_item else ""
            
            # Show/hide the row based on the search text
            # Fix: properly structure the boolean expression and pass it as the second argument
            should_hide = bool(search_text and not (search_text in file_id or search_text in filename))
            self.vs_files_table.setRowHidden(row, should_hide)

    def remove_selected_files(self):
        """Remove selected files from the vector store"""
        # Get the selected vector store
        vs_selected_items = self.vs_list.selectedItems()
        if not vs_selected_items:
            QMessageBox.warning(self, "Error", "Please select a vector store first.")
            return
        
        # Get the vector store ID from the selected item
        store_item = None
        for item in vs_selected_items:
            if item.column() == 0:  # ID column
                store_item = item
                break
            
        if not store_item:
            QMessageBox.warning(self, "Error", "Please select a valid vector store.")
            return
        
        store_data = store_item.data(Qt.UserRole)
        if not store_data or not store_data.get('id'):
            QMessageBox.warning(self, "Error", "Invalid vector store selection.")
            return
        
        vector_store_id = store_data['id']
        
        # Get selected files
        selected_ranges = self.vs_files_table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self, "Error", "Please select at least one file to remove.")
            return
        
        # Collect all selected rows
        selected_rows = set()
        for selection_range in selected_ranges:
            for row in range(selection_range.topRow(), selection_range.bottomRow() + 1):
                selected_rows.add(row)
        
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Please select at least one file to remove.")
            return
        
        # Get file IDs to remove
        file_ids = []
        for row in selected_rows:
            id_item = self.vs_files_table.item(row, 0)
            if id_item:
                file_ids.append(id_item.text())
        
        # Confirm deletion
        confirm_dialog = QMessageBox(
            QMessageBox.Question,
            "Confirm Removal",
            f"Are you sure you want to remove {len(file_ids)} file(s) from this vector store?",
            QMessageBox.Yes | QMessageBox.No,
            self
        )
        confirm_dialog.setDefaultButton(QMessageBox.No)
        
        # Set dark title bar for confirmation dialog
        if platform.system() == "Windows":
            QTimer.singleShot(0, lambda: WindowsStyleHelper.set_dark_title_bar(int(confirm_dialog.winId())))
        
        if confirm_dialog.exec_() != QMessageBox.Yes:
            return
            
        # Show progress dialog
        progress = QProgressDialog(
            "Removing files...", "Cancel", 0, len(file_ids), self
        )
        progress.setWindowTitle("Removing Files")
        progress.setWindowModality(Qt.WindowModal)
        
        # Set dark title bar for progress dialog
        if platform.system() == "Windows":
            QTimer.singleShot(0, lambda: WindowsStyleHelper.set_dark_title_bar(int(progress.winId())))
            
        progress.show()
        
        # Create a worker to remove the files
        def remove_files():
            results = []
            for i, file_id in enumerate(file_ids):
                try:
                    response = self.storage_manager.client.beta.vector_stores.files.delete(
                        vector_store_id=vector_store_id,
                        file_id=file_id
                    )
                    results.append(response)
                    progress.setValue(i + 1)
                    
                    if progress.wasCanceled():
                        break
                    
                except Exception as e:
                    self.signals.error.emit(str(e))
                
            return results
        
        worker = self._create_worker(remove_files)
        worker.signals.error.connect(self._show_error)
        worker.signals.finished.connect(progress.close)
        worker.signals.finished.connect(lambda: self.refresh_vector_store_files())
        worker.start()

    def _filter_files(self):
        """Filter the files table based on search text and date filter"""
        search_text = self.file_search_field.text().lower()
        date_filter = self.file_date_filter.currentText()
        
        # Get the current timestamp for date filtering
        now = datetime.now().timestamp()
        one_day = 24 * 60 * 60
        
        # Calculate the cutoff time based on the selected filter
        if date_filter == "Today":
            cutoff_time = now - one_day
        elif date_filter == "Last 7 Days":
            cutoff_time = now - (7 * one_day)
        elif date_filter == "Last 30 Days":
            cutoff_time = now - (30 * one_day)
        elif date_filter == "Last 90 Days":
            cutoff_time = now - (90 * one_day)
        else:
            cutoff_time = 0  # All time
        
        # Loop through all rows and apply filters
        for row in range(self.files_table.rowCount()):
            # Get the file data from the Filename column item
            filename_item = self.files_table.item(row, 0)  # Column 0 is now Filename
            if not filename_item:
                continue
            
            file_data = filename_item.data(Qt.UserRole)
            if not file_data:
                continue
            
            # Check if the file matches the search text
            file_id = file_data.get('id', '').lower()
            filename = file_data.get('filename', '').lower()
            
            matches_search = (not search_text or 
                             search_text in file_id or 
                             search_text in filename)
            
            # Check if the file matches the date filter
            created_at = file_data.get('created_at', 0)
            matches_date = created_at >= cutoff_time
            
            # Show/hide the row based on the filters
            self.files_table.setRowHidden(row, not (matches_search and matches_date)) 

    def _retry_initialization(self):
        """Retry initializing the storage manager and UI"""
        try:
            self.storage_manager = OpenAIStorageManager()
            
            # Clear the current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Initialize signals and UI
            self.signals.error.connect(self._show_error)
            self.active_workers = []
            self.init_ui()
            
            QMessageBox.information(
                self,
                "Connection Successful",
                "Successfully connected to the OpenAI API. The Vector Store panel is now available."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize the OpenAI storage manager: {str(e)}\n\n"
                f"Please check your OpenAI API key and connectivity."
            )