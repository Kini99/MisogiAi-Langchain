// Code Interpreter Frontend Application
class CodeInterpreter {
    constructor() {
        this.websocket = null;
        this.clientId = this.generateClientId();
        this.isConnected = false;
        this.isExecuting = false;
        this.currentLanguage = 'python';
        this.editor = null;
        this.currentTheme = 'dark';
        
        this.initializeElements();
        this.initializeCodeMirror();
        this.initializeWebSocket();
        this.bindEvents();
        this.loadSampleCode();
    }
    
    initializeElements() {
        this.elements = {
            languageSelector: document.getElementById('language-selector'),
            runBtn: document.getElementById('run-btn'),
            analyzeBtn: document.getElementById('analyze-btn'),
            explainBtn: document.getElementById('explain-btn'),
            clearBtn: document.getElementById('clear-btn'),
            clearOutputBtn: document.getElementById('clear-output-btn'),
            copyOutputBtn: document.getElementById('copy-output-btn'),
            themeToggle: document.getElementById('theme-toggle'),
            outputContent: document.getElementById('output-content'),
            connectionStatus: document.getElementById('connection-status'),
            executionStatus: document.getElementById('execution-status'),
            languageInfo: document.getElementById('language-info'),
            analysisPanel: document.getElementById('analysis-panel'),
            explanationPanel: document.getElementById('explanation-panel'),
            analysisContent: document.getElementById('analysis-content'),
            explanationContent: document.getElementById('explanation-content'),
            closeAnalysisBtn: document.getElementById('close-analysis-btn'),
            closeExplanationBtn: document.getElementById('close-explanation-btn')
        };
    }
    
