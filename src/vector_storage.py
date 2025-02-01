import openai
import json
import os
import time
import copy  # for copying our template dict
import logging  # Ensure logging is imported
from openai import OpenAI
from .openai_assistant import ClientConfig
from rich.console import Console
from .data_handler import main as data_handler_main




console = Console()

def upload_file_to_vector_store(
    vector_store_id,
    file_paths,
    data_path,
    api_key_env= ClientConfig.OPENAI_API_KEY,
    meta_template_path=None
):
    """
    Uploads files to the specified vector store using the upload_and_poll method
    and updates data.json. If meta_template_path is provided, it will be used as
    the base metadata template for each new file instead of hard-coded defaults.
    """
    try:
        client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)

        # 1. Load user-defined metadata template (if any).
        metadata_template = {}
        if meta_template_path and os.path.isfile(meta_template_path):
            with open(meta_template_path, 'r') as fp:
                metadata_template = json.load(fp)

        # 2. Load existing data.json
        with open(data_path, 'r+') as data_file:
            data = json.load(data_file)
            unstructured_files = data.get("unstructured_vector_files", [])
            max_file_id = max((file_obj.get("file_id", 0) for file_obj in unstructured_files), default=0)

            file_metadata = []
            file_streams = [open(path, "rb") for path in file_paths]
            client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id,
                files=file_streams
            )
            for stream in file_streams:
                stream.close()

            # 3. Get the newly uploaded files & build the final metadata from the template
            files_in_store = list_files_in_vector_store(vector_store_id, api_key_env=api_key_env)
            latest_files = sorted(files_in_store, key=lambda x: x.created_at, reverse=True)[:len(file_paths)]

            for path, vector_store_file in zip(file_paths, latest_files):
                file_name = os.path.basename(path)
                existing_file = next((f for f in unstructured_files if f["file_name"] == file_name), None)

                # Copy the metadata template so we don't mutate the original dictionary
                single_file_metadata = copy.deepcopy(metadata_template)

                # Fill in the fields that need to be unique per file
                single_file_metadata["file_id"] = (
                    existing_file["file_id"] if existing_file else max_file_id + 1
                )
                single_file_metadata["file_name"] = file_name
                single_file_metadata["file_location"] = path
                single_file_metadata["vector_store_file_id"] = vector_store_file.id
                single_file_metadata["vector_store_id"] = vector_store_id

                # If an existing record is found, update it; otherwise append
                if existing_file:
                    unstructured_files[unstructured_files.index(existing_file)] = single_file_metadata
                else:
                    unstructured_files.append(single_file_metadata)
                    max_file_id += 1

            # 4. Commit changes back to data.json
            data["unstructured_vector_files"] = unstructured_files
            data_file.seek(0)
            json.dump(data, data_file, indent=4)
            data_file.truncate()

            # 5. Optionally combine schema and data if needed
            combine_schema_and_data('schema.json', data_path, 'metadata.json')

        return file_metadata
    except Exception as e:
        print(f"Error uploading files to vector store: {e}")
        return None
    
def list_files_in_vector_store(vector_store_id, ):
    """Lists all files in the specified vector store."""
    try:
        client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)

        files = client.beta.vector_stores.files.list(vector_store_id=vector_store_id)
        for file in files.data:
            print(f"File ID: {file.id}, Created At: {file.created_at}, Vector Store ID: {file.vector_store_id}")
        return files.data
    except Exception as e:
        print(f"Error listing files in vector store: {e}")
        return None

def update_data_json(data_path, file_metadata):
    """Appends new file metadata to the unstructured_vector_files section in data.json."""
    try:
        with open(data_path, 'r+') as data_file:
            data = json.load(data_file)
            if "unstructured_vector_files" not in data:
                data["unstructured_vector_files"] = []
            data["unstructured_vector_files"].extend(file_metadata)
            data_file.seek(0)
            json.dump(data, data_file, indent=4)
            data_file.truncate()
        print(f"data.json updated with new file metadata.")
    except Exception as e:
        print(f"Error updating data.json: {e}")

def delete_file_from_vector_store(vector_store_id, file_id, ):
    """Deletes a file from the vector store by its ID."""
    try:
        client = OpenAI(api_key=ClientConfig.OPENAI_API_KEY)

        client.beta.vector_stores.files.delete(
            vector_store_id=vector_store_id,
            file_id=file_id
        )
        print(f"File {file_id} deleted from vector store {vector_store_id}.")
    except Exception as e:
        print(f"Error deleting file from vector store: {e}")

