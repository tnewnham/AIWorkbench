# Standard library imports for OS interaction, timing, JSON handling, datetime operations, and system functions.
import os         
import time       
import json       
import datetime   
import sys        

# Third-party library imports for OpenAI API interaction, rich console output, and environment variable loading.
from openai import OpenAI                    
from rich.console import Console             
from rich.markdown import Markdown           
from rich.json import JSON                   
from dotenv import load_dotenv               

# Immediately load environment variables from the .env file at module import.
load_dotenv()  # Ensures environment variables are available throughout the module

def pretty_print(response: str):
    """
    Pretty prints the given response string using rich formatting.
    - If response is a markdown code block, renders it as Markdown.
    - If response is valid JSON, pretty prints it as formatted JSON.
    - Otherwise, prints the response as plain text.
    """
    console = Console()  # Initialize rich console for styled output

    # Check if the response starts with a Markdown code block indicator.
    if response.strip().startswith("```markdown"):
        # Extract content between the markdown code block markers.
        content = "\n".join(response.split("\n")[1:-1])
        console.print(Markdown(content.strip()))
        return

    # Attempt to parse the response as JSON.
    try:
        parsed_json = json.loads(response)
        console.print(JSON.from_data(parsed_json))
    except json.JSONDecodeError:
        # Fallback: Print as plain text if JSON parsing fails.
        console.print(response, markup=False)

class OpenAiAssistantManager:
    """
    Manages operations related to OpenAI assistants via the OpenAI API.
    Provides methods to create, list, retrieve, modify, and delete assistants.
    """
    def __init__(self, api_key: str):
        # Initialize OpenAI client using the provided API key.
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
        """
        Create a new assistant with the given configuration parameters.
        Parameters mirror API requirements (model, name, description, etc.).
        """
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
        """
        List existing assistants with optional pagination.
        - limit: Number of assistants to list.
        - order: Sort order ('desc' or 'asc').
        - after/before: Cursors for pagination.
        """
        return self.client.beta.assistants.list(
            limit=limit,
            order=order,
            after=after,
            before=before
        )

    def retrieve_assistant(self, assistant_id: str):
        """
        Retrieve details of a specific assistant by its ID.
        """
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
        """
        Modify an existing assistant with new parameters.
        Mirrors create_assistant parameters; updates provided fields.
        """
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
        """
        Delete an assistant identified by its ID.
        """
        return self.client.beta.assistants.delete(assistant_id)

class ClientConfig:
    """
    Configuration class for OpenAI assistants.
    Centralizes environment variables, debug settings, and polling intervals.
    """
    console = Console()  # Shared console instance for logging
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # Default to development environment
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")             # Required API key for OpenAI services
    GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")   # Optional: Google Gemini API key
    BENDER = os.getenv("BENDER")
    
    # Set debug mode and polling interval based on environment.
    DEBUG_MODE = ENVIRONMENT == "development"  # True if in development mode
    POLL_INTERVAL = 2 if ENVIRONMENT == "development" else 5  # Faster polling in development

    @classmethod
    def validate_config(cls):
        """
        Validate that all required environment variables are set.
        Raises an EnvironmentError if a required variable is missing.
        """
        console = Console()
        required_vars = {
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
            "GOOGLE_GEMINI_API_KEY": cls.GOOGLE_GEMINI_API_KEY,
            "BENDER": cls.BENDER,
            
        }
        # Check for missing environment variables.
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # If in debug mode, print configuration details.
        if cls.DEBUG_MODE:
            console.print("Running in DEBUG mode", style="bold green")
            console.print(f"Environment: {cls.ENVIRONMENT}", style="bold green")
            console.print(f"Poll interval: {cls.POLL_INTERVAL} seconds", style="bold green")

def initialize_chat():
    """
    Initialize a new chat thread using the OpenAI API.
    Returns the thread object on success or None on failure.
    """
    console = Console()
    try:
        # Instantiate a new OpenAI client using the configured API key.
        client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
        # Create a new chat thread via the beta API.
        thread = client.beta.threads.create()
        console.print("Chat thread initialized successfully", style="bold green")
        return thread
    except Exception as e:
        console.print("Error initializing chat thread:", style="bold red")
        console.print(str(e), style="bold red")
        return None

