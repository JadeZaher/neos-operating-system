# NEOS - New Earth Operating System

A modular, non-sovereign governance architecture with AI-powered governance facilitation.

## Quick Start (Windows Development)

### Prerequisites
- Python 3.12+
- Anthropic API key (or local LLM setup - see Local LLM section below)

### 1. Automated Setup
```batch
setup-dev.bat
```

This script:
- Creates a Python virtual environment (`.venv/`)
- Installs all dependencies
- Creates necessary `.env` files
- Initializes SQLite database with sample data

### 2. Configure API Key

**Option A - Anthropic Cloud (Default):**
Edit `agent/.env` and replace `sk-ant-your-key-here` with your actual Anthropic API key:
```env
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

**Option B - Local LLM (LiteLLM + Ollama):**
See "Local LLM Setup" section below for complete configuration.

### 3. Start Development Server

**Option A - Command Line:**
```batch
start-dev.bat
```

**Option B - Windsurf Debug:**
- Open the project in Windsurf
- Press `F5` or go to Run & Debug
- Select "NEOS Agent Debug" configuration

### 4. Access the Application
- Dashboard: http://localhost:8000/dashboard
- API Health: http://localhost:8000/api/v1/health

## Project Structure

```
neos-operating-system/
├── agent/                    # Sanic web service (governance dashboard)
│   ├── src/neos_agent/      # Main application code
│   ├── scripts/             # Database seeding scripts
│   ├── templates/           # Jinja2 templates
│   └── tests/               # Test suite
├── neos-core/               # 54 governance skill modules
├── .vscode/                 # Windsurf debug configuration
├── setup-dev.bat           # Automated setup script
├── start-dev.bat           # Development server launcher
└── README.md               # This file
```

## Development Workflow

### Making Changes
- The development server auto-reloads on file changes
- Use the Windsurf debug configuration for breakpoints
- Database uses SQLite for local development (`neos.db`)

### Running Tests
```batch
cd agent
..\venv\Scripts\python -m pytest tests/ -v
```

### Database Management
- **SQLite**: Automatically managed, no migrations needed for dev
- **Reset database**: Delete `neos.db` and run `python -m scripts.seed_omnione`

## Local LLM Setup

Run NEOS with local models using LiteLLM + Ollama while maintaining full Claude tool compatibility.

### Prerequisites
- [Ollama](https://ollama.ai/) installed and running
- A compatible local model (e.g., `llama3.1:8b`, `qwen2.5:7b`)

### 1. Install Ollama and Download Model
```bash
# Install Ollama (Windows)
# Download from https://ollama.ai/

# Pull a model (recommended for governance tasks)
ollama pull llama3.1:8b
# OR for smaller footprint
ollama pull qwen2.5:7b

# Verify installation
ollama list
```

### 2. Install LiteLLM
```batch
# Activate virtual environment first
.venv\Scripts\activate.bat

# Install LiteLLM
pip install litellm
```

### 3. Start LiteLLM Proxy
```batch
# Start proxy with your chosen model
litellm --model ollama/llama3.1:8b --port 8001

# Keep this terminal running - it proxies Claude API calls to Ollama
```

### 4. Configure NEOS for Local LLM
Edit `agent/.env`:
```env
# Local LLM configuration
ANTHROPIC_API_KEY=not-needed-for-local
ANTHROPIC_BASE_URL=http://localhost:8001
CLAUDE_MODEL=ollama/llama3.1:8b

# Keep other settings
DATABASE_URL=sqlite+aiosqlite:///neos.db
NEOS_CORE_PATH=../neos-core
LOG_LEVEL=info
CORS_ORIGINS=*
```

### 5. Start NEOS Development Server
```batch
# In a NEW terminal (keep LiteLLM running)
start-dev.bat
```

### Switching Between Cloud and Local LLMs

**To use Anthropic Cloud:**
```env
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
# Remove ANTHROPIC_BASE_URL line
CLAUDE_MODEL=claude-sonnet-4-20250514
```

**To use Local LLM:**
```env
ANTHROPIC_API_KEY=not-needed-for-local
ANTHROPIC_BASE_URL=http://localhost:8001
CLAUDE_MODEL=ollama/llama3.1:8b
```

### Recommended Local Models

| Model | Size | Best For | Notes |
|-------|------|----------|-------|
| `llama3.1:8b` | 8B | General governance | Good balance of capability/speed |
| `qwen2.5:7b` | 7B | Complex reasoning | Strong analytical capabilities |
| `llama3.1:70b` | 70B | High-quality responses | Requires powerful hardware |

### Troubleshooting Local LLMs

**LiteLLM connection issues:**
- Ensure Ollama is running: `ollama serve`
- Check model is downloaded: `ollama list`
- Verify LiteLLM proxy is accessible: `curl http://localhost:8001/v1/models`

**Performance issues:**
- Use smaller models for testing (`qwen2.5:7b`)
- Ensure sufficient RAM (8B models need ~8GB RAM)
- Consider GPU acceleration if available

**Tool calling problems:**
- LiteLLM automatically handles Claude tool format conversion
- All 23 governance tools work unchanged
- If issues occur, check LiteLLM logs for model compatibility

## Configuration

### Environment Variables
Key variables in `agent/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection | `sqlite+aiosqlite:///neos.db` |
| `ANTHROPIC_API_KEY` | Claude API key (or `not-needed-for-local`) | Required |
| `ANTHROPIC_BASE_URL` | LLM base URL (for local LLMs) | Anthropic default |
| `NEOS_CORE_PATH` | Path to governance skills | `../neos-core` |
| `CLAUDE_MODEL` | Model to use (Claude or `ollama/model-name`) | `claude-sonnet-4-20250514` |
| `LOG_LEVEL` | Logging verbosity | `info` |

### Production Deployment
For production deployment with PostgreSQL:
1. Set `DATABASE_URL=postgresql+asyncpg://...`
2. Run migrations: `python -m alembic upgrade head`
3. Use production startup: `python -m neos_agent.main --workers 4`

## Key Components

### Agent Web Service
- **Framework**: Sanic (async Python)
- **Frontend**: Datastar + Tailwind CSS (server-rendered)
- **Database**: SQLAlchemy 2.0 with async support
- **AI Integration**: Anthropic Claude API

### Governance Features
- Real-time dashboard with SSE updates
- AI-powered governance chat
- Agreement management and workflow
- ACT process (Advice/Consent/Test)
- Decision records and memory
- Member onboarding and profiles
- Domain management with metrics

### NEOS Skills
54 governance modules across 10 layers:
- Layer I: Foundational Agreements
- Layer II: Authority Framework
- Layer III: ACT Engine
- Layer IV: Economic System
- Layer V: Inter-Unit Coordination
- Layer VI: Conflict Resolution
- Layer VII: Safeguard Systems
- Layer VIII: Emergency Protocols
- Layer IX: Memory & Learning
- Layer X: Exit & Portability

## Troubleshooting

### Common Issues
- **Module not found**: Run `setup-dev.bat` to reinstall dependencies
- **Database errors**: Delete `neos.db` and restart the server
- **Port 8000 in use**: Modify `start-dev.bat` to use different port

### Windows-Specific Notes
- Use `python -m neos_agent.main` instead of `sanic` CLI
- Virtual environment scripts are in `.venv/Scripts/` (not `bin/`)
- All batch files handle Windows path separators automatically

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest tests/ -v`
5. Submit a pull request

## License

See individual component licenses for more information.

---

**First ecosystem**: OmniOne - A community in Bali stewarded by Green Earth Vision (GEV, 501c3)
