#!/usr/bin/env python3

import argparse
import json
import sys
from typing import Optional, Dict, List, BinaryIO
from datetime import datetime
import os
from openai import OpenAI
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

class OpenAIStorageManager:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("API key not found in environment variables")
            raise ValueError("API key not found. Please set AI_ANALYST_API_KEY environment variable.")
        logger.info("Initializing OpenAI client")
        self.client = OpenAI(api_key=api_key)
        
    def list_vector_stores(self, limit: int = 20, order: str = "desc") -> Dict:
        """List all vector stores in the account."""
        try:
            logger.info(f"Listing vector stores (limit={limit}, order={order})")
            response = self.client.beta.vector_stores.list(
                limit=limit,
                order=order
            )
            # Convert response to dictionary for easier handling
            stores_data = {
                "data": [
                    {
                        "id": store.id,
                        "name": store.name,
                        "created_at": store.created_at,
                        "bytes": getattr(store, 'bytes', 0),
                        "file_counts": {
                            "total": store.file_counts.total if hasattr(store, 'file_counts') else 0,
                            "completed": store.file_counts.completed if hasattr(store, 'file_counts') else 0,
                            "in_progress": store.file_counts.in_progress if hasattr(store, 'file_counts') else 0,
                            "failed": store.file_counts.failed if hasattr(store, 'file_counts') else 0,
                            "cancelled": store.file_counts.cancelled if hasattr(store, 'file_counts') else 0
                        }
                    }
                    for store in response.data
                ]
            }
            logger.info(f"Successfully retrieved {len(stores_data['data'])} vector stores")
            logger.debug(f"Vector stores response: {json.dumps(stores_data, default=str)}")
            return stores_data
        except Exception as e:
            logger.error(f"Error listing vector stores: {str(e)}")
            return {"data": []}

    def create_vector_store(self, name: str, file_ids: Optional[List[str]] = None) -> Dict:
        """Create a new vector store."""
        try:
            logger.info(f"Creating vector store '{name}' with files: {file_ids}")
            vector_store = self.client.beta.vector_stores.create(
                name=name,
                file_ids=file_ids if file_ids else None
            )
            logger.info(f"Successfully created vector store with ID: {vector_store.get('id')}")
            return vector_store
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            return {}

    def get_vector_store(self, vector_store_id: str) -> Dict:
        """Retrieve details of a specific vector store."""
        try:
            vector_store = self.client.beta.vector_stores.retrieve(
                vector_store_id=vector_store_id
            )
            return vector_store
        except Exception as e:
            print(f"Error retrieving vector store: {str(e)}")
            return {}

    def delete_vector_store(self, vector_store_id: str) -> Dict:
        """Delete a vector store."""
        try:
            result = self.client.beta.vector_stores.delete(
                vector_store_id=vector_store_id
            )
            return result
        except Exception as e:
            print(f"Error deleting vector store: {str(e)}")
            return {}

    def list_vector_store_files(self, vector_store_id: str, limit: int = 20) -> Dict:
        """List all files in a vector store."""
        try:
            files = self.client.beta.vector_stores.files.list(
                vector_store_id=vector_store_id,
                limit=limit
            )
            return files
        except Exception as e:
            print(f"Error listing vector store files: {str(e)}")
            return {}

    def upload_file(self, file_path: str, purpose: str) -> Dict:
        """Upload a file to OpenAI."""
        try:
            with open(file_path, "rb") as file:
                response = self.client.files.create(
                    file=file,
                    purpose=purpose
                )
            return response
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            return {}

    def list_files(self, purpose: Optional[str] = None, limit: int = 100, order: str = "desc") -> Dict:
        """List all files or files with specific purpose."""
        try:
            logger.info(f"Listing files (purpose={purpose}, limit={limit}, order={order})")
            response = self.client.files.list(
                purpose=purpose,
                limit=limit,
                order=order
            )
            # Convert response to dictionary for easier handling
            files_data = {
                "data": [
                    {
                        "id": file.id,
                        "filename": file.filename,
                        "bytes": file.bytes,
                        "created_at": file.created_at,
                        "purpose": file.purpose,
                        "status": getattr(file, 'status', None)
                    }
                    for file in response.data
                ]
            }
            logger.info(f"Successfully retrieved {len(files_data['data'])} files")
            logger.debug(f"Files response: {json.dumps(files_data, default=str)}")
            return files_data
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return {"data": []}

    def get_file(self, file_id: str) -> Dict:
        """Get details of a specific file."""
        try:
            logger.info(f"Retrieving file details for ID: {file_id}")
            file = self.client.files.retrieve(file_id)
            logger.info(f"Successfully retrieved file: {file.get('filename', file_id)}")
            return file
        except Exception as e:
            logger.error(f"Error retrieving file: {str(e)}")
            return {}

    def delete_file(self, file_id: str) -> Dict:
        """Delete a file."""
        try:
            result = self.client.files.delete(file_id)
            return result
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return {}

    def get_file_content(self, file_id: str, output_path: Optional[str] = None) -> Optional[bytes]:
        """Get the content of a file. Optionally save to a file."""
        try:
            content = self.client.files.content(file_id)
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(content)
                print(f"File content saved to: {output_path}")
            
            return content
        except Exception as e:
            print(f"Error retrieving file content: {str(e)}")
            return None

    def delete_files_by_pattern(self, pattern: str, dry_run: bool = True) -> List[Dict]:
        """Delete files matching a pattern in their filename.
        
        Args:
            pattern: String to match in filename (case-insensitive)
            dry_run: If True, only show what would be deleted without actually deleting
        
        Returns:
            List of deleted file information
        """
        try:
            logger.info(f"Finding files matching pattern: {pattern}")
            files = self.list_files(limit=100)  # Get all files
            
            if not files or "data" not in files:
                return []

            pattern = pattern.lower()
            matching_files = [
                file for file in files["data"]
                if pattern in file["filename"].lower()
            ]
            
            logger.info(f"Found {len(matching_files)} files matching pattern")
            
            if dry_run:
                return matching_files
            
            deleted_files = []
            for file in matching_files:
                try:
                    result = self.delete_file(file["id"])
                    if result and result.get("deleted"):
                        deleted_files.append(file)
                        logger.info(f"Successfully deleted file: {file['filename']} ({file['id']})")
                    else:
                        logger.warning(f"Failed to delete file: {file['filename']} ({file['id']})")
                except Exception as e:
                    logger.error(f"Error deleting file {file['id']}: {str(e)}")
            
            return deleted_files
        except Exception as e:
            logger.error(f"Error in delete_files_by_pattern: {str(e)}")
            return []

    def delete_vector_stores_by_pattern(self, pattern: str, dry_run: bool = True) -> List[Dict]:
        """Delete vector stores matching a pattern in their name.
        
        Args:
            pattern: String to match in vector store name (case-insensitive)
            dry_run: If True, only show what would be deleted without actually deleting
        
        Returns:
            List of deleted vector store information
        """
        try:
            logger.info(f"Finding vector stores matching pattern: {pattern}")
            stores = self.list_vector_stores(limit=100)  # Get all vector stores
            
            if not stores or "data" not in stores:
                return []

            pattern = pattern.lower()
            matching_stores = [
                store for store in stores["data"]
                if pattern in store["name"].lower()
            ]
            
            logger.info(f"Found {len(matching_stores)} vector stores matching pattern")
            
            if dry_run:
                return matching_stores
            
            deleted_stores = []
            for store in matching_stores:
                try:
                    result = self.delete_vector_store(store["id"])
                    if result and result.get("deleted"):
                        deleted_stores.append(store)
                        logger.info(f"Successfully deleted vector store: {store['name']} ({store['id']})")
                    else:
                        logger.warning(f"Failed to delete vector store: {store['name']} ({store['id']})")
                except Exception as e:
                    logger.error(f"Error deleting vector store {store['id']}: {str(e)}")
            
            return deleted_stores
        except Exception as e:
            logger.error(f"Error in delete_vector_stores_by_pattern: {str(e)}")
            return []

