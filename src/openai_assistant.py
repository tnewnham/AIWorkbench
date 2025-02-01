import os
import time
import json
import datetime
import sys
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.json import JSON
from dotenv import load_dotenv

# Load environment variables at module level
load_dotenv()

def pretty_print(response: str):
    console = Console()

    # First, check if response starts with a Markdown code block.
    if response.strip().startswith("```markdown"):
        content = "\n".join(response.split("\n")[1:-1])
        console.print(Markdown(content.strip()))
        return

    # Next, try parsing the response as JSON.
    try:
        parsed_json = json.loads(response)
        console.print(JSON.from_data(parsed_json))
    except json.JSONDecodeError:
        # If parsing as JSON fails, fall back to printing as plain text.
        console.print(response, markup=False)

class OpenAiAssistantManager:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def create_assistant(self,
                         model: str,
                         name: str = None,
                         description: str = None,
                         instructions: str = None,
                         tools: list = None,
                         tool_resources: dict = None,
                         metadata: dict = None,
                         temperature: float = 1.0,
                         top_p: float = 1.0,
                         response_format="auto"):
        return self.client.beta.assistants.create(
            model=model,
            name=name,
            description=description,
            instructions=instructions,
            tools=tools or [],
            tool_resources=tool_resources,
            metadata=metadata,
            temperature=temperature,
            top_p=top_p,
            response_format=response_format
        )

    def list_assistants(self,
                        limit: int = 20,
                        order: str = "desc",
                        after: str = None,
                        before: str = None):
        return self.client.beta.assistants.list(
            limit=limit,
            order=order,
            after=after,
            before=before
        )

    def retrieve_assistant(self, assistant_id: str):
        return self.client.beta.assistants.retrieve(assistant_id)

    def modify_assistant(self,
                         assistant_id: str,
                         model: str = None,
                         name: str = None,
                         description: str = None,
                         instructions: str = None,
                         tools: list = None,
                         tool_resources: dict = None,
                         metadata: dict = None,
                         temperature: float = 1.0,
                         top_p: float = 1.0,
                         response_format="auto"):
        return self.client.beta.assistants.update(
            assistant_id,
            model=model,
            name=name,
            description=description,
            instructions=instructions,
            tools=tools,
            tool_resources=tool_resources,
            metadata=metadata,
            temperature=temperature,
            top_p=top_p,
            response_format=response_format
        )

    def delete_assistant(self, assistant_id: str):
        return self.client.beta.assistants.delete(assistant_id)


class ClientConfig:
    """Configuration class for OpenAI assistants"""
    console = Console()
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
    
    # Debug settings based on environment
    DEBUG_MODE = ENVIRONMENT == "development"
    POLL_INTERVAL = 2 if ENVIRONMENT == "development" else 5
    
    @classmethod
    def validate_config(cls):
        """Validate that all required environment variables are set"""
        console = Console()
        required_vars = {
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        if cls.DEBUG_MODE:
            console.print("Running in DEBUG mode", style="bold green")
            console.print(f"Environment: {cls.ENVIRONMENT}", style="bold green")
            console.print(f"Poll interval: {cls.POLL_INTERVAL} seconds", style="bold green")

def initialize_chat():
    """Initialize a new chat thread using the OpenAI API."""
    console = Console()
    try:
        client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
        thread = client.beta.threads.create()
        console.print("Chat thread initialized successfully", style="bold green")
        return thread
    except Exception as e:
        console.print("Error initializing chat thread:", style="bold red")
        console.print(str(e), style="bold red")
        return None

def upload_file(client, file_path):
    console = Console()
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    try:
        console.print(f"Uploading file: {file_path}", style="bold green")
        with open(file_path, "rb") as file:
            response = client.files.create(
                file=file,
                purpose="assistants"
            )
        console.print(f"File uploaded successfully. ID: {response.id}", style="bold green")
        return response.id
    except Exception as e:
        console.print("Error uploading file:", style="bold red")
        console.print(str(e), style="bold red")
        return None

def send_user_message(thread_id, message, file_path=None):
    """Send a message to the chat thread with optional file attachment."""
    console = Console()
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    
    # Prepare message content
    content = message
    file_ids = []
    
    # Handle file upload if provided
    if file_path:
        if not os.path.exists(file_path):
            pretty_print(f"File not found: {file_path}")
            return
            
        file_id = upload_file(client, file_path)
        if file_id:
            file_ids.append(file_id)
    
    # Create message with or without file
    try:
        message_data = {
            "thread_id": thread_id,
            "role": "user",
            "content": content
        }
        if file_ids:
            message_data["file_ids"] = file_ids
            console.print("Creating message with file attachment", style="bold green")
        else:
            console.print("Creating message", style="bold green")
        
        response = client.beta.threads.messages.create(**message_data)
        console.print("Message sent successfully", style="bold green")
        return response
    except Exception as e:
        console.print("Error sending message:", style="bold red")
        console.print(str(e), style="bold red")
        return None

def start_run(thread_id, ASSISTANT_ID):
    """Start a run for the given chat thread."""
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=ASSISTANT_ID)
    return run

