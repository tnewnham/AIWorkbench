import os
from dotenv import load_dotenv
from rich.console import Console
from .openai_assistant import OpenAiAssistantManager
from .openai_assistant import ClientConfig

load_dotenv()

console = Console()

OPEN_AI_KEY = ClientConfig.OPENAI_API_KEY


## Financial Assistant Config
class FinancialAssistantConfig:
    """Configuration class for OpenAI assistants"""
    def __init__(self):    
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
        self.agent_created = False

    
    def create_agents(self):
        # Placeholder for dynamically created assistant IDs
        self.OUTLINE_AGENT_ID = None
        self.FORMULATE_QUESTIONS_AGENT_ID = None
        self.VECTOR_STORE_SEARCH_AGENT_ID = None
        self.WRITER_AGENT_ID = None
        self.REVIEWER_AGENT_ID = None


        self.DEBUG_MODE = self.ENVIRONMENT == "development"
        self.POLL_INTERVAL = 2 if self.ENVIRONMENT == "development" else 5


        assistant_manager = OpenAiAssistantManager(api_key=self.OPENAI_API_KEY)

        console.print("Creating Agents", style="bold yellow")

        outline_agent = assistant_manager.create_assistant(
            model="gpt-4o",
            name="outline_agent",
            description="An agent that outlines a quartly report analysis paper.",
            instructions="""
                You are an expert at planning comprehensive financial analyses of a company's quarterly report. 
                The user will provide a company name, reporting period, and any special focus (e.g., cost structure, revenue trends). 
                Your job is to create a structured outline that thoroughly covers all relevant financial metrics. 
                Include sections that address:

                1. Executive Summary
                2. Revenue Analysis (year-over-year, quarter-over-quarter)
                3. Cost and Expense Breakdown (operating expenses, cost of goods sold, etc.)
                4. Profitability (gross margin, net margin, EBITDA if relevant)
                5. Balance Sheet Highlights (assets, liabilities, liquidity measures)
                6. Cash Flow Analysis
                7. Notable One-Time Items or Special Events
                8. Risks and Challenges
                9. Growth Outlook and Predictions (market trends, competitive positioning)
                10. Conclusion

                Another agent will then formulate questions for each section to gather the data needed to complete the analysis. 
                use json object response format.
            """,
            temperature=1.0,
            top_p=1.0,
            response_format={
                "type": "json_object"
            }
            )

        console.print(f"Outline Agent created: {outline_agent.id}", style="bold green")
        self.OUTLINE_AGENT_ID = outline_agent.id


        formulate_questions_agent_response_schema = {
             "name": "research_questions_output",
             "strict": True,
             "schema": {
               "type": "object",
               "properties": {
                 "questions": {
                   "type": "array",
                   "description": "A list of straightforward questions derived from a research paper outline. No more than 15 questions.",
                   "items": {
                     "type": "string",
                     "description": "A single straightforward question."
                   }
                 }
               },
               "required": [
                 "questions"
               ],
               "additionalProperties": False
             }
        }          

        formulate_questions_agent = assistant_manager.create_assistant(
            model="gpt-4o",
            name="formulate_questions_agent",
            description="An agent that formulates questions from a research paper outline.",
            instructions="""
                You are an expert at generating direct, finance-focused questions. 
                You will receive an outline for a company's financial analysis. 
                For each outline section, create questions that gather the essential facts from the quarterly report. 
                Each question should be straightforward and targeted (e.g., "What was the revenue growth rate this quarter compared to last year?"). 
                do not ask more than 13 questions. 
                Do not assume prior knowledge—ask for any data needed to fill the outline completely. 
                Follow the json schema response format provided.
            """,
            tools=[],
            tool_resources={},
            metadata={},
            temperature=1.0,
            top_p=1.0,
            response_format={
                "type": "json_schema",
                "json_schema": formulate_questions_agent_response_schema
            }
        )


        console.print(f"Formulate Questions Agent created: {formulate_questions_agent.id}", style="bold green")
        self.FORMULATE_QUESTIONS_AGENT_ID = formulate_questions_agent.id


        vector_store_search_agent = assistant_manager.create_assistant(
            model="gpt-4o-mini",
            name="vector_store_search_agent",
            description="An agent that searches a vector store for answers to questions.",
            instructions="""
                Answer the questions only with data available in the vector store. 
                Perform semantic searches to locate relevant passages from the company's quarterly filings, investor presentations, or related financial documents. 
                Summarize or quote only what is found, without introducing external information. 
                Cite page/section references if available. 
                If an answer cannot be found, state that the information is not in the store.

                Process:
                1. Identify Key Terms (e.g., "net income," "revenue Q3," "free cash flow")
                2. Perform Semantic Search on the vector store
                3. Extract and Summarize the relevant sections
                4. Formulate a concise, direct response with references

                Output Format:
                - Clear, concise sentences
                - Citations (page/section numbers where possible)
                - Note any missing data if the store has no matching content 
                - use json object response formatting when appropriate         
            """,
            tools=[
                {"type": "code_interpreter"},
                {"type": "file_search"}],
            temperature=0.07,
            top_p=0.90
        )
        console.print(f"Vector Store Search Agent created: {vector_store_search_agent.id}", style="bold green")
        self.VECTOR_STORE_SEARCH_AGENT_ID = vector_store_search_agent.id


        self.writer_agent_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 65536,
            "response_mime_type": "text/plain"
        }
            
        self.WRITER_AGENT_SYSTEM_MESSAGE = """
            You are an expert financial analyst. 
            You will receive:
            - A user prompt describing the company and reporting period
            - A structured outline
            - A set of Q&A data from the vector store

            Use only the Q&A data provided to compose a coherent, in-depth financial analysis. 
            Address every item in the outline. 
            If a Q&A indicates data is not found for a particular topic, include a brief note (e.g., "Data unavailable for this item."). 
            Do not introduce external or speculative data. 
            Focus on clarity and detail based on what is in the Q&A. 
            Do you think the company is a good investment?
            Return the final analysis in Markdown format only.
        """

        reviewer_agent_response_schema = {
              "name": "research_questions_output",
              "strict": True,
              "schema": {
                "type": "object",
                "properties": {
                  "questions": {
                    "type": "array",
                    "description": "A list of straightforward questions derived from a companies quartely report analysis paper",
                    "items": {
                      "type": "string",
                      "description": "A single straightforward question."
                    }
                  },
                  "last_questions": {
                    "type": "boolean",
                    "description": "Indicates whether these are the last questions (true) or not (false)."
                  }
                },
                "required": [
                  "questions",
                  "last_questions"
                ],
                "additionalProperties": False
              }
        }

        reviewer_agent = assistant_manager.create_assistant(
            model="gpt-4o",
            name="reviewer_agent",
            description="An expert financial analyst that provides feedback.",
            instructions="""
                You are an expert financial reviewer who critiques quarterly financial reports. 
                You are extremely detail-oriented, inquisitive and persnickety.

                You receive:
                - The user's original prompt
                - The financial analysis outline
                - The completed analysis

                Be thorough and have a bias toward seeking clarity. 
                Check whether the analysis fully addresses the prompt and covers each outline section with sufficient detail. 
                If any point is even slightly unclear, incomplete, or insufficiently supported, ask up to 4 direct, clarifying questions. 
                Each question should focus on what's missing or inadequately addressed. 
                If the analysis is unquestionably complete and all sections are well-supported, ask zero questions and set last_questions to true. 
                Do not request more information about items the data explicitly states are unavailable. 
                No multi part questions.
                Follow the json schema response format provided.
            """,
            temperature=1,
            top_p=0.95,
            response_format={
                "type": "json_schema",
                "json_schema": reviewer_agent_response_schema
            }
        )
        console.print(f"Reviewer Agent created: {reviewer_agent.id}", style="bold green")
        self.REVIEWER_AGENT_ID = reviewer_agent.id

        self.agent_created = True