def format_timestamp(timestamp: int) -> str:
    """Convert Unix timestamp to human-readable format."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def display_vector_store(store: Dict) -> None:
    """Display vector store information in a formatted way."""
    if not store:
        return
    
    print("\nVector Store Details:")
    print(f"ID: {store.get('id', 'N/A')}")
    print(f"Name: {store.get('name', 'N/A')}")
    if store.get('created_at'):
        print(f"Created: {format_timestamp(store.get('created_at'))}")
    print(f"Size: {store.get('bytes', 0):,} bytes")
    
    file_counts = store.get('file_counts', {})
    if file_counts:
        print("\nFile Counts:")
        print(f"Total: {file_counts.get('total', 0)}")
        print(f"Completed: {file_counts.get('completed', 0)}")
        print(f"In Progress: {file_counts.get('in_progress', 0)}")
        print(f"Failed: {file_counts.get('failed', 0)}")
        print(f"Cancelled: {file_counts.get('cancelled', 0)}")

def display_file(file: Dict) -> None:
    """Display file information in a formatted way."""
    if not file:
        return
    
    print("\nFile Details:")
    print(f"ID: {file.get('id', 'N/A')}")
    print(f"Filename: {file.get('filename', 'N/A')}")
    print(f"Purpose: {file.get('purpose', 'N/A')}")
    if file.get('created_at'):
        print(f"Created: {format_timestamp(file.get('created_at'))}")
    print(f"Size: {file.get('bytes', 0):,} bytes")
    if file.get('status'):  # Deprecated but still show if present
        print(f"Status: {file.get('status')}")

def print_interactive_help():
    """Print help information for interactive mode."""
    print("\nAvailable Commands:")
    print("  --help                     Show this help message")
    print("  --exit                     Exit the program")
    print("\nFile Commands:")
    print("  --list                     List all files")
    print("  --list-purpose <purpose>   List files by purpose (assistants/vision/fine-tune/batch)")
    print("  --upload <file> <purpose>  Upload a file")
    print("  --delete <file_id>         Delete a file")
    print("  --delete-many <id1,id2>    Delete multiple files (comma-separated)")
    print("  --get <file_id>            Get file details")
    print("  --download <id> [path]     Download file content (optionally to path)")
    print("  --delete-where <pattern>   Find and delete files containing pattern in filename")
    print("  --delete-where-dry <pat>   Show files that would be deleted by pattern")
    print("\nVector Store Commands:")
    print("  --vs-list                  List all vector stores")
    print("  --vs-create <name>         Create a vector store")
    print("  --vs-delete <id>           Delete a vector store")
    print("  --vs-get <id>              Get vector store details")
    print("  --vs-files <id>            List files in vector store")
    print("  --vs-delete-where <pattern>   Find and delete vector stores containing pattern in name")
    print("  --vs-delete-where-dry <pat>   Show vector stores that would be deleted by pattern")

def parse_interactive_command(cmd: str, manager: OpenAIStorageManager):
    """Parse and execute interactive commands."""
    parts = cmd.split()
    if not parts:
        return

    command = parts[0].lower()
    logger.info(f"Processing command: {command}")

    try:
        if command == "--help":
            print_interactive_help()

        elif command == "--list":
            logger.info("Executing list files command")
            files = manager.list_files()
            if files and "data" in files and files["data"]:
                print(f"\nFound {len(files['data'])} files:")
                for file in files["data"]:
                    display_file(file)
                    print("-" * 50)
            else:
                logger.warning("No files found")
                print("No files found in your account")

        elif command == "--list-purpose" and len(parts) > 1:
            purpose = parts[1]
            if purpose not in ["assistants", "vision", "fine-tune", "batch"]:
                print("Invalid purpose. Must be one of: assistants, vision, fine-tune, batch")
                return
            files = manager.list_files(purpose=purpose)
            if files and "data" in files:
                print(f"\nFound {len(files['data'])} {purpose} files:")
                for file in files["data"]:
                    display_file(file)
                    print("-" * 50)

        elif command == "--delete" and len(parts) > 1:
            file_id = parts[1]
            result = manager.delete_file(file_id)
            if result and result.get("deleted"):
                print(f"\nSuccessfully deleted file: {file_id}")

        elif command == "--delete-many" and len(parts) > 1:
            file_ids = parts[1].split(",")
            for file_id in file_ids:
                result = manager.delete_file(file_id.strip())
                if result and result.get("deleted"):
                    print(f"Successfully deleted file: {file_id}")
                else:
                    print(f"Failed to delete file: {file_id}")

        elif command == "--upload" and len(parts) > 2:
            file_path = parts[1]
            purpose = parts[2]
            if purpose not in ["assistants", "vision", "fine-tune", "batch"]:
                print("Invalid purpose. Must be one of: assistants, vision, fine-tune, batch")
                return
            file = manager.upload_file(file_path, purpose)
            if file:
                print("\nUploaded file:")
                display_file(file)

        elif command == "--get" and len(parts) > 1:
            file_id = parts[1]
            file = manager.get_file(file_id)
            if file:
                display_file(file)

        elif command == "--download" and len(parts) > 1:
            file_id = parts[1]
            output_path = parts[2] if len(parts) > 2 else None
            content = manager.get_file_content(file_id, output_path)
            if content and not output_path:
                print("\nFile content:")
                print(content.decode('utf-8'))

        elif command == "--vs-list":
            logger.info("Executing list vector stores command")
            stores = manager.list_vector_stores()
            if stores and "data" in stores and stores["data"]:
                print(f"\nFound {len(stores['data'])} vector stores:")
                for store in stores["data"]:
                    display_vector_store(store)
                    print("-" * 50)
            else:
                logger.warning("No vector stores found")
                print("No vector stores found in your account")

        elif command == "--vs-create" and len(parts) > 1:
            name = parts[1]
            store = manager.create_vector_store(name)
            if store:
                print("\nCreated new vector store:")
                display_vector_store(store)

        elif command == "--vs-delete" and len(parts) > 1:
            store_id = parts[1]
            result = manager.delete_vector_store(store_id)
            if result and result.get("deleted"):
                print(f"\nSuccessfully deleted vector store: {store_id}")

        elif command == "--vs-get" and len(parts) > 1:
            store_id = parts[1]
            store = manager.get_vector_store(store_id)
            if store:
                display_vector_store(store)

        elif command == "--vs-files" and len(parts) > 1:
            store_id = parts[1]
            files = manager.list_vector_store_files(store_id)
            if files and "data" in files:
                print(f"\nFound {len(files['data'])} files in vector store {store_id}:")
                for file in files["data"]:
                    print(f"\nFile ID: {file.get('id')}")
                    print(f"Created: {format_timestamp(file.get('created_at'))}")
                    print(f"Status: {file.get('status')}")
                    if file.get('usage_bytes'):
                        print(f"Size: {file.get('usage_bytes')} bytes")
                    print("-" * 30)

        elif command == "--delete-where" and len(parts) > 1:
            pattern = parts[1]
            print(f"\nWARNING: This will delete all files containing '{pattern}' in their filename.")
            confirmation = input("Are you sure you want to proceed? (yes/no): ").lower()
            if confirmation == "yes":
                deleted_files = manager.delete_files_by_pattern(pattern, dry_run=False)
                if deleted_files:
                    print(f"\nSuccessfully deleted {len(deleted_files)} files:")
                    for file in deleted_files:
                        print(f"- {file['filename']} ({file['id']})")
                else:
                    print("No files found matching the pattern.")
            else:
                print("Operation cancelled.")

        elif command == "--delete-where-dry" and len(parts) > 1:
            pattern = parts[1]
            matching_files = manager.delete_files_by_pattern(pattern, dry_run=True)
            if matching_files:
                print(f"\nFound {len(matching_files)} files that would be deleted:")
                for file in matching_files:
                    print(f"\nFile Details:")
                    print(f"Filename: {file['filename']}")
                    print(f"ID: {file['id']}")
                    print(f"Purpose: {file['purpose']}")
                    if file.get('created_at'):
                        print(f"Created: {format_timestamp(file['created_at'])}")
                    print(f"Size: {file['bytes']:,} bytes")
            else:
                print("No files found matching the pattern.")

        elif command == "--vs-delete-where" and len(parts) > 1:
            pattern = parts[1]
            print(f"\nWARNING: This will delete all vector stores containing '{pattern}' in their name.")
            confirmation = input("Are you sure you want to proceed? (yes/no): ").lower()
            if confirmation == "yes":
                deleted_stores = manager.delete_vector_stores_by_pattern(pattern, dry_run=False)
                if deleted_stores:
                    print(f"\nSuccessfully deleted {len(deleted_stores)} vector stores:")
                    for store in deleted_stores:
                        print(f"- {store['name']} ({store['id']})")
                else:
                    print("No vector stores found matching the pattern.")
            else:
                print("Operation cancelled.")

        elif command == "--vs-delete-where-dry" and len(parts) > 1:
            pattern = parts[1]
            matching_stores = manager.delete_vector_stores_by_pattern(pattern, dry_run=True)
            if matching_stores:
                print(f"\nFound {len(matching_stores)} vector stores that would be deleted:")
                for store in matching_stores:
                    display_vector_store(store)
                    print("-" * 50)
            else:
                print("No vector stores found matching the pattern.")

        else:
            print("Unknown command. Type --help for available commands.")

    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        print(f"Error executing command: {str(e)}")

def interactive_mode():
    """Run the program in interactive mode."""
    try:
        logger.info("Starting interactive mode")
        manager = OpenAIStorageManager()
        print("OpenAI Storage Management Tool - Interactive Mode")
        print("Type --help for available commands or --exit to quit")
        
        while True:
            try:
                cmd = input("\n> ").strip()
                if cmd.lower() == "--exit":
                    logger.info("Exiting interactive mode")
                    break
                if cmd:
                    logger.info(f"Received command: {cmd}")
                    parse_interactive_command(cmd, manager)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                print("\nUse --exit to quit")
            except Exception as e:
                logger.error(f"Error in interactive mode: {str(e)}")
                print(f"Error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to start interactive mode: {str(e)}")
        print(f"Failed to start interactive mode: {str(e)}")

def main():
    if len(sys.argv) > 1:
        # Original command-line mode
        parser = argparse.ArgumentParser(description="OpenAI Storage Management Tool")
        subparsers = parser.add_subparsers(dest="command", help="Commands")

        # List vector stores
        list_parser = subparsers.add_parser("list", help="List all vector stores")
        list_parser.add_argument("--limit", type=int, default=20, help="Number of stores to list")
        list_parser.add_argument("--order", choices=["asc", "desc"], default="desc", help="Sort order")

        # Create vector store
        create_parser = subparsers.add_parser("create", help="Create a new vector store")
        create_parser.add_argument("name", help="Name of the vector store")
        create_parser.add_argument("--files", nargs="*", help="File IDs to include")

        # Get vector store details
        get_parser = subparsers.add_parser("get", help="Get vector store details")
        get_parser.add_argument("id", help="Vector store ID")

        # Delete vector store
        delete_parser = subparsers.add_parser("delete", help="Delete a vector store")
        delete_parser.add_argument("id", help="Vector store ID")

        # List files in vector store
        vs_files_parser = subparsers.add_parser("vs-files", help="List files in a vector store")
        vs_files_parser.add_argument("id", help="Vector store ID")
        vs_files_parser.add_argument("--limit", type=int, default=20, help="Number of files to list")

        # Upload file
        upload_parser = subparsers.add_parser("upload", help="Upload a file")
        upload_parser.add_argument("file", help="Path to the file to upload")
        upload_parser.add_argument("purpose", choices=["assistants", "vision", "fine-tune", "batch"], 
                                 help="Purpose of the file")

        # List files
        list_files_parser = subparsers.add_parser("list-files", help="List all files")
        list_files_parser.add_argument("--purpose", choices=["assistants", "vision", "fine-tune", "batch"],
                                     help="Filter by purpose")
        list_files_parser.add_argument("--limit", type=int, default=100, help="Number of files to list")
        list_files_parser.add_argument("--order", choices=["asc", "desc"], default="desc", help="Sort order")

        # Get file details
        file_get_parser = subparsers.add_parser("file", help="Get file details")
        file_get_parser.add_argument("id", help="File ID")

        # Delete file
        file_delete_parser = subparsers.add_parser("file-delete", help="Delete a file")
        file_delete_parser.add_argument("id", help="File ID")

        # Download file content
        file_content_parser = subparsers.add_parser("file-content", help="Get file content")
        file_content_parser.add_argument("id", help="File ID")
        file_content_parser.add_argument("--output", help="Output file path")

        args = parser.parse_args()
        manager = OpenAIStorageManager()

        if args.command == "list":
            stores = manager.list_vector_stores(limit=args.limit, order=args.order)
            if stores and "data" in stores:
                print(f"\nFound {len(stores['data'])} vector stores:")
                for store in stores["data"]:
                    display_vector_store(store)
                    print("-" * 50)

        elif args.command == "create":
            store = manager.create_vector_store(args.name, args.files)
            if store:
                print("\nCreated new vector store:")
                display_vector_store(store)

        elif args.command == "get":
            store = manager.get_vector_store(args.id)
            if store:
                display_vector_store(store)

        elif args.command == "delete":
            result = manager.delete_vector_store(args.id)
            if result and result.get("deleted"):
                print(f"\nSuccessfully deleted vector store: {args.id}")

        elif args.command == "vs-files":
            files = manager.list_vector_store_files(args.id, args.limit)
            if files and "data" in files:
                print(f"\nFound {len(files['data'])} files in vector store {args.id}:")
                for file in files["data"]:
                    print(f"\nFile ID: {file.get('id')}")
                    print(f"Created: {format_timestamp(file.get('created_at'))}")
                    print(f"Status: {file.get('status')}")
                    if file.get('usage_bytes'):
                        print(f"Size: {file.get('usage_bytes')} bytes")
                    print("-" * 30)

        elif args.command == "upload":
            file = manager.upload_file(args.file, args.purpose)
            if file:
                print("\nUploaded file:")
                display_file(file)

        elif args.command == "list-files":
            files = manager.list_files(args.purpose, args.limit, args.order)
            if files and "data" in files:
                print(f"\nFound {len(files['data'])} files:")
                for file in files["data"]:
                    display_file(file)
                    print("-" * 50)

        elif args.command == "file":
            file = manager.get_file(args.id)
            if file:
                display_file(file)

        elif args.command == "file-delete":
            result = manager.delete_file(args.id)
            if result and result.get("deleted"):
                print(f"\nSuccessfully deleted file: {args.id}")

        elif args.command == "file-content":
            content = manager.get_file_content(args.id, args.output)
            if content and not args.output:
                print("\nFile content:")
                print(content.decode('utf-8'))

        else:
            parser.print_help()
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