def save_message_file(client, content_block, base_path="data/generated"):
    console = Console()
    try:
        # Create directory if it doesn't exist
        os.makedirs(base_path, exist_ok=True)
        
        if hasattr(content_block, 'image_file'):
            file_id = content_block.image_file.file_id
            file_path = os.path.join(base_path, f"{file_id}.png")
            
            console.print(f"Downloading file: {file_id}", style="bold green")
            file_data = client.files.content(file_id)
            file_bytes = file_data.read()
            
            with open(file_path, "wb") as file:
                file.write(file_bytes)
            console.print(f"File saved to: {file_path}", style="bold green")
            return file_path
    except Exception as e:
        console.print("Error saving file:", style="bold red")
        console.print(str(e), style="bold red")
    return None

def process_message_content(client, message):
    formatted_content = []
    
    for content_block in message.content:
        if hasattr(content_block, 'text'):
            # Handle text content
            text_content = content_block.text.value
            for line in text_content.split('\n'):
                if line.strip():
                    formatted_content.append(("text", line))
        elif hasattr(content_block, 'image_file'):
            # Handle file content
            file_path = save_message_file(client, content_block)
            if file_path:
                formatted_content.append(("file", file_path))
    
    return formatted_content

def poll_run_status_and_submit_outputs(thread_id, run_id):
    """Poll the run status and submit tool outputs if required."""
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    
    start_time = datetime.datetime.now()
    while True:
        try:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            elapsed_time = datetime.datetime.now() - start_time
            elapsed_seconds = int(elapsed_time.total_seconds())
            print(f"Elapsed Time: {elapsed_seconds} seconds", end='\r')
            sys.stdout.flush()
            
            if run_status.status == 'completed':
                pretty_print("Run completed successfully\n")
                process_run_completion(client, thread_id)
                break
            elif run_status.status == 'requires_action':
                handle_required_action(client, run_status, thread_id, run_id)
            elif run_status.status == 'failed':
                handle_run_failure(run_status)
                break
            else:
                time.sleep(ClientConfig.POLL_INTERVAL)
        except Exception as e:
            pretty_print("API Error occurred:")
            pretty_print(str(e))
            if hasattr(e, 'response'):
                pretty_print("Response details:")
                pretty_print(e.response)  # Keep error response unformatted
            break

def handle_required_action(client, run_status, thread_id, run_id):
    """Handle actions required by the run status. This is a placeholder for the actual implementation."""
    console = Console()

    if run_status.required_action.type == 'submit_tool_outputs':
        tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
        console.print("Tool Calls Received:", style="bold green")
        tool_outputs = []
        for tool_call in tool_calls:
            console.print("Raw Tool Call Details:", style="bold green")
            tool_call_dict = tool_call.to_dict() if hasattr(tool_call, 'to_dict') else vars(tool_call)
            console.print(json.dumps(tool_call_dict, indent=4), style="bold green")
            
            console.print("Function Details:", style="bold green")
            console.print(f"Name: {tool_call.function.name}", style="bold green")
            
            console.print("Raw Arguments:", style="bold green")
            console.print(tool_call.function.arguments, style="bold green")
            
            console.print("Parsed Arguments:", style="bold green")
            arguments = json.loads(tool_call.function.arguments)
            console.print(json.dumps(arguments, indent=6), style="bold green")
            
            console.print(f"Executing: {tool_call.function.name}", style="bold green")
            function_output = execute_function(tool_call.function.name, arguments)
            
            tool_output = {
                "tool_call_id": tool_call.id,
                "output": json.dumps(function_output)
            }
            tool_outputs.append(tool_output)
            
            console.print("Function Output:", style="bold green")
            console.print(json.dumps(function_output, indent=6), style="bold green")
        
        client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )
        console.print("Tool outputs submitted successfully", style="bold green")