def get_table_schema(schema):
    """Prints and returns the schema of the vector storage."""
    try:
        print(json.dumps(schema, indent=4))
        return schema
    except Exception as e:
        print(f"Error retrieving schema: {e}")

def replace_file_in_vector_store(vector_store_id, file_id, new_file_path, api_key_env=ClientConfig.OPENAI_API_KEY):
    """Replaces an existing file in the vector store with a new file."""
    try:
        # Delete the existing file
        delete_file_from_vector_store(vector_store_id, file_id, api_key_env=api_key_env)
        print(f"Deleted file {file_id} from vector store {vector_store_id}.")

        # Upload the new file
        upload_file_to_vector_store(vector_store_id, [new_file_path], api_key_env=api_key_env)
        print(f"Uploaded new file from {new_file_path} to vector store {vector_store_id}.")
    except Exception as e:
        print(f"Error replacing file in vector store: {e}")

def create_vector_store_schema(schema_path):
    """Loads and initializes the schema for the vector store."""
    try:
        # Added check for empty file
        if os.path.getsize(schema_path) == 0:
            print("Empty schema file detected, returning empty schema.")
            return {}

        with open(schema_path, 'r') as file:
            schema = json.load(file)
        print("Schema loaded successfully.")
        return schema
    except Exception as e:
        print(f"Error loading schema: {e}")
        return None

def combine_schema_and_data(schema_path, data_path, output_path):
    """Combines schema and data JSON files into one."""
    try:
        with open(schema_path, 'r') as schema_file:
            schema = json.load(schema_file)
        with open(data_path, 'r') as data_file:
            data = json.load(data_file)

        combined = {"schema": schema, "data": data}

        with open(output_path, 'w') as output_file:
            json.dump(combined, output_file, indent=4)

        print(f"Combined schema and data saved to {output_path}")
    except Exception as e:
        print(f"Error combining schema and data: {e}")

def separate_schema_and_data(combined_path, schema_output_path, data_output_path):
    """Separates combined schema and data JSON into two files."""
    try:
        with open(combined_path, 'r') as combined_file:
            combined = json.load(combined_file)

        schema = combined.get("schema")
        data = combined.get("data")

        if schema:
            with open(schema_output_path, 'w') as schema_file:
                json.dump(schema, schema_file, indent=4)

        if data:
            with open(data_output_path, 'w') as data_file:
                json.dump(data, data_file, indent=4)

        print(f"Schema saved to {schema_output_path}")
        print(f"Data saved to {data_output_path}")
    except Exception as e:
        print(f"Error separating schema and data: {e}")

def get_unstructured_file_paths(directory):
    """Get a list of all file paths in the specified directory."""
    return [os.path.join(directory, file) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]

