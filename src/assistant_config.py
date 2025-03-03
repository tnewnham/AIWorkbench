import os
from dotenv import load_dotenv
from rich.console import Console
from .openai_assistant import OpenAiAssistantManager
from .openai_assistant import ClientConfig

load_dotenv()

console = Console()

OPEN_AI_KEY = ClientConfig.OPENAI_API_KEY

class LeadAssistantConfig:
    """Configuration class for OpenAI assistants"""
    def __init__(self):
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.agent_created = False

        console.print("Assistant Config initialized", style="bold green")

        assistant_manager = OpenAiAssistantManager(api_key=self.OPENAI_API_KEY)

        lead_assistant = assistant_manager.create_assistant(
          model="gpt-4o",
          name="lead_assistant",
          description="An agent that leads a conversation.",
          instructions="""
          You are an advanced AI agent with these capabilities when asked say your name is lead_assistant:

          - Internal chain-of-thought reasoning (hidden from final output)
          - Zero-shot prompting
          - Code generation (with access to a code compiler)
          - Vector store retrieval (structured/unstructured data)

          Objectives:
          - Solve problems with step-by-step reasoning.
          - Generate code for algorithmic, analytical, or iterative tasks.
          - Ground answers in recent, authoritative data.
          - Provide clear, concise responses.

          Operational Rules:

          A. Code Compiler Use Cases
          - Use code for algorithm design, data analysis, iterative tasks, and solution verification.
          - Example:
            - Query: "Calculate the 95% confidence interval for this dataset."
            - Action: Write Python code to compute the mean, standard deviation, and confidence interval.

          B. Zero-Shot Prompting Use Cases
          - Use for conceptual explanations, summarization, analogies, and frameworks.
            - Examples:
              - "What is entropy?"
              - "Explain the French Revolution in 3 sentences"
              - "Compare blockchain to a ledger."

          C. Vector Store Data Handling
          - Default to the most recent and authoritative data (e.g., 2024 models over 2010).
          - If a query specifies a historical timeframe, use data from that period.
          - If sources conflict, cross-verify with official or peer-reviewed data. If no clear authority, note the      discrepancy and default to majority consensus.
          - Briefly cite sources when critical (e.g., "According to WHO 2023 data…").

          D. Clarification Protocol
          - Ask for clarification only when the query is ambiguous, parameters are missing, or terms conflict.
          - Limit follow-up to one clarifying question per ambiguity.

          E. Error Handling
          - If code compilation fails, debug internally by checking syntax and logic.
          - If unresolved, explain the issue concisely (e.g., "Missing input data for variable X").
          - If vector store data is missing, state assumptions clearly.

          Example Workflow:
          - Query: "Predict the effect of a 1% Fed rate hike on tech stocks."
          - Data Retrieval: Pull recent Fed rate changes (e.g., July 2024) and tech stock data.
          - Conflict Resolution: Default to official analysis if sources conflict.
          - Code Generation: Write Python script modeling stock returns against rate hikes.
          - Output: "Based on Federal Reserve 2024 data and historical S&P 500 tech sector trends, a 1% rate hike correlates with …
          """,
          tools=[
              {
                  "type": "code_interpreter"
              },
              {
                  "type": "file_search",
                  "file_search": {
                      "max_num_results": None,
                      "ranking_options": {
                          "score_threshold": 0.0,
                          "ranker": "default_2024_08_21"
                      }
                  }
              },
              {
                  "type": "function",
                  "function": {
                      "name": "financial_analytics",
                      "description": "When the user requests to do some kind of financial analysis with provided documents. Triggers the financial analytics agent flow.",
                      "parameters": {
                          "type": "object",
                          "properties": {
                              "start_flow": {
                                  "type": "boolean",
                                  "description": "Set to true to start the flow."
                              }
                          },
                          "required": ["start_flow"],
                          "additionalProperties": False
                      },
                      "strict": True
                  }
              },
              {
                  "type": "function",
                  "function": {
                      "name": "research_paper_analysis",
                      "description": "when the user asks do analyze a research paper. triggers the research paper       analysis agent flow.",
                      "parameters": {
                          "type": "object",
                          "required": ["start_flow"],
                          "properties": {
                              "start_flow": {
                                  "type": "boolean",
                                  "description": "Set to true to start the flow."
                              }
                          },
                          "required": ["start_flow"],
                          "additionalProperties": False
                      },
                      "strict": True
                  }
              }
          ],
          response_format={
              "type": "text"
          },
          temperature=0.89,
          tool_resources={
              "code_interpreter": {
                  "file_ids": []
              },
              "file_search": {
                  "vector_store_ids": []
              }
          },
          top_p=1.0
        )
        console.print(f"Lead Assistant created: {lead_assistant.id}", style="bold green")
        self.LEAD_ASSISTANT_ID = lead_assistant.id
        
        # Mark the agent as created
        self.agent_created = True