def handle_run_failure(run_status):
    """Handle the failure of a run."""
    console = Console()
    console .print("Run failed. Details:", style="bold red")
    console.print(f"Status: {run_status.status}", style="bold red")
    console.print(f"Last error: {run_status.last_error}", style="bold red")
    if hasattr(run_status, 'failed_at'):
        console.print(f"Failed at: {run_status.failed_at}", style="bold red")
    if hasattr(run_status, 'file_ids'):
        console.print(f"File IDs: {run_status.file_ids}", style="bold red")
    if hasattr(run_status, 'metadata'):
        console.print(f"Metadata: {run_status.metadata}", style="bold red")

def process_run_completion(client, thread_id):
    """Process the completion of a run."""
    console = Console()
    message_response = client.beta.threads.messages.list(thread_id=thread_id)
    
    for message in message_response.data:
        role = message.role.upper()
        console.print(f"Message from {role}:", style="bold green")
        console.print("Raw Message Content:", style="bold green")
        console.print(json.dumps(message.content, indent=4, default=str), style="bold green")
        
        # Process message content
        formatted_content = process_message_content(client, message)
        
        console.print("Formatted Content:", style="bold green")
        
        for content_type, content in formatted_content:
            if content_type == "text":
                pretty_print(content)
            elif content_type == "file":
                console.print(f"Generated file saved at: {content}", style="bold green")

def execute_function(function_name, arguments):
    """Execute the function based on the function name and arguments."""
    pretty_print(f"Executing function: {function_name} with arguments: {arguments}")
    return {"result": "Function executed successfully"}

def read_test_prompt():
    """Read the test prompt from file."""
    try:
        with open('tests/test_prompt', 'r') as file:
            return file.read().strip()
    except Exception as e:
        pretty_print("Error reading test prompt:")
        pretty_print(str(e))
        return None

def process_outline_agent_run(thread_id, run_id):
    """Process the run for the outline agent and return the last message from the assistant."""
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    
    start_time = datetime.datetime.now()
    while True:
        try:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            elapsed_time = datetime.datetime.now() - start_time
            elapsed_seconds = int(elapsed_time.total_seconds())
            print(f"Elapsed Time: {elapsed_seconds} seconds", end='\r')
            sys.stdout.flush()
            
            if run_status.status == 'completed':
                pretty_print("Run completed successfully")
                return get_last_assistant_message(client, thread_id)
            elif run_status.status == 'failed':
                handle_run_failure(run_status)
                break
            else:
                time.sleep(ClientConfig.POLL_INTERVAL)
                
        except Exception as e:
            pretty_print("API Error occurred:")
            pretty_print(str(e))
            if hasattr(e, 'response'):
                pretty_print("Response details:")
                pretty_print(e.response)  # Keep error response unformatted
            break

def get_last_assistant_message(client, thread_id):
    """Retrieve the last message from the assistant in the chat thread."""
    message_response = client.beta.threads.messages.list(thread_id=thread_id)
    last_message = ""
    
    for message in message_response.data:
        if message.role == "assistant":
            last_message = message.content[0].text.value if message.content else ""
    
    return last_message

def process_formulate_question_agent_run(thread_id, run_id):
    """Process the run for the formulate question agent and return the last message from the assistant."""
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    console = Console()
    
    start_time = datetime.datetime.now()
    while True:
        try:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            elapsed_time = datetime.datetime.now() - start_time
            elapsed_seconds = int(elapsed_time.total_seconds())
            print(f"Elapsed Time: {elapsed_seconds} seconds", end='\r')
            sys.stdout.flush()
            
            if run_status.status == 'completed':
                pretty_print("Run completed successfully")
                return get_last_assistant_message(client, thread_id)
            elif run_status.status == 'failed':
                handle_run_failure(run_status)
                break
            else:
                time.sleep(ClientConfig.POLL_INTERVAL)
                
        except Exception as e:
            console.print("API Error occurred:", style="bold red")
            console.print(str(e), style="bold red")
            if hasattr(e, 'response'):
                console.print("Response details:", style="bold red")
                pretty_print(e.response)  # Keep error response unformatted
            break