def clear_and_update_vector_store(
    vector_store_id,
    data_path,
    api_key_env=ClientConfig.OPENAI_API_KEY,
    meta_template_path=None
):
    """
    Clears the vector store and uploads all available local files, updating data.json with new file IDs.
    If meta_template_path is provided, it will be used as the base metadata template 
    for unstructured_vector_files instead of hard-coded defaults.
    """
    try:
        # 1. Load the API key
        client = openai.Client(api_key=ClientConfig.OPENAI_API_KEY)

        # 2. Optionally load metadata template
        metadata_template = {}
        if meta_template_path and os.path.isfile(meta_template_path):
            with open(meta_template_path, 'r') as template_file:
                metadata_template = json.load(template_file)

        # 3. Load data.json
        with open(data_path, 'r+') as data_file:
            data = json.load(data_file)
            unstructured_files = data.get("unstructured_vector_files", [])

            # 4. Clear existing files from the vector store
            files = list_files_in_vector_store(vector_store_id, api_key_env=api_key_env)
            for file in files:
                client.beta.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file.id)
                print(f"Deleted file {file.id} from vector store {vector_store_id}.")

            # 5. Upload metadata.json itself first
            with open("data/metadata.json", "rb") as meta_stream:
                meta_file = client.beta.vector_stores.files.upload(
                    vector_store_id=vector_store_id,
                    file=meta_stream
                )
                existing_meta = next(
                    (f for f in unstructured_files if f["file_name"] == "data/metadata.json"),
                    None
                )
                if existing_meta:
                    existing_meta["vector_store_file_id"] = meta_file.id
                else:
                    single_meta_entry = copy.deepcopy(metadata_template) if metadata_template else {}
                    # Fill necessary fields for metadata.json
                    single_meta_entry["file_id"] = single_meta_entry.get("file_id", 1)
                    single_meta_entry["file_name"] = "metadata.json"
                    single_meta_entry["vector_store_file_id"] = meta_file.id
                    single_meta_entry["vector_store_id"] = vector_store_id
                    single_meta_entry["metadata"] = single_meta_entry.get("metadata", "Metadata file for vector store")
                    unstructured_files.insert(0, single_meta_entry)

            # 6. Upload the rest of the files
            file_paths = get_unstructured_file_paths("semantic_model/unstructured_vector_files")
            file_streams = [open(path, "rb") for path in file_paths]
            client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id,
                files=file_streams
            )
            for stream in file_streams:
                stream.close()

            # Give the vector store time to index
            time.sleep(5)

            # 7. Retrieve newly uploaded files and fill metadata
            files_in_store = list_files_in_vector_store(vector_store_id, api_key_env=api_key_env)
            latest_files = sorted(files_in_store, key=lambda x: x.created_at, reverse=True)[:len(file_paths)]
            next_file_id = 2

            for path, vector_store_file in zip(file_paths, latest_files):
                file_name = os.path.basename(path)
                existing_file = next((f for f in unstructured_files if f["file_name"] == file_name), None)

                if existing_file:
                    existing_file["vector_store_file_id"] = vector_store_file.id
                else:
                    single_file_metadata = copy.deepcopy(metadata_template) if metadata_template else {}
                    # Fill the fields needed
                    single_file_metadata["file_id"] = single_file_metadata.get("file_id", next_file_id)
                    single_file_metadata["file_name"] = file_name
                    single_file_metadata["file_location"] = path
                    single_file_metadata["vector_store_file_id"] = vector_store_file.id
                    single_file_metadata["vector_store_id"] = vector_store_id
                    unstructured_files.append(single_file_metadata)
                    next_file_id += 1

            # 8. Save updates back to data.json
            data["Unstructured_Vector_Files"] = unstructured_files
            data_file.seek(0)
            json.dump(data, data_file, indent=4)
            data_file.truncate()

            # 9. Combine schema/data if needed
            combine_schema_and_data('schema.json', data_path, 'metadata.json')

    except Exception as e:
        print(f"Error clearing and updating vector store: {e}")

def update_metadata_in_vector_store(vector_store_id, api_key_env=ClientConfig.OPENAI_API_KEY):
    """Update the metadata.json file in the vector store."""
    # Run the data handler to update metadata.json
    data_handler_main(
        directory="semantic_model/structured_vector_files",
        data_output_path="data/data.json",
        schema_output_path="data/schema.json",
        json_file_path=None,
        excel_file_path=None
    )

    # Upload the updated metadata.json
    upload_file_to_vector_store(vector_store_id=vector_store_id, file_id="data/metadata.json", api_key_env=api_key_env)
    logging.info("Updated metadata.json in the vector store.") 

def create_file_batch(vector_store_id, file_ids, chunking_strategy=None):
    """
    Create a vector store file batch with a list of already-uploaded file IDs.
    Returns the file batch object.
    """
    try:
        
        client = openai.Client(api_key=ClientConfig.OPENAI_API_KEY)
        
        payload = {"file_ids": file_ids}
        if chunking_strategy:
            payload["chunking_strategy"] = chunking_strategy
        
        batch = client.beta.vector_stores.file_batches.create(
            vector_store_id=vector_store_id,
            **payload
        )
        logging.info(f"Created file batch with ID {batch.id} for vector store {vector_store_id}.")
        return batch
    except Exception as e:
        logging.error(f"Error creating file batch: {e}")
        return None

def retrieve_file_batch(vector_store_id, batch_id):
    """
    Retrieve a vector store file batch by its ID.
    """
    try:
        client = openai.Client(api_key=ClientConfig.OPENAI_API_KEY)
        
        batch = client.beta.vector_stores.file_batches.retrieve(
            vector_store_id=vector_store_id,
            batch_id=batch_id
        )
        logging.info(f"Retrieved file batch {batch_id}: status -> {batch.status}")
        return batch
    except Exception as e:
        logging.error(f"Error retrieving file batch: {e}")
        return None

def cancel_file_batch(vector_store_id, batch_id):
    """
    Cancel an in-progress file batch, if possible.
    """
    try:
        client = openai.Client(api_key=ClientConfig.OPENAI_API_KEY)
        
        cancelled_batch = client.beta.vector_stores.file_batches.cancel(
            vector_store_id=vector_store_id,
            file_batch_id=batch_id
        )
        logging.info(f"Cancelled file batch {batch_id}. Status is now {cancelled_batch.status}.")
        return cancelled_batch
    except Exception as e:
        logging.error(f"Error cancelling file batch: {e}")
        return None