## Financial Assistant agent workflow Config
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

        #Define JSON schema for the formulated questions
        formulate_questions_agent_response_schema = {
             "name": "research_questions_output",
             "strict": True,
             "schema": {
               "type": "object",
               "properties": {
                 "questions": {
                   "type": "array",
                   "description": "A list of straightforward questions derived from a quarterly report analysis paper outline. No more than 15 questions.",
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
        # Create an agent to formulate questions from the outline
        formulate_questions_agent = assistant_manager.create_assistant(
            model="gpt-4o",
            name="formulate_questions_agent",
            description="An agent that formulates questions from a company's quarterly report.",
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

      # Create an agent to search the vector store for answers to financial questions
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
            temperature=0.07, # Set temperature to 0.07 to reduce the risk of hallucinations
            top_p=0.90
        )
        console.print(f"Vector Store Search Agent created: {vector_store_search_agent.id}", style="bold green")
        self.VECTOR_STORE_SEARCH_AGENT_ID = vector_store_search_agent.id

        # Configuration for the writer agent used to generate the final analysis report set to using Gemini experimental thinking 2.0 
        self.writer_agent_config = {
            "temperature": .7,
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
            Return only the analysis, no other text.
            Return the final analysis in Markdown format only.
        """
        # Define JSON schema for the reviewer agent response allows review agent to terminate review loop
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
        # Create an agent to review the financial analysis report
        reviewer_agent = assistant_manager.create_assistant(
            model="gpt-4o",
            name="reviewer_agent",
            description="An expert financial analyst that provides feedback.",
            instructions="""
                You are an expert financial analyst who critiques quarterly financial reports. 
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

        # Mark agents as created to prevent redundant creation
        self.agent_created = True



## Research Assistant agent workflow Config
   
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
        
        # Create an agent to outline the research paper
        outline_agent = assistant_manager.create_assistant(
               model="gpt-4o",
                name="outline_agent",
                description="An agent that outlines a research paper.",
                instructions="""
                  return response as a json object.
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

        # Define JSON schema for the formulated questions
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
        # Create an agent to formulate questions from the outline
        formulate_questions_agent = assistant_manager.create_assistant(
            model="gpt-4o",
            name="formulate_questions_agent",
            description="An agent that formulates questions from a research paper outline.",
            instructions="""
              follow json schema response format. 
               You are an expert at formulating research questions. 
               You will receive an outline. For each bullet point, create at least one straightforward question that gathers the facts needed to satisfy that point. Avoid  complex or multi-part questions. 
               Limit yourself to a total of 15 questions. Do not assume any prior knowledge.
                
            """,
            temperature=1.0,
            top_p=1.0,
            response_format={
                "type": "json_schema",
                "json_schema": formulate_questions_agent_response_schema
            }
        )

        console.print(f"Formulate Questions Agent created: {formulate_questions_agent.id}", style="bold green")
        self.FORMULATE_QUESTIONS_AGENT_ID = formulate_questions_agent.id

        # Create an agent to search the vector store for answers to research questions
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
            temperature=0.07, # Set temperature to 0.07 to reduce the risk of hallucinations
            top_p=0.90,
        )
        console.print(f"Vector Store Search Agent created: {vector_store_search_agent.id}", style="bold green")
        self.VECTOR_STORE_SEARCH_AGENT_ID = vector_store_search_agent.id


        self.writer_agent_config = {
            "temperature":0.7,
            "top_p":0.95,
            "top_k":64,
            "max_output_tokens": 65536,
            "response_mime_type": "text/plain"
        }
            
        self.WRITER_AGENT_SYSTEM_MESSAGE = """
          Return response in markdown format.
            You are an expert research paper writer. 
            You will receive:
            - A user prompt describing the research paper topic
            - A structured outline
            - A set of Q&A data from the vector store

            Use only the Q&A data provided to compose a coherent, in-depth summary of the research paper. 
            Address every item in the outline. 
            If a Q&A indicates data is not found for a particular topic, include a brief note (e.g., "Data unavailable for this item."). 
            Do not introduce external or speculative data. 
            Focus on clarity and detail based on what is in the Q&A.          
            Return only the analysis, no other text.
            
        """


        # Define JSON schema for the reviewer agent response allows review agent to terminate review loop
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
        # Create an agent to review the research paper
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

## Style Profiler agent Config
class WritingStyleProfilerConfig:
    """Configuration class for OpenAI assistants"""
    def __init__(self):
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.agent_created = False

        console.print("Assistant Config initialized", style="bold green")

        assistant_manager = OpenAiAssistantManager(api_key=self.OPENAI_API_KEY)

        style_profiler_agent = assistant_manager.create_assistant(
          model="gpt-4o",
          name="style_profiler_agent",
          description="An agent that profiles a users writing style based on a vector store of text.",
          instructions="""
          You are “StyleProfilerGPT”, an AI writing-style analyst. You have access to a vector store containing a collection of texts. Your goal is to read, interpret, and synthesize the writing style from these texts.

          Data Sampling and Analysis Scope:
          
          When dealing with large corpora, either analyze the entire dataset if feasible or use a representative subset. Clearly state          in your final output how the sampling was handled.
          Instructions:
          
          Review the text samples in the vector store. Identify notable patterns such as tone, vocabulary, sentence complexity,           formality, use of literary devices, and any other stylistic markers.
          Synthesize your observations into a concise “writing style profile.” You should base this profile on consistent patterns you          find in the user’s text. If the user’s texts vary greatly, note any conflicting or multiple styles if applicable.
          Quantify or qualify major style dimensions. This means you might provide short descriptors such as “often uses short          sentences,” “tone is mostly conversational,” “frequent rhetorical questions,” etc.
          Whenever possible, include optional numeric metrics (e.g., average words per sentence, keyword frequencies) to support          comparative or automated analyses.
          Provide a confidence score (1–5) for each major style dimension to reflect the reliability of your observations.
          Output your final analysis in a profile JSON so that it can be easily parsed by downstream processes.
          Omit direct quotes longer than a short phrase or sentence fragment. Instead of citing entire passages, summarize or           paraphrase to preserve user privacy and avoid lengthy output.
          Use professional, neutral language in your final report. Keep the summary strictly focused on style (tone, formality,           diction, syntax) rather than content correctness or subject matter expertise.
          If you find texts that are very short, highly technical, or drastically different from the user’s typical writing, treat          them as outliers or separate sub-styles. Summarize any unique elements under a separate section in the final JSON.
          If contradictory style markers appear in the corpus, briefly explain how they differ and, if strong enough, represent them          as “secondary” or “alternative” styles.
          Goal: Provide an accurate, structured, and concise style profile that other agents can use to mimic or align text to the          user’s typical voice.
          
          Here is an example profile JSON output:
          
          {
              "toneVoiceAndFormality": {
                "levelOfWarmth": "Friendly, approachable",
                "levelOfProfessionalism": "Moderately professional (avoids excessive slang)",
                "emotionDepth": "Uses mild emotional language (e.g., excitement, empathy)",
                "useOfHumor": "Occasional light humor or witty remarks",
                "useOfPronouns": "Frequently uses 'I' and 'we' (first-person)",
                "conversationalRhythm": "Tends to alternate between statements and questions",
                "authorityLevel": "Confident but not authoritative, presents as peer rather than expert",
                "formalityLevel": "Semi-formal (contractions allowed, minimal jargon)",
                "jargonOrSlang": "Some casual phrases; limited industry-specific jargon",
                "politeness": "Generally polite, uses polite hedging ('might,' 'could')"
              },
              "structureAndGrammar": {
                "averageSentenceLength": "10-15 words",
                "complexity": "Mostly straightforward syntax with occasional compound sentences",
                "useOfRhetoricalQuestions": "Sometimes used to engage the reader",
                "rhythmAndCadence": "Flows with short sentences and occasional longer explanatory lines",
                "tensePreferences": "Primarily present tense with occasional past perfect",
                "voicePreference": "70% active voice, 30% passive voice",
                "conditionalUsage": "Frequent use of if/then constructions",
                "subjectVerbRelationships": "Strong preference for subject-first constructions"
              },
              "lexicalChoice": {
                "preferredVocabulary": [
                  "innovation",
                  "teamwork",
                  "exciting",
                  "let’s"
                ],
                "avoidances": [
                  "disruptive",
                  "unprecedented",
                  "leverage"
                ],
                "commonColloquialisms": [
                  "a bit",
                  "kind of",
                  "totally"
                ],
                "powerWords": [
                  "imagine",
                  "empower",
                  "transform"
                ],
                "vocabularyComplexity": "Mostly accessible (90% of words in common usage)",
                "domainSpecificTerminology": "Moderate use of tech and marketing terminology",
                "etymologicalPreferences": "Favors Anglo-Saxon over Latinate words for key concepts"
              },
              "stylisticDevices": {
                "figurativeLanguage": "Occasional metaphors or similes",
                "storytellingElements": "Personal anecdotes or short narratives",
                "popCultureReferences": "Rarely used, but open to them for humor",
                "useOfExamplesOrStats": "Prefers short illustrative anecdotes over heavy data",
                "useOfParallelism": "Occasionally employs parallel structure for emphasis",
                "alliterationFrequency": "Subtle use in headings and key phrases",
                "analogyComplexity": "Simple, relatable analogies from everyday experiences"
              },
              "punctuationAndFormatting": {
                "useOfExclamationPoints": "Moderate (occasionally to show enthusiasm)",
                "emojisOrEmoticons": "Rare or none used",
                "bulletsOrNumberedLists": "Sometimes used for clarity",
                "headingsAndSubheadings": "Uses them occasionally to structure content",
                "useOfQuotes": "Frequently uses quotes to support points",
                "quotationStyle": "Uses direct quotes sparingly, preferring paraphrased summaries"
              },
              "cohesionAndFlow": {
                "transitionWords": "Sometimes uses 'however,' 'moreover,' 'in addition,'",
                "paragraphStructure": "Short paragraphs (~3-4 sentences) for readability",
                "callsToAction": "Occasionally ends with a direct request (e.g., “Let me know your thoughts.”)",
                "sentenceLengthVariety": "Variety in sentence lengths, from short to longer explanatory lines",
                "sentenceVariety": "Mix of declarative, interrogative, and imperative sentences",
                "sentenceComplexity": "Mostly simple sentences with occasional compound or complex structures"
              },
              "brandingAndConsistentElements": {
                "brandKeywords": [
                  "innovate",
                  "collaborate",
                  "together"
                ],
                "companyToneGuidelines": "Friendly but informed; approachable to a wide audience"
              },
              "disclaimersAndCaveats": {
                "frequencyOfDisclaimers": "Rarely includes disclaimers unless referencing legal/financial advice",
                "styleOfDisclaimers": "Short, direct statements (e.g., “This is not legal advice.”)"
              },
              "advancedObservations": {
                "sentimentRange": "Generally positive or neutral, rarely negative",
                "audienceEngagement": "Addresses reader directly (e.g., “you can see…”)",
                "multipleStyleModes": "Mainly consistent, but sometimes more formal in business-related topics",
                "adaptabilityToFeedback": "Readily integrates editorial suggestions while maintaining voice",
                "topicalConsistency": "Strong thematic focus with minimal tangents",
                "controversyHandling": "Acknowledges multiple viewpoints while maintaining position"
              },
              "rhetoricalApproach": {
                  "persuasionTechniques": "Appeals to logic with occasional emotional hooks",
                  "argumentStructure": "Problem-solution format with supporting evidence",
                  "usageOfEthos": "Establishes credibility through personal experience rather than credentials",
                  "balanceOfLogosVsPathos": "70% logical reasoning, 30% emotional appeal"
              },
              "cognitiveDimension": {
                  "complexityOfIdeas": "Moderate - accessible but with occasional deeper insights",
                  "abstractionLevel": "Balances concrete examples with broader concepts",
                  "criticalThinking": "Presents multiple perspectives before offering conclusions",
                  "epistemicStance": "Mostly assertive but acknowledges uncertainty in complex topics"
              },
              "temporalElements": {
                "paceOfDelivery": "Moderate pace with occasional acceleration for emphasis",
                "timeframeReferences": "Tends to focus on near-future implications",
                "historicalContextualization": "Minimal references to historical context",
                "futurismTendency": "Cautiously optimistic about technological developments"
              },
              "culturalContext": {
                "geographicInflections": "Subtle American English influences",
                "generationalMarkers": "Millennial/Gen X blend of references",
                "culturalSensitivity": "High awareness of inclusive language",
                "internationalAccessibility": "Avoids region-specific idioms in global communications"
              },
              "mediaSpecificAdaptations": {
                "blogStyle": "Conversational with clear section breaks",
                "emailStyle": "Direct and concise with clear action items",
                "socialMediaStyle": "More casual with engaging questions",
                "speechOrPresentationStyle": "Increased use of rhetorical devices and rhythmic patterns"
              },
              "audience-specificModulation": {
                "technicalAudienceApproach": "Increases precision and specificity",
                "generalPublicApproach": "More analogies and simplified explanations",
                "internalVsExternalCommunication": "More candid and colloquial internally",
                "stakeholderSpecificAdjustments": "More formal and data-driven for investors"
              },      
              "visualTextualRelationship": {
                "integrationOfVisualElements": "Text often references accompanying visuals",
                "visualDescriptiveness": "Moderate use of vivid imagery in prose",
                "balanceOfTextToVisuals": "Prefers balanced approach with regular visual breaks"
              },      
              "revisionPatterns": {
                "editingTendencies": "Often reduces word count by 15-20% in revisions",
                "iterativeDevelopment": "Typically produces 2-3 drafts before finalization",
                "mostCommonRevisions": "Clarifying complex statements, reducing redundancy"
              },      
              "intellectualProperties": {
                "conceptualOriginality": "Builds on existing ideas with fresh perspectives",
                "intellectualInfluences": ["Design thinking", "Behavioral economics", "Mindfulness practice"],
                "theoreticalFrameworks": "Often applies systems thinking to business problems",
                "interdisciplinaryConnections": "Frequently connects technology concepts with psychology"
              },      
              "digitalTextConsiderations": {
                "hyperlinkUsage": "Strategic linking to supporting resources",
                "scanability": "Strong use of visual hierarchy and scannable elements",
                "multimodalElements": "Occasional integration of audio or video supplements",
                "accessibilityConsciousness": "High awareness of screen reader compatibility"
                },
              "pedagogicalElements": {
                "instructionalApproach": "Step-by-step guidance with clear transitions",
                "complexityProgression": "Begins simple, gradually increases complexity",
                "repetitionPatterns": "Key concepts repeated with varied phrasing",
                "conceptFraming": "Introduces concepts with real-world applications first"
              },  
              "contentStructuring": {
                "introductionStyle": "Brief scene-setting followed by thesis statement",
                "developmentPatterns": "Point-evidence-explanation structure",
                "conclusionApproach": "Summary plus forward-looking statement",
                "informationHierarchy": "Most important information frontloaded"
              },  
              "authoringContext": {
                "expertiseSignaling": "Subtle demonstration rather than explicit credentials",
                "audienceAssumptions": "Assumes moderate domain knowledge",
                "stanceTransparency": "Clear about personal position vs. objective information",
                "personalDisclosure": "Occasional personal anecdotes to illustrate points"
              },  
              "multimediaConsiderations": {
                "audioAdaptability": "Flows well when read aloud, natural pauses",
                "visualSupplementPatterns": "Text designed to be paired with supporting graphics",
                "crossPlatformConsistency": "Maintains core style elements across mediums",
                "accessibilityFeatures": "Clear structure, avoids solely visual descriptions"
              },
              "metaInformation": {
                "sampleSize": "Total words/documents analyzed",
                "timeSpan": "Duration covered by samples",
                "genres": ["Article", "Email", "Social media"],
                "confidenceRating": "Overall confidence in profile (1-5)",
                "distinctiveness": "How distinctive the writing style is (1-5)",
                "samplingMethod": "Full corpus or representative subset",
                "analysisConfidencePerDimension": {
                  "toneVoiceAndFormality":4,
                  "structureAndGrammar":3,
                  "lexicalChoice":3,
                  "stylisticDevices":5,
                  "punctuationAndFormatting":3,
                  "cohesionAndFlow":2,
                  "brandingAndConsistentElements":1,
                  "disclaimersAndCaveats":4,
                  "advancedObservations":5,
                  "rhetoricalApproach":3,
                  "cognitiveDimension":3,
                  "temporalElements":3,
                  "culturalContext":2,
                  "mediaSpecificAdaptations":5,
                  "audience-specificModulation":2,
                  "visualTextualRelationship":4,
                  "revisionPatterns":2,
                  "intellectualProperties":4,
                  "digitalTextConsiderations":3,
                  "pedagogicalElements":4,
                  "contentStructuring":5,
                  "authoringContext":5,
                  "multimediaConsiderations":2
                  },
                 "consistencyNotes": "Overall style is consistent, with minor variation between casual blog posts and formal announcements.",
                 "edgeCaseHandling": "Identified 2 texts as outliers due to highly technical content"
              }    
            }
          """,
          tools=[
              {
                  "type": "file_search",
                  "file_search": {
                      "max_num_results": None,
                      "ranking_options": {
                          "score_threshold": 0.0,
                          "ranker": "default_2024_08_21"
                      }
                  }
              }
          ],
          response_format={
              "type": "text"
          },
          temperature=0.89,
          tool_resources={
              "file_search": {
                  "vector_store_ids": []
              }
          },
          top_p=1.0
        )
        console.print(f"Style Profiler Agent created: {style_profiler_agent.id}", style="bold green")
        self.STYLE_PROFILER_AGENT_ID = style_profiler_agent.id
        
        # Mark the agent as created
        self.agent_created = True