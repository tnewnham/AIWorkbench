# AIWorkbench

AIWorkbench is a Python-based application that provides both a **terminal interface** and a **GUI** for interacting with advanced language models (OpenAI GPT-like assistants, Google's Gemini, Anthropic Claude, etc.). It supports:

- **Multiple assistant configurations** (financial analysis, research analysis, style profiling, etc.).
- **Vector store management** for uploading, listing, and retrieving files.
- **Workflow orchestration** for generating outlines, formulating clarifying questions, searching vector stores, writing final responses, and reviewing them in iterative loops. Started by prompting the lead assistant run either run a finalcial analysis report or a research paper analysis.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [GUI Mode](#gui-mode)
  - [Terminal Mode](#terminal-mode)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Assistant Configurations](#assistant-configurations)
- [Workflows](#workflows)
- [Contributing](#contributing)
- [License](#license)

---

## Features

1. **Terminal Interface**: Start a simple interactive chat session with a single assistant.  
2. **GUI Mode (Qt5)**: Leverages PyQt5 for a graphical interface that includes:  
   - A chat interface featuring a conversation panel, file uploads, structured messages.  
   - Sidebar panels for managing vector stores, chat completion models, and assistant configurations.  
3. **Multiple Assistants / Agents**:
   - Financial analysis, research analysis, lead assistant, style profiler, etc.
   - Each agent can be dynamically created or retrieved by code in `src/openai_assistant.py` and `src/assistant_config.py`.
4. **OpenAI Resource Manager**:
   - Manage vector stores (create, delete, list, or retrieve).
   - Manage files in your OpenAI account (upload, download, delete).
   - Pattern-matching to delete or list resources that match a certain string.
5. **Analysis Workflow**:
   - Outline an analysis or research subject.
   - Generate clarifying questions.
   - Run vector-store-based searches to answer these questions.
   - Feed the content to a "writer" agent for final drafting.
   - Optionally loop with a "reviewer" agent to refine content until complete.

---

## Installation

1. **Clone this repository** (or download the source code):
   ```bash
   git clone https://github.com/example/aiworkbench.git
   cd aiworkbench
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Create or update your `.env` file at the project root (see [Environment Variables](#environment-variables) for more info):
     ```bash
     OPENAI_API_KEY=...
     # ...
     ```

---

## Usage

### GUI Mode

1. **Run in GUI mode**:
   ```bash
   python main.py
   ```
   - If you do **not** specify `--terminal` or `-t`, the application tries to launch the Qt5 GUI.
   - The GUI includes:
     - **Chat Tab:** A conversation panel with an AI assistant, a message history, and file uploads.
     - **Assistants Panel:** Manage different assistants (create, delete, or assign them to the active chat).
     - **Vector Stores Panel:** Manage your vector stores and files.
     - **Chat Models Panel:** Switch between different chat completion configurations.

### Terminal Mode

1. **Run in Terminal mode**:
   ```bash
   python main.py --terminal
   ```
2. **Interact**: The program will show a banner, then let you type messages.  
   - Type your text to continue a conversation with the system.
   - Type `--help` or check the docstrings for more commands.
   - Type `exit` or `quit` to leave the session.

---

## Project Structure 

```
aiworkbench/
│
├── main.py                         # Entry point - parses arguments for terminal or GUI mode
├── requirements.txt                # Python dependencies
├── .env (example)                  # Environment variables (user-provided)
│
├── src/
│   ├── openai_assistant.py         # Primary module for communicating with OpenAI
│   ├── assistant_config.py         # Classes to create various specialized assistants
│   ├── chat_completion_config.py   # Configuration for chat completions
│   ├── task_functions.py           # High-level tasks (financial analysis, research, etc.)
│   ├── analyst.py                  # AnalysisTask class implementing a multi-agent workflow
│   ├── vector_storage.py           # Helper functions to upload or list files in vector stores
│   ├── openai_resource_manager.py  # CLI tool to manage vector stores & files
│   ├── terminal_interface.py       # Terminal-based interactive chat
│   ├── chat_ui_qt.py               # PyQt5-based chat UI elements
│   ├── main_window.py              # Main PyQt5 window & layout
│   ├── editor.py                   # Stub for a fine-tune editor (placeholder)
│   ├── signals.py                  # Global PyQt signals for cross-module communication
│   ├── chat_completion.py          # Helper classes/functions for chat completion with streaming
│   ├── chat_completion_panel.py    # PyQt5 panel to manage multiple completion configurations
│   ├── vector_store_panel.py       # PyQt5 panel for vector store creation, deletion, file uploads
│   ├── assistants_panel.py         # PyQt5 panel to list, create, or delete OpenAI assistants
│   ├── windows_style_helper.py     # Dark title bar styling for Windows
│   ├── workflow_manager.py         # Manages background tasks for multi-agent workflows
│   └── ...
│
└── tests/                          # (Optional) test files or placeholders
```

---

## Environment Variables

Your `.env` file (or environment variable settings) should include at least:

- **OPENAI_API_KEY**: The API key for OpenAI.  
- **GOOGLE_GEMINI_API_KEY**: Required for workflow.  
- **ENVIRONMENT**: "development" or "production" for debug mode & polling intervals.  
- **ASSISTANT_ID**: The ID of your lead assistant, if you want the default terminal interface to use a specific assistant.  

You can also set IDs for other specialized assistants if you already created them manually, or rely on the `assistant_config.py` classes to create them on startup.

---

## Assistant Configurations

In `src/assistant_config.py`, you will find classes for different specialized workflows:

1. **LeadAssistantConfig**: Creates a single "lead" assistant that can handle a broad conversation.  
2. **FinancialAssistantConfig**: Creates agents specialized in financial analysis.  
3. **ResearchAssistantConfig**: Creates agents specialized in research-oriented tasks.  
4. **WritingStyleProfilerConfig**: Analyzes a user's writing style from a vector store of text and returns a json that can be used to edit ai generated text to match the users writing stye (More features to come).  

These classes rely on `OpenAiAssistantManager` (and thus your `OPENAI_API_KEY`) to create or retrieve assistants. They set up instructions, model choices, and tool resources (like code interpreter or file search).

---

## Workflows

### Analysis Flow (Example)
1. **Outline Agent**: Summarizes or outlines a domain-specific analysis.  
2. **Questions Agent**: Generates clarifying questions.  
3. **Vector-Store Search Agent**: Retrieves relevant text from user-provided documents.  
4. **Writer (Gemini/Other)**: Creates a cohesive final report.  
5. **Reviewer Agent**: Iterates, asks more clarifications if needed, and finalizes the analysis.

This process is orchestrated via the `AnalysisTask` in `src/analyst.py`, often triggered by `task_functions.py` or a GUI prompt.


## License

This project is available under the [MIT License](https://opensource.org/licenses/MIT), unless otherwise specified. See [LICENSE](LICENSE) for full details. 