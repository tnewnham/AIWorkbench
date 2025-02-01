import os
from dotenv import load_dotenv
from rich.console import Console
from src.analyst import AnalysisWorkflow
from src.assistant_config import FinancialAssistantConfig, ResearchAssistantConfig
from src.openai_assistant import ClientConfig

load_dotenv()
console = Console()

def main():
    # Example usage: pass a custom prompt and folder path
    example_prompt = (
        """Write an in-depth financial analysis of NVIDIA's Q1 2025 earnings report. 
        Focus on revenue trends, expenses, profitability, and any notable one-time items. 
        Evaluate the company's financial health, potential growth opportunities, and risks. 
        Discuss potential factors that might influence future performance.
        focus on AI, AI hardware trends, AI as a service, and robotics.
        Discuss the company's impact on the broader market."""
    )
    example_folder_path = "example_data/nvidia_fiscal_report_q1_2025/"  # adjust as needed
    
    use_financial_config = True  # This could be based on a command-line argument or config file

    if use_financial_config:
        config = FinancialAssistantConfig()
    else:
        config = ResearchAssistantConfig()

    config.create_agents()

    # Financial Assistant Config
    workflow = AnalysisWorkflow(
        user_prompt=example_prompt, 
        folder_path=example_folder_path, 
        OUTLINE_AGENT_ID=config.OUTLINE_AGENT_ID, 
        FORMULATE_QUESTIONS_AGENT_ID=config.FORMULATE_QUESTIONS_AGENT_ID, 
        VECTOR_STORE_SEARCH_AGENT_ID=config.VECTOR_STORE_SEARCH_AGENT_ID, 
        WRITER_AGENT_SYSTEM_MESSAGE=config.WRITER_AGENT_SYSTEM_MESSAGE, 
        WRITER_AGENT_CONFIG=config.WRITER_AGENT_ID,
        REVIEWER_AGENT_ID=config.REVIEWER_AGENT_ID, 
        GOOGLE_GEMINI_API_KEY=ClientConfig.GOOGLE_GEMINI_API_KEY,
        OPEN_AI_API_KEY=ClientConfig.OPENAI_API_KEY
    )
    
    workflow.run_analysis()

if __name__ == "__main__":
    main()
