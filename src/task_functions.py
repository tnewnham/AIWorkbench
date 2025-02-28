import os
from dotenv import load_dotenv
from rich.console import Console

from .analyst import AnalysisTask
from .assistant_config import FinancialAssistantConfig, ResearchAssistantConfig
from .openai_assistant import ClientConfig
from .openai_assistant import pretty_print
load_dotenv()
console = Console()

def analysis_task(user_prompt, folder_path, assistant_config):
    # Example usage: pass a custom prompt and folder path
    # adjust as needed
    # This could be based on a command-line argument or config file

    if assistant_config == "financial":
        config = FinancialAssistantConfig()
    elif assistant_config == "research":
        config = ResearchAssistantConfig()
    else:
        raise ValueError("No valid configuration selected")

    config.create_agents()
    # Financial Assistant Config
    task = AnalysisTask(
        user_prompt=user_prompt, 
        folder_path=folder_path, 
        OUTLINE_AGENT_ID=config.OUTLINE_AGENT_ID, 
        FORMULATE_QUESTIONS_AGENT_ID=config.FORMULATE_QUESTIONS_AGENT_ID, 
        VECTOR_STORE_SEARCH_AGENT_ID=config.VECTOR_STORE_SEARCH_AGENT_ID, 
        WRITER_AGENT_SYSTEM_MESSAGE=config.WRITER_AGENT_SYSTEM_MESSAGE, 
        WRITER_AGENT_CONFIG=config.WRITER_AGENT_ID,
        REVIEWER_AGENT_ID=config.REVIEWER_AGENT_ID, 
        GOOGLE_GEMINI_API_KEY=ClientConfig.GOOGLE_GEMINI_API_KEY,
        OPEN_AI_API_KEY=ClientConfig.OPENAI_API_KEY
    )
    
    analysis_writer_response, analysis_combined_message = task.run_analysis()

        # Combine the outputs with a double newline separator for readability.
    combined_analysis_text = analysis_writer_response + "\n\n" + analysis_combined_message
    
    # Save the combined text to the specified output file.
    with open("docs/analysis_output.txt", "w", encoding="utf-8") as output_file:
        output_file.write(combined_analysis_text)
        
    console.print(f"Analysis results saved to: {"docs/analysis_output.txt"}", style="bold green")
    #pretty_print(analysis_combined_message)
    #pretty_print(analysis_writer_response)
    return analysis_writer_response, analysis_combined_message



# example usage
if __name__ == "__main__":


    user_prompt = (
        """Write an in-depth financial analysis of NVIDIA's Q1 2025 earnings report. 
        Focus on revenue trends, expenses, profitability, and any notable one-time items. 
        Evaluate the company's financial health, potential growth opportunities, and risks. 
        Discuss potential factors that might influence future performance.
        focus on AI, AI hardware trends, AI as a service, and robotics.
        Discuss the company's impact on the broader market."""
    )
    folder_path = "example_data/nvidia_fiscal_report_q1_2025/" 
    assistant_config = "financial"

    analysis_writer_response, analysis_combined_message = analysis_task(user_prompt, folder_path, assistant_config)
    pretty_print(analysis_combined_message)
    pretty_print(analysis_writer_response)



