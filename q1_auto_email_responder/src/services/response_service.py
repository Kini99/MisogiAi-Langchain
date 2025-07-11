"""
Intelligent response generation service using LangChain and LangGraph.
"""

import asyncio
import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from loguru import logger

from ..config import get_settings
from ..models.email import Email, EmailResponse
from ..models.policy import PolicySearchResult
from ..models.template import ResponseTemplate, TemplateRenderResult
from .policy_service import policy_service
from .cache_service import cache_service


class ResponseService:
    """Intelligent email response generation service."""
    
    def __init__(self):
        """Initialize response service with LangChain components."""
        self.settings = get_settings()
        self.llm = None
        self.workflow = None
        self._initialize_llm()
        self._initialize_workflow()
    
    def _initialize_llm(self):
        """Initialize language model."""
        try:
            if self.settings.openai_api_key:
                self.llm = ChatOpenAI(
                    model="gpt-4",
                    temperature=0.7,
                    api_key=self.settings.openai_api_key
                )
                logger.info("OpenAI LLM initialized")
            else:
                logger.warning("No OpenAI API key provided, using fallback response generation")
                self.llm = None
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None
    
    def _initialize_workflow(self):
        """Initialize LangGraph workflow for response generation."""
        try:
            # Define the state schema
            class ResponseState:
                email: Email
                relevant_policies: List[PolicySearchResult]
                selected_template: Optional[ResponseTemplate]
                generated_response: Optional[EmailResponse]
                confidence_score: float
                error_message: Optional[str]
            
            # Create the workflow graph
            workflow = StateGraph(ResponseState)
            
            # Add nodes
            workflow.add_node("analyze_email", self._analyze_email)
            workflow.add_node("search_policies", self._search_policies)
            workflow.add_node("select_template", self._select_template)
            workflow.add_node("generate_response", self._generate_response)
            workflow.add_node("validate_response", self._validate_response)
            
            # Define edges
            workflow.add_edge("analyze_email", "search_policies")
            workflow.add_edge("search_policies", "select_template")
            workflow.add_edge("select_template", "generate_response")
            workflow.add_edge("generate_response", "validate_response")
            workflow.add_edge("validate_response", END)
            
            # Compile the workflow
            self.workflow = workflow.compile()
            logger.info("LangGraph workflow initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow: {e}")
            self.workflow = None
    
    async def generate_response(self, email: Email) -> EmailResponse:
        """Generate intelligent response for an email."""
        try:
            start_time = datetime.utcnow()
            
            # Check cache first
            cache_key = self._get_email_cache_key(email)
            cached_response = await cache_service.get(cache_key)
            if cached_response:
                logger.info(f"Using cached response for email {email.id}")
                return EmailResponse(**cached_response)
            
            if self.workflow and self.llm:
                # Use LangGraph workflow
                response = await self._generate_with_workflow(email)
            else:
                # Use fallback method
                response = await self._generate_fallback_response(email)
            
            # Cache the response
            await cache_service.set(cache_key, response.dict())
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Generated response for email {email.id} in {processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response for email {email.id}: {e}")
            return await self._generate_error_response(email, str(e))
    
    async def _generate_with_workflow(self, email: Email) -> EmailResponse:
        """Generate response using LangGraph workflow."""
        try:
            # Initialize state
            initial_state = {
                "email": email,
                "relevant_policies": [],
                "selected_template": None,
                "generated_response": None,
                "confidence_score": 0.0,
                "error_message": None
            }
            
            # Execute workflow
            result = await self.workflow.ainvoke(initial_state)
            
            if result.get("error_message"):
                raise Exception(result["error_message"])
            
            return result["generated_response"]
            
        except Exception as e:
            logger.error(f"Workflow generation failed: {e}")
            raise
    
    async def _analyze_email(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze email content and extract key information."""
        try:
            email = state["email"]
            
            # Create analysis prompt
            analysis_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an email analysis expert. Analyze the email and extract:
                1. Main topic/subject
                2. Sender's intent (question, request, complaint, etc.)
                3. Urgency level (low, medium, high)
                4. Required response type (informational, action, acknowledgment)
                5. Key entities mentioned
                6. Category tags for policy search
                
                Return a JSON object with these fields."""),
                ("human", "Email Subject: {subject}\nEmail Body: {body}")
            ])
            
            if self.llm:
                chain = analysis_prompt | self.llm | JsonOutputParser()
                analysis = await chain.ainvoke({
                    "subject": email.subject,
                    "body": email.body
                })
            else:
                # Fallback analysis
                analysis = {
                    "topic": email.subject,
                    "intent": "general",
                    "urgency": "medium",
                    "response_type": "informational",
                    "entities": [],
                    "tags": ["general"]
                }
            
            state["email_analysis"] = analysis
            return state
            
        except Exception as e:
            state["error_message"] = f"Email analysis failed: {e}"
            return state
    
    async def _search_policies(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Search for relevant policies based on email analysis."""
        try:
            analysis = state.get("email_analysis", {})
            email = state["email"]
            
            # Create search query
            search_query = f"{email.subject} {email.body}"
            if analysis.get("tags"):
                search_query += " " + " ".join(analysis["tags"])
            
            # Search policies
            relevant_policies = await policy_service.search_policies(
                query=search_query,
                limit=3
            )
            
            state["relevant_policies"] = relevant_policies
            return state
            
        except Exception as e:
            state["error_message"] = f"Policy search failed: {e}"
            return state
    
    async def _select_template(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Select appropriate response template."""
        try:
            analysis = state.get("email_analysis", {})
            policies = state.get("relevant_policies", [])
            
            # For now, use a simple template selection logic
            # In a real implementation, you would have template management
            template = ResponseTemplate(
                id="default",
                name="Default Response Template",
                subject_template="Re: {original_subject}",
                body_template="""Thank you for your email regarding {topic}.

Based on our company policies, here is the information you requested:

{policy_content}

If you have any further questions, please don't hesitate to contact us.

Best regards,
{company_name}""",
                category="general",
                author="system"
            )
            
            state["selected_template"] = template
            return state
            
        except Exception as e:
            state["error_message"] = f"Template selection failed: {e}"
            return state
    
    async def _generate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the actual response using LLM."""
        try:
            email = state["email"]
            template = state["selected_template"]
            policies = state.get("relevant_policies", [])
            analysis = state.get("email_analysis", {})
            
            # Prepare context
            policy_context = ""
            if policies:
                policy_context = "\n\n".join([
                    f"Policy: {p.policy.title}\n{p.policy.content[:500]}..."
                    for p in policies[:2]
                ])
            
            # Create generation prompt
            generation_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a professional email response generator. 
                Generate a polite, professional, and accurate response based on the provided context.
                
                Guidelines:
                - Be concise but comprehensive
                - Use a professional tone
                - Reference relevant policies when appropriate
                - Address the sender's specific concerns
                - Include a clear call to action if needed"""),
                ("human", """Email to respond to:
                Subject: {subject}
                Body: {body}
                
                Analysis: {analysis}
                
                Relevant Policies: {policy_context}
                
                Template: {template}
                
                Generate a response that follows the template structure but adapts to the specific email content.""")
            ])
            
            if self.llm:
                chain = generation_prompt | self.llm
                response_text = await chain.ainvoke({
                    "subject": email.subject,
                    "body": email.body,
                    "analysis": json.dumps(analysis),
                    "policy_context": policy_context,
                    "template": template.body_template
                })
                
                # Parse response
                response_content = response_text.content
            else:
                # Fallback response
                response_content = template.body_template.format(
                    topic=analysis.get("topic", "your inquiry"),
                    policy_content=policy_context or "our standard procedures",
                    company_name="Our Company"
                )
            
            # Create response object
            response = EmailResponse(
                email_id=email.id,
                response_subject=f"Re: {email.subject}",
                response_body=response_content,
                generated_at=datetime.utcnow(),
                policy_references=[p.policy.id for p in policies],
                template_used=template.id,
                confidence_score=0.8 if policies else 0.6,
                auto_send=False
            )
            
            state["generated_response"] = response
            state["confidence_score"] = response.confidence_score
            return state
            
        except Exception as e:
            state["error_message"] = f"Response generation failed: {e}"
            return state
    
    async def _validate_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated response."""
        try:
            response = state.get("generated_response")
            if not response:
                state["error_message"] = "No response generated"
                return state
            
            # Basic validation
            if len(response.response_body) < 10:
                state["error_message"] = "Response too short"
                return state
            
            if len(response.response_body) > 2000:
                state["error_message"] = "Response too long"
                return state
            
            # Adjust confidence based on validation
            if response.confidence_score < 0.5:
                response.auto_send = False
            
            return state
            
        except Exception as e:
            state["error_message"] = f"Response validation failed: {e}"
            return state
    
    async def _generate_fallback_response(self, email: Email) -> EmailResponse:
        """Generate fallback response when LLM is not available."""
        try:
            # Search for relevant policies
            search_query = f"{email.subject} {email.body}"
            policies = await policy_service.search_policies(query=search_query, limit=2)
            
            # Create simple response
            if policies:
                policy_content = policies[0].policy.content[:300] + "..."
                response_body = f"""Thank you for your email.

