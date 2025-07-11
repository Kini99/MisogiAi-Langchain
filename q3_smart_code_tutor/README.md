# Full-Stack Code Interpreter

A modern, real-time code interpreter with intelligent explanations powered by RAG (Retrieval-Augmented Generation) and secure sandboxed execution.

## 🚀 Features

### Core Functionality
- **Interactive Code Editor** with syntax highlighting for Python & JavaScript
- **Real-time Code Execution** in secure E2B sandboxed environments
- **Intelligent Code Analysis** with AST parsing and linting
- **AI-Powered Explanations** using LangChain and RAG
- **WebSocket Streaming** for real-time communication
- **Concurrent Execution Handling** with session management

### Technical Stack
- **Backend**: FastAPI with WebSocket support
- **Frontend**: Modern JavaScript with CodeMirror editor
- **Code Execution**: E2B sandbox integration
- **AI/ML**: LangChain, LangGraph, OpenAI GPT-4
- **Vector Database**: ChromaDB for RAG
- **Styling**: Modern CSS with dark theme

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Node.js 18+ (for JavaScript execution)
- E2B API key (for sandboxed execution)
- OpenAI API key (for RAG explanations)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd w5d2q3
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` file:
```env
# E2B Configuration
E2B_API_KEY=your_e2b_api_key_here
E2B_PROJECT_ID=your_e2b_project_id_here

# OpenAI Configuration (for RAG)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Vector Database
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Code Execution Limits
MAX_EXECUTION_TIME=30
MAX_MEMORY_USAGE=512
```

4. **Run the application**
```bash
cd backend
python main.py
```

5. **Access the application**
Open your browser and navigate to `http://localhost:8000`

## 📁 Project Structure

```
w5d2q3/
├── backend/
│   ├── api/
│   │   ├── code_execution.py      # REST API endpoints
│   │   └── websocket_manager.py   # WebSocket connection management
│   ├── core/
│   │   └── config.py              # Configuration settings
│   ├── services/
│   │   ├── e2b_service.py         # E2B sandbox integration
│   │   ├── rag_service.py         # RAG and AI explanations
│   │   └── code_analyzer.py       # Code analysis and linting
│   ├── models/                    # Data models
│   ├── utils/                     # Utility functions
│   └── main.py                    # FastAPI application
├── frontend/
│   └── public/
│       ├── index.html             # Main HTML page
│       ├── styles.css             # Modern CSS styling
│       └── app.js                 # Frontend JavaScript
├── docs/                          # Documentation files
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `E2B_API_KEY` | E2B API key for sandboxed execution | Required |
| `E2B_PROJECT_ID` | E2B project ID | Optional |
| `OPENAI_API_KEY` | OpenAI API key for RAG | Required |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `false` |
| `MAX_EXECUTION_TIME` | Max execution time (seconds) | `30` |
| `MAX_MEMORY_USAGE` | Max memory usage (MB) | `512` |

### Supported Languages

- **Python 3.11**: Full execution with standard library
- **JavaScript (Node.js 18)**: Full execution with npm packages

## 🎯 Usage

### Code Execution
1. Select your programming language (Python or JavaScript)
2. Write or paste your code in the editor
3. Click "Run Code" or press `Ctrl+Enter`
4. View real-time execution output

### Code Analysis
1. Write your code in the editor
2. Click "Analyze" button
3. View detailed analysis including:
   - Code complexity metrics
   - Function and class information
   - Potential issues and suggestions
   - Best practices recommendations

### AI Explanations
1. Write your code in the editor
2. Click "Explain" button
3. Get intelligent explanations powered by RAG:
   - What the code does
   - How it works
   - Best practices and improvements
   - Common pitfalls to avoid

### Keyboard Shortcuts
- `Ctrl+Enter`: Run code
- `Ctrl+Space`: Code completion (where supported)

## 🔒 Security Features

- **Sandboxed Execution**: All code runs in isolated E2B environments
- **Resource Limits**: Configurable time and memory limits
- **Session Management**: Automatic cleanup of execution sessions
- **Input Validation**: Comprehensive input sanitization
- **Error Handling**: Graceful error handling and recovery

## 🚀 Performance Features

- **Real-time Streaming**: WebSocket-based real-time communication
- **Concurrent Execution**: Handle multiple users simultaneously
- **Async Processing**: Non-blocking code execution
- **Connection Management**: Automatic reconnection and session cleanup
- **Caching**: Vector database caching for faster RAG responses

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest tests/
```

### Frontend Testing
```bash
# Manual testing through browser
# Open browser developer tools for debugging
```

## 📊 Monitoring

The application includes comprehensive logging and monitoring:

- **Connection Status**: Real-time WebSocket connection monitoring
- **Execution Status**: Live execution progress tracking
- **Error Logging**: Detailed error logging and reporting
- **Performance Metrics**: Execution time and resource usage tracking

## 🔧 Development

### Adding New Languages
1. Update `backend/services/e2b_service.py` with new language support
2. Add language mode to CodeMirror in `frontend/public/app.js`
3. Update language selector in `frontend/public/index.html`
4. Add language-specific analysis in `backend/services/code_analyzer.py`

### Extending RAG Capabilities
1. Add new documents to `backend/services/rag_service.py`
2. Update prompt templates for better explanations
3. Configure additional vector database collections

### Customizing UI
1. Modify `frontend/public/styles.css` for styling changes
2. Update `frontend/public/app.js` for functionality changes
3. Modify `frontend/public/index.html` for structure changes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **E2B** for secure sandboxed execution
- **OpenAI** for AI-powered explanations
- **LangChain** for RAG implementation
- **CodeMirror** for the code editor
- **FastAPI** for the backend framework

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in the `docs/` folder
- Review the configuration examples

## 🔄 Updates

Stay updated with the latest features and improvements:
- Watch the repository for updates
- Check the changelog for version history
- Follow the development roadmap

---

**Built with ❤️ using modern web technologies and AI/ML frameworks** 