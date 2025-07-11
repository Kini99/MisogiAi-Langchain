"""
RAG service for intelligent code explanations using LangChain and vector search
"""
import asyncio
import json
import logging
import os
from typing import AsyncGenerator, Dict, List, Optional
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from backend.core.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for intelligent code explanations"""
    
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.qa_chain = None
        self.docs_directory = Path(settings.docs_directory)
        self.chroma_persist_directory = Path(settings.chroma_persist_directory)
        
    async def initialize(self):
        """Initialize the RAG service"""
        try:
            # Initialize embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            # Initialize vector store
            if self.chroma_persist_directory.exists():
                self.vectorstore = Chroma(
                    persist_directory=str(self.chroma_persist_directory),
                    embedding_function=self.embeddings
                )
                logger.info("Loaded existing vector store")
            else:
                # Create new vector store and load documents
                await self._load_documents()
                
            # Initialize LLM if API key is available
            if settings.openai_api_key:
                self.llm = ChatOpenAI(
                    api_key=settings.openai_api_key,
                    model_name=settings.openai_model,
                    temperature=0.1
                )
                
                # Create QA chain
                prompt_template = PromptTemplate(
                    input_variables=["context", "question"],
                    template="""
You are an expert programming assistant. Use the following context to provide a clear, helpful explanation for the user's question about code.

Context: {context}

Question: {question}

Please provide a comprehensive explanation that includes:
1. What the code does
2. How it works
3. Best practices and potential improvements
4. Common pitfalls to avoid

Answer:"""
                )
                
                self.qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5}),
                    chain_type_kwargs={"prompt": prompt_template}
                )
                
            logger.info("RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            
    async def _load_documents(self):
        """Load and process documentation files"""
        try:
            documents = []
            
            # Load Python documentation
            python_docs = await self._load_python_docs()
            documents.extend(python_docs)
            
            # Load JavaScript documentation
            js_docs = await self._load_javascript_docs()
            documents.extend(js_docs)
            
            # Load coding best practices
            best_practices = await self._load_best_practices()
            documents.extend(best_practices)
            
            # Load error solutions
            error_solutions = await self._load_error_solutions()
            documents.extend(error_solutions)
            
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            split_docs = text_splitter.split_documents(documents)
            
            # Create vector store
            self.vectorstore = Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                persist_directory=str(self.chroma_persist_directory)
            )
            
            self.vectorstore.persist()
            logger.info(f"Loaded {len(split_docs)} document chunks into vector store")
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            
    async def _load_python_docs(self) -> List[Document]:
        """Load Python documentation"""
        docs = []
        
        # Python basics
        docs.append(Document(
            page_content="""
Python is a high-level, interpreted programming language. Key features:
- Dynamic typing
- Automatic memory management
- Extensive standard library
- Support for multiple programming paradigms

Common Python constructs:
- Variables: x = 10
- Functions: def my_function(): pass
- Classes: class MyClass: pass
- Lists: [1, 2, 3]
- Dictionaries: {"key": "value"}
- Loops: for item in items: pass
- Conditionals: if condition: pass
            """,
            metadata={"source": "python_basics", "type": "documentation"}
        ))
        
        # Python best practices
        docs.append(Document(
            page_content="""
Python Best Practices:
1. Use meaningful variable names
2. Follow PEP 8 style guide
3. Use list comprehensions for simple operations
4. Handle exceptions properly
5. Use type hints when possible
6. Write docstrings for functions and classes
7. Use virtual environments for project isolation
8. Keep functions small and focused
9. Use context managers for resource management
10. Prefer explicit over implicit
            """,
            metadata={"source": "python_best_practices", "type": "best_practices"}
        ))
        
        return docs
        
    async def _load_javascript_docs(self) -> List[Document]:
        """Load JavaScript documentation"""
        docs = []
        
        # JavaScript basics
        docs.append(Document(
            page_content="""
JavaScript is a high-level, interpreted programming language. Key features:
- Dynamic typing
- Prototype-based object-oriented programming
- First-class functions
- Event-driven programming

Common JavaScript constructs:
- Variables: let x = 10; const y = 20;
- Functions: function myFunction() {} or const myFunction = () => {};
- Objects: {key: "value"}
- Arrays: [1, 2, 3]
- Loops: for (let i = 0; i < items.length; i++) {}
- Conditionals: if (condition) {}
- Async/await: async function myAsyncFunction() {}
            """,
            metadata={"source": "javascript_basics", "type": "documentation"}
        ))
        
        # JavaScript best practices
        docs.append(Document(
            page_content="""
