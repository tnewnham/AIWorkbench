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
import google.generativeai as genai


load_dotenv()

console = Console()


class AnalysisTask:

    def __init__(self, user_prompt: str, folder_path: str, OUTLINE_AGENT_ID: str, FORMULATE_QUESTIONS_AGENT_ID: str, VECTOR_STORE_SEARCH_AGENT_ID: str, WRITER_AGENT_SYSTEM_MESSAGE: str, WRITER_AGENT_CONFIG: dict, REVIEWER_AGENT_ID: str, GOOGLE_GEMINI_API_KEY: str, OPEN_AI_API_KEY: str):
        self.user_prompt = user_prompt
        self.folder_path = folder_path
        self.OUTLINE_AGENT_ID = OUTLINE_AGENT_ID
        self.FORMULATE_QUESTIONS_AGENT_ID = FORMULATE_QUESTIONS_AGENT_ID
        self.VECTOR_STORE_SEARCH_AGENT_ID = VECTOR_STORE_SEARCH_AGENT_ID
        self.WRITER_AGENT_SYSTEM_MESSAGE = WRITER_AGENT_SYSTEM_MESSAGE
        self.WRITER_AGENT_CONFIG = WRITER_AGENT_CONFIG
        self.REVIEWER_AGENT_ID = REVIEWER_AGENT_ID
        self.GOOGLE_GEMINI_API_KEY = GOOGLE_GEMINI_API_KEY
        self.OPEN_AI_API_KEY = OPEN_AI_API_KEY

    def run_analysis(self):
        try:
            # Validate environment settings
            OPEN_AI_KEY = self.OPEN_AI_API_KEY
            # Initialize Gemini for token counting
            genai.configure(api_key=self.GOOGLE_GEMINI_API_KEY)
            gemini_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-thinking-exp-01-21",
                generation_config = self.WRITER_AGENT_CONFIG,
                system_instruction= self.WRITER_AGENT_SYSTEM_MESSAGE,
                tools='code_execution')
            TOKEN_LIMIT = int(os.getenv("TOKEN_LIMIT", 65536))
            TOKEN_BUFFER = int(os.getenv("TOKEN_BUFFER", 5000))

            # Create a new vector store and load files from the given folder path
            search_agent_vector_store = create_vector_store(name="search_agent_vector_store")
            if not search_agent_vector_store:
                raise RuntimeError("Failed to create vector store.")

            vector_store_id = search_agent_vector_store.id
            file_paths = get_all_file_paths_in_directory(self.folder_path)
            upload_files_to_vector_store_only(vector_store_id, file_paths)

            # 1. Outline Agent
            outline_chat = initialize_chat()
            if not outline_chat:
                raise RuntimeError("Failed to initialize chat for outline.")

            send_user_message(outline_chat.id, self.user_prompt)
            outline_run = start_run(outline_chat.id, self.OUTLINE_AGENT_ID)
            if not outline_run:
                raise RuntimeError("Failed to start run for outline agent.")
            outline = process_outline_agent_run(outline_chat.id, outline_run.id)
            console.print("Final Output from Outline Agent:", style="bold yellow")
            pretty_print(outline)

            # 2. Formulate Questions Agent
            question_chat = initialize_chat()
            if not question_chat:
                raise RuntimeError("Failed to initialize chat for question formulation.")

            send_user_message(question_chat.id, outline)
            question_run = start_run(question_chat.id, self.FORMULATE_QUESTIONS_AGENT_ID)
            if not question_run:
                raise RuntimeError("Failed to start run for question formulation.")
            questions_string = process_formulate_question_agent_run(question_chat.id, question_run.id)
            console.print("Final Output from Formulate Question Agent:", style="bold yellow")
            pretty_print(questions_string)

            questions_json = json.loads(questions_string)

            # 3. Vector Store Search Agent
            questions_and_answers = process_questions_with_search_agent(
                assistant_id= self.VECTOR_STORE_SEARCH_AGENT_ID,
                vector_store_id=vector_store_id,
                questions_json=questions_json
            )
            if not questions_and_answers:
                raise RuntimeError("Failed to process Q&A with search agent.")

            # Prepare combined message for writer
            combined_message = self.user_prompt + "\n\n" + outline + "\n\nQuestions and Answers:\n"
            for qa in questions_and_answers["questions_and_answers"]:
                combined_message += f"\nQ: {qa['question']}\nA: {qa['answer']}\n"

            # 4. Writer Agent with Gemini
            writer_chat = process_writer_agent(gemini_model, combined_message)
            console.print("Writer Agent Response:", style="bold magenta")
            pretty_print(writer_chat.text)                        


            # 5. Loop reviewer feedback
            while True:
                reviewer_chat = initialize_chat()
                if not reviewer_chat:
                    raise RuntimeError("Failed to initialize chat for reviewer agent.")

                review_message = self.user_prompt + "\n\n" + outline + "\n\n" + writer_chat.text
                send_user_message(reviewer_chat.id, review_message)

                reviewer_run = start_run(reviewer_chat.id, self.REVIEWER_AGENT_ID)
                if not reviewer_run:
                    raise RuntimeError("Failed to start run for reviewer agent.")
                reviewer_questions_string = process_reviewer_agent_run(reviewer_chat.id, reviewer_run.id)
                pretty_print(reviewer_questions_string)

                reviewer_questions_json = json.loads(reviewer_questions_string)
                is_last_questions = reviewer_questions_json.get("last_questions", False)

                if is_last_questions:
                    console.print("Review Passed", style="bold magenta")
                    console.print("Final writer input:", style="bold magenta")
                    #pretty_print(combined_message)
                    return writer_chat.text, combined_message
                    #break

                # If not final, the reviewer wants more clarifications
                new_questions_and_answers = process_questions_with_search_agent(
                    assistant_id=self.VECTOR_STORE_SEARCH_AGENT_ID,
                    vector_store_id=vector_store_id,
                    questions_json=reviewer_questions_json
                )
                if not new_questions_and_answers:
                    raise RuntimeError("Failed to process reviewer Q&A with search agent.")

                questions_and_answers["questions_and_answers"].extend(new_questions_and_answers["questions_and_answers"])

                combined_message = self.user_prompt + "\n\n" + outline + "\n\nQuestions and Answers:\n"
                for qa in questions_and_answers["questions_and_answers"]:
                    combined_message += f"Q: {qa['question']}\nA: {qa['answer']}\n"

                combined_message_tokens_response = gemini_model.count_tokens(combined_message)
                combined_message_tokens = combined_message_tokens_response.total_tokens

                console.print(f"Combined Message Tokens: {combined_message_tokens}", style="bold yellow")

                if combined_message_tokens < (TOKEN_LIMIT - TOKEN_BUFFER):
                    writer_chat = process_writer_agent(gemini_model, combined_message)  

                    console.print("Writer Agent Response:", style="bold magenta")
                    pretty_print(writer_chat.text)
                else:
                    console.print("Token limit exceeded. Sending final message and terminating.", style="bold red")

                    writer_chat = process_writer_agent(gemini_model, combined_message)

                    console.print("Writer Agent Response:", style="bold magenta")
                    #pretty_print(writer_chat.text)
                    return writer_chat.text, combined_message
                    #break

        except Exception as e:
            console.print("An unexpected error occurred in the workflow:", style="bold red")
            console.print(f"Error Details: {str(e)}", style="bold red")