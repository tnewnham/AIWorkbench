import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from .openai_assistant import (
    initialize_chat,
    send_user_message,
    start_run,
    process_outline_agent_run,
    process_formulate_question_agent_run,
    pretty_print,
    process_questions_with_search_agent,
    process_reviewer_agent_run,
    process_writer_agent
)
from .vector_storage import (
    create_vector_store,
    get_all_file_paths_in_directory,
    upload_files_to_vector_store_only
)



load_dotenv()

console = Console()

class fine_tune_editor:
    def __init__(self, folder_path: str):
        self.folder_path = folder_path

    def fine_tune_editor(self):
        pass

    def fine_tune_editor_run(self):
        pass
