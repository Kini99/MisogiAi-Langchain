# Stock Market Chat - Real-time AI Trading Assistant

A comprehensive real-time stock market chat application that streams live market data, fetches trending financial news, and provides AI-powered stock recommendations through an interactive chat interface.

## 🚀 Features

### Real-time Chat Interface
- **WebSocket-based real-time communication**
- **Interactive chat with AI assistant**
- **Modern, responsive UI with real-time updates**
- **Message history and session management**

### Live Market Data
- **Real-time stock prices and market data**
- **Multiple stock symbols support**
- **Market indices (S&P 500, NASDAQ, DOW)**
- **Trending stocks analysis**
- **Historical data and technical indicators**

### Financial News Integration
- **Real-time financial news from NewsAPI**
- **Sentiment analysis of news articles**
- **Stock-specific news filtering**
- **Automatic news relevance scoring**

### AI-Powered Recommendations
- **LangChain and LangGraph integration**
- **Comprehensive stock analysis workflow**
- **Technical and fundamental analysis**
- **Sentiment-based recommendations**
- **Risk assessment and price targets**

### Advanced Features
- **Vector database for knowledge storage**
- **Rate limiting and connection management**
- **Comprehensive logging and monitoring**
- **Scalable architecture for concurrent users**

## 🛠️ Technology Stack

### Backend
- **Python 3.11** - Core programming language
- **FastAPI** - Modern web framework
- **WebSockets** - Real-time communication
- **SQLAlchemy** - Database ORM
- **ChromaDB** - Vector database for embeddings

### AI & ML
- **LangChain 0.1.0** - LLM framework
- **LangGraph 0.0.26** - Workflow orchestration
- **OpenAI GPT-4** - AI model for recommendations
- **TextBlob & VADER** - Sentiment analysis

### Data Sources
- **Yahoo Finance (yfinance)** - Stock market data
- **NewsAPI** - Financial news
- **Alpha Vantage** - Alternative market data
- **Finnhub** - Additional financial data

### Frontend
- **HTML5/CSS3** - Modern responsive design
- **JavaScript (ES6+)** - Interactive functionality
- **WebSocket API** - Real-time updates
- **Font Awesome** - Icons and UI elements

## 📋 Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git
- Modern web browser with WebSocket support

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd stock-market-chat
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory:
```env
# Application Settings
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./stock_chat.db
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Redis (optional)
REDIS_URL=redis://localhost:6379

# API Keys (Get free keys from respective services)
OPENAI_API_KEY=your_openai_api_key_here
NEWS_API_KEY=your_news_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
FINNHUB_API_KEY=your_finnhub_key_here

# AI Model Settings
OPENAI_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-ada-002
MAX_TOKENS=1000
TEMPERATURE=0.7

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=60
MAX_CONCURRENT_CONNECTIONS=100
```

### 5. Initialize Database
```bash
python -c "from app.core.database import init_db; init_db()"
```

### 6. Run the Application
```bash
python run.py
```

The application will be available at `http://localhost:8000`

## 🔑 API Keys Setup

### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account and get your API key
3. Add to `.env` file: `OPENAI_API_KEY=your_key_here`

### NewsAPI Key
1. Visit [NewsAPI](https://newsapi.org/)
2. Sign up for a free account
3. Get your API key
4. Add to `.env` file: `NEWS_API_KEY=your_key_here`

### Optional: Alpha Vantage & Finnhub
- **Alpha Vantage**: [Get free API key](https://www.alphavantage.co/support/#api-key)
- **Finnhub**: [Get free API key](https://finnhub.io/register)

## 📖 Usage

### Starting the Application
```bash
# Development mode with auto-reload
python run.py

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Web Interface
1. Open your browser and navigate to `http://localhost:8000`
2. The chat interface will automatically connect via WebSocket
3. Start asking questions about stocks, market data, or get AI recommendations

### Example Chat Commands
- **"What's the price of AAPL?"** - Get current stock price
- **"Show me market news"** - Get latest financial news
- **"Analyze TSLA"** - Get AI-powered stock analysis
- **"Market summary"** - Get overview of major indices
- **"Show trending stocks"** - Get trending stocks by volume/movement

### API Endpoints
- `GET /api/stocks/{symbol}` - Get stock data
- `GET /api/market/summary` - Get market summary
- `GET /api/news` - Get financial news
- `GET /api/recommendations/{symbol}` - Get AI recommendation
- `GET /api/search/stocks` - Search for stocks
- `WebSocket /ws/{user_id}` - Real-time chat

## 🏗️ Architecture

### Project Structure
```
stock-market-chat/
├── app/
│   ├── api/
│   │   ├── endpoints/          # REST API endpoints
│   │   └── websockets/         # WebSocket handlers
│   ├── core/
│   │   ├── config.py          # Configuration settings
│   │   └── database.py        # Database models and setup
│   ├── services/
│   │   ├── ai/                # AI recommendation service
│   │   ├── data/              # Stock data service
│   │   └── news/              # News service
│   └── utils/                 # Utility functions
├── templates/
│   └── index.html             # Main chat interface
├── static/                    # Static assets
├── logs/                      # Application logs
├── chroma_db/                 # Vector database
├── requirements.txt           # Python dependencies
├── run.py                     # Application entry point
└── README.md                  # This file
```

### Key Components

#### 1. Real-time Communication
- **WebSocket Manager**: Handles multiple concurrent connections
- **Chat Handler**: Processes messages and generates responses
- **Message Queue**: Manages message flow and rate limiting

#### 2. Data Services
- **Stock Data Service**: Fetches live market data from multiple sources
- **News Service**: Retrieves and analyzes financial news
- **Caching Layer**: Optimizes API calls and response times

#### 3. AI Recommendation System
- **LangGraph Workflow**: Multi-step analysis pipeline
- **Technical Analysis**: Moving averages, RSI, trend analysis
- **Sentiment Analysis**: News sentiment and market sentiment
- **Recommendation Engine**: AI-powered buy/sell/hold decisions

#### 4. Vector Database
- **ChromaDB**: Stores embeddings for semantic search
- **Knowledge Base**: Historical data and analysis results
- **RAG Enhancement**: Retrieval-augmented generation for better responses

## 🔧 Configuration

### Environment Variables
All configuration is handled through environment variables in the `.env` file:

- **Application**: Host, port, debug mode
- **Database**: Connection strings and settings
- **API Keys**: External service authentication
- **AI Models**: Model selection and parameters
- **Rate Limiting**: Request limits and throttling

### Customization
- **UI Theme**: Modify CSS in `templates/index.html`
- **AI Prompts**: Edit prompts in `app/services/ai/ai_service.py`
- **Data Sources**: Add new APIs in respective service files
- **Analysis Logic**: Customize technical indicators and algorithms

## 📊 Performance

### Optimization Features
- **Connection Pooling**: Efficient database connections
- **Request Caching**: Reduces API calls and improves response times
- **Async Processing**: Non-blocking I/O operations
- **Rate Limiting**: Prevents API abuse and ensures fair usage
- **Memory Management**: Efficient data structures and cleanup

### Scalability
- **Horizontal Scaling**: Stateless design allows multiple instances
- **Load Balancing**: WebSocket connections can be distributed
- **Database Optimization**: Indexed queries and connection pooling
- **Caching Strategy**: Multi-level caching for better performance

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_stock_service.py
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: Service interaction testing
- **WebSocket Tests**: Real-time communication testing
- **API Tests**: REST endpoint testing