def upload_file(file_path):
    """
    Uploads a file to OpenAI for assistant use.
    - Opens the file in binary read mode.
    - Calls the API to upload with purpose "assistants".
    Returns the file ID on success; None on error.
    """
    console = Console()
    # Reinitialize client with API key in case of context loss.
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    try:
        console.print(f"Uploading file: {file_path}", style="bold green")
        with open(file_path, "rb") as file:
            file = client.files.create(
                file=file,
                purpose="assistants"
            )
        console.print(f"File uploaded successfully. ID: {file.id}", style="bold green")
        return file.id
    except Exception as e:
        console.print("Error uploading file:", style="bold red")
        console.print(str(e), style="bold red")
        return None

def send_user_message(thread_id, message, file_path=None):
    """
    Sends a message to a specified chat thread.
    - Optionally uploads a file if file_path is provided.
    - Constructs message payload with role "user".
    Returns the API response or None if an error occurs.
    """
    console = Console()
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    
    # Set up the message content.
    content = message
    file_ids = []
    
    # Check for file attachment and upload if present.
    if file_path:
        if not os.path.exists(file_path):
            pretty_print(f"File not found: {file_path}")
            return
            
        file_id = upload_file(client, file_path)
        if file_id:
            file_ids.append(file_id)
    
    # Prepare and send the message payload.
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
    """
    Starts a run for a given chat thread using a specific assistant.
    Calls the API to create a new run.
    """
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=ASSISTANT_ID)
    return run

def save_message_file(client, file_id, base_path="data/generated"):
    """
    Saves a file using its file ID.
    - Ensures the target directory exists.
    - Downloads file content via API and writes it to disk.
    Returns the file path if saved; otherwise None.
    """
    console = Console()
    try:
        # Ensure the output directory exists.
        os.makedirs(base_path, exist_ok=True)
        
        # Retrieve file content
        file_data = client.files.content(file_id)
        file_bytes = file_data.read()
        
        # Define the file path
        file_path = os.path.join(base_path, f"{file_id}.png")
        
        console.print(f"Downloading file: {file_id}", style="bold green")
        
        # Write the file content to disk
        with open(file_path, "wb") as file:
            file.write(file_bytes)
        console.print(f"File saved to: {file_path}", style="bold green")
        return file_path
    except Exception as e:
        console.print("Error saving file:", style="bold red")
        console.print(str(e), style="bold red")
    return None

def process_message_content(client, message):
    """
    Processes the content of a message.
    - Iterates over content blocks and distinguishes text from image files and URLs.
    - For text, prints the value; for image files, saves to disk; for image URLs, prints the URL.
    Returns a list of tuples (content_type, content).
    """
    formatted_content = []
    
    for content_block in message.content:
        if content_block.type == 'text':
            # Extract and print text content.
            text_content = content_block.text.value
            #pretty_print(text_content)
            formatted_content.append(("text", text_content))
        elif content_block.type == 'image_file':
            # Process image file content by saving and recording its path.
            file_id = content_block.image_file.file_id
            file_path = save_message_file(client, file_id)
            if file_path:
                formatted_content.append(("file", file_path))
        elif content_block.type == 'image_url':
            # Print the image URL
            image_url = content_block.image_url.url
            pretty_print(f"Image URL: {image_url}")
            formatted_content.append(("url", image_url))
    
    return formatted_content, text_content

