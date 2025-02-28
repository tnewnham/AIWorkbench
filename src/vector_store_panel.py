#!/usr/bin/env python
"""
Vector Store Management Panel for the OpenAI Chat Interface.
This module provides UI components to manage OpenAI vector stores and files.
"""
import os
import sys
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QListWidget, QListWidgetItem, QSplitter, QFileDialog, QMessageBox,
    QComboBox, QLineEdit, QFormLayout, QGroupBox, QProgressBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QCheckBox,
    QApplication
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject, QThread, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor

# Import the OpenAI storage manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openai_storage_tool import OpenAIStorageManager

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
        self.storage_manager = OpenAIStorageManager()
        self.active_workers = []  # Keep track of active worker threads
        self.init_ui()
        
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
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #3E3E42; }")
        
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
        self.vs_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vs_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.vs_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.vs_list.itemSelectionChanged.connect(self.on_vector_store_selected)
        
        # Vector Store details
        details_group = QGroupBox("Vector Store Details")
        details_layout = QVBoxLayout(details_group)
        
        self.vs_details = QTextEdit()
        self.vs_details.setReadOnly(True)
        details_layout.addWidget(self.vs_details)
        
        # Vector Store files panel
        files_group = QGroupBox("Files in Vector Store")
        files_layout = QVBoxLayout(files_group)
        
        self.vs_files_table = QTableWidget()
        self.vs_files_table.setColumnCount(3)
        self.vs_files_table.setHorizontalHeaderLabels(["ID", "Created", "Status"])
        self.vs_files_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        files_layout.addWidget(self.vs_files_table)
        
        # Add files button panel
        add_files_layout = QHBoxLayout()
        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.clicked.connect(self.add_files_to_vector_store)
        self.refresh_files_btn = QPushButton("Refresh Files")
        self.refresh_files_btn.clicked.connect(self.refresh_vector_store_files)
        
        add_files_layout.addWidget(self.add_files_btn)
        add_files_layout.addWidget(self.refresh_files_btn)
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
        
        # File operations panel
        operations_layout = QHBoxLayout()
        self.refresh_files_list_btn = QPushButton("Refresh")
        self.refresh_files_list_btn.clicked.connect(self.refresh_files)
        self.delete_file_btn = QPushButton("Delete")
        self.delete_file_btn.clicked.connect(self.delete_selected_file)
        self.download_file_btn = QPushButton("Download")
        self.download_file_btn.clicked.connect(self.download_selected_file)
        
        # Purpose filter
        self.purpose_filter = QComboBox()
        self.purpose_filter.addItem("All Purposes")
        self.purpose_filter.addItem("assistants")
        self.purpose_filter.addItem("vision")
        self.purpose_filter.addItem("fine-tune")
        self.purpose_filter.addItem("batch")
        self.purpose_filter.currentTextChanged.connect(self.refresh_files)
        
        operations_layout.addWidget(QLabel("Purpose:"))
        operations_layout.addWidget(self.purpose_filter)
        operations_layout.addWidget(self.refresh_files_list_btn)
        operations_layout.addWidget(self.download_file_btn)
        operations_layout.addWidget(self.delete_file_btn)
        
        layout.addLayout(operations_layout)
        
        # Files list
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(5)
        self.files_table.setHorizontalHeaderLabels(["ID", "Filename", "Purpose", "Size", "Created"])
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.files_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.files_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.files_table.itemSelectionChanged.connect(self.on_file_selected)
        
        # File details
        self.file_details = QTextEdit()
        self.file_details.setReadOnly(True)
        
        # Add widgets to layout using splitter
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.files_table)
        splitter.addWidget(self.file_details)
        
        layout.addWidget(splitter)
        return tab
    
    def create_upload_tab(self):
        """Create the Upload tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File selection
        file_selection_group = QGroupBox("File Selection")
        file_selection_layout = QVBoxLayout(file_selection_group)
        
        select_file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_file)
        
        select_file_layout.addWidget(self.file_path_edit)
        select_file_layout.addWidget(self.browse_btn)
        file_selection_layout.addLayout(select_file_layout)
        
        # Purpose selection
        purpose_layout = QHBoxLayout()
        purpose_layout.addWidget(QLabel("Purpose:"))
        self.purpose_combo = QComboBox()
        self.purpose_combo.addItems(["assistants", "vision", "fine-tune", "batch"])
        purpose_layout.addWidget(self.purpose_combo)
        
        file_selection_layout.addLayout(purpose_layout)
        
        # Upload button
        self.upload_btn = QPushButton("Upload File")
        self.upload_btn.clicked.connect(self.upload_file)
        file_selection_layout.addWidget(self.upload_btn)
        
        # Progress bar
        self.upload_progress = QProgressBar()
        self.upload_progress.setVisible(False)
        file_selection_layout.addWidget(self.upload_progress)
        
        # Batch upload section
        batch_upload_group = QGroupBox("Batch Upload")
        batch_upload_layout = QVBoxLayout(batch_upload_group)
        
        self.batch_files_list = QListWidget()
        batch_upload_layout.addWidget(self.batch_files_list)
        
        batch_buttons_layout = QHBoxLayout()
        self.add_batch_files_btn = QPushButton("Add Files")
        self.add_batch_files_btn.clicked.connect(self.add_batch_files)
        self.clear_batch_btn = QPushButton("Clear")
        self.clear_batch_btn.clicked.connect(self.batch_files_list.clear)
        self.upload_batch_btn = QPushButton("Upload All")
        self.upload_batch_btn.clicked.connect(self.upload_batch_files)
        
        batch_buttons_layout.addWidget(self.add_batch_files_btn)
        batch_buttons_layout.addWidget(self.clear_batch_btn)
        batch_buttons_layout.addWidget(self.upload_batch_btn)
        batch_upload_layout.addLayout(batch_buttons_layout)
        
        # Layout
        layout.addWidget(file_selection_group)
        layout.addWidget(batch_upload_group)
        
        return tab
    
    def refresh_vector_stores(self):
        """Refresh the list of vector stores"""
        worker = self._create_worker(self.storage_manager.list_vector_stores)
        worker.signals.result.connect(self._on_vector_stores_loaded)
        worker.signals.error.connect(self._show_error)
        worker.start()
    
    def _on_vector_stores_loaded(self, stores_data):
        """Handle loaded vector stores data"""
        if not stores_data or "data" not in stores_data:
            return
        
        self.vs_list.setRowCount(len(stores_data["data"]))
        for row, store in enumerate(stores_data["data"]):
            # ID
            id_item = QTableWidgetItem(store["id"])
            id_item.setData(Qt.UserRole, store)
            self.vs_list.setItem(row, 0, id_item)
            
            # Name
            self.vs_list.setItem(row, 1, QTableWidgetItem(store["name"]))
            
            # Created
            created_time = datetime.fromtimestamp(store["created_at"])
            created_str = created_time.strftime("%Y-%m-%d %H:%M:%S")
            self.vs_list.setItem(row, 2, QTableWidgetItem(created_str))
            
            # Files count
            files_count = store["file_counts"]["total"]
            self.vs_list.setItem(row, 3, QTableWidgetItem(str(files_count)))
    
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
        
        store_data = selected_items[0].data(Qt.UserRole)
        if not store_data:
            return
        
        worker = self._create_worker(self.storage_manager.list_vector_store_files, store_data['id'])
        worker.signals.result.connect(self._on_vector_store_files_loaded)
        worker.signals.error.connect(self._show_error)
        worker.start()
    
    def _on_vector_store_files_loaded(self, files_data):
        """Handle loaded vector store files data"""
        self.vs_files_table.setRowCount(0)
        
        if not files_data or "data" not in files_data:
            return
        
        self.vs_files_table.setRowCount(len(files_data["data"]))
        for row, file in enumerate(files_data["data"]):
            # ID
            self.vs_files_table.setItem(row, 0, QTableWidgetItem(file.get('id', '')))
            
            # Created
            created_time = datetime.fromtimestamp(file.get('created_at', 0))
            created_str = created_time.strftime("%Y-%m-%d %H:%M:%S")
            self.vs_files_table.setItem(row, 1, QTableWidgetItem(created_str))
            
            # Status
            self.vs_files_table.setItem(row, 2, QTableWidgetItem(file.get('status', '')))
    
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
        
        confirm = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_stores)} vector store(s)?\n\n{stores_text}\n\nThis operation cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
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
        
        store_data = selected_items[0].data(Qt.UserRole)
        if not store_data:
            return
        
        # Show file selection dialog
        # This is not fully implemented yet - need to modify the API to add files to existing vector store
        QMessageBox.information(self, "Info", "This feature is coming soon.")
    
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
        """Handle loaded files data"""
        self.files_table.setRowCount(0)
        self.file_details.clear()
        
        if not files_data or "data" not in files_data:
            return
        
        self.files_table.setRowCount(len(files_data["data"]))
        for row, file in enumerate(files_data["data"]):
            # ID
            id_item = QTableWidgetItem(file["id"])
            id_item.setData(Qt.UserRole, file)
            self.files_table.setItem(row, 0, id_item)
            
            # Filename
            self.files_table.setItem(row, 1, QTableWidgetItem(file["filename"]))
            
            # Purpose
            self.files_table.setItem(row, 2, QTableWidgetItem(file["purpose"]))
            
            # Size
            size_str = f"{file['bytes']:,} bytes"
            self.files_table.setItem(row, 3, QTableWidgetItem(size_str))
            
            # Created
            created_time = datetime.fromtimestamp(file["created_at"])
            created_str = created_time.strftime("%Y-%m-%d %H:%M:%S")
            self.files_table.setItem(row, 4, QTableWidgetItem(created_str))
    
    def on_file_selected(self):
        """Handle file selection"""
        selected_items = self.files_table.selectedItems()
        if not selected_items:
            self.file_details.clear()
            return
        
        file_data = selected_items[0].data(Qt.UserRole)
        if not file_data:
            return
        
        # Display details
        details_text = f"ID: {file_data['id']}\n"
        details_text += f"Filename: {file_data['filename']}\n"
        details_text += f"Purpose: {file_data['purpose']}\n"
        details_text += f"Size: {file_data['bytes']:,} bytes\n"
        details_text += f"Created: {datetime.fromtimestamp(file_data['created_at']).strftime('%Y-%m-%d %H:%M:%S')}\n"
        if file_data.get('status'):
            details_text += f"Status: {file_data['status']}\n"
        
        self.file_details.setText(details_text)
    
    def delete_selected_file(self):
        """Delete the selected file"""
        selected_items = self.files_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a file to delete.")
            return
        
        file_data = selected_items[0].data(Qt.UserRole)
        if not file_data:
            return
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to delete file '{file_data['filename']}'?\nThis operation cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
        
        worker = self._create_worker(self.storage_manager.delete_file, file_data['id'])
        worker.signals.result.connect(lambda result: (
            QMessageBox.information(self, "Success", "File deleted successfully."),
            self.refresh_files()
        ))
        worker.signals.error.connect(self._show_error)
        worker.start()
    
    def download_selected_file(self):
        """Download the selected file"""
        selected_items = self.files_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a file to download.")
            return
        
        file_data = selected_items[0].data(Qt.UserRole)
        if not file_data:
            return
        
        # Get save location
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            file_data['filename'],
            "All Files (*.*)"
        )
        
        if not filename:
            return
        
        # Download the file
        QMessageBox.information(self, "Info", f"Downloading to {filename}...")
        
        # This is a placeholder - need to implement file download in OpenAIStorageManager
        # worker = Worker(self.storage_manager.get_file_content, file_data['id'], filename)
        # worker.signals.result.connect(lambda _: QMessageBox.information(self, "Success", "File downloaded successfully."))
        # worker.signals.error.connect(self._show_error)
        # worker.start()
    
    def browse_file(self):
        """Open file browser dialog"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            "All Files (*.*)"
        )
        
        if filename:
            self.file_path_edit.setText(filename)
    
    def upload_file(self):
        """Upload a file to OpenAI"""
        file_path = self.file_path_edit.text()
        if not file_path:
            QMessageBox.warning(self, "Error", "Please select a file to upload.")
            return
        
        purpose = self.purpose_combo.currentText()
        
        # Show progress
        self.upload_progress.setVisible(True)
        self.upload_progress.setValue(0)
        
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
        current = self.upload_progress.value()
        if current < 95:  # Don't reach 100 until we get confirmation
            self.upload_progress.setValue(current + 5)
    
    def _on_file_uploaded(self, file_data):
        """Handle uploaded file data"""
        self.progress_timer.stop()
        self.upload_progress.setValue(100)
        
        QMessageBox.information(
            self, 
            "Success", 
            f"File '{file_data.get('filename', 'unknown')}' uploaded successfully."
        )
        
        # Clear form and refresh
        self.file_path_edit.clear()
        self.upload_progress.setVisible(False)
        self.refresh_files()
    
    def _on_upload_error(self, error_message):
        """Handle upload error"""
        self.progress_timer.stop()
        self.upload_progress.setVisible(False)
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
        
        purpose = self.purpose_combo.currentText()
        
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