def run_vector_store_search_agent(assistant_id, vector_store_id, message_content):
    """Run the vector store search agent with the specified vector store ID."""
    console = Console()
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    
    try:
        run = client.beta.threads.create_and_run(
            assistant_id=assistant_id,
            thread={
                "messages": [
                    {"role": "user", "content": message_content}
                ]
            },
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store_id]
                }
            }
        )
        console.print("Vector Store Search Agent run started successfully", style="bold green")
        return run
    except Exception as e:
        console.print("Error running Vector Store Search Agent:", style="bold red")
        console.print(str(e), style="bold red")
        return None

def process_questions_with_search_agent(assistant_id, vector_store_id, questions_json):
    """Process a list of questions with the search agent and collect responses."""
    console = Console()
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    responses = {"questions_and_answers": []}

    try:
        # Access the list of questions from the new JSON structure
        questions = questions_json.get("questions", [])
        for question in questions:
            # Debugging: Print the question being processed
            console.print(f"Processing question: {question}", style="bold blue")

            if not question.strip():
                console.print("Skipping empty question content", style="bold blue")
                continue

            # Send the question to the search agent
            run = client.beta.threads.create_and_run(
                assistant_id=assistant_id,
                thread={
                    "messages": [
                        {"role": "user", "content": question}
                    ]
                },
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                }
            )

            # Poll the run status until it is completed
            start_time = datetime.datetime.now()
            while True:
                run_status = client.beta.threads.runs.retrieve(thread_id=run.thread_id, run_id=run.id)
                elapsed_time = datetime.datetime.now() - start_time
                elapsed_seconds = int(elapsed_time.total_seconds())
                print(f"Elapsed Time: {elapsed_seconds} seconds", end='\r')
                sys.stdout.flush()
                
                if run_status.status == 'completed':
                    console.print("Run completed successfully", style="bold green")
                    answer = get_last_assistant_message(client, run.thread_id)
                    responses["questions_and_answers"].append({
                        "question": question,
                        "answer": answer
                    })
                    break
                elif run_status.status == 'failed':
                    console.print("Run failed", style="bold red")
                    # Print detailed error information
                    if hasattr(run_status, 'last_error'):
                        console.print(f"Last error: {run_status.last_error}", style="bold red")
                    if hasattr(run_status, 'failed_at'):
                        console.print(f"Failed at: {run_status.failed_at}", style="bold red")
                    responses["questions_and_answers"].append({
                        "question": question,
                        "answer": "No response received"
                    })
                    break
                else:
                    time.sleep(ClientConfig.POLL_INTERVAL)

        console.print("Questions processed successfully", style="bold green")
        return responses
    
    except Exception as e:
        console.print("Error processing questions with search agent:", style="bold red")
        console.print(str(e), style="bold red")
        return None

def process_reviewer_agent_run(thread_id, run_id):
    """Process the run for the reviewer agent and return the last message from the assistant."""
    console = Console()
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    
    start_time = datetime.datetime.now()
    while True:
        try:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            elapsed_time = datetime.datetime.now() - start_time
            elapsed_seconds = int(elapsed_time.total_seconds())
            print(f"Elapsed Time: {elapsed_seconds} seconds", end='\r')
            sys.stdout.flush()
            
            if run_status.status == 'completed':
                console.print("Run completed successfully", style="bold green")
                return get_last_assistant_message(client, thread_id)
            elif run_status.status == 'failed':
                handle_run_failure(run_status)
                break
            else:
                time.sleep(ClientConfig.POLL_INTERVAL)
                
        except Exception as e:
            console.print("API Error occurred:", style="bold red")
            console.print(str(e), style="bold red")
            if hasattr(e, 'response'):
                console.print("Response details:", style="bold red")
                pretty_print(e.response)  # Keep error response unformatted
            break