JavaScript Best Practices:
1. Use const and let instead of var
2. Use arrow functions for short functions
3. Use template literals for string interpolation
4. Handle promises properly with async/await
5. Use strict mode ('use strict')
6. Avoid global variables
7. Use meaningful variable names
8. Handle errors with try-catch
9. Use modern ES6+ features
10. Follow consistent naming conventions
            """,
            metadata={"source": "javascript_best_practices", "type": "best_practices"}
        ))
        
        return docs
        
    async def _load_best_practices(self) -> List[Document]:
        """Load general coding best practices"""
        docs = []
        
        docs.append(Document(
            page_content="""
General Coding Best Practices:
1. Write readable and maintainable code
2. Use meaningful variable and function names
3. Keep functions small and focused (single responsibility)
4. Avoid code duplication (DRY principle)
5. Write comprehensive tests
6. Use version control effectively
7. Document your code
8. Follow consistent formatting and style
9. Handle errors gracefully
10. Optimize for performance when necessary
11. Use design patterns appropriately
12. Keep dependencies minimal and up-to-date
            """,
            metadata={"source": "general_best_practices", "type": "best_practices"}
        ))
        
        return docs
        
    async def _load_error_solutions(self) -> List[Document]:
        """Load common error solutions"""
        docs = []
        
        # Python errors
        docs.append(Document(
            page_content="""
Common Python Errors and Solutions:

1. IndentationError: Check for consistent indentation (4 spaces)
2. NameError: Variable not defined - check variable scope and spelling
3. TypeError: Wrong data type - check variable types and conversions
4. IndexError: List index out of range - check list bounds
5. KeyError: Dictionary key not found - use .get() method or check keys
6. AttributeError: Object has no attribute - check object type and methods
7. ImportError: Module not found - check module name and installation
8. SyntaxError: Invalid syntax - check for missing colons, brackets, etc.
9. ZeroDivisionError: Division by zero - add checks before division
10. FileNotFoundError: File doesn't exist - check file path and permissions
            """,
            metadata={"source": "python_errors", "type": "error_solutions"}
        ))
        
        # JavaScript errors
        docs.append(Document(
            page_content="""
Common JavaScript Errors and Solutions:

1. ReferenceError: Variable not defined - check variable declaration and scope
2. TypeError: Wrong data type - check variable types and null/undefined
3. SyntaxError: Invalid syntax - check for missing semicolons, brackets, etc.
4. RangeError: Invalid array length - check array bounds and operations
5. URIError: Invalid URI - check URL encoding and format
6. EvalError: eval() function error - avoid using eval() for security
7. TypeError: Cannot read property - check for null/undefined objects
8. TypeError: Cannot set property - check object mutability
9. SyntaxError: Unexpected token - check for missing operators or brackets
10. ReferenceError: Cannot access before initialization - check hoisting and let/const
            """,
            metadata={"source": "javascript_errors", "type": "error_solutions"}
        ))
        
        return docs
        
    async def get_explanation(self, query: str, context: str = "") -> AsyncGenerator[str, None]:
        """Get intelligent explanation for code or query"""
        try:
            if not self.qa_chain:
                yield "RAG service not available. Please configure OpenAI API key."
                return
                
            # Combine query with context
            full_query = f"{query}\n\nContext: {context}" if context else query
            
            # Get response from QA chain
            response = await self.qa_chain.arun(full_query)
            
            # Stream response in chunks
            words = response.split()
            chunk_size = 5
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                yield chunk + " "
                await asyncio.sleep(0.1)  # Small delay for streaming effect
                
        except Exception as e:
            logger.error(f"RAG query error: {e}")
            yield f"Error getting explanation: {str(e)}"
            
    async def search_documents(self, query: str, k: int = 5) -> List[Dict]:
        """Search for relevant documents"""
        try:
            if not self.vectorstore:
                return []
                
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            
            documents = []
            for doc, score in results:
                documents.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
                
            return documents
            
        except Exception as e:
            logger.error(f"Document search error: {e}")
            return []
            
    async def add_document(self, content: str, metadata: Dict):
        """Add a new document to the vector store"""
        try:
            if not self.vectorstore:
                return
                
            doc = Document(page_content=content, metadata=metadata)
            self.vectorstore.add_documents([doc])
            self.vectorstore.persist()
            
            logger.info("Document added to vector store")
            
        except Exception as e:
            logger.error(f"Error adding document: {e}") 