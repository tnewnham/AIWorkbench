import os
from rich.console import Console

console = Console()

def validate_environment_variables(required_vars):
    """
    Validate that all required environment variables are set.
    :param required_vars: A dictionary where keys are variable names and values are the variables themselves.
    :raises EnvironmentError: If any required environment variable is missing.
    """
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

    console.print("All required environment variables are set.", style="bold green") 