## Research Assistant Config
   
class ResearchAssistantConfig:
    """Configuration class for OpenAI assistants"""
    def __init__(self):
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.OPENAI_API_KEY = os.getenv("AI_ANALYST_API_KEY")
        self.GOOGLE_GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
        self.agent_created = False

    # Placeholder for dynamically created assistant IDs
    def create_agents(self):
        self.OUTLINE_AGENT_ID = None
        self.FORMULATE_QUESTIONS_AGENT_ID = None
        self.VECTOR_STORE_SEARCH_AGENT_ID = None
        self.WRITER_AGENT_ID = None
        self.REVIEWER_AGENT_ID = None

        self.SEARCH_AGENT_VECTOR_STORE_ID = os.getenv("SEARCH_AGENT_VECTOR_STORE_ID")

        self.DEBUG_MODE = self.ENVIRONMENT == "development"
        self.POLL_INTERVAL = 2 if self.ENVIRONMENT == "development" else 5


        assistant_manager = OpenAiAssistantManager(api_key=self.OPENAI_API_KEY)

        console.print("Creating Agents", style="bold yellow")
        

        outline_agent = assistant_manager.create_assistant(
               model="gpt-4o",
                name="outline_agent",
                description="An agent that outlines a research paper.",
                instructions="""
                    You are an expert at planning research papers. 
                    The user will provide a topic and requirements. 
                    Your job is to create a detailed, specific outline. 
                    Break down each section with clear headings and subheadings. 
                    Include logical structure and any relevant subtopics or supporting points. 
                    Another agent will then formulate questions for each section to gather the facts needed to fill the outline.

            """,
            temperature=1.0,
            top_p=1.0,
            response_format={
                "type": "json_object"
            }
        )
        console.print(f"Outline Agent created: {outline_agent.id}", style="bold green")
        self.OUTLINE_AGENT_ID = outline_agent.id


        formulate_questions_agent_response_schema = {
             "name": "research_questions_output",
             "strict": True,
             "schema": {
               "type": "object",
               "properties": {
                 "questions": {
                   "type": "array",
                   "description": "A list of straightforward questions derived from a research paper outline.",
                   "items": {
                     "type": "string",
                     "description": "A single straightforward question."
                   }
                 }
               },
               "required": [
                 "questions"
               ],
               "additionalProperties": False
             }
        }          

        formulate_questions_agent = assistant_manager.create_assistant(
            model="gpt-4o",
            name="formulate_questions_agent",
            description="An agent that formulates questions from a research paper outline.",
            instructions="""
               You are an expert at formulating research questions. 
               You will receive an outline. For each bullet point, create at least one straightforward question that gathers the facts needed to satisfy that point. Avoid  complex or multi-part questions. 
               Limit yourself to a total of 15 questions. Do not assume any prior knowledge.
               follow json schema response format provided.  
            """,
            tools=[],
            tool_resources={},
            metadata={},
            temperature=1.0,
            top_p=1.0,
            response_format={
                "type": "json_schema",
                "json_schema": formulate_questions_agent_response_schema
            }
        )

        console.print(f"Formulate Questions Agent created: {formulate_questions_agent.id}", style="bold green")
        self.FORMULATE_QUESTIONS_AGENT_ID = formulate_questions_agent.id


        vector_store_search_agent = assistant_manager.create_assistant(
            model="gpt-4o-mini",
            name="vector_store_search_agent",
            description="An agent that searches a vector store for answers to questions.",
            instructions="""
                Answer questions solely using the data stored in the vector store. 
                Perform semantic searches to locate relevant passages that match the user's query. Summarize or quote the retrieved content to form a concise answer. 
                Include references to specific sections or page numbers when applicable. 
                If the question cannot be answered with the available information, clearly state that the relevant data is not found.

                Process
                Identify Key Terms
                Parse the user's question to extract topics, keywords, and entities.

                Semantic Search
                Query the vector store using the identified terms. 
                Retrieve paragraphs or sentences with the highest semantic similarity.

                Extract and Summarize
                If multiple passages are found, summarize the content or select the most relevant excerpt. 
                Provide sufficient detail for clarity without adding information not present in the vector store.

                Formulate Response
                Present the final answer as a short paragraph or bullet points. 
                Reference page or section numbers where relevant. If data is missing or does not address the query, 
                inform the user that the vector store does not contain the needed information.

                Output Format
                Clarity: Write in clear, concise sentences.
                References: Cite page numbers or sections where applicable.
                Honesty: If an answer cannot be located in the PDF, state that no matching content is found.
                Example
                Input:
                "What are the report's primary recommendations for cost reduction?"

                Process:

                Key terms: "report," "primary recommendations," "cost reduction."
                Use these terms in a semantic search of the vector store.
                Identify relevant passages discussing cost-saving strategies.
                Summarize the points addressing recommendations.
                Output:
                "The report recommends consolidating supply chains, renegotiating vendor contracts, 
                and reducing overhead expenses. For a detailed discussion, see pages 14-16."
            """,
            tools=[
                {"type": "code_interpreter"},
                {"type": "file_search"}],
            temperature=0.07,
            top_p=0.90,
        )
        console.print(f"Vector Store Search Agent created: {vector_store_search_agent.id}", style="bold green")
        self.VECTOR_STORE_SEARCH_AGENT_ID = vector_store_search_agent.id


        reviewer_agent_response_schema = {
              "name": "research_questions_output",
              "strict": True,
              "schema": {
                "type": "object",
                "properties": {
                  "questions": {
                    "type": "array",
                    "description": "A list of straightforward questions derived from a research paper outline.",
                    "items": {
                      "type": "string",
                      "description": "A single straightforward question."
                    }
                  },
                  "last_questions": {
                    "type": "boolean",
                    "description": "Indicates whether these are the last questions (true) or not (false)."
                  }
                },
                "required": [
                  "questions",
                  "last_questions"
                ],
                "additionalProperties": False
              }
        }

        reviewer_agent = assistant_manager.create_assistant(
            model="gpt-4o",
            name="reviewer_agent",
            description="An agent that reviews a research paper and provides feedback.",
            instructions="""
                You are an expert research paper reviewer who is extremely detail-oriented and inquisitive. You receive:
                A user prompt.
                An original outline.
                A paper prepared according to that outline.
                Your task:
                Evaluate whether the paper fully and accurately addresses the user prompt and outline with enough detail.
                If any point is unclear, incomplete, or insufficiently supported, produce up to 4 clarifying questions.
                Each question must be straightforward, avoid complex or multi-part questions.
                Be terse and neutral.
                Provide no unsolicited advice, commentary, or apologies.
                Only finalize when you are sure every element of the user prompt and outline is fulfilled, 
                meaning there are no more clarifications to seek. 
                At that point, provide zero questions and set last_questions to true.
                If the speaker indicates their source material does not cover a certain topic or question, do not keep asking about it.
                follow json schema response format provided.  
            """,
            temperature=1,
            top_p=0.95,
            response_format={
                "type": "json_schema",
                "json_schema": reviewer_agent_response_schema
            }
        )
        console.print(f"Reviewer Agent created: {reviewer_agent.id}", style="bold green")
        self.REVIEWER_AGENT_ID = reviewer_agent.id