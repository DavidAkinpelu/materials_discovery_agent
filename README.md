# Materials Discovery Agent

An intelligent, AI-powered research assistant for materials science discovery. Built with **LangGraph** and **OpenAI** models, it autonomously explores scientific databases, validates findings, checks intellectual property status, and provides comprehensive materials recommendations.

## ✨ Features

- 🤖 **ReAct Agent Architecture**: Autonomous reasoning and action loop powered by LangGraph
- 🔬 **Multi-Database Integration**: Materials Project, PubChem, SureChEMBL, and Web Search
- 💬 **Conversational Interface**: Natural language queries with clarification capabilities
- 🧠 **Long-term Memory**: Persistent conversation history and user preferences
- 🎨 **Modern UI**: React + Tailwind CSS with markdown-formatted responses
- 🖼️ **Multimodal Support**: Chemical structure visualization with image generation
- 📊 **Observability**: Integrated Langfuse tracing for debugging and monitoring
- ⚡ **Async Architecture**: Non-blocking I/O for fast, parallel database queries

## 🏗️ Architecture

### ReAct Agent Workflow

The system uses a **ReAct (Reasoning + Acting)** pattern where the agent:

1. **Reasons** about which tools and databases to use
2. **Acts** by executing searches and analyses
3. **Observes** results and decides next steps
4. **Responds** with well-formatted, actionable insights

The agent autonomously:
- Translates vague queries into specific database searches
- Asks clarifying questions when needed (max 5 questions)
- Validates scientific accuracy of results
- Checks patent/IP status for novelty assessment
- Formats responses with proper markdown structure

### 🛠️ Integrated Tools & Databases

| Tool | Description | Use Cases |
|------|-------------|-----------|
| **Materials Project** | 150k+ inorganic materials with computed properties | Band gap, formation energy, elasticity, crystal structure |
| **PubChem** | 111M+ organic compounds with chemical properties | SMILES, molecular formulas, safety data, physical properties |
| **SureChEMBL** | Patent database with 20M+ chemical structures | IP status, novelty assessment, patent landscape analysis |
| **Exa.ai** | Semantic web search engine | Real-world applications, pricing, definitions, validation |
| **Image Generation** | Chemical structure visualization | SMILES to PNG conversion for multimodal analysis |

### 🧠 Memory & State Management

- **Short-term Memory**: SQLite-based conversation checkpoints via `AsyncSqliteSaver`
- **Long-term Memory**: User-specific facts and preferences via `AsyncSqliteStore`
- **Session Persistence**: Conversations resume across page refreshes

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (tested on 3.13)
- **Node.js 18+** (for frontend)
- **API Keys** (required):
  - [OpenAI API Key](https://platform.openai.com/api-keys) ()
  - [Materials Project API Key](https://materialsproject.org/api) (free registration)
  - [Exa.ai API Key](https://exa.ai/) (for web search)
- **Optional**:
  - [Langfuse Account](https://langfuse.com/) (for observability)

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd materials_discovery_agent
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys:
#   OPENAI_API_KEY=sk-...
#   MATERIALS_PROJECT_API_KEY=...
#   EXA_API_KEY=...
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Run the Application

**Terminal 1 - Backend (Port 8000):**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend (Port 5000):**
```bash
cd frontend
npm run dev
```

**Access the Application:**
Open your browser to `http://localhost:5000`

### 5. Optional: Enable Langfuse Observability

1. Sign up at [langfuse.com](https://langfuse.com/)
2. Create a project and copy your keys
3. Add to `backend/.env`:
   ```bash
   LANGFUSE_PUBLIC_KEY=pk-...
   LANGFUSE_SECRET_KEY=sk-...
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```
4. Restart the backend - traces will appear in your Langfuse dashboard

## ⚙️ Configuration

All settings are centralized in `backend/config.py` using Pydantic settings. Override via environment variables:

### Model Configuration
```bash
LLM_MODEL=gpt-4o                    # OpenAI model name
LLM_TEMPERATURE=0.0                  # Temperature (0.0-2.0)
```

### Search & Query Settings
```bash
DEFAULT_SEARCH_RESULTS=10            # Default number of search results
HTTP_TIMEOUT=30                      # HTTP request timeout (seconds)
```

### Server Ports
```bash
BACKEND_PORT=8000                    # Backend API port
FRONTEND_PORT=5000                   # Frontend dev server port
```

### Database Files
- `backend/long_term_memory.db` - User preferences and facts (long-term memory)

**Note:** Database files are automatically created on first run and are gitignored.

## 📊 Observability with Langfuse

Monitor agent execution, tool calls, and reasoning traces in real-time:

1. **Sign up**: [langfuse.com](https://langfuse.com/)
2. **Create project** and copy keys
3. **Configure** in `backend/.env`:
   ```bash
   LANGFUSE_PUBLIC_KEY=pk-...
   LANGFUSE_SECRET_KEY=sk-...
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```
4. **View traces** at your Langfuse dashboard

Traces include:
- Full conversation flow
- Tool execution timing
- LLM prompts and responses
- Error tracking

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Development Workflow

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature`
3. **Make changes** and test thoroughly
4. **Run linters** (if you add them): `black`, `isort`, `mypy`
5. **Commit**: `git commit -m "feat: add your feature"`
6. **Push**: `git push origin feature/your-feature`
7. **Open a Pull Request** with a clear description

### Areas for Contribution

- **New Data Sources**: Add wrappers for Crystallography Open Database, NIST, etc.
- **Advanced Queries**: Multi-step reasoning, comparison queries
- **UI Enhancements**: Data visualization, export features
- **Testing**: Unit tests for tools, integration tests for agent
- **Documentation**: Tutorials, use case examples
- **Performance**: Caching strategies, query optimization

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Use strict mode, follow React best practices
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Materials Project** for the comprehensive materials database
- **PubChem** (NCBI) for chemical compound data
- **SureChEMBL** (EMBL-EBI) for patent chemistry data
- **LangChain/LangGraph** for the agent framework
- **OpenAI** for GPT-4o
- **Exa.ai** for semantic web search

## 📧 Contact & Support

- **Issues**: Open an issue on GitHub for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Email**: [your-email@example.com]

---

**Built with ❤️ for materials scientists, chemists, and researchers**
