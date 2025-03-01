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
    result = pyqtSignal(str, object)  # result, context object
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
        # Set up progress updates - just one at the beginning
        self.signals.progress.emit("Starting analysis", 0)
        
        # Check if the assistant_config object is already provided
        assistant_config = agent_config.get("assistant_config")
        
        # If no assistant_config provided, create it based on config_type
        if not assistant_config:
            config_type = agent_config.get("CONFIG_TYPE", "research")
            
            try:
                if config_type == "financial":
                    from src.assistant_config import FinancialAssistantConfig
                    assistant_config = FinancialAssistantConfig()
                else:
                    from src.assistant_config import ResearchAssistantConfig
                    assistant_config = ResearchAssistantConfig()
                
                # Create agents if they don't exist yet
                if not assistant_config.agent_created:
                    # Avoid multiple system messages - just one is enough
                    self.signals.log.emit("Creating assistants...")
                    assistant_config.create_agents()
                
                # Store the assistant_config for future use
                agent_config["assistant_config"] = assistant_config
            except Exception as e:
                self.signals.log.emit(f"Warning: Could not initialize Assistant Config: {str(e)}")
                import traceback
                self.signals.log.emit(traceback.format_exc())
                return None
        
        # Verify that we have all required IDs
        missing_ids = []
        required_ids = ["OUTLINE_AGENT_ID", "FORMULATE_QUESTIONS_AGENT_ID", 
                       "VECTOR_STORE_SEARCH_AGENT_ID", "REVIEWER_AGENT_ID"]
        
        for id_name in required_ids:
            # Try to get from agent_config first, then from assistant_config
            if not agent_config.get(id_name):
                if hasattr(assistant_config, id_name) and getattr(assistant_config, id_name):
                    agent_config[id_name] = getattr(assistant_config, id_name)
                    self.signals.log.emit(f"Using {id_name}: {agent_config[id_name][:8]}...")
                else:
                    missing_ids.append(id_name)
        
        if missing_ids:
            self.signals.log.emit(f"Error: Missing required assistant IDs: {', '.join(missing_ids)}")
            return None
        
        # Additional properties from assistant_config
        if not agent_config.get("WRITER_AGENT_SYSTEM_MESSAGE") and hasattr(assistant_config, "WRITER_AGENT_SYSTEM_MESSAGE"):
            agent_config["WRITER_AGENT_SYSTEM_MESSAGE"] = assistant_config.WRITER_AGENT_SYSTEM_MESSAGE
        
        if not agent_config.get("WRITER_AGENT_CONFIG"):
            if hasattr(assistant_config, "writer_agent_config"):
                agent_config["WRITER_AGENT_CONFIG"] = assistant_config.writer_agent_config
            elif hasattr(assistant_config, "WRITER_AGENT_ID"):
                agent_config["WRITER_AGENT_CONFIG"] = assistant_config.WRITER_AGENT_ID
        
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
        """Run analysis in a background thread"""
        try:
            # Run the analysis - this returns a tuple (writer_chat.text, combined_message)
            result_tuple = task.run_analysis()
            
            # Extract the main result text (first item in the tuple)
            result_text = result_tuple[0] if isinstance(result_tuple, tuple) else result_tuple
            
            # Only send completion message
            self.signals.progress.emit("Analysis complete", 100)
            
            # Send result - now using the extracted text
            self.signals.result.emit(result_text, {"task": task, "full_result": result_tuple})
            
            # Call callback if provided
            if callback:
                callback(result_text, {"task": task, "full_result": result_tuple})
        except Exception as e:
            self.signals.error.emit(str(e))
            import traceback
            self.signals.log.emit(traceback.format_exc())
    
    def _cleanup_temp_dir(self, temp_dir: str):
        """Clean up the temporary directory"""
        import shutil
        try:
            shutil.rmtree(temp_dir)
            self.signals.log.emit(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            self.signals.log.emit(f"Error cleaning up temp directory: {str(e)}") 