def list_batch_files(vector_store_id, batch_id, limit=20, order='desc', after=None, before=None, filter=None, api_key_env=ClientConfig.OPENAI_API_KEY):
    """
    List files in a specific file batch.
    """
    try:
        API_KEY = api_key_env
        client = openai.Client(api_key=API_KEY)
        
        files_list = client.beta.vector_stores.file_batches.list_files(
            vector_store_id=vector_store_id,
            batch_id=batch_id,
            limit=limit,
            order=order,
            after=after,
            before=before,
            filter=filter
        )
        logging.info(f"Listed files in batch {batch_id}. Found {len(files_list.data)} files.")
        return files_list
    except Exception as e:
        logging.error(f"Error listing files in batch {batch_id}: {e}")
        return None

def upload_files_to_vector_store_only(vector_store_id, file_paths, api_key_env=ClientConfig.OPENAI_API_KEY):

    try:
        # Load the API key from environment variables
        client = openai.Client(api_key=api_key_env)

        # Open file streams for each file path
        file_streams = [open(path, "rb") for path in file_paths]

        # Upload files to the vector store
        client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id,
            files=file_streams
        )

        # Close all file streams
        for stream in file_streams:
            stream.close()

        console.print(f"Files uploaded successfully to vector store {vector_store_id}.", style="bold green")
    except Exception as e:
        console.print(f"Error uploading files to vector store: {e}", style="bold red")

def upload_file_to_openai(file_path, purpose="assistants"):
    """Upload a file to OpenAI and return the file ID."""
    try:        
        client = openai.Client(api_key=ClientConfig.OPENAI_API_KEY)

        with open(file_path, "rb") as file:
            response = client.files.create(
                file=file,
                purpose=purpose
            )
        # Access the file ID correctly
        file_id = response.id
        print(f"File uploaded successfully. ID: {file_id}")
        return file_id
    except Exception as e:
        print(f"Error uploading file to OpenAI: {e}")
        return None

def create_vector_store(name=None, file_ids=None, expires_after=None, chunking_strategy=None, metadata=None):
    """Create a new vector store."""
    try:
        client = openai.Client(api_key=ClientConfig.OPENAI_API_KEY)
        response = client.beta.vector_stores.create(
            name=name,
            file_ids=file_ids,
            expires_after=expires_after,
            chunking_strategy=chunking_strategy,
            metadata=metadata
        )
        # Print and return the vector store details
        console.print(f"Vector store created with ID: {response.id}", style="bold green")
        return response
    except Exception as e:
        console.print(f"Error creating vector store: {e}", style="bold red")
        return None

def upload_file_to_vector_store(vector_store_id, file_id, chunking_strategy=None):
    """Attach a file to an existing vector store."""
    client = openai.Client(api_key=ClientConfig.OPENAI_API_KEY)
    try:
        response = client.beta.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_id,
            chunking_strategy=chunking_strategy
        )
        print(f"File {file_id} uploaded to vector store {vector_store_id}.")
        return response
    except Exception as e:
        print(f"Error uploading file to vector store: {e}")
        return None

def list_vector_store_files(vector_store_id, limit=20, order='desc', after=None, before=None, filter=None):
    """List files in a vector store."""
    client = openai.Client(api_key=ClientConfig.OPENAI_API_KEY)
    try:
        response = client.beta.vector_stores.files.list(
            vector_store_id=vector_store_id,
            limit=limit,
            order=order,
            after=after,
            before=before,
            filter=filter
        )
        return response['data']
    except Exception as e:
        print(f"Error listing files in vector store: {e}")
        return None

def retrieve_vector_store_file(vector_store_id, file_id):
    """Retrieve a specific file from a vector store."""
    client = openai.Client(api_key=ClientConfig.OPENAI_API_KEY)
    try:
        response = client.beta.vector_stores.files.retrieve(
            vector_store_id=vector_store_id,
            file_id=file_id
        )
        return response
    except Exception as e:
        print(f"Error retrieving file from vector store: {e}")
        return None

def get_all_file_paths_in_directory(directory_path):
    """
    Retrieve all file paths from the specified directory.
    
    Args:
        directory_path: Path to the directory.
    
    Returns:
        List of file paths in the directory.
    """
    return [os.path.join(directory_path, file_name) for file_name in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, file_name))]