def poll_run_status_and_submit_outputs(thread_id, run_id):
    """
    Continuously polls the status of a run until completion.
    - If status is 'completed', retrieves the most recent message from the assistant using message retrieval.
    - If 'requires_action', handles required tool output submission.
    - If 'failed', handles failure output.
    Utilizes a polling interval based on ClientConfig.
    """
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    console = Console()
    start_time = datetime.datetime.now()
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            elapsed_time = datetime.datetime.now() - start_time
            elapsed_seconds = int(elapsed_time.total_seconds())
            print(f"Elapsed Time: {elapsed_seconds} seconds", end='\r')
            sys.stdout.flush()
            
            if run.status == 'completed':
                pretty_print("Run completed successfully\n")
                # Retrieve the last message from the run
                message_list = client.beta.threads.messages.list(thread_id=thread_id)
                last_message = message_list.data[0]  # Assuming this is available
                #message = client.beta.threads.messages.retrieve(thread_id=thread_id, message_id=first_messgae_id)                # Process the message content
                
                formatted_content, text_content = process_message_content(client, last_message)                
                pretty_print(text_content)
                #print(formatted_content)
                #print(message) # debug print statement
                return last_message, text_content
            elif run.status == 'requires_action':
                handle_required_action(client, run, thread_id)
            elif run.status == 'failed':
                handle_run_failure(run)
                break
            else:
                time.sleep(ClientConfig.POLL_INTERVAL)
        except Exception as e:
            console.print("API Error occurred:", style="bold red")
            console.print(str(e), style="bold red")
            if hasattr(e, 'response'):
                console.print("Response details:", style="bold red")
                console.print(e.response, style="bold red")  # Output API error details unformatted
            break

def handle_required_action(client, run, thread_id):
    """
    Handles actions required by a run.
    - Specifically processes 'submit_tool_outputs' type actions.
    - Extracts tool call details, executes corresponding functions, and submits outputs.
    """
    console = Console()

    if run.required_action.type == 'submit_tool_outputs':
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        console.print("Tool Calls Received:", style="bold green")
        tool_outputs = []
        for tool_call in tool_calls:
            console.print("Raw Tool Call Details:", style="bold green")
            # Convert tool call details to a dictionary representation.
            tool_call_dict = tool_call.to_dict() if hasattr(tool_call, 'to_dict') else vars(tool_call)
            console.print(json.dumps(tool_call_dict, indent=4), style="bold green")
            
            console.print("Function Details:", style="bold green")
            console.print(f"Name: {tool_call.function.name}", style="bold green")
            
            console.print("Raw Arguments:", style="bold green")
            console.print(tool_call.function.arguments, style="bold green")
            
            console.print("Parsed Arguments:", style="bold green")
            # Parse JSON formatted function arguments.
            arguments = json.loads(tool_call.function.arguments)
            console.print(json.dumps(arguments, indent=6), style="bold green")
            
            console.print(f"Executing: {tool_call.function.name}", style="bold green")
            # Execute the function with provided arguments.
            function_output = execute_function(tool_call.function.name, arguments)
            
            tool_output = {
                "tool_call_id": tool_call.id,
                "output": json.dumps(function_output)
            }
            tool_outputs.append(tool_output)
            
            console.print("Function Output:", style="bold green")
            console.print(json.dumps(function_output, indent=6), style="bold green")
        
        # Submit the aggregated tool outputs back to the API.
        client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
        console.print("Tool outputs submitted successfully", style="bold green")

def handle_run_failure(run_status):
    """
    Handles failure of a run by printing detailed error information.
    - Outputs status, last error, failure time, file IDs, and metadata if available.
    """
    console = Console()
    console.print("Run failed. Details:", style="bold red")
    console.print(f"Status: {run_status.status}", style="bold red")
    console.print(f"Last error: {run_status.last_error}", style="bold red")
    if hasattr(run_status, 'failed_at'):
        console.print(f"Failed at: {run_status.failed_at}", style="bold red")
    if hasattr(run_status, 'file_ids'):
        console.print(f"File IDs: {run_status.file_ids}", style="bold red")
    if hasattr(run_status, 'metadata'):
        console.print(f"Metadata: {run_status.metadata}", style="bold red")

def process_run_completion(client, thread_id):
    """
    Processes the completion of a run by:
    - Retrieving all messages in the thread.
    - Printing raw and formatted message content.
    - Handling text and file content appropriately.
    """
    console = Console()
    message_response = client.beta.threads.messages.list(thread_id=thread_id)
    
    for message in message_response.data:
        role = message.role.upper()
        console.print(f"Message from {role}:", style="bold green")
        #console.print("Raw Message Content:", style="bold green")
        #console.print(json.dumps(message.content, indent=4, default=str), style="bold green")        
        # Process each content block in the message.
        formatted_content = process_message_content(client, message)
        
        console.print("Formatted Content:", style="bold green")
        for content_type, content in formatted_content:
            if content_type == "file":
                console.print(f"Generated file saved at: {content}", style="bold green")
            # elif content_type == "text":
            #     pretty_print(content)

