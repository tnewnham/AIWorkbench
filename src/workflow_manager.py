#!/usr/bin/env python
"""
Workflow Manager - Connects the GUI with analysis workflows
"""
import os
import threading
from typing import List, Dict, Any, Optional, Callable

from PyQt5.QtCore import QObject, pyqtSignal

from .analyst import AnalysisTask
from src.openai_assistant import pretty_print

class WorkflowSignals(QObject):
    """Signals for workflow communication"""
    progress = pyqtSignal(str, int)  # message, percentage
    result = pyqtSignal(str, str)  # result, context
    error = pyqtSignal(str)  # error message
    log = pyqtSignal(str)  # log message

class WorkflowManager:
    """Manages execution of analysis workflows"""
    
    def __init__(self):
        self.signals = WorkflowSignals()
        self.active_threads = []
    
    def run_analysis(self, user_prompt: str, file_paths: List[str], 
                     agent_config: Dict[str, Any], callback: Optional[Callable] = None):
        """
        Run analysis workflow in a background thread
        
        Args:
            user_prompt: The user's analysis request
            file_paths: List of selected file paths
            agent_config: Configuration for the agents
            callback: Optional callback when analysis completes
        """
        # Set up progress updates
        self.signals.progress.emit("Starting analysis", 0)
        
        # Pass the list of file paths directly to the analysis task
        task = AnalysisTask(
            user_prompt=user_prompt,
            folder_path=file_paths,  # Pass file_paths list directly
            OUTLINE_AGENT_ID=agent_config.get("OUTLINE_AGENT_ID"),
            FORMULATE_QUESTIONS_AGENT_ID=agent_config.get("FORMULATE_QUESTIONS_AGENT_ID"),
            VECTOR_STORE_SEARCH_AGENT_ID=agent_config.get("VECTOR_STORE_SEARCH_AGENT_ID"),
            WRITER_AGENT_SYSTEM_MESSAGE=agent_config.get("WRITER_AGENT_SYSTEM_MESSAGE"),
            WRITER_AGENT_CONFIG=agent_config.get("WRITER_AGENT_CONFIG"),
            REVIEWER_AGENT_ID=agent_config.get("REVIEWER_AGENT_ID"),
            GOOGLE_GEMINI_API_KEY=agent_config.get("GOOGLE_GEMINI_API_KEY"),
            OPEN_AI_API_KEY=agent_config.get("OPEN_AI_API_KEY")
        )
        
        # Run the analysis task in a thread
        threading.Thread(
            target=self._run_analysis_thread,
            args=(task, callback),
            daemon=True
        ).start()
        
        return task
    
    def _create_temp_dir_with_files(self, file_paths: List[str]) -> str:
        """Create a temporary directory with symlinks to selected files"""
        import tempfile
        import platform
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix="analysis_")
        self.signals.log.emit(f"Created temporary directory: {temp_dir}")
        
        # Create symlinks or copies of files
        for src_path in file_paths:
            # Get just the filename
            filename = os.path.basename(src_path)
            # Target path in temp directory
            dst_path = os.path.join(temp_dir, filename)
            
            try:
                if platform.system() == "Windows":
                    # Windows doesn't support symlinks easily, so copy
                    import shutil
                    shutil.copy2(src_path, dst_path)
                else:
                    # Create symlink on Unix/Mac
                    os.symlink(src_path, dst_path)
                
                self.signals.log.emit(f"Added file: {filename}")
            except Exception as e:
                self.signals.log.emit(f"Error adding file {filename}: {str(e)}")
        
        return temp_dir
    
    def _run_analysis_thread(self, task: AnalysisTask, callback: Optional[Callable]):
        """Run the analysis in a thread"""
        try:
            self.signals.progress.emit("Running analysis...", 20)
            
            # Run analysis
            result, context = task.run_analysis()
            
            # Emit result
            self.signals.result.emit(result, context)
            
            # Cleanup
            self._cleanup_temp_dir(task.folder_path)
            
            # Call callback if provided
            if callback:
                callback(result, context)
                
        except Exception as e:
            self.signals.error.emit(f"Analysis error: {str(e)}")
            
            # Try to clean up
            try:
                self._cleanup_temp_dir(task.folder_path)
            except:
                pass
    
    def _cleanup_temp_dir(self, temp_dir: str):
        """Clean up the temporary directory"""
        import shutil
        try:
            shutil.rmtree(temp_dir)
            self.signals.log.emit(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            self.signals.log.emit(f"Error cleaning up temp directory: {str(e)}") 