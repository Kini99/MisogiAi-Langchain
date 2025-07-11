# Intelligent Email Response System

An AI-powered email response system that integrates with Gmail MCP to automatically generate appropriate responses based on company policies and FAQs.

## Features

- **Gmail MCP Integration**: Seamless integration with Gmail for email processing
- **Company Policy Management**: Store and manage company policies, FAQs, and response templates
- **Semantic Search**: Intelligent search for relevant policies using vector embeddings
- **Batch Processing**: Process multiple emails efficiently with prompt caching
- **Caching System**: Redis-based caching for frequently accessed policies
- **Async Processing**: High-performance async email processing

## Technical Stack

- **Python 3.11**: Core runtime
- **LangChain & LangGraph**: AI/ML framework for intelligent processing
- **ChromaDB**: Vector database for semantic search
- **Redis**: Caching layer for performance optimization
- **FastAPI**: REST API framework
- **Gmail API**: Email integration via MCP

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd intelligent-email-response-system
   ```

2. **Create virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the system**:
   ```bash
   python -m src.initialize
   ```

## Gmail API Setup

Before running the system, you need to set up Gmail API authentication. Follow these steps:

### 1. Create Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API** for your project:
   - Go to **APIs & Services** → **Library**
   - Search for "Gmail API"
   - Click on it and press **Enable**

### 2. Create OAuth 2.0 Credentials

1. In Google Cloud Console, go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client IDs**
3. Choose **Desktop application** as the application type
4. Give it a name (e.g., "Email Response System")
5. Click **Create**
6. Note down your **Client ID** and **Client Secret**

### 3. Generate Refresh Token

Use the provided script to generate your refresh token:

```bash
# Make sure you have the required dependencies
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Run the token generator script
python generate_gmail_token.py
```

The script will:
1. Ask for your Client ID and Client Secret
2. Open a browser window for Google authentication
3. Ask you to sign in and grant permissions
4. Display your refresh token

**Copy the refresh token** - you'll need it for the next step.

### 4. Configure Environment Variables

Create a `.env` file with your Gmail credentials:

```env
# Gmail API Configuration
GMAIL_CLIENT_ID=your_actual_client_id
GMAIL_CLIENT_SECRET=your_actual_client_secret
GMAIL_REFRESH_TOKEN=your_actual_refresh_token

# Database Configuration
REDIS_URL=redis://localhost:6379
CHROMA_PERSIST_DIRECTORY=./data/chroma

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# AI/ML Configuration
OPENAI_API_KEY=your_openai_api_key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Cache Configuration
CACHE_TTL=3600
BATCH_SIZE=10
```

### 5. Test Your Setup

Test that your Gmail authentication works:

```bash
python -c "
from src.services.gmail_service import GmailService
import asyncio

async def test():
    gmail = GmailService()
    emails = await gmail.get_emails(max_results=1)
    print(f'✓ Successfully connected to Gmail! Found {len(emails)} emails')

asyncio.run(test())
"
```

## Configuration

## Usage

### Starting the System

1. **Start Redis** (if not running):
   ```bash
   redis-server
   ```

2. **Run the main application**:
   ```bash
   python -m src.main
   ```

3. **Start the API server**:
   ```bash
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```

### API Endpoints

- `POST /api/emails/process` - Process incoming emails
- `GET /api/policies` - List all policies
- `POST /api/policies` - Add new policy
- `GET /api/templates` - List response templates
- `POST /api/templates` - Add new template

### Command Line Interface

```bash
# Process emails in batch
python -m src.cli process-emails --batch-size 10

# Add company policy
python -m src.cli add-policy --file policy.md --category "hr"

# Generate response for specific email
python -m src.cli generate-response --email-id "email_id"
```

## Project Structure

```
intelligent-email-response-system/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main application entry point
│   ├── config.py              # Configuration management
│   ├── models/                # Data models
│   │   ├── __init__.py
│   │   ├── email.py
│   │   ├── policy.py
│   │   └── template.py
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── gmail_service.py   # Gmail MCP integration
│   │   ├── policy_service.py  # Policy management
│   │   ├── cache_service.py   # Caching layer
│   │   └── response_service.py # Response generation
│   ├── api/                   # REST API
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routes/
│   │   └── middleware/
│   ├── cli/                   # Command line interface
│   │   ├── __init__.py
│   │   └── commands.py
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       ├── embeddings.py
│       └── validators.py
├── data/                      # Data storage
│   ├── policies/              # Company policies
│   ├── templates/             # Response templates
│   └── chroma/                # Vector database
├── tests/                     # Test suite
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## Development

### Running Tests

```bash
pytest tests/
```