def execute_function(function_name, arguments):
    """
    Executes a function based on its name and provided arguments.
    - Currently a placeholder that returns a dummy successful result.
    """
    pretty_print(f"Executing function: {function_name} with arguments: {arguments}")
    return {"result": "Function executed successfully"}

def read_test_prompt():
    """
    Reads and returns the test prompt from 'tests/test_prompt' file.
    Returns the prompt text or None if an error occurs.
    """
    try:
        with open('tests/test_prompt', 'r') as file:
            return file.read().strip()
    except Exception as e:
        pretty_print("Error reading test prompt:")
        pretty_print(str(e))
        return None

def process_outline_agent_run(thread_id, run_id):
    """
    Processes a run for the outline agent.
    - Polls run status until 'completed' or 'failed'.
    - On completion, retrieves and returns the last assistant message.
    """
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
                pretty_print(e.response)  # Output API error details unformatted
            break

def get_last_assistant_message(client, thread_id):
    """
    Retrieves the last message from the assistant in the specified thread.
    - Iterates through messages and returns the assistant's text content.
    """
    message_response = client.beta.threads.messages.list(thread_id=thread_id)
    last_message = ""
    
    for message in message_response.data:
        if message.role == "assistant":
            last_message = message.content[0].text.value if message.content else ""
    
    return last_message

def process_formulate_question_agent_run(thread_id, run_id):
    """
    Processes a run for the formulate question agent.
    - Polls until the run is 'completed' or 'failed'.
    - On completion, returns the last assistant message.
    """
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
                pretty_print(e.response)  # Output API error details unformatted
            break

def run_vector_store_search_agent(assistant_id, vector_store_id, message_content):
    """
    Runs the vector store search agent.
    - Constructs a new thread with the user's message.
    - Specifies tool resources to limit search to the given vector store.
    Returns the run object on success.
    """
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
    """
    Processes multiple questions using the search agent.
    - Extracts questions from the provided JSON structure.
    - For each question, creates and polls a new run.
    - Aggregates question and answer pairs into a response dictionary.
    """
    console = Console()
    client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)
    responses = {"questions_and_answers": []}

    try:
        # Retrieve list of questions from the JSON input.
        questions = questions_json.get("questions", [])
        for question in questions:
            console.print(f"Processing question: {question}", style="bold blue")

            if not question.strip():
                console.print("Skipping empty question content", style="bold blue")
                continue

            # Create and run a new thread for each question.
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

            # Poll run status until completion.
            start_time = datetime.datetime.now()
            while True:
                run_status = client.beta.threads.runs.retrieve(thread_id=run.thread_id, run_id=run.id)
                elapsed_time = datetime.datetime.now() - start_time
                elapsed_seconds = int(elapsed_time.total_seconds())
                print(f"Elapsed Time: {elapsed_seconds} seconds", end='\r')
                sys.stdout.flush()
                
                if run_status.status == 'completed':
                    console.print("Run completed successfully\n", style="bold green")
                    answer = get_last_assistant_message(client, run.thread_id)
                    responses["questions_and_answers"].append({
                        "question": question,
                        "answer": answer
                    })
                    break
                elif run_status.status == 'failed':
                    console.print("Run failed", style="bold red")
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
    """
    Processes a run for the reviewer agent.
    - Continuously polls until run status is 'completed' or 'failed'.
    - On success, returns the last assistant message.
    """
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
                pretty_print(e.response)  # Output API error details unformatted
            break

def process_writer_agent(gemini_model, combined_message):
    """
    Processes the writer agent.
    - Constructs a new thread with the user's message.
    - returns the last assistant message.
    """
    console = Console()
    try:
        writer_thread = gemini_model.start_chat(history=[])
        if not writer_thread:
            raise RuntimeError("Failed to start chat for writer agent.")
        writer_chat = writer_thread.send_message(combined_message)
        if not writer_chat or not writer_chat.text:
            raise RuntimeError("Writer agent returned empty response.")
        return writer_chat
    except Exception as e:
        raise RuntimeError("Error executing writer agent.") from e