Based on our company policies, here is the relevant information:

{policy_content}

If you need further assistance, please let us know.

Best regards,
Company Support Team"""
                confidence_score = 0.7
                policy_references = [p.policy.id for p in policies]
            else:
                response_body = f"""Thank you for your email regarding "{email.subject}".

We have received your message and will review it shortly. A member of our team will get back to you as soon as possible.

Best regards,
Company Support Team"""
                confidence_score = 0.5
                policy_references = []
            
            return EmailResponse(
                email_id=email.id,
                response_subject=f"Re: {email.subject}",
                response_body=response_body,
                generated_at=datetime.utcnow(),
                policy_references=policy_references,
                confidence_score=confidence_score,
                auto_send=False
            )
            
        except Exception as e:
            logger.error(f"Fallback response generation failed: {e}")
            return await self._generate_error_response(email, str(e))
    
    async def _generate_error_response(self, email: Email, error_message: str) -> EmailResponse:
        """Generate error response when generation fails."""
        return EmailResponse(
            email_id=email.id,
            response_subject=f"Re: {email.subject}",
            response_body=f"""Thank you for your email.

We apologize, but we are currently experiencing technical difficulties processing your request. 
Our team has been notified and will respond to your inquiry as soon as possible.

We appreciate your patience.

Best regards,
Company Support Team""",
            generated_at=datetime.utcnow(),
            confidence_score=0.0,
            auto_send=False
        )
    
    def _get_email_cache_key(self, email: Email) -> str:
        """Generate cache key for email response."""
        email_hash = hashlib.md5(
            f"{email.id}:{email.subject}:{email.body}".encode()
        ).hexdigest()
        return f"response:{email_hash}"
    
    async def batch_generate_responses(self, emails: List[Email]) -> List[EmailResponse]:
        """Generate responses for multiple emails in batch."""
        try:
            tasks = [self.generate_response(email) for email in emails]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_responses = []
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.error(f"Failed to generate response for email {emails[i].id}: {response}")
                    # Generate error response
                    error_response = await self._generate_error_response(emails[i], str(response))
                    valid_responses.append(error_response)
                else:
                    valid_responses.append(response)
            
            logger.info(f"Generated {len(valid_responses)} responses for {len(emails)} emails")
            return valid_responses
            
        except Exception as e:
            logger.error(f"Batch response generation failed: {e}")
            return []


# Global response service instance
response_service = ResponseService() 