    initializeCodeMirror() {
        const textarea = document.getElementById('code-editor');
        
        this.editor = CodeMirror.fromTextArea(textarea, {
            mode: 'python',
            theme: 'monokai',
            lineNumbers: true,
            autoCloseBrackets: true,
            matchBrackets: true,
            matchTags: true,
            showTrailingSpace: true,
            styleActiveLine: true,
            indentUnit: 4,
            tabSize: 4,
            indentWithTabs: false,
            lineWrapping: true,
            foldGutter: true,
            gutters: ['CodeMirror-linenumbers'],
            extraKeys: {
                'Ctrl-Enter': () => this.runCode(),
                'Ctrl-Space': 'autocomplete'
            }
        });
        
        // Set initial size
        this.editor.setSize('100%', '100%');
    }
    
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.clientId}`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            this.isConnected = true;
            this.updateConnectionStatus('online');
            this.log('Connected to server', 'success');
        };
        
        this.websocket.onmessage = (event) => {
            this.handleWebSocketMessage(JSON.parse(event.data));
        };
        
        this.websocket.onclose = () => {
            this.isConnected = false;
            this.updateConnectionStatus('offline');
            this.log('Disconnected from server', 'warning');
            
            // Attempt to reconnect after 5 seconds
            setTimeout(() => {
                if (!this.isConnected) {
                    this.initializeWebSocket();
                }
            }, 5000);
        };
        
        this.websocket.onerror = (error) => {
            this.updateConnectionStatus('offline');
            this.log('WebSocket error: ' + error, 'error');
        };
    }
    
    bindEvents() {
        // Language selector
        this.elements.languageSelector.addEventListener('change', (e) => {
            this.currentLanguage = e.target.value;
            this.updateLanguageInfo();
            this.updateEditorMode();
        });
        
        // Buttons
        this.elements.runBtn.addEventListener('click', () => this.runCode());
        this.elements.analyzeBtn.addEventListener('click', () => this.analyzeCode());
        this.elements.explainBtn.addEventListener('click', () => this.explainCode());
        this.elements.clearBtn.addEventListener('click', () => this.clearEditor());
        this.elements.clearOutputBtn.addEventListener('click', () => this.clearOutput());
        this.elements.copyOutputBtn.addEventListener('click', () => this.copyOutput());
        this.elements.themeToggle.addEventListener('click', () => this.toggleTheme());
        
        // Panel close buttons
        this.elements.closeAnalysisBtn.addEventListener('click', () => this.hideAnalysisPanel());
        this.elements.closeExplanationBtn.addEventListener('click', () => this.hideExplanationPanel());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.runCode();
            }
        });
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'execution_start':
                this.handleExecutionStart(message);
                break;
            case 'execution_output':
                this.handleExecutionOutput(message);
                break;
            case 'execution_complete':
                this.handleExecutionComplete(message);
                break;
            case 'execution_error':
                this.handleExecutionError(message);
                break;
            case 'analysis_result':
                this.handleAnalysisResult(message);
                break;
            case 'analysis_error':
                this.handleAnalysisError(message);
                break;
            case 'rag_response':
                this.handleRAGResponse(message);
                break;
            case 'rag_error':
                this.handleRAGError(message);
                break;
            default:
                this.log(`Unknown message type: ${message.type}`, 'warning');
        }
    }
    
    handleExecutionStart(message) {
        this.isExecuting = true;
        this.updateExecutionStatus('Executing...');
        this.log(`Starting execution (ID: ${message.execution_id})`, 'info');
        this.disableButtons();
    }
    
    handleExecutionOutput(message) {
        this.log(message.data, 'stdout');
    }
    
    handleExecutionComplete(message) {
        this.isExecuting = false;
        this.updateExecutionStatus('Ready');
        this.log('Execution completed', 'success');
        this.enableButtons();
    }
    
    handleExecutionError(message) {
        this.isExecuting = false;
        this.updateExecutionStatus('Error');
        this.log(`Execution error: ${message.error}`, 'error');
        this.enableButtons();
    }
    
    handleAnalysisResult(message) {
        this.showAnalysisPanel(message.data);
    }
    
    handleAnalysisError(message) {
        this.log(`Analysis error: ${message.error}`, 'error');
    }
    
    handleRAGResponse(message) {
        this.appendExplanation(message.data);
    }
    
    handleRAGError(message) {
        this.log(`Explanation error: ${message.error}`, 'error');
    }
    
    runCode() {
        if (!this.isConnected) {
            this.log('Not connected to server', 'error');
            return;
        }
        
        if (this.isExecuting) {
            this.log('Code execution already in progress', 'warning');
            return;
        }
        
        const code = this.editor.getValue().trim();
        if (!code) {
            this.log('No code to execute', 'warning');
            return;
        }
        
        this.clearOutput();
        this.log(`Running ${this.currentLanguage} code...`, 'info');
        
        this.sendWebSocketMessage({
            type: 'code_execution',
            code: code,
            language: this.currentLanguage
        });
    }
    
    analyzeCode() {
        if (!this.isConnected) {
            this.log('Not connected to server', 'error');
            return;
        }
        
        const code = this.editor.getValue().trim();
        if (!code) {
            this.log('No code to analyze', 'warning');
            return;
        }
        
        this.log('Analyzing code...', 'info');
        
        this.sendWebSocketMessage({
            type: 'code_analysis',
            code: code,
            language: this.currentLanguage
        });
    }
    
    explainCode() {
        if (!this.isConnected) {
            this.log('Not connected to server', 'error');
            return;
        }
        
        const code = this.editor.getValue().trim();
        if (!code) {
            this.log('No code to explain', 'warning');
            return;
        }
        
        this.showExplanationPanel();
        this.log('Getting AI explanation...', 'info');
        
        this.sendWebSocketMessage({
            type: 'rag_query',
            query: 'Explain this code and provide best practices',
            context: code
        });
    }
    
    sendWebSocketMessage(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        } else {
            this.log('WebSocket not connected', 'error');
        }
    }
    
    log(message, type = 'stdout') {
        const timestamp = new Date().toLocaleTimeString();
        const line = document.createElement('div');
        line.className = `output-line ${type}`;
        line.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${this.escapeHtml(message)}`;
        
        this.elements.outputContent.appendChild(line);
        this.elements.outputContent.scrollTop = this.elements.outputContent.scrollHeight;
    }
    
    clearEditor() {
        this.editor.setValue('');
        this.log('Editor cleared', 'info');
    }
    
    clearOutput() {
        this.elements.outputContent.innerHTML = '';
    }
    
    copyOutput() {
        const output = this.elements.outputContent.innerText;
        navigator.clipboard.writeText(output).then(() => {
            this.log('Output copied to clipboard', 'success');
        }).catch(() => {
            this.log('Failed to copy output', 'error');
        });
    }
    
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        const theme = this.currentTheme === 'dark' ? 'monokai' : 'default';
        this.editor.setOption('theme', theme);
        
        const icon = this.elements.themeToggle.querySelector('i');
        icon.className = this.currentTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
        
        this.log(`Theme switched to ${this.currentTheme}`, 'info');
    }
    
    updateConnectionStatus(status) {
        const indicator = this.elements.connectionStatus;
        indicator.className = `status-indicator ${status}`;
        
        const icon = indicator.querySelector('i');
        const text = indicator.querySelector('span') || indicator;
        
        switch (status) {
            case 'online':
                icon.className = 'fas fa-circle';
                text.textContent = 'Online';
                break;
            case 'offline':
                icon.className = 'fas fa-circle';
                text.textContent = 'Offline';
                break;
            case 'connecting':
                icon.className = 'fas fa-circle';
                text.textContent = 'Connecting...';
                break;
        }
    }
    
    updateExecutionStatus(status) {
        this.elements.executionStatus.textContent = status;
    }
    
    updateLanguageInfo() {
        const languageNames = {
            'python': 'Python 3.11',
            'javascript': 'JavaScript (Node.js)'
        };
        this.elements.languageInfo.textContent = languageNames[this.currentLanguage] || this.currentLanguage;
    }
    
    updateEditorMode() {
        const mode = this.currentLanguage === 'python' ? 'python' : 'javascript';
        this.editor.setOption('mode', mode);
    }
    
    disableButtons() {
        this.elements.runBtn.disabled = true;
        this.elements.analyzeBtn.disabled = true;
        this.elements.explainBtn.disabled = true;
    }
    
    enableButtons() {
        this.elements.runBtn.disabled = false;
        this.elements.analyzeBtn.disabled = false;
        this.elements.explainBtn.disabled = false;
    }
    
    showAnalysisPanel(analysis) {
        this.elements.analysisContent.innerHTML = this.renderAnalysis(analysis);
        this.elements.analysisPanel.classList.remove('hidden');
    }
    
    hideAnalysisPanel() {
        this.elements.analysisPanel.classList.add('hidden');
    }
    
    showExplanationPanel() {
        this.elements.explanationContent.innerHTML = '<div class="loading">Getting explanation...</div>';
        this.elements.explanationPanel.classList.remove('hidden');
    }
    
    hideExplanationPanel() {
        this.elements.explanationPanel.classList.add('hidden');
    }
    
    appendExplanation(text) {
        const content = this.elements.explanationContent;
        if (content.querySelector('.loading')) {
            content.innerHTML = '';
        }
        content.innerHTML += this.escapeHtml(text);
        content.scrollTop = content.scrollHeight;
    }
    
    renderAnalysis(analysis) {
        if (analysis.error) {
            return `<div class="analysis-item error">${this.escapeHtml(analysis.error)}</div>`;
        }
        
        let html = '';
        
        // Basic info
        html += `
            <div class="analysis-section">
                <h4>Code Overview</h4>
                <div class="analysis-item info">
                    <strong>Language:</strong> ${analysis.language}<br>
                    <strong>Lines of Code:</strong> ${analysis.lines_of_code}<br>
                    <strong>Complexity:</strong> ${analysis.complexity}
                </div>
            </div>
        `;
        
        // Functions
        if (analysis.functions && analysis.functions.length > 0) {
            html += `
                <div class="analysis-section">
                    <h4>Functions (${analysis.functions.length})</h4>
                    ${analysis.functions.map(func => `
                        <div class="analysis-item info">
                            <strong>${func.name}</strong> (line ${func.line})
                            ${func.args ? `<br>Parameters: ${func.args.join(', ')}` : ''}
                            ${func.has_docstring ? '<br><span class="success">✓ Has docstring</span>' : '<br><span class="warning">⚠ Missing docstring</span>'}
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Classes
        if (analysis.classes && analysis.classes.length > 0) {
            html += `
                <div class="analysis-section">
                    <h4>Classes (${analysis.classes.length})</h4>
                    ${analysis.classes.map(cls => `
                        <div class="analysis-item info">
                            <strong>${cls.name}</strong> (line ${cls.line})
                            ${cls.methods ? `<br>Methods: ${cls.methods.join(', ')}` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Issues
        if (analysis.issues && analysis.issues.length > 0) {
            html += `
                <div class="analysis-section">
                    <h4>Issues (${analysis.issues.length})</h4>
                    ${analysis.issues.map(issue => `
                        <div class="analysis-item warning">
                            <strong>${issue.type}:</strong> ${this.escapeHtml(issue.message)}
                            ${issue.suggestion ? `<br><em>Suggestion:</em> ${this.escapeHtml(issue.suggestion)}` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Suggestions
        if (analysis.suggestions && analysis.suggestions.length > 0) {
            html += `
                <div class="analysis-section">
                    <h4>Suggestions</h4>
                    ${analysis.suggestions.map(suggestion => `
                        <div class="analysis-item info">
                            💡 ${this.escapeHtml(suggestion)}
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        return html;
    }
    
    loadSampleCode() {
        const sampleCode = this.currentLanguage === 'python' ? 
            `# Welcome to Code Interpreter!
# Try running this sample code

def fibonacci(n):
    """Calculate the nth Fibonacci number"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the function
for i in range(10):
    print(f"Fibonacci({i}) = {fibonacci(i)}")

# List comprehension example
squares = [x**2 for x in range(5)]
print(f"Squares: {squares}")` :
            `// Welcome to Code Interpreter!
// Try running this sample code

function fibonacci(n) {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n-1) + fibonacci(n-2);
}

// Test the function
for (let i = 0; i < 10; i++) {
    console.log(\`Fibonacci(\${i}) = \${fibonacci(i)}\`);
}

// Array methods example
const numbers = [1, 2, 3, 4, 5];
const squares = numbers.map(x => x ** 2);
console.log(\`Squares: \${squares}\`);`;
        
        this.editor.setValue(sampleCode);
    }
    
    generateClientId() {
        return 'client_' + Math.random().toString(36).substr(2, 9);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.codeInterpreter = new CodeInterpreter